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
from typing import Set

from aea.cli.registry.fetch import fetch_agent
from aea.cli.utils.context import Context
from aea.configurations.base import PublicId


class Project:
    """Agent project representation."""

    def __init__(self, public_id: PublicId, path: str):
        """Init project with public_id and project's path."""
        self.public_id: PublicId = public_id
        self.path: str = path
        self.agents: Set[str] = set()

    @classmethod
    def load(cls, working_dir: str, public_id: PublicId) -> "Project":
        """Load project with given pubblic_id to working_dir."""
        ctx = Context(cwd=working_dir)
        path = os.path.join(working_dir, public_id.author, public_id.name)
        fetch_agent(
            ctx, public_id, target_dir=os.path.join(public_id.author, public_id.name)
        )
        return cls(public_id, path)

    def remove(self) -> None:
        """Remove project, do cleanup."""
        rmtree(self.path)
