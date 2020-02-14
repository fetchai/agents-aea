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
from unittest import TestCase, mock

import pytest

import yaml

from aea.configurations.base import (
    AgentConfig,
    CRUDCollection,
    ConnectionConfig,
    ProtocolConfig,
    ProtocolSpecification,
    ProtocolSpecificationParseError,
    PublicId,
    SkillConfig,
    SpeechActContentConfig,
    _get_default_configuration_file_name_from_type,
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


class GetDefaultConfigurationFileNameFromStrTestCase(TestCase):
    """Test case for _get_default_configuration_file_name_from_type method."""

    def test__get_default_configuration_file_name_from_type_positive(self):
        """Test for _get_default_configuration_file_name_from_type method positive result."""
        _get_default_configuration_file_name_from_type("agent")
        _get_default_configuration_file_name_from_type("connection")
        _get_default_configuration_file_name_from_type("protocol")
        _get_default_configuration_file_name_from_type("skill")


class PublicIdTestCase(TestCase):
    """Test case for PublicId class."""

    @mock.patch("aea.configurations.base.re.match", return_value=False)
    def test_public_id_from_str_not_matching(self, *mocks):
        """Test case for from_str method regex not matching."""
        with self.assertRaises(ValueError):
            PublicId.from_str("public_id_str")

    def test_public_id_from_json_positive(self):
        """Test case for from_json method positive result."""
        obj = {"author": "author", "name": "name", "version": "version"}
        PublicId.from_json(obj)

    def test_public_id_json_positive(self):
        """Test case for json property positive result."""
        obj = PublicId("author", "name", "version")
        obj.json


class AgentConfigTestCase(TestCase):
    """Test case for AgentConfig class."""

    def test_init_logging_config_positive(self):
        """Test case for from_json method positive result."""
        AgentConfig(logging_config={})

    def test_default_connection(self):
        """Test case for default_connection setter positive result."""
        agent_config = AgentConfig()
        agent_config.default_connection = None
        agent_config.default_connection = 1


class SpeechActContentConfigTestCase(TestCase):
    """Test case for SpeechActContentConfig class."""

    @mock.patch("aea.configurations.base.SpeechActContentConfig._check_consistency")
    def test_speech_act_content_config_init_positive(self, arg):
        """Test case for __init__ method positive result."""
        SpeechActContentConfig()

    def test__check_consistency_positive(self):
        """Test case for _check_consistency method positive result."""
        SpeechActContentConfig(arg1="arg1", arg2="arg2")
        with self.assertRaises(ProtocolSpecificationParseError):
            SpeechActContentConfig(arg1=None, arg2=1)
        with self.assertRaises(ProtocolSpecificationParseError):
            SpeechActContentConfig(arg1="", arg2="")

    def test_json_positive(self):
        """Test case for json property positive result."""
        config = SpeechActContentConfig()
        config.json

    def test_from_json_positive(self):
        """Test case for from_json method positive result."""
        SpeechActContentConfig.from_json({})


class ProtocolSpecificationTestCase(TestCase):
    """Test case for ProtocolSpecification class."""

    def test_init_positive(self):
        """Test case for __init__ method positive result."""
        ProtocolSpecification()

    def test_json_positive(self):
        """Test case for json property positive result."""
        obj = ProtocolSpecification()
        obj.json

    @mock.patch("aea.configurations.base.SpeechActContentConfig.from_json")
    @mock.patch("aea.configurations.base.ProtocolSpecification._check_consistency")
    def test_from_json_positive(self, *mocks):
        """Test case for from_json method positive result."""
        json_disc = {
            "name": "name",
            "author": "author",
            "version": "version",
            "license": "license",
            "description": "description",
            "speech_acts": {"arg1": "arg1", "arg2": "arg2"},
        }
        ProtocolSpecification.from_json(json_disc)

    def test__check_consistency_positive(self):
        """Test case for _check_consistency method positive result."""
        obj = ProtocolSpecification()
        with self.assertRaises(ProtocolSpecificationParseError):
            obj._check_consistency()

        obj.speech_acts = mock.Mock()
        read_all_mock = mock.Mock(return_value=[(1, 2)])
        obj.speech_acts.read_all = read_all_mock
        with self.assertRaises(ProtocolSpecificationParseError):
            obj._check_consistency()

        read_all_mock = mock.Mock(return_value=[["", 1]])
        obj.speech_acts.read_all = read_all_mock
        with self.assertRaises(ProtocolSpecificationParseError):
            obj._check_consistency()

        speech_act_content_config = mock.Mock()
        speech_act_content_config.args = {1: 2}
        read_all_mock = mock.Mock(return_value=[["1", speech_act_content_config]])
        obj.speech_acts.read_all = read_all_mock
        obj._check_consistency()
