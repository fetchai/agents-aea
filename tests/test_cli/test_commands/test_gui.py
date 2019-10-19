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
import subprocess
import tempfile
import time
from pathlib import Path

import jsonschema
import pytest
from jsonschema import Draft4Validator

from ...conftest import AGENT_CONFIGURATION_SCHEMA, CONFIGURATION_SCHEMA_DIR, CLI_LOG_OPTION, tcpping


class TestGui:
    """Test that the command 'aea gui' works as expected."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.schema = json.load(open(AGENT_CONFIGURATION_SCHEMA))
        cls.resolver = jsonschema.RefResolver("file://{}/".format(Path(CONFIGURATION_SCHEMA_DIR).absolute()), cls.schema)
        cls.validator = Draft4Validator(cls.schema, resolver=cls.resolver)

        cls.agent_name = "myagent"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)
        cls.proc = subprocess.Popen(["aea", *CLI_LOG_OPTION, "gui"])
        time.sleep(10.0)

    def test_gui(self, pytestconfig):
        """Test that the gui process has been spawned correctly."""
        if pytestconfig.getoption("ci"):
            pytest.skip('skipped: CI')
        else:
            assert tcpping("localhost", 8080)

    @classmethod
    def teardown_class(cls):
        """Teardowm the test."""
        cls.proc.terminate()
        cls.proc.wait(2.0)
        os.chdir(cls.cwd)
