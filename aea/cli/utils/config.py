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
from typing import Dict

import click

import jsonschema  # type: ignore

import yaml

from aea.cli.utils.constants import CLI_CONFIG_PATH
from aea.cli.utils.context import Context
from aea.cli.utils.package_utils import load_yaml
from aea.configurations.base import (
    DEFAULT_AEA_CONFIG_FILE,
    PackageType,
    _get_default_configuration_file_name_from_type,
)
from aea.configurations.loader import ConfigLoader


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


def load_item_config(item_type: str, package_path: Path) -> ConfigLoader:
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
