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

"""This module contains the tests of the ledger API connection module."""
import asyncio
import logging
from pathlib import Path
from typing import cast

import pytest

import aea
from aea.connections.base import Connection
from aea.crypto.cosmos import CosmosCrypto
from aea.crypto.ethereum import EthereumCrypto, EthereumApi
from aea.crypto.fetchai import FetchAICrypto
from aea.crypto.wallet import CryptoStore
from aea.identity.base import Identity
from aea.mail.base import Envelope

from packages.fetchai.protocols.ledger_api import LedgerApiMessage
from packages.fetchai.protocols.ledger_api.custom_types import AnyObject

from tests.conftest import (
    COSMOS_ADDRESS_ONE,
    ETHEREUM_ADDRESS_ONE,
    FETCHAI_ADDRESS_ONE,
    ROOT_DIR, ETHEREUM_PRIVATE_KEY_PATH,
)
from tests.test_packages.test_connections.test_ledger_api.utils import make_ethereum_transaction

logger = logging.getLogger(__name__)


ledger_ids = pytest.mark.parametrize(
    "ledger_id,address",
    [
        (FetchAICrypto.identifier, FETCHAI_ADDRESS_ONE),
        (EthereumCrypto.identifier, ETHEREUM_ADDRESS_ONE),
        (CosmosCrypto.identifier, COSMOS_ADDRESS_ONE),
    ],
)


@pytest.fixture()
async def ledger_apis_connection(request):
    identity = Identity("name", FetchAICrypto().address)
    crypto_store = CryptoStore()
    directory = Path(ROOT_DIR, "packages", "fetchai", "connections", "ledger_api")
    connection = Connection.from_dir(
        directory, identity=identity, crypto_store=crypto_store
    )
    connection = cast(Connection, connection)
    await connection.connect()
    yield connection
    await connection.disconnect()


@pytest.mark.asyncio
@ledger_ids
async def test_get_balance(ledger_id, address, ledger_apis_connection: Connection):
    """Test get balance."""
    request = LedgerApiMessage(
        LedgerApiMessage.Performative.GET_BALANCE, ledger_id=ledger_id, address=address
    )
    envelope = Envelope("", "", request.protocol_id, message=request)
    await ledger_apis_connection.send(envelope)
    await asyncio.sleep(0.01)
    response = await ledger_apis_connection.receive()

    assert response is not None
    assert type(response.message) == LedgerApiMessage
    message = cast(LedgerApiMessage, response.message)
    actual_balance_amount = message.amount
    expected_balance_amount = aea.crypto.registries.make_ledger_api(
        ledger_id
    ).get_balance(address)
    assert actual_balance_amount == expected_balance_amount


@pytest.mark.asyncio
async def test_send_signed_transaction_ethereum(ledger_apis_connection: Connection):
    """Test send signed transaction with Ethereum APIs."""
    crypto1 = EthereumCrypto(private_key_path=ETHEREUM_PRIVATE_KEY_PATH)
    crypto2 = EthereumCrypto()
    api = aea.crypto.registries.make_ledger_api(EthereumCrypto.identifier)
    api = cast(EthereumApi, api)

    amount = 40000
    fee = 30000
    tx_nonce = api.generate_tx_nonce(crypto1.address, crypto2.address)
    tx = make_ethereum_transaction(crypto1,
                              api,
                              crypto2.address,
                              amount,
                              fee,
                              tx_nonce,
                              chain_id=3)

    signed_transaction = crypto1.sign_transaction(tx)
    request = LedgerApiMessage(
        LedgerApiMessage.Performative.SEND_SIGNED_TX,
        ledger_id=EthereumCrypto.identifier,
        signed_tx=AnyObject(signed_transaction)
    )
    envelope = Envelope("", "", request.protocol_id, message=request)
    await ledger_apis_connection.send(envelope)
    await asyncio.sleep(0.01)
    response = await ledger_apis_connection.receive()

    assert response is not None
    assert type(response.message) == LedgerApiMessage
    response_message = cast(LedgerApiMessage, response.message)
    assert response_message.performative == LedgerApiMessage.Performative.TX_DIGEST
    assert response_message.digest is not None
    assert type(response_message.digest) == str
    assert type(response_message.digest.startswith("0x"))

    # check that the transaction is valid
    is_valid = api.is_transaction_valid(response_message.digest, crypto2.address,
                             crypto1.address, tx_nonce, amount)
    assert is_valid, "Transaction not valid."

# @pytest.mark.asyncio
# @ledger_ids
# async def test_get_transaction_receipt(ledger_id, address, ledger_apis_connection: Connection):
#     """Test get balance."""
#     request = LedgerApiMessage(
#         LedgerApiMessage.Performative.GET_TRANSACTION_RECEIPT, ledger_id=ledger_id, tx_digest=address
#     )
#     envelope = Envelope("", "", request.protocol_id, message=request)
#     await ledger_apis_connection.send(envelope)
#     await asyncio.sleep(0.01)
#     response = await ledger_apis_connection.receive()
#
#     assert response is not None
#     assert type(response.message) == LedgerApiMessage
#     message = cast(LedgerApiMessage, response.message)
#     actual_balance_amount = message.amount
#     expected_balance_amount = aea.crypto.registries.make_ledger_api(
#         ledger_id
#     ).get_balance(address)
#     assert actual_balance_amount == expected_balance_amount
