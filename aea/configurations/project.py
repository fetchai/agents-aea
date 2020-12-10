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
"""This module contains the implementation of AEA agents project configuiration."""
import os
from shutil import rmtree
from typing import Any, Dict, List, Set

from aea.aea import AEA
from aea.aea_builder import AEABuilder
from aea.cli.fetch import fetch_agent_locally
from aea.cli.registry.fetch import fetch_agent
from aea.cli.utils.context import Context
from aea.configurations.base import PublicId
from aea.configurations.constants import DEFAULT_REGISTRY_NAME


class Project:
    """Agent project representation."""

    def __init__(self, public_id: PublicId, path: str):
        """Init project with public_id and project's path."""
        self.public_id: PublicId = public_id
        self.path: str = path
        self.agents: Set[str] = set()

    @classmethod
    def load(
        cls,
        working_dir: str,
        public_id: PublicId,
        is_local: bool = False,
        is_restore: bool = False,
        registry_path: str = DEFAULT_REGISTRY_NAME,
        skip_consistency_check: bool = False,
    ) -> "Project":
        """
        Load project with given public_id to working_dir.

        :param working_dir: the working directory
        :param public_id: the public id
        :param is_local: whether to fetch from local or remote
        :param registry_path: the path to the registry locally
        :param skip_consistency_check: consistency checks flag
        """
        ctx = Context(cwd=working_dir, registry_path=registry_path)
        ctx.set_config("skip_consistency_check", skip_consistency_check)

        path = os.path.join(working_dir, public_id.author, public_id.name)
        target_dir = os.path.join(public_id.author, public_id.name)

        if not is_restore and not os.path.exists(target_dir):
            if is_local:
                ctx.set_config("is_local", True)
                fetch_agent_locally(ctx, public_id, target_dir=target_dir)
            else:
                fetch_agent(ctx, public_id, target_dir=target_dir)

        return cls(public_id, path)

    def remove(self) -> None:
        """Remove project, do cleanup."""
        rmtree(self.path)


class AgentAlias:
    """Agent alias representation."""

    def __init__(
        self,
        project: Project,
        agent_name: str,
        config: List[Dict],
        agent: AEA,
        builder: AEABuilder,
    ):
        """Init agent alias with project, config, name, agent, builder."""
        self.project = project
        self.config = config
        self.agent_name = agent_name
        self.agent = agent
        self.builder = builder
        self.project.agents.add(self.agent_name)

    def remove_from_project(self):
        """Remove agent alias from project."""
        self.project.agents.remove(self.agent_name)

    @property
    def dict(self) -> Dict[str, Any]:
        """Convert AgentAlias to dict."""
        return {
            "public_id": str(self.project.public_id),
            "agent_name": self.agent_name,
            "config": self.config,
        }
