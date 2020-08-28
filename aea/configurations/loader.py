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
from copy import deepcopy
from pathlib import Path
from typing import Dict, Generic, List, TextIO, Tuple, Type, TypeVar, Union, cast


import jsonschema
from jsonschema import Draft4Validator

import yaml
from yaml import SafeLoader

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
from aea.exceptions import enforce
from aea.helpers.base import yaml_dump, yaml_dump_all, yaml_load, yaml_load_all

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
    if os.name == "nt":  # pragma: nocover  # cause platform depended
        root_path = "file:///{}/".format("/".join(base_uri_path.absolute().parts))
    else:  # pragma: nocover  # cause platform depended
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

    def validate(self, json_data: Dict) -> None:
        """
        Validate a JSON object.

        :param json_data: the JSON data.
        :return: None.
        """
        if self.configuration_class.package_type == PackageType.AGENT:
            json_data_copy = deepcopy(json_data)
            json_data_copy.pop("component_configurations", None)
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

    def _validate(self, json_data: Dict) -> None:
        """
        Validate a configuration file.

        :param json_data: the JSON object of the configuration file to validate.
        :return: None
        :raises ValidationError: if the file doesn't comply with the JSON schema.
              | ValueError: if other consistency checks fail.
        """
        # this might raise ValidationError.
        self.validate(json_data)

        expected_type = self.configuration_class.package_type
        if expected_type != PackageType.AGENT and "type" in json_data:
            actual_type = PackageType(json_data["type"])
            if expected_type != actual_type:
                raise ValueError(
                    f"The field type is not correct: expected {expected_type}, found {actual_type}."
                )

    def _load_component_config(self, file_pointer: TextIO) -> T:
        """Load a component configuration."""
        configuration_file_json = yaml_load(file_pointer)
        return self._load_from_json(configuration_file_json)

    def _load_from_json(self, configuration_file_json: Dict) -> T:
        """Load component configuration from JSON object."""
        self._validate(configuration_file_json)
        key_order = list(configuration_file_json.keys())
        configuration_obj = self.configuration_class.from_json(configuration_file_json)
        configuration_obj._key_order = key_order  # pylint: disable=protected-access
        return configuration_obj

    def _load_agent_config(self, file_pointer: TextIO) -> AgentConfig:
        """Load an agent configuration."""
        configuration_file_jsons = yaml_load_all(file_pointer)

        if len(configuration_file_jsons) == 0:
            raise ValueError("Agent configuration file was empty.")
        agent_config_json = configuration_file_jsons[0]
        self._validate(agent_config_json)
        key_order = list(agent_config_json.keys())
        agent_configuration_obj = cast(
            AgentConfig, self.configuration_class.from_json(agent_config_json)
        )
        agent_configuration_obj._key_order = (  # pylint: disable=protected-access
            key_order
        )

        component_configurations: Dict[ComponentId, Dict] = {}
        # load the other components.
        for i, component_configuration_json in enumerate(configuration_file_jsons[1:]):
            component_id, component_config = self._process_component_section(
                i, component_configuration_json
            )
            if component_id in component_configurations:
                raise ValueError(
                    f"Configuration of component {component_id} occurs more than once."
                )
            component_configurations[component_id] = component_config

        agent_configuration_obj.component_configurations = component_configurations
        return agent_configuration_obj

    def _dump_agent_config(
        self, configuration: AgentConfig, file_pointer: TextIO
    ) -> None:
        """Dump agent configuration."""
        agent_config_part = configuration.ordered_json
        agent_config_part.pop("component_configurations")
        self.validator.validate(instance=agent_config_part)
        result = [agent_config_part] + configuration.component_configurations_json()
        yaml_dump_all(result, file_pointer)

    def _dump_component_config(self, configuration: T, file_pointer: TextIO) -> None:
        """Dump component configuration."""
        result = configuration.ordered_json
        self.validator.validate(instance=result)
        yaml_dump(result, file_pointer)

    def _process_component_section(
        self, i: int, component_configuration_json: Dict
    ) -> Tuple[ComponentId, Dict]:
        """
        Process a component configuration in an agent configuration file.

        It breaks down in:
        - extract the component id
        - validate the component configuration
        - check that there are only configurable fields

        :param i: the index of the component in the file.
        :param component_configuration_json: the JSON object.
        :return: the processed component configuration.
        """
        component_id, result = self._split_component_id_and_config(
            i, component_configuration_json
        )
        self._validate_component_configuration(component_id, result)
        self._check_only_configurable_fields(component_id, result)
        return component_id, result

    @staticmethod
    def _split_component_id_and_config(
        i: int, component_configuration_json: Dict
    ) -> Tuple[ComponentId, Dict]:
        """
        Split component id and configuration.

        :param i: the position of the component configuration in the agent config file..
        :param component_configuration_json: the JSON object to process.
        :return: the component id and the configuration object.
        :raises ValueError: if the component id cannot be extracted.
        """
        result = deepcopy(component_configuration_json)
        # author, name, version, type are mandatory fields
        missing_fields = {"author", "name", "version", "type"}.difference(
            component_configuration_json.keys()
        )
        if len(missing_fields) > 0:
            raise ValueError(
                f"There are missing fields in component id {i + 1}: {missing_fields}."
            )
        component_name = result.pop("name")
        component_author = result.pop("author")
        component_version = result.pop("version")
        component_type = ComponentType(result.pop("type"))
        component_public_id = PublicId(
            component_author, component_name, component_version
        )
        component_id = ComponentId(component_type, component_public_id)
        return component_id, result

    @staticmethod
    def _validate_component_configuration(
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
        # we need to populate the required fields to validate the configurations.
        temporary_config = deepcopy(configuration)
        # common to every package
        temporary_config["name"] = component_id.name
        temporary_config["author"] = component_id.author
        temporary_config["version"] = component_id.version
        temporary_config["license"] = "some_license"
        temporary_config["aea_version"] = "0.1.0"
        if component_id.component_type == ComponentType.PROTOCOL:
            pass  # no other required field
        elif component_id.component_type == ComponentType.CONNECTION:
            temporary_config["class_name"] = "SomeClassName"
            temporary_config["protocols"] = []
            temporary_config.setdefault("config", {})
        elif component_id.component_type == ComponentType.CONTRACT:
            temporary_config["class_name"] = "SomeClassName"
        elif component_id.component_type == ComponentType.SKILL:
            temporary_config["protocols"] = []
            temporary_config["contracts"] = []
            temporary_config["skills"] = []
        loader = ConfigLoaders.from_package_type(component_id.package_type)
        try:
            loader._load_from_json(temporary_config)  # pylint: disable=protected-access
        except jsonschema.ValidationError as e:
            raise ValueError(
                f"Configuration of component {component_id} is not valid."
            ) from e
        # all good!

    @staticmethod
    def _check_only_configurable_fields(
        component_id: ComponentId, configuration: Dict
    ) -> None:
        """
        Check that there are only configurable fields.

        :param component_id: the component id.
        :param configuration: the configuration object.
        :return: None
        """
        configurable_fields = (
            component_id.package_type.configuration_class().configurable_fields
        )
        non_configurable_fields = set(configuration.keys()).difference(
            configurable_fields
        )
        enforce(
            len(non_configurable_fields) == 0,
            f"Bad configuration for component {component_id}: {non_configurable_fields} are non-configurable fields.",
        )


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


_config_loader()
