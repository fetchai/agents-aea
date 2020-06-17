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
from pathlib import Path

import click

from aea.cli.utils.click_utils import PublicIdParameter
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project, pass_ctx
from aea.cli.utils.loggers import logger
from aea.configurations.base import DEFAULT_AEA_CONFIG_FILE, PublicId


@click.group()
@click.pass_context
@check_aea_project
def remove(click_context):
    """Remove a resource from the agent."""


@remove.command()
@click.argument("connection_id", type=PublicIdParameter(), required=True)
@pass_ctx
def connection(ctx: Context, connection_id):
    """
    Remove a connection from the agent.

    It expects the public id of the connection to remove from the local registry.
    """
    remove_item(ctx, "connection", connection_id)


@remove.command()
@click.argument("contract_id", type=PublicIdParameter(), required=True)
@pass_ctx
def contract(ctx: Context, contract_id):
    """
    Remove a contract from the agent.

    It expects the public id of the contract to remove from the local registry.
    """
    remove_item(ctx, "contract", contract_id)


@remove.command()
@click.argument("protocol_id", type=PublicIdParameter(), required=True)
@pass_ctx
def protocol(ctx: Context, protocol_id):
    """
    Remove a protocol from the agent.

    It expects the public id of the protocol to remove from the local registry.
    """
    remove_item(ctx, "protocol", protocol_id)


@remove.command()
@click.argument("skill_id", type=PublicIdParameter(), required=True)
@pass_ctx
def skill(ctx: Context, skill_id):
    """
    Remove a skill from the agent.

    It expects the public id of the skill to remove from the local registry.
    """
    remove_item(ctx, "skill", skill_id)


def remove_item(ctx: Context, item_type: str, item_id: PublicId) -> None:
    """
    Remove an item from the configuration file and agent, given the public id.

    :param ctx: Context object.
    :param item_type: type of item.
    :param item_id: item public ID.

    :return: None
    :raises ClickException: if some error occures.
    """
    item_name = item_id.name
    item_type_plural = "{}s".format(item_type)
    existing_item_ids = getattr(ctx.agent_config, item_type_plural)
    existing_items_name_to_ids = {
        public_id.name: public_id for public_id in existing_item_ids
    }

    agent_name = ctx.agent_config.agent_name
    click.echo(
        "Removing {item_type} '{item_name}' from the agent '{agent_name}'...".format(
            agent_name=agent_name, item_type=item_type, item_name=item_name
        )
    )

    if (
        item_id not in existing_items_name_to_ids.keys()
        and item_id not in existing_item_ids
    ):
        raise click.ClickException(
            "The {} '{}' is not supported.".format(item_type, item_id)
        )

    item_folder = Path(ctx.cwd, "vendor", item_id.author, item_type_plural, item_name)
    if not item_folder.exists():
        # check if it is present in custom packages.
        item_folder = Path(ctx.cwd, item_type_plural, item_name)
        if not item_folder.exists():
            raise click.ClickException(
                "{} {} not found. Aborting.".format(item_type.title(), item_name)
            )
        elif (
            item_folder.exists() and not ctx.agent_config.author == item_id.author
        ):  # pragma: no cover
            raise click.ClickException(
                "{} {} author is different from {} agent author. "
                "Please fix the author field.".format(item_name, item_type, agent_name)
            )
        else:
            logger.debug(
                "Removing local {} {}.".format(item_type, item_name)
            )  # pragma: no cover

    try:
        shutil.rmtree(item_folder)
    except BaseException:
        raise click.ClickException("An error occurred.")

    # removing the protocol to the configurations.
    item_public_id = existing_items_name_to_ids[item_name]
    logger.debug("Removing the {} from {}".format(item_type, DEFAULT_AEA_CONFIG_FILE))
    existing_item_ids.remove(item_public_id)
    with open(os.path.join(ctx.cwd, DEFAULT_AEA_CONFIG_FILE), "w") as f:
        ctx.agent_loader.dump(ctx.agent_config, f)
