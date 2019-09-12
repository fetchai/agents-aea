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
from pathlib import Path
from typing import Dict

import click
import click_log
import jsonschema  # type: ignore

from aea.skills.base.config import DEFAULT_AEA_CONFIG_FILE, AgentConfig
from aea.skills.base.loader import ConfigLoader

logger = logging.getLogger("aea")
logger = click_log.basic_config(logger=logger)


class Context(object):
    """A class to keep configuration of the cli tool."""

    agent_config: AgentConfig

    def __init__(self, cwd: str = "."):
        """Init the context."""
        self.config = dict()  # type: Dict
        self.loader = ConfigLoader()
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
        ctx.agent_config = ctx.loader.load_agent_configuration(fp)
    except FileNotFoundError:
        logger.error("Agent configuration file '{}' not found in the current directory. "
                     "Aborting...".format(DEFAULT_AEA_CONFIG_FILE))
        exit(-1)
    except jsonschema.exceptions.ValidationError:
        logger.error("Agent configuration file '{}' is invalid. Please check the documentation."
                     "Aborting...".format(DEFAULT_AEA_CONFIG_FILE))


class AEAConfigException(Exception):
    """Exception about AEA configuration."""
