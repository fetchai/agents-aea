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

import click
import click_log
from jsonschema import ValidationError

import aea
from aea.cli.add import add
from aea.cli.common import Context, pass_ctx, logger
from aea.skills.base.config import DEFAULT_AEA_CONFIG_FILE, ConnectionConfig, AgentConfig
from aea.cli.remove import remove
from aea.cli.run import run


@click.group()
@click.version_option('0.1.0')
@click.pass_context
@click_log.simple_verbosity_option(logger, default="INFO")
def cli(ctx) -> None:
    """Command-line tool for setting up an Autonomous Economic Agent."""
    ctx.obj = Context(cwd=".")


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

        # create a config file inside it
        config_file = open(os.path.join(agent_name, DEFAULT_AEA_CONFIG_FILE), "w")
        agent_config = AgentConfig(agent_name=agent_name, aea_version=aea.__version__, private_key_pem_path="")
        agent_config.set_default_connection(ConnectionConfig(
            name="default-oef",
            type="oef",
            addr="127.0.0.1",
            port=10000
        ))
        ctx.agent_loader.dump(agent_config, config_file)
        logger.info("Created config file {}".format(DEFAULT_AEA_CONFIG_FILE))

    except OSError:
        logger.error("Directory already exist. Aborting...")
        exit(-1)
    except ValidationError as e:
        logger.error(str(e))
        shutil.rmtree(agent_name, ignore_errors=True)
        exit(-1)
    except Exception as e:
        logger.exception(e)
        shutil.rmtree(agent_name, ignore_errors=True)
        exit(-1)


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
        exit(-1)


cli.add_command(add)
cli.add_command(remove)
cli.add_command(run)

if __name__ == '__main__':
    cli()
