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

"""This test module contains the tests for the `aea freeze` sub-command."""

import json
import os
import shutil
import tempfile
from pathlib import Path

import jsonschema
import pytest
from jsonschema import Draft4Validator

from aea.cli import cli
from aea.configurations.loader import make_jsonschema_base_uri

from tests.conftest import (
    AGENT_CONFIGURATION_SCHEMA,
    CLI_LOG_OPTION,
    CONFIGURATION_SCHEMA_DIR,
    CUR_PATH,
    CliRunner,
    MAX_FLAKY_RERUNS,
)


class TestFreeze:
    """Test that the command 'aea freeze' works as expected."""

    def setup(self):
        """Set the test up."""
        self.schema = json.load(open(AGENT_CONFIGURATION_SCHEMA))
        self.resolver = jsonschema.RefResolver(
            make_jsonschema_base_uri(Path(CONFIGURATION_SCHEMA_DIR)), self.schema
        )
        self.validator = Draft4Validator(self.schema, resolver=self.resolver)

        self.cwd = os.getcwd()
        self.t = tempfile.mkdtemp()
        # copy the 'dummy_aea' directory in the parent of the agent folder.
        shutil.copytree(Path(CUR_PATH, "data", "dummy_aea"), Path(self.t, "dummy_aea"))
        self.runner = CliRunner()
        os.chdir(Path(self.t, "dummy_aea"))
        self.result = self.runner.invoke(
            cli, [*CLI_LOG_OPTION, "freeze"], standalone_mode=False
        )

    @pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
    def test_exit_code_equal_to_zero_and_correct_output(self):
        """Assert that the exit code is equal to zero (i.e. success)."""
        assert self.result.exit_code == 0
        """Test that the command has printed the correct output."""
        assert (
            self.result.output
            == """open-aea-ledger-cosmos<2.0.0,>=1.0.0\nopen-aea-ledger-ethereum<2.0.0,>=1.0.0\nopen-aea-ledger-fetchai<2.0.0,>=1.0.0\nprotobuf\n"""
        )

    def teardown(self):
        """Tear the test down."""
        os.chdir(self.cwd)
        try:
            shutil.rmtree(self.t)
        except (OSError, IOError):
            pass
