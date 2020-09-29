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
import os
import threading
from asyncio.tasks import FIRST_COMPLETED
from shutil import rmtree
from threading import Thread
from typing import Callable, Dict, List, Optional

from aea.aea import AEA
from aea.aea_builder import AEABuilder
from aea.configurations.base import ComponentId, PublicId
from aea.configurations.constants import DEFAULT_LEDGER
from aea.configurations.project import Project
from aea.crypto.helpers import create_private_key
from aea.helpers.base import yaml_load_all


class AgentAlias:
    """Agent alias representation."""

    def __init__(self, project: Project, name: str, config: List[Dict], agent: AEA):
        """Init agent alias with project, config, name, agent."""
        self.project = project
        self.config = config
        self.name = name
        self.agent = agent
        self.project.agents.add(self.name)

    def remove(self):
        """Remove agent alias from project."""
        self.project.agents.remove(self.name)


class AsyncTask:
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
        pass

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
        if not self._done_future:  # pragma: nocover
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


class ThreadedTask(AsyncTask):
    """Threaded task."""

    def __init__(self, agent: AEA, loop: asyncio.AbstractEventLoop) -> None:
        """Init task with agent and loop."""
        AsyncTask.__init__(self, agent, loop)
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


class Manager:
    """Abstract agents manager."""

    AGENT_DO_NOT_OVERRIDE_VALUES = ["skills", "connections", "protocols", "contracts"]
    MODES = ["async", "threaded"]
    DEFALUT_TIMEOUT_FOR_BLOCKING_OPERATIONS = 60

    def __init__(self, working_dir: str, mode: str = "async") -> None:
        """
        Initialize manager.

        :param working_dir: directory to store base agents.
        """
        self.working_dir = working_dir
        self._was_working_dir_created = False
        self._is_running = False
        self._projects: Dict[PublicId, Project] = {}
        self._keys_dir = os.path.abspath(os.path.join(self.working_dir, "keys"))
        self._agents: Dict[str, AgentAlias] = {}
        self._agents_tasks: Dict[str, AsyncTask] = {}

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

    def _run_thread(self) -> None:
        """Run internal thread with own event loop."""
        self._loop = asyncio.new_event_loop()
        self._event = asyncio.Event(loop=self._loop)
        self._loop.run_until_complete(self._manager_loop())

    async def _manager_loop(self) -> None:
        """Perform manager stop."""
        if not self._event:
            raise ValueError("Do not use this method directly, use start_manager.")

        self._started_event.set()

        while self._is_running:
            tasks_for_agents = {
                task.wait(): agent_name
                for agent_name, task in self._agents_tasks.items()
            }
            wait_tasks = list(tasks_for_agents.keys()) + [self._event.wait()]  # type: ignore
            done, _ = await asyncio.wait(wait_tasks, return_when=FIRST_COMPLETED)

            if self._event.is_set():
                self._event.clear()

            for task in done:
                if task not in tasks_for_agents:
                    await task
                    continue
                agent_name = tasks_for_agents[task]
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

    def start_manager(self) -> "Manager":
        """Start manager."""
        if self._is_running:
            return self

        self._ensure_working_dir()
        self._started_event.clear()
        self._is_running = True
        self._thread = Thread(target=self._run_thread, daemon=True)
        self._thread.start()
        self._started_event.wait(self.DEFALUT_TIMEOUT_FOR_BLOCKING_OPERATIONS)
        return self

    def stop_manager(self) -> "Manager":
        """
        Stop manager.

        Stops all running agents and stop agent.

        :return: None
        """
        if not self._is_running:
            return self

        if not self._loop or not self._event or not self._thread:  # pragma: nocover
            raise ValueError("Manager was not started!")

        if not self._thread.is_alive():  # pragma: nocover
            return self

        self.stop_all_agents()

        for agent_name in self.list_agents():
            self.remove_agent(agent_name)

        for project in list(self._projects.keys()):
            self.remove_project(project)

        self._cleanup()

        self._is_running = False

        self._loop.call_soon_threadsafe(self._event.set)

        if self._thread.ident != threading.get_ident():
            self._thread.join(self.DEFALUT_TIMEOUT_FOR_BLOCKING_OPERATIONS)

        self._thread = None
        return self

    def _cleanup(self) -> None:
        """Remove workdir if was created."""
        if self._was_working_dir_created and os.path.exists(self.working_dir):
            rmtree(self.working_dir)

    def add_project(self, public_id: PublicId) -> "Manager":
        """Fetch agent project and all dependencies to working_dir."""
        if public_id in self._projects:
            raise ValueError(f"Project {public_id} was already added!")
        self._projects[public_id] = Project.load(self.working_dir, public_id)
        return self

    def remove_project(self, public_id: PublicId) -> "Manager":
        """Remove agent project."""
        if public_id not in self._projects:
            raise ValueError(f"Project {public_id} was not added!")

        if self._projects[public_id].agents:
            raise ValueError(
                f"Can not remove projects with aliases exists: {self._projects[public_id].agents}"
            )

        self._projects.pop(public_id).remove()
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
        agent_name: str,
        agent_overrides: Optional[dict] = None,
        component_overrides: Optional[List[dict]] = None,
    ) -> "Manager":
        """
        Create new agent configuration based on project with config overrides applied.

        Alias is stored in memory only!

        :param public_id: base agent project public id
        :param agent_name: unique name for the agent
        :param agent_overrides: overrides for agent config.
        :param component_overrides: overrides for component section.

        :return: manager
        """
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
        )
        self._agents[agent_name] = agent_alias
        return self

    def list_agents(self, running_only: bool = False) -> List[str]:
        """
        List all agents.

        :param running_only: returns only running if set to True

        :return: list of agents names
        """
        if running_only:
            return [i for i in self._agents.keys() if self._is_agent_running(i)]
        return list(self._agents.keys())

    def remove_agent(self, agent_name: str) -> "Manager":
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
        agent_alias.remove()
        return self

    def start_agent(self, agent_name: str) -> "Manager":
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
            task = AsyncTask(agent_alias.agent, self._loop)
        elif self._mode == "threaded":
            task = ThreadedTask(agent_alias.agent, self._loop)

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

    def start_all_agents(self) -> "Manager":
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

    def stop_agent(self, agent_name: str) -> "Manager":
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
        event.wait(self.DEFALUT_TIMEOUT_FOR_BLOCKING_OPERATIONS)

        return self

    def stop_all_agents(self) -> "Manager":
        """
        Stop all agents running.

        :return: None
        """
        agents_list = self.list_agents(running_only=True)
        self.stop_agents(agents_list)

        return self

    def stop_agents(self, agent_names: List[str]) -> "Manager":
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

    def start_agents(self, agent_names: List[str]) -> "Manager":
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
        os.makedirs(self._keys_dir)

    def _build_agent_alias(
        self,
        project: Project,
        agent_name: str,
        agent_overrides=None,
        component_overrides=None,
    ) -> AgentAlias:
        """Create agent alias for project, with given name and overrided values."""
        json_config = self._make_config(
            project.path, agent_overrides, component_overrides
        )

        builder = AEABuilder.from_config_json(json_config, project.path)
        builder.set_name(agent_name)
        builder.set_runtime_mode("threaded")

        if not builder.private_key_paths:
            default_ledger = json_config[0].get("default_ledger", DEFAULT_LEDGER)
            builder.add_private_key(
                default_ledger, self._create_private_key(agent_name, default_ledger)
            )
        agent = builder.build()
        return AgentAlias(project, agent_name, json_config, agent)

    @staticmethod
    def _update_dict(base: dict, override: dict) -> dict:
        """Apply overrides for dict."""
        base = copy.deepcopy(base)
        base.update(override)
        return base

    def _make_config(
        self,
        project_path: str,
        agent_overrides: Optional[dict] = None,
        component_overrides: Optional[List[dict]] = None,
    ) -> List[dict]:
        """Make new config baseed on proejct's config with overrides applied."""
        agent_overrides = agent_overrides or {}
        component_overrides = component_overrides or []

        if any([key in agent_overrides for key in self.AGENT_DO_NOT_OVERRIDE_VALUES]):
            raise ValueError(
                'Do not override any of {" ".join(self.AGENT_DO_NOT_OVERRIDE_VALUES)}'
            )

        json_data = yaml_load_all(
            AEABuilder.get_configuration_file_path(project_path).open()
        )
        agent_config = self._update_dict(json_data[0], agent_overrides)

        components_configs = {PublicId.from_json(obj): obj for obj in json_data[1:]}

        for obj in component_overrides:
            component_id = ComponentId(obj["type"], PublicId.from_json(obj))
            components_configs[component_id] = self._update_dict(
                components_configs.get(component_id, {}), obj
            )

        return [agent_config] + list(components_configs.values())

    def _create_private_key(self, name, ledger) -> str:
        """Create new key for agent alias in working dir keys dir."""
        path = os.path.join(self._keys_dir, f"{name}_{ledger}_private.key")
        create_private_key(ledger, path)
        return path
