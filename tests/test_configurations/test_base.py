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
import re
from copy import copy
from pathlib import Path
from unittest import TestCase, mock
from unittest.mock import Mock

import pytest
import semver
import yaml
from packaging.specifiers import SpecifierSet

from aea.configurations.base import (
    AgentConfig,
    CRUDCollection,
    ComponentId,
    ComponentType,
    ConnectionConfig,
    ContractConfig,
    Dependency,
    PackageId,
    PackageType,
    PackageVersion,
    ProtocolConfig,
    ProtocolSpecification,
    PublicId,
    SkillConfig,
    SpeechActContentConfig,
    _check_aea_version,
    _compare_fingerprints,
    _get_default_configuration_file_name_from_type,
    dependencies_from_json,
    dependencies_to_json,
)
from aea.configurations.constants import (
    DEFAULT_AEA_CONFIG_FILE,
    DEFAULT_GIT_REF,
    DEFAULT_LEDGER,
    DEFAULT_PYPI_INDEX_URL,
    DEFAULT_SKILL_CONFIG_FILE,
)
from aea.configurations.loader import ConfigLoaders, load_component_configuration

from tests.conftest import (
    AUTHOR,
    CUR_PATH,
    DUMMY_SKILL_PATH,
    ROOT_DIR,
    agent_config_files,
    connection_config_files,
    contract_config_files,
    protocol_config_files,
    random_string,
    skill_config_files,
)
from tests.data.dummy_skill import PUBLIC_ID as DUMMY_SKILL_PUBLIC_ID


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

    def test_keys(self):
        """Test the keys method."""
        collection = CRUDCollection()
        collection.create("one", 1)
        collection.create("two", 2)

        keyvalue_pairs = collection.keys()
        assert {"one", "two"} == set(keyvalue_pairs)


class TestContractConfig:
    """Test the contract configuration class."""

    @pytest.mark.parametrize("contract_path", contract_config_files)
    def test_from_json_and_to_json(self, contract_path):
        """Test the 'from_json' method and 'to_json' work correctly."""
        f = open(contract_path)
        original_json = yaml.safe_load(f)
        original_json["build_directory"] = "some"

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
        original_json["build_directory"] = "some"

        expected_config = ConnectionConfig.from_json(original_json)
        assert isinstance(expected_config, ConnectionConfig)
        assert isinstance(expected_config.package_dependencies, set)
        assert not expected_config.is_abstract_component
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
        original_json["build_directory"] = "some"

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
        original_json["build_directory"] = "some"

        expected_config = SkillConfig.from_json(original_json)
        assert isinstance(expected_config, SkillConfig)
        expected_json = expected_config.json
        actual_config = SkillConfig.from_json(expected_json)
        actual_json = actual_config.json
        assert expected_json == actual_json

    def test_update_method(self):
        """Test the update method."""
        skill_config_path = Path(DUMMY_SKILL_PATH)
        loader = ConfigLoaders.from_package_type(PackageType.SKILL)
        skill_config = loader.load(skill_config_path.open())

        dummy_behaviour = skill_config.behaviours.read("dummy")
        expected_dummy_behaviour_args = copy(dummy_behaviour.args)
        expected_dummy_behaviour_args["behaviour_arg_1"] = 42

        dummy_handler = skill_config.handlers.read("dummy")
        expected_dummy_handler_args = copy(dummy_handler.args)
        expected_dummy_handler_args["handler_arg_1"] = 42

        dummy_model = skill_config.models.read("dummy")
        expected_dummy_model_args = copy(dummy_model.args)
        expected_dummy_model_args["model_arg_1"] = 42

        new_configurations = {
            "behaviours": {"dummy": {"args": dict(behaviour_arg_1=42)}},
            "handlers": {"dummy": {"args": dict(handler_arg_1=42)}},
            "models": {"dummy": {"args": dict(model_arg_1=42)}},
        }
        directory = "test_directory"
        skill_config.directory = directory
        skill_config.update(new_configurations)

        assert skill_config.directory == directory

        assert (
            expected_dummy_behaviour_args == skill_config.behaviours.read("dummy").args
        )
        assert expected_dummy_handler_args == skill_config.handlers.read("dummy").args
        assert expected_dummy_model_args == skill_config.models.read("dummy").args
        assert len(skill_config.package_dependencies)

    def test_update_method_raises_error_if_skill_component_not_allowed(self):
        """Test that we raise error if the custom configuration contain unexpected skill components."""
        skill_config_path = Path(
            ROOT_DIR,
            "packages",
            "fetchai",
            "skills",
            "error",
            DEFAULT_SKILL_CONFIG_FILE,
        )
        loader = ConfigLoaders.from_package_type(PackageType.SKILL)
        skill_config = loader.load(skill_config_path.open())
        new_configurations = {
            "behaviours": {"new_behaviour": {"args": {}}},
            "handlers": {"new_handler": {"args": {}}},
            "models": {"new_model": {"args": {}}},
        }

        with pytest.raises(
            ValueError,
            match="Attribute `behaviours.new_behaviour.args` is not allowed to be updated!",
        ):
            skill_config.update(new_configurations)

    def test_update_method_raises_error_if_we_try_to_change_classname_of_skill_component(
        self,
    ):
        """Test that we raise error if we try to change the 'class_name' field of a skill component configuration."""
        skill_config_path = Path(
            ROOT_DIR,
            "packages",
            "fetchai",
            "skills",
            "error",
            DEFAULT_SKILL_CONFIG_FILE,
        )
        loader = ConfigLoaders.from_package_type(PackageType.SKILL)
        skill_config = loader.load(skill_config_path.open())
        new_configurations = {
            "handlers": {"error_handler": {"class_name": "SomeClass", "args": {}}},
        }

        with pytest.raises(
            ValueError,
            match="Attribute `handlers.error_handler.class_name` is not allowed to be updated!",
        ):
            skill_config.update(new_configurations)


