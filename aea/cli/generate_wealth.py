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

from aea.configurations.base import AgentConfig
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project
from aea.cli.utils.package_utils import try_get_balance, verify_or_create_private_keys
from aea.crypto.helpers import try_generate_testnet_wealth
from aea.crypto.registries import faucet_apis_registry, make_faucet_api_cls
from aea.crypto.wallet import Wallet


FUNDS_RELEASE_TIMEOUT = 30


@click.command()
@click.argument(
    "type_",
    metavar="TYPE",
    type=click.Choice(list(faucet_apis_registry.supported_ids)),
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


def _try_generate_wealth(click_context: click.core.Context, type_: str, sync: bool) -> None:
    """
    Try generate wealth for the provided network identifier.

    :param click_context: the click context
    :param type_: the network type
    :param sync: whether to sync or not
    :return: None
    """
    ctx = cast(Context, click_context.obj)
    verify_or_create_private_keys(ctx=ctx)

    private_key_paths = {
        config_pair[0]: config_pair[1]
        for config_pair in ctx.agent_config.private_key_paths.read_all()
    }
    wallet = Wallet(private_key_paths)
    try:
        address = wallet.addresses[type_]
        faucet_api_cls = make_faucet_api_cls(type_)
        testnet = faucet_api_cls.testnet_name
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


def _wait_funds_release(agent_config: AgentConfig, wallet: Wallet, type_: str) -> bool:
    """
    Wait for the funds to be released.

    :param agent_config: the agent config
    :param wallet: the wallet
    :param type_: the network type
    """
    start_balance = try_get_balance(agent_config, wallet, type_)
    end_time = time.time() + FUNDS_RELEASE_TIMEOUT
    has_hit_timeout = True
    while time.time() < end_time:
        current_balance = try_get_balance(agent_config, wallet, type_)
        if start_balance != current_balance:
            has_hit_timeout = False
            break  # pragma: no cover
        time.sleep(1)
    if has_hit_timeout:
        raise ValueError("Timeout hit. Syncing did not finish.")
