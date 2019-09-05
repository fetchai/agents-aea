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

from aea.cli.common import DEFAULT_AEA_CONFIG_FILE, AgentConfig, Context, pass_ctx, logger


@click.group()
@pass_ctx
def remove(ctx: Context):
    """Remove a resource from the agent."""
    try:
        ctx.agent_config = AgentConfig()
        ctx.agent_config.load(DEFAULT_AEA_CONFIG_FILE)
    except FileNotFoundError:
        logger.error("Agent configuration file not found '{}'. Aborting...".format(DEFAULT_AEA_CONFIG_FILE))
        exit(-1)


@remove.command()
@click.argument('protocol_name', type=str, required=True)
@pass_ctx
def protocol(ctx: Context, protocol_name):
    """Remove a protocol from the agent."""
    agent_name = ctx.agent_config.agent_name
    logger.info("Removing protocol {protocol_name} from the agent {agent_name}..."
                .format(agent_name=agent_name, protocol_name=protocol_name))

    if protocol_name not in ctx.agent_config.protocols:
        logger.warning("The protocol '{}' is not supported.".format(protocol_name))

    try:
        shutil.rmtree(os.path.join("protocols", protocol_name))
    except:
        logger.exception("An error occurred.")
        return

    # removing the protocol to the configurations.
    logger.debug("Removing the protocol from {}".format(DEFAULT_AEA_CONFIG_FILE))
    if protocol_name in ctx.agent_config.protocols:
        ctx.agent_config.protocols.remove(protocol_name)
    ctx.agent_config.dump(open(DEFAULT_AEA_CONFIG_FILE, "w"))


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

    try:
        shutil.rmtree(os.path.join("skills", skill_name))
    except:
        logger.exception("An error occurred.")
        return

    # removing the protocol to the configurations.
    logger.debug("Removing the skill from {}".format(DEFAULT_AEA_CONFIG_FILE))
    if skill_name in ctx.agent_config.skills:
        ctx.agent_config.skills.remove(skill_name)
    ctx.agent_config.dump(open(DEFAULT_AEA_CONFIG_FILE, "w"))