class TestAgentConfig:
    """Test the agent configuration class."""

    @pytest.mark.parametrize("agent_path", agent_config_files)
    def test_from_json_and_to_json(self, agent_path):
        """Test the 'from_json' method and 'to_json' work correctly."""
        f = open(agent_path)
        original_jsons = list(yaml.safe_load_all(f))
        components = original_jsons[1:]
        original_json = original_jsons[0]
        original_json["component_configurations"] = components
        original_json["build_entrypoint"] = "some"

        expected_config = AgentConfig.from_json(original_json)
        assert isinstance(expected_config, AgentConfig)
        expected_json = expected_config.json
        actual_config = AgentConfig.from_json(expected_json)
        actual_json = actual_config.json
        assert expected_json == actual_json


class TestAgentConfigUpdate:
    """Test methods that change the agent configuration."""

    def setup(self):
        """Set up the tests."""
        self.aea_config_path = Path(
            CUR_PATH, "data", "dummy_aea", DEFAULT_AEA_CONFIG_FILE
        )
        self.loader = ConfigLoaders.from_package_type(PackageType.AGENT)
        self.aea_config: AgentConfig = self.loader.load(self.aea_config_path.open())
        self.dummy_skill_component_id = ComponentId(
            ComponentType.SKILL, DUMMY_SKILL_PUBLIC_ID
        )

        self.new_dummy_skill_config = {
            "behaviours": {"dummy": {"args": dict(behaviour_arg_1=42)}},
            "handlers": {"dummy": {"args": dict(handler_arg_1=42)}},
            "models": {"dummy": {"args": dict(model_arg_1=42)}},
        }

    def test_all_components_id(self):
        """Test all components id listing."""
        assert self.dummy_skill_component_id in self.aea_config.all_components_id

    def test_component_configurations_setter(self):
        """Test component configuration setter."""
        assert self.aea_config.component_configurations == {}
        new_component_configurations = {
            self.dummy_skill_component_id: self.new_dummy_skill_config
        }
        self.aea_config.component_configurations = new_component_configurations

    def test_component_configurations_setter_negative(self):
        """Test component configuration setter with wrong configurations."""
        assert self.aea_config.component_configurations == {}
        new_component_configurations = {
            self.dummy_skill_component_id: {
                "handlers": {"dummy": {"class_name": "SomeClass"}}
            }
        }
        with pytest.raises(
            ValueError, match=r"Configuration of component .* is not valid.*"
        ):
            self.aea_config.component_configurations = new_component_configurations

    def test_aea_version_setter(self):
        """Test 'aea_version' setter."""
        new_version_specifier = "==0.1.0"
        self.aea_config.aea_version = new_version_specifier
        assert self.aea_config.aea_version == new_version_specifier
        assert self.aea_config.aea_version_specifiers == SpecifierSet(
            new_version_specifier
        )

    def test_update(self):
        """Test the update method."""
        new_private_key_paths = dict(ethereum="foo")
        expected_private_key_paths = dict(
            ethereum="foo",
            cosmos="cosmos_private_key.txt",
            fetchai="fetchai_private_key.txt",
        )
        self.aea_config.update(
            dict(
                component_configurations={
                    self.dummy_skill_component_id: self.new_dummy_skill_config
                },
                private_key_paths=new_private_key_paths,
                connection_private_key_paths=new_private_key_paths,
            )
        )
        assert (
            self.aea_config.component_configurations[self.dummy_skill_component_id]
            == self.new_dummy_skill_config
        )
        assert (
            dict(self.aea_config.private_key_paths.read_all())
            == expected_private_key_paths
        )
        assert (
            dict(self.aea_config.connection_private_key_paths.read_all())
            == expected_private_key_paths
        )

        # test idempotence
        self.aea_config.update(
            dict(
                component_configurations={
                    self.dummy_skill_component_id: self.new_dummy_skill_config
                }
            )
        )
        assert (
            self.aea_config.component_configurations[self.dummy_skill_component_id]
            == self.new_dummy_skill_config
        )

        # to json
        self.aea_config.json


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

    @mock.patch("aea.configurations.data_types.re.match", return_value=None)
    def test_public_id_from_str_not_matching(self, *mocks):
        """Test case for from_str method regex not matching."""
        with self.assertRaises(ValueError):
            PublicId.from_str("public_id_str")

    def test_public_id_from_json_positive(self):
        """Test case for from_json method positive result."""
        obj = {"author": AUTHOR, "name": "name", "version": "0.1.0"}
        PublicId.from_json(obj)

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

    def test_is_valid_str(self):
        """Test is_valid_str method."""
        assert PublicId.is_valid_str("author/name:0.1.0")
        assert not PublicId.is_valid_str("author!name:0.1.0")

    def test_try_from_str(self):
        """Test is_valid_str method."""
        assert PublicId.try_from_str("author/name:0.1.0")
        assert not PublicId.try_from_str("author!name:0.1.0")


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

    def test_name_and_author(self):
        """Test case for default_connection setter positive result."""
        agent_config = AgentConfig(agent_name="my_agent", author="fetchai")
        agent_config.name = "new_name"
        agent_config.author = "new_author"


