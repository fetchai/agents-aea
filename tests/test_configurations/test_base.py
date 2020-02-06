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

"""This module contains the tests for the aea.configurations.base module."""

import pytest

import yaml

from aea.configurations.base import (
    AgentConfig,
    CRUDCollection,
    ConnectionConfig,
    ProtocolConfig,
    SkillConfig,
)

from ..conftest import (
    agent_config_files,
    connection_config_files,
    protocol_config_files,
    skill_config_files,
)


class TestCRUDCollection:
    """Test the CRUDCollection data structure."""

    def test_create_with_existing_key(self):
        """Test that creating and item with an existing key raises an exception."""
        collection = CRUDCollection()
        collection.create("one", 1)

        with pytest.raises(ValueError, match="Item with name .* already present"):
            collection.create("one", 1)

    def test_read_not_empty(self):
        """Test that reading a previously created item gives a non-empty result."""
        collection = CRUDCollection()
        collection.create("one", 1)
        item = collection.read("one")
        assert item == 1

    def test_read_empty(self):
        """Test that reading with a non-existing key returns None."""
        collection = CRUDCollection()
        item = collection.read("one")
        assert item is None

    def test_update(self):
        """Test that the update method works correctly."""
        collection = CRUDCollection()
        collection.create("one", 1)

        assert collection.read("one") == 1
        collection.update("one", 2)
        assert collection.read("one") == 2

    def test_delete(self):
        """Test that the delete method works correctly."""
        collection = CRUDCollection()
        collection.create("one", 1)

        assert collection.read("one") == 1
        collection.delete("one")
        assert collection.read("one") is None

    def test_read_all(self):
        """Test that the read_all method works correctly."""
        collection = CRUDCollection()
        collection.create("one", 1)
        collection.create("two", 2)

        keyvalue_pairs = collection.read_all()
        assert {("one", 1), ("two", 2)} == set(keyvalue_pairs)


class TestConnectionConfig:
    """Test the connection configuration class."""

    @pytest.mark.parametrize("connection_path", connection_config_files)
    def test_from_json_and_to_json(self, connection_path):
        """Test the 'from_json' method and 'to_json' work correctly."""
        f = open(connection_path)
        original_json = yaml.safe_load(f)

        expected_config = ConnectionConfig.from_json(original_json)
        assert isinstance(expected_config, ConnectionConfig)
        expected_json = expected_config.json
        actual_config = ConnectionConfig.from_json(expected_json)
        actual_json = actual_config.json
        assert expected_json == actual_json


class TestProtocolConfig:
    """Test the protocol configuration class."""

    @pytest.mark.parametrize("protocol_path", protocol_config_files)
    def test_from_json_and_to_json(self, protocol_path):
        """Test the 'from_json' method and 'to_json' work correctly."""
        f = open(protocol_path)
        original_json = yaml.safe_load(f)

        expected_config = ProtocolConfig.from_json(original_json)
        assert isinstance(expected_config, ProtocolConfig)
        expected_json = expected_config.json
        actual_config = ProtocolConfig.from_json(expected_json)
        actual_json = actual_config.json
        assert expected_json == actual_json


class TestSkillConfig:
    """
    Test the skill configuration class.

    This suite tests also the handlers/tasks/behaviours/models configuration classes.
    """

    @pytest.mark.parametrize("skill_path", skill_config_files)
    def test_from_json_and_to_json(self, skill_path):
        """Test the 'from_json' method and 'to_json' work correctly."""
        f = open(skill_path)
        original_json = yaml.safe_load(f)

        expected_config = SkillConfig.from_json(original_json)
        assert isinstance(expected_config, SkillConfig)
        expected_json = expected_config.json
        actual_config = SkillConfig.from_json(expected_json)
        actual_json = actual_config.json
        assert expected_json == actual_json


class TestAgentConfig:
    """Test the agent configuration class."""

    @pytest.mark.parametrize("agent_path", agent_config_files)
    def test_from_json_and_to_json(self, agent_path):
        """Test the 'from_json' method and 'to_json' work correctly."""
        f = open(agent_path)
        original_json = yaml.safe_load(f)

        expected_config = AgentConfig.from_json(original_json)
        assert isinstance(expected_config, AgentConfig)
        expected_json = expected_config.json
        actual_config = AgentConfig.from_json(expected_json)
        actual_json = actual_config.json
        assert expected_json == actual_json
