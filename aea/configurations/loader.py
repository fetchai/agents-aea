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

"""Implementation of the parser for configuration file."""

import inspect
import json
import os
import re
from pathlib import Path
from typing import Dict, Generic, List, TextIO, Type, TypeVar, Union

import jsonschema
from jsonschema import Draft4Validator

import yaml
from yaml import SafeLoader

from aea.configurations.base import (
    AgentConfig,
    ConnectionConfig,
    ContractConfig,
    PackageType,
    ProtocolConfig,
    ProtocolSpecification,
    SkillConfig,
)
from aea.helpers.base import yaml_dump, yaml_load

_CUR_DIR = os.path.dirname(inspect.getfile(inspect.currentframe()))  # type: ignore
_SCHEMAS_DIR = os.path.join(_CUR_DIR, "schemas")

T = TypeVar(
    "T",
    AgentConfig,
    SkillConfig,
    ConnectionConfig,
    ContractConfig,
    ProtocolConfig,
    ProtocolSpecification,
)


def make_jsonschema_base_uri(base_uri_path: Path) -> str:
    """
    Make the JSONSchema base URI, cross-platform.

    :param base_uri_path: the path to the base directory.
    :return: the string in URI form.
    """
    if os.name == "nt":
        root_path = "file:///{}/".format("/".join(base_uri_path.absolute().parts))
    else:
        root_path = "file://{}/".format(base_uri_path.absolute())
    return root_path


class ConfigLoader(Generic[T]):
    """This class implement parsing, serialization and validation functionalities for the 'aea' configuration files."""

    def __init__(self, schema_filename: str, configuration_class: Type[T]):
        """
        Initialize the parser for configuration files.

        :param schema_filename: the path to the JSON-schema file in 'aea/configurations/schemas'.
        :param configuration_class: the configuration class (e.g. AgentConfig, SkillConfig etc.)
        """
        base_uri = Path(_SCHEMAS_DIR)
        self._schema = json.load((base_uri / schema_filename).open())
        root_path = make_jsonschema_base_uri(base_uri)
        self._resolver = jsonschema.RefResolver(root_path, self._schema)
        self._validator = Draft4Validator(self._schema, resolver=self._resolver)
        self._configuration_class = configuration_class  # type: Type[T]

    @property
    def validator(self) -> Draft4Validator:
        """Get the json schema validator."""
        return self._validator

    @property
    def required_fields(self) -> List[str]:
        """
        Get required fields.

        :return: list of required fields.
        """
        return self._schema["required"]

    @property
    def configuration_class(self) -> Type[T]:
        """Get the configuration class of the loader."""
        return self._configuration_class

    def load_protocol_specification(self, file_pointer: TextIO) -> T:
        """
        Load an agent configuration file.

        :param file_pointer: the file pointer to the configuration file
        :return: the configuration object.
        :raises
        """
        yaml_data = yaml.safe_load_all(file_pointer)
        yaml_documents = list(yaml_data)
        configuration_file_json = yaml_documents[0]
        if len(yaml_documents) == 1:
            protobuf_snippets_json = {}
            dialogue_configuration = {}  # type: Dict
        elif len(yaml_documents) == 2:
            protobuf_snippets_json = (
                {} if "initiation" in yaml_documents[1] else yaml_documents[1]
            )
            dialogue_configuration = (
                yaml_documents[1] if "initiation" in yaml_documents[1] else {}
            )
        elif len(yaml_documents) == 3:
            protobuf_snippets_json = yaml_documents[1]
            dialogue_configuration = yaml_documents[2]
        else:
            raise ValueError(
                "Incorrect number of Yaml documents in the protocol specification."
            )

        self.validator.validate(instance=configuration_file_json)

        protocol_specification = self.configuration_class.from_json(
            configuration_file_json
        )
        protocol_specification.protobuf_snippets = protobuf_snippets_json
        protocol_specification.dialogue_config = dialogue_configuration
        return protocol_specification

    def load(self, file_pointer: TextIO) -> T:
        """
        Load an agent configuration file.

        :param file_pointer: the file pointer to the configuration file
        :return: the configuration object.
        :raises
        """
        configuration_file_json = yaml_load(file_pointer)

        self.validator.validate(instance=configuration_file_json)

        key_order = list(configuration_file_json.keys())
        configuration_obj = self.configuration_class.from_json(configuration_file_json)
        configuration_obj._key_order = key_order  # pylint: disable=protected-access
        return configuration_obj

    def dump(self, configuration: T, file_pointer: TextIO) -> None:
        """Dump a configuration.

        :param configuration: the configuration to be dumped.
        :param file_pointer: the file pointer to the configuration file
        :return: None
        """
        result = configuration.ordered_json
        self.validator.validate(instance=result)
        yaml_dump(result, file_pointer)

    @classmethod
    def from_configuration_type(
        cls, configuration_type: Union[PackageType, str]
    ) -> "ConfigLoader":
        """Get the configuration loader from the type."""
        configuration_type = PackageType(configuration_type)
        return ConfigLoaders.from_package_type(configuration_type)


class ConfigLoaders:
    """Configuration Loader class to load any package type."""

    _from_configuration_type_to_loaders = {
        PackageType.AGENT: ConfigLoader("aea-config_schema.json", AgentConfig),
        PackageType.PROTOCOL: ConfigLoader(
            "protocol-config_schema.json", ProtocolConfig
        ),
        PackageType.CONNECTION: ConfigLoader(
            "connection-config_schema.json", ConnectionConfig
        ),
        PackageType.SKILL: ConfigLoader("skill-config_schema.json", SkillConfig),
        PackageType.CONTRACT: ConfigLoader(
            "contract-config_schema.json", ContractConfig
        ),
    }  # type: Dict[PackageType, ConfigLoader]

    @classmethod
    def from_package_type(
        cls, configuration_type: Union[PackageType, str]
    ) -> "ConfigLoader":
        """
        Get a config loader from the configuration type.

        :param configuration_type: the configuration type
        """
        configuration_type = PackageType(configuration_type)
        return cls._from_configuration_type_to_loaders[configuration_type]


def _config_loader():
    envvar_matcher = re.compile(r"\${([^}^{]+)\}")

    def envvar_constructor(_loader, node):  # pragma: no cover
        """Extract the matched value, expand env variable, and replace the match."""
        node_value = node.value
        match = envvar_matcher.match(node_value)
        env_var = match.group()[2:-1]

        # check for defaults
        var_name, default_value = env_var.split(":")
        var_name = var_name.strip()
        default_value = default_value.strip()
        var_value = os.getenv(var_name, default_value)
        return var_value + node_value[match.end() :]

    yaml.add_implicit_resolver("!envvar", envvar_matcher, None, SafeLoader)
    yaml.add_constructor("!envvar", envvar_constructor, SafeLoader)


# TODO: instead of this, create custom loader and use it
#       by wrapping yaml.safe_load to use it
_config_loader()
