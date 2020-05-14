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

from aea.crypto.fetchai import FETCHAI
from aea.crypto.helpers import _try_generate_testnet_wealth, create_private_key
from aea.crypto.ledger_apis import LedgerApis
from aea.crypto.wallet import Wallet


logger = logging.getLogger("aea")
logging.basicConfig(level=logging.INFO)

FETCHAI_PRIVATE_KEY_FILE_1 = "fet_private_key_1.txt"
FETCHAI_PRIVATE_KEY_FILE_2 = "fet_private_key_2.txt"


def run():
    # Create a private keys
    create_private_key(FETCHAI, private_key_file=FETCHAI_PRIVATE_KEY_FILE_1)
    create_private_key(FETCHAI, private_key_file=FETCHAI_PRIVATE_KEY_FILE_2)

    # Set up the wallets
    wallet_1 = Wallet({FETCHAI: FETCHAI_PRIVATE_KEY_FILE_1})
    wallet_2 = Wallet({FETCHAI: FETCHAI_PRIVATE_KEY_FILE_2})

    # Set up the LedgerApis
    ledger_apis = LedgerApis({FETCHAI: {"network": "testnet"}}, FETCHAI)

    # Generate some wealth
    _try_generate_testnet_wealth(FETCHAI, wallet_1.addresses[FETCHAI])

    logger.info("Sending amount to {}".format(wallet_2.addresses.get(FETCHAI)))

    # Create the transaction and send it to the ledger.
    ledger_api = ledger_apis.apis[FETCHAI]
    tx_nonce = ledger_api.generate_tx_nonce(
        wallet_2.addresses.get(FETCHAI), wallet_1.addresses.get(FETCHAI)
    )
    tx_digest = ledger_api.transfer(
        crypto=wallet_1.crypto_objects.get(FETCHAI),
        destination_address=wallet_2.addresses.get(FETCHAI),
        amount=1,
        tx_fee=1,
        tx_nonce=tx_nonce,
    )
    logger.info("Transaction complete.")
    logger.info("The transaction digest is {}".format(tx_digest))


if __name__ == "__main__":
    run()
