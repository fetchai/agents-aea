# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2019 Fetch.AI Limited
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
"""This module contains the tests for the aea configurations project."""
import os
import shutil
import tempfile
from unittest.mock import Mock

from aea.cli import cli
from aea.configurations.base import PublicId
from aea.configurations.project import AgentAlias, Project
from aea.helpers.base import cd
from aea.test_tools.click_testing import CliRunner


class TestProjectAndAgentAlias:
    """Check project and agent alias."""

    def setup(self):
        """Set the test up."""
        self.cwd = os.getcwd()
        self.t = tempfile.mkdtemp()
        os.chdir(self.t)
        self.runner = CliRunner()
        self.project_public_id = PublicId("fetchai", "my_first_aea", "0.11.0")
        self.project_path = os.path.join(
            self.t, self.project_public_id.author, self.project_public_id.name
        )

    def test_project(self):
        """Test project laoded and removed."""
        project = Project.load(self.t, self.project_public_id)
        assert os.path.exists(self.project_path)

        with cd(self.project_path):
            result = self.runner.invoke(
                cli,
                ["config", "get", "agent.agent_name"],
                catch_exceptions=False,
                standalone_mode=False,
            )
        assert self.project_public_id.name in result.output
        project.remove()
        assert not os.path.exists(self.project_path)

    def test_agents(self):
        """Test agent added to project and rmeoved."""
        project = Project(self.project_public_id, self.project_path)
        alias = AgentAlias(project, "test", [], Mock(), Mock())
        assert project.agents
        alias.remove_from_project()
        assert not project.agents

    def teardown(self):
        """Tear dowm the test."""
        os.chdir(self.cwd)
        try:
            shutil.rmtree(self.t)
        except (OSError, IOError):
            pass