class SpeechActContentConfigTestCase(TestCase):
    """Test case for SpeechActContentConfig class."""

    def test_speech_act_content_config_init_positive(self):
        """Test case for __init__ method positive result."""
        SpeechActContentConfig()

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
        ProtocolSpecification(
            name="my_protocol",
            author="fetchai",
            protocol_specification_id="some/author:0.1.0",
        )

    def test_json_positive(self):
        """Test case for json property positive result."""
        obj = ProtocolSpecification(
            name="my_protocol",
            author="fetchai",
            protocol_specification_id="some/author:0.1.0",
        )
        obj.json

    @mock.patch("aea.configurations.base.SpeechActContentConfig.from_json")
    def test_from_json_positive(self, *mocks):
        """Test case for from_json method positive result."""
        json_disc = {
            "name": "name",
            "author": AUTHOR,
            "version": "0.1.0",
            "license": "license",
            "description": "description",
            "speech_acts": {"arg1": "arg1", "arg2": "arg2"},
            "protocol_specification_id": "some/author:0.1.0",
        }
        ProtocolSpecification.from_json(json_disc)


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
    configuration = ProtocolConfig(
        "name", "author", "0.1.0", protocol_specification_id="some/author:0.1.0"
    )
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


def test_public_id_from_string():
    """Test parsing the public id from string."""
    public_id = PublicId.from_str("author/package:0.1.0")
    assert public_id.author == "author"
    assert public_id.name == "package"
    assert public_id.version == "0.1.0"


def test_public_id_from_string_without_version_string():
    """Test parsing the public id without version string."""
    public_id = PublicId.from_str("author/package")
    assert public_id.author == "author"
    assert public_id.name == "package"
    assert public_id.version == "latest"


def test_public_id_from_string_with_version_string_latest():
    """Test parsing the public id with version string 'latest'."""
    public_id = PublicId.from_str("author/package:latest")
    assert public_id.author == "author"
    assert public_id.name == "package"
    assert public_id.version == "latest"


def test_public_id_from_uri_path():
    """Test PublicId.from_uri_path"""
    result = PublicId.from_uri_path("author/package_name/0.1.0")
    assert result.name == "package_name"
    assert result.author == "author"
    assert result.version == "0.1.0"


