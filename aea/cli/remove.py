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
import sys

import click

from aea.cli.common import Context, pass_ctx, logger, try_to_load_agent_config, PublicIdParameter
from aea.configurations.base import DEFAULT_AEA_CONFIG_FILE, PublicId


@click.group()
@pass_ctx
def remove(ctx: Context):
    """Remove a resource from the agent."""
    try_to_load_agent_config(ctx)


def _remove_item(ctx: Context, item_type, item_id: PublicId):
    """Remove an item from the configuration file and agent, given the public id."""
    item_name = item_id.name
    item_type_plural = "{}s".format(item_type)
    existing_item_ids = getattr(ctx.agent_config, item_type_plural)
    existing_items_name_to_ids = {public_id.name: public_id for public_id in existing_item_ids}

    agent_name = ctx.agent_config.agent_name
    logger.info("Removing {item_type} '{item_name}' from the agent '{agent_name}'..."
                .format(agent_name=agent_name, item_type=item_type, item_name=item_name))

    if item_id not in existing_items_name_to_ids.keys() and item_id not in existing_item_ids:
        logger.error("The {} '{}' is not supported.".format(item_type, item_id))
        sys.exit(1)

    if item_id.author != ctx.agent_config.author:
        item_folder = os.path.join("vendor", item_id.author, item_type_plural, item_name)
    else:
        item_folder = os.path.join(item_type_plural, item_name)

    try:
        shutil.rmtree(item_folder)
    except BaseException:
        logger.exception("An error occurred.")
        sys.exit(1)

    # removing the protocol to the configurations.
    item_public_id = existing_items_name_to_ids[item_name]
    logger.debug("Removing the {} from {}".format(item_type, DEFAULT_AEA_CONFIG_FILE))
    existing_item_ids.remove(item_public_id)
    ctx.agent_loader.dump(ctx.agent_config, open(DEFAULT_AEA_CONFIG_FILE, "w"))


@remove.command()
@click.argument('connection_id', type=PublicIdParameter(), required=True)
@pass_ctx
def connection(ctx: Context, connection_id):
    """
    Remove a connection from the agent.

    It expects the public id of the connection to remove from the local registry.
    """
    _remove_item(ctx, "connection", connection_id)


@remove.command()
@click.argument('protocol_id', type=PublicIdParameter(), required=True)
@pass_ctx
def protocol(ctx: Context, protocol_id):
    """
    Remove a protocol from the agent.

    It expects the public id of the protocol to remove from the local registry.
    """
    _remove_item(ctx, "protocol", protocol_id)


@remove.command()
@click.argument('skill_id', type=PublicIdParameter(), required=True)
@pass_ctx
def skill(ctx: Context, skill_id):
    """
    Remove a skill from the agent.

    It expects the public id of the skill to remove from the local registry.
    """
    _remove_item(ctx, "skill", skill_id)
