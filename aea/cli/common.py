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

"""Implementation of the common utils of the aea cli."""

import logging
import logging.config
import os
import sys
from pathlib import Path
from typing import Dict, List, cast, Optional

import click
import jsonschema  # type: ignore
from dotenv import load_dotenv

from aea.cli.loggers import default_logging_config
from aea.configurations.base import DEFAULT_AEA_CONFIG_FILE, AgentConfig, SkillConfig, ConnectionConfig, ProtocolConfig, \
    DEFAULT_PROTOCOL_CONFIG_FILE, Dependencies, PublicId, \
    _get_default_configuration_file_name_from_type
from aea.configurations.loader import ConfigLoader
from aea.crypto.fetchai import FETCHAI
from aea.helpers.base import add_agent_component_module_to_sys_modules, load_agent_component_package

logger = logging.getLogger("aea")
logger = default_logging_config(logger)

DEFAULT_VERSION = "0.1.0"
DEFAULT_CONNECTION = PublicId.from_string("fetchai/stub:" + DEFAULT_VERSION)  # type: PublicId
DEFAULT_SKILL = PublicId.from_string("fetchai/error:" + DEFAULT_VERSION)  # type: PublicId
DEFAULT_LEDGER = FETCHAI
DEFAULT_REGISTRY_PATH = str(Path("./", "packages"))


class Context(object):
    """A class to keep configuration of the cli tool."""

    agent_config: AgentConfig

    def __init__(self, cwd: str = "."):
        """Init the context."""
        self.config = dict()  # type: Dict
        self.agent_loader = ConfigLoader("aea-config_schema.json", AgentConfig)
        self.skill_loader = ConfigLoader("skill-config_schema.json", SkillConfig)
        self.connection_loader = ConfigLoader("connection-config_schema.json", ConnectionConfig)
        self.protocol_loader = ConfigLoader("protocol-config_schema.json", ProtocolConfig)
        self.cwd = cwd

    def set_config(self, key, value) -> None:
        """
        Set a config.

        :param key: the key for the configuration.
        :param value: the value associated with the key.
        :return: None
        """
        self.config[key] = value
        logger.debug('  config[%s] = %s' % (key, value))

    def _get_item_dependencies(self, item_type, public_id: PublicId) -> Dependencies:
        """Get the dependencies from item type and public id."""
        item_type_plural = item_type + "s"
        default_config_file_name = _get_default_configuration_file_name_from_type(item_type)
        if public_id.author != self.agent_config.author:
            path = str(Path("vendor", public_id.author, item_type_plural, public_id.name, default_config_file_name))
        else:
            path = str(Path(item_type_plural, public_id.name, default_config_file_name))
        config_loader = ConfigLoader.from_configuration_type(item_type)
        config = config_loader.load(open(path))
        deps = cast(Dependencies, config.dependencies)
        return deps

    def get_dependencies(self) -> Dependencies:
        """Aggregate the dependencies from every component.

        :return a list of dependency version specification. e.g. ["gym >= 1.0.0"]
        """
        dependencies = {}  # type: Dependencies
        for protocol_id in self.agent_config.protocols:
            dependencies.update(self._get_item_dependencies("protocol", protocol_id))

        for connection_id in self.agent_config.connections:
            dependencies.update(self._get_item_dependencies("connection", connection_id))

        for skill_id in self.agent_config.skills:
            dependencies.update(self._get_item_dependencies("skill", skill_id))

        return dependencies


pass_ctx = click.make_pass_decorator(Context)


def try_to_load_agent_config(ctx: Context, exit_on_except: bool = True) -> None:
    """
    Load agent config to a click context object.

    :param ctx: click command context object.
    :param exit_on_except: bool option to exit on exception (default = True).

    :return None
    """
    try:
        path = Path(os.path.join(ctx.cwd, DEFAULT_AEA_CONFIG_FILE))
        with open(str(path), mode="r", encoding="utf-8") as fp:
            ctx.agent_config = ctx.agent_loader.load(fp)
            logging.config.dictConfig(ctx.agent_config.logging_config)
    except FileNotFoundError:
        if exit_on_except:
            logger.error("Agent configuration file '{}' not found in the current directory.".format(DEFAULT_AEA_CONFIG_FILE))
            sys.exit(1)
    except jsonschema.exceptions.ValidationError:
        if exit_on_except:
            logger.error("Agent configuration file '{}' is invalid. Please check the documentation.".format(DEFAULT_AEA_CONFIG_FILE))
            sys.exit(1)


