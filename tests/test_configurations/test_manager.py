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
"""This test module contains the tests for the configurations manager module."""

import os
from copy import deepcopy
from unittest.mock import patch

import pytest
import yaml

from aea.configurations.manager import AgentConfigManager


agent_config_data = yaml.safe_load(
    """
agent_name: Agent0
author: dummy_author
version: 1.0.0
description: dummy_aea agent description
license: Apache-2.0
aea_version: '>=0.8.0, <0.9.0'
fingerprint: {}
fingerprint_ignore_patterns: []
connections:
- fetchai/local:0.13.0
contracts: []
protocols:
- fetchai/default:0.10.0
skills:
- dummy_author/dummy:0.1.0
default_connection: fetchai/local:0.13.0
default_ledger: cosmos
logging_config:
  disable_existing_loggers: ${DISABLE_LOGS:bool}
  version: 1
private_key_paths:
  cosmos: cosmos_private_key.txt
  ethereum: ethereum_private_key.txt
connection_private_key_paths:
  cosmos: cosmos_private_key.txt
  ethereum: ethereum_private_key.txt
registry_path: ../../packages
default_routing: {}
"""
)


def test_envvars_applied():
    """Test env vars replaced with values."""
    dct = deepcopy(agent_config_data)
    with patch.object(AgentConfigManager, "_load_config_data", return_value=[dct]):
        os.environ["DISABLE_LOGS"] = "true"
        agent_config_manager = AgentConfigManager.load(".", substitude_env_vars=True)
    assert (
        agent_config_manager.json["logging_config"]["disable_existing_loggers"] is True
    )

    with patch.object(AgentConfigManager, "_load_config_data", return_value=[dct]):
        os.environ["DISABLE_LOGS"] = "false"
        agent_config_manager = AgentConfigManager.load(".", substitude_env_vars=True)
    assert (
        agent_config_manager.json["logging_config"]["disable_existing_loggers"] is False
    )

    # no env! no default value
    os.environ.pop("DISABLE_LOGS")
    with pytest.raises(
        ValueError,
        match="Var name DISABLE_LOGS not found in env variables and no default value set!",
    ):
        with patch.object(AgentConfigManager, "_load_config_data", return_value=[dct]):
            agent_config_manager = AgentConfigManager.load(
                ".", substitude_env_vars=True
            )
        assert (
            agent_config_manager.json["logging_config"]["disable_existing_loggers"]
            is False
        )

    # check default value specified
    dct["logging_config"]["disable_existing_loggers"] = "${DISABLE_LOGS:bool:true}"
    with patch.object(AgentConfigManager, "_load_config_data", return_value=[dct]):
        agent_config_manager = AgentConfigManager.load(".", substitude_env_vars=True)
        assert (
            agent_config_manager.json["logging_config"]["disable_existing_loggers"]
            is True
        )

    # check incorrect data type
    dct["logging_config"]["disable_existing_loggers"] = "${DISABLE_LOGS:int:true}"
    with pytest.raises(ValueError, match="Cannot convert string `true` to type `int`"):
        with patch.object(AgentConfigManager, "_load_config_data", return_value=[dct]):
            agent_config_manager = AgentConfigManager.load(
                ".", substitude_env_vars=True
            )
            assert (
                agent_config_manager.json["logging_config"]["disable_existing_loggers"]
                is True
            )

    # not applied
    dct = deepcopy(agent_config_data)
    with patch.object(AgentConfigManager, "_load_config_data", return_value=[dct]):
        os.environ["DISABLE_LOGS"] = "true"
        agent_config_manager = AgentConfigManager.load(".", substitude_env_vars=False)
    assert (
        agent_config_manager.json["logging_config"]["disable_existing_loggers"]
        == dct["logging_config"]["disable_existing_loggers"]
    )


def test_envvars_preserved():
    """Test env vars not modified on config update."""
    dct = deepcopy(agent_config_data)
    new_cosmos_key_value = "cosmons_key_updated"

    with patch.object(AgentConfigManager, "_load_config_data", return_value=[dct]):
        os.environ["DISABLE_LOGS"] = "true"
        agent_config_manager = AgentConfigManager.load(".", substitude_env_vars=False)

    assert (
        agent_config_manager.json["logging_config"]["disable_existing_loggers"]
        == dct["logging_config"]["disable_existing_loggers"]
    )

    with patch.object(AgentConfigManager, "_load_config_data", return_value=[dct]):
        os.environ["DISABLE_LOGS"] = "true"
        agent_config_manager = AgentConfigManager.load(".", substitude_env_vars=False)

    assert (
        agent_config_manager.json["private_key_paths"]["cosmos"] != new_cosmos_key_value
    )
    agent_config_manager.update_config(
        {"private_key_paths": {"cosmos": new_cosmos_key_value}}
    )

    assert (
        agent_config_manager.json["logging_config"]["disable_existing_loggers"]
        == dct["logging_config"]["disable_existing_loggers"]
    )
    assert (
        agent_config_manager.json["private_key_paths"]["cosmos"] == new_cosmos_key_value
    )
