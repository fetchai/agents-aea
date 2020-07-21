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
from unittest.mock import Mock, patch

import pytest

from aea.configurations.base import ProtocolId
from aea.configurations.constants import DEFAULT_LEDGER
from aea.connections.base import Connection, ConnectionStatus
from aea.crypto.registries import make_crypto, make_ledger_api
from aea.crypto.wallet import CryptoStore
from aea.helpers.transaction.base import (
    RawTransaction,
    SignedTransaction,
    Terms,
    TransactionDigest,
    TransactionReceipt,
)
from aea.identity.base import Identity
from aea.mail.base import Envelope

from packages.fetchai.connections.ledger.connection import LedgerConnection
from packages.fetchai.connections.ledger.contract_dispatcher import ContractApiDialogues
from packages.fetchai.connections.ledger.ledger_dispatcher import (
    LedgerApiDialogues,
    LedgerApiRequestDispatcher,
)
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage


from tests.conftest import (
    COSMOS,
    COSMOS_ADDRESS_ONE,
    COSMOS_TESTNET_CONFIG,
    ETHEREUM,
    ETHEREUM_ADDRESS_ONE,
    ETHEREUM_PRIVATE_KEY_PATH,
    ETHEREUM_TESTNET_CONFIG,
    FETCHAI,
    FETCHAI_ADDRESS_ONE,
    FETCHAI_TESTNET_CONFIG,
    ROOT_DIR,
)

logger = logging.getLogger(__name__)


ledger_ids = pytest.mark.parametrize(
    "ledger_id,address,config",
    [
        (FETCHAI, FETCHAI_ADDRESS_ONE, FETCHAI_TESTNET_CONFIG),
        (ETHEREUM, ETHEREUM_ADDRESS_ONE, ETHEREUM_TESTNET_CONFIG),
        (COSMOS, COSMOS_ADDRESS_ONE, COSMOS_TESTNET_CONFIG),
    ],
)


@pytest.fixture()
async def ledger_apis_connection(request):
    """Make a connection."""
    crypto = make_crypto(DEFAULT_LEDGER)
    identity = Identity("name", crypto.address)
    crypto_store = CryptoStore()
    directory = Path(ROOT_DIR, "packages", "fetchai", "connections", "ledger")
    connection = Connection.from_dir(
        directory, identity=identity, crypto_store=crypto_store
    )
    connection = cast(Connection, connection)
    await connection.connect()
    yield connection
    await connection.disconnect()


@pytest.mark.integration
@pytest.mark.ledger
@pytest.mark.asyncio
@ledger_ids
async def test_get_balance(
    ledger_id, address, config, ledger_apis_connection: Connection
):
    """Test get balance."""
    import aea  # noqa # to load registries

    ledger_api_dialogues = LedgerApiDialogues()
    request = LedgerApiMessage(
        performative=LedgerApiMessage.Performative.GET_BALANCE,
        dialogue_reference=ledger_api_dialogues.new_self_initiated_dialogue_reference(),
        ledger_id=ledger_id,
        address=address,
    )

    request.counterparty = str(ledger_apis_connection.connection_id)
    ledger_api_dialogue = ledger_api_dialogues.update(request)
    assert ledger_api_dialogue is not None
    envelope = Envelope(
        to=str(ledger_apis_connection.connection_id),
        sender=address,
        protocol_id=request.protocol_id,
        message=request,
    )

    await ledger_apis_connection.send(envelope)
    await asyncio.sleep(0.01)
    response = await ledger_apis_connection.receive()

    assert response is not None
    assert type(response.message) == LedgerApiMessage
    response_msg = cast(LedgerApiMessage, response.message)
    response_dialogue = ledger_api_dialogues.update(response_msg)
    assert response_dialogue == ledger_api_dialogue
    assert response_msg.performative == LedgerApiMessage.Performative.BALANCE
    actual_balance_amount = response_msg.balance
    expected_balance_amount = make_ledger_api(ledger_id, **config).get_balance(address)
    assert actual_balance_amount == expected_balance_amount


