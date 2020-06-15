# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2020 Fetch.AI Limited
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

"""A module with config tools of the aea cli."""

import logging
import logging.config
import os
from pathlib import Path
from typing import Dict, Tuple

import click

import jsonschema

import yaml

from aea.cli.utils.constants import (
    ALLOWED_PATH_ROOTS,
    CLI_CONFIG_PATH,
    RESOURCE_TYPE_TO_CONFIG_FILE,
)
from aea.cli.utils.context import Context
from aea.cli.utils.exceptions import AEAConfigException
from aea.cli.utils.generic import load_yaml
from aea.configurations.base import (
    DEFAULT_AEA_CONFIG_FILE,
    PackageConfiguration,
    PackageType,
    _get_default_configuration_file_name_from_type,
)
from aea.configurations.loader import ConfigLoader, ConfigLoaders
from aea.exceptions import AEAException


def try_to_load_agent_config(
    ctx: Context, is_exit_on_except: bool = True, agent_src_path: str = None
) -> None:
    """
    Load agent config to a click context object.

    :param ctx: click command context object.
    :param is_exit_on_except: bool option to exit on exception (default = True).
    :param agent_src_path: path to an agent dir if needed to load a custom config.

    :return None
    """
    if agent_src_path is None:
        agent_src_path = ctx.cwd

    try:
        path = Path(os.path.join(agent_src_path, DEFAULT_AEA_CONFIG_FILE))
        with path.open(mode="r", encoding="utf-8") as fp:
            ctx.agent_config = ctx.agent_loader.load(fp)
            logging.config.dictConfig(ctx.agent_config.logging_config)
    except FileNotFoundError:
        if is_exit_on_except:
            raise click.ClickException(
                "Agent configuration file '{}' not found in the current directory.".format(
                    DEFAULT_AEA_CONFIG_FILE
                )
            )
    except jsonschema.exceptions.ValidationError:
        if is_exit_on_except:
            raise click.ClickException(
                "Agent configuration file '{}' is invalid. Please check the documentation.".format(
                    DEFAULT_AEA_CONFIG_FILE
                )
            )


def _init_cli_config() -> None:
    """
    Create cli config folder and file.

    :return: None
    """
    conf_dir = os.path.dirname(CLI_CONFIG_PATH)
    if not os.path.exists(conf_dir):
        os.makedirs(conf_dir)
    with open(CLI_CONFIG_PATH, "w+") as f:
        yaml.dump({}, f, default_flow_style=False)


def update_cli_config(dict_conf: Dict) -> None:
    """
    Update CLI config and write to yaml file.

    :param dict_conf: dict config to write.

    :return: None
    """
    config = get_or_create_cli_config()
    config.update(dict_conf)
    with open(CLI_CONFIG_PATH, "w") as f:
        yaml.dump(config, f, default_flow_style=False)


def get_or_create_cli_config() -> Dict:
    """
    Read or create CLI config from yaml file.

    :return: dict CLI config.
    """
    try:
        return load_yaml(CLI_CONFIG_PATH)
    except FileNotFoundError:
        _init_cli_config()
    return load_yaml(CLI_CONFIG_PATH)


def load_item_config(item_type: str, package_path: Path) -> PackageConfiguration:
    """
    Load item configuration.

    :param item_type: type of item.
    :param package_path: path to package from which config should be loaded.

    :return: configuration object.
    """
    configuration_file_name = _get_default_configuration_file_name_from_type(item_type)
    configuration_path = package_path / configuration_file_name
    configuration_loader = ConfigLoader.from_configuration_type(PackageType(item_type))
    item_config = configuration_loader.load(configuration_path.open())
    return item_config


def handle_dotted_path(value: str) -> Tuple:
    """Separate the path between path to resource and json path to attribute.

    Allowed values:
        'agent.an_attribute_name'
        'protocols.my_protocol.an_attribute_name'
        'connections.my_connection.an_attribute_name'
        'contracts.my_contract.an_attribute_name'
        'skills.my_skill.an_attribute_name'
        'vendor.author.[protocols|connections|skills].package_name.attribute_name

    :param value: dotted path.

    :return: Tuple[list of settings dict keys, filepath, config loader].
    """
    parts = value.split(".")

    root = parts[0]
    if root not in ALLOWED_PATH_ROOTS:
        raise AEAException(
            "The root of the dotted path must be one of: {}".format(ALLOWED_PATH_ROOTS)
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
        raise AEAException(
            "The path is too short. Please specify a path up to an attribute name."
        )

    # if the root is 'agent', stop.
    if root == "agent":
        resource_type_plural = "agents"
        path_to_resource_configuration = Path(DEFAULT_AEA_CONFIG_FILE)
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
            raise AEAException(
                "Resource vendor/{}/{}/{} does not exist.".format(
                    resource_author, resource_type_plural, resource_name
                )
            )
    else:
        # navigate the resources of the agent to reach the target configuration file.
        resource_type_plural = root
        resource_name = parts[1]
        path_to_resource_directory = Path(".") / resource_type_plural / resource_name
        path_to_resource_configuration = (
            path_to_resource_directory
            / RESOURCE_TYPE_TO_CONFIG_FILE[resource_type_plural]
        )
        json_path = parts[2:]
        if not path_to_resource_directory.exists():
            raise AEAException(
                "Resource {}/{} does not exist.".format(
                    resource_type_plural, resource_name
                )
            )

    config_loader = ConfigLoader.from_configuration_type(resource_type_plural[:-1])
    return json_path, path_to_resource_configuration, config_loader


def update_item_config(item_type: str, package_path: Path, **kwargs) -> None:
    """
    Update item config and item config file.

    :param item_type: type of item.
    :param package_path: path to a package folder.
    :param kwargs: pairs of config key-value to update.

    :return: None
    """
    item_config = load_item_config(item_type, package_path)
    for key, value in kwargs.items():
        setattr(item_config, key, value)

    config_filepath = os.path.join(
        package_path, item_config.default_configuration_filename
    )
    loader = ConfigLoaders.from_package_type(item_type)
    with open(config_filepath, "w") as f:
        loader.dump(item_config, f)


def validate_item_config(item_type: str, package_path: Path) -> None:
    """
    Validate item configuration.

    :param item_type: type of item.
    :param package_path: path to a package folder.

    :return: None
    :raises AEAConfigException: if something is wrong with item configuration.
    """
    item_config = load_item_config(item_type, package_path)
    loader = ConfigLoaders.from_package_type(item_type)
    for field_name in loader.required_fields:
        if not getattr(item_config, field_name):
            raise AEAConfigException(
                "Parameter '{}' is missing from {} config.".format(
                    field_name, item_type
                )
            )
