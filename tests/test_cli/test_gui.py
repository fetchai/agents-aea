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
"""This test module contains the tests for the `aea gui` sub-command."""
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

import jsonschema
from jsonschema import Draft4Validator

import pytest

from aea.cli import cli
from aea.configurations.loader import make_jsonschema_base_uri
from aea.test_tools.click_testing import CliRunner

from tests.common.pexpect_popen import PexpectWrapper
from tests.conftest import (
    AGENT_CONFIGURATION_SCHEMA,
    CLI_LOG_OPTION,
    CONFIGURATION_SCHEMA_DIR,
    tcpping,
)


@pytest.mark.network
class TestGui:
    """Test that the command 'aea gui' works as expected."""

    def setup(self):
        """Set the test up."""
        self.runner = CliRunner()
        self.schema = json.load(open(AGENT_CONFIGURATION_SCHEMA))
        self.resolver = jsonschema.RefResolver(
            make_jsonschema_base_uri(Path(CONFIGURATION_SCHEMA_DIR).absolute()),
            self.schema,
        )
        self.validator = Draft4Validator(self.schema, resolver=self.resolver)

        self.agent_name = "myagent"
        self.cwd = os.getcwd()
        self.t = tempfile.mkdtemp()
        os.chdir(self.t)
        result = self.runner.invoke(
            cli, [*CLI_LOG_OPTION, "init", "--local", "--author", "test_author"],
        )

        assert result.exit_code == 0

    def test_gui(self):
        """Test that the gui process has been spawned correctly."""
        self.proc = PexpectWrapper(  # nosec
            [sys.executable, "-m", "aea.cli", "-v", "DEBUG", "gui"],
            encoding="utf-8",
            logfile=sys.stdout,
        )
        self.proc.expect_exact(["Running on http://"], timeout=20)

        assert tcpping("127.0.0.1", 8080)

    def teardown(self):
        """Tear the test down."""
        self.proc.terminate()
        self.proc.wait_to_complete(10)
        os.chdir(self.cwd)
        try:
            shutil.rmtree(self.t)
        except OSError:
            pass
