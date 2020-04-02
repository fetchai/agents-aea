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
import sys
from pathlib import Path
from typing import Collection, cast

import click

from aea.cli.common import (
    Context,
    PublicIdParameter,
    _copy_package_directory,
    _find_item_locally,
    check_aea_project,
    logger,
)
from aea.cli.registry.utils import fetch_package
from aea.configurations.base import (
    ConfigurationType,
    DEFAULT_AEA_CONFIG_FILE,
    PublicId,
    _get_default_configuration_file_name_from_type,
)
from aea.configurations.base import (  # noqa: F401
    DEFAULT_CONNECTION_CONFIG_FILE,
    DEFAULT_PROTOCOL_CONFIG_FILE,
    DEFAULT_SKILL_CONFIG_FILE,
)
from aea.configurations.loader import ConfigLoader


@click.group()
@click.option("--local", is_flag=True, help="For adding from local folder.")
@click.pass_context
@check_aea_project
def add(click_context, local):
    """Add a resource to the agent."""
    ctx = cast(Context, click_context.obj)
    if local:
        ctx.set_config("is_local", True)


def _is_item_present(item_type, item_public_id, ctx):
    item_type_plural = item_type + "s"
    dest_path = Path(
        ctx.cwd, "vendor", item_public_id.author, item_type_plural, item_public_id.name
    )
    # check item presence only by author/package_name pair, without version.
    items_in_config = set(
        map(lambda x: (x.author, x.name), getattr(ctx.agent_config, item_type_plural))
    )
    return (
        item_public_id.author,
        item_public_id.name,
    ) in items_in_config and dest_path.exists()


def _add_protocols(click_context, protocols: Collection[PublicId]):
    ctx = cast(Context, click_context.obj)
    # check for dependencies not yet added, and add them.
    for protocol_public_id in protocols:
        if protocol_public_id not in ctx.agent_config.protocols:
            logger.debug(
                "Adding protocol '{}' to the agent...".format(protocol_public_id)
            )
            _add_item(click_context, "protocol", protocol_public_id)


def _add_item(click_context, item_type, item_public_id) -> None:
    """
    Add an item.

    :param click_context: the click context.
    :param item_type: the item type.
    :param item_public_id: the item public id.
    :return: None
    """
    ctx = cast(Context, click_context.obj)
    agent_name = cast(str, ctx.agent_config.agent_name)
    item_type_plural = item_type + "s"
    supported_items = getattr(ctx.agent_config, item_type_plural)

    is_local = ctx.config.get("is_local")

    click.echo(
        "Adding {} '{}' to the agent '{}'...".format(
            item_type, item_public_id, agent_name
        )
    )

    # check if we already have an item with the same name
    logger.debug(
        "{} already supported by the agent: {}".format(
            item_type_plural.capitalize(), supported_items
        )
    )
    if _is_item_present(item_type, item_public_id, ctx):
        logger.error(
            "A {} with id '{}/{}' already exists. Aborting...".format(
                item_type, item_public_id.author, item_public_id.name
            )
        )
        sys.exit(1)

    # find and add protocol
    if is_local:
        package_path = _find_item_locally(ctx, item_type, item_public_id)
        _copy_package_directory(
            ctx, package_path, item_type, item_public_id.name, item_public_id.author
        )
        if item_type in {"connection", "skill"}:
            configuration_file_name = _get_default_configuration_file_name_from_type(
                item_type
            )
            configuration_path = package_path / configuration_file_name
            configuration_loader = ConfigLoader.from_configuration_type(
                ConfigurationType(item_type)
            )
            item_configuration = configuration_loader.load(configuration_path.open())
            _add_protocols(click_context, item_configuration.protocols)
    else:
        fetch_package(item_type, public_id=item_public_id, cwd=ctx.cwd)

    # add the item to the configurations.
    logger.debug(
        "Registering the {} into {}".format(item_type, DEFAULT_AEA_CONFIG_FILE)
    )
    supported_items.add(item_public_id)
    ctx.agent_loader.dump(
        ctx.agent_config, open(os.path.join(ctx.cwd, DEFAULT_AEA_CONFIG_FILE), "w")
    )


@add.command()
@click.argument("connection_public_id", type=PublicIdParameter(), required=True)
@click.pass_context
def connection(click_context, connection_public_id: PublicId):
    """Add a connection to the configuration file."""
    _add_item(click_context, "connection", connection_public_id)


@add.command()
@click.argument("contract_public_id", type=PublicIdParameter(), required=True)
@click.pass_context
def contract(click_context, contract_public_id: PublicId):
    """Add a contract to the configuration file."""
    _add_item(click_context, "contract", contract_public_id)


@add.command()
@click.argument("protocol_public_id", type=PublicIdParameter(), required=True)
@click.pass_context
def protocol(click_context, protocol_public_id):
    """Add a protocol to the agent."""
    _add_item(click_context, "protocol", protocol_public_id)


@add.command()
@click.argument("skill_public_id", type=PublicIdParameter(), required=True)
@click.pass_context
def skill(click_context, skill_public_id: PublicId):
    """Add a skill to the agent."""
    _add_item(click_context, "skill", skill_public_id)
