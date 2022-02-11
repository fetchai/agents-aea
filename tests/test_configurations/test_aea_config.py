# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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
"""This module contains the tests for the aea configurations."""
import io
from enum import Enum
from pathlib import Path
from textwrap import dedent
from typing import Any, List, Sequence
from unittest import TestCase

import pytest
import yaml
from jsonschema.exceptions import ValidationError  # type: ignore

from aea.aea import AEA
from aea.aea_builder import AEABuilder
from aea.configurations.base import (
    AgentConfig,
    ComponentId,
    ComponentType,
    PackageType,
    PublicId,
)
from aea.configurations.loader import ConfigLoader, ConfigLoaders
from aea.exceptions import AEAValidationError
from aea.helpers.exception_policy import ExceptionPolicyEnum
from aea.helpers.yaml_utils import yaml_load_all

from tests.conftest import CUR_PATH, ROOT_DIR


class NotSet(type):
    """Definition to use when variable is not set."""


base_config = dedent(
    """
agent_name: my_seller_aea
author: solarw
version: 0.1.0
license: Apache-2.0
fingerprint: {}
fingerprint_ignore_patterns: []
aea_version: '>=1.0.0, <2.0.0'
description: ''
connections: []
contracts: []
protocols: []
skills: []
default_connection: null
default_ledger: cosmos
required_ledgers: [cosmos]
private_key_paths:
    cosmos: tests/data/cosmos_private_key.txt
connection_private_key_paths:
    cosmos: tests/data/cosmos_private_key.txt
dependencies: {}
"""
)


class BaseConfigTestVariable(TestCase):
    """Base class to test aea config variables."""

    OPTION_NAME: str = ""
    CONFIG_ATTR_NAME: str = ""
    GOOD_VALUES: Sequence[Any] = []
    INCORRECT_VALUES: List[Any] = []
    BASE_CONFIG: str = base_config
    REQUIRED: bool = False
    AEA_ATTR_NAME: str = ""
    AEA_DEFAULT_VALUE: Any = None

    @classmethod
    def setUpClass(cls) -> None:
        """Skip tests for base class."""
        if cls is BaseConfigTestVariable:
            pytest.skip("base class")
        super(BaseConfigTestVariable, cls).setUpClass()

    @property
    def loader(self) -> ConfigLoader:
        """
        Create ConfigLoader for Agent config.

        :return: ConfigLoader for AgentConfig
        """
        return ConfigLoader.from_configuration_type(PackageType.AGENT)

    def _make_configuration_yaml(self, value: Any = NotSet) -> str:
        """Create yaml text configuration file for aea with value for tested parameter.

        :param value: value to set for test config parameter

        :return: string yaml
        """
        if value is NotSet:
            return self.BASE_CONFIG
        value = self._un_enum_value(value)
        return f"{self.BASE_CONFIG}\n" + yaml.dump({self.OPTION_NAME: value})

    def _make_configuration(self, value: Any = NotSet) -> AgentConfig:
        """Create AgentConfig file using generated yaml file with value set.

        :param value: value to set for test config parameter

        :return: AgentConfig
        """
        config_data = self._make_configuration_yaml(value)
        f = io.StringIO(config_data)
        return self.loader.load(f)

    @staticmethod
    def _un_enum_value(value: Any) -> Any:
        """Return enum.value if value is enum, otherwise just value."""
        if isinstance(value, Enum):
            value = value.value
        return value

    def test_no_variable_passed(self) -> None:
        """Test option not specified in cofig."""
        if self.REQUIRED:
            with self.assertRaises(ValidationError):
                self._make_configuration(NotSet)
            return
        configuration = self._make_configuration(NotSet)
        assert getattr(configuration, self.CONFIG_ATTR_NAME) is None

    def test_good_value_passed(self) -> None:
        """Test correct values parsed and set."""
        for good_value in self.GOOD_VALUES:
            good_value = self._un_enum_value(good_value)
            configuration = self._make_configuration(good_value)
            assert getattr(configuration, self.CONFIG_ATTR_NAME) == good_value

    def test_incorrect_value_passed(self) -> None:
        """Test validation error on incorrect values."""
        for incorrect_value in self.INCORRECT_VALUES:
            with pytest.raises(
                AEAValidationError,
                match="The following errors occurred during validation:",
            ):
                self._make_configuration(incorrect_value)

    def _get_aea_value(self, aea: AEA) -> Any:
        """Get AEA attribute value.

        :param aea: AEA instance to get attribute value from.

        :return: value of attribute.
        """
        return getattr(aea, self.AEA_ATTR_NAME)

    def test_builder_applies_default_value_to_aea(self) -> None:
        """Test AEABuilder applies default value to AEA instance when option is not specified in config."""
        configuration = self._make_configuration(NotSet)
        builder = AEABuilder()
        builder.set_from_configuration(configuration, aea_project_path=Path("."))
        aea = builder.build()

        assert self._get_aea_value(aea) == self.AEA_DEFAULT_VALUE

    def test_builder_applies_config_value_to_aea(self) -> None:
        """Test AEABuilder applies value to AEA instance when option is specified in config."""
        for good_value in self.GOOD_VALUES:
            configuration = self._make_configuration(good_value)
            builder = AEABuilder()
            builder.set_from_configuration(
                configuration, aea_project_path=Path(ROOT_DIR)
            )
            aea = builder.build()

            assert self._get_aea_value(aea) == good_value


