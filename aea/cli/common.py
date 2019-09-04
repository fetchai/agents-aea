# -*- coding: utf-8 -*-
import logging
import pprint
from typing import Optional

import click
import click_log
import yaml

import aea

DEFAULT_AEA_CONFIG_FILE = "aea-config.yaml"
logger = logging.getLogger("aea")
logger = click_log.basic_config(logger=logger)


class AgentConfig(object):
    """Class to represent the agent configuration file."""

    def __init__(self, agent_name: Optional[str] = None,):
        """Instantiate the agent configuration object."""
        self.agent_name = agent_name
        self.aea_version = aea.__version__
        self.protocols = []
        self.skills = []

    def load(self, path):
        """Load data from an agent configuration file."""
        file = open(path, mode="r", encoding="utf-8")
        config_file = yaml.safe_load(file)

        self.agent_name = config_file["agent_name"]
        self.aea_version = config_file["aea_version"]
        self.protocols = config_file["protocols"]
        self.skills = config_file["skills"]

    def dump(self, file):
        """Dump data to an agent configuration file."""
        logger.debug("Dumping YAML: {}".format(pprint.pformat(vars(self))))
        yaml.safe_dump(vars(self), file)


class Context(object):
    """A class to keep configuration of the cli tool."""

    def __init__(self):
        """Init the context."""
        self.config = {}
        self.agent_config = None  # type: Optional[AgentConfig]

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
