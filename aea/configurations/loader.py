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
from copy import deepcopy
from pathlib import Path
from typing import Dict, Generic, List, TextIO, Type, TypeVar, Union, cast

import jsonschema
import yaml
from jsonschema import Draft4Validator

from aea.configurations.base import (
    AgentConfig,
    ComponentConfiguration,
    ComponentId,
    ComponentType,
    ConnectionConfig,
    ContractConfig,
    PackageType,
    ProtocolConfig,
    ProtocolSpecification,
    PublicId,
    SkillConfig,
)
from aea.helpers.yaml_utils import yaml_dump, yaml_dump_all, yaml_load, yaml_load_all


_CUR_DIR = os.path.dirname(inspect.getfile(inspect.currentframe()))  # type: ignore
_SCHEMAS_DIR = os.path.join(_CUR_DIR, "schemas")

_PREFIX_BASE_CONFIGURABLE_PARTS = "base"
_SCHEMAS_CONFIGURABLE_PARTS_DIRNAME = "configurable_parts"
_POSTFIX_CUSTOM_CONFIG = "-custom_config.json"
_STARTING_INDEX_CUSTOM_CONFIGS = 1

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
    if os.name == "nt":  # pragma: nocover  # cause platform depended
        root_path = "file:///{}/".format("/".join(base_uri_path.absolute().parts))
    else:  # pragma: nocover  # cause platform depended
        root_path = "file://{}/".format(base_uri_path.absolute())
    return root_path


def _get_path_to_custom_config_schema_from_type(component_type: ComponentType) -> str:
    """
    Get the path to the custom config schema

    :param component_type: a component type.
    :return: the path to the JSON schema file.
    """
    path_prefix: Path = Path(_SCHEMAS_DIR) / _SCHEMAS_CONFIGURABLE_PARTS_DIRNAME
    if component_type in {ComponentType.SKILL, ComponentType.CONNECTION}:
        filename_prefix = component_type.value
    else:
        filename_prefix = _PREFIX_BASE_CONFIGURABLE_PARTS
    full_path = path_prefix / (filename_prefix + _POSTFIX_CUSTOM_CONFIG)
    return str(full_path)


class BaseConfigLoader:
    """Base class for configuration loader classes."""

    def __init__(self, schema_filename: str):
        """
        Initialize the base configuration loader.

        :param schema_filename: the path to the schema.
        """
        base_uri = Path(_SCHEMAS_DIR)
        self._schema = json.load((base_uri / schema_filename).open())
        root_path = make_jsonschema_base_uri(base_uri)
        self._resolver = jsonschema.RefResolver(root_path, self._schema)
        self._validator = Draft4Validator(self._schema, resolver=self._resolver)

    @property
    def validator(self) -> Draft4Validator:
        """Get the json schema validator."""
        return self._validator

    def validate(self, json_data: Dict) -> None:
        """
        Validate a JSON object.

        :param json_data: the JSON data.
        :return: None.
        """
        self.validator.validate(json_data)

    @property
    def required_fields(self) -> List[str]:
        """
        Get the required fields.

        :return: list of required fields.
        """
        return self._schema["required"]


