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

"""Implementation of the 'aea push' subcommand."""

from shutil import copytree
from typing import cast

import click

from aea.cli.registry.push import check_package_public_id, push_item
from aea.cli.utils.click_utils import PublicIdParameter
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project, pass_ctx
from aea.cli.utils.package_utils import (
    try_get_item_source_path,
    try_get_item_target_path,
)
from aea.configurations.base import PublicId
from aea.configurations.constants import CONNECTION, CONTRACT, PROTOCOL, SKILL


@click.group()
@click.option("--local", is_flag=True, help="For pushing items to local folder.")
@click.pass_context
@check_aea_project
def push(click_context, local):
    """Push a non-vendor package of the agent to the registry."""
    ctx = cast(Context, click_context.obj)
    ctx.set_config("local", local)


@push.command(name=CONNECTION)
@click.argument("connection-id", type=PublicIdParameter(), required=True)
@pass_ctx
def connection(ctx: Context, connection_id):
    """Push a connection to the registry or save it in local registry."""
    if ctx.config.get("local"):
        _save_item_locally(ctx, CONNECTION, connection_id)
    else:
        push_item(ctx, CONNECTION, connection_id)


@push.command(name=CONTRACT)
@click.argument("contract-id", type=PublicIdParameter(), required=True)
@pass_ctx
def contract(ctx: Context, contract_id):
    """Push a contract to the registry or save it in local registry."""
    if ctx.config.get("local"):
        _save_item_locally(ctx, CONTRACT, contract_id)
    else:
        push_item(ctx, CONTRACT, contract_id)


@push.command(name=PROTOCOL)
@click.argument("protocol-id", type=PublicIdParameter(), required=True)
@pass_ctx
def protocol(ctx: Context, protocol_id):
    """Push a protocol to the registry or save it in local registry."""
    if ctx.config.get("local"):
        _save_item_locally(ctx, PROTOCOL, protocol_id)
    else:
        push_item(ctx, PROTOCOL, protocol_id)


@push.command(name=SKILL)
@click.argument("skill-id", type=PublicIdParameter(), required=True)
@pass_ctx
def skill(ctx: Context, skill_id):
    """Push a skill to the registry or save it in local registry."""
    if ctx.config.get("local"):
        _save_item_locally(ctx, SKILL, skill_id)
    else:
        push_item(ctx, SKILL, skill_id)


def _save_item_locally(ctx: Context, item_type: str, item_id: PublicId) -> None:
    """
    Save item to local packages.

    :param item_type: str type of item (connection/protocol/skill).
    :param item_id: the public id of the item.
    :return: None
    """
    item_type_plural = item_type + "s"

    source_path = try_get_item_source_path(
        ctx.cwd, None, item_type_plural, item_id.name
    )

    check_package_public_id(source_path, item_type, item_id)

    target_path = try_get_item_target_path(
        ctx.agent_config.registry_path,
        ctx.agent_config.author,
        item_type_plural,
        item_id.name,
    )
    copytree(source_path, target_path)
    click.echo(
        f'{item_type.title()} "{item_id}" successfully saved in packages folder.'
    )
