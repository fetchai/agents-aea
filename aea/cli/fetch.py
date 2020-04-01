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

"""Implementation of the 'aea fetch' subcommand."""

import os
from distutils.dir_util import copy_tree
from typing import cast

import click

from aea.cli.add import _add_item
from aea.cli.common import (
    Context,
    DEFAULT_REGISTRY_PATH,
    PublicIdParameter,
    _try_get_item_source_path,
    try_to_load_agent_config,
)
from aea.cli.registry.fetch import fetch_agent
from aea.configurations.base import PublicId


@click.command(name="fetch")
@click.option("--local", is_flag=True, help="For fetching agent from local folder.")
@click.argument("public-id", type=PublicIdParameter(), required=True)
@click.pass_context
def fetch(click_context, public_id, local):
    """Fetch Agent from Registry."""
    ctx = cast(Context, click_context.obj)
    if local:
        ctx.set_config("is_local", True)
        _fetch_agent_locally(ctx, public_id, click_context)
    else:
        fetch_agent(ctx, public_id)


def _fetch_agent_locally(ctx: Context, public_id: PublicId, click_context) -> None:
    """
    Fetch Agent from local packages.

    :param ctx: Context
    :param public_id: public ID of agent to be fetched.

    :return: None
    """
    packages_path = os.path.basename(DEFAULT_REGISTRY_PATH)
    source_path = _try_get_item_source_path(
        packages_path, public_id.author, "agents", public_id.name
    )
    target_path = os.path.join(ctx.cwd, public_id.name)
    if os.path.exists(target_path):
        raise click.ClickException(
            'Item "{}" already exists in target folder.'.format(public_id.name)
        )
    copy_tree(source_path, target_path)

    # add dependencies
    ctx.cwd = target_path
    try_to_load_agent_config(ctx)

    for item_type in ("skill", "connection", "contract", "protocol"):
        item_type_plural = "{}s".format(item_type)
        required_items = getattr(ctx.agent_config, item_type_plural)
        for item_id in required_items:
            try:
                _add_item(click_context, item_type, item_id)
                # if item_type_plural == "connections":
                #     click_context.invoke(
                #         add_connection_command, connection_public_id=item_id
                #     )
                # elif item_type_plural == "contracts":
                #     click_context.invoke(
                #         add_contract_command, contract_public_id=item_id
                #     )
                # elif item_type_plural == "protocols":
                #     click_context.invoke(
                #         add_protocol_command, protocol_public_id=item_id
                #     )
                # elif item_type_plural == "skills":
                #     click_context.invoke(add_skill_command, skill_public_id=item_id)
            except SystemExit:
                continue
    click.echo("Agent {} successfully fetched.".format(public_id.name))
