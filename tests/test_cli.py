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
from jsonschema import validate, Draft7Validator  # type: ignore

from aea.cli import cli
from .conftest import CUR_PATH, ROOT_DIR


def test_no_argument():
    """Test that if we run the cli tool without arguments, it exits gracefully."""
    runner = CliRunner()
    result = runner.invoke(cli, [])
    assert result.exit_code == 0


# def test_use_case():
#     """Test a common use case for the 'aea' tool."""
#     runner = CliRunner()
#     agent_name = "myagent"
#     with runner.isolated_filesystem() as t:
#         configs = dict(stdout=subprocess.PIPE)
#
#         # create an agent
#         proc = subprocess.Popen(["aea", "create", agent_name], cwd=t, **configs)
#         proc.wait(timeout=1)
#         assert proc.returncode == 0
#
#         # add protocol oef
#         proc = subprocess.Popen(["aea", "add", "protocol", "oef"], cwd=os.path.join(t, agent_name), **configs)
#         proc.wait(timeout=1)
#         assert proc.returncode == 0
#
#         # add protocol tac
#         proc = subprocess.Popen(["aea", "add", "protocol", "tac"], cwd=os.path.join(t, agent_name), **configs)
#         proc.wait(timeout=1)
#         assert proc.returncode == 0
#
#         # add protocol default
#         proc = subprocess.Popen(["aea", "add", "protocol", "default"], cwd=os.path.join(t, agent_name), **configs)
#         proc.wait(timeout=1)
#         assert proc.returncode == 0
#
#         # remove protocol default
#         proc = subprocess.Popen(["aea", "remove", "protocol", "default"], cwd=os.path.join(t, agent_name), **configs)
#         proc.wait(timeout=1)
#         assert proc.returncode == 0
#
#         # add dummy skill
#         proc = subprocess.Popen(["aea", "add", "skill", "dummy_skill", os.path.join(CUR_PATH, "data", "dummy_skill")],
#                                 cwd=os.path.join(t, agent_name), **configs)
#         proc.wait(timeout=1)
#         assert proc.returncode == 0
#
#         # remove dummy skill
#         proc = subprocess.Popen(["aea", "remove", "skill", "dummy_skill"],
#                                 cwd=os.path.join(t, agent_name), **configs)
#         proc.wait(timeout=1)
#         assert proc.returncode == 0
#
#         # add dummy skill
#         proc = subprocess.Popen(["aea", "add", "skill", "dummy_skill", os.path.join(CUR_PATH, "data", "dummy_skill")],
#                                 cwd=os.path.join(t, agent_name), **configs)
#         proc.wait(timeout=1)
#         assert proc.returncode == 0
#
#         # run agent
#         proc = subprocess.Popen(["aea", "run"],
#                                 cwd=os.path.join(t, agent_name), **configs)
#         time.sleep(2.0)
#         proc.terminate()
#         proc.wait(5.0)
#
#         # delete agent
#         proc = subprocess.Popen(["aea", "delete", agent_name], cwd=t, **configs)
#         proc.wait(timeout=1)
#         assert proc.returncode == 0


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
    agent_config_schema = json.load(open(os.path.join(ROOT_DIR, "aea", "configurations", "schemas", "aea-config_schema.json")))
    agent_config_file = yaml.safe_load(open(os.path.join(CUR_PATH, "data", "aea-config.example.yaml")))
    pprint.pprint(agent_config_file)
    validate(instance=agent_config_file, schema=agent_config_schema)


def test_validate_skill_config():
    """Test that the validation of the skill configuration file works correctly."""
    skill_config_schema = json.load(open(os.path.join(ROOT_DIR, "aea", "configurations", "schemas", "skill-config_schema.json")))
    skill_config_file = yaml.safe_load(open(os.path.join(CUR_PATH, "data", "dummy_skill", "skill.yaml")))
    pprint.pprint(skill_config_file)
    validate(instance=skill_config_file, schema=skill_config_schema)


def test_validate_connection_config():
    """Test that the validation of the connection configuration file works correctly."""
    connection_config_schema = json.load(open(os.path.join(ROOT_DIR, "aea", "configurations", "schemas", "connection-config_schema.json")))
    connection_config_file = yaml.safe_load(open(os.path.join(CUR_PATH, "data", "dummy_connection", "connection.yaml")))
    pprint.pprint(connection_config_file)
    validate(instance=connection_config_file, schema=connection_config_schema)