@pytest.mark.integration
@pytest.mark.ledger
@pytest.mark.asyncio
async def test_send_signed_transaction_ethereum(ledger_apis_connection: Connection):
    """Test send signed transaction with Ethereum APIs."""
    import aea  # noqa # to load registries

    crypto1 = make_crypto(ETHEREUM, private_key_path=ETHEREUM_PRIVATE_KEY_PATH)
    crypto2 = make_crypto(ETHEREUM)
    ledger_api_dialogues = LedgerApiDialogues()

    amount = 40000
    fee = 30000

    request = LedgerApiMessage(
        performative=LedgerApiMessage.Performative.GET_RAW_TRANSACTION,
        dialogue_reference=ledger_api_dialogues.new_self_initiated_dialogue_reference(),
        terms=Terms(
            ledger_id=ETHEREUM,
            sender_address=crypto1.address,
            counterparty_address=crypto2.address,
            amount_by_currency_id={"ETH": -amount},
            quantities_by_good_id={"some_service_id": 1},
            is_sender_payable_tx_fee=True,
            nonce="",
            fee_by_currency_id={"ETH": fee},
            chain_id=3,
        ),
    )
    request.counterparty = str(ledger_apis_connection.connection_id)
    ledger_api_dialogue = ledger_api_dialogues.update(request)
    assert ledger_api_dialogue is not None
    envelope = Envelope(
        to=str(ledger_apis_connection.connection_id),
        sender=crypto1.address,
        protocol_id=request.protocol_id,
        message=request,
    )
    await ledger_apis_connection.send(envelope)
    await asyncio.sleep(0.01)
    response = await ledger_apis_connection.receive()

    assert response is not None
    assert type(response.message) == LedgerApiMessage
    response_message = cast(LedgerApiMessage, response.message)
    assert (
        response_message.performative == LedgerApiMessage.Performative.RAW_TRANSACTION
    )
    response_dialogue = ledger_api_dialogues.update(response_message)
    assert response_dialogue == ledger_api_dialogue
    assert type(response_message.raw_transaction) == RawTransaction
    assert response_message.raw_transaction.ledger_id == request.terms.ledger_id

    # raw_tx = api.get_transfer_transaction(
    #     sender_address=crypto1.address,
    #     destination_address=crypto2.address,
    #     amount=amount,
    #     tx_fee=fee,
    #     tx_nonce="",
    #     chain_id=3,
    # )

    signed_transaction = crypto1.sign_transaction(response_message.raw_transaction.body)
    request = LedgerApiMessage(
        performative=LedgerApiMessage.Performative.SEND_SIGNED_TRANSACTION,
        dialogue_reference=ledger_api_dialogue.dialogue_label.dialogue_reference,
        signed_transaction=SignedTransaction(ETHEREUM, signed_transaction),
    )
    request.counterparty = str(ledger_apis_connection.connection_id)
    ledger_api_dialogue.update(request)
    envelope = Envelope(
        to=str(ledger_apis_connection.connection_id),
        sender=crypto1.address,
        protocol_id=request.protocol_id,
        message=request,
    )
    await ledger_apis_connection.send(envelope)
    await asyncio.sleep(0.01)
    response = await ledger_apis_connection.receive()

    assert response is not None
    assert type(response.message) == LedgerApiMessage
    response_message = cast(LedgerApiMessage, response.message)
    assert (
        response_message.performative != LedgerApiMessage.Performative.ERROR
    ), f"Received error: {response_message.message}"
    assert (
        response_message.performative
        == LedgerApiMessage.Performative.TRANSACTION_DIGEST
    )
    response_dialogue = ledger_api_dialogues.update(response_message)
    assert response_dialogue == ledger_api_dialogue
    assert type(response_message.transaction_digest) == TransactionDigest
    assert type(response_message.transaction_digest.body) == str
    assert (
        response_message.transaction_digest.ledger_id
        == request.signed_transaction.ledger_id
    )
    assert type(response_message.transaction_digest.body.startswith("0x"))

    request = LedgerApiMessage(
        performative=LedgerApiMessage.Performative.GET_TRANSACTION_RECEIPT,
        dialogue_reference=ledger_api_dialogue.dialogue_label.dialogue_reference,
        transaction_digest=response_message.transaction_digest,
    )
    request.counterparty = str(ledger_apis_connection.connection_id)
    ledger_api_dialogue.update(request)
    envelope = Envelope(
        to=str(ledger_apis_connection.connection_id),
        sender=crypto1.address,
        protocol_id=request.protocol_id,
        message=request,
    )
    await ledger_apis_connection.send(envelope)
    await asyncio.sleep(0.01)
    response = await ledger_apis_connection.receive()

    assert response is not None
    assert type(response.message) == LedgerApiMessage
    response_message = cast(LedgerApiMessage, response.message)
    assert (
        response_message.performative
        == LedgerApiMessage.Performative.TRANSACTION_RECEIPT
    )
    response_dialogue = ledger_api_dialogues.update(response_message)
    assert response_dialogue == ledger_api_dialogue
    assert type(response_message.transaction_receipt) == TransactionReceipt
    assert response_message.transaction_receipt.receipt is not None
    assert response_message.transaction_receipt.transaction is not None
    assert (
        response_message.transaction_receipt.ledger_id
        == request.transaction_digest.ledger_id
    )

    # # check that the transaction is settled (to update nonce!)
    # is_settled = False
    # attempts = 0
    # while not is_settled and attempts < 60:
    #     attempts += 1
    #     tx_receipt = api.get_transaction_receipt(
    #         response_message.transaction_digest.body
    #     )
    #     is_settled = api.is_transaction_settled(tx_receipt)
    #     await asyncio.sleep(4.0)
    # assert is_settled, "Transaction not settled."


