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
import json
import os
import threading
from asyncio.tasks import FIRST_COMPLETED
from collections import defaultdict
from shutil import rmtree
from threading import Thread
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from aea.aea import AEA
from aea.configurations.constants import AEA_MANAGER_DATA_DIRNAME, DEFAULT_REGISTRY_NAME
from aea.configurations.data_types import PublicId
from aea.helpers.io import open_file
from aea.manager.project import AgentAlias, Project


class ProjectNotFoundError(ValueError):
    """Project not found exception."""


class ProjectCheckError(ValueError):
    """Project check error exception."""

    def __init__(self, msg: str, source_exception: Exception):
        """Init exception."""
        super().__init__(msg)
        self.source_exception = source_exception


class AgentRunAsyncTask:
    """Async task wrapper for agent."""

    def __init__(self, agent: AEA, loop: asyncio.AbstractEventLoop) -> None:
        """Init task with agent and loop."""
        self.run_loop: asyncio.AbstractEventLoop = loop
        self.caller_loop: asyncio.AbstractEventLoop = loop
        self._done_future: Optional[asyncio.Future] = None
        self.task: Optional[asyncio.Task] = None
        self.agent = agent

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
        """Init task with agent and loop."""
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


class MultiAgentManager:
    """Multi agents manager."""

    MODES = ["async", "threaded"]
    DEFAULT_TIMEOUT_FOR_BLOCKING_OPERATIONS = 60
    SAVE_FILENAME = "save.json"

    def __init__(
        self,
        working_dir: str,
        mode: str = "async",
        registry_path: str = DEFAULT_REGISTRY_NAME,
        auto_add_remove_project: bool = False,
    ) -> None:
        """
        Initialize manager.

        :param working_dir: directory to store base agents.
        :param mode: str. async or threaded
        :param registry_path: str. path to the local packages registry
        :param auto_add_remove_project: bool. add/remove project on the first agent add/last agent remove

        :return: None
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
        self._agents_tasks: Dict[str, AgentRunAsyncTask] = {}

        self._thread: Optional[Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._event: Optional[asyncio.Event] = None

        self._error_callbacks: List[Callable[[str, BaseException], None]] = []
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
    ) -> None:
        """Add error callback to call on error raised."""
        self._error_callbacks.append(error_callback)

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
        """
        if public_id.to_any() in self._versionless_projects_set:
            raise ValueError(
                f"The project ({public_id.author}/{public_id.name}) was already added!"
            )

        self._versionless_projects_set.add(public_id.to_any())

        project = Project.load(
            self.working_dir,
            public_id,
            local,
            remote,
            registry_path=self.registry_path,
            is_restore=restore,
        )

        if not restore:
            project.install_pypi_dependencies()
            project.build()

        try:
            project.check()
        except Exception as e:
            project.remove()
            raise ProjectCheckError(
                f"Failed to load project: {public_id} Error: {str(e)}", e
            )

        self._projects[public_id] = project
        return self

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
        :param config: agent config (used for agent re-creation).

        :param local: whether or not to fetch from local registry.
        :param remote: whether or not to fetch from remote registry.
        :param restore: bool flag for restoring already fetched agent.

        :return: manager
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
    ) -> None:
        """
        Set agent overrides.

        :param agent_name: str
        :param agent_overides: optional dict of agent config overrides
        :param components_overrides: optional list of dict of components overrides

        :return: None
        """
        if agent_name not in self._agents:  # pragma: nocover
            raise ValueError(f"Agent with name {agent_name} does not exist!")

        if self._is_agent_running(agent_name):  # pragma: nocover
            raise ValueError("Agent is running. stop it first!")

        self._agents[agent_name].set_overrides(agent_overides, components_overrides)

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

        aea = agent_alias.get_aea_instance()

        if self._mode == "async":
            task = AgentRunAsyncTask(aea, self._loop)
        elif self._mode == "threaded":
            task = AgentRunThreadTask(aea, self._loop)

        task.start()
        self._agents_tasks[agent_name] = task
        self._loop.call_soon_threadsafe(self._event.set)
        return self

    def _is_agent_running(self, agent_name: str) -> bool:
        """Return is agent running state."""
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

        :return: None
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
                wait_future.add_done_callback(event_set)  # pramga: nocover

        self._loop.call_soon_threadsafe(_add_cb)
        agent_task.stop()
        event.wait(self.DEFAULT_TIMEOUT_FOR_BLOCKING_OPERATIONS)

        return self

    def stop_all_agents(self) -> "MultiAgentManager":
        """
        Stop all agents running.

        :return: None
        """
        agents_list = self.list_agents(running_only=True)
        self.stop_agents(agents_list)

        return self

    def stop_agents(self, agent_names: List[str]) -> "MultiAgentManager":
        """
        Stop specified agents.

        :return: None
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

        :return: None
        """
        for agent_name in agent_names:
            self.start_agent(agent_name)

        return self

    def get_agent_alias(self, agent_name: str) -> AgentAlias:
        """
        Return details about agent alias definition.

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

        :return: None
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
        """
        Save MultiAgentManager state.

        :return: None.
        """
        with open_file(self._save_path, "w") as f:
            json.dump(self.dict_state, f, indent=4, sort_keys=True)
