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
import os
from pathlib import Path
import sys
from typing import Dict

import click
import click_log
import jsonschema  # type: ignore

from aea.configurations.base import DEFAULT_AEA_CONFIG_FILE, AgentConfig, SkillConfig, ConnectionConfig
from aea.configurations.loader import ConfigLoader

logger = logging.getLogger("aea")
logger = click_log.basic_config(logger=logger)


class Context(object):
    """A class to keep configuration of the cli tool."""

    agent_config: AgentConfig

    def __init__(self, cwd: str = "."):
        """Init the context."""
        self.config = dict()  # type: Dict
        self.agent_loader = ConfigLoader("aea-config_schema.json", AgentConfig)
        self.skill_loader = ConfigLoader("skill-config_schema.json", SkillConfig)
        self.connection_loader = ConfigLoader("connection-config_schema.json", ConnectionConfig)
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


pass_ctx = click.make_pass_decorator(Context)


def _try_to_load_agent_config(ctx: Context):
    try:
        path = Path(DEFAULT_AEA_CONFIG_FILE)
        fp = open(str(path), mode="r", encoding="utf-8")
        ctx.agent_config = ctx.agent_loader.load(fp)
    except FileNotFoundError:
        logger.error("Agent configuration file '{}' not found in the current directory. "
                     "Aborting...".format(DEFAULT_AEA_CONFIG_FILE))
        exit(-1)
    except jsonschema.exceptions.ValidationError:
        logger.error("Agent configuration file '{}' is invalid. Please check the documentation."
                     "Aborting...".format(DEFAULT_AEA_CONFIG_FILE))


def _try_to_load_protocols(ctx: Context):
    try:
        for protocol_name in ctx.agent_config.protocols:
            logger.debug("Processing protocol {}".format(protocol_name))
            # protocol_config = ctx.protocol_loader.load(open(os.path.join(directory, DEFAULT_PROTOCOL_CONFIG_FILE)))
            # if protocol_config is None:
            #     exit(-1)

            protocol_spec = importlib.util.spec_from_file_location(protocol_name, os.path.join(ctx.agent_config.registry_path, "protocols", "gym", "__init__.py"))
            if protocol_spec is None:
                logger.warning("Protocol not found in registry.")
                continue

            protocol_module = importlib.util.module_from_spec(protocol_spec)
            sys.modules[protocol_spec.name + "_protocol"] = protocol_module
    except FileNotFoundError:
        logger.error("Protocols not found in registry")
        exit(-1)


class AEAConfigException(Exception):
    """Exception about AEA configuration."""