class TestPeriodConfigVariable(BaseConfigTestVariable):
    """Test `period` aea config option."""

    OPTION_NAME = "period"
    CONFIG_ATTR_NAME = "period"
    GOOD_VALUES = [0.1, 1.1]
    INCORRECT_VALUES = [0, "sTrING?", -1]
    REQUIRED = False
    AEA_ATTR_NAME = "_period"
    AEA_DEFAULT_VALUE = AEABuilder.DEFAULT_AGENT_ACT_PERIOD


class TestExecutionTimeoutConfigVariable(BaseConfigTestVariable):
    """Test `execution_timeout` aea config option."""

    OPTION_NAME = "execution_timeout"
    CONFIG_ATTR_NAME = "execution_timeout"
    GOOD_VALUES = [0, 1.1]
    INCORRECT_VALUES = ["sTrING?", -1]
    REQUIRED = False
    AEA_ATTR_NAME = "_execution_timeout"
    AEA_DEFAULT_VALUE = AEABuilder.DEFAULT_EXECUTION_TIMEOUT


class TestMaxReactionsConfigVariable(BaseConfigTestVariable):
    """Test `max_reactions` aea config option."""

    OPTION_NAME = "max_reactions"
    CONFIG_ATTR_NAME = "max_reactions"
    GOOD_VALUES = [1, 10]
    INCORRECT_VALUES = ["sTrING?", -1, 0, 1.1]
    REQUIRED = False
    AEA_ATTR_NAME = "max_reactions"
    AEA_DEFAULT_VALUE = AEABuilder.DEFAULT_MAX_REACTIONS


class TestLoopModeConfigVariable(BaseConfigTestVariable):
    """Test `loop_mode` aea config option."""

    OPTION_NAME = "loop_mode"
    CONFIG_ATTR_NAME = "loop_mode"
    GOOD_VALUES = ["async", "sync"]
    INCORRECT_VALUES = [None, "sTrING?", -1]
    REQUIRED = False
    AEA_ATTR_NAME = "_loop_mode"
    AEA_DEFAULT_VALUE = AEABuilder.DEFAULT_LOOP_MODE

    def _get_aea_value(self, aea: AEA) -> Any:
        """Get AEA attribute value.

        :param aea: AEA isntance to get atribute value from.

        :return: value of attribute.
        """
        return aea.runtime.loop_mode


class TestSkillExceptionPolicyConfigVariable(BaseConfigTestVariable):
    """Test `skill_exception_policy` aea config option."""

    OPTION_NAME = "skill_exception_policy"
    CONFIG_ATTR_NAME = "skill_exception_policy"
    GOOD_VALUES = ExceptionPolicyEnum  # type: ignore
    INCORRECT_VALUES = [None, "sTrING?", -1]
    REQUIRED = False
    AEA_ATTR_NAME = "_skills_exception_policy"
    AEA_DEFAULT_VALUE = ExceptionPolicyEnum.propagate


