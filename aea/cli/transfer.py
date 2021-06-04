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

"""Implementation of the 'aea transfer' subcommand."""
import time
from typing import Optional, cast

import click

from aea.cli.get_address import _try_get_address
from aea.cli.utils.click_utils import password_option
from aea.cli.utils.context import Context
from aea.cli.utils.decorators import check_aea_project
from aea.cli.utils.package_utils import (
    _override_ledger_configurations,
    get_wallet_from_context,
    try_get_balance,
)
from aea.common import Address
from aea.crypto.ledger_apis import LedgerApis
from aea.crypto.registries import ledger_apis_registry


DEFAULT_SETTLE_TIMEOUT = 60


@click.command()
@click.argument(
    "type_",
    metavar="TYPE",
    type=click.Choice(ledger_apis_registry.supported_ids),
    required=True,
)
@click.argument(
    "address", type=str, required=True,
)
@click.argument(
    "amount", type=int, required=True,
)
@click.argument("fee", type=int, required=False, default=100)
@password_option()
@click.option("-y", "--yes", type=bool, is_flag=True, default=False)
@click.option("--settle-timeout", type=int, default=DEFAULT_SETTLE_TIMEOUT)
@click.option("--sync", type=bool, is_flag=True, default=False)
@click.pass_context
@check_aea_project
def transfer(
    click_context: click.Context,
    type_: str,
    address: str,
    amount: int,
    fee: int,
    password: Optional[str],
    yes: bool,
    settle_timeout: int,
    sync: bool,
) -> None:
    """Transfer wealth associated with a private key of the agent to another account."""
    ctx = cast(Context, click_context.obj)
    try:
        own_address = _try_get_address(ctx, type_, password)
    except KeyError:
        raise click.ClickException(
            f"No private key registered for `{type_}` in wallet!"
        )
    if not yes:
        click.confirm(
            f"You are about to transfer from {own_address} to {address} on ledger {type_} the amount {amount} with fee {fee}. Do you want to continue?",
            abort=True,
        )

    tx_digest = do_transfer(ctx, type_, address, amount, fee, password)

    if not tx_digest:
        raise click.ClickException("Failed to send a transaction!")

    if sync:
        click.echo("Transaction set. Waiting to be settled...")
        wait_tx_settled(type_, tx_digest, timeout=settle_timeout)
        click.echo(
            f"Transaction successfully settled. Sent {amount} with fee {fee} to {address}, transaction digest: {tx_digest}"
        )
    else:
        click.echo(
            f"Transaction successfully submitted. Sending {amount} with fee {fee} to {address}, transaction digest: {tx_digest}"
        )


def wait_tx_settled(
    identifier: str, tx_digest: str, timeout: float = DEFAULT_SETTLE_TIMEOUT
) -> None:
    """
    Wait transaction is settled successfully.

    :param identifier: str, ledger id
    :param tx_digest: str, transaction digest
    :param timeout: int, timeout in seconds before timeout error raised

    :raises TimeoutError: on timeout
    """
    t = time.time()
    while True:
        if time.time() - t > timeout:
            raise TimeoutError()
        if LedgerApis.is_transaction_settled(identifier, tx_digest):
            return
        time.sleep(1)


def do_transfer(
    ctx: Context,
    identifier: str,
    address: Address,
    amount: int,
    tx_fee: int,
    password: Optional[str] = None,
) -> Optional[str]:
    """
    Perform wealth transfer to another account.

    :param ctx: click context
    :param identifier: str, ledger id to perform transfer operation
    :param address: address of the recipient
    :param amount: int, amount of wealth to transfer
    :param tx_fee: int, fee for transaction
    :param password: the password to encrypt/decrypt the private key

    :return: str, transaction digest or None if failed.
    """
    click.echo("Starting transfer ...")
    wallet = get_wallet_from_context(ctx, password=password)
    source_address = wallet.addresses[identifier]

    _override_ledger_configurations(ctx.agent_config)
    balance = int(try_get_balance(ctx.agent_config, wallet, identifier))
    total_payable = amount + tx_fee
    if total_payable > balance:
        raise click.ClickException(
            f"Balance is not enough! Available={balance}, required={total_payable}!"
        )

    tx_nonce = LedgerApis.generate_tx_nonce(identifier, source_address, address)
    transaction = LedgerApis.get_transfer_transaction(
        identifier, source_address, address, amount, tx_fee, tx_nonce
    )
    tx_signed = wallet.sign_transaction(identifier, transaction)
    return LedgerApis.send_signed_transaction(identifier, tx_signed)
