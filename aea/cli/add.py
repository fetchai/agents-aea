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

from pathlib import Path
from typing import Collection, cast

import click
from click.core import Context as ClickContext

from aea.cli.registry.utils import fetch_package
from aea.cli.utils.click_utils import PublicIdParameter
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project, clean_after
from aea.cli.utils.loggers import logger
from aea.cli.utils.package_utils import (
    copy_package_directory,
    find_item_in_distribution,
    find_item_locally,
    get_package_dest_path,
    is_fingerprint_correct,
    is_item_present,
    register_item,
)
from aea.configurations.base import (
    PackageType,
    PublicId,
    _get_default_configuration_file_name_from_type,
)
from aea.configurations.constants import (
    DEFAULT_CONNECTION,
    DEFAULT_PROTOCOL,
    DEFAULT_SKILL,
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


@clean_after
def _add_item(
    click_context: ClickContext, item_type: str, item_public_id: PublicId
) -> None:
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

    dest_path = get_package_dest_path(
        ctx, item_public_id.author, item_type_plural, item_public_id.name
    )
    is_local = ctx.config.get("is_local")

    ctx.clean_paths.append(dest_path)
    if item_public_id in [DEFAULT_CONNECTION, DEFAULT_PROTOCOL, DEFAULT_SKILL]:
        source_path = find_item_in_distribution(ctx, item_type, item_public_id)
        package_path = copy_package_directory(
            ctx,
            source_path,
            item_type,
            item_public_id.name,
            item_public_id.author,
            dest_path,
        )
    elif is_local:
        source_path = find_item_locally(ctx, item_type, item_public_id)
        package_path = copy_package_directory(
            ctx,
            source_path,
            item_type,
            item_public_id.name,
            item_public_id.author,
            dest_path,
        )
    else:
        package_path = fetch_package(
            item_type, public_id=item_public_id, cwd=ctx.cwd, dest=dest_path
        )

    item_config = _load_item_config(item_type, package_path)

    if not is_fingerprint_correct(package_path, item_config):
        raise click.ClickException("Failed to add an item with incorrect fingerprint.")

    _add_item_deps(click_context, item_type, item_config)
    register_item(ctx, item_type, item_public_id)


def _add_protocols(
    click_context: ClickContext, protocols: Collection[PublicId]
) -> None:
    """
    Add protocols to AEA by list of public IDs.

    :param click_context: click context object.
    :param protocols: a Collection of protocol public IDs to be added.

    :return: None
    """
    ctx = cast(Context, click_context.obj)
    for protocol_public_id in protocols:
        if protocol_public_id not in ctx.agent_config.protocols:
            logger.debug(
                "Adding protocol '{}' to the agent...".format(protocol_public_id)
            )
            _add_item(click_context, "protocol", protocol_public_id)


def _load_item_config(item_type: str, package_path: Path) -> ConfigLoader:
    """
    Load item configuration.

    :param item_type: type of item.
    :param package_path: path to package from which config should be loaded.

    :return: configuration object.
    """
    configuration_file_name = _get_default_configuration_file_name_from_type(item_type)
    configuration_path = package_path / configuration_file_name
    configuration_loader = ConfigLoader.from_configuration_type(PackageType(item_type))
    item_config = configuration_loader.load(configuration_path.open())
    return item_config


def _add_item_deps(click_context: ClickContext, item_type: str, item_config) -> None:
    """
    Add item dependencies. Calls _add_item recursively.

    :param click_context: click context object.
    :param item_type: type of item.
    :param item_config: item configuration object.

    :return: None
    """
    if item_type in {"connection", "skill"}:
        _add_protocols(click_context, item_config.protocols)

    if item_type == "skill":
        for contract_public_id in item_config.contracts:
            _add_item(click_context, "contract", contract_public_id)
