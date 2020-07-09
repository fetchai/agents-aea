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

import time
from typing import cast

import click

from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project
from aea.cli.utils.package_utils import try_get_balance, verify_or_create_private_keys
from aea.crypto.helpers import (
    IDENTIFIER_TO_FAUCET_APIS,
    TESTNETS,
    try_generate_testnet_wealth,
)
from aea.crypto.wallet import Wallet


FUNDS_RELEASE_TIMEOUT = 10


@click.command()
@click.argument(
    "type_",
    metavar="TYPE",
    type=click.Choice(list(IDENTIFIER_TO_FAUCET_APIS.keys())),
    required=True,
)
@click.option(
    "--sync", is_flag=True, help="For waiting till the faucet has released the funds."
)
@click.pass_context
@check_aea_project
def generate_wealth(click_context, sync, type_):
    """Generate wealth for address on test network."""
    _try_generate_wealth(click_context, type_, sync)


def _try_generate_wealth(click_context, type_, sync):
    ctx = cast(Context, click_context.obj)
    verify_or_create_private_keys(ctx)

    private_key_paths = {
        config_pair[0]: config_pair[1]
        for config_pair in ctx.agent_config.private_key_paths.read_all()
    }
    wallet = Wallet(private_key_paths)
    try:
        address = wallet.addresses[type_]
        testnet = TESTNETS[type_]
        click.echo(
            "Requesting funds for address {} on test network '{}'".format(
                address, testnet
            )
        )
        try_generate_testnet_wealth(type_, address)
        if sync:
            _wait_funds_release(ctx.agent_config, wallet, type_)

    except (AssertionError, ValueError) as e:  # pragma: no cover
        raise click.ClickException(str(e))


def _wait_funds_release(agent_config, wallet, type_):
    start_balance = try_get_balance(agent_config, wallet, type_)
    end_time = time.time() + FUNDS_RELEASE_TIMEOUT
    while time.time() < end_time:
        if start_balance != try_get_balance(agent_config, wallet, type_):
            break  # pragma: no cover
        time.sleep(1)
