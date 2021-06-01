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
"""Implementation of the 'aea generate_wealth' subcommand."""
from typing import Optional, cast

import click

from aea.cli.utils.click_utils import password_option
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project
from aea.cli.utils.package_utils import get_wallet_from_context
from aea.crypto.helpers import try_generate_testnet_wealth
from aea.crypto.registries import faucet_apis_registry, make_faucet_api_cls


@click.command()
@click.argument(
    "type_",
    metavar="TYPE",
    type=click.Choice(list(faucet_apis_registry.supported_ids)),
    required=True,
)
@click.argument("url", metavar="URL", type=str, required=False, default=None)
@password_option()
@click.option(
    "--sync", is_flag=True, help="For waiting till the faucet has released the funds."
)
@click.pass_context
@check_aea_project
def generate_wealth(
    click_context: click.Context,
    type_: str,
    url: str,
    password: Optional[str],
    sync: bool,
) -> None:
    """Generate wealth for the agent on a test network."""
    ctx = cast(Context, click_context.obj)
    _try_generate_wealth(ctx, type_, url, sync, password)


def _try_generate_wealth(
    ctx: Context,
    type_: str,
    url: Optional[str],
    sync: bool = False,
    password: Optional[str] = None,
) -> None:
    """
    Try generate wealth for the provided network identifier.

    :param ctx: the click context
    :param type_: the network type
    :param url: the url
    :param sync: whether to sync or not
    :param password: the password to encrypt/decrypt the private key.
    """
    wallet = get_wallet_from_context(ctx, password=password)
    try:
        address = wallet.addresses[type_]
        faucet_api_cls = make_faucet_api_cls(type_)
        testnet = faucet_api_cls.network_name
        click.echo(
            "Requesting funds for address {} on test network '{}'".format(
                address, testnet
            )
        )
        try_generate_testnet_wealth(type_, address, url, sync)

    except ValueError as e:  # pragma: no cover
        raise click.ClickException(str(e))
