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
from typing import cast

import click

from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project
from aea.configurations.base import DEFAULT_AEA_CONFIG_FILE
from aea.crypto.helpers import try_validate_private_key_path
from aea.crypto.registry import registry


@click.command()
@click.argument(
    "type_",
    metavar="TYPE",
    type=click.Choice(list(registry.supported_crypto_ids)),
    required=True,
)
@click.argument(
    "file",
    metavar="FILE",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, readable=True),
    required=True,
)
@click.pass_context
@check_aea_project
def add_key(click_context, type_, file):
    """Add a private key to the wallet."""
    _add_private_key(click_context, type_, file)


def _add_private_key(click_context: click.core.Context, type_: str, file: str) -> None:
    """
    Add private key to the wallet.

    :param click_context: click context object.
    :param:

    :return: None
    """
    ctx = cast(Context, click_context.obj)
    try_validate_private_key_path(type_, file)
    _try_add_key(ctx, type_, file)


def _try_add_key(ctx, type_, filepath):
    try:
        ctx.agent_config.private_key_paths.create(type_, filepath)
    except ValueError as e:  # pragma: no cover
        raise click.ClickException(str(e))
    ctx.agent_loader.dump(
        ctx.agent_config, open(os.path.join(ctx.cwd, DEFAULT_AEA_CONFIG_FILE), "w")
    )
