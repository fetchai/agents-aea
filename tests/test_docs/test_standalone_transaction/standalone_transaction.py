# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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
"""This module contains the last code-block from the standalone-transaction.md file."""

import logging

from aea_ledger_fetchai import FetchAICrypto

from aea.crypto.helpers import create_private_key, try_generate_testnet_wealth
from aea.crypto.ledger_apis import LedgerApis
from aea.crypto.wallet import Wallet


logger = logging.getLogger("aea")
logging.basicConfig(level=logging.INFO)

FETCHAI_PRIVATE_KEY_FILE_1 = "fetchai_private_key_1.txt"
FETCHAI_PRIVATE_KEY_FILE_2 = "fetchai_private_key_2.txt"


def run():
    """Run demo."""

    # Create a private keys
    create_private_key(
        FetchAICrypto.identifier, private_key_file=FETCHAI_PRIVATE_KEY_FILE_1
    )
    create_private_key(
        FetchAICrypto.identifier, private_key_file=FETCHAI_PRIVATE_KEY_FILE_2
    )

    # Set up the wallets
    wallet_1 = Wallet({FetchAICrypto.identifier: FETCHAI_PRIVATE_KEY_FILE_1})
    wallet_2 = Wallet({FetchAICrypto.identifier: FETCHAI_PRIVATE_KEY_FILE_2})

    # Generate some wealth
    try_generate_testnet_wealth(
        FetchAICrypto.identifier, wallet_1.addresses[FetchAICrypto.identifier]
    )

    logger.info(
        "Sending amount to {}".format(wallet_2.addresses.get(FetchAICrypto.identifier))
    )

    # Create the transaction and send it to the ledger.
    tx_nonce = LedgerApis.generate_tx_nonce(
        FetchAICrypto.identifier,
        wallet_2.addresses.get(FetchAICrypto.identifier),
        wallet_1.addresses.get(FetchAICrypto.identifier),
    )
    transaction = LedgerApis.get_transfer_transaction(
        identifier=FetchAICrypto.identifier,
        sender_address=wallet_1.addresses.get(FetchAICrypto.identifier),
        destination_address=wallet_2.addresses.get(FetchAICrypto.identifier),
        amount=1,
        tx_fee=1,
        tx_nonce=tx_nonce,
    )
    signed_transaction = wallet_1.sign_transaction(
        FetchAICrypto.identifier, transaction
    )
    transaction_digest = LedgerApis.send_signed_transaction(
        FetchAICrypto.identifier, signed_transaction
    )

    logger.info("Transaction complete.")
    logger.info("The transaction digest is {}".format(transaction_digest))


if __name__ == "__main__":
    run()
