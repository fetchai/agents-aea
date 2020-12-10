# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2020 Fetch.AI Limited
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

"""Implementation of the 'aea add_key' subcommand."""

import os
from typing import Optional, cast

import click

from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project
from aea.configurations.constants import (
    DEFAULT_AEA_CONFIG_FILE,
    PRIVATE_KEY_PATH_SCHEMA,
)
from aea.crypto.helpers import try_validate_private_key_path
from aea.crypto.registries import crypto_registry


@click.command()
@click.argument(
    "type_",
    metavar="TYPE",
    type=click.Choice(list(crypto_registry.supported_ids)),
    required=True,
)
@click.argument(
    "file",
    metavar="FILE",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=False,
)
@click.option(
    "--connection", is_flag=True, help="For adding a private key for connections."
)
@click.pass_context
@check_aea_project
def add_key(click_context, type_, file, connection):
    """Add a private key to the wallet of the agent."""
    _add_private_key(click_context, type_, file, connection)


def _add_private_key(
    click_context: click.core.Context,
    type_: str,
    file: Optional[str] = None,
    connection: bool = False,
) -> None:
    """
    Add private key to the wallet.

    :param click_context: click context object.
    :param type_: type.
    :param file: path to file.
    :param connection: whether or not it is a private key for a connection

    :return: None
    """
    ctx = cast(Context, click_context.obj)
    if file is None:
        file = PRIVATE_KEY_PATH_SCHEMA.format(type_)
    try_validate_private_key_path(type_, file)
    _try_add_key(ctx, type_, file, connection)


def _try_add_key(ctx: Context, type_: str, filepath: str, connection: bool = False):
    try:
        if connection:
            ctx.agent_config.connection_private_key_paths.create(type_, filepath)
        else:
            ctx.agent_config.private_key_paths.create(type_, filepath)
    except ValueError as e:  # pragma: no cover
        raise click.ClickException(str(e))
    ctx.agent_loader.dump(
        ctx.agent_config, open(os.path.join(ctx.cwd, DEFAULT_AEA_CONFIG_FILE), "w")
    )
