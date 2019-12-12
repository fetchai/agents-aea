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

"""Core definitions for the AEA command-line tool."""

import os
import shutil
import sys
from pathlib import Path
from typing import cast

import click
from click import pass_context
from jsonschema import ValidationError

import aea
from aea.cli.add import add
from aea.cli.add import connection, skill
from aea.cli.common import Context, pass_ctx, logger, _try_to_load_agent_config, DEFAULT_REGISTRY_PATH
from aea.cli.install import install
from aea.cli.list import list as _list
from aea.cli.loggers import simple_verbosity_option
from aea.cli.remove import remove
from aea.cli.run import run
from aea.cli.scaffold import scaffold
from aea.cli.search import search
from aea.configurations.base import DEFAULT_AEA_CONFIG_FILE, AgentConfig, PrivateKeyPathConfig
from aea.crypto.default import DefaultCrypto
from aea.crypto.ethereum import EthereumCrypto
from aea.crypto.fetchai import FetchAICrypto
from aea.crypto.helpers import DEFAULT_PRIVATE_KEY_FILE, FETCHAI_PRIVATE_KEY_FILE, ETHEREUM_PRIVATE_KEY_FILE, \
    _validate_private_key_path

DEFAULT_CONNECTION = "oef"
DEFAULT_SKILL = "error"


@click.group(name="aea")
@click.version_option(aea.__version__, prog_name="aea")
@simple_verbosity_option(logger, default="INFO")
@click.pass_context
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
    logger.info("Initializing AEA project '{}'".format(agent_name))
    logger.info("Creating project directory '/{}'".format(agent_name))

    # create the agent's directory
    try:
        path.mkdir(exist_ok=False)

        # create a config file inside it
        logger.info("Creating config file {}".format(DEFAULT_AEA_CONFIG_FILE))
        config_file = open(os.path.join(agent_name, DEFAULT_AEA_CONFIG_FILE), "w")
        agent_config = AgentConfig(agent_name=agent_name, aea_version=aea.__version__, authors="", version="v1", license="", url="", registry_path=DEFAULT_REGISTRY_PATH, description="")
        agent_config.default_connection = DEFAULT_CONNECTION
        ctx.agent_loader.dump(agent_config, config_file)

        # next commands must be done from the agent's directory -> overwrite ctx.cwd
        ctx.agent_config = agent_config
        ctx.cwd = agent_config.agent_name

        logger.info("Default connections:")
        click_context.invoke(connection, connection_name=DEFAULT_CONNECTION)

        logger.info("Default skills:")
        click_context.invoke(skill, skill_name=DEFAULT_SKILL)

    except OSError:
        logger.error("Directory already exist. Aborting...")
        sys.exit(1)
    except ValidationError as e:
        logger.error(str(e))
        shutil.rmtree(agent_name, ignore_errors=True)
        sys.exit(1)
    except Exception as e:
        logger.exception(e)
        shutil.rmtree(agent_name, ignore_errors=True)
        sys.exit(1)


@cli.command()
@click.argument('agent_name', type=click.Path(exists=True, file_okay=False, dir_okay=True), required=True)
@pass_ctx
def delete(ctx: Context, agent_name):
    """Delete an agent."""
    path = Path(agent_name)

    # check that the target folder is an AEA project.
    cwd = os.getcwd()
    try:
        os.chdir(agent_name)
        fp = open(DEFAULT_AEA_CONFIG_FILE, mode="r", encoding="utf-8")
        ctx.agent_config = ctx.agent_loader.load(fp)
        _try_to_load_agent_config(ctx)
    except Exception:
        logger.error("The name provided is not an AEA project.")
        sys.exit(1)
    finally:
        os.chdir(cwd)

    logger.info("Deleting agent project directory '/{}'...".format(path))

    # delete the agent's directory
    try:
        shutil.rmtree(path, ignore_errors=False)
    except OSError:
        logger.error("An error occurred while deleting the agent directory. Aborting...")
        sys.exit(1)


@cli.command()
@pass_ctx
def freeze(ctx: Context):
    """Get the dependencies."""
    _try_to_load_agent_config(ctx)
    for dependency_name, dependency_data in sorted(ctx.get_dependencies().items(), key=lambda x: x[0]):
        print(dependency_name + dependency_data.get("version", ""))


@cli.command()
@pass_ctx
@click.option('-p', '--port', default=8080)
def gui(ctx: Context, port):
    """Run the CLI GUI."""
    import aea.cli_gui  # pragma: no cover
    logger.info("Running the GUI.....(press Ctrl+C to exit)")   # pragma: no cover
    aea.cli_gui.run(port)   # pragma: no cover


@cli.command()
@click.argument("type_", metavar="TYPE", type=click.Choice([
    DefaultCrypto.identifier,
    FetchAICrypto.identifier,
    EthereumCrypto.identifier,
    "all"]), required=True)
@pass_ctx
def generate_key(ctx: Context, type_):
    """Generate private keys."""
    if type_ == DefaultCrypto.identifier or type_ == "all":
        DefaultCrypto().dump(open(DEFAULT_PRIVATE_KEY_FILE, "wb"))
    if type_ == FetchAICrypto.identifier or type_ == "all":
        FetchAICrypto().dump(open(FETCHAI_PRIVATE_KEY_FILE, "wb"))
    if type_ == EthereumCrypto.identifier or type_ == "all":
        EthereumCrypto().dump(open(ETHEREUM_PRIVATE_KEY_FILE, "wb"))


@cli.command()
@click.argument("type_", metavar="TYPE", type=click.Choice([
    DefaultCrypto.identifier,
    FetchAICrypto.identifier,
    EthereumCrypto.identifier
]), required=True)
@click.argument("file", metavar="FILE", type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
                required=True)
@pass_ctx
def add_key(ctx: Context, type_, file):
    """Add a private key to the wallet."""
    _try_to_load_agent_config(ctx)
    _validate_private_key_path(file, type_)
    try:
        ctx.agent_config.private_key_paths.create(type_, PrivateKeyPathConfig(type_, file))
    except ValueError as e:     # pragma: no cover
        logger.error(str(e))    # pragma: no cover
    ctx.agent_loader.dump(ctx.agent_config, open(os.path.join(ctx.cwd, DEFAULT_AEA_CONFIG_FILE), "w"))


cli.add_command(add)
cli.add_command(_list)
cli.add_command(search)
cli.add_command(scaffold)
cli.add_command(remove)
cli.add_command(install)
cli.add_command(run)
