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

"""This module contains some utilities for the ledger API connection tests."""
from typing import Dict

from aea.crypto.base import Crypto
from aea.crypto.ethereum import EthereumApi, GAS_ID, DEFAULT_GAS_PRICE
from aea.mail.base import Address


def make_ethereum_transaction(
        crypto: Crypto,
        api: EthereumApi,
        destination_address: Address,
        amount: int,
        tx_fee: int,
        tx_nonce: str,
        chain_id: int = 1,
        **kwargs,
) -> Dict:
    tx_digest = None
    try:
        nonce = api.api.eth.getTransactionCount(  # pylint: disable=no-member
            api.api.toChecksumAddress(crypto.address)
        )
    except Exception:
        nonce = None

    if nonce is None:
        return tx_digest

    transaction = {
        "nonce": nonce,
        "chainId": chain_id,
        "to": destination_address,
        "value": amount,
        "gas": tx_fee,
        "gasPrice": api.api.toWei(DEFAULT_GAS_PRICE, GAS_ID),
        "data": tx_nonce,
    }
    return transaction
