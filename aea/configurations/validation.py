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
"""Implementation of the configuration validation."""
import inspect
import json
import os
from copy import deepcopy
from pathlib import Path
from typing import Dict, List

import jsonschema
from jsonschema import Draft4Validator
from jsonschema._utils import find_additional_properties
from jsonschema._validators import additionalProperties
from jsonschema.validators import extend

from aea.configurations.constants import AGENT
from aea.configurations.data_types import ComponentId, ComponentType, PublicId


_CUR_DIR = os.path.dirname(inspect.getfile(inspect.currentframe()))  # type: ignore
_SCHEMAS_DIR = os.path.join(_CUR_DIR, "schemas")

_PREFIX_BASE_CONFIGURABLE_PARTS = "base"
_SCHEMAS_CONFIGURABLE_PARTS_DIRNAME = "configurable_parts"
_POSTFIX_CUSTOM_CONFIG = "-custom_config.json"


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


class ExtraPropertiesError(ValueError):
    """Extra properties exception."""

    def __str__(self) -> str:
        """Get string representation of the object."""
        return (
            f"ExtraPropertiesError: properties not expected: {', '.join(self.args[0])}"
        )

    def __repr__(self) -> str:
        """Get string representation of the object."""
        return str(self)


def ownAdditionalProperties(validator, aP, instance, schema):
    """Additioinal properties validator."""
    for _ in additionalProperties(validator, aP, instance, schema):
        raise ExtraPropertiesError(list(find_additional_properties(instance, schema)))
    return iter(())


OwnDraft4Validator = extend(
    validator=Draft4Validator,
    validators={"additionalProperties": ownAdditionalProperties},
)


class ConfigValidator:
    """Configuration validator implementation."""

    def __init__(self, schema_filename: str):
        """
        Initialize the parser for configuration files.

        :param schema_filename: the path to the JSON-schema file in 'aea/configurations/schemas'.
        """
        base_uri = Path(_SCHEMAS_DIR)
        self._schema = json.load((base_uri / schema_filename).open())
        root_path = make_jsonschema_base_uri(base_uri)
        self._resolver = jsonschema.RefResolver(root_path, self._schema)
        self._validator = OwnDraft4Validator(self._schema, resolver=self._resolver)

    @staticmethod
    def split_component_id_and_config(
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

    @classmethod
    def validate_component_configuration(
        cls, component_id: ComponentId, configuration: Dict
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
            cls(schema_file).validate(
                dict(
                    type=str(component_id.component_type),
                    public_id=str(component_id.public_id),
                    **configuration,
                )
            )
        except (ExtraPropertiesError, jsonschema.ValidationError) as e:
            raise ValueError(
                f"Configuration of component {component_id} is not valid. {e}"
            ) from e

    def validate(self, json_data: Dict) -> None:
        """
        Validate a JSON object against the right JSON schema.

        :param json_data: the JSON data.
        :return: None.
        """
        if json_data.get("type", AGENT) == AGENT:
            json_data_copy = deepcopy(json_data)

            # validate component_configurations
            self.validate_agent_components_configuration(
                json_data_copy.pop("component_configurations", [])
            )

            # validate agent config
            self._validator.validate(instance=json_data_copy)
        else:
            self._validator.validate(instance=json_data)

    def validate_agent_components_configuration(
        self, component_configurations: Dict
    ) -> None:
        """
        Validate agent component configurations overrides.

        :param component_configurations:

        :return: None
        """
        for idx, component_configuration_json in enumerate(component_configurations):
            component_id = self.split_component_id_and_config(
                idx, component_configuration_json
            )
            self.validate_component_configuration(
                component_id, component_configuration_json
            )

    @property
    def required_fields(self) -> List[str]:
        """
        Get the required fields.

        :return: list of required fields.
        """
        return self._schema["required"]
