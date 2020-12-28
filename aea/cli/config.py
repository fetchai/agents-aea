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
"""Implementation of the 'aea config' subcommand."""
import contextlib
import json
from pathlib import Path
from typing import Dict, List, NewType, Optional, Tuple, Union, cast

import click
from click.exceptions import ClickException

from aea.aea_builder import AEABuilder
from aea.cli.utils.config import (
    _try_get_component_id_from_prefix,
    _try_get_configuration_object_from_aea_config,
    handle_dotted_path,
)
from aea.cli.utils.constants import (
    CONFIG_SUPPORTED_KEY_TYPES,
    FALSE_EQUIVALENTS,
    FROM_STRING_TO_TYPE,
)
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project, pass_ctx
from aea.configurations.base import (
    AgentConfig,
    ComponentConfiguration,
    ComponentId,
    DEFAULT_AEA_CONFIG_FILE,
    PackageType,
)
from aea.configurations.loader import ConfigLoader, load_component_configuration
from aea.configurations.validation import ExtraPropertiesError
from aea.exceptions import AEAException
from aea.helpers.storage.backends.base import JSON_TYPES


class VariableDoesNotExist(ValueError):
    """Variable does not exist in a config exception."""


JsonPath = List[str]
VariablePath = Union[str, JsonPath]


NotExistsType = NewType("NotExistsType", object)
NotExists = NotExistsType(None)


@click.group()
@click.pass_context
@check_aea_project
def config(click_context):  # pylint: disable=unused-argument
    """Read or modify a configuration of the agent."""


@config.command()
@click.argument("JSON_PATH", required=True)
@pass_ctx
def get(ctx: Context, json_path: str):
    """Get a field."""
    try:
        value = AgentConfigManager(ctx.agent_config, ctx.cwd).get_variable(json_path)
    except (ValueError, AEAException) as e:
        raise ClickException(*e.args)

    if isinstance(value, dict):
        # turn it to json compatible string, not dict str representation
        value = json.dumps(value, sort_keys=True)
    click.echo(value)


@config.command(name="set")
@click.option(
    "--type",
    "type_",
    default=None,
    type=click.Choice(CONFIG_SUPPORTED_KEY_TYPES + [None]),  # type: ignore
    help="Specify the type of the value.",
)
@click.argument("JSON_PATH", required=True)
@click.argument("VALUE", required=True, type=str)
@pass_ctx
def set_command(
    ctx: Context, json_path: str, value: str, type_: Optional[str],
):
    """Set a field."""
    try:
        agent_config_manager = AgentConfigManager(ctx.agent_config, ctx.cwd)

        current_value = None
        with contextlib.suppress(VariableDoesNotExist):
            current_value = agent_config_manager.get_variable(json_path)

        # type was not specified, tried to auto determine
        if type_ is None:
            # apply str as default type
            converted_value = AgentConfigManager.convert_value_str_to_type(value, "str")
            if current_value is not None:
                # try to convert to original value's type
                with contextlib.suppress(Exception):
                    converted_value = AgentConfigManager.convert_value_str_to_type(
                        value, type(current_value).__name__
                    )
        else:
            # convert to type specified by user
            converted_value = AgentConfigManager.convert_value_str_to_type(
                value, cast(str, type_)
            )

        agent_config_manager.set_variable(json_path, converted_value)
        agent_config_manager.dump_config()
    except ExtraPropertiesError as e:  # pragma: nocover
        raise ClickException(f"Attribute `{e.args[0][0]}` is not allowed to change!")
    except (ValueError, AEAException) as e:
        raise ClickException(*e.args)


class AgentConfigManager:
    """AeaConfig manager."""

    component_configurations = "component_configurations"

    def __init__(
        self, agent_config: AgentConfig, aea_project_directory: Union[str, Path]
    ) -> None:
        """
        Init manager.

        :param agent_config: AgentConfig to manage.
        :param aea_project_directory: directory where project for agent_config placed.
        """
        self.agent_config = agent_config
        self.aea_project_directory = aea_project_directory

    def load_component_configuration(
        self, component_id: ComponentId, skip_consistency_check: bool = True,
    ) -> ComponentConfiguration:
        """
        Load component configuration from the project directory.

        :param component_id: Id of the component to load config for.
        :param skip_consistency_check: bool.

        :return: ComponentConfiguration
        """
        path = AEABuilder.find_component_directory_from_component_id(
            aea_project_directory=Path(self.aea_project_directory),
            component_id=component_id,
        )
        return load_component_configuration(
            component_type=component_id.component_type,
            directory=path,
            skip_consistency_check=skip_consistency_check,
        )

    @property
    def agent_config_file_path(self) -> Path:
        """Return agent config file path."""
        return Path(self.aea_project_directory) / DEFAULT_AEA_CONFIG_FILE

    @classmethod
    def load(cls, aea_project_path: str) -> "AgentConfigManager":
        """Create AgentConfigManager instance from agent project path."""
        raise NotImplementedError  # pragma: nocover

    def set_variable(self, path: VariablePath, value: JSON_TYPES) -> None:
        """
        Set config variable.

        :param path: str dotted path  or List[Union[ComponentId, str]]
        :param value: one of the json friendly objects.

        :return: None
        """
        component_id, json_path = self._parse_path(path)
        data = self._make_dict_for_path_and_value(json_path, value)
        overrides = {}
        if component_id:
            overrides[self.component_configurations] = {component_id: data}
        else:
            # agent
            overrides.update(data)

        self.update_config(overrides)

    @staticmethod
    def _make_dict_for_path_and_value(json_path: JsonPath, value: JSON_TYPES) -> Dict:
        """
        Turn json_path and value into overrides dict.

        :param json_path: List[str] represents config variable path:
        :param value: json friendly value

        :return: dict of overrides
        """
        data: Dict = {}
        nested = data
        for key in json_path[:-1]:
            nested[key] = {}
            nested = nested[key]
        nested[json_path[-1]] = value
        return data

    def get_variable(self, path: VariablePath) -> JSON_TYPES:
        """
        Set config variable.

        :param path: str dotted path or List[Union[ComponentId, str]]

        :return: json friendly value.
        """
        component_id, json_path = self._parse_path(path)

        if component_id:
            configrations_data = [
                _try_get_configuration_object_from_aea_config(
                    self.agent_config, component_id
                )
                or {},
                self.load_component_configuration(component_id).json,
            ]
        else:
            configrations_data = [self.agent_config.json]

        for data in configrations_data:
            value = self._get_value_for_json_path(data, json_path)
            if value is not NotExists:
                return cast(JSON_TYPES, value)

        raise VariableDoesNotExist(
            f"Attribute `{'.'.join(json_path)}` for {'{}({}) config'.format(component_id.component_type,component_id.public_id) if component_id else 'AgentConfig'} does not exist"
        )

    @staticmethod
    def _get_value_for_json_path(
        data: Dict, json_path: JsonPath
    ) -> Union[NotExistsType, JSON_TYPES]:
        """
        Get value by json path from the dict object.

        :param data: dict to get value from
        :param json_path: List[str]

        :return: one of the json values of NotExists if value not presents in data dict.
        """
        value = json.loads(json.dumps(data))  # in case or ordered dict
        prev_key = ""
        for key in json_path:
            if not isinstance(value, dict):
                raise ValueError(f"Attribute '{prev_key}' is not a dictionary.")

            if key not in value:
                return NotExists
            value = value[key]
            prev_key = key
        return value

    def _parse_path(self, path: VariablePath) -> Tuple[Optional[ComponentId], JsonPath]:
        """
        Get component_id and json path from dotted path or list of str with first optional component id.

        :param path: dotted path str, list of str with first optional component id

        :return: Tuple of optonal component id if path related to component and List[str]
        """
        if isinstance(path, str):
            json_path, *_, component_id = handle_dotted_path(
                path, self.agent_config.author
            )
        else:  # pragma: nocover
            if isinstance(path[0], ComponentId):
                json_path = path[1:]
                component_id = path[0]
            else:
                component_id = None
                json_path = path
        if component_id:
            component_id = _try_get_component_id_from_prefix(
                set(self.agent_config.all_components_id), component_id.component_prefix
            )
        return component_id, json_path

    def update_config(self, overrides: Dict) -> None:
        """
        Apply overrides for agent config.

        Validates and applies agent config and component overrides.
        Does not save it on the disc!

        :param overrides: overrided values dictionary

        :return: None
        """
        for component_id, obj in overrides.get("component_configurations", {}).items():
            component_configuration = self.load_component_configuration(component_id)
            component_configuration.check_overrides_valid(obj)

        self.agent_config.update(overrides)

    @property
    def json(self) -> Dict:
        """Return current agent config json representation."""
        return self.agent_config.json

    def dump_config(self) -> None:
        """Save agent config on the disc."""
        config_data = self.json
        self.agent_config.validate_config_data(config_data)
        with open(self.agent_config_file_path, "w") as file_pointer:
            ConfigLoader.from_configuration_type(PackageType.AGENT).dump(
                self.agent_config, file_pointer
            )

    @staticmethod
    def convert_value_str_to_type(value: str, type_str: str) -> JSON_TYPES:
        """Convert value by type name to native python type."""
        try:
            type_ = FROM_STRING_TO_TYPE[type_str]
            if type_ == bool:
                return value not in FALSE_EQUIVALENTS
            if type_ is None:
                return None
            if type_ in (dict, list):
                return json.loads(value)
            return type_(value)
        except (ValueError, json.decoder.JSONDecodeError):  # pragma: no cover
            raise ValueError("Cannot convert {} to type {}".format(value, type_))
