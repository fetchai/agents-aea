# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2020 Fetch.AI Limited
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------
"""This module contains the implementation of AEA agents manager."""
import asyncio
import datetime
import json
import multiprocessing
import os
import threading
from abc import ABC, abstractmethod
from asyncio.tasks import FIRST_COMPLETED
from collections import defaultdict
from multiprocessing.synchronize import Event
from shutil import rmtree
from threading import Thread
from traceback import format_exc
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from aea.aea import AEA
from aea.configurations.base import AgentConfig
from aea.configurations.constants import AEA_MANAGER_DATA_DIRNAME, DEFAULT_REGISTRY_NAME
from aea.configurations.data_types import PackageIdPrefix, PublicId
from aea.exceptions import enforce
from aea.helpers.io import open_file
from aea.manager.project import AgentAlias, Project
from aea.manager.utils import (
    get_venv_dir_for_project,
    project_check,
    project_install_and_build,
    run_in_venv,
)


class ProjectNotFoundError(ValueError):
    """Project not found exception."""


class ProjectCheckError(ValueError):
    """Project check error exception."""

    def __init__(self, msg: str, source_exception: Exception):
        """Init exception."""
        super().__init__(msg)
        self.source_exception = source_exception


class ProjectPackageConsistencyCheckError(ValueError):
    """Check consistency of package versions against already added project."""

    def __init__(
        self,
        agent_project_id: PublicId,
        conflicting_packages: List[Tuple[PackageIdPrefix, str, str, Set[PublicId]]],
    ):
        """
        Initialize the exception.

        :param agent_project_id: the agent project id whose addition has failed.
        :param conflicting_packages: the conflicting packages.
        """
        self.agent_project_id = agent_project_id
        self.conflicting_packages = conflicting_packages
        super().__init__(self._build_error_message())

    def _build_error_message(self) -> str:
        """Build the error message."""
        conflicting_packages = sorted(self.conflicting_packages, key=str)
        message = f"cannot add project '{self.agent_project_id}': the following AEA dependencies have conflicts with previously added projects:\n"
        for (
            (type_, author, name),
            existing_version,
            new_version,
            agents,
        ) in conflicting_packages:
            message += f"- '{author}/{name}' of type {type_}: the new version '{new_version}' conflicts with existing version '{existing_version}' of the same package required by agents: {list(agents)}\n"
        return message


class BaseAgentRunTask(ABC):
    """Base abstract class for agent run tasks."""

    @abstractmethod
    def start(self) -> None:
        """Start task."""

    @abstractmethod
    def wait(self) -> asyncio.Future:
        """Return future to wait task completed."""

    @abstractmethod
    def stop(self) -> None:
        """Stop task."""

    @property
    @abstractmethod
    def is_running(self) -> bool:
        """Return is task running."""


class AgentRunAsyncTask(BaseAgentRunTask):
    """Async task wrapper for agent."""

    def __init__(self, agent: AEA, loop: asyncio.AbstractEventLoop) -> None:
        """Init task with agent alias and loop."""
        self.agent = agent
        self.run_loop: asyncio.AbstractEventLoop = loop
        self.caller_loop: asyncio.AbstractEventLoop = loop
        self._done_future: Optional[asyncio.Future] = None
        self.task: Optional[asyncio.Task] = None

    def create_run_loop(self) -> None:
        """Create run loop."""

    def start(self) -> None:
        """Start task."""
        self.create_run_loop()
        self.task = self.run_loop.create_task(self._run_wrapper())
        self._done_future = asyncio.Future(loop=self.caller_loop)

    def wait(self) -> asyncio.Future:
        """Return future to wait task completed."""
        if not self._done_future:  # pragma: nocover
            raise ValueError("Task not started!")
        return self._done_future

    def stop(self) -> None:
        """Stop task."""
        if not self.run_loop or not self.task:  # pragma: nocover
            raise ValueError("Task was not started!")
        self.run_loop.call_soon_threadsafe(self.task.cancel)

    async def _run_wrapper(self) -> None:
        """Run task internals."""
        if not self._done_future:  # pragma: nocover
            raise ValueError("Task was not started! please use start method")
        exc = None
        try:
            await self.run()
        except asyncio.CancelledError:  # pragma: nocover
            pass
        except Exception as e:  # pylint: disable=broad-except
            exc = e
        finally:
            self.caller_loop.call_soon_threadsafe(self._set_result, exc)

    def _set_result(self, exc: Optional[BaseException]) -> None:
        """Set result of task execution."""
        if not self._done_future or self._done_future.done():  # pragma: nocover
            return
        if exc:
            self._done_future.set_exception(exc)
        else:
            self._done_future.set_result(None)

    async def run(self) -> None:
        """Run task body."""
        self.agent.runtime.set_loop(self.run_loop)
        await self.agent.runtime.run()

    @property
    def is_running(self) -> bool:
        """Return is task running."""
        return not self.wait().done()


