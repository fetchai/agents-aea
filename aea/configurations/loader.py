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
from pathlib import Path
from typing import Dict, Generic, List, TextIO, Type, TypeVar, Union, cast

import yaml

from aea.configurations.base import (
    AgentConfig,
    ComponentConfiguration,
    ComponentId,
    ComponentType,
    ConnectionConfig,
    ContractConfig,
    PACKAGE_TYPE_TO_CONFIG_CLASS,
    PackageConfiguration,
    PackageType,
    ProtocolConfig,
    ProtocolSpecification,
    SkillConfig,
)
from aea.configurations.validation import ConfigValidator, make_jsonschema_base_uri
from aea.helpers.io import open_file
from aea.helpers.yaml_utils import yaml_dump, yaml_dump_all, yaml_load, yaml_load_all


_STARTING_INDEX_CUSTOM_CONFIGS = 1


_ = make_jsonschema_base_uri  # for tests compatibility

T = TypeVar(
    "T",
    AgentConfig,
    SkillConfig,
    ConnectionConfig,
    ContractConfig,
    ProtocolConfig,
    ProtocolSpecification,
)


class BaseConfigLoader:
    """Base class for configuration loader classes."""

    def __init__(self, schema_filename: str) -> None:
        """
        Initialize the parser for configuration files.

        :param schema_filename: the path to the JSON-schema file in 'aea/configurations/schemas'.
        """
        self._validator = ConfigValidator(schema_filename)

    @property
    def validator(self) -> ConfigValidator:
        """Get the json schema validator."""
        return self._validator

    def validate(self, json_data: Dict) -> None:
        """
        Validate a JSON object.

        :param json_data: the JSON data.
        """
        self.validator.validate(json_data)

    @property
    def required_fields(self) -> List[str]:
        """
        Get the required fields.

        :return: list of required fields.
        """
        return self.validator.required_fields


class ConfigLoader(Generic[T], BaseConfigLoader):
    """Parsing, serialization and validation for package configuration files."""

    def __init__(self, schema_filename: str, configuration_class: Type[T]) -> None:
        """
        Initialize the parser for configuration files.

        :param schema_filename: the path to the JSON-schema file in 'aea/configurations/schemas'.
        :param configuration_class: the configuration class (e.g. AgentConfig, SkillConfig etc.)
        """
        super().__init__(schema_filename)
        self._configuration_class = configuration_class  # type: Type[T]

    @property
    def configuration_class(self) -> Type[T]:
        """Get the configuration class of the loader."""
        return self._configuration_class

    def load_protocol_specification(
        self, file_pointer: TextIO
    ) -> ProtocolSpecification:
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

        self.validate(configuration_file_json)

        protocol_specification = cast(
            ProtocolSpecification,
            self.configuration_class.from_json(configuration_file_json),
        )
        protocol_specification.protobuf_snippets = protobuf_snippets_json
        protocol_specification.dialogue_config = dialogue_configuration
        return protocol_specification

    def load(self, file_pointer: TextIO) -> T:
        """
        Load a configuration file.

        :param file_pointer: the file pointer to the configuration file
        :return: the configuration object.
        """
        if self.configuration_class.package_type == PackageType.AGENT:
            return cast(T, self._load_agent_config(file_pointer))
        return self._load_component_config(file_pointer)

    def dump(self, configuration: T, file_pointer: TextIO) -> None:
        """Dump a configuration.

        :param configuration: the configuration to be dumped.
        :param file_pointer: the file pointer to the configuration file
        """
        if self.configuration_class.package_type == PackageType.AGENT:
            self._dump_agent_config(cast(AgentConfig, configuration), file_pointer)
        else:
            self._dump_component_config(configuration, file_pointer)

    @classmethod
    def from_configuration_type(
        cls, configuration_type: Union[PackageType, str]
    ) -> "ConfigLoader":
        """Get the configuration loader from the type."""
        configuration_type = PackageType(configuration_type)
        return ConfigLoaders.from_package_type(configuration_type)

    def _load_component_config(self, file_pointer: TextIO) -> T:
        """Load a component configuration."""
        configuration_file_json = yaml_load(file_pointer)
        return self._load_from_json(configuration_file_json)

    def _load_from_json(self, configuration_file_json: Dict) -> T:
        """Load component configuration from JSON object."""
        self.validate(configuration_file_json)
        key_order = list(configuration_file_json.keys())
        configuration_obj = cast(
            T, self.configuration_class.from_json(configuration_file_json)
        )
        configuration_obj._key_order = key_order  # pylint: disable=protected-access
        return configuration_obj

    def load_agent_config_from_json(
        self, configuration_json: List[Dict], validate: bool = True
    ) -> AgentConfig:
        """
        Load agent configuration from configuration json data.

        :param configuration_json: list of dicts with aea configuration
        :param validate: whether or not to validate

        :return: AgentConfig instance
        """
        if len(configuration_json) == 0:
            raise ValueError("Agent configuration file was empty.")
        agent_config_json = configuration_json[0]
        if validate:
            self.validate(agent_config_json)
        key_order = list(agent_config_json.keys())
        agent_configuration_obj = cast(
            AgentConfig, self.configuration_class.from_json(agent_config_json)
        )
        agent_configuration_obj._key_order = (  # pylint: disable=protected-access
            key_order
        )

        component_configurations = self._get_component_configurations(
            configuration_json
        )
        agent_configuration_obj.component_configurations = component_configurations
        return agent_configuration_obj

    def _get_component_configurations(
        self, configuration_file_jsons: List[Dict]
    ) -> Dict[ComponentId, Dict]:
        """
        Get the component configurations from the tail pages of the aea-config.yaml file.

        :param configuration_file_jsons: the JSON objects of the custom configurations of a aea-config.yaml file.
        :return: a dictionary whose keys are component ids and values are the configurations.
        """
        component_configurations: Dict[ComponentId, Dict] = {}
        # load the other components.
        for i, component_configuration_json in enumerate(
            configuration_file_jsons[_STARTING_INDEX_CUSTOM_CONFIGS:]
        ):
            component_id = self._process_component_section(
                i, component_configuration_json
            )
            if component_id in component_configurations:
                raise ValueError(
                    f"Configuration of component {component_id} occurs more than once."
                )
            component_configurations[component_id] = component_configuration_json
        return component_configurations

    def _load_agent_config(self, file_pointer: TextIO) -> AgentConfig:
        """Load an agent configuration."""
        configuration_file_jsons = yaml_load_all(file_pointer)
        return self.load_agent_config_from_json(configuration_file_jsons)

    def _dump_agent_config(
        self, configuration: AgentConfig, file_pointer: TextIO
    ) -> None:
        """Dump agent configuration."""
        agent_config_part = configuration.ordered_json
        self.validate(agent_config_part)
        agent_config_part.pop("component_configurations")
        result = [agent_config_part] + configuration.component_configurations_json()
        yaml_dump_all(result, file_pointer)

    def _dump_component_config(self, configuration: T, file_pointer: TextIO) -> None:
        """Dump component configuration."""
        result = configuration.ordered_json
        self.validate(result)
        yaml_dump(result, file_pointer)

    def _process_component_section(
        self, component_index: int, component_configuration_json: Dict
    ) -> ComponentId:
        """
        Process a component configuration in an agent configuration file.

        It breaks down in:
        - extract the component id
        - validate the component configuration
        - check that there are only configurable fields

        :param component_index: the index of the component in the file.
        :param component_configuration_json: the JSON object.
        :return: the processed component configuration.
        """
        component_id = self.validator.split_component_id_and_config(
            component_index, component_configuration_json
        )
        self.validator.validate_component_configuration(
            component_id, component_configuration_json
        )
        return component_id


