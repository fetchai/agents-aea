# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2019 Fetch.AI Limited
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

from aea.crypto.cosmos import CosmosCrypto
from aea.crypto.helpers import create_private_key, try_generate_testnet_wealth
from aea.crypto.ledger_apis import DEFAULT_LEDGER_CONFIGS, LedgerApis
from aea.crypto.wallet import Wallet


logger = logging.getLogger("aea")
logging.basicConfig(level=logging.INFO)

COSMOS_PRIVATE_KEY_FILE_1 = "cosmos_private_key_1.txt"
COSMOS_PRIVATE_KEY_FILE_2 = "cosmos_private_key_2.txt"


def run():
    # Create a private keys
    create_private_key(
        CosmosCrypto.identifier, private_key_file=COSMOS_PRIVATE_KEY_FILE_1
    )
    create_private_key(
        CosmosCrypto.identifier, private_key_file=COSMOS_PRIVATE_KEY_FILE_2
    )

    # Set up the wallets
    wallet_1 = Wallet({CosmosCrypto.identifier: COSMOS_PRIVATE_KEY_FILE_1})
    wallet_2 = Wallet({CosmosCrypto.identifier: COSMOS_PRIVATE_KEY_FILE_2})

    # Set up the LedgerApis
    ledger_apis = LedgerApis(DEFAULT_LEDGER_CONFIGS, CosmosCrypto.identifier)

    # Generate some wealth
    try_generate_testnet_wealth(
        CosmosCrypto.identifier, wallet_1.addresses[CosmosCrypto.identifier]
    )

    logger.info(
        "Sending amount to {}".format(wallet_2.addresses.get(CosmosCrypto.identifier))
    )

    # Create the transaction and send it to the ledger.
    tx_nonce = ledger_apis.generate_tx_nonce(
        CosmosCrypto.identifier,
        wallet_2.addresses.get(CosmosCrypto.identifier),
        wallet_1.addresses.get(CosmosCrypto.identifier),
    )
    transaction = ledger_apis.get_transfer_transaction(
        identifier=CosmosCrypto.identifier,
        sender_address=wallet_1.addresses.get(CosmosCrypto.identifier),
        destination_address=wallet_2.addresses.get(CosmosCrypto.identifier),
        amount=1,
        tx_fee=1,
        tx_nonce=tx_nonce,
    )
    signed_transaction = wallet_1.sign_transaction(CosmosCrypto.identifier, transaction)
    transaction_digest = ledger_apis.send_signed_transaction(
        CosmosCrypto.identifier, signed_transaction
    )

    logger.info("Transaction complete.")
    logger.info("The transaction digest is {}".format(transaction_digest))


if __name__ == "__main__":
    run()