class AgentRunThreadTask(AgentRunAsyncTask):
    """Threaded wrapper to run agent."""

    def __init__(self, agent: AEA, loop: asyncio.AbstractEventLoop) -> None:
        """Init task with agent alias and loop."""
        AgentRunAsyncTask.__init__(self, agent, loop)
        self._thread: Optional[Thread] = None

    def create_run_loop(self) -> None:
        """Create run loop."""
        self.run_loop = asyncio.new_event_loop()

    def start(self) -> None:
        """Run task in a dedicated thread."""
        super().start()
        self._thread = threading.Thread(
            target=self.run_loop.run_until_complete, args=[self.task], daemon=True
        )
        self._thread.start()

    def stop(self,) -> None:
        """Stop the task."""
        super().stop()
        if self._thread is not None:
            self._thread.join()


class AgentRunProcessTask(BaseAgentRunTask):
    """Subprocess wrapper to run agent."""

    PROCESS_JOIN_TIMEOUT = 20  # in seconds
    PROCESS_ALIVE_SLEEP_TIME = 0.005  # in seconds

    def __init__(  # pylint: disable=super-init-not-called
        self, agent_alias: AgentAlias, loop: asyncio.AbstractEventLoop
    ) -> None:
        """Init task with agent alias and loop."""
        self.caller_loop: asyncio.AbstractEventLoop = loop
        self._manager = multiprocessing.Manager()
        self._stop_event = self._manager.Event()
        self.agent_alias = agent_alias
        self.process: Optional[multiprocessing.Process] = None
        self._wait_task: Optional[asyncio.Future] = None
        self._result_queue = self._manager.Queue()

    def start(self) -> None:
        """Run task in a dedicated process."""
        self._wait_task = asyncio.ensure_future(
            self._wait_for_result(), loop=self.caller_loop
        )
        self.process = multiprocessing.Process(
            target=self._run_agent,
            args=(self.agent_alias, self._stop_event, self._result_queue),
        )
        self.process.start()

    async def _wait_for_result(self) -> Any:
        """Wait for the result of the function call."""
        if not self.process:
            raise ValueError("Task not started!")  # pragma: nocover

        while self.process.is_alive():
            await asyncio.sleep(self.PROCESS_ALIVE_SLEEP_TIME)

        result = self._result_queue.get_nowait()
        self.process.join(self.PROCESS_JOIN_TIMEOUT)
        if isinstance(result, Exception):
            raise result
        return result

    def wait(self) -> asyncio.Future:
        """Return future to wait task completed."""
        if not self._wait_task:
            raise ValueError("Task not started")  # pragma: nocover

        return self._wait_task

    @staticmethod
    def _run_agent(
        agent_alias: AgentAlias, stop_event: Event, result_queue: multiprocessing.Queue,
    ) -> None:
        """Start an agent in a child process."""
        t: Optional[Thread] = None
        r: Optional[Exception] = None
        run_stop_thread: bool = True
        # set a new event loop, cause it's a new process
        asyncio.set_event_loop(asyncio.new_event_loop())
        try:
            aea = agent_alias.get_aea_instance()

            def stop_event_thread() -> None:
                try:
                    while run_stop_thread:
                        if stop_event.wait(0.01) is True:
                            break
                finally:
                    aea.runtime.stop()

            t = Thread(target=stop_event_thread, daemon=True)
            t.start()
            loop = asyncio.get_event_loop()
            aea.runtime.set_loop(loop)
            aea.start()
        except BaseException as e:  # pylint: disable=broad-except
            print(
                f"Exception in agent subprocess task at {datetime.datetime.now()}:\n{format_exc()}"
            )
            r = Exception(str(e), repr(e))
        finally:
            run_stop_thread = False
            if t:
                t.join(10)

        result_queue.put(r)

    def stop(self) -> None:
        """Stop the task."""
        if not self.process:
            raise ValueError("Task not started!")  # pragma: nocover

        self._stop_event.set()
        self.process.join(self.PROCESS_JOIN_TIMEOUT)
        if self.is_running:  # pragma: nocover
            self.process.terminate()
            self.process.join(5)
            raise ValueError(
                f"process was not stopped within timeout: {self.PROCESS_JOIN_TIMEOUT} and was terminated"
            )

    @property
    def is_running(self) -> bool:
        """Is agent running."""
        if not self.process:
            raise ValueError("Task not started!")  # pragma: nocover

        return self.process.is_alive()


