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
from typing import Union, cast

import click

from aea.cli.registry.add import fetch_package
from aea.cli.utils.click_utils import PublicIdParameter, registry_flag
from aea.cli.utils.config import load_item_config
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project, clean_after, pass_ctx
from aea.cli.utils.loggers import logger
from aea.cli.utils.package_utils import (
    copy_package_directory,
    find_item_in_distribution,
    find_item_locally,
    get_item_id_present,
    get_package_path,
    is_distributed_item,
    is_fingerprint_correct,
    is_item_present,
    register_item,
)
from aea.configurations.base import (
    ConnectionConfig,
    PackageConfiguration,
    PublicId,
    SkillConfig,
)
from aea.configurations.constants import CONNECTION, CONTRACT, PROTOCOL, SKILL
from aea.exceptions import enforce


@click.group()
@registry_flag()
@click.pass_context
@check_aea_project
def add(click_context: click.Context, local: bool, remote: bool) -> None:
    """Add a package to the agent."""
    ctx = cast(Context, click_context.obj)
    enforce(
        not (local and remote), "'local' and 'remote' options are mutually exclusive."
    )
    if not local and not remote:
        try:
            ctx.registry_path
        except ValueError as e:
            click.echo(f"{e}\nTrying remote registry (`--remote`).")
            remote = True
    is_mixed = not local and not remote
    ctx.set_config("is_local", local and not remote)
    ctx.set_config("is_mixed", is_mixed)


@add.command()
@click.argument("connection_public_id", type=PublicIdParameter(), required=True)
@pass_ctx
def connection(ctx: Context, connection_public_id: PublicId) -> None:
    """Add a connection to the agent."""
    add_item(ctx, CONNECTION, connection_public_id)


@add.command()
@click.argument("contract_public_id", type=PublicIdParameter(), required=True)
@pass_ctx
def contract(ctx: Context, contract_public_id: PublicId) -> None:
    """Add a contract to the agent."""
    add_item(ctx, CONTRACT, contract_public_id)


@add.command()
@click.argument("protocol_public_id", type=PublicIdParameter(), required=True)
@pass_ctx
def protocol(ctx: Context, protocol_public_id: PublicId) -> None:
    """Add a protocol to the agent."""
    add_item(ctx, PROTOCOL, protocol_public_id)


@add.command()
@click.argument("skill_public_id", type=PublicIdParameter(), required=True)
@pass_ctx
def skill(ctx: Context, skill_public_id: PublicId) -> None:
    """Add a skill to the agent."""
    add_item(ctx, SKILL, skill_public_id)


@clean_after
def add_item(ctx: Context, item_type: str, item_public_id: PublicId) -> None:
    """
    Add an item.

    :param ctx: Context object.
    :param item_type: the item type.
    :param item_public_id: the item public id.
    """
    click.echo(f"Adding {item_type} '{item_public_id}'...")
    if is_item_present(ctx.cwd, ctx.agent_config, item_type, item_public_id):
        present_item_id = get_item_id_present(
            ctx.agent_config, item_type, item_public_id
        )
        raise click.ClickException(
            "A {} with id '{}' already exists. Aborting...".format(
                item_type, present_item_id
            )
        )

    dest_path = get_package_path(ctx.cwd, item_type, item_public_id)
    is_local = ctx.config.get("is_local")
    is_mixed = ctx.config.get("is_mixed")

    ctx.clean_paths.append(dest_path)

    if is_mixed:
        package_path = fetch_item_mixed(ctx, item_type, item_public_id, dest_path)
    elif is_local:
        package_path = find_item_locally_or_distributed(
            ctx, item_type, item_public_id, dest_path
        )
    else:
        package_path = fetch_package(
            item_type, public_id=item_public_id, cwd=ctx.cwd, dest=dest_path
        )
    item_config = load_item_config(item_type, package_path)

    if not ctx.config.get("skip_consistency_check") and not is_fingerprint_correct(
        package_path, item_config
    ):  # pragma: no cover
        raise click.ClickException("Failed to add an item with incorrect fingerprint.")

    _add_item_deps(ctx, item_type, item_config)
    register_item(ctx, item_type, item_config.public_id)
    click.echo(f"Successfully added {item_type} '{item_config.public_id}'.")


def _add_item_deps(
    ctx: Context, item_type: str, item_config: PackageConfiguration
) -> None:
    """
    Add item dependencies. Calls add_item recursively.

    :param ctx: Context object.
    :param item_type: type of item.
    :param item_config: item configuration object.
    """
    if item_type in {CONNECTION, SKILL}:
        item_config = cast(Union[SkillConfig, ConnectionConfig], item_config)
        # add missing protocols
        for protocol_public_id in item_config.protocols:
            if protocol_public_id not in ctx.agent_config.protocols:
                add_item(ctx, PROTOCOL, protocol_public_id)

    if item_type == SKILL:
        item_config = cast(SkillConfig, item_config)
        # add missing contracts
        for contract_public_id in item_config.contracts:
            if contract_public_id not in ctx.agent_config.contracts:
                add_item(ctx, CONTRACT, contract_public_id)

        # add missing connections
        for connection_public_id in item_config.connections:
            if connection_public_id not in ctx.agent_config.connections:
                add_item(ctx, CONNECTION, connection_public_id)

        # add missing skill
        for skill_public_id in item_config.skills:
            if skill_public_id not in ctx.agent_config.skills:
                add_item(ctx, SKILL, skill_public_id)


def find_item_locally_or_distributed(
    ctx: Context, item_type: str, item_public_id: PublicId, dest_path: str
) -> Path:
    """
    Unify find item locally both in case it is distributed or not.

    :param ctx: the CLI context.
    :param item_type: the item type.
    :param item_public_id: the item public id.
    :param dest_path: the path to the destination.
    :return: the path to the found package.
    """
    is_distributed = is_distributed_item(item_public_id)
    if is_distributed:  # pragma: nocover
        source_path = find_item_in_distribution(ctx, item_type, item_public_id)
        package_path = copy_package_directory(source_path, dest_path)
    else:
        source_path, _ = find_item_locally(ctx, item_type, item_public_id)
        package_path = copy_package_directory(source_path, dest_path)

    return package_path


def fetch_item_mixed(
    ctx: Context, item_type: str, item_public_id: PublicId, dest_path: str,
) -> Path:
    """
    Find item, mixed mode.

    That is, give priority to local registry, and fall back to remote registry
    in case of failure.

    :param ctx: the CLI context.
    :param item_type: the item type.
    :param item_public_id: the item public id.
    :param dest_path: the path to the destination.
    :return: the path to the found package.
    """
    try:
        package_path = find_item_locally_or_distributed(
            ctx, item_type, item_public_id, dest_path
        )
    except click.ClickException as e:
        logger.debug(
            f"Fetch from local registry failed (reason={str(e)}), trying remote registry..."
        )
        # the following might raise exception, but we don't catch it this time
        package_path = fetch_package(
            item_type, public_id=item_public_id, cwd=ctx.cwd, dest=dest_path
        )
    return package_path
