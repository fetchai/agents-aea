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
"""Implementation of the 'aea upgrade' subcommand."""

from typing import cast

import click

from aea.cli.add import add_item
from aea.cli.registry.add import _get_package_meta
from aea.cli.remove import remove_item
from aea.cli.utils.click_utils import PublicIdParameter
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project, clean_after, pass_ctx
from aea.cli.utils.package_utils import (
    find_item_locally,
    get_item_public_id_by_author_name,
    get_items,
    is_item_present,
)
from aea.configurations.base import PublicId


@click.group(invoke_without_command=True)
@click.option("--local", is_flag=True, help="For upgrading from local folder.")
@click.pass_context
@check_aea_project
def upgrade(click_context, local):
    """Upgrade agent's component."""
    ctx = cast(Context, click_context.obj)
    if local:
        ctx.set_config("is_local", True)

    if click_context.invoked_subcommand is None:
        upgrade_project(ctx)


@upgrade.command()
@click.argument("connection_public_id", type=PublicIdParameter(), required=True)
@pass_ctx
def connection(ctx: Context, connection_public_id: PublicId):
    """Upgrade a connection at the configuration file."""
    upgrade_item(ctx, "connection", connection_public_id)


@upgrade.command()
@click.argument("contract_public_id", type=PublicIdParameter(), required=True)
@pass_ctx
def contract(ctx: Context, contract_public_id: PublicId):
    """Upgrade a contract at the configuration file."""
    upgrade_item(ctx, "contract", contract_public_id)


@upgrade.command()
@click.argument("protocol_public_id", type=PublicIdParameter(), required=True)
@pass_ctx
def protocol(ctx: Context, protocol_public_id):
    """Upgrade a protocol for the agent."""
    upgrade_item(ctx, "protocol", protocol_public_id)


@upgrade.command()
@click.argument("skill_public_id", type=PublicIdParameter(), required=True)
@pass_ctx
def skill(ctx: Context, skill_public_id: PublicId):
    """Upgrade a skill for the agent."""
    upgrade_item(ctx, "skill", skill_public_id)


@clean_after
def upgrade_project(ctx: Context) -> None:  # pylint: disable=unused-argument
    """Perform project upgrade."""
    click.echo("Upgrade project is not ready yet")


@clean_after
def upgrade_item(ctx: Context, item_type: str, item_public_id: PublicId) -> None:
    """
    Upgrade an item.

    :param ctx: Context object.
    :param item_type: the item type.
    :param item_public_id: the item public id.
    :return: None
    """
    agent_name = cast(str, ctx.agent_config.agent_name)
    if not _check_upgrade_is_required(ctx, item_type, item_public_id):
        raise click.ClickException(
            f"Item {item_type} {item_public_id.author}/{item_public_id.name} can not be updated. Aborting..."
        )

    click.echo(
        "Upgrading {} to '{}' for the agent '{}'...".format(
            item_type, item_public_id, agent_name
        )
    )

    remove_item(ctx, item_type, item_public_id)
    add_item(ctx, item_type, item_public_id)
    click.echo("{} for the agent '{}' upgraded".format(item_public_id, agent_name))


def _check_upgrade_is_required(ctx: Context, item_type: str, item_public_id: PublicId):
    """
    Check item can be upgraded or not.

    :param ctx: Context object.
    :param item_type: the item type.
    :param item_public_id: the item public id.
    :return: None
    """
    registered_item_ids = get_items(ctx.agent_config, item_type)

    def is_item_with_version_present(public_id: PublicId) -> bool:
        if public_id.version == "latest":
            return False
        return public_id in registered_item_ids

    if not is_item_present(ctx, item_type, item_public_id):
        raise click.ClickException(
            "Error: A {} with id '{}/{}' is not registered. Please use `add` command. Aborting...".format(
                item_type, item_public_id.author, item_public_id.name
            ),
        )

    if is_item_with_version_present(item_public_id):
        click.echo(
            "A {} with id '{}/{}' already has version {}. Nothing to upgrade.".format(
                item_type,
                item_public_id.author,
                item_public_id.name,
                item_public_id.version,
            ),
        )
        return False

    current_item_public_id = get_item_public_id_by_author_name(
        ctx.agent_config, item_type, item_public_id.author, item_public_id.name
    )

    if (
        current_item_public_id is None
    ):  # pragma: nocover. already checked above, need for mypy only
        raise click.ClickException(f"Item {item_public_id} is not registered!")

    if item_public_id.version == "latest":
        item_public_id = _get_latest_version(ctx, item_type, item_public_id)

        if is_item_with_version_present(item_public_id):
            click.echo(
                "A {} with id '{}/{}' already has the latest version {}. Nothing to upgrade.".format(
                    item_type,
                    item_public_id.author,
                    item_public_id.name,
                    item_public_id.version,
                )
            )
            return False

    return True


def _get_latest_version(
    ctx: Context, item_type: str, item_public_id: PublicId
) -> PublicId:
    """
    Get latest avalable package version public id.

    :param ctx: Context object.
    :param item_type: the item type.
    :param item_public_id: the item public id.
    :return: PublicId
    """
    is_local = ctx.config.get("is_local")
    try:
        if is_local:
            _, item_config = find_item_locally(ctx, item_type, item_public_id)
            latest_item_public_id = item_config.public_id
        else:
            package_meta = _get_package_meta(item_type, item_public_id)
            latest_item_public_id = PublicId.from_str(package_meta["public_id"])
    except Exception:  # pylint: disable=broad-except
        raise click.ClickException(
            f"Package {item_public_id} details can not be fetched from the registry!"
        )

    return latest_item_public_id