@pytest.mark.asyncio
async def test_unsupported_protocol(ledger_apis_connection: LedgerConnection):
    """Test fail on protocol not supported."""
    envelope = Envelope(
        to=str(ledger_apis_connection.connection_id),
        sender="test",
        protocol_id=ProtocolId.from_str("author/package_name:0.1.0"),
        message=b"message",
    )
    with pytest.raises(ValueError):
        ledger_apis_connection._schedule_request(envelope)


@pytest.mark.asyncio
async def test_new_message_wait_flag(ledger_apis_connection: LedgerConnection):
    """Test wait for new message."""
    task = asyncio.ensure_future(ledger_apis_connection.receive())
    await asyncio.sleep(0.1)
    assert not task.done()
    task.cancel()


@pytest.mark.asyncio
async def test_no_balance():
    """Test no balance."""
    dispatcher = LedgerApiRequestDispatcher(ConnectionStatus())
    mock_api = Mock()
    contract_api_dialogues = ContractApiDialogues()
    message = LedgerApiMessage(
        performative=LedgerApiMessage.Performative.GET_BALANCE,
        dialogue_reference=contract_api_dialogues.new_self_initiated_dialogue_reference(),
        ledger_id=ETHEREUM,
        address="test",
    )
    message.counterparty = "test"
    dialogue = contract_api_dialogues.update(message)
    mock_api.get_balance.return_value = None
    msg = dispatcher.get_balance(mock_api, message, dialogue)

    assert msg.performative == LedgerApiMessage.Performative.ERROR


@pytest.mark.asyncio
async def test_no_raw_tx():
    """Test no raw tx returned."""
    dispatcher = LedgerApiRequestDispatcher(ConnectionStatus())
    mock_api = Mock()
    contract_api_dialogues = ContractApiDialogues()
    message = LedgerApiMessage(
        performative=LedgerApiMessage.Performative.GET_RAW_TRANSACTION,
        dialogue_reference=contract_api_dialogues.new_self_initiated_dialogue_reference(),
        terms=Terms(
            ledger_id=ETHEREUM,
            sender_address="1111",
            counterparty_address="22222",
            amount_by_currency_id={"ETH": -1},
            quantities_by_good_id={"some_service_id": 1},
            is_sender_payable_tx_fee=True,
            nonce="",
            fee_by_currency_id={"ETH": 10},
            chain_id=3,
        ),
    )
    message.counterparty = "test"
    dialogue = contract_api_dialogues.update(message)
    mock_api.get_transfer_transaction.return_value = None
    msg = dispatcher.get_raw_transaction(mock_api, message, dialogue)

    assert msg.performative == LedgerApiMessage.Performative.ERROR


@pytest.mark.asyncio
async def test_attempts_get_transaction_receipt():
    """Test retry and sleep."""
    dispatcher = LedgerApiRequestDispatcher(ConnectionStatus())
    dispatcher.connection_status.is_connected = True
    mock_api = Mock()
    contract_api_dialogues = ContractApiDialogues()
    message = LedgerApiMessage(
        performative=LedgerApiMessage.Performative.GET_TRANSACTION_RECEIPT,
        dialogue_reference=contract_api_dialogues.new_self_initiated_dialogue_reference(),
        transaction_digest=TransactionDigest("asdad", "sdfdsf"),
    )
    message.counterparty = "test"
    dialogue = contract_api_dialogues.update(message)
    mock_api.get_transaction.return_value = None
    mock_api.is_transaction_settled.return_value = True
    with patch.object(dispatcher, "MAX_ATTEMPTS", 2):
        with patch.object(dispatcher, "TIMEOUT", 0.001):
            msg = dispatcher.get_transaction_receipt(mock_api, message, dialogue)

    assert msg.performative == LedgerApiMessage.Performative.ERROR