ASYNC_MODE = "async"
THREADED_MODE = "threaded"
MULTIPROCESS_MODE = "multiprocess"


class MultiAgentManager:
    """Multi agents manager."""

    MODES = [ASYNC_MODE, THREADED_MODE, MULTIPROCESS_MODE]
    _MODE_TASK_CLASS = {
        ASYNC_MODE: AgentRunAsyncTask,
        THREADED_MODE: AgentRunThreadTask,
        MULTIPROCESS_MODE: AgentRunProcessTask,
    }
    DEFAULT_TIMEOUT_FOR_BLOCKING_OPERATIONS = 60
    VENV_BUILD_TIMEOUT = 240
    SAVE_FILENAME = "save.json"

    def __init__(
        self,
        working_dir: str,
        mode: str = "async",
        registry_path: str = DEFAULT_REGISTRY_NAME,
        auto_add_remove_project: bool = False,
        password: Optional[str] = None,
    ) -> None:
        """
        Initialize manager.

        :param working_dir: directory to store base agents.
        :param mode: str. async or threaded
        :param registry_path: str. path to the local packages registry
        :param auto_add_remove_project: bool. add/remove project on the first agent add/last agent remove
        :param password: the password to encrypt/decrypt the private key.
        """
        self.working_dir = working_dir
        self._auto_add_remove_project = auto_add_remove_project
        self._save_path = os.path.join(self.working_dir, self.SAVE_FILENAME)

        self.registry_path = registry_path
        self._was_working_dir_created = False
        self._is_running = False
        self._projects: Dict[PublicId, Project] = {}
        self._versionless_projects_set: Set[PublicId] = set()
        self._data_dir = os.path.abspath(
            os.path.join(self.working_dir, AEA_MANAGER_DATA_DIRNAME)
        )
        self._agents: Dict[str, AgentAlias] = {}
        self._agents_tasks: Dict[str, BaseAgentRunTask] = {}

        self._thread: Optional[Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._event: Optional[asyncio.Event] = None

        self._error_callbacks: List[Callable[[str, BaseException], None]] = [
            self._default_error_callback
        ]
        self._custom_callback_added: bool = False
        self._last_start_status: Optional[
            Tuple[
                bool,
                Dict[PublicId, List[Dict]],
                List[Tuple[PublicId, List[Dict], Exception]],
            ]
        ] = None

        if mode not in self.MODES:
            raise ValueError(
                f'Invalid mode {mode}. Valid modes are {", ".join(self.MODES)}'
            )
        self._started_event = threading.Event()
        self._mode = mode
        self._password = password

        # this flags will control whether we have already printed the warning message
        # for a certain agent
        self._warning_message_printed_for_agent: Dict[str, bool] = {}

        # the dictionary keeps track of the AEA packages used across
        # AEA projects in the same MAM.
        # It maps package prefixes to a pair: (version, agent_ids)
        # where agent_ids is the set of agent ids whose projects
        # have the package in the key at the specific version.
        self._package_id_prefix_to_version: Dict[
            PackageIdPrefix, Tuple[str, Set[PublicId]]
        ] = {}

    @property
    def data_dir(self) -> str:
        """Get the certs directory."""
        return self._data_dir

    def get_data_dir_of_agent(self, agent_name: str) -> str:
        """Get the data directory of a specific agent."""
        return os.path.join(self.data_dir, agent_name)

    @property
    def is_running(self) -> bool:
        """Is manager running."""
        return self._is_running

    @property
    def dict_state(self) -> Dict[str, Any]:
        """Create MultiAgentManager dist state."""
        return {
            "projects": [str(public_id) for public_id in self._projects.keys()],
            "agents": [alias.dict for alias in self._agents.values()],
        }

    @property
    def projects(self) -> Dict[PublicId, Project]:
        """Get all projects."""
        return self._projects

    def _run_thread(self) -> None:
        """Run internal thread with own event loop."""
        self._loop = asyncio.new_event_loop()
        self._event = asyncio.Event(loop=self._loop)
        self._loop.run_until_complete(self._manager_loop())

    async def _manager_loop(self) -> None:
        """Await and control running manager."""
        if not self._event:  # pragma: nocover
            raise ValueError("Do not use this method directly, use start_manager.")

        self._started_event.set()

        while self._is_running:
            agents_run_tasks_futures = {
                task.wait(): agent_name
                for agent_name, task in self._agents_tasks.items()
            }
            wait_tasks = list(agents_run_tasks_futures.keys()) + [self._event.wait()]  # type: ignore
            done, _ = await asyncio.wait(wait_tasks, return_when=FIRST_COMPLETED)

            if self._event.is_set():
                self._event.clear()

            for task in done:
                if task not in agents_run_tasks_futures:
                    # task not in agents_run_tasks_futures, so it's event_wait, skip it
                    await task
                    continue

                agent_name = agents_run_tasks_futures[task]
                self._agents_tasks.pop(agent_name)
                if task.exception():
                    for callback in self._error_callbacks:
                        callback(agent_name, task.exception())
                else:
                    await task

    def add_error_callback(
        self, error_callback: Callable[[str, BaseException], None]
    ) -> "MultiAgentManager":
        """Add error callback to call on error raised."""
        if len(self._error_callbacks) == 1 and not self._custom_callback_added:
            # only default callback present, reset before adding new callback
            self._custom_callback_added = True
            self._error_callbacks = []
        self._error_callbacks.append(error_callback)
        return self

    def start_manager(
        self, local: bool = False, remote: bool = False
    ) -> "MultiAgentManager":
        """
        Start manager.

        If local = False and remote = False, then the packages
        are fetched in mixed mode (i.e. first try from local
        registry, and then from remote registry in case of failure).

        :param local: whether or not to fetch from local registry.
        :param remote: whether or not to fetch from remote registry.

        :return: the MultiAgentManager instance.
        """
        if self._is_running:
            return self

        self._ensure_working_dir()
        self._last_start_status = self._load_state(local=local, remote=remote)

        self._started_event.clear()
        self._is_running = True
        self._thread = Thread(target=self._run_thread, daemon=True)
        self._thread.start()
        self._started_event.wait(self.DEFAULT_TIMEOUT_FOR_BLOCKING_OPERATIONS)
        return self

    @property
    def last_start_status(
        self,
    ) -> Tuple[
        bool, Dict[PublicId, List[Dict]], List[Tuple[PublicId, List[Dict], Exception]],
    ]:
        """Get status of the last agents start loading state."""
        if self._last_start_status is None:
            raise ValueError("Manager was not started")
        return self._last_start_status

    def stop_manager(
        self, cleanup: bool = True, save: bool = False
    ) -> "MultiAgentManager":
        """
        Stop manager.

        Stops all running agents and stop agent.

        :param cleanup: bool is cleanup on stop.
        :param save: bool is save state to file on stop.

        :return: None
        """
        if not self._is_running:
            return self

        if not self._loop or not self._event or not self._thread:  # pragma: nocover
            raise ValueError("Manager was not started!")

        if not self._thread.is_alive():  # pragma: nocover
            return self

        self.stop_all_agents()

        if save:
            self._save_state()

        for agent_name in self.list_agents():
            self.remove_agent(agent_name, skip_project_auto_remove=True)

        if cleanup:
            for project in list(self._projects.keys()):
                self.remove_project(project, keep_files=save)
            self._cleanup(only_data=save)

        self._is_running = False

        self._loop.call_soon_threadsafe(self._event.set)

        if self._thread.ident != threading.get_ident():
            self._thread.join(self.DEFAULT_TIMEOUT_FOR_BLOCKING_OPERATIONS)

        self._thread = None
        self._warning_message_printed_for_agent = {}
        return self

    def _cleanup(self, only_data: bool = False) -> None:
        """Remove workdir if was created."""
        if only_data:
            rmtree(self.data_dir)
        else:
            if self._was_working_dir_created and os.path.exists(self.working_dir):
                rmtree(self.working_dir)

    def add_project(
        self,
        public_id: PublicId,
        local: bool = False,
        remote: bool = False,
        restore: bool = False,
    ) -> "MultiAgentManager":
        """
        Fetch agent project and all dependencies to working_dir.

        If local = False and remote = False, then the packages
        are fetched in mixed mode (i.e. first try from local
        registry, and then from remote registry in case of failure).

        :param public_id: the public if of the agent project.
        :param local: whether or not to fetch from local registry.
        :param remote: whether or not to fetch from remote registry.
        :param restore: bool flag for restoring already fetched agent.
        :return: self
        """
        if public_id.to_any() in self._versionless_projects_set:
            raise ValueError(
                f"The project ({public_id.author}/{public_id.name}) was already added!"
            )

        project = Project.load(
            self.working_dir,
            public_id,
            local,
            remote,
            registry_path=self.registry_path,
            is_restore=restore,
            skip_aea_validation=False,
        )

        if not restore:
            self._project_install_and_build(project)

        self._check_version_consistency(project.agent_config)

        try:
            self._check_project(project)
        except Exception as e:
            project.remove()
            raise ProjectCheckError(
                f"Failed to load project: {public_id} Error: {str(e)}", e
            )

        self._add_new_package_versions(project.agent_config)
        self._versionless_projects_set.add(public_id.to_any())
        self._projects[public_id] = project
        return self

    def _project_install_and_build(self, project: Project) -> None:
        """Build and install project dependencies."""
        if self._mode == MULTIPROCESS_MODE:
            venv_dir = get_venv_dir_for_project(project)
            run_in_venv(
                venv_dir, project_install_and_build, self.VENV_BUILD_TIMEOUT, project
            )
        else:
            venv_dir = get_venv_dir_for_project(project)
            project_install_and_build(project)

    def _check_project(self, project: Project) -> None:
        if self._mode == MULTIPROCESS_MODE:
            venv_dir = get_venv_dir_for_project(project)
            run_in_venv(venv_dir, project_check, 120, project)
        else:
            project_check(project)

    def remove_project(
        self, public_id: PublicId, keep_files: bool = False
    ) -> "MultiAgentManager":
        """Remove agent project."""
        if public_id not in self._projects:
            raise ValueError(f"Project {public_id} is not present!")

        if self._projects[public_id].agents:
            raise ValueError(
                f"Can not remove projects with aliases exists: {self._projects[public_id].agents}"
            )

        project = self._projects.pop(public_id)
        self._remove_package_versions(project.agent_config)
        self._versionless_projects_set.remove(public_id.to_any())
        if not keep_files:
            project.remove()

        return self

    def list_projects(self) -> List[PublicId]:
        """
        List all agents projects added.

        :return: list of public ids of projects
        """
        return list(self._projects.keys())

    def add_agent(
        self,
        public_id: PublicId,
        agent_name: Optional[str] = None,
        agent_overrides: Optional[dict] = None,
        component_overrides: Optional[List[dict]] = None,
        local: bool = False,
        remote: bool = False,
        restore: bool = False,
    ) -> "MultiAgentManager":
        """
        Create new agent configuration based on project with config overrides applied.

        Alias is stored in memory only!

        :param public_id: base agent project public id
        :param agent_name: unique name for the agent
        :param agent_overrides: overrides for agent config.
        :param component_overrides: overrides for component section.
        :param local: whether or not to fetch from local registry.
        :param remote: whether or not to fetch from remote registry.
        :param restore: bool flag for restoring already fetched agent.
        :return: self
        """
        agent_name = agent_name or public_id.name

        if agent_name in self._agents:
            raise ValueError(f"Agent with name {agent_name} already exists!")

        project = self._projects.get(public_id, None)

        if project is None and self._auto_add_remove_project:
            self.add_project(public_id, local, remote, restore)
            project = self._projects.get(public_id, None)

        if project is None:
            raise ProjectNotFoundError(f"{public_id} project is not added!")

        agent_alias = AgentAlias(
            project=project,
            agent_name=agent_name,
            data_dir=self.get_data_dir_of_agent(agent_name),
            password=self._password,
        )
        agent_alias.set_overrides(agent_overrides, component_overrides)
        project.agents.add(agent_name)
        self._agents[agent_name] = agent_alias
        return self

    def add_agent_with_config(
        self, public_id: PublicId, config: List[dict], agent_name: Optional[str] = None,
    ) -> "MultiAgentManager":
        """
        Create new agent configuration based on project with config provided.

        Alias is stored in memory only!

        :param public_id: base agent project public id
        :param agent_name: unique name for the agent
        :param config: agent config (used for agent re-creation).

        :return: manager
        """
        agent_name = agent_name or public_id.name

        if agent_name in self._agents:  # pragma: nocover
            raise ValueError(f"Agent with name {agent_name} already exists!")

        if public_id not in self._projects:  # pragma: nocover
            raise ValueError(f"{public_id} project is not added!")

        project = self._projects[public_id]

        agent_alias = AgentAlias(
            project=project,
            agent_name=agent_name,
            data_dir=self.get_data_dir_of_agent(agent_name),
            password=self._password,
        )
        agent_alias.set_agent_config_from_data(config)
        project.agents.add(agent_name)
        self._agents[agent_name] = agent_alias
        return self

    def get_agent_overridables(self, agent_name: str) -> Tuple[Dict, List[Dict]]:
        """
        Get agent config  overridables.

        :param agent_name: str

        :return: Tuple of agent overridables dict and  and list of component overridables dict.
        """
        if agent_name not in self._agents:  # pragma: nocover
            raise ValueError(f"Agent with name {agent_name} does not exist!")

        return self._agents[agent_name].get_overridables()

    def set_agent_overrides(
        self,
        agent_name: str,
        agent_overides: Optional[Dict],
        components_overrides: Optional[List[Dict]],
    ) -> "MultiAgentManager":
        """
        Set agent overrides.

        :param agent_name: str
        :param agent_overides: optional dict of agent config overrides
        :param components_overrides: optional list of dict of components overrides
        :return: self
        """
        if agent_name not in self._agents:  # pragma: nocover
            raise ValueError(f"Agent with name {agent_name} does not exist!")

        if self._is_agent_running(agent_name):  # pragma: nocover
            raise ValueError("Agent is running. stop it first!")

        self._agents[agent_name].set_overrides(agent_overides, components_overrides)
        return self

    def list_agents_info(self) -> List[Dict[str, Any]]:
        """
        List agents detailed info.

        :return: list of dicts that represents agent info: public_id, name, is_running.
        """
        return [
            {
                "agent_name": agent_name,
                "public_id": str(alias.project.public_id),
                "addresses": alias.get_addresses(),
                "is_running": self._is_agent_running(agent_name),
            }
            for agent_name, alias in self._agents.items()
        ]

    def list_agents(self, running_only: bool = False) -> List[str]:
        """
        List all agents.

        :param running_only: returns only running if set to True

        :return: list of agents names
        """
        if running_only:
            return [i for i in self._agents.keys() if self._is_agent_running(i)]
        return list(self._agents.keys())

    def remove_agent(
        self, agent_name: str, skip_project_auto_remove: bool = False
    ) -> "MultiAgentManager":
        """
        Remove agent alias definition from registry.

        :param agent_name: agent name to remove
        :param skip_project_auto_remove: disable auto project remove on last agent removed.

        :return: None
        """
        if agent_name not in self._agents:
            raise ValueError(f"Agent with name {agent_name} does not exist!")

        if self._is_agent_running(agent_name):
            raise ValueError("Agent is running. stop it first!")

        agent_alias = self._agents.pop(agent_name)
        agent_alias.remove_from_project()
        project: Project = agent_alias.project

        if (
            not project.agents
            and self._auto_add_remove_project
            and not skip_project_auto_remove
        ):
            self.remove_project(project.public_id, keep_files=False)

        return self

    def start_agent(self, agent_name: str) -> "MultiAgentManager":
        """
        Start selected agent.

        :param agent_name: agent name to start

        :return: None
        """
        if not self._loop or not self._event:  # pragma: nocover
            raise ValueError("agent is not started!")

        agent_alias = self._agents.get(agent_name)

        if not agent_alias:
            raise ValueError(f"{agent_name} is not registered!")

        if self._is_agent_running(agent_name):
            raise ValueError(f"{agent_name} is already started!")

        task_cls = self._MODE_TASK_CLASS[self._mode]
        if self._mode == MULTIPROCESS_MODE:
            task = task_cls(agent_alias, self._loop)
        else:
            agent = agent_alias.get_aea_instance()
            task = task_cls(agent, self._loop)

        task.start()

        self._agents_tasks[agent_name] = task

        self._loop.call_soon_threadsafe(self._event.set)
        return self

    def _is_agent_running(self, agent_name: str) -> bool:
        """Return is agent task in running state."""
        if agent_name not in self._agents_tasks:
            return False

        task = self._agents_tasks[agent_name]
        return task.is_running

    def start_all_agents(self) -> "MultiAgentManager":
        """
        Start all not started agents.

        :return: None
        """
        self.start_agents(
            [
                agent_name
                for agent_name in self.list_agents()
                if not self._is_agent_running(agent_name)
            ]
        )
        return self

    def stop_agent(self, agent_name: str) -> "MultiAgentManager":
        """
        Stop running agent.

        :param agent_name: agent name to stop

        :return: self
        """
        if not self._is_agent_running(agent_name) or not self._thread or not self._loop:
            raise ValueError(f"{agent_name} is not running!")

        agent_task = self._agents_tasks[agent_name]

        if self._thread.ident == threading.get_ident():  # pragma: nocover
            # In same thread do not perform blocking operations!
            agent_task.stop()
            return self

        wait_future = agent_task.wait()

        event = threading.Event()

        def event_set(*args: Any) -> None:  # pylint: disable=unused-argument
            event.set()

        def _add_cb() -> None:
            if wait_future.done():
                event_set()  # pragma: nocover
            else:
                wait_future.add_done_callback(event_set)  # pragma: nocover

        self._loop.call_soon_threadsafe(_add_cb)
        agent_task.stop()
        event.wait(self.DEFAULT_TIMEOUT_FOR_BLOCKING_OPERATIONS)

        if agent_task.is_running:  # pragma: nocover
            raise ValueError(f"cannot stop task of agent {agent_name}")

        return self

    def stop_all_agents(self) -> "MultiAgentManager":
        """
        Stop all agents running.

        :return: self
        """
        agents_list = self.list_agents(running_only=True)
        self.stop_agents(agents_list)

        return self

    def stop_agents(self, agent_names: List[str]) -> "MultiAgentManager":
        """
        Stop specified agents.

        :param agent_names: names of agents
        :return: self
        """
        for agent_name in agent_names:
            if not self._is_agent_running(agent_name):
                raise ValueError(f"{agent_name} is not running!")

        for agent_name in agent_names:
            self.stop_agent(agent_name)

        return self

    def start_agents(self, agent_names: List[str]) -> "MultiAgentManager":
        """
        Stop specified agents.

        :param agent_names: names of agents
        :return: self
        """
        for agent_name in agent_names:
            self.start_agent(agent_name)

        return self

    def get_agent_alias(self, agent_name: str) -> AgentAlias:
        """
        Return details about agent alias definition.

        :param agent_name: name of agent
        :return: AgentAlias
        """
        if agent_name not in self._agents:  # pragma: nocover
            raise ValueError(f"Agent with name {agent_name} does not exist!")
        return self._agents[agent_name]

    def _ensure_working_dir(self) -> None:
        """Create working dir if needed."""
        if not os.path.exists(self.working_dir):
            os.makedirs(self.working_dir)
            self._was_working_dir_created = True

        if not os.path.isdir(self.working_dir):  # pragma: nocover
            raise ValueError(f"{self.working_dir} is not a directory!")
        if not os.path.exists(self.data_dir):
            os.makedirs(self.data_dir)

    def _load_state(
        self, local: bool, remote: bool
    ) -> Tuple[
        bool, Dict[PublicId, List[Dict]], List[Tuple[PublicId, List[Dict], Exception]],
    ]:
        """
        Load saved state from file.

        Fetch agent project and all dependencies to working_dir.

        If local = False and remote = False, then the packages
        are fetched in mixed mode (i.e. first try from local
        registry, and then from remote registry in case of failure).

        :param local: whether or not to fetch from local registry.
        :param remote: whether or not to fetch from remote registry.

        :return: Tuple of bool indicating load success, settings of loaded, list of failed
        :raises: ValueError if failed to load state.
        """
        if not os.path.exists(self._save_path):
            return False, {}, []

        save_json = {}
        with open_file(self._save_path) as f:
            save_json = json.load(f)

        if not save_json:
            return False, {}, []  # pragma: nocover

        projects_agents: Dict[PublicId, List] = defaultdict(list)

        for agent_settings in save_json["agents"]:
            projects_agents[PublicId.from_str(agent_settings["public_id"])].append(
                agent_settings
            )

        failed_to_load: List[Tuple[PublicId, List[Dict], Exception]] = []
        loaded_ok: Dict[PublicId, List[Dict]] = {}
        for project_public_id, agents_settings in projects_agents.items():
            try:
                self.add_project(
                    project_public_id, local=local, remote=remote, restore=True,
                )
            except ProjectCheckError as e:
                failed_to_load.append((project_public_id, agents_settings, e))
                break

            for agent_settings in agents_settings:
                self.add_agent_with_config(
                    public_id=PublicId.from_str(agent_settings["public_id"]),
                    agent_name=agent_settings["agent_name"],
                    config=agent_settings["config"],
                )

            loaded_ok[project_public_id] = agents_settings

        return True, loaded_ok, failed_to_load

    def _save_state(self) -> None:
        """Save MultiAgentManager state."""
        with open_file(self._save_path, "w") as f:
            json.dump(self.dict_state, f, indent=4, sort_keys=True)

    def _default_error_callback(
        self, agent_name: str, exception: BaseException
    ) -> None:
        """
        Handle errors from running agents.

        This is the default error callback. To replace it
        with another one, use the method 'add_error_callback'.

        :param agent_name: the agent name
        :param exception: the caught exception
        """
        self._print_exception_occurred_but_no_error_callback(agent_name, exception)

    def _print_exception_occurred_but_no_error_callback(
        self, agent_name: str, exception: BaseException
    ) -> None:
        """
        Print a warning message when an exception occurred but no error callback is registered.

        :param agent_name: the agent name.
        :param exception: the caught exception.
        """
        if self._warning_message_printed_for_agent.get(agent_name, False):
            return  # pragma: nocover
        self._warning_message_printed_for_agent[agent_name] = True
        print(
            f"WARNING: An exception occurred during the execution of agent '{agent_name}':\n",
            str(exception),
            repr(exception),
            "\nHowever, since no error callback was found the exception is handled silently. Please "
            "add an error callback using the method 'add_error_callback' of the MultiAgentManager instance.",
        )

    def _check_version_consistency(self, agent_config: AgentConfig) -> None:
        """
        Check that the agent dependencies in input are consistent with the other projects.

        :param agent_config: the agent configuration we are going to add.
        :return: None
        :raises ProjectPackageConsistencyCheckError: if a version conflict is detected.
        """
        existing_packages = set(self._package_id_prefix_to_version.keys())
        prefix_to_version = {
            component_id.component_prefix: component_id.version
            for component_id in agent_config.package_dependencies
        }
        component_prefixes_to_be_added = set(prefix_to_version.keys())

        potentially_conflicting_packages = existing_packages.intersection(
            component_prefixes_to_be_added
        )
        if len(potentially_conflicting_packages) == 0:
            return

        # conflicting_packages is a list of tuples whose elements are:
        # - package id prefix: the triple (component type, author, name)
        # - current_version: the version currently present in the MAM, across all projects
        # - new_version: the version of the package in the new project
        # - agents: the set of agents in the MAM that have the package;
        #           used to provide a better error message
        conflicting_packages: List[Tuple[PackageIdPrefix, str, str, Set[PublicId]]] = []
        for package_prefix in potentially_conflicting_packages:
            existing_version, agents = self._package_id_prefix_to_version[
                package_prefix
            ]
            new_version = prefix_to_version[package_prefix]
            if existing_version != new_version:
                conflicting_packages.append(
                    (package_prefix, existing_version, new_version, agents)
                )

        if len(conflicting_packages) == 0:
            return

        raise ProjectPackageConsistencyCheckError(
            agent_config.public_id, conflicting_packages
        )

    def _add_new_package_versions(self, agent_config: AgentConfig) -> None:
        """
        Add new package versions.

        This method is called whenever a project agent is added.
        It updates an internal data structure that it is used to
        check inconsistencies of AEA package versions across projects.
        In particular, all the AEA packages with the same "prefix" must
        be of the same version.

        :param agent_config: the agent configuration.
        """
        for component_id in agent_config.package_dependencies:
            if component_id.component_prefix not in self._package_id_prefix_to_version:
                self._package_id_prefix_to_version[component_id.component_prefix] = (
                    component_id.version,
                    set(),
                )
            version, agents = self._package_id_prefix_to_version[
                component_id.component_prefix
            ]
            enforce(
                version == component_id.version,
                f"internal consistency error: expected version '{version}', found {component_id.version}",
            )
            agents.add(agent_config.public_id)

    def _remove_package_versions(self, agent_config: AgentConfig) -> None:
        """
        Remove package versions.

        This method is called whenever a project agent is removed.
        It updates an internal data structure that it is used to
        check inconsistencies of AEA package versions across projects.
        In particular, all the AEA packages with the same "prefix" must
        be of the same version.

        :param agent_config: the agent configuration.
        """
        package_prefix_to_remove = set()
        for (
            package_prefix,
            (_version, agents),
        ) in self._package_id_prefix_to_version.items():
            if agent_config.public_id in agents:
                agents.remove(agent_config.public_id)
                if len(agents) == 0:
                    package_prefix_to_remove.add(package_prefix)

        for package_prefix in package_prefix_to_remove:
            self._package_id_prefix_to_version.pop(package_prefix)
