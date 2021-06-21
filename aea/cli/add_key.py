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

from aea.cli.utils.click_utils import password_option
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project
from aea.configurations.constants import (
    DEFAULT_AEA_CONFIG_FILE,
    PRIVATE_KEY_PATH_SCHEMA,
)
from aea.crypto.helpers import try_validate_private_key_path
from aea.crypto.registries import crypto_registry
from aea.helpers.io import open_file


key_file_argument = click.Path(
    exists=True, file_okay=True, dir_okay=False, readable=True
)


@click.command()
@click.argument(
    "type_",
    metavar="TYPE",
    type=click.Choice(list(crypto_registry.supported_ids)),
    required=True,
)
@click.argument(
    "file", metavar="FILE", type=key_file_argument, required=False,
)
@password_option()
@click.option(
    "--connection", is_flag=True, help="For adding a private key for connections."
)
@click.pass_context
@check_aea_project
def add_key(
    click_context: click.Context,
    type_: str,
    file: str,
    password: Optional[str],
    connection: bool,
) -> None:
    """Add a private key to the wallet of the agent."""
    _add_private_key(click_context, type_, file, password, connection)


def _add_private_key(
    click_context: click.core.Context,
    type_: str,
    file: Optional[str] = None,
    password: Optional[str] = None,
    connection: bool = False,
) -> None:
    """
    Add private key to the wallet.

    :param click_context: click context object.
    :param type_: type.
    :param file: path to file.
    :param connection: whether or not it is a private key for a connection.
    :param password: the password to encrypt/decrypt the private key.
    """
    ctx = cast(Context, click_context.obj)
    if file is None:
        file = PRIVATE_KEY_PATH_SCHEMA.format(type_)

    key_file_argument.convert(file, None, click_context)
    try:
        try_validate_private_key_path(type_, file, password=password)
    except Exception as e:
        raise click.ClickException(repr(e)) from e
    _try_add_key(ctx, type_, file, connection)


def _try_add_key(
    ctx: Context, type_: str, filepath: str, connection: bool = False
) -> None:
    try:
        if connection:
            ctx.agent_config.connection_private_key_paths.create(type_, filepath)
        else:
            ctx.agent_config.private_key_paths.create(type_, filepath)
    except ValueError as e:  # pragma: no cover
        raise click.ClickException(str(e))
    with open_file(os.path.join(ctx.cwd, DEFAULT_AEA_CONFIG_FILE), "w") as fp:
        ctx.agent_loader.dump(ctx.agent_config, fp)
