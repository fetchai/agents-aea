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
from click import pass_context
from jsonschema import ValidationError

import aea
from aea.cli.add import connection, add, skill
from aea.cli.common import Context, pass_ctx, logger, _try_to_load_agent_config
from aea.cli.list import list as _list
from aea.cli.install import install
from aea.cli.remove import remove
from aea.cli.run import run
from aea.cli.scaffold import scaffold
from aea.cli.search import search
from aea.configurations.base import DEFAULT_AEA_CONFIG_FILE, AgentConfig, DEFAULT_PRIVATE_KEY_PATHS

DEFAULT_CONNECTION = "oef"
DEFAULT_SKILL = "error"


@click.group()
@click.version_option('0.1.0')
@click.pass_context
@click_log.simple_verbosity_option(logger, default="INFO")
def cli(ctx) -> None:
    """Command-line tool for setting up an Autonomous Economic Agent."""
    ctx.obj = Context(cwd=".")


@cli.command()
@click.argument('agent_name', type=str, required=True)
@pass_context
def create(click_context, agent_name):
    """Create an agent."""
    ctx = cast(Context, click_context.obj)
    path = Path(agent_name)
    logger.info("Creating agent's directory in '{}'".format(path))

    # create the agent's directory
    try:
        path.mkdir(exist_ok=False)

        # create a config file inside it
        config_file = open(os.path.join(agent_name, DEFAULT_AEA_CONFIG_FILE), "w")
        agent_config = AgentConfig(agent_name=agent_name, aea_version=aea.__version__, authors="", version="v1", license="", url="", registry_path="../packages", private_key_paths=DEFAULT_PRIVATE_KEY_PATHS)
        agent_config.default_connection = DEFAULT_CONNECTION
        ctx.agent_loader.dump(agent_config, config_file)
        logger.info("Created config file {}".format(DEFAULT_AEA_CONFIG_FILE))

        # next commands must be done from the agent's directory -> overwrite ctx.cwd
        ctx.agent_config = agent_config
        ctx.cwd = agent_config.agent_name

        logger.info("Adding default connection '{}' to the agent...".format(DEFAULT_CONNECTION))
        click_context.invoke(connection, connection_name=DEFAULT_CONNECTION)

        logger.info("Adding default skill '{}' to the agent...".format(DEFAULT_SKILL))
        click_context.invoke(skill, skill_name=DEFAULT_SKILL)

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


@cli.command()
@pass_ctx
def freeze(ctx: Context):
    """Get the dependencies."""
    _try_to_load_agent_config(ctx)
    for d in ctx.get_dependencies():
        print(d)


cli.add_command(add)
cli.add_command(_list)
cli.add_command(search)
cli.add_command(scaffold)
cli.add_command(remove)
cli.add_command(install)
cli.add_command(run)

if __name__ == '__main__':
    cli()  # pragma: no cover
