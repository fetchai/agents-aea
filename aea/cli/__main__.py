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

"""Entry-point for the AEA command-line tool."""

import os
import shutil
from pathlib import Path
from typing import cast

import click
import click_log

from aea.aea import AEA
from aea.channel.oef import OEFMailBox
from aea.cli.add import add
from aea.cli.remove import remove
from aea.cli.common import DEFAULT_AEA_CONFIG_FILE, AgentConfig, Context, pass_ctx, _try_to_load_agent_config, logger


@click.group()
@click.version_option('0.1.0')
@click.pass_context
@click_log.simple_verbosity_option(logger, default="INFO")
def cli(ctx) -> None:
    """
    Command-line tool for setting up an Autonomous Economic Agent.

    :param ctx: the context
    :return: None
    """
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
    agent_name = cast(str, ctx.agent_config.agent_name)
    agent = AEA(agent_name, directory=str(Path(".")))
    agent.mailbox = OEFMailBox(public_key=agent.crypto.public_key, oef_addr=oef_addr, oef_port=oef_port)
    try:
        agent.start()
    except KeyboardInterrupt:
        logger.info("Interrupted.")
    except Exception:
        raise
    finally:
        agent.stop()


cli.add_command(add)
cli.add_command(remove)

if __name__ == '__main__':
    cli()
