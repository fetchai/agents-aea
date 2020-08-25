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

"""Implementation of the 'aea get_multiaddress' subcommand."""

from typing import cast, Optional

import click

from aea.cli.utils.click_utils import PublicIdParameter
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project
from aea.configurations.base import PublicId
from aea.crypto.registries import crypto_registry


@click.command()
@click.argument(
    "ledger_id",
    metavar="TYPE",
    type=click.Choice(list(crypto_registry.supported_ids)),
    required=True,
)
@click.option(
    "--connection", type=PublicIdParameter(), required=False, default=None,
)
@click.pass_context
@check_aea_project
def get_multiaddress(click_context, ledger_id, connection: Optional[PublicId]):
    """Get the address associated with the private key."""
    address = _try_get_multiaddress(click_context, ledger_id, connection)
    click.echo(address)


def _try_get_multiaddress(
    click_context, ledger_id: str, connection_id: Optional[PublicId]
):
    """
    Try to get the multi-address.

    :param click_context: click context object.
    :param ledger_id: the ledger id.
    :param connection_id: the connection id.

    :return: address.
    """
    ctx = cast(Context, click_context.obj)
