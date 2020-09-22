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
from abc import ABC, abstractmethod
from typing import Dict, List

from aea.aea_builder import PathLike
from aea.configurations.base import PublicId


class AbstractManager(ABC):
    """Abstract agents manager."""

    def __init__(self, working_dir: PathLike) -> None:
        """
        Initialize manager.

        :param working_dir: directory to store base agents.
        """
        self.working_dir = working_dir

    @abstractmethod
    def start_manager(self) -> None:
        """Start manager."""

    @abstractmethod
    def stop_manager(self, cleanup: bool = False) -> None:
        """
        Stop manager.

        Stops all running agents and stop agent.

        :param cleanup: remove agents_dir and purge in memory registry.

        :return: None
        """

    @abstractmethod
    def add_project(self, public_id: PublicId) -> None:
        """Fetch agent project and all dependencies to working_dir."""

    @abstractmethod
    def remove_project(self, public_id: PublicId) -> None:
        """Remove agent project."""

    @abstractmethod
    def list_projects(self) -> List[PublicId]:
        """
        List all agents projects added.

        :return: lit of public ids of projects
        """

    @abstractmethod
    def add_agent(
        self, project_id: PublicId, agent_name: str, config_overrides: Dict
    ) -> None:
        """
        Create new agent configuration based on project with config overrides applied.

        Alias is stored in memory only!

        :param project_id: base agent public id
        :param agent_name: unique name for the agent
        :param config_overrides: overrides for component section.

        :return: None
        """

    @abstractmethod
    def list_agents(self, running_only: bool = False) -> List[str]:
        """
        List all agents.

        :param running_only: returns only running if set to True

        :return: list of agents names
        """

    @abstractmethod
    def remove_agent(self, agent_name: str) -> None:
        """
        Remove agent alias definition from registry.

        :param agent_name: agent name to remove

        :return: None
        """

    @abstractmethod
    def start_agent(self, agent_name: str) -> None:
        """
        Start selected agent.

        :param agent_name: agent name to start

        :return: None
        """

    @abstractmethod
    def start_all_agents(self) -> None:
        """
        Start all not started agents.

        :return: None
        """

    @abstractmethod
    def stop_agent(self, agent_name: str) -> None:
        """
        Stop running agent.

        :param agent_name: agent name to stop

        :return: None
        """

    @abstractmethod
    def stop_all_agents(self) -> None:
        """
        Stop all agents running.

        :return: None
        """

    @abstractmethod
    def get_agent_details(self, agent_name: str) -> dict:
        """
        Return details about agent definition.

        {
            "project": str
            "overrides": dict
        }
        """
