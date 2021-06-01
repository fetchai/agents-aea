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


"""Implementation of the 'aea get_address' subcommand."""
from typing import Optional, cast

import click

from aea.cli.utils.click_utils import password_option
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project
from aea.cli.utils.package_utils import get_wallet_from_context
from aea.crypto.registries import crypto_registry


@click.command()
@click.argument(
    "type_",
    metavar="TYPE",
    type=click.Choice(list(crypto_registry.supported_ids)),
    required=True,
)
@password_option()
@click.pass_context
@check_aea_project
def get_address(
    click_context: click.Context, type_: str, password: Optional[str]
) -> None:
    """Get the address associated with a private key of the agent."""
    ctx = cast(Context, click_context.obj)
    address = _try_get_address(ctx, type_, password)
    click.echo(address)


def _try_get_address(ctx: Context, type_: str, password: Optional[str] = None) -> str:
    """
    Try to get address.

    :param ctx: click context object.
    :param type_: type.
    :param password: the password to encrypt/decrypt the private key.

    :return: address.
    """
    wallet = get_wallet_from_context(ctx, password=password)
    try:
        address = wallet.addresses[type_]
        return address
    except ValueError as e:  # pragma: no cover
        raise click.ClickException(str(e))
