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
"""This test module contains the tests for the configurations manager module."""
import os
from copy import deepcopy
from pathlib import Path
from typing import Dict, cast
from unittest.mock import mock_open, patch

import pytest
import yaml

from aea.configurations.constants import CONNECTION
from aea.configurations.data_types import ComponentId, PublicId
from aea.configurations.manager import (
    AgentConfigManager,
    find_component_directory_from_component_id,
    handle_dotted_path,
)
from aea.configurations.validation import SAME_MARK
from aea.exceptions import AEAException

from tests.conftest import ROOT_DIR


DUMMY_AEA = Path(ROOT_DIR) / "tests" / "data" / "dummy_aea"
DUMMY_AEA_CONFIG = """
agent_name: Agent0
author: dummy_author
version: 1.0.0
description: dummy_aea agent description
license: Apache-2.0
aea_version: '>=1.0.0, <2.0.0'
fingerprint: {}
fingerprint_ignore_patterns: []
connections:
- fetchai/local:0.20.0
contracts: []
protocols:
- fetchai/default:1.0.0
skills:
- dummy_author/dummy:0.1.0
- fetchai/error:0.17.0
default_connection: fetchai/local:0.20.0
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
default_routing: {}
"""

DUMMY_SKILL_OVERRIDE = """
public_id: dummy_author/test_skill:0.1.0
type: skill
models:
  scaffold:
    args:
      recursive:
        hello: world
"""

AGENT_CONFIG_DATA = yaml.safe_load(DUMMY_AEA_CONFIG)


def test_envvars_applied():
    """Test env vars replaced with values."""
    dct = deepcopy(AGENT_CONFIG_DATA)
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
        match="`DISABLE_LOGS` not found in env variables and no default value set!",
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
    dct = deepcopy(AGENT_CONFIG_DATA)
    with patch.object(AgentConfigManager, "_load_config_data", return_value=[dct]):
        os.environ["DISABLE_LOGS"] = "true"
        agent_config_manager = AgentConfigManager.load(".", substitude_env_vars=False)
    assert (
        agent_config_manager.json["logging_config"]["disable_existing_loggers"]
        == dct["logging_config"]["disable_existing_loggers"]
    )


@patch.object(AgentConfigManager, "get_overridables", return_value=[{}, {}])
def test_envvars_preserved(*mocks):
    """Test env vars not modified on config update."""
    dct = deepcopy(AGENT_CONFIG_DATA)
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


def test_agent_attribute_get_set():
    """Test agent config manager  get set variables."""
    dct = deepcopy(AGENT_CONFIG_DATA)
    with patch.object(AgentConfigManager, "_load_config_data", return_value=[dct]):
        os.environ["DISABLE_LOGS"] = "true"
        agent_config_manager = AgentConfigManager.load(
            DUMMY_AEA, substitude_env_vars=False
        )
        assert (
            agent_config_manager.get_variable("agent.default_ledger")
            == dct["default_ledger"]
        )
        assert (
            agent_config_manager.get_variable("vendor.fetchai.skills.error.name")
            == "error"
        )

        assert (
            agent_config_manager.get_variable(
                "vendor.fetchai.connections.local.is_abstract"
            )
            is False
        )
        agent_config_manager.set_variable(
            "vendor.fetchai.connections.local.is_abstract", True
        )
        assert (
            agent_config_manager.get_variable(
                "vendor.fetchai.connections.local.is_abstract"
            )
            is True
        )

        agent_config_manager.set_variable("agent.default_ledger", "fetchai")
        assert agent_config_manager.get_variable("agent.default_ledger") == "fetchai"

        assert (
            agent_config_manager.json["component_configurations"][0]["is_abstract"]
            is True
        )

    agent_config_manager = AgentConfigManager.load(DUMMY_AEA, substitude_env_vars=False)
    # agent_config_manager.set_variable(  # noqa: E800
    #     "vendor.fetchai.connections.p2p_libp2p.config.delegate_uri", "some_url"  # noqa: E800
    # )  # noqa: E800
    # assert (  # noqa: E800
    #     agent_config_manager.get_variable(  # noqa: E800
    #         "vendor.fetchai.connections.p2p_libp2p.config.delegate_uri"  # noqa: E800
    #     )  # noqa: E800
    #     == "some_url"  # noqa: E800
    # )  # noqa: E800

    with pytest.raises(
        ValueError, match="Attribute `does_not_exist` for AgentConfig does not exist"
    ):
        agent_config_manager.get_variable("agent.does_not_exist")

    agent_config_manager.validate_current_config()
    agent_config_manager.verify_private_keys(DUMMY_AEA, lambda x, y, z: None)


