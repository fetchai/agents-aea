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

from typing import cast

import click

from aea.cli.registry.add import fetch_package
from aea.cli.utils.click_utils import PublicIdParameter
from aea.cli.utils.config import load_item_config
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project, clean_after, pass_ctx
from aea.cli.utils.package_utils import (
    copy_package_directory,
    find_item_in_distribution,
    find_item_locally,
    get_package_path,
    is_fingerprint_correct,
    is_item_present,
    register_item,
)
from aea.configurations.base import PublicId
from aea.configurations.constants import (
    DEFAULT_CONNECTION,
    DEFAULT_SKILL,
    LOCAL_PROTOCOLS,
)


@click.group()
@click.option("--local", is_flag=True, help="For adding from local folder.")
@click.pass_context
@check_aea_project
def add(click_context, local):
    """Add a resource to the agent."""
    ctx = cast(Context, click_context.obj)
    if local:
        ctx.set_config("is_local", True)


@add.command()
@click.argument("connection_public_id", type=PublicIdParameter(), required=True)
@pass_ctx
def connection(ctx: Context, connection_public_id: PublicId):
    """Add a connection to the configuration file."""
    add_item(ctx, "connection", connection_public_id)


@add.command()
@click.argument("contract_public_id", type=PublicIdParameter(), required=True)
@pass_ctx
def contract(ctx: Context, contract_public_id: PublicId):
    """Add a contract to the configuration file."""
    add_item(ctx, "contract", contract_public_id)


@add.command()
@click.argument("protocol_public_id", type=PublicIdParameter(), required=True)
@pass_ctx
def protocol(ctx: Context, protocol_public_id):
    """Add a protocol to the agent."""
    add_item(ctx, "protocol", protocol_public_id)


@add.command()
@click.argument("skill_public_id", type=PublicIdParameter(), required=True)
@pass_ctx
def skill(ctx: Context, skill_public_id: PublicId):
    """Add a skill to the agent."""
    add_item(ctx, "skill", skill_public_id)


@clean_after
def add_item(ctx: Context, item_type: str, item_public_id: PublicId) -> None:
    """
    Add an item.

    :param ctx: Context object.
    :param item_type: the item type.
    :param item_public_id: the item public id.
    :return: None
    """
    agent_name = cast(str, ctx.agent_config.agent_name)

    click.echo(
        "Adding {} '{}' to the agent '{}'...".format(
            item_type, item_public_id, agent_name
        )
    )
    if is_item_present(ctx, item_type, item_public_id):
        raise click.ClickException(
            "A {} with id '{}/{}' already exists. Aborting...".format(
                item_type, item_public_id.author, item_public_id.name
            )
        )

    dest_path = get_package_path(ctx, item_type, item_public_id)
    is_local = ctx.config.get("is_local")

    ctx.clean_paths.append(dest_path)
    if item_public_id in [DEFAULT_CONNECTION, *LOCAL_PROTOCOLS, DEFAULT_SKILL]:
        source_path = find_item_in_distribution(ctx, item_type, item_public_id)
        package_path = copy_package_directory(source_path, dest_path)
    elif is_local:
        source_path = find_item_locally(ctx, item_type, item_public_id)
        package_path = copy_package_directory(source_path, dest_path)
    else:
        package_path = fetch_package(
            item_type, public_id=item_public_id, cwd=ctx.cwd, dest=dest_path
        )
    item_config = load_item_config(item_type, package_path)

    if not is_fingerprint_correct(package_path, item_config):  # pragma: no cover
        raise click.ClickException("Failed to add an item with incorrect fingerprint.")

    _add_item_deps(ctx, item_type, item_config)
    register_item(ctx, item_type, item_public_id)


def _add_item_deps(ctx: Context, item_type: str, item_config) -> None:
    """
    Add item dependencies. Calls add_item recursively.

    :param ctx: Context object.
    :param item_type: type of item.
    :param item_config: item configuration object.

    :return: None
    """
    if item_type in {"connection", "skill"}:
        # add missing protocols
        for protocol_public_id in item_config.protocols:
            if protocol_public_id not in ctx.agent_config.protocols:
                add_item(ctx, "protocol", protocol_public_id)

    if item_type == "skill":
        # add missing contracts
        for contract_public_id in item_config.contracts:
            if contract_public_id not in ctx.agent_config.contracts:
                add_item(ctx, "contract", contract_public_id)

        # add missing skill
        for skill_public_id in item_config.skills:
            if skill_public_id not in ctx.agent_config.skills:
                add_item(ctx, "skill", skill_public_id)
