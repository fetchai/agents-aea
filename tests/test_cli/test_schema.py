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

"""This test module contains the tests for the JSON schemas of the configuration files."""
import json
import os
import pprint

import yaml
from jsonschema import validate, Draft7Validator  # type: ignore

from ..conftest import CUR_PATH, ROOT_DIR, AGENT_CONFIGURATION_SCHEMA, SKILL_CONFIGURATION_SCHEMA, \
    CONNECTION_CONFIGURATION_SCHEMA


def test_agent_configuration_schema_is_valid_wrt_draft_07():
    """Test that the JSON schema for the agent configuration file is compliant with the specification Draft 07."""
    agent_config_schema = json.load(open(os.path.join(ROOT_DIR, "aea", "configurations", "schemas", "aea-config_schema.json")))
    Draft7Validator.check_schema(agent_config_schema)


def test_skill_configuration_schema_is_valid_wrt_draft_07():
    """Test that the JSON schema for the skill configuration file is compliant with the specification Draft 07."""
    skill_config_schema = json.load(open(os.path.join(ROOT_DIR, "aea", "configurations", "schemas", "skill-config_schema.json")))
    Draft7Validator.check_schema(skill_config_schema)


def test_connection_configuration_schema_is_valid_wrt_draft_07():
    """Test that the JSON schema for the connection configuration file is compliant with the specification Draft 07."""
    connection_config_schema = json.load(open(os.path.join(ROOT_DIR, "aea", "configurations", "schemas", "connection-config_schema.json")))
    Draft7Validator.check_schema(connection_config_schema)


def test_validate_agent_config():
    """Test that the validation of the agent configuration file works correctly."""
    agent_config_schema = json.load(open(AGENT_CONFIGURATION_SCHEMA))
    agent_config_file = yaml.safe_load(open(os.path.join(CUR_PATH, "data", "aea-config.example.yaml")))
    pprint.pprint(agent_config_file)
    validate(instance=agent_config_file, schema=agent_config_schema)


def test_validate_skill_config():
    """Test that the validation of the skill configuration file works correctly."""
    skill_config_schema = json.load(open(SKILL_CONFIGURATION_SCHEMA))
    skill_config_file = yaml.safe_load(open(os.path.join(CUR_PATH, "data", "dummy_skill", "skill.yaml")))
    pprint.pprint(skill_config_file)
    validate(instance=skill_config_file, schema=skill_config_schema)


def test_validate_connection_config():
    """Test that the validation of the connection configuration file works correctly."""
    connection_config_schema = json.load(open(CONNECTION_CONFIGURATION_SCHEMA))
    connection_config_file = yaml.safe_load(open(os.path.join(CUR_PATH, "data", "dummy_connection", "connection.yaml")))
    pprint.pprint(connection_config_file)
    validate(instance=connection_config_file, schema=connection_config_schema)