class TestStorageUriConfigVariable(BaseConfigTestVariable):
    """Test `storage_uri` aea config option."""

    OPTION_NAME = "storage_uri"
    CONFIG_ATTR_NAME = "storage_uri"
    GOOD_VALUES = ["sqlite://test"]  # type: ignore
    INCORRECT_VALUES = [None, -1]
    REQUIRED = False
    AEA_ATTR_NAME = "_storage_uri"
    AEA_DEFAULT_VALUE = None


class TestConnectionExceptionPolicyConfigVariable(BaseConfigTestVariable):
    """Test `skill_exception_policy` aea config option."""

    OPTION_NAME = "connection_exception_policy"
    CONFIG_ATTR_NAME = "connection_exception_policy"
    GOOD_VALUES = ExceptionPolicyEnum  # type: ignore
    INCORRECT_VALUES = [None, "sTrING?", -1]
    REQUIRED = False
    AEA_ATTR_NAME = "_connection_exception_policy"
    AEA_DEFAULT_VALUE = ExceptionPolicyEnum.propagate


class TestRuntimeModeConfigVariable(BaseConfigTestVariable):
    """Test `runtime_mode` aea config option."""

    OPTION_NAME = "runtime_mode"
    CONFIG_ATTR_NAME = "runtime_mode"
    GOOD_VALUES = ["threaded", "async"]
    INCORRECT_VALUES = [None, "sTrING?", -1]
    REQUIRED = False
    AEA_ATTR_NAME = "_runtime_mode"
    AEA_DEFAULT_VALUE = AEABuilder.DEFAULT_RUNTIME_MODE


def test_agent_configuration_loading_multipage():
    """Test agent configuration loading, multi-page case."""
    loader = ConfigLoaders.from_package_type(PackageType.AGENT)
    agent_config = loader.load(
        Path(CUR_PATH, "data", "aea-config.example_multipage.yaml").open()
    )

    # test main agent configuration loaded correctly
    assert agent_config.agent_name == "myagent"
    assert agent_config.author == "fetchai"

    # test component configurations loaded correctly
    assert len(agent_config.component_configurations) == 1
    keys = list(agent_config.component_configurations)
    dummy_skill_public_id = PublicId.from_str("dummy_author/dummy:0.1.0")
    expected_component_id = ComponentId("skill", dummy_skill_public_id)
    assert keys[0] == expected_component_id


def test_agent_configuration_loading_multipage_when_empty_file():
    """Test agent configuration loading, multi-page case, in case of empty file."""
    with pytest.raises(ValueError, match="Agent configuration file was empty."):
        loader = ConfigLoaders.from_package_type(PackageType.AGENT)
        loader.load(io.StringIO())


def test_agent_configuration_loading_multipage_when_type_not_found():
    """Test agent configuration loading, multi-page case, when type not found in some component."""
    # remove type field manually
    file = Path(CUR_PATH, "data", "aea-config.example_multipage.yaml").open()
    jsons = list(yaml.safe_load_all(file))
    jsons[1].pop("type")
    modified_file = io.StringIO()
    yaml.safe_dump_all(jsons, modified_file)
    modified_file.seek(0)

    with pytest.raises(
        ValueError, match="There are missing fields in component id 1: {'type'}."
    ):
        loader = ConfigLoaders.from_package_type(PackageType.AGENT)
        loader.load(modified_file)


def test_agent_configuration_loading_multipage_when_same_id():
    """Test agent configuration loading, multi-page case, when there are two components with the same id."""
    file = Path(CUR_PATH, "data", "aea-config.example_multipage.yaml").open()
    jsons = list(yaml.safe_load_all(file))
    # add twice the last component
    jsons.append(jsons[-1])
    modified_file = io.StringIO()
    yaml.safe_dump_all(jsons, modified_file)
    modified_file.seek(0)

    with pytest.raises(
        ValueError,
        match=r"Configuration of component \(skill, dummy_author/dummy:0.1.0\) occurs more than once.",
    ):
        loader = ConfigLoaders.from_package_type(PackageType.AGENT)
        loader.load(modified_file)


