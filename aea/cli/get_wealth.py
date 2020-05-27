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

"""Implementation of the 'aea get_wealth' subcommand."""

from typing import cast

import click

from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project
from aea.cli.utils.package_utils import try_get_balance, verify_or_create_private_keys
from aea.crypto.ledger_apis import SUPPORTED_LEDGER_APIS
from aea.crypto.wallet import Wallet


@click.command()
@click.argument(
    "type_", metavar="TYPE", type=click.Choice(SUPPORTED_LEDGER_APIS), required=True,
)
@click.pass_context
@check_aea_project
def get_wealth(click_context, type_):
    """Get the wealth associated with the private key."""
    wealth = _try_get_wealth(click_context, type_)
    click.echo(wealth)


def _try_get_wealth(click_context, type_):
    ctx = cast(Context, click_context.obj)
    verify_or_create_private_keys(ctx)
    private_key_paths = {
        config_pair[0]: config_pair[1]
        for config_pair in ctx.agent_config.private_key_paths.read_all()
    }
    wallet = Wallet(private_key_paths)
    return try_get_balance(ctx.agent_config, wallet, type_)
