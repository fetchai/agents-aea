# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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

"""Implementation of the 'aea remove_key' subcommand."""

import os
from typing import cast

import click

from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project
from aea.configurations.constants import DEFAULT_AEA_CONFIG_FILE
from aea.crypto.registries import crypto_registry
from aea.helpers.io import open_file


@click.command()
@click.argument(
    "type_",
    metavar="TYPE",
    type=click.Choice(list(crypto_registry.supported_ids)),
    required=True,
)
@click.option(
    "--connection", is_flag=True, help="For removing a private key for connections."
)
@click.pass_context
@check_aea_project
def remove_key(click_context: click.Context, type_: str, connection: bool) -> None:
    """Remove a private key from the wallet of the agent."""
    _remove_private_key(click_context, type_, connection)


def _remove_private_key(
    click_context: click.core.Context,
    type_: str,
    connection: bool = False,
) -> None:
    """
    Remove private key to the wallet.

    :param click_context: click context object.
    :param type_: type.
    :param connection: whether or not it is a private key for a connection
    """
    ctx = cast(Context, click_context.obj)
    _try_remove_key(ctx, type_, connection)


def _try_remove_key(ctx: Context, type_: str, connection: bool = False) -> None:
    private_keys = (
        ctx.agent_config.connection_private_key_paths
        if connection
        else ctx.agent_config.private_key_paths
    )
    existing_keys = private_keys.keys()
    if type_ not in existing_keys:
        raise click.ClickException(
            f"There is no {'connection ' if connection else ''}key registered with id {type_}."
        )
    private_keys.delete(type_)
    ctx.agent_loader.dump(
        ctx.agent_config, open_file(os.path.join(ctx.cwd, DEFAULT_AEA_CONFIG_FILE), "w")
    )