def test_recursive_updates() -> None:
    """Test recursive updates."""
    agent_config_manager = AgentConfigManager.load(DUMMY_AEA, substitude_env_vars=True)
    agent_config_manager.set_variable(
        "skills.test_skill.models.scaffold.args.recursive", {"foo": "bar"}
    )
    value = cast(
        Dict,
        agent_config_manager.get_variable(
            "skills.test_skill.models.scaffold.args.recursive"
        ),
    )

    assert value == {"foo": "bar"}

    agent_config_manager.set_variable(
        "skills.test_skill.models.scaffold.args.recursive",
        {"hello": "world"},
    )
    value = cast(
        Dict,
        agent_config_manager.get_variable(
            "skills.test_skill.models.scaffold.args.recursive"
        ),
    )

    assert value == {"hello": "world"}

    agent_config_manager.set_variable(
        "skills.test_skill.models.scaffold.args.recursive.hello",
        "world_0",
    )
    value = cast(
        Dict,
        agent_config_manager.get_variable(
            "skills.test_skill.models.scaffold.args.recursive"
        ),
    )

    assert value == {"hello": "world_0"}


def test_agent_attribute_get_overridables():
    """Test AgentConfigManager.get_overridables."""
    agent_config_manager = AgentConfigManager.load(DUMMY_AEA, substitude_env_vars=False)
    agent_overrides, component_overrides = agent_config_manager.get_overridables()
    assert "default_ledger" in agent_overrides
    assert "is_abstract" in list(component_overrides.values())[0]


def test_dump_config():
    """Test AgentConfigManager.dump_config."""
    agent_config_manager = AgentConfigManager.load(DUMMY_AEA, substitude_env_vars=False)
    with patch("aea.configurations.manager.open_file", mock_open()), patch(
        "aea.configurations.loader.ConfigLoader.dump"
    ) as dump_mock:
        agent_config_manager.dump_config()

    dump_mock.assert_called_once()


def test_handle_dotted_path():
    """Test handle_dotted_path."""
    with pytest.raises(
        AEAException, match=r"The root of the dotted path must be one of:"
    ):
        handle_dotted_path("something", author="fetchai")

    with pytest.raises(
        AEAException,
        match=r"The path is too short. Please specify a path up to an attribute name.",
    ):
        handle_dotted_path("skills", author="fetchai")

    with pytest.raises(
        AEAException, match=r"is not a valid component type. Please use one of"
    ):
        handle_dotted_path("vendor.fetchai.notskills.dummy.name", author="fetchai")

    with pytest.raises(AEAException, match=r"Resource .* does not exist."):
        handle_dotted_path("skills.notdummy.name", author="fetchai")


def test_find_component_directory_from_component_id():
    """Test find_component_directory_from_component_id."""
    with pytest.raises(ValueError, match=r"Package .* not found."):
        find_component_directory_from_component_id(
            Path("."),
            ComponentId(
                component_type=CONNECTION, public_id=PublicId("test", "test", "1.0.1")
            ),
        )


def test_agent_attribute_get_and_apply_overridables():
    """Test AgentConfigManager.get_overridables and apply it."""
    agent_config_manager = AgentConfigManager.load(DUMMY_AEA, substitude_env_vars=False)
    initial_agent_config_json = agent_config_manager.json

    agent_overrides, component_overrides = agent_config_manager.get_overridables()

    agent_config_manager.update_config(agent_overrides)
    assert initial_agent_config_json == agent_config_manager.json

    agent_overrides["component_configurations"] = component_overrides
    agent_config_manager.update_config(agent_overrides)

    assert agent_config_manager._filter_overrides(agent_overrides) == SAME_MARK

    agent_overrides["execution_timeout"] = 12
    assert agent_config_manager._filter_overrides(agent_overrides) == {
        "execution_timeout": 12
    }
