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

"""This test module contains the tests for the `aea run` sub-command."""
import logging
import os
import shutil
import tempfile
from pathlib import Path

import yaml
from click.testing import CliRunner

from aea.cli import cli
from aea.configurations.base import DEFAULT_AEA_CONFIG_FILE
from ...conftest import CLI_LOG_OPTION, CUR_PATH


class TestRun:
    """Test that the command 'aea run' works as expected."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)
        result = cls.runner.invoke(cli, [*CLI_LOG_OPTION, "create", cls.agent_name])
        assert result.exit_code == 0

        os.chdir(Path(cls.t, cls.agent_name))
        shutil.copytree(Path(CUR_PATH, "data", "stopping_skill"), Path(cls.t, cls.agent_name, "skills", "stopping"))
        config_path = Path(cls.t, cls.agent_name, DEFAULT_AEA_CONFIG_FILE)
        config = yaml.safe_load(open(config_path))
        config.setdefault("skills", []).append("stopping")
        yaml.safe_dump(config, open(config_path, "w"))

        try:
            cli.main([*CLI_LOG_OPTION, "run"])
        except SystemExit as e:
            cls.exit_code = e.code

    def test_exit_code_equal_to_zero(self):
        """Assert that the exit code is equal to zero (i.e. success)."""
        assert self.exit_code == 0

    @classmethod
    def teardown_class(cls):
        """Teardowm the test."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass
