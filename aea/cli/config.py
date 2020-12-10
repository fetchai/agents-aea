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
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import click

from aea.cli.utils.config import (
    _try_get_configuration_object_from_aea_config,
    handle_dotted_path,
)
from aea.cli.utils.constants import (
    CONFIG_SUPPORTED_KEY_TYPES,
    CONFIG_SUPPORTED_VALUE_TYPES,
    FALSE_EQUIVALENTS,
    FROM_STRING_TO_TYPE,
)
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project, pass_ctx
from aea.cli.utils.generic import get_parent_object, load_yaml
from aea.configurations.base import (
    AgentConfig,
    ComponentId,
    DEFAULT_AEA_CONFIG_FILE,
    PackageType,
    SkillConfig,
)
from aea.configurations.loader import ConfigLoader
from aea.exceptions import AEAException


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
    value = ConfigGetSet(ctx, json_path).get()
    click.echo(value)


@config.command(name="set")
@click.option(
    "--type",
    default="str",
    type=click.Choice(CONFIG_SUPPORTED_KEY_TYPES),
    help="Specify the type of the value.",
)
@click.argument("JSON_PATH", required=True)
@click.argument("VALUE", required=True, type=str)
@pass_ctx
def set_command(
    ctx: Context,
    json_path: str,
    value: str,
    type: str,  # pylint: disable=redefined-builtin
):
    """Set a field."""
    ConfigGetSet(ctx, json_path).set(value, type)


