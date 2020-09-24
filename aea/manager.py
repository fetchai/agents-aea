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
import copy
import os
from shutil import rmtree
from typing import Dict, List, Optional, Set

from aea.aea import AEA
from aea.aea_builder import AEABuilder
from aea.cli.registry.fetch import fetch_agent
from aea.cli.utils.context import Context
from aea.configurations.base import ComponentId, PublicId
from aea.configurations.constants import DEFAULT_LEDGER
from aea.crypto.helpers import create_private_key
from aea.helpers.base import yaml_load_all


class Project:
    """Agent project representation."""

    def __init__(self, public_id: PublicId, path: str):
        """Init project with public_id and project's path."""
        self.public_id = public_id
        self.path = path
        self.agents: Set[str] = set()

    @classmethod
    def load(cls, working_dir, public_id) -> "Project":
        """Load project with given pubblic_id to working_dir."""
        ctx = Context(cwd=working_dir)
        path = os.path.join(working_dir, public_id.author, public_id.name)
        fetch_agent(ctx, public_id, dir=os.path.join(public_id.author, public_id.name))
        return cls(public_id, path)

    def remove(self):
        """Remove project, do cleanup."""
        rmtree(self.path)


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


class Manager:
    """Abstract agents manager."""

    AGENT_DO_NOT_OVERRIDE_VALUES = ["skills", "connections", "protocols", "contracts"]

    def __init__(self, working_dir: str) -> None:
        """
        Initialize manager.

        :param working_dir: directory to store base agents.
        """
        self.working_dir = working_dir
        self._was_working_dir_created = False
        self.is_started = False
        self._projects: Dict[PublicId, Project] = {}
        self._keys_dir = os.path.abspath(os.path.join(self.working_dir, "keys"))
        self._agents: Dict[str, AgentAlias] = {}

    def start_manager(self) -> None:
        """Start manager."""
        self._ensure_working_dir()
        self.is_started = True

    def stop_manager(self, cleanup: bool = False) -> None:
        """
        Stop manager.

        Stops all running agents and stop agent.

        :param cleanup: remove agents_dir and purge in memory registry.

        :return: None
        """
        if self._was_working_dir_created:
            rmtree(self.working_dir)

        self.is_started = False

    def add_project(self, public_id: PublicId) -> None:
        """Fetch agent project and all dependencies to working_dir."""
        if public_id in self._projects:
            raise ValueError(f"Project {public_id} was already added!")
        self._projects[public_id] = Project.load(self.working_dir, public_id)

    def remove_project(self, public_id: PublicId) -> None:
        """Remove agent project."""
        if public_id not in self._projects:
            raise ValueError(f"Project {public_id} was not added!")

        self._projects.pop(public_id).remove()

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
    ) -> None:
        """
        Create new agent configuration based on project with config overrides applied.

        Alias is stored in memory only!

        :param public_id: base agent project public id
        :param agent_name: unique name for the agent
        :param agent_overrides: overrides for agent config.
        :param component_overrides: overrides for component section.

        :return: None
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

    def list_agents(self, running_only: bool = False) -> List[str]:
        """
        List all agents.

        :param running_only: returns only running if set to True

        :return: list of agents names
        """
        return list(self._agents.keys())

    def remove_agent(self, agent_name: str) -> None:
        """
        Remove agent alias definition from registry.

        :param agent_name: agent name to remove

        :return: None
        """
        if agent_name not in self._agents:
            raise ValueError(f"Agent with name {agent_name} does not exist!")

        agent_alias = self._agents.pop(agent_name)
        agent_alias.remove()

    def start_agent(self, agent_name: str) -> None:
        """
        Start selected agent.

        :param agent_name: agent name to start

        :return: None
        """

    def start_all_agents(self) -> None:
        """
        Start all not started agents.

        :return: None
        """

    def stop_agent(self, agent_name: str) -> None:
        """
        Stop running agent.

        :param agent_name: agent name to stop

        :return: None
        """

    def stop_all_agents(self) -> None:
        """
        Stop all agents running.

        :return: None
        """

    def stop_agents(self, agent_names: List[str]) -> None:
        """
        Stop specified agents.

        :return: None
        """

    def start_agents(self, agent_names: List[str]) -> None:
        """
        Stop specified agents.

        :return: None
        """

    def get_agent_details(self, agent_name: str) -> AgentAlias:
        """
        Return details about agent definition.

        :return: AgentAlias
        """
        if agent_name not in self._agents:
            raise ValueError(f"Agent with name {agent_name} does not exist!")
        return self._agents[agent_name]

    def _ensure_working_dir(self) -> None:
        """Create working dir if needed."""
        if not os.path.exists(self.working_dir):
            os.makedirs(self.working_dir)
            self._was_working_dir_created = True

        if not os.path.isdir(self.working_dir):
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

        if not builder.private_key_paths:
            default_ledger = json_config[0].get("default_ledger", DEFAULT_LEDGER)
            builder.add_private_key(
                default_ledger, self._create_private_key(agent_name, default_ledger)
            )
        agent = builder.build()
        return AgentAlias(project, agent_name, json_config, agent)

    def _update_dict(self, base: dict, override: dict) -> dict:
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
