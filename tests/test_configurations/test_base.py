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
from pathlib import Path
from unittest import TestCase, mock

import pytest

import semver

import yaml

import aea
from aea.configurations.base import (
    AgentConfig,
    CRUDCollection,
    ComponentConfiguration,
    ComponentId,
    ComponentType,
    ConnectionConfig,
    ContractConfig,
    PackageId,
    PackageType,
    ProtocolConfig,
    ProtocolSpecification,
    ProtocolSpecificationParseError,
    PublicId,
    SkillConfig,
    SpeechActContentConfig,
    _check_aea_version,
    _compare_fingerprints,
    _get_default_configuration_file_name_from_type,
)
from aea.configurations.constants import DEFAULT_LEDGER

from tests.conftest import (
    AUTHOR,
    agent_config_files,
    connection_config_files,
    contract_config_files,
    protocol_config_files,
    skill_config_files,
    skip_test_windows,
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


class TestContractConfig:
    """Test the contract configuration class."""

    @pytest.mark.parametrize("contract_path", contract_config_files)
    def test_from_json_and_to_json(self, contract_path):
        """Test the 'from_json' method and 'to_json' work correctly."""
        f = open(contract_path)
        original_json = yaml.safe_load(f)

        expected_config = ContractConfig.from_json(original_json)
        assert isinstance(expected_config, ContractConfig)
        expected_json = expected_config.json
        actual_config = ContractConfig.from_json(expected_json)
        actual_json = actual_config.json
        assert expected_json == actual_json


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
        _get_default_configuration_file_name_from_type("contract")


class PublicIdTestCase(TestCase):
    """Test case for PublicId class."""

    @mock.patch("aea.configurations.base.re.match", return_value=False)
    def test_public_id_from_str_not_matching(self, *mocks):
        """Test case for from_str method regex not matching."""
        with self.assertRaises(ValueError):
            PublicId.from_str("public_id_str")

    def test_public_id_from_json_positive(self):
        """Test case for from_json method positive result."""
        obj = {"author": AUTHOR, "name": "name", "version": "0.1.0"}
        PublicId.from_json(obj)

    def test_public_id_latest_positive(self):
        """Test case for latest property positive result."""
        name = "name"
        obj = PublicId(AUTHOR, name, "0.1.0")
        assert obj.latest == "{}/{}:*".format(AUTHOR, name)

    def test_public_id_json_positive(self):
        """Test case for json property positive result."""
        obj = PublicId(AUTHOR, "name", "0.1.0")
        obj.json

    def test_public_id_eq_positive(self):
        """Test case for json __eq__ method positive result."""
        obj1 = PublicId(AUTHOR, "name", "0.1.0")
        obj2 = PublicId(AUTHOR, "name", "0.1.0")
        self.assertTrue(obj1 == obj2)

    def test_public_id_lt_positive(self):
        """Test case for json __lt__ method positive result."""
        obj1 = PublicId(AUTHOR, "name", "1.0.0")
        obj2 = PublicId(AUTHOR, "name", "2.0.0")
        self.assertTrue(obj1 < obj2)


class AgentConfigTestCase(TestCase):
    """Test case for AgentConfig class."""

    def test_init_logging_config_positive(self):
        """Test case for from_json method positive result."""
        AgentConfig(agent_name="my_agent", author="fetchai", logging_config={})

    def test_default_connection(self):
        """Test case for default_connection setter positive result."""
        agent_config = AgentConfig(agent_name="my_agent", author="fetchai")
        agent_config.default_connection = None
        agent_config.default_connection = 1
        agent_config.public_id


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
        ProtocolSpecification(name="my_protocol", author="fetchai")

    def test_json_positive(self):
        """Test case for json property positive result."""
        obj = ProtocolSpecification(name="my_protocol", author="fetchai")
        obj.json

    @mock.patch("aea.configurations.base.SpeechActContentConfig.from_json")
    @mock.patch("aea.configurations.base.ProtocolSpecification._check_consistency")
    def test_from_json_positive(self, *mocks):
        """Test case for from_json method positive result."""
        json_disc = {
            "name": "name",
            "author": AUTHOR,
            "version": "0.1.0",
            "license": "license",
            "description": "description",
            "speech_acts": {"arg1": "arg1", "arg2": "arg2"},
        }
        ProtocolSpecification.from_json(json_disc)

    def test__check_consistency_positive(self):
        """Test case for _check_consistency method positive result."""
        obj = ProtocolSpecification(name="my_protocol", author="fetchai")
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


def test_package_type_plural():
    """Test PackageType.to_plural"""
    assert PackageType.AGENT.to_plural() == "agents"
    assert PackageType.PROTOCOL.to_plural() == "protocols"
    assert PackageType.CONNECTION.to_plural() == "connections"
    assert PackageType.CONTRACT.to_plural() == "contracts"
    assert PackageType.SKILL.to_plural() == "skills"


def test_package_type_str():
    """Test PackageType.__str__"""
    assert str(PackageType.AGENT) == "agent"
    assert str(PackageType.PROTOCOL) == "protocol"
    assert str(PackageType.CONNECTION) == "connection"
    assert str(PackageType.CONTRACT) == "contract"
    assert str(PackageType.SKILL) == "skill"


def test_component_type_str():
    """Test ComponentType.__str__"""
    assert str(ComponentType.PROTOCOL) == "protocol"
    assert str(ComponentType.CONNECTION) == "connection"
    assert str(ComponentType.CONTRACT) == "contract"
    assert str(ComponentType.SKILL) == "skill"


def test_configuration_ordered_json():
    """Test configuration ordered json."""
    configuration = ProtocolConfig("name", "author", "0.1.0")
    configuration._key_order = ["aea_version"]
    configuration.ordered_json


def test_public_id_versions():
    """Test that a public id version can be initialized with different objects."""
    PublicId("author", "name", "0.1.0")
    PublicId("author", "name", semver.VersionInfo(major=0, minor=1, patch=0))


def test_public_id_invalid_version():
    """Test the case when the version id is of an invalid type."""
    with pytest.raises(ValueError, match="Version type not valid."):
        PublicId("author", "name", object())


def test_public_id_from_uri_path():
    """Test PublicId.from_uri_path"""
    result = PublicId.from_uri_path("author/package_name/0.1.0")
    assert result.name == "package_name"
    assert result.author == "author"
    assert result.version == "0.1.0"


def test_public_id_from_uri_path_wrong_input():
    """Test that when a bad formatted path is passed in input of PublicId.from_uri_path
    an exception is raised."""
    with pytest.raises(
        ValueError, match="Input 'bad/formatted:input' is not well formatted."
    ):
        PublicId.from_uri_path("bad/formatted:input")


def test_public_id_to_uri_path():
    """Test PublicId.to_uri_path"""
    public_id = PublicId("author", "name", "0.1.0")
    assert public_id.to_uri_path == "author/name/0.1.0"


def test_pubic_id_repr():
    """Test PublicId.__repr__"""
    public_id = PublicId("author", "name", "0.1.0")
    assert repr(public_id) == "<author/name:0.1.0>"


def test_public_id_comparator_when_author_is_different():
    """Test PublicId.__lt__ when author is different."""
    pid1 = PublicId("author_1", "name", "0.1.0")
    pid2 = PublicId("author_2", "name", "0.1.0")
    with pytest.raises(
        ValueError,
        match="The public IDs .* and .* cannot be compared. Their author or name attributes are different.",
    ):
        pid1 < pid2


def test_public_id_comparator_when_name_is_different():
    """Test PublicId.__lt__ when author is different."""
    pid1 = PublicId("author", "name_1", "0.1.0")
    pid2 = PublicId("author", "name_2", "0.1.0")
    with pytest.raises(
        ValueError,
        match="The public IDs .* and .* cannot be compared. Their author or name attributes are different.",
    ):
        pid1 < pid2


def test_package_id_version():
    """Test PackageId.version"""
    package_id = PackageId(PackageType.PROTOCOL, PublicId("author", "name", "0.1.0"))
    assert package_id.version == "0.1.0"


def test_package_id_str():
    """Test PackageId.__str__"""
    package_id = PackageId(PackageType.PROTOCOL, PublicId("author", "name", "0.1.0"))
    assert str(package_id) == "(protocol, author/name:0.1.0)"


def test_package_id_lt():
    """Test PackageId.__lt__"""
    package_id_1 = PackageId(PackageType.PROTOCOL, PublicId("author", "name", "0.1.0"))
    package_id_2 = PackageId(PackageType.PROTOCOL, PublicId("author", "name", "0.2.0"))

    assert package_id_1 < package_id_2


def test_component_id_prefix_import_path():
    """Test ComponentId.prefix_import_path"""
    component_id = ComponentId(
        ComponentType.PROTOCOL, PublicId("author", "name", "0.1.0")
    )
    assert component_id.prefix_import_path == "packages.author.protocols.name"


def test_component_configuration_load_file_not_found():
    """Test Component.load when a file is not found."""
    with mock.patch("builtins.open", side_effect=FileNotFoundError):
        with pytest.raises(FileNotFoundError):
            ComponentConfiguration.load(
                ComponentType.PROTOCOL, mock.MagicMock(spec=Path)
            )


def test_component_configuration_check_fingerprint_bad_directory():
    """Test ComponentConfiguration.check_fingerprint when a bad directory is provided."""
    config = ProtocolConfig("name", "author", "0.1.0")
    with pytest.raises(ValueError, match="Directory .* is not valid."):
        config.check_fingerprint(Path("non_existing_directory"))


@skip_test_windows
def test_component_configuration_check_fingerprint_different_fingerprints_vendor():
    """Test ComponentConfiguration.check_fingerprint when the fingerprints differ for a vendor package."""
    config = ProtocolConfig("name", "author", "0.1.0")
    package_dir = Path("path", "to", "dir")
    error_regex = (
        f"Fingerprints for package {package_dir} do not match:\nExpected: {dict()}\nActual: {dict(foo='bar')}\n"
        + "Vendorized projects should not be tampered with, please revert any changes to protocol author/name:0.1.0"
    )

    with pytest.raises(ValueError, match=error_regex):
        with mock.patch(
            "aea.configurations.base._compute_fingerprint", return_value={"foo": "bar"}
        ):
            _compare_fingerprints(config, package_dir, True, PackageType.PROTOCOL)


@skip_test_windows
def test_component_configuration_check_fingerprint_different_fingerprints_no_vendor():
    """Test ComponentConfiguration.check_fingerprint when the fingerprints differ for a non-vendor package."""
    config = ProtocolConfig("name", "author", "0.1.0")
    package_dir = Path("path", "to", "dir")
    error_regex = (
        f"Fingerprints for package {package_dir} do not match:\nExpected: {dict()}\nActual: {dict(foo='bar')}\n"
        + "Please fingerprint the package before continuing: 'aea fingerprint protocol author/name:0.1.0"
    )

    with pytest.raises(ValueError, match=error_regex):
        with mock.patch(
            "aea.configurations.base._compute_fingerprint", return_value={"foo": "bar"}
        ):
            _compare_fingerprints(config, package_dir, False, PackageType.PROTOCOL)


def test_check_aea_version_when_it_fails():
    """Test the check for the AEA version when it fails."""
    config = ProtocolConfig("name", "author", "0.1.0", aea_version=">0.1.0")
    with mock.patch.object(aea, "__version__", "0.1.0"):
        with pytest.raises(
            ValueError,
            match="The CLI version is 0.1.0, but package author/name:0.1.0 requires version >0.1.0",
        ):
            _check_aea_version(config)


def test_connection_config_with_connection_id():
    """Test construction of ConnectionConfig with connection id."""
    ConnectionConfig(connection_id=PublicId("name", "author", "0.1.0"))


def test_agent_config_package_dependencies():
    """Test agent config package dependencies."""
    agent_config = AgentConfig("name", "author")
    assert agent_config.package_dependencies == set()

    pid = PublicId("author", "name", "0.1.0")
    agent_config.protocols.add(pid)
    agent_config.connections.add(pid)
    agent_config.contracts.add(pid)
    agent_config.skills.add(pid)

    assert agent_config.package_dependencies == {
        PackageId(PackageType.PROTOCOL, pid),
        PackageId(PackageType.CONNECTION, pid),
        PackageId(PackageType.CONTRACT, pid),
        PackageId(PackageType.SKILL, pid),
    }


def test_agent_config_to_json_with_optional_configurations():
    """Test agent config to json with optional configurations."""
    agent_config = AgentConfig(
        "name",
        "author",
        timeout=0.1,
        execution_timeout=1.0,
        max_reactions=100,
        decision_maker_handler=dict(dotted_path="", file_path=""),
        skill_exception_policy="propagate",
        default_routing={"author/name:0.1.0": "author/name:0.1.0"},
        loop_mode="sync",
        runtime_mode="async",
    )
    agent_config.default_connection = "author/name:0.1.0"
    agent_config.default_ledger = DEFAULT_LEDGER
    agent_config.json


def test_protocol_specification_attributes():
    protocol_specification = ProtocolSpecification("name", "author", "0.1.0")

    # test getter and setter for 'protobuf_snippets'
    assert protocol_specification.protobuf_snippets == {}
    protocol_specification.protobuf_snippets = {"a": 1}
    assert protocol_specification.protobuf_snippets == {"a": 1}

    # test getter and setter for 'dialogue_config'
    assert protocol_specification.dialogue_config == {}
    protocol_specification.dialogue_config = {"a": 1}
    assert protocol_specification.dialogue_config == {"a": 1}


def test_contract_config_component_type():
    """Test ContractConfig.component_type"""
    config = ContractConfig("name", "author", "0.1.0")
    assert config.component_type == ComponentType.CONTRACT
