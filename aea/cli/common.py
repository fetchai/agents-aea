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
from typing import Dict, List, cast

import click
import jsonschema  # type: ignore
from dotenv import load_dotenv

from aea.cli.loggers import default_logging_config
from aea.configurations.base import DEFAULT_AEA_CONFIG_FILE, AgentConfig, SkillConfig, ConnectionConfig, ProtocolConfig, \
    DEFAULT_PROTOCOL_CONFIG_FILE, DEFAULT_CONNECTION_CONFIG_FILE, DEFAULT_SKILL_CONFIG_FILE
from aea.configurations.loader import ConfigLoader

logger = logging.getLogger("aea")
logger = default_logging_config(logger)

DEFAULT_REGISTRY_PATH = "../packages"


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

    def get_dependencies(self) -> List[str]:
        """Aggregate the dependencies from every component.

        :return a list of dependency version specification. e.g. ["gym >= 1.0.0"]
        """
        dependencies = []  # type: List[str]
        for protocol_id in self.agent_config.protocols:
            path = str(Path("protocols", protocol_id, DEFAULT_PROTOCOL_CONFIG_FILE))
            protocol_config = self.protocol_loader.load(open(path))
            deps = cast(List[str], protocol_config.dependencies)
            dependencies.extend(deps)

        for connection_id in self.agent_config.connections:
            path = str(Path("connections", connection_id, DEFAULT_CONNECTION_CONFIG_FILE))
            connection_config = self.connection_loader.load(open(path))
            deps = cast(List[str], connection_config.dependencies)
            dependencies.extend(deps)

        for skill_id in self.agent_config.skills:
            path = str(Path("skills", skill_id, DEFAULT_SKILL_CONFIG_FILE))
            skill_config = self.skill_loader.load(open(path))
            deps = cast(List[str], skill_config.dependencies)
            dependencies.extend(deps)

        return sorted(set(dependencies))


pass_ctx = click.make_pass_decorator(Context)


def _try_to_load_agent_config(ctx: Context):
    try:
        path = Path(DEFAULT_AEA_CONFIG_FILE)
        fp = open(str(path), mode="r", encoding="utf-8")
        ctx.agent_config = ctx.agent_loader.load(fp)
        logging.config.dictConfig(ctx.agent_config.logging_config)
    except FileNotFoundError:
        logger.error("Agent configuration file '{}' not found in the current directory.".format(DEFAULT_AEA_CONFIG_FILE))
        exit(-1)
    except jsonschema.exceptions.ValidationError as e:
        logger.error("Agent configuration file '{}' is invalid. Please check the documentation.".format(DEFAULT_AEA_CONFIG_FILE))
        exit(-1)


def _try_to_load_protocols(ctx: Context):
    for protocol_name in ctx.agent_config.protocols:
        try:
            logger.debug("Processing protocol {}".format(protocol_name))
            protocol_config = ctx.protocol_loader.load(open(os.path.join("protocols", protocol_name, DEFAULT_PROTOCOL_CONFIG_FILE)))
            if protocol_config is None:
                logger.debug("Protocol configuration file for protocol {} not found.".format(protocol_name))
                exit(-1)

            protocol_spec = importlib.util.spec_from_file_location(protocol_name, os.path.join(ctx.agent_config.registry_path, "protocols", protocol_name, "__init__.py"))
            if protocol_spec is None:
                logger.warning("Protocol not found in registry.")
                continue

            protocol_module = importlib.util.module_from_spec(protocol_spec)
            sys.modules[protocol_spec.name + "_protocol"] = protocol_module
        except FileNotFoundError:
            logger.error("Protocol {} not found in registry".format(protocol_name))
            exit(-1)


def _load_env_file(env_file: str):
    """
    Load the content of the environment file into the process environment.

    :param env_file: path to the env file.
    :return: None.
    """
    load_dotenv(dotenv_path=Path(env_file), override=False)


class AEAConfigException(Exception):
    """Exception about AEA configuration."""
