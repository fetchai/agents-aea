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

from typing import cast

import click

from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project
from aea.cli.utils.package_utils import verify_or_create_private_keys
from aea.crypto.registries import crypto_registry
from aea.crypto.wallet import Wallet


@click.command()
@click.argument(
    "type_",
    metavar="TYPE",
    type=click.Choice(list(crypto_registry.supported_ids)),
    required=True,
)
@click.pass_context
@check_aea_project
def get_address(click_context, type_):
    """Get the address associated with the private key."""
    address = _try_get_address(click_context, type_)
    click.echo(address)


def _try_get_address(click_context, type_):
    """
    Try to get address.

    :param click_context: click context object.
    :param type_: type.

    :return: address.
    """
    ctx = cast(Context, click_context.obj)
    verify_or_create_private_keys(ctx)

    private_key_paths = {
        config_pair[0]: config_pair[1]
        for config_pair in ctx.agent_config.private_key_paths.read_all()
    }
    try:
        wallet = Wallet(private_key_paths)
        address = wallet.addresses[type_]
        return address
    except ValueError as e:  # pragma: no cover
        raise click.ClickException(str(e))