def test_public_id_from_uri_path_wrong_input():
    """Test that when a bad formatted path is passed in input of PublicId.from_uri_path an exception is raised."""
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


def test_pubic_id_to_latest():
    """Test PublicId.to_latest"""
    public_id = PublicId("author", "name", "0.1.0")
    expected_public_id = PublicId("author", "name", "latest")
    actual_public_id = public_id.to_latest()
    assert expected_public_id == actual_public_id


def test_pubic_id_to_any():
    """Test PublicId.to_any"""
    public_id = PublicId("author", "name", "0.1.0")
    expected_public_id = PublicId("author", "name", "any")
    actual_public_id = public_id.to_any()
    assert expected_public_id == actual_public_id


def test_pubic_id_same_prefix():
    """Test PublicId.same_prefix"""
    same_1 = PublicId("author", "name", "0.1.0")
    same_2 = PublicId("author", "name", "0.1.1")
    different = PublicId("author", "different_name", "0.1.0")

    assert same_1.same_prefix(same_2)
    assert same_2.same_prefix(same_1)

    assert not different.same_prefix(same_1)
    assert not same_1.same_prefix(different)

    assert not different.same_prefix(same_2)
    assert not same_2.same_prefix(different)


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


def test_package_id_repr():
    """Test PackageId.__repr__"""
    package_id = PackageId(PackageType.PROTOCOL, PublicId("author", "name", "0.1.0"))
    assert repr(package_id) == "PackageId(protocol, author/name:0.1.0)"


def test_package_id_lt():
    """Test PackageId.__lt__"""
    package_id_1 = PackageId(PackageType.PROTOCOL, PublicId("author", "name", "0.1.0"))
    package_id_2 = PackageId(PackageType.PROTOCOL, PublicId("author", "name", "0.2.0"))

    assert package_id_1 < package_id_2


def test_package_id_from_uri_path():
    """Test PackageId.from_uri_path"""
    result = PackageId.from_uri_path("skill/author/package_name/0.1.0")
    assert str(result.package_type) == "skill"
    assert result.public_id.name == "package_name"
    assert result.public_id.author == "author"
    assert result.public_id.version == "0.1.0"


def test_package_id_to_uri_path():
    """Test PackageId.to_uri_path"""
    package_id = PackageId(PackageType.PROTOCOL, PublicId("author", "name", "0.1.0"))
    assert package_id.to_uri_path == "protocol/author/name/0.1.0"


def test_package_id_from_uri_path_negative():
    """Test PackageId.from_uri_path with invalid type"""
    with pytest.raises(
        ValueError,
        match="Input 'not_a_valid_type/author/package_name/0.1.0' is not well formatted.",
    ):
        PackageId.from_uri_path("not_a_valid_type/author/package_name/0.1.0")


def test_component_id_prefix_import_path():
    """Test ComponentId.prefix_import_path"""
    component_id = ComponentId(
        ComponentType.PROTOCOL, PublicId("author", "name", "0.1.0")
    )
    assert component_id.prefix_import_path == "packages.author.protocols.name"
    assert component_id.json


def test_component_id_same_prefix():
    """Test ComponentId.same_prefix"""
    component_id_1 = ComponentId(
        ComponentType.PROTOCOL, PublicId("author", "name", "0.1.0")
    )
    component_id_2 = ComponentId(
        ComponentType.PROTOCOL, PublicId("author", "name", "0.2.0")
    )
    assert component_id_1.same_prefix(component_id_2)


def test_component_configuration_load_file_not_found():
    """Test Component.load when a file is not found."""
    with mock.patch(
        "aea.configurations.loader.open_file", side_effect=FileNotFoundError
    ):
        with pytest.raises(FileNotFoundError):
            load_component_configuration(
                ComponentType.PROTOCOL, mock.MagicMock(spec=Path)
            )


def test_component_configuration_check_fingerprint_bad_directory():
    """Test ComponentConfiguration.check_fingerprint when a bad directory is provided."""
    config = ProtocolConfig(
        "name", "author", "0.1.0", protocol_specification_id="some/author:0.1.0"
    )
    with pytest.raises(ValueError, match="Directory .* is not valid."):
        config.check_fingerprint(Path("non_existing_directory"))