class ConfigGetSet:
    """Tool to get/set value in agent config."""

    def __init__(self, ctx: Context, dotted_path: str) -> None:
        """Init tool.

        :param ctx: click context
        :param dotted_path: str with attribute path to get/set
        """
        self.dotted_path = dotted_path
        self.ctx = ctx

        (
            self.json_path,
            self.path_to_resource_configuration,
            self.config_loader,
            self.component_id,
        ) = self._handle_dotted_path()

    def _handle_dotted_path(
        self,
    ) -> Tuple[List[str], Path, ConfigLoader, Optional[ComponentId]]:
        """Handle dotted path."""
        try:
            return handle_dotted_path(self.dotted_path, self.agent_config.author)
        except AEAException as e:
            raise click.ClickException(*e.args)

    @property
    def parent_obj_path(self) -> List[str]:
        """Get the parent object (dotted) path."""
        return self.json_path[:-1]

    @property
    def attr_name(self) -> str:
        """Attribute name."""
        return self.json_path[-1]

    def get(self) -> Union[str, int]:
        """Get config value."""
        if self.component_id:
            return self._get_component_value()

        return self._get_agent_value()

    def _get_agent_value(self) -> Union[str, int]:
        """Get config value for agent config."""
        configuration_object = self._load_configuration_object()
        return self._get_value_from_configuration_object(configuration_object)

    def _get_component_value(self) -> Union[str, int]:
        """Get config value for component section in agent config or component package."""
        configuration_object_from_agent = self._get_configuration_object_from_agent()
        try:
            if not configuration_object_from_agent:
                raise click.ClickException("")
            return self._get_value_from_configuration_object(
                configuration_object_from_agent
            )
        except click.ClickException:
            configuration_object = self._load_configuration_object()
            return self._get_value_from_configuration_object(configuration_object)

    @property
    def is_target_agent(self) -> bool:
        """Is target of get/update is agent config."""
        return self.component_id is None

    def _load_configuration_object(self) -> Dict:
        """Load configuration object for component/agent."""
        if self.is_target_agent:
            configuration_object = self.agent_config.json
        else:
            configuration_object = load_yaml(str(self.path_to_resource_configuration))

        self.config_loader.validate(configuration_object)
        return configuration_object

    def _get_configuration_object_from_agent(
        self,
    ) -> Optional[Dict[str, Union[str, int]]]:
        """Get component configuration object from agent component configurations."""
        if not self.component_id:  # pragma: nocover
            raise ValueError("component in not set")

        return _try_get_configuration_object_from_aea_config(
            self.ctx, self.component_id
        )

    def _get_value_from_configuration_object(
        self, conf_obj: Dict[str, Union[str, int]]
    ) -> Any:
        """Get value from configuration object."""
        return self._get_parent_object(conf_obj).get(self.attr_name)

    def _get_parent_object(
        self, conf_obj: Dict[str, Union[str, int]]
    ) -> Dict[str, Union[str, int]]:
        """
        Get and validate parent object.

        :param conf_obj: configuration object.

        :return: parent object.
        :raises: ClickException if attribute is not valid.
        """
        parent_obj_path = self.parent_obj_path
        attr_name = self.attr_name
        try:
            parent_obj = get_parent_object(conf_obj, parent_obj_path)
        except ValueError as e:
            raise click.ClickException(str(e))

        if attr_name not in parent_obj:
            raise click.ClickException("Attribute '{}' not found.".format(attr_name))
        if not isinstance(parent_obj.get(attr_name), CONFIG_SUPPORTED_VALUE_TYPES):
            raise click.ClickException(  # pragma: nocover
                "Attribute '{}' is not of primitive type.".format(attr_name)
            )
        return parent_obj

    @property
    def agent_config(self) -> AgentConfig:
        """Return current context AgentConfig."""
        return self.ctx.agent_config

    def _check_set_field_name(self) -> None:
        """
        Check field names on set operation.

        :return: None

        :raises: click.ClickException is field is not allowed to be changeed.
        """
        top_level_key = self.json_path[0]

        if self.component_id:
            config_class = self.component_id.package_type.configuration_class()
        else:
            config_class = type(self.agent_config)

        if top_level_key not in config_class.FIELDS_ALLOWED_TO_UPDATE:
            raise click.ClickException(
                f"Field `{top_level_key}` is not allowed to change!"
            )
        if config_class == SkillConfig:
            if top_level_key not in SkillConfig.FIELDS_WITH_NESTED_FIELDS:
                return  # pragma: nocover
            if len(self.json_path) < 3:
                path = ".".join(self.json_path)
                raise click.ClickException(f"Path '{path}' not valid for skill.")
            second_level_key = self.json_path[1]
            third_level_key = self.json_path[2]
            if third_level_key not in SkillConfig.NESTED_FIELDS_ALLOWED_TO_UPDATE:
                raise click.ClickException(  # pragma: nocover
                    f"Field `{top_level_key}.{second_level_key}.{third_level_key}` is not allowed to change!"
                )

    def _fix_component_id_version(self) -> None:
        """Update self.component_id with actual version defined in agent instead of latest."""
        if not self.component_id:  # pragma: nocover: check for mypy
            raise ValueError("Component id is not set")

        component_id = None

        for component_id in self.agent_config.package_dependencies:
            if (
                component_id.author == self.component_id.author
                and component_id.package_type == self.component_id.package_type
                and component_id.name == self.component_id.name
            ):
                break
        else:  # pragma: nocover  # should be always ok, cause component has to be alrady registered
            raise ValueError("component is not registered?")

        self.component_id = component_id

    def _parent_object_for_agent_component_configuration(
        self,
    ) -> Dict[str, Union[str, int]]:
        if not self.component_id:  # pragma: nocover: check for mypy
            raise ValueError("no component specified")
        configuration_object = self.agent_config.component_configurations.get(
            self.component_id, {}
        )
        self.agent_config.component_configurations[
            self.component_id
        ] = configuration_object
        parent_object = configuration_object
        # get or create parent object in component configuration
        for i in self.parent_obj_path:
            if i not in parent_object:
                parent_object[i] = {}
            parent_object = parent_object[i]
        return parent_object

    def set(self, value: str, type_str: str) -> None:
        """
        Set config value.

        :param value: value to set
        :param  type_str: name of the value type.

        :return None
        """
        # do a check across real configuration
        self._check_set_field_name()

        configuration_object = self._load_configuration_object()
        parent_configuration_object = self._get_parent_object(configuration_object)

        if self.component_id:
            # component. parent is component config in agent config
            self._fix_component_id_version()
            parent_configuration_object = (
                self._parent_object_for_agent_component_configuration()
            )
            self._update_object(parent_configuration_object, type_str, value)
            agent_configuration_object = self.agent_config.json
        else:
            # already agent
            self._update_object(parent_configuration_object, type_str, value)
            agent_configuration_object = configuration_object
        self._dump_agent_configuration(agent_configuration_object)

    def _update_object(self, parent_object: Dict, type_str: str, value: str) -> None:
        """
        Update dict with value converted to type.

        :param parent_object: dict where value should be updated,
        :param: type_str: type name to convert value on update.
        :param value: str of the value to set.

        :return: None
        """
        type_ = FROM_STRING_TO_TYPE[type_str]
        try:
            if type_ == bool:
                parent_object[self.attr_name] = value not in FALSE_EQUIVALENTS
            elif type_ is None:
                parent_object[self.attr_name] = None
            elif type_ in (dict, list):
                parent_object[self.attr_name] = json.loads(value)
            else:
                parent_object[self.attr_name] = type_(value)
        except (ValueError, json.decoder.JSONDecodeError):  # pragma: no cover
            raise click.ClickException(
                "Cannot convert {} to type {}".format(value, type_)
            )

    @property
    def agent_config_loader(self) -> ConfigLoader:
        """Return agent config loader."""
        return ConfigLoader.from_configuration_type(PackageType.AGENT)

    @property
    def agent_config_file_path(self) -> Path:
        """Return agent config file path."""
        return Path(".") / DEFAULT_AEA_CONFIG_FILE

    def _dump_agent_configuration(
        self, agent_configuration_object: Dict[str, Union[str, int]]
    ) -> None:
        """Save agent configuration."""
        try:
            configuration_obj = self.agent_config_loader.configuration_class.from_json(
                agent_configuration_object
            )
            self.agent_config_loader.validate(configuration_obj.json)
            with open(self.agent_config_file_path, "w") as file_pointer:
                self.agent_config_loader.dump(configuration_obj, file_pointer)
        except Exception as e:  # pragma: nocover
            raise click.ClickException(f"Attribute or value not valid. {e}")