class ConfigLoader(Generic[T], BaseConfigLoader):
    """Parsing, serialization and validation for package configuration files."""

    def __init__(self, schema_filename: str, configuration_class: Type[T]):
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

    def validate(self, json_data: Dict) -> None:
        """
        Validate a JSON object against the right JSON schema.

        :param json_data: the JSON data.
        :return: None.
        """
        if self.configuration_class.package_type == PackageType.AGENT:
            json_data_copy = deepcopy(json_data)

            # validate component_configurations
            component_configurations = json_data_copy.pop(
                "component_configurations", {}
            )
            for idx, component_configuration_json in enumerate(
                component_configurations
            ):
                component_id = self._split_component_id_and_config(
                    idx, component_configuration_json
                )
                self.validate_component_configuration(
                    component_id, component_configuration_json
                )

            # validate agent config
            self._validator.validate(instance=json_data_copy)
        else:
            self._validator.validate(instance=json_data)

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
        :return: None
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
        configuration_obj = self.configuration_class.from_json(configuration_file_json)
        configuration_obj._key_order = key_order  # pylint: disable=protected-access
        return configuration_obj

    def load_agent_config_from_json(
        self, configuration_json: List[Dict]
    ) -> AgentConfig:
        """
        Load agent configuration from configuration json data.

        :param configuration_json: list of dicts with aea configuration

        :return: AgentConfig instance
        """
        if len(configuration_json) == 0:
            raise ValueError("Agent configuration file was empty.")
        agent_config_json = configuration_json[0]
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
        self, configuration_file_jsons
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
        self.validator.validate(instance=result)
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
        component_id = self._split_component_id_and_config(
            component_index, component_configuration_json
        )
        self.validate_component_configuration(
            component_id, component_configuration_json
        )
        return component_id

    @staticmethod
    def _split_component_id_and_config(
        component_index: int, component_configuration_json: Dict
    ) -> ComponentId:
        """
        Split component id and configuration.

        :param component_index: the position of the component configuration in the agent config file..
        :param component_configuration_json: the JSON object to process.
        :return: the component id and the configuration object.
        :raises ValueError: if the component id cannot be extracted.
        """
        # author, name, version, type are mandatory fields
        missing_fields = {"public_id", "type"}.difference(
            component_configuration_json.keys()
        )
        if len(missing_fields) > 0:
            raise ValueError(
                f"There are missing fields in component id {component_index + 1}: {missing_fields}."
            )
        public_id_str = component_configuration_json.pop("public_id")
        component_type = ComponentType(component_configuration_json.pop("type"))
        component_public_id = PublicId.from_str(public_id_str)
        component_id = ComponentId(component_type, component_public_id)
        return component_id

    @staticmethod
    def validate_component_configuration(
        component_id: ComponentId, configuration: Dict
    ) -> None:
        """
        Validate the component configuration of an agent configuration file.

        This check is to detect inconsistencies in the specified fields.

        :param component_id: the component id.
        :param configuration: the configuration dictionary.
        :return: None
        :raises ValueError: if the configuration is not valid.
        """
        schema_file = _get_path_to_custom_config_schema_from_type(
            component_id.component_type
        )
        try:
            BaseConfigLoader(schema_file).validate(
                dict(
                    type=str(component_id.component_type),
                    public_id=str(component_id.public_id),
                    **configuration,
                )
            )
        except jsonschema.ValidationError as e:
            raise ValueError(
                f"Configuration of component {component_id} is not valid. {e}"
            ) from e


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


def load_component_configuration(
    component_type: ComponentType,
    directory: Path,
    skip_consistency_check: bool = False,
) -> "ComponentConfiguration":
    """
    Load configuration and check that it is consistent against the directory.

    :param component_type: the component type.
    :param directory: the root of the package
    :param skip_consistency_check: if True, the consistency check are skipped.
    :return: the configuration object.
    """
    configuration_object = _load_configuration_object(component_type, directory)
    if not skip_consistency_check:
        configuration_object._check_configuration_consistency(  # pylint: disable=protected-access
            directory
        )
    return configuration_object


def _load_configuration_object(
    component_type: ComponentType, directory: Path
) -> "ComponentConfiguration":
    """
    Load the configuration object, without consistency checks.

    :param component_type: the component type.
    :param directory: the directory of the configuration.
    :return: the configuration object.
    :raises FileNotFoundError: if the configuration file is not found.
    """
    configuration_loader = ConfigLoader.from_configuration_type(
        component_type.to_configuration_type()
    )
    configuration_filename = (
        configuration_loader.configuration_class.default_configuration_filename
    )
    configuration_filepath = directory / configuration_filename
    try:
        fp = open(configuration_filepath)
        configuration_object = configuration_loader.load(fp)
    except FileNotFoundError:
        raise FileNotFoundError(
            "{} configuration not found: {}".format(
                component_type.value.capitalize(), configuration_filepath
            )
        )
    return configuration_object