def test_component_configuration_check_fingerprint_different_fingerprints_vendor():
    """Test ComponentConfiguration.check_fingerprint when the fingerprints differ for a vendor package."""
    config = ProtocolConfig(
        "name", "author", "0.1.0", protocol_specification_id="some/author:0.1.0"
    )
    package_dir = Path("path", "to", "dir")
    error_regex = (
        f"Fingerprints for package {re.escape(str(package_dir))} do not match:\nExpected: {dict()}\nActual: {dict(foo='bar')}\n"
        + "Vendorized projects should not be tampered with, please revert any changes to protocol author/name:0.1.0"
    )

    with pytest.raises(ValueError, match=error_regex):
        with mock.patch(
            "aea.configurations.base._compute_fingerprint", return_value={"foo": "bar"}
        ):
            _compare_fingerprints(config, package_dir, True, PackageType.PROTOCOL)


def test_component_configuration_check_fingerprint_different_fingerprints_no_vendor():
    """Test ComponentConfiguration.check_fingerprint when the fingerprints differ for a non-vendor package."""
    config = ProtocolConfig(
        "name", "author", "0.1.0", protocol_specification_id="some/author:0.1.0"
    )
    package_dir = Path("path", "to", "dir")
    error_regex = (
        f"Fingerprints for package {re.escape(str(package_dir))} do not match:\nExpected: {dict()}\nActual: {dict(foo='bar')}\n"
        + "Please fingerprint the package before continuing: 'aea fingerprint protocol author/name:0.1.0"
    )

    with pytest.raises(ValueError, match=error_regex):
        with mock.patch(
            "aea.configurations.base._compute_fingerprint", return_value={"foo": "bar"}
        ):
            _compare_fingerprints(config, package_dir, False, PackageType.PROTOCOL)


def test_agent_fingerprint_different_fingerprints():
    """Test ComponentConfiguration.check_fingerprint for agent."""
    config = Mock()
    config.fingerprint = {}
    package_dir = Path("path", "to", "dir")
    error_regex = (
        f"Fingerprints for package {re.escape(str(package_dir))} do not match:\nExpected: {dict()}\nActual: {dict(foo='bar')}\n"
        + "Please fingerprint the package before continuing: 'aea fingerprint"
    )

    with pytest.raises(ValueError, match=error_regex):
        with mock.patch(
            "aea.configurations.base._compute_fingerprint", return_value={"foo": "bar"}
        ):
            _compare_fingerprints(config, package_dir, False, PackageType.AGENT)


def test_check_aea_version_when_it_fails():
    """Test the check for the AEA version when it fails."""
    config = ProtocolConfig(
        "name",
        "author",
        "0.1.0",
        aea_version=">0.1.0",
        protocol_specification_id="some/author:0.1.0",
    )
    with mock.patch("aea.configurations.base.__aea_version__", "0.1.0"):
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
        period=0.1,
        execution_timeout=1.0,
        max_reactions=100,
        decision_maker_handler=dict(dotted_path="", file_path=""),
        error_handler=dict(dotted_path="", file_path=""),
        skill_exception_policy="propagate",
        connection_exception_policy="propagate",
        default_routing={"author/name:0.1.0": "author/name:0.1.0"},
        currency_denominations={"fetchai": "fet"},
        loop_mode="sync",
        runtime_mode="async",
        storage_uri="some_uri_to_storage",
        task_manager_mode="threaded",
    )
    agent_config.default_connection = "author/name:0.1.0"
    agent_config.default_ledger = DEFAULT_LEDGER
    agent_config.json
    assert agent_config.package_id == PackageId.from_uri_path("agent/author/name/0.1.0")


def test_protocol_specification_attributes():
    """Test protocol specification attributes."""
    protocol_specification = ProtocolSpecification(
        "name", "author", "0.1.0", protocol_specification_id="some/author:0.1.0"
    )

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


def test_package_version_eq_negative():
    """Test package version __eq__."""
    v1 = PackageVersion("0.1.0")
    v2 = PackageVersion("0.2.0")
    assert v1 != v2


def test_package_version_lt():
    """Test package version __lt__."""
    v1 = PackageVersion("0.1.0")
    v2 = PackageVersion("0.2.0")
    v3 = PackageVersion("latest")
    assert v1 < v2 < v3


