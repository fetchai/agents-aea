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

"""This test module contains the tests for the `aea` command-line tool."""
import json
import os
import pprint

import yaml
from click.testing import CliRunner
from jsonschema import validate, Draft7Validator

from aea.cli import cli
from .conftest import CUR_PATH, ROOT_DIR


def test_no_argument():
    """Test that if we run the cli tool without arguments, it exits gracefully."""
    runner = CliRunner()
    result = runner.invoke(cli, [])
    assert result.exit_code == 0


def test_agent_configuration_schema_is_valid_wrt_draft_07():
    """Test that the JSON schema for the agent configuration file is compliant with the specification Draft 07."""
    agent_config_schema = json.load(open(os.path.join(ROOT_DIR, "aea", "cli", "schemas", "aea-config_schema.json")))
    Draft7Validator.check_schema(agent_config_schema)


def test_validate_config():
    """Test that the validation of the agent configuration file works correctly."""
    agent_config_schema = json.load(open(os.path.join(ROOT_DIR, "aea", "cli", "schemas", "aea-config_schema.json")))
    agent_config_file = yaml.safe_load(open(os.path.join(CUR_PATH, "data", "aea-config.example.yaml")))
    pprint.pprint(agent_config_file)
    validate(instance=agent_config_file, schema=agent_config_schema)
