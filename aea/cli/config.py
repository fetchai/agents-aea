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

"""Implementation of the 'aea list' subcommand."""

from typing import Dict, List, cast

import click

from aea.cli.utils.click_utils import AEAJsonPathType
from aea.cli.utils.constants import (
    FALSE_EQUIVALENTS,
    FROM_STRING_TO_TYPE,
)
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project, pass_ctx
from aea.cli.utils.generic import get_parent_object, load_yaml
from aea.configurations.loader import ConfigLoader


@click.group()
@click.pass_context
@check_aea_project
def config(click_context):
    """Read or modify a configuration."""


@config.command()
@click.argument("JSON_PATH", required=True, type=AEAJsonPathType())
@pass_ctx
def get(ctx: Context, json_path: List[str]):
    """Get a field."""
    value = _get_config_value(ctx, json_path)
    click.echo(value)


@config.command(name="set")
@click.option(
    "--type",
    default="str",
    type=click.Choice(["str", "int", "bool", "float"]),
    help="Specify the type of the value.",
)
@click.argument("JSON_PATH", required=True, type=AEAJsonPathType())
@click.argument("VALUE", required=True, type=str)
@pass_ctx
def set_command(
    ctx: Context,
    json_path: List[str],
    value: str,
    type: str,  # pylint: disable=redefined-builtin
):
    """Set a field."""
    _set_config(ctx, json_path, value, type)


def _get_config_value(ctx: Context, json_path: List[str]):
    config_loader = cast(ConfigLoader, ctx.config.get("configuration_loader"))
    configuration_file_path = cast(str, ctx.config.get("configuration_file_path"))

    configuration_object = load_yaml(configuration_file_path)
    config_loader.validator.validate(instance=configuration_object)

    parent_object_path = json_path[:-1]
    attribute_name = json_path[-1]
    parent_object = _get_and_validate_parent_obj(
        configuration_object, parent_object_path, attribute_name
    )

    return parent_object.get(attribute_name)


def _set_config(ctx: Context, json_path: List[str], value: str, type_str: str) -> None:
    config_loader = cast(ConfigLoader, ctx.config.get("configuration_loader"))
    configuration_file_path = cast(str, ctx.config.get("configuration_file_path"))

    configuration_object = load_yaml(configuration_file_path)
    config_loader.validator.validate(instance=configuration_object)

    parent_object_path = json_path[:-1]
    attribute_name = json_path[-1]
    parent_object = _get_and_validate_parent_obj(
        configuration_object, parent_object_path, attribute_name
    )

    type_ = FROM_STRING_TO_TYPE[type_str]
    try:
        if type_ != bool:
            parent_object[attribute_name] = type_(value)
        else:
            parent_object[attribute_name] = value not in FALSE_EQUIVALENTS
    except ValueError:  # pragma: no cover
        raise click.ClickException("Cannot convert {} to type {}".format(value, type_))

    try:
        configuration_obj = config_loader.configuration_class.from_json(
            configuration_object
        )
        config_loader.validator.validate(instance=configuration_obj.json)
        config_loader.dump(configuration_obj, open(configuration_file_path, "w"))
    except Exception:
        raise click.ClickException("Attribute or value not valid.")


def _get_and_validate_parent_obj(
    conf_obj: Dict, parent_obj_path: List, attr_name: str
) -> Dict:
    """
    Get and validate parent object.

    :param conf_obj: configuration object.
    :param parent_obj_path: parent object path.
    :param attr_name: attribute name.

    :return: parent object.
    :raises: ClickException if attribute is not valid.
    """
    try:
        parent_obj = get_parent_object(conf_obj, parent_obj_path)
    except ValueError as e:
        raise click.ClickException(str(e))

    if attr_name not in parent_obj:
        raise click.ClickException("Attribute '{}' not found.".format(attr_name))
    if not isinstance(parent_obj.get(attr_name), (str, int, bool, float)):
        raise click.ClickException(
            "Attribute '{}' is not of primitive type.".format(attr_name)
        )
    return parent_obj