class TestDependencyGetPipInstallArgs:
    """Test 'get_pip_install_args' of 'Dependency' class."""

    @classmethod
    def setup_class(cls):
        """Set up the class."""
        cls.package_name = "package_name"
        cls.version = "<0.2.0,>=0.1.0"
        cls.custom_index = "https://test.pypi.org"
        cls.git_url = "https://github.com/some-author/some-repository.git"
        cls.ref = "develop"

    def test_only_name_and_version(self):
        """Test only with name and version."""
        # no index and no git
        dep = Dependency(self.package_name, self.version)
        assert dep.get_pip_install_args() == [
            f"{self.package_name}{self.version}",
        ]

    def test_name_version_index(self):
        """Test the method with name, version and index."""
        dep = Dependency(self.package_name, self.version, self.custom_index)
        assert dep.get_pip_install_args() == [
            "-i",
            self.custom_index,
            f"{self.package_name}{self.version}",
        ]

    def test_name_version_index_git(self):
        """Test the method when name, version, index and git fields are provided."""
        dep = Dependency(
            self.package_name, self.version, self.custom_index, self.git_url
        )
        git_url = f"git+{self.git_url}@{DEFAULT_GIT_REF}#egg={self.package_name}"
        assert dep.get_pip_install_args() == ["-i", self.custom_index, git_url]

    def test_name_version_index_git_ref(self):
        """Test the method when name, version, index, git and ref fields are provided."""
        dep = Dependency(
            self.package_name, self.version, self.custom_index, self.git_url, self.ref
        )
        git_url = f"git+{self.git_url}@{self.ref}#egg={self.package_name}"
        assert dep.get_pip_install_args() == ["-i", self.custom_index, git_url]


def test_dependencies_from_to_json():
    """Test serialization and deserialization of Dependencies object."""
    version_str = "==0.1.0"
    git_url = "https://some-git-repo.git"
    branch = "some-branch"
    dep1 = Dependency("package_1", version_str, DEFAULT_PYPI_INDEX_URL, git_url, branch)
    dep2 = Dependency("package_2", version_str)
    expected_obj = {"package_1": dep1, "package_2": dep2}
    expected_obj_json = dependencies_to_json(expected_obj)
    assert expected_obj_json == {
        "package_1": {
            "version": "==0.1.0",
            "index": DEFAULT_PYPI_INDEX_URL,
            "git": git_url,
            "ref": branch,
        },
        "package_2": {"version": version_str},
    }

    actual_obj = dependencies_from_json(expected_obj_json)
    assert expected_obj == actual_obj


def test_dependency_from_json_fail_more_than_one_key():
    """Test failure of Dependency.from_json due to more than one key at the top level."""
    bad_obj = {"field_1": {}, "field_2": {}}
    keys = set(bad_obj.keys())
    with pytest.raises(ValueError, match=f"Only one key allowed, found {keys}"):
        Dependency.from_json(bad_obj)


def test_dependency_from_json_fail_not_allowed_keys():
    """Test failure of Dependency.from_json due to unallowed keys"""
    bad_obj = {"field_1": {"not-allowed-key": "value"}}
    with pytest.raises(ValueError, match="Not allowed keys: {'not-allowed-key'}"):
        Dependency.from_json(bad_obj)


def test_dependency_to_string():
    """Test dependency.__str__ method."""
    dependency = Dependency(
        "package_1", "==0.1.0", "https://index.com", "https://some-repo.git", "branch"
    )
    assert (
        str(dependency)
        == "Dependency(name='package_1', version='==0.1.0', index='https://index.com', git='https://some-repo.git', ref='branch')"
    )


def test_check_public_id_consistency_negative():
    """Test ComponentId.check_public_id_consistency raises error when directory does not exists."""
    random_dir_name = random_string()
    with pytest.raises(ValueError, match=f"Directory {random_dir_name} is not valid."):
        component_configuration = ProtocolConfig(
            "name", "author", protocol_specification_id="some/author:0.1.0"
        )
        component_configuration.check_public_id_consistency(Path(random_dir_name))


def test_check_public_id_consistency_positive():
    """Test ComponentId.check_public_id_consistency works."""
    skill_config_path = Path(DUMMY_SKILL_PATH)
    loader = ConfigLoaders.from_package_type(PackageType.SKILL)
    skill_config = loader.load(skill_config_path.open())
    skill_config.check_public_id_consistency(Path(skill_config_path).parent)


def test_component_id_from_json():
    """Test ComponentId.from_json."""
    json_data = {
        "type": "connection",
        "author": "author",
        "name": "name",
        "version": "1.0.0",
    }
    assert ComponentId.from_json(json_data).json == json_data
