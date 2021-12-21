# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021 Valory AG
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

"""This test module contains the tests for the `aea create` sub-command."""

import logging
import os
import shutil
from pathlib import Path
from typing import List
from unittest.mock import patch

from click.testing import Result
from aea.configurations.base import AgentConfig
from aea.configurations.constants import DEFAULT_AEA_CONFIG_FILE
from aea.configurations.data_types import PackageType, PublicId
from aea.configurations.loader import ConfigLoader, load_component_configuration

from aea.test_tools.click_testing import CliRunner
from tests.conftest import AUTHOR, CLI_LOG_OPTION, ROOT_DIR
from aea.cli import cli

TEST_DIR = Path(ROOT_DIR) / "tests" / "test_contract_dependencies"


class TestCreate:
    """Test that the command 'aea create <agent_name>' works as expected."""

    def _load_agent_config(self) -> AgentConfig:
        """Load agent config for current dir."""
        agent_loader = ConfigLoader.from_configuration_type(PackageType.AGENT)
        with open(str(self.agent_dir / DEFAULT_AEA_CONFIG_FILE), "r") as fp:
            agent_config = agent_loader.load(fp)
        return agent_config

    def _run_command(self, options: List) -> Result:
        """Run command with default options."""
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, f"--registry-path={str(TEST_DIR/'packages')}", *options],
        )
        assert result.exit_code == 0, result.stdout
        return result

    def test_run(self):
        """Run the test."""

        os.chdir(str(TEST_DIR))

        self.agent_name = "default_agent"
        self.agent_dir = TEST_DIR / self.agent_name
        self.runner = CliRunner()
        result = self.runner.invoke(
            cli,
            [
                *CLI_LOG_OPTION,
                "init",
                "--local",
                "--author",
                AUTHOR,
                "--default-registry",
                "http",
            ],
        )
        assert result.exit_code == 0, result.stdout

        result = self._run_command(
            [
                "create",
                "--empty",
                "--local",
                self.agent_name,
            ]
        )
        os.chdir(self.agent_dir)
        result = self._run_command(
            [
                "add",
                "--local",
                "contract",
                "default_author/stub_1:0.1.0",
            ]
        )

        agent_config = self._load_agent_config()
        assert all(
            [
                PublicId.from_str(pid) in agent_config.contracts
                for pid in [
                    "default_author/stub_0:0.1.0",
                    "default_author/stub_1:0.1.0",
                ]
            ]
        )
        assert all(
            [
                (
                    self.agent_dir / "vendor" / "default_author" / "contracts" / pid
                ).is_dir()
                for pid in ["stub_0", "stub_1"]
            ]
        )

        result = self._run_command(
            [
                "build",
            ]
        )
        assert result.stdout == "Build completed!\n"

    def teardown(
        self,
    ):
        """Test teardown."""
        shutil.rmtree(str(self.agent_dir))
        os.chdir(str(ROOT_DIR))
