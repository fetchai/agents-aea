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
import copy
import json
import os
import threading
from asyncio.tasks import FIRST_COMPLETED
from pathlib import Path
from shutil import rmtree
from threading import Thread
from typing import Any, Callable, Dict, List, Optional

from aea.aea import AEA
from aea.aea_builder import AEABuilder
from aea.configurations.base import AgentConfig, ComponentId, PackageType, PublicId
from aea.configurations.constants import (
    CONNECTIONS,
    CONTRACTS,
    DEFAULT_LEDGER,
    DEFAULT_REGISTRY_NAME,
    PROTOCOLS,
    SKILLS,
)
from aea.configurations.loader import ConfigLoaders
from aea.configurations.project import AgentAlias, Project
from aea.crypto.helpers import create_private_key


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


class MultiAgentManager:
    """Multi agents manager."""

    AGENT_DO_NOT_OVERRIDE_VALUES = [CONNECTIONS, CONTRACTS, PROTOCOLS, SKILLS]
    MODES = ["async", "threaded"]
    DEFAULT_TIMEOUT_FOR_BLOCKING_OPERATIONS = 60
    SAVE_FILENAME = "save.json"

    def __init__(
        self,
        working_dir: str,
        mode: str = "async",
        registry_path: str = DEFAULT_REGISTRY_NAME,
    ) -> None:
        """
        Initialize manager.

        :param working_dir: directory to store base agents.
        """
        self.working_dir = working_dir
        self._save_path = os.path.join(self.working_dir, self.SAVE_FILENAME)

        self.registry_path = registry_path
        self._was_working_dir_created = False
        self._is_running = False
        self._projects: Dict[PublicId, Project] = {}
        self._keys_dir = os.path.abspath(os.path.join(self.working_dir, "keys"))
        self._agents: Dict[str, AgentAlias] = {}
        self._agents_tasks: Dict[str, AgentRunAsyncTask] = {}

        self._thread: Optional[Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._event: Optional[asyncio.Event] = None

        self._error_callbacks: List[Callable[[str, BaseException], None]] = []

        if mode not in self.MODES:
            raise ValueError(
                f'Invalid mode {mode}. Valid modes are {", ".join(self.MODES)}'
            )
        self._started_event = threading.Event()
        self._mode = mode

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
        if not self._event:
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

    def start_manager(self, local: bool = True) -> "MultiAgentManager":
        """Start manager."""
        if self._is_running:
            return self

        self._ensure_working_dir()
        self._load_state(local=local)

        self._started_event.clear()
        self._is_running = True
        self._thread = Thread(target=self._run_thread, daemon=True)
        self._thread.start()
        self._started_event.wait(self.DEFAULT_TIMEOUT_FOR_BLOCKING_OPERATIONS)
        return self

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
            self.remove_agent(agent_name)

        if cleanup:
            for project in list(self._projects.keys()):
                self.remove_project(project, keep_files=save)
            self._cleanup(only_keys=save)

        self._is_running = False

        self._loop.call_soon_threadsafe(self._event.set)

        if self._thread.ident != threading.get_ident():
            self._thread.join(self.DEFAULT_TIMEOUT_FOR_BLOCKING_OPERATIONS)

        self._thread = None
        return self

    def _cleanup(self, only_keys: bool = False) -> None:
        """Remove workdir if was created."""
        if only_keys:
            rmtree(self._keys_dir)
        else:
            if self._was_working_dir_created and os.path.exists(self.working_dir):
                rmtree(self.working_dir)

    def add_project(
        self, public_id: PublicId, local: bool = True, restore: bool = False
    ) -> "MultiAgentManager":
        """
        Fetch agent project and all dependencies to working_dir.

        :param public_id: the public if of the agent project.
        :param local: whether or not to fetch from local registry.
        :param restore: bool flag for restoring already fetched agent.
        """
        if public_id in self._projects:
            raise ValueError(f"Project {public_id} was already added!")
        self._projects[public_id] = Project.load(
            self.working_dir,
            public_id,
            local,
            registry_path=self.registry_path,
            is_restore=restore,
        )
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
        if not keep_files:
            project.remove()

        return self

    def list_projects(self) -> List[PublicId]:
        """
        List all agents projects added.

        :return: lit of public ids of projects
        """
        return list(self._projects.keys())

    def add_agent(
        self,
        public_id: PublicId,
        agent_name: Optional[str] = None,
        agent_overrides: Optional[dict] = None,
        component_overrides: Optional[List[dict]] = None,
        config: Optional[List[dict]] = None,
    ) -> "MultiAgentManager":
        """
        Create new agent configuration based on project with config overrides applied.

        Alias is stored in memory only!

        :param public_id: base agent project public id
        :param agent_name: unique name for the agent
        :param agent_overrides: overrides for agent config.
        :param component_overrides: overrides for component section.
        :param config: agent config (used for agent re-creation).

        :return: manager
        """
        if any((agent_overrides, component_overrides)) and config is not None:
            raise ValueError(  # pragma: nocover
                "Can not add agent with overrides and full config."
                "One of those must be used."
            )

        agent_name = agent_name or public_id.name

        if agent_name in self._agents:
            raise ValueError(f"Agent with name {agent_name} already exists!")

        if public_id not in self._projects:
            raise ValueError(f"{public_id} project is not added!")

        project = self._projects[public_id]

        agent_alias = self._build_agent_alias(
            project=project,
            agent_name=agent_name,
            agent_overrides=agent_overrides,
            component_overrides=component_overrides,
            config=config,
        )
        self._agents[agent_name] = agent_alias
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

    def remove_agent(self, agent_name: str) -> "MultiAgentManager":
        """
        Remove agent alias definition from registry.

        :param agent_name: agent name to remove

        :return: None
        """
        if agent_name not in self._agents:
            raise ValueError(f"Agent with name {agent_name} does not exist!")

        if self._is_agent_running(agent_name):
            raise ValueError("Agent is running. stop it first!")

        agent_alias = self._agents.pop(agent_name)
        agent_alias.remove_from_project()
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

        if self._mode == "async":
            task = AgentRunAsyncTask(agent_alias.agent, self._loop)
        elif self._mode == "threaded":
            task = AgentRunThreadTask(agent_alias.agent, self._loop)

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

        def event_set(*args):  # pylint: disable=unused-argument
            event.set()

        def _add_cb():
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
        if not os.path.exists(self._keys_dir):
            os.makedirs(self._keys_dir)

    def _build_agent_alias(
        self,
        project: Project,
        agent_name: str,
        agent_overrides: Optional[dict] = None,
        component_overrides: Optional[List[dict]] = None,
        config: Optional[List[dict]] = None,
    ) -> AgentAlias:
        """Create agent alias for project, with given name and overrided values."""
        if not config:
            config = self._make_config(
                project.path, agent_overrides, component_overrides
            )

        builder = AEABuilder.from_config_json(config, project.path)
        builder.set_name(agent_name)
        builder.set_runtime_mode("threaded")

        if not builder.private_key_paths:
            default_ledger = config[0].get("default_ledger", DEFAULT_LEDGER)
            builder.add_private_key(
                default_ledger, self._create_private_key(agent_name, default_ledger)
            )
        agent = builder.build()
        return AgentAlias(project, agent_name, config, agent, builder)

    def install_pypi_dependencies(self) -> None:
        """Install dependencies for every project has at least one agent alias."""
        for project in self._projects.values():
            self._install_pypi_dependencies_for_project(project)

    def _install_pypi_dependencies_for_project(self, project: Project) -> None:
        """Install dependencies for project specified if has at least one agent alias."""
        if not project.agents:
            return
        self._install_pypi_dependencies_for_agent(list(project.agents)[0])

    def _install_pypi_dependencies_for_agent(self, agent_name: str) -> None:
        """Install dependencies for the agent registered."""
        self._agents[agent_name].builder.install_pypi_dependencies()

    def _make_config(
        self,
        project_path: str,
        agent_overrides: Optional[dict] = None,
        component_overrides: Optional[List[dict]] = None,
    ) -> List[dict]:
        """Make new config based on project's config with overrides applied."""
        agent_overrides = agent_overrides or {}
        component_overrides = component_overrides or []

        if any([key in agent_overrides for key in self.AGENT_DO_NOT_OVERRIDE_VALUES]):
            raise ValueError(
                'Do not override any of {" ".join(self.AGENT_DO_NOT_OVERRIDE_VALUES)}'
            )

        agent_configuration_file_path: Path = AEABuilder.get_configuration_file_path(
            project_path
        )
        loader = ConfigLoaders.from_package_type(PackageType.AGENT)
        with agent_configuration_file_path.open() as fp:
            agent_config: AgentConfig = loader.load(fp)

        # prepare configuration overrides
        # - agent part
        agent_update_dictionary: Dict = dict(**agent_overrides)
        # - components part
        components_configs: Dict[ComponentId, Dict] = {}
        for obj in component_overrides:
            obj = copy.copy(obj)
            author, name, version = (
                obj.pop("author"),
                obj.pop("name"),
                obj.pop("version"),
            )
            component_id = ComponentId(obj.pop("type"), PublicId(author, name, version))
            components_configs[component_id] = obj
        agent_update_dictionary["component_configurations"] = components_configs
        # do the override (and valiation)
        agent_config.update(agent_update_dictionary)

        # return the multi-paged JSON object.
        json_data = agent_config.ordered_json
        result: List[Dict] = [json_data] + json_data.pop("component_configurations")
        return result

    def _create_private_key(self, name, ledger) -> str:
        """Create new key for agent alias in working dir keys dir."""
        path = os.path.join(self._keys_dir, f"{name}_{ledger}_private.key")
        create_private_key(ledger, path)
        return path

    def _load_state(self, local: bool) -> None:
        """
        Load saved state from file.

        :param local: bool is local project and agents re-creation.

        :return: None
        :raises: ValueError if failed to load state.
        """
        if not os.path.exists(self._save_path):
            return

        save_json = {}
        with open(self._save_path) as f:
            save_json = json.load(f)

        if not save_json:
            return  # pragma: nocover

        try:
            for public_id in save_json["projects"]:
                self.add_project(
                    PublicId.from_str(public_id), local=local, restore=True
                )

            for agent_settings in save_json["agents"]:
                self.add_agent(
                    public_id=PublicId.from_str(agent_settings["public_id"]),
                    agent_name=agent_settings["agent_name"],
                    config=agent_settings["config"],
                )
        except ValueError as e:  # pragma: nocover
            raise ValueError(f"Failed to load state. {e}")

    def _save_state(self) -> None:
        """
        Save MultiAgentManager state.

        :return: None.
        """
        with open(self._save_path, "w") as f:
            json.dump(self.dict_state, f, indent=4, sort_keys=True)
