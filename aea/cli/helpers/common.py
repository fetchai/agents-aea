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
import pprint
from typing import List, Optional, Dict

import click
import click_log
import yaml

import aea

DEFAULT_AEA_CONFIG_FILE = "aea-config.yaml"
logger = logging.getLogger("aea")
logger = click_log.basic_config(logger=logger)


class ConnectionConfig:
    """Handle connection configuration."""

    def __init__(self, name: str, type: str, **config):
        """Initialize a connection configuration object."""
        self.name = name
        self.type = type
        self.config = config

    @classmethod
    def from_dict(cls, obj: dict) -> 'ConnectionConfig':
        """Parse configuration from a dictionary object."""
        name = obj["name"]
        type = obj["type"]
        config = obj["config"]
        return ConnectionConfig(name, type, **config)


class AgentConfig(object):
    """Class to represent the agent configuration file."""

    def __init__(self, agent_name: Optional[str] = None):
        """Instantiate the agent configuration object."""
        self.agent_name = agent_name
        self.aea_version = aea.__version__
        self.connections = {}  # type: Dict[str, ConnectionConfig]
        self.protocols = []  # type: List[Dict]
        self.skills = []  # type: List[Dict]

        # set default connection
        self.connections["default-oef"] = ConnectionConfig(
            name="default-oef",
            type="oef",
            addr="127.0.0.1",
            port=10000
        )
        self.default_connection = "default-oef"

    def load(self, path):
        """Load data from an agent configuration file."""
        file = open(path, mode="r", encoding="utf-8")
        config_file = yaml.safe_load(file)

        self.agent_name = config_file["agent_name"]
        self.aea_version = config_file["aea_version"]
        self.connections = {c["connection"]["name"]: ConnectionConfig.from_dict(c["connection"])
                            for c in config_file["connections"]}
        self.protocols = config_file["protocols"]
        self.skills = config_file["skills"]

    def dump(self, file):
        """Dump data to an agent configuration file."""
        result = vars(self)
        result["connections"] = [{"connection": vars(c)} for c in result["connections"].values()]

        logger.debug("Dumping YAML: {}".format(pprint.pformat(result)))
        yaml.safe_dump(result, file)


class Context(object):
    """A class to keep configuration of the cli tool."""

    agent_config: AgentConfig

    def __init__(self):
        """Init the context."""
        self.config = {}

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
        ctx.agent_config = AgentConfig()
        ctx.agent_config.load(DEFAULT_AEA_CONFIG_FILE)
    except FileNotFoundError:
        logger.error("Agent configuration file '{}' not found in the current directory. "
                     "Aborting...".format(DEFAULT_AEA_CONFIG_FILE))
        exit(-1)


class AEAConfigException(Exception):
    """Exception about AEA configuration."""