def _try_to_load_protocols(ctx: Context):
    for protocol_public_id in ctx.agent_config.protocols:
        protocol_name = protocol_public_id.name
        protocol_author = protocol_public_id.author
        logger.debug("Processing protocol {}".format(protocol_public_id))
        if protocol_public_id.author != ctx.agent_config.author:
            protocol_dir = Path("vendor", protocol_public_id.author, "protocols", protocol_name)
        else:
            protocol_dir = Path("protocols", protocol_name)
        try:
            ctx.protocol_loader.load(open(protocol_dir / DEFAULT_PROTOCOL_CONFIG_FILE))
        except FileNotFoundError:
            logger.error("Protocol configuration file for protocol {} not found.".format(protocol_name))
            sys.exit(1)

        try:
            protocol_package = load_agent_component_package("protocol", protocol_name, protocol_author, protocol_dir)
            add_agent_component_module_to_sys_modules("protocol", protocol_name, protocol_author, protocol_package)
        except Exception:
            logger.error("A problem occurred while processing protocol {}.".format(protocol_public_id))
            sys.exit(1)


def _load_env_file(env_file: str):
    """
    Load the content of the environment file into the process environment.

    :param env_file: path to the env file.
    :return: None.
    """
    load_dotenv(dotenv_path=Path(env_file), override=False)


def format_items(items):
    """Format list of items (protocols/connections) to a string for CLI output."""
    list_str = ''
    for item in items:
        list_str += (
            '{line}\n'
            'Public ID: {public_id}\n'
            'Name: {name}\n'
            'Description: {description}\n'
            'Author: {author}\n'
            'Version: {version}\n'
            '{line}\n'.format(
                name=item['name'],
                public_id=item['public_id'],
                description=item['description'],
                author=item['author'],
                version=item['version'],
                line='-' * 30
            ))
    return list_str


def format_skills(items):
    """Format list of skills to a string for CLI output."""
    list_str = ''
    for item in items:
        list_str += (
            '{line}\n'
            'Public ID: {public_id}\n'
            'Name: {name}\n'
            'Description: {description}\n'
            'Protocols: {protocols}\n'
            'Version: {version}\n'
            '{line}\n'.format(
                name=item['name'],
                # TODO: switch to unsafe get public_id when every obj has it
                public_id=item.get('public_id'),
                description=item['description'],
                version=item['version'],
                protocols=''.join(
                    name + ' | ' for name in item['protocol_names']
                ),
                line='-' * 30
            ))
    return list_str


def retrieve_details(name: str, loader: ConfigLoader, config_filepath: str) -> Dict:
    """Return description of a protocol, skill, connection."""
    config = loader.load(open(str(config_filepath)))
    item_name = config.agent_name if isinstance(config, AgentConfig) else config.name
    assert item_name == name
    return {"public_id": str(config.public_id), "name": item_name, "author": config.author,
            "description": config.description, "version": config.version}


class AEAConfigException(Exception):
    """Exception about AEA configuration."""


class ConnectionsOption(click.Option):
    """Click option for the --connections option in 'aea run'."""

    def type_cast_value(self, ctx, value) -> Optional[List[str]]:
        """
        Parse the list of string passed through command line.

        E.g. from 'stub,local' to ['stub', 'local'].

        :param ctx: the click context
        :param value: the list of connection names, as a string.
        :return:
        """
        if value is None:
            return None
        try:
            def arg_strip(s):
                return s.strip(" '\"")

            connection_names = set(arg_strip(s) for s in value.split(",") if arg_strip(s) != "")
            return list(connection_names)
        except Exception:  # pragma: no cover
            raise click.BadParameter(value)


class PublicIdParameter(click.ParamType):
    """Define a public id parameter for Click applications."""

    def __init__(self, *args, **kwargs):
        """
        Initialize the Public Id parameter.

        Just forwards arguments to parent constructor.
        """
        super().__init__(*args, **kwargs)

    def get_metavar(self, param):
        """Return the metavar default for this param if it provides one."""
        return "PUBLIC_ID"

    def convert(self, value, param, ctx):
        """Convert the value. This is not invoked for values that are `None` (the missing value)."""
        try:
            return PublicId.from_string(value)
        except ValueError:
            raise click.BadParameter(value)


def try_get_item_source_path(path: str, item_type_plural: str, item_name: str) -> str:
    """
    Get the item source path.

    :param path: the source path root
    :param item_type_plural: the item type (plural)
    :param item_name: the item name

    :return: the item source path
    """
    source_path = os.path.join(path, item_type_plural, item_name)
    if not os.path.exists(source_path):
        raise click.ClickException(
            'Item "{}" not found in source folder.'.format(item_name)
        )
    return source_path


def try_get_item_target_path(path: str, item_type_plural: str, item_name: str) -> str:
    """
    Get the item target path.

    :param path: the target path root
    :param item_type_plural: the item type (plural)
    :param item_name: the item name

    :return: the item target path
    """
    target_path = os.path.join(path, item_type_plural, item_name)
    if os.path.exists(target_path):
        raise click.ClickException(
            'Item "{}" already exists in target folder.'.format(item_name)
        )
    return target_path
