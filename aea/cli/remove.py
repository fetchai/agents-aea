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

"""Implementation of the 'aea remove' subcommand."""

import os
import shutil

import click

from aea.cli.common import Context, pass_ctx, logger, _try_to_load_agent_config
from aea.configurations.base import DEFAULT_AEA_CONFIG_FILE


@click.group()
@pass_ctx
def remove(ctx: Context):
    """Remove a resource from the agent."""
    _try_to_load_agent_config(ctx)


@remove.command()
@click.argument('connection_name', type=str, required=True)
@pass_ctx
def connection(ctx: Context, connection_name):
    """Remove a connection from the agent."""
    agent_name = ctx.agent_config.agent_name
    logger.info("Removing connection {connection_name} from the agent {agent_name}..."
                .format(agent_name=agent_name, connection_name=connection_name))

    if connection_name not in ctx.agent_config.connections:
        logger.error("Connection '{}' not found.".format(connection_name))
        exit(-1)

    connection_folder = os.path.join("connections", connection_name)
    try:
        shutil.rmtree(connection_folder)
    except BaseException:
        logger.exception("An error occurred while deleting '{}'.".format(connection_folder))
        return

    ctx.agent_config.connections.remove(connection_name)

    # removing the connection to the configurations.
    logger.debug("Removing the connection from {}".format(DEFAULT_AEA_CONFIG_FILE))
    if connection_name in ctx.agent_config.connections:
        ctx.agent_config.connections.remove(connection_name)

    ctx.agent_loader.dump(ctx.agent_config, open(DEFAULT_AEA_CONFIG_FILE, "w"))


@remove.command()
@click.argument('protocol_name', type=str, required=True)
@pass_ctx
def protocol(ctx: Context, protocol_name):
    """Remove a protocol from the agent."""
    agent_name = ctx.agent_config.agent_name
    logger.info("Removing protocol {protocol_name} from the agent {agent_name}..."
                .format(agent_name=agent_name, protocol_name=protocol_name))

    if protocol_name not in ctx.agent_config.protocols:
        logger.warning("Protocol '{}' not found.".format(protocol_name))
        exit(-1)

    protocol_folder = os.path.join("protocols", protocol_name)
    try:
        shutil.rmtree(protocol_folder)
    except BaseException:
        logger.exception("An error occurred.")
        return

    # removing the protocol to the configurations.
    logger.debug("Removing the protocol from {}".format(DEFAULT_AEA_CONFIG_FILE))
    if protocol_name in ctx.agent_config.protocols:
        ctx.agent_config.protocols.remove(protocol_name)
    ctx.agent_loader.dump(ctx.agent_config, open(DEFAULT_AEA_CONFIG_FILE, "w"))


@remove.command()
@click.argument('skill_name', type=str, required=True)
@pass_ctx
def skill(ctx: Context, skill_name):
    """Remove a skill from the agent."""
    agent_name = ctx.agent_config.agent_name
    logger.info("Removing skill {skill_name} from the agent {agent_name}..."
                .format(agent_name=agent_name, skill_name=skill_name))

    if skill_name not in ctx.agent_config.skills:
        logger.warning("The skill '{}' is not supported.".format(skill_name))
        exit(-1)

    skill_folder = os.path.join("skills", skill_name)
    try:
        shutil.rmtree(skill_folder)
    except BaseException:
        logger.exception("An error occurred.")
        return

    # removing the protocol to the configurations.
    logger.debug("Removing the skill from {}".format(DEFAULT_AEA_CONFIG_FILE))
    if skill_name in ctx.agent_config.skills:
        ctx.agent_config.skills.remove(skill_name)
    ctx.agent_loader.dump(ctx.agent_config, open(DEFAULT_AEA_CONFIG_FILE, "w"))
