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


"""This module contains the tests for the aea.configurations.loader module."""
import os
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import OrderedDict
from unittest import mock
from unittest.mock import MagicMock

import pytest
import yaml

import aea
from aea.configurations.base import PackageType, ProtocolSpecification
from aea.configurations.loader import ConfigLoader
from aea.configurations.validation import make_jsonschema_base_uri
from aea.exceptions import AEAEnforceError
from aea.protocols.generator.common import load_protocol_specification

from tests.conftest import protocol_specification_files


def test_windows_uri_path():
    """Test uri path on running platform."""
    path = Path("aea", "configurations").absolute()
    output = make_jsonschema_base_uri(path)

    if os.name == "nt":
        assert output == f"file:///{'/'.join(path.parts)}/"
    else:
        assert output == f"file:/{'/'.join(path.parts)}/"


def test_config_loader_get_required_fields():
    """Test required fields of ConfigLoader."""
    config_loader = ConfigLoader.from_configuration_type(PackageType.PROTOCOL)
    config_loader.required_fields


@mock.patch.object(aea.configurations.loader, "yaml_dump")
@mock.patch.object(ConfigLoader, "validate")
@mock.patch("builtins.open")
def test_config_loader_dump_component(*_mocks):
    """Test ConfigLoader.dump"""
    config_loader = ConfigLoader.from_configuration_type(PackageType.PROTOCOL)
    configuration = MagicMock()
    config_loader.dump(configuration, open("foo"))


@mock.patch.object(aea.configurations.loader, "yaml_dump_all")
@mock.patch.object(ConfigLoader, "validate")
@mock.patch("builtins.open")
def test_config_loader_dump_agent_config(*_mocks):
    """Test ConfigLoader.dump"""
    config_loader = ConfigLoader.from_configuration_type(PackageType.AGENT)
    configuration = MagicMock(ordered_json={"component_configurations": []})
    config_loader.dump(configuration, open("foo"))


@mock.patch.object(aea.configurations.loader, "yaml_dump_all")
@mock.patch.object(ConfigLoader, "validate")
def test_config_loader_load_service_config(*_mocks):
    """Test ConfigLoader.dump"""

    config = OrderedDict(
        {
            "name": "Service",
            "author": "valory",
            "version": "0.1.0",
            "description": "Description",
            "aea_version": ">=1.0.0, <2.0.0",
            "license": "Apache-2.0",
            "agent": "agent",
            "network": "hardhat",
            "number_of_agents": "4",
        }
    )

    with TemporaryDirectory() as temp_dir:
        schema_file = Path(temp_dir, "schema.json").absolute()
        config_file = Path(temp_dir, "service.yaml")
        schema_file.write_text("{}")

        config_loader_cls = MagicMock()
        config_loader_cls.schema = str(schema_file)
        config_loader_cls.from_json = lambda x: MagicMock(**x)

        config_loader = ConfigLoader.from_configuration_type(
            PackageType.SERVICE, {PackageType.SERVICE: config_loader_cls}
        )

        dummy_obj = MagicMock()
        dummy_obj.package_type = PackageType.SERVICE
        dummy_obj.ordered_json = config

        config_loader.dump(dummy_obj, config_file.open("w+"))
        service_config = config_loader.load(config_file.open("r"))
        assert any([getattr(service_config, key) == val for key, val in config.items()])


@pytest.mark.parametrize("spec_file_path", protocol_specification_files)
def test_load_protocol_specification(spec_file_path):
    """Test for the utility function 'load_protocol_specification'"""
    result = load_protocol_specification(spec_file_path)
    assert type(result) == ProtocolSpecification


@mock.patch("aea.protocols.generator.common.open_file")
@mock.patch.object(ConfigLoader, "validate")
def test_load_protocol_specification_only_first_part(*_mocks):
    """Test 'load_protocol_specification' with only the first part."""
    valid_protocol_specification = dict(
        name="name",
        author="author",
        version="0.1.0",
        license="",
        aea_version="0.1.0",
        speech_acts={"example": {}},
        protocol_specification_id="test/test:0.1.0",
        description="some",
    )
    with mock.patch.object(
        yaml, "safe_load_all", return_value=[valid_protocol_specification]
    ):
        load_protocol_specification("foo")


@mock.patch("aea.protocols.generator.common.open_file")
@mock.patch.object(ConfigLoader, "validate")
def test_load_protocol_specification_two_parts(*_mocks):
    """Test 'load_protocol_specification' with two parts."""
    valid_protocol_specification = dict(
        name="name",
        author="author",
        version="0.1.0",
        license="",
        aea_version="0.1.0",
        speech_acts={"example": {}},
        protocol_specification_id="test/test:0.1.0",
        description="some",
    )
    with mock.patch.object(
        yaml,
        "safe_load_all",
        return_value=[valid_protocol_specification, valid_protocol_specification],
    ):
        load_protocol_specification("foo")


def test_load_protocol_specification_too_many_parts():
    """Test 'load_protocol_specification' with more than three parts."""
    with pytest.raises(
        ValueError,
        match="Incorrect number of Yaml documents in the protocol specification.",
    ):
        with mock.patch.object(
            yaml, "safe_load_all", return_value=[{}] * 4
        ), mock.patch("aea.protocols.generator.common.open_file"):
            load_protocol_specification("foo")


@mock.patch.object(aea, "__version__", "0.1.0")
def test_load_package_configuration_with_incompatible_aea_version(*_mocks):
    """Test that loading a package configuration with incompatible AEA version raises an error."""
    config_loader = ConfigLoader.from_configuration_type(
        PackageType.PROTOCOL, skip_aea_validation=False
    )
    specifier_set = "<2.0.0,>=1.0.0"
    file = StringIO(f"name: some_protocol\naea_version: '{specifier_set}'")
    with pytest.raises(
        AEAEnforceError,
        match=f"AEA version in use '0.1.0' is not compatible with the specifier set '{specifier_set}'.",
    ):
        config_loader.load(file)
