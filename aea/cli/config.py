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

import sys
from pathlib import Path
from typing import Dict, List, cast

import click

import yaml

from aea.cli.common import Context, logger, pass_ctx, try_to_load_agent_config, from_string_to_type
from aea.configurations.base import (
    DEFAULT_AEA_CONFIG_FILE,
    DEFAULT_CONNECTION_CONFIG_FILE,
    DEFAULT_PROTOCOL_CONFIG_FILE,
    DEFAULT_SKILL_CONFIG_FILE,
)
from aea.configurations.loader import ConfigLoader

ALLOWED_PATH_ROOTS = ["agent", "skills", "protocols", "connections", "vendor"]
RESOURCE_TYPE_TO_CONFIG_FILE = {
    "skills": DEFAULT_SKILL_CONFIG_FILE,
    "protocols": DEFAULT_PROTOCOL_CONFIG_FILE,
    "connections": DEFAULT_CONNECTION_CONFIG_FILE,
}  # type: Dict[str, str]


class AEAJsonPathType(click.ParamType):
    """This class implements the JSON-path parameter type for the AEA CLI tool."""

    name = "json-path"

    def convert(self, value, param, ctx):
        """Separate the path between path to resource and json path to attribute.

        Allowed values:
            'agent.an_attribute_name'
            'protocols.my_protocol.an_attribute_name'
            'connections.my_connection.an_attribute_name'
            'skills.my_skill.an_attribute_name'
            'vendor.author.[protocols|connections|skills].package_name.attribute_name
        """
        parts = value.split(".")

        root = parts[0]
        if root not in ALLOWED_PATH_ROOTS:
            self.fail(
                "The root of the dotted path must be one of: {}".format(
                    ALLOWED_PATH_ROOTS
                )
            )

        if (
            len(parts) < 1
            or parts[0] == "agent"
            and len(parts) < 2
            or parts[0] == "vendor"
            and len(parts) < 5
            or parts[0] != "agent"
            and len(parts) < 3
        ):
            self.fail(
                "The path is too short. Please specify a path up to an attribute name."
            )

        # if the root is 'agent', stop.
        if root == "agent":
            resource_type_plural = "agents"
            path_to_resource_configuration = DEFAULT_AEA_CONFIG_FILE
            json_path = parts[1:]
        elif root == "vendor":
            resource_author = parts[1]
            resource_type_plural = parts[2]
            resource_name = parts[3]
            path_to_resource_directory = (
                Path(".")
                / "vendor"
                / resource_author
                / resource_type_plural
                / resource_name
            )
            path_to_resource_configuration = (
                path_to_resource_directory
                / RESOURCE_TYPE_TO_CONFIG_FILE[resource_type_plural]
            )
            json_path = parts[4:]
            if not path_to_resource_directory.exists():
                self.fail(
                    "Resource vendor/{}/{}/{} does not exist.".format(
                        resource_author, resource_type_plural, resource_name
                    )
                )
        else:
            # navigate the resources of the agent to reach the target configuration file.
            resource_type_plural = root
            resource_name = parts[1]
            path_to_resource_directory = (
                Path(".") / resource_type_plural / resource_name
            )
            path_to_resource_configuration = (
                path_to_resource_directory
                / RESOURCE_TYPE_TO_CONFIG_FILE[resource_type_plural]
            )
            json_path = parts[2:]
            if not path_to_resource_directory.exists():
                self.fail(
                    "Resource {}/{} does not exist.".format(
                        resource_type_plural, resource_name
                    )
                )

        config_loader = ConfigLoader.from_configuration_type(resource_type_plural[:-1])
        ctx.obj.set_config("configuration_file_path", path_to_resource_configuration)
        ctx.obj.set_config("configuration_loader", config_loader)
        return json_path


def _get_parent_object(obj: dict, dotted_path: List[str]):
    """
    Given a nested dictionary, return the object denoted by the dotted path (if any).

    In particular if dotted_path = [], it returns the same object.

    :param obj: the dictionary.
    :param dotted_path: the path to the object.
    :return: the target dictionary
    :raise ValueError: if the path is not valid.
    """
    index = 0
    current_object = obj
    while index < len(dotted_path):
        current_attribute_name = dotted_path[index]
        current_object = current_object.get(current_attribute_name, None)
        # if the dictionary does not have the key we want, fail.
        if current_object is None:
            raise ValueError("Cannot get attribute '{}'".format(current_attribute_name))
        index += 1
    # if we are not at the last step and the attribute value is not a dictionary, fail.
    if isinstance(current_object, dict):
        return current_object
    else:
        raise ValueError("The target object is not a dictionary.")


@click.group()
@pass_ctx
def config(ctx: Context):
    """Read or modify a configuration."""
    try_to_load_agent_config(ctx)


@config.command()
@click.argument("JSON_PATH", required=True, type=AEAJsonPathType())
@pass_ctx
def get(ctx: Context, json_path: List[str]):
    """Get a field."""
    config_loader = cast(ConfigLoader, ctx.config.get("configuration_loader"))
    configuration_file_path = cast(str, ctx.config.get("configuration_file_path"))

    configuration_object = yaml.safe_load(open(configuration_file_path))
    config_loader.validator.validate(instance=configuration_object)

    parent_object_path = json_path[:-1]
    attribute_name = json_path[-1]
    try:
        parent_object = _get_parent_object(configuration_object, parent_object_path)
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)

    if attribute_name not in parent_object:
        logger.error("Attribute '{}' not found.".format(attribute_name))
        sys.exit(1)
    if not isinstance(parent_object.get(attribute_name), (str, int, bool, float)):
        logger.error("Attribute '{}' is not of primitive type.".format(attribute_name))
        sys.exit(1)

    attribute_value = parent_object.get(attribute_name)
    print(attribute_value)


@config.command()
@click.option("--type", default="str", type=click.Choice(["str", "int", "bool", "float"]),
              help="Specify the type of the value.")
@click.argument("JSON_PATH", required=True, type=AEAJsonPathType())
@click.argument("VALUE", required=True, type=str)
@pass_ctx
def set(ctx: Context, json_path: List[str], value, type):
    """Set a field."""
    type_ = from_string_to_type[type]
    config_loader = cast(ConfigLoader, ctx.config.get("configuration_loader"))
    configuration_file_path = cast(str, ctx.config.get("configuration_file_path"))

    configuration_dict = yaml.safe_load(open(configuration_file_path))
    config_loader.validator.validate(instance=configuration_dict)

    parent_object_path = json_path[:-1]
    attribute_name = json_path[-1]
    try:
        parent_object = _get_parent_object(configuration_dict, parent_object_path)
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)

    if attribute_name not in parent_object:
        logger.error("Attribute '{}' not found.".format(attribute_name))
        sys.exit(1)
    if not isinstance(parent_object.get(attribute_name), (str, int, bool, float)):
        logger.error("Attribute '{}' is not of primitive type.".format(attribute_name))
        sys.exit(1)

    try:
        parent_object[attribute_name] = type_(value)
    except ValueError:
        logger.error("Cannot convert {} to type {}".format(value, type_))

    try:
        configuration_obj = config_loader.configuration_type.from_json(
            configuration_dict
        )
        config_loader.validator.validate(instance=configuration_obj.json)
        config_loader.dump(configuration_obj, open(configuration_file_path, "w"))
    except Exception:
        logger.error("Attribute or value not valid.")
        sys.exit(1)
