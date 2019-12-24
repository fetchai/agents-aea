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

import importlib.util
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
    DEFAULT_PROTOCOL_CONFIG_FILE, DEFAULT_CONNECTION_CONFIG_FILE, DEFAULT_SKILL_CONFIG_FILE, Dependencies, PublicId
from aea.configurations.loader import ConfigLoader
from aea.crypto.fetchai import FETCHAI

logger = logging.getLogger("aea")
logger = default_logging_config(logger)

DEFAULT_REGISTRY_PATH = str(Path("..", "packages"))
DEFAULT_CONNECTION = PublicId.from_string("fetchai/stub:0.1.0")  # type: PublicId
DEFAULT_SKILL = PublicId.from_string("fetchai/error:0.1.0")  # type: PublicId
DEFAULT_LEDGER = FETCHAI


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

    def get_dependencies(self) -> Dependencies:
        """Aggregate the dependencies from every component.

        :return a list of dependency version specification. e.g. ["gym >= 1.0.0"]
        """
        dependencies = {}  # type: Dependencies
        for protocol_id in self.agent_config.protocols:
            path = str(Path("protocols", protocol_id.name, DEFAULT_PROTOCOL_CONFIG_FILE))
            protocol_config = self.protocol_loader.load(open(path))
            deps = cast(Dependencies, protocol_config.dependencies)
            dependencies.update(deps)

        for connection_id in self.agent_config.connections:
            path = str(Path("connections", connection_id.name, DEFAULT_CONNECTION_CONFIG_FILE))
            connection_config = self.connection_loader.load(open(path))
            deps = cast(Dependencies, connection_config.dependencies)
            dependencies.update(deps)

        for skill_id in self.agent_config.skills:
            path = str(Path("skills", skill_id.name, DEFAULT_SKILL_CONFIG_FILE))
            skill_config = self.skill_loader.load(open(path))
            deps = cast(Dependencies, skill_config.dependencies)
            dependencies.update(deps)

        return dependencies


pass_ctx = click.make_pass_decorator(Context)


def _try_to_load_agent_config(ctx: Context):
    try:
        path = Path(DEFAULT_AEA_CONFIG_FILE)
        fp = open(str(path), mode="r", encoding="utf-8")
        ctx.agent_config = ctx.agent_loader.load(fp)
        logging.config.dictConfig(ctx.agent_config.logging_config)
    except FileNotFoundError:
        logger.error("Agent configuration file '{}' not found in the current directory.".format(DEFAULT_AEA_CONFIG_FILE))
        sys.exit(1)
    except jsonschema.exceptions.ValidationError:
        logger.error("Agent configuration file '{}' is invalid. Please check the documentation.".format(DEFAULT_AEA_CONFIG_FILE))
        sys.exit(1)


def _try_to_load_protocols(ctx: Context):
    for protocol_public_id in ctx.agent_config.protocols:
        protocol_name = protocol_public_id.name
        logger.debug("Processing protocol {}".format(protocol_public_id))
        try:
            ctx.protocol_loader.load(open(os.path.join("protocols", protocol_name, DEFAULT_PROTOCOL_CONFIG_FILE)))
        except FileNotFoundError:
            logger.error("Protocol configuration file for protocol {} not found.".format(protocol_name))
            sys.exit(1)

        try:
            protocol_spec = importlib.util.spec_from_file_location(protocol_name, os.path.join("protocols", protocol_name, "__init__.py"))
            protocol_module = importlib.util.module_from_spec(protocol_spec)
            protocol_spec.loader.exec_module(protocol_module)  # type: ignore
            sys.modules[protocol_spec.name + "_protocol"] = protocol_module
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
            'Version: {version}\n'
            '{line}\n'.format(
                name=item['name'],
                # TODO: switch to unsafe get public_id when every obj has it
                public_id=item.get('public_id'),
                description=item['description'],
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


def retrieve_details(name: str, loader: ConfigLoader, config_filepath: str):
    """Return description of a protocol, skill or connection."""
    config = loader.load(open(str(config_filepath)))
    assert config.name == name
    return {"name": config.name, "description": config.description, "version": config.version}


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
