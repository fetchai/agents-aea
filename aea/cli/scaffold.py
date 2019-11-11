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

"""Implementation of the 'aea add' subcommand."""

import os
import shutil
import sys
from pathlib import Path

import click
from jsonschema import ValidationError

from aea import AEA_DIR
from aea.cli.common import Context, pass_ctx, logger, _try_to_load_agent_config
from aea.configurations.base import DEFAULT_AEA_CONFIG_FILE


@click.group()
@pass_ctx
def scaffold(ctx: Context):
    """Scaffold a resource for the agent."""
    _try_to_load_agent_config(ctx)


@scaffold.command()
@click.argument('connection_name', type=str, required=True)
@pass_ctx
def connection(ctx: Context, connection_name: str) -> None:
    """Add a connection scaffolding to the configuration file and agent."""
    # check if we already have a connection with the same name
    logger.debug("Connections already supported by the agent: {}".format(ctx.agent_config.connections))
    if connection_name in ctx.agent_config.connections:
        logger.error("A connection with name '{}' already exists. Aborting...".format(connection_name))
        sys.exit(1)

    try:

        Path("connections").mkdir(exist_ok=True)

        # create the connection folder
        dest = Path(os.path.join("connections", connection_name))

        # copy the skill package into the agent's supported skills.
        src = Path(os.path.join(AEA_DIR, "connections", "scaffold"))
        logger.info("Copying connection modules. src={} dst={}".format(src, dest))

        shutil.copytree(src, dest)

        # add the connection to the configurations.
        logger.info("Registering the connection into {}".format(DEFAULT_AEA_CONFIG_FILE))
        ctx.agent_config.connections.add(connection_name)
        ctx.agent_loader.dump(ctx.agent_config, open(os.path.join(ctx.cwd, DEFAULT_AEA_CONFIG_FILE), "w"))

    except FileExistsError:
        logger.error("A connection with this name already exists. Please choose a different name and try again.")
        sys.exit(1)
    except ValidationError:
        logger.error("Error when validating the skill configuration file.")
        shutil.rmtree(os.path.join("connections", connection_name), ignore_errors=True)
        sys.exit(1)
    except Exception as e:
        logger.exception(e)
        shutil.rmtree(os.path.join("connections", connection_name), ignore_errors=True)
        sys.exit(1)


@scaffold.command()
@click.argument('protocol_name', type=str, required=True)
@pass_ctx
def protocol(ctx: Context, protocol_name: str):
    """Add a protocol scaffolding to the configuration file and agent."""
    # check if we already have a protocol with the same name
    logger.debug("Protocols already supported by the agent: {}".format(ctx.agent_config.protocols))
    if protocol_name in ctx.agent_config.protocols:
        logger.error("A protocol with name '{}' already exists. Aborting...".format(protocol_name))
        sys.exit(1)

    try:
        # create the 'protocols' folder if it doesn't exist:
        Path("protocols").mkdir(exist_ok=True)

        # create the protocol folder
        dest = Path(os.path.join("protocols", protocol_name))

        # copy the skill package into the agent's supported skills.
        src = Path(os.path.join(AEA_DIR, "protocols", "scaffold"))
        logger.info("Copying protocol modules. src={} dst={}".format(src, dest))

        shutil.copytree(src, dest)

        # add the protocol to the configurations.
        logger.info("Registering the protocol into {}".format(DEFAULT_AEA_CONFIG_FILE))
        ctx.agent_config.protocols.add(protocol_name)
        ctx.agent_loader.dump(ctx.agent_config, open(os.path.join(ctx.cwd, DEFAULT_AEA_CONFIG_FILE), "w"))

    except FileExistsError:
        logger.error("A protocol with this name already exists. Please choose a different name and try again.")
        sys.exit(1)
    except ValidationError:
        logger.error("Error when validating the skill configuration file.")
        shutil.rmtree(os.path.join("protocols", protocol_name), ignore_errors=True)
        sys.exit(1)
    except Exception as e:
        logger.exception(e)
        shutil.rmtree(os.path.join("protocols", protocol_name), ignore_errors=True)
        sys.exit(1)


@scaffold.command()
@click.argument('skill_name', type=str, required=True)
@pass_ctx
def skill(ctx: Context, skill_name: str):
    """Add a skill scaffolding to the configuration file and agent."""
    # check if we already have a skill with the same name
    logger.debug("Skills already supported by the agent: {}".format(ctx.agent_config.skills))
    if skill_name in ctx.agent_config.skills:
        logger.error("A skill with name '{}' already exists. Aborting...".format(skill_name))
        sys.exit(1)

    try:
        # create the 'skills' folder if it doesn't exist:
        Path("skills").mkdir(exist_ok=True)

        # create the skill folder
        dest = Path(os.path.join("skills", skill_name))

        # copy the skill package into the agent's supported skills.
        src = Path(os.path.join(AEA_DIR, "skills", "scaffold"))
        logger.info("Copying skill modules. src={} dst={}".format(src, dest))

        shutil.copytree(src, dest)

        # add the skill to the configurations.
        logger.info("Registering the protocol into {}".format(DEFAULT_AEA_CONFIG_FILE))
        ctx.agent_config.skills.add(skill_name)
        ctx.agent_loader.dump(ctx.agent_config, open(os.path.join(ctx.cwd, DEFAULT_AEA_CONFIG_FILE), "w"))

    except FileExistsError:
        logger.error("A skill with this name already exists. Please choose a different name and try again.")
        sys.exit(1)
    except ValidationError:
        logger.error("Error when validating the skill configuration file.")
        shutil.rmtree(os.path.join("skills", skill_name), ignore_errors=True)
        sys.exit(1)
    except Exception as e:
        logger.exception(e)
        shutil.rmtree(os.path.join("skills", skill_name), ignore_errors=True)
        sys.exit(1)