def test_agent_configuration_loading_multipage_validation_error():
    """Test agent configuration loading, multi-page case, when the configuration is invalid."""
    file = Path(CUR_PATH, "data", "aea-config.example_multipage.yaml").open()
    jsons = list(yaml.safe_load_all(file))
    # make invalid the last component configuration
    jsons[-1]["invalid_attribute"] = "foo"
    modified_file = io.StringIO()
    yaml.safe_dump_all(jsons, modified_file)
    modified_file.seek(0)

    with pytest.raises(
        ValueError,
        match=r"Configuration of component \(skill, dummy_author/dummy:0.1.0\) is not valid.",
    ):
        loader = ConfigLoaders.from_package_type(PackageType.AGENT)
        loader.load(modified_file)


@pytest.mark.parametrize(
    "component_type",
    [
        ComponentType.PROTOCOL,
        ComponentType.CONNECTION,
        ComponentType.CONTRACT,
        ComponentType.SKILL,
    ],
)
def test_agent_configuration_loading_multipage_positive_case(component_type):
    """Test agent configuration loading, multi-page case, positive case."""
    public_id = PublicId("dummy_author", "dummy", "0.1.0")
    file = Path(CUR_PATH, "data", "aea-config.example.yaml").open()
    json_data = yaml.safe_load(file)
    json_data[component_type.to_plural()].append(str(public_id))
    modified_file = io.StringIO()
    yaml.safe_dump(json_data, modified_file)
    modified_file.flush()
    modified_file.write("---\n")
    modified_file.write(f"public_id: {public_id}\n")
    modified_file.write(f"type: {component_type.value}\n")
    modified_file.seek(0)
    expected_component_id = ComponentId(
        component_type, PublicId("dummy_author", "dummy", "0.1.0")
    )

    loader = ConfigLoaders.from_package_type(PackageType.AGENT)
    agent_config = loader.load(modified_file)
    assert isinstance(agent_config.component_configurations, dict)
    assert len(agent_config.component_configurations)
    assert set(agent_config.component_configurations.keys()) == {expected_component_id}


def test_agent_configuration_dump_multipage():
    """Test agent configuration dump with component configuration."""
    loader = ConfigLoaders.from_package_type(PackageType.AGENT)
    agent_config = loader.load(
        Path(CUR_PATH, "data", "aea-config.example_multipage.yaml").open()
    )

    # test main agent configuration loaded correctly
    assert agent_config.agent_name == "myagent"
    assert agent_config.author == "fetchai"

    # test component configurations loaded correctly
    assert len(agent_config.component_configurations) == 1
    fp = io.StringIO()
    loader.dump(agent_config, fp)
    fp.seek(0)
    agent_config = yaml_load_all(fp)
    assert agent_config[0]["agent_name"] == "myagent"
    assert agent_config[1]["public_id"] == "dummy_author/dummy:0.1.0"
    assert agent_config[1]["type"] == "skill"


def test_agent_configuration_dump_multipage_fails_bad_component_configuration():
    """Test agent configuration dump with INCORRECT component configuration."""
    loader = ConfigLoaders.from_package_type(PackageType.AGENT)
    agent_config = loader.load(
        Path(CUR_PATH, "data", "aea-config.example_multipage.yaml").open()
    )

    # test main agent configuration loaded correctly
    assert agent_config.agent_name == "myagent"
    assert agent_config.author == "fetchai"

    # test component configurations loaded correctly
    assert len(agent_config.component_configurations) == 1
    list(agent_config.component_configurations.values())[0][
        "BAD FIELD"
    ] = "not in specs!"
    fp = io.StringIO()
    with pytest.raises(
        ValueError,
        match="Configuration of component .* is not valid. ExtraPropertiesError: properties not expected: BAD FIELD",
    ):
        loader.dump(agent_config, fp)


class TestTaskManagerModeConfigVariable(BaseConfigTestVariable):
    """Test `task_manager_mode` aea config option."""

    OPTION_NAME = "task_manager_mode"
    CONFIG_ATTR_NAME = "task_manager_mode"
    GOOD_VALUES = ["threaded", "multiprocess"]
    INCORRECT_VALUES = [None, "sTrING?", -1]
    REQUIRED = False
    AEA_ATTR_NAME = "_task_manager_mode"
    AEA_DEFAULT_VALUE = AEABuilder.DEFAULT_TASKMANAGER_MODE
