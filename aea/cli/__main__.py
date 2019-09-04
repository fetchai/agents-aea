#!/usr/bin/env python3
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
import importlib.util
import logging
import os
import pprint
import shutil
from pathlib import Path
from typing import Optional

import click
import click_log
import yaml

import aea
from aea.aea import AEA
from aea.channel.oef import OEFMailBox

logger = logging.getLogger("aea")
logger = click_log.basic_config(logger=logger)

DEFAULT_AEA_CONFIG_FILE = "aea-config.yaml"


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


@click.group()
@click.version_option('0.1.0')
@click.pass_context
@click_log.simple_verbosity_option(logger, default="INFO")
def cli(ctx):
    """A command-line tool for setting up an Autonomous Economic Agent."""
    ctx.obj = Context()


@cli.command()
@click.argument('agent_name', type=str, required=True)
@pass_ctx
def create(ctx: Context, agent_name):
    """Create an agent."""
    path = Path(agent_name)
    logger.info("Creating agent's directory in '{}'".format(path))

    # create the agent's directory
    try:
        path.mkdir(exist_ok=False)
    except OSError:
        logger.error("Directory already exist. Aborting...")
        return

    # create a config file inside it
    config_file = open(os.path.join(agent_name, DEFAULT_AEA_CONFIG_FILE), "w")
    agent_config = AgentConfig(agent_name=agent_name)
    agent_config.dump(config_file)

    logger.info("Created config file {}".format(DEFAULT_AEA_CONFIG_FILE))


@cli.command()
@click.argument('agent_name', type=str, required=True)
@pass_ctx
def delete(ctx: Context, agent_name):
    """Delete an agent."""
    path = Path(agent_name)
    logger.info("Deleting agent's directory in '{}'...".format(path))

    # delete the agent's directory
    try:
        shutil.rmtree(path, ignore_errors=False)
    except OSError:
        logger.error("An error occurred while deleting the agent directory. Aborting...")
        return


@cli.command()
@click.argument('oef_addr', type=str, default="127.0.0.1")
@click.argument('oef_port', type=int, default=10000)
@pass_ctx
def run(ctx: Context, oef_addr, oef_port):
    """Run the agent."""
    _try_to_load_agent_config(ctx)
    agent_name = ctx.agent_config.agent_name
    agent = AEA(agent_name, directory=str(Path(agent_name)))
    agent.mailbox = OEFMailBox(public_key=agent.crypto.public_key, oef_addr=oef_addr, oef_port=oef_port)
    try:
        agent.start()
    except KeyboardInterrupt:
        logger.info("Interrupted.")
    except Exception:
        raise
    finally:
        agent.stop()


@cli.group()
@pass_ctx
def add(ctx: Context):
    """Add a resource to the agent."""
    try:
        ctx.agent_config = AgentConfig()
        ctx.agent_config.load(DEFAULT_AEA_CONFIG_FILE)
    except FileNotFoundError:
        logger.error("Agent configuration file not found '{}'. Aborting...".format(DEFAULT_AEA_CONFIG_FILE))
        exit(-1)


@add.command()
@click.argument('protocol_name', type=str, required=True)
@pass_ctx
def protocol(ctx: Context, protocol_name):
    """Add a protocol to the agent."""
    agent_name = ctx.agent_config.agent_name
    logger.debug("Adding protocol {protocol_name} to the agent {agent_name}..."
                 .format(agent_name=agent_name, protocol_name=protocol_name))

    # find the supported protocols and check if the candidate protocol is supported.
    protocols_module_spec = importlib.util.find_spec("aea.protocols")
    _protocols_submodules = protocols_module_spec.loader.contents()
    _protocols_submodules = filter(lambda x: not x.startswith("__") and x != "base", _protocols_submodules)
    aea_supported_protocol = set(_protocols_submodules)
    logger.debug("Supported protocols: {}".format(aea_supported_protocol))
    if protocol_name not in aea_supported_protocol:
        logger.error("Protocol '{}' not supported. Aborting...".format(protocol_name))
        return

    # check if we already have a protocol with the same name
    logger.debug("Protocols already supported by the agent: {}".format(ctx.agent_config.protocols))
    if protocol_name in ctx.agent_config.protocols:
        logger.error("A protocol with name '{}' already exists. Aborting...".format(protocol_name))
        return

    # copy the protocol package into the agent's supported protocols.
    protocols_dir = protocols_module_spec.submodule_search_locations[0]
    src = os.path.join(protocols_dir, protocol_name)
    dest = os.path.join("protocols", protocol_name)
    logger.info("Copying protocol modules. src={} dst={}".format(src, dest))
    shutil.copytree(src, dest)

    # make the 'protocols' folder a Python package.
    logger.debug("Creating {}".format(os.path.join(agent_name, "protocols", "__init__.py")))
    Path(os.path.join("protocols", "__init__.py")).touch(exist_ok=True)

    # add the protocol to the configurations.
    logger.debug("Registering the protocol into {}".format(DEFAULT_AEA_CONFIG_FILE))
    ctx.agent_config.protocols.append(protocol_name)
    ctx.agent_config.dump(open(DEFAULT_AEA_CONFIG_FILE, "w"))


@add.command()
@click.argument('agent_name', type=str, required=True)
@click.argument('skill_name', type=str, required=True)
@pass_ctx
def skill(ctx: Context, agent_name, skill_name):
    """Add a skill to the agent."""
    pass


if __name__ == '__main__':
    cli()