class ConfigLoaders:
    """Configuration Loader class to load any package type."""

    @classmethod
    def from_package_type(
        cls, configuration_type: Union[PackageType, str]
    ) -> "ConfigLoader":
        """
        Get a config loader from the configuration type.

        :param configuration_type: the configuration type.
        :return: configuration loader
        """
        config_class: Type[PackageConfiguration] = PACKAGE_TYPE_TO_CONFIG_CLASS[
            PackageType(configuration_type)
        ]
        return ConfigLoader(config_class.schema, config_class)


def load_component_configuration(
    component_type: ComponentType,
    directory: Path,
    skip_consistency_check: bool = False,
) -> ComponentConfiguration:
    """
    Load configuration and check that it is consistent against the directory.

    :param component_type: the component type.
    :param directory: the root of the package
    :param skip_consistency_check: if True, the consistency check are skipped.
    :return: the configuration object.
    """
    package_type = component_type.to_package_type()
    configuration_object = load_package_configuration(
        package_type, directory, skip_consistency_check
    )
    configuration_object = cast(ComponentConfiguration, configuration_object)
    return configuration_object


def load_package_configuration(
    package_type: PackageType, directory: Path, skip_consistency_check: bool = False,
) -> PackageConfiguration:
    """
    Load configuration and check that it is consistent against the directory.

    :param package_type: the package type.
    :param directory: the root of the package
    :param skip_consistency_check: if True, the consistency check are skipped.
    :return: the configuration object.
    """
    configuration_object = _load_configuration_object(package_type, directory)
    if not skip_consistency_check and isinstance(
        configuration_object, ComponentConfiguration
    ):
        configuration_object._check_configuration_consistency(  # pylint: disable=protected-access
            directory
        )
    return configuration_object


def _load_configuration_object(
    package_type: PackageType, directory: Path
) -> PackageConfiguration:
    """
    Load the configuration object, without consistency checks.

    :param package_type: the package type.
    :param directory: the directory of the configuration.
    :return: the configuration object.
    :raises FileNotFoundError: if the configuration file is not found.
    """
    configuration_loader = ConfigLoader.from_configuration_type(package_type)
    configuration_filename = (
        configuration_loader.configuration_class.default_configuration_filename
    )
    configuration_filepath = directory / configuration_filename
    try:
        with open_file(configuration_filepath) as fp:
            configuration_object = configuration_loader.load(fp)
    except FileNotFoundError:
        raise FileNotFoundError(
            "{} configuration not found: {}".format(
                package_type.value.capitalize(), configuration_filepath
            )
        )
    return configuration_object
