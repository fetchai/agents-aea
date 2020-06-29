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
from aea.crypto.ethereum import EthereumApi, EthereumCrypto
from aea.crypto.fetchai import FetchAICrypto
from aea.crypto.wallet import CryptoStore
from aea.helpers.dialogue.base import Dialogue as BaseDialogue
from aea.helpers.dialogue.base import DialogueLabel as BaseDialogueLabel
from aea.helpers.transaction.base import SignedTransaction
from aea.identity.base import Identity
from aea.mail.base import Envelope
from aea.protocols.base import Message

from packages.fetchai.protocols.ledger_api.dialogues import LedgerApiDialogue
from packages.fetchai.protocols.ledger_api.dialogues import (
    LedgerApiDialogues as BaseLedgerApiDialogues,
)
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage

from tests.conftest import (
    COSMOS_ADDRESS_ONE,
    ETHEREUM_ADDRESS_ONE,
    ETHEREUM_PRIVATE_KEY_PATH,
    FETCHAI_ADDRESS_ONE,
    ROOT_DIR,
)

logger = logging.getLogger(__name__)


ledger_ids = pytest.mark.parametrize(
    "ledger_id,address",
    [
        (FetchAICrypto.identifier, FETCHAI_ADDRESS_ONE),
        (EthereumCrypto.identifier, ETHEREUM_ADDRESS_ONE),
        (CosmosCrypto.identifier, COSMOS_ADDRESS_ONE),
    ],
)


class LedgerApiDialogues(BaseLedgerApiDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, agent_address: str) -> None:
        """
        Initialize dialogues.

        :return: None
        """
        BaseLedgerApiDialogues.__init__(self, agent_address)

    @staticmethod
    def role_from_first_message(message: Message) -> BaseDialogue.Role:
        """Infer the role of the agent from an incoming/outgoing first message

        :param message: an incoming/outgoing first message
        :return: The role of the agent
        """
        return LedgerApiDialogue.AgentRole.LEDGER

    def create_dialogue(
        self, dialogue_label: BaseDialogueLabel, role: BaseDialogue.Role,
    ) -> LedgerApiDialogue:
        """
        Create an instance of fipa dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param role: the role of the agent this dialogue is maintained for

        :return: the created dialogue
        """
        dialogue = LedgerApiDialogue(
            dialogue_label=dialogue_label, agent_address=self.agent_address, role=role,
        )
        return dialogue


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
    ledger_api_dialogues = LedgerApiDialogues(address)
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
    actual_balance_amount = response_msg.balance
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
    ledger_api_dialogues = LedgerApiDialogues(crypto1.address)

    amount = 40000
    fee = 30000
    tx_nonce = api.generate_tx_nonce(crypto1.address, crypto2.address)

    raw_tx = api.get_transfer_transaction(
        sender_address=crypto1.address,
        destination_address=crypto2.address,
        amount=amount,
        tx_fee=fee,
        tx_nonce=tx_nonce,
        chain_id=3,
    )

    signed_transaction = crypto1.sign_transaction(raw_tx)
    request = LedgerApiMessage(
        performative=LedgerApiMessage.Performative.SEND_SIGNED_TRANSACTION,
        dialogue_reference=ledger_api_dialogues.new_self_initiated_dialogue_reference(),
        ledger_id=EthereumCrypto.identifier,
        signed_transaction=SignedTransaction(
            EthereumCrypto.identifier, signed_transaction
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
        response_message.performative
        == LedgerApiMessage.Performative.TRANSACTION_DIGEST
    )
    response_dialogue = ledger_api_dialogues.update(response_message)
    assert response_dialogue == ledger_api_dialogue
    assert response_message.transaction_digest is not None
    assert type(response_message.transaction_digest) == str
    assert type(response_message.transaction_digest.startswith("0x"))

    # check that the transaction is settled (to update nonce!)
    is_settled = False
    attempts = 0
    while not is_settled and attempts < 60:
        attempts += 1
        tx_receipt = api.get_transaction_receipt(response_message.transaction_digest)
        is_settled = api.is_transaction_settled(tx_receipt,)
        await asyncio.sleep(4.0)
    assert is_settled, "Transaction not settled."


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
