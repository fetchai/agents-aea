# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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

import os
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import List
from unittest import mock

from click.testing import Result

from aea.cli import cli
from aea.configurations.base import AgentConfig
from aea.configurations.constants import DEFAULT_AEA_CONFIG_FILE
from aea.configurations.data_types import PackageType, PublicId
from aea.configurations.loader import ConfigLoader
from aea.test_tools.click_testing import CliRunner

from tests.conftest import AUTHOR, CLI_LOG_OPTION, ROOT_DIR


REGISTRY_PATH = Path(ROOT_DIR) / "tests" / "data" / "packages"


class TestCreate:
    """Test that the command 'aea create <agent_name>' works as expected."""

    def _load_agent_config(self) -> AgentConfig:
        """Load agent config for current dir."""
        agent_loader = ConfigLoader.from_configuration_type(PackageType.AGENT)
        with open(str(self.agent_dir / DEFAULT_AEA_CONFIG_FILE), "r") as fp:
            agent_config = agent_loader.load(fp)
        return agent_config

    def _run_command(self, options: List, assert_exit_code: bool = True) -> Result:
        """Run command with default options."""
        result = self.runner.invoke(
            cli,
            ["-v", "INFO", f"--registry-path={str(REGISTRY_PATH)}", *options],
        )
        if assert_exit_code:
            assert result.exit_code == 0, result.stdout
        return result

    def test_run(self):
        """Run the test."""

        temp_dir = Path(TemporaryDirectory().name)
        temp_dir.mkdir(exist_ok=True)
        os.chdir(str(temp_dir))
        self.agent_name = "default_agent"
        self.agent_dir = temp_dir / self.agent_name
        self.runner = CliRunner()
        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR],
        )
        assert result.exit_code == 0, result.stdout
        result = self._run_command(["create", "--empty", "--local", self.agent_name])
        os.chdir(self.agent_dir)
        result = self._run_command(
            ["add", "--local", "contract", "default_author/stub_1:0.1.0"]
        )
        agent_config = self._load_agent_config()
        assert all(
            [
                PublicId.from_str(pid)
                in {p.without_hash() for p in agent_config.contracts}
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

        with mock.patch("click.echo") as echo_mock:
            result = self._run_command(["build"])
            echo_mock.assert_called_with("Build completed!")

        self._run_command(["generate-key", "ethereum"])
        self._run_command(["add-key", "ethereum"])

        outputs = []

        def _print_patch(line: str, *args, **kwargs) -> None:
            outputs.append(line)

        with mock.patch("builtins.print", new=_print_patch):
            result = self._run_command(["run"], False)

        assert "Contract stub_0 initialized." in outputs
        assert "Contract stub_1 initialized." in outputs

    def teardown(
        self,
    ):
        """Test teardown."""
        os.chdir(str(ROOT_DIR))
