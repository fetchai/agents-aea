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

import os
from shutil import copytree

import click

from aea.cli.common import (
    Context,
    PublicIdParameter,
    pass_ctx,
    try_get_item_source_path,
    try_get_item_target_path,
    try_to_load_agent_config,
)
from aea.cli.registry.push import push_item
from aea.cli.registry.utils import load_yaml
from aea.configurations.base import PublicId


@click.group()
@click.option("--registry", is_flag=True, help="For pushing items to Registry.")
@pass_ctx
def push(ctx: Context, registry):
    """Push item to Registry or save it in local packages."""
    try_to_load_agent_config(ctx)
    ctx.set_config("registry", registry)


@push.command(name="connection")
@click.argument("connection-id", type=PublicIdParameter(), required=True)
@pass_ctx
def connection(ctx: Context, connection_id):
    """Push connection to Registry or save it in local packages."""
    if not ctx.config.get("registry"):
        _save_item_locally(ctx, "connection", connection_id)
    else:
        push_item(ctx, "connection", connection_id)


@push.command(name="protocol")
@click.argument("protocol-id", type=PublicIdParameter(), required=True)
@pass_ctx
def protocol(ctx: Context, protocol_id):
    """Push protocol to Registry or save it in local packages."""
    if not ctx.config.get("registry"):
        _save_item_locally(ctx, "protocol", protocol_id)
    else:
        push_item(ctx, "protocol", protocol_id)


@push.command(name="skill")
@click.argument("skill-id", type=PublicIdParameter(), required=True)
@pass_ctx
def skill(ctx: Context, skill_id):
    """Push skill to Registry or save it in local packages."""
    if not ctx.config.get("registry"):
        _save_item_locally(ctx, "skill", skill_id)
    else:
        push_item(ctx, "skill", skill_id)


def _save_item_locally(ctx: Context, item_type: str, item_id: PublicId) -> None:
    """
    Save item to local packages.

    :param item_type: str type of item (connection/protocol/skill).
    :param item_id: the public id of the item.
    :return: None
    """
    item_type_plural = item_type + "s"

    source_path = try_get_item_source_path(ctx.cwd, item_id.author, item_type_plural, item_id.name)
    target_path = try_get_item_target_path(
        ctx.agent_config.registry_path, item_type_plural, item_id.name
    )
    _check_package_public_id(source_path, item_type, item_id)
    copytree(source_path, target_path)
    click.echo(
        '{} "{}" successfully saved in packages folder.'.format(
            item_type.title(), item_id
        )
    )


def _check_package_public_id(source_path, item_type, item_id) -> None:
    # we load only based on item_name, hence also check item_version and item_author match.
    config = load_yaml(os.path.join(source_path, item_type + ".yaml"))
    item_author = config.get("author", "")
    item_name = config.get("name", "")
    item_version = config.get("version", "")
    if (
        item_id.name != item_name
        or item_id.author != item_author
        or item_id.version != item_version
    ):
        raise click.ClickException(
            "Version or author do not match. Expected '{}', found '{}'".format(
                item_id, item_author + "/" + item_name + ":" + item_version
            )
        )
