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
"""This module contains the tests for the aea configurations."""
import io
from enum import Enum
from pathlib import Path
from textwrap import dedent
from typing import Any, List, Sequence
from unittest import TestCase

from jsonschema.exceptions import ValidationError  # type: ignore

import pytest

import yaml

from aea.aea import AEA
from aea.aea_builder import AEABuilder
from aea.configurations.base import AgentConfig, PackageType
from aea.configurations.loader import ConfigLoader
from aea.helpers.exception_policy import ExceptionPolicyEnum

from tests.conftest import ROOT_DIR


class NotSet(type):
    """Definition to use when variable is not set."""


base_config = dedent(
    """
agent_name: my_seller_aea
author: solarw
version: 0.1.0
license: Apache-2.0
aea_version: 0.3.0
description: ''
connections: []
contracts: []
protocols: []
skills: []
default_connection: fetchai/stub:0.6.0
default_ledger: cosmos
private_key_paths:
    cosmos: tests/data/cosmos_private_key.txt
connection_private_key_paths:
    cosmos: tests/data/cosmos_private_key.txt
registry_path: ../packages
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
            with self.assertRaises(ValidationError):
                self._make_configuration(incorrect_value)

    def _get_aea_value(self, aea: AEA) -> Any:
        """Get AEA attribute value.

        :param aea: AEA isntance to get atribute value from.

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


class TestTimeoutConfigVariable(BaseConfigTestVariable):
    """Test `timeout` aea config option."""

    OPTION_NAME = "timeout"
    CONFIG_ATTR_NAME = "timeout"
    GOOD_VALUES = [0, 1.1]
    INCORRECT_VALUES = ["sTrING?", -1]
    REQUIRED = False
    AEA_ATTR_NAME = "_timeout"
    AEA_DEFAULT_VALUE = AEABuilder.DEFAULT_AGENT_LOOP_TIMEOUT


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
    GOOD_VALUES = ["sync", "async"]
    INCORRECT_VALUES = [None, "sTrING?", -1]
    REQUIRED = False
    AEA_ATTR_NAME = "_loop_mode"
    AEA_DEFAULT_VALUE = AEABuilder.DEFAULT_LOOP_MODE


class TestSkillExceptionPolicyConfigVariable(BaseConfigTestVariable):
    """Test `skill_exception_policy` aea config option."""

    OPTION_NAME = "skill_exception_policy"
    CONFIG_ATTR_NAME = "skill_exception_policy"
    GOOD_VALUES = ExceptionPolicyEnum  # type: ignore
    INCORRECT_VALUES = [None, "sTrING?", -1]
    REQUIRED = False
    AEA_ATTR_NAME = "_skills_exception_policy"
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
