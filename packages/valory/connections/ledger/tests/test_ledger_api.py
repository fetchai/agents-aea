# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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
# pylint: skip-file

import asyncio
import logging
import platform
import time
from pathlib import Path
from typing import Any, Dict, Optional, cast
from unittest.mock import Mock, patch

import pytest
from aea_ledger_ethereum import EthereumCrypto
from aea_ledger_ethereum.test_tools.constants import ETHEREUM_PRIVATE_KEY_PATH
from aea_ledger_ethereum.test_tools.fixture_helpers import (  # noqa: F401 pylint: disable=unsed-import
    DEFAULT_GANACHE_CHAIN_ID,
    ganache,
)
from web3.eth import Eth

from aea.common import Address
from aea.configurations.data_types import PublicId
from aea.connections.base import Connection, ConnectionStates
from aea.crypto.ledger_apis import LedgerApis
from aea.crypto.registries import make_crypto, make_ledger_api
from aea.helpers.async_utils import AsyncState
from aea.helpers.transaction.base import (
    RawTransaction,
    SignedTransaction,
    Terms,
    TransactionDigest,
    TransactionReceipt,
)
from aea.mail.base import Envelope, Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue

from packages.valory.connections.ledger.connection import LedgerConnection
from packages.valory.connections.ledger.ledger_dispatcher import (
    LedgerApiRequestDispatcher,
)
from packages.valory.protocols.ledger_api.custom_types import Kwargs
from packages.valory.protocols.ledger_api.dialogues import LedgerApiDialogue
from packages.valory.protocols.ledger_api.dialogues import (
    LedgerApiDialogues as BaseLedgerApiDialogues,
)
from packages.valory.protocols.ledger_api.message import LedgerApiMessage


SOME_SKILL_ID = "some/skill:0.1.0"
PACKAGE_DIR = Path(__file__).parent.parent

skip_docker_tests = pytest.mark.skipif(
    platform.system() != "Linux",
    reason="Docker daemon is not available in Windows and macOS CI containers.",
)
logger = logging.getLogger(__name__)
ledger_ids = pytest.mark.parametrize(
    "ledger_id,address",
    [
        (EthereumCrypto.identifier, EthereumCrypto(ETHEREUM_PRIVATE_KEY_PATH).address),
    ],
)
gas_strategies = pytest.mark.parametrize(
    "gas_strategies",
    [
        {"gas_price_strategy": None},
        {"gas_price_strategy": "gas_station"},
        {"gas_price_strategy": "eip1559"},
        {
            "max_fee_per_gas": 1_000_000_000,
            "max_priority_fee_per_gas": 1_000_000_000,
        },
    ],
)


class LedgerApiDialogues(BaseLedgerApiDialogues):
    """The dialogues class keeps track of all ledger_api dialogues."""

    def __init__(self, self_address: Address, **kwargs: Any) -> None:
        """Initialize dialogues."""

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message"""
            return LedgerApiDialogue.Role.AGENT

        BaseLedgerApiDialogues.__init__(
            self,
            self_address=self_address,
            role_from_first_message=role_from_first_message,
        )


@pytest.mark.usefixtures("ganache")
@skip_docker_tests
class TestLedgerDispatcher:
    """Tests for ledger dispatcher."""

    @pytest.mark.asyncio
    @ledger_ids
    async def test_get_balance(
        self,
        ledger_id: str,
        address: str,
        ledger_apis_connection: Connection,
        update_default_ethereum_ledger_api: None,
        ethereum_testnet_config: Dict,
    ) -> None:
        """Test get balance method."""

        config = ethereum_testnet_config
        ledger_api_dialogues = LedgerApiDialogues(SOME_SKILL_ID)
        request, ledger_api_dialogue = ledger_api_dialogues.create(
            counterparty=str(ledger_apis_connection.connection_id),
            performative=LedgerApiMessage.Performative.GET_BALANCE,  # type: ignore
            ledger_id=ledger_id,
            address=address,
        )
        envelope = Envelope(
            to=request.to,
            sender=request.sender,
            message=request,
        )

        await ledger_apis_connection.send(envelope)
        await asyncio.sleep(0.01)
        response = await ledger_apis_connection.receive()

        assert response is not None
        assert isinstance(response.message, LedgerApiMessage)
        response_msg = cast(LedgerApiMessage, response.message)
        response_dialogue = ledger_api_dialogues.update(response_msg)
        assert response_dialogue == ledger_api_dialogue
        assert response_msg.performative == LedgerApiMessage.Performative.BALANCE
        actual_balance_amount = response_msg.balance
        expected_balance_amount = make_ledger_api(ledger_id, **config).get_balance(
            address
        )
        assert actual_balance_amount == expected_balance_amount

    @pytest.mark.asyncio
    @ledger_ids
    async def test_get_state(
        self,
        ledger_id: str,
        address: str,
        ledger_apis_connection: Connection,
        update_default_ethereum_ledger_api: None,
        ethereum_testnet_config: Dict,
    ) -> None:
        """Test get state."""

        config = ethereum_testnet_config

        if "ethereum" in ledger_id:
            callable_name = "get_block"
        else:
            callable_name = "blocks"
        args = ("latest",)
        kwargs = Kwargs({})

        ledger_api_dialogues = LedgerApiDialogues(SOME_SKILL_ID)
        request, ledger_api_dialogue = ledger_api_dialogues.create(
            counterparty=str(ledger_apis_connection.connection_id),
            performative=LedgerApiMessage.Performative.GET_STATE,  # type: ignore
            ledger_id=ledger_id,
            callable=callable_name,
            args=args,
            kwargs=kwargs,
        )
        envelope = Envelope(
            to=request.to,
            sender=request.sender,
            message=request,
        )

        await ledger_apis_connection.send(envelope)
        await asyncio.sleep(0.01)
        response = await ledger_apis_connection.receive()

        assert response is not None
        assert isinstance(response.message, LedgerApiMessage)
        response_msg = cast(LedgerApiMessage, response.message)
        response_dialogue = ledger_api_dialogues.update(response_msg)
        assert response_dialogue == ledger_api_dialogue

        assert (
            response_msg.performative == LedgerApiMessage.Performative.STATE
        ), response_msg
        actual_block = response_msg.state.body
        expected_block = make_ledger_api(ledger_id, **config).get_state(
            callable_name, *args
        )
        assert actual_block == expected_block

    @pytest.mark.asyncio
    @gas_strategies
    async def test_get_raw_transaction(
        self,
        gas_strategies: Dict,
        ledger_apis_connection: Connection,
        update_default_ethereum_ledger_api: None,
    ) -> None:
        """Test get raw transaction with Ethereum APIs."""
        import aea  # noqa # to load registries

        crypto1 = make_crypto(
            EthereumCrypto.identifier, private_key_path=ETHEREUM_PRIVATE_KEY_PATH
        )
        crypto2 = make_crypto(EthereumCrypto.identifier)
        ledger_api_dialogues = LedgerApiDialogues(SOME_SKILL_ID)

        amount = 40000
        fee = 10 ** 7

        # Create ledger_api dialogue: get raw transaction
        request, ledger_api_dialogue = ledger_api_dialogues.create(
            counterparty=str(ledger_apis_connection.connection_id),
            performative=LedgerApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
            terms=Terms(
                ledger_id=EthereumCrypto.identifier,
                sender_address=crypto1.address,
                counterparty_address=crypto2.address,
                amount_by_currency_id={"ETH": -amount},
                quantities_by_good_id={"some_service_id": 1},
                is_sender_payable_tx_fee=True,
                nonce="",
                fee_by_currency_id={"ETH": fee},
                chain_id=DEFAULT_GANACHE_CHAIN_ID,
                **gas_strategies,
            ),
        )
        request = cast(LedgerApiMessage, request)
        envelope = Envelope(
            to=request.to,
            sender=request.sender,
            message=request,
        )
        await ledger_apis_connection.send(envelope)
        await asyncio.sleep(0.01)

        # Raw transaction
        response = await ledger_apis_connection.receive()

        assert response is not None
        assert isinstance(response.message, LedgerApiMessage)
        response_message = cast(LedgerApiMessage, response.message)
        assert (
            response_message.performative
            == LedgerApiMessage.Performative.RAW_TRANSACTION
        )
        response_dialogue = ledger_api_dialogues.update(response_message)
        assert response_dialogue == ledger_api_dialogue
        assert isinstance(response_message.raw_transaction, RawTransaction)
        assert response_message.raw_transaction.ledger_id == request.terms.ledger_id

    @pytest.mark.asyncio
    @gas_strategies
    async def test_send_signed_transaction_ethereum(
        self, gas_strategies: Dict, ledger_apis_connection: LedgerConnection
    ) -> None:
        """Test send signed transaction with Ethereum APIs."""
        ledger_api_dialogues = LedgerApiDialogues(SOME_SKILL_ID)

        crypto1 = make_crypto(
            EthereumCrypto.identifier, private_key_path=ETHEREUM_PRIVATE_KEY_PATH
        )
        crypto2 = make_crypto(EthereumCrypto.identifier)

        # First, send a transaction so we can get a digest at the end
        amount = 40000
        fee = 10 ** 7

        request, ledger_api_dialogue = ledger_api_dialogues.create(
            counterparty=str(ledger_apis_connection.connection_id),
            performative=LedgerApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
            terms=Terms(
                ledger_id=EthereumCrypto.identifier,
                sender_address=crypto1.address,
                counterparty_address=crypto2.address,
                amount_by_currency_id={"ETH": -amount},
                quantities_by_good_id={"some_service_id": 1},
                is_sender_payable_tx_fee=True,
                nonce="",
                fee_by_currency_id={"ETH": fee},
                chain_id=DEFAULT_GANACHE_CHAIN_ID,
                **gas_strategies,
            ),
        )
        request = cast(LedgerApiMessage, request)
        envelope = Envelope(
            to=request.to,
            sender=request.sender,
            message=request,
        )

        # Check that we got the correct transaction response
        await ledger_apis_connection.send(envelope)
        await asyncio.sleep(0.01)
        response = await ledger_apis_connection.receive()

        assert response is not None
        assert isinstance(response.message, LedgerApiMessage)
        response_message = cast(LedgerApiMessage, response.message)
        assert (
            response_message.performative
            == LedgerApiMessage.Performative.RAW_TRANSACTION
        )
        response_dialogue = ledger_api_dialogues.update(response_message)
        assert response_dialogue == ledger_api_dialogue
        assert isinstance(response_message.raw_transaction, RawTransaction)
        assert response_message.raw_transaction.ledger_id == request.terms.ledger_id

        # Sign the transaction
        signed_transaction = crypto1.sign_transaction(
            response_message.raw_transaction.body
        )

        # Create new dialogue starting with signed transaction
        request, ledger_api_dialogue = ledger_api_dialogues.create(
            counterparty=str(ledger_apis_connection.connection_id),
            performative=LedgerApiMessage.Performative.SEND_SIGNED_TRANSACTION,  # type: ignore
            signed_transaction=SignedTransaction(
                EthereumCrypto.identifier, signed_transaction
            ),
        )
        request = cast(LedgerApiMessage, request)
        envelope = Envelope(
            to=request.to,
            sender=request.sender,
            message=request,
        )

        await ledger_apis_connection.send(envelope)
        await asyncio.sleep(0.01)

        # Transaction digest
        response = await ledger_apis_connection.receive()

        assert response is not None
        assert isinstance(response.message, LedgerApiMessage)
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
        assert isinstance(response_message.transaction_digest, TransactionDigest)
        assert isinstance(response_message.transaction_digest.body, str)
        assert (
            response_message.transaction_digest.ledger_id
            == request.signed_transaction.ledger_id
        )
        await asyncio.sleep(0.01)
        # Create new dialogue starting with GET_TRANSACTION_RECEIPT
        request, ledger_api_dialogue = ledger_api_dialogues.create(
            counterparty=str(ledger_apis_connection.connection_id),
            performative=LedgerApiMessage.Performative.GET_TRANSACTION_RECEIPT,  # type: ignore
            transaction_digest=response_message.transaction_digest,
        )
        envelope = Envelope(
            to=request.to,
            sender=request.sender,
            message=request,
        )
        await ledger_apis_connection.send(envelope)
        await asyncio.sleep(0.01)

        # Transaction receipt
        response = await ledger_apis_connection.receive()

        assert response is not None
        assert isinstance(response.message, LedgerApiMessage)
        response_message = cast(LedgerApiMessage, response.message)
        assert (
            response_message.performative
            == LedgerApiMessage.Performative.TRANSACTION_RECEIPT
        )
        response_dialogue = ledger_api_dialogues.update(response_message)
        assert response_dialogue == ledger_api_dialogue
        assert isinstance(response_message.transaction_receipt, TransactionReceipt)
        assert response_message.transaction_receipt.receipt is not None
        assert response_message.transaction_receipt.transaction is not None
        assert (
            response_message.transaction_receipt.ledger_id
            == request.transaction_digest.ledger_id  # type: ignore
        )
        assert LedgerApis.is_transaction_settled(
            response_message.transaction_receipt.ledger_id,
            response_message.transaction_receipt.receipt,
        ), "Transaction not settled."

    @pytest.mark.asyncio
    async def test_unsupported_protocol(
        self, ledger_apis_connection: LedgerConnection
    ) -> None:
        """Test fail on protocol not supported."""
        envelope = Envelope(
            to=str(ledger_apis_connection.connection_id),
            sender="test/skill:0.1.0",
            protocol_specification_id=PublicId.from_str("author/package_name:0.1.0"),
            message=b"message",
        )
        with pytest.raises(ValueError, match="Protocol not supported"):
            ledger_apis_connection._schedule_request(envelope)

    @pytest.mark.asyncio
    async def test_no_balance(
        self,
    ) -> None:
        """Test no balance."""
        dispatcher = LedgerApiRequestDispatcher(
            AsyncState(), connection_id=LedgerConnection.connection_id
        )
        mock_api = Mock()
        message = LedgerApiMessage(
            performative=LedgerApiMessage.Performative.GET_BALANCE,  # type: ignore
            dialogue_reference=dispatcher.dialogues.new_self_initiated_dialogue_reference(),
            ledger_id=EthereumCrypto.identifier,
            address="test",
        )
        message.to = dispatcher.dialogues.self_address
        message.sender = "test"
        dialogue = cast(
            Optional[LedgerApiDialogue], dispatcher.dialogues.update(message)
        )
        assert dialogue is not None

        mock_api.get_balance.return_value = None
        msg = dispatcher.get_balance(mock_api, message, dialogue)
        assert msg.performative == LedgerApiMessage.Performative.ERROR

    @pytest.mark.asyncio
    async def test_no_raw_tx(
        self,
    ) -> None:
        """Test no raw tx returned."""
        dispatcher = LedgerApiRequestDispatcher(
            AsyncState(), connection_id=LedgerConnection.connection_id
        )
        mock_api = Mock()
        message = LedgerApiMessage(
            performative=LedgerApiMessage.Performative.GET_RAW_TRANSACTION,  # type: ignore
            dialogue_reference=dispatcher.dialogues.new_self_initiated_dialogue_reference(),
            terms=Terms(
                ledger_id=EthereumCrypto.identifier,
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
        message.to = dispatcher.dialogues.self_address
        message.sender = "test"
        dialogue = cast(
            Optional[LedgerApiDialogue], dispatcher.dialogues.update(message)
        )
        assert dialogue is not None

        mock_api.get_transfer_transaction.return_value = None
        msg = dispatcher.get_raw_transaction(mock_api, message, dialogue)
        assert msg.performative == LedgerApiMessage.Performative.ERROR

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "failing_ledger_method_name",
        ("get_transaction_receipt", "is_transaction_settled", "get_transaction"),
    )
    @pytest.mark.parametrize("retries", (0, 5, 20))
    @pytest.mark.parametrize("retry_timeout", (0.1,))
    @pytest.mark.parametrize("ledger_raise_error", (True, False))
    async def test_attempts_get_transaction_receipt(
        self,
        failing_ledger_method_name: str,
        retries: int,
        retry_timeout: float,
        ledger_raise_error: bool,
    ) -> None:
        """Test retry and sleep."""
        dispatcher = LedgerApiRequestDispatcher(
            AsyncState(ConnectionStates.connected),
            connection_id=LedgerConnection.connection_id,
        )
        mock_api = Mock()
        message = LedgerApiMessage(
            performative=LedgerApiMessage.Performative.GET_TRANSACTION_RECEIPT,  # type: ignore
            dialogue_reference=dispatcher.dialogues.new_self_initiated_dialogue_reference(),
            transaction_digest=TransactionDigest("asdad", "sdfdsf"),
        )
        message.to = dispatcher.dialogues.self_address
        message.sender = "test"
        dialogue = dispatcher.dialogues.update(message)
        assert dialogue is not None
        assert isinstance(dialogue, LedgerApiDialogue)

        mock_api.is_transaction_settled.return_value = (
            True if failing_ledger_method_name == "get_transaction" else False
        )
        failing_ledger_method = getattr(mock_api, failing_ledger_method_name)
        if (
            ledger_raise_error
            and failing_ledger_method_name != "is_transaction_settled"
        ):
            failing_ledger_method.side_effect = ValueError()
        elif failing_ledger_method_name != "is_transaction_settled":
            failing_ledger_method.return_value = None

        with patch.object(dispatcher, "retry_attempts", retries):
            with patch.object(dispatcher, "retry_timeout", retry_timeout):
                msg = await dispatcher.get_transaction_receipt(
                    mock_api, message, dialogue
                )

        assert (
            msg.performative == LedgerApiMessage.Performative.ERROR
        ), "performative should be `ERROR`, please revisit the test's implementation."
        times_called = failing_ledger_method.call_count
        expected_times = retries
        assert times_called == expected_times, "Tried more times than expected!"

    @pytest.mark.asyncio
    @ledger_ids
    async def test_get_transaction_receipt_node_blocking(
        self,
        ledger_id: str,
        address: str,
        ledger_apis_connection: LedgerConnection,
        update_default_ethereum_ledger_api: None,
        ethereum_testnet_config: Dict,
    ) -> None:
        """Test retry strategy when the node is blocking."""
        retry_attempts = expected_times_called = 2
        retry_timeout = 0.001
        blocking_duration = 1

        # the retry strategy's total duration is an arithmetic progression
        expected_duration = sum(i * retry_timeout for i in range(retry_attempts))
        assert expected_duration < blocking_duration, (
            "The purpose of this test is to check whether the retry strategy works if a node is blocking."
            f"Therefore, the blocking time ({blocking_duration}) must be larger than the expected duration "
            f"({expected_duration}) of the retry strategy."
        )

        ledger_api_dialogues = LedgerApiDialogues(SOME_SKILL_ID)
        request, ledger_api_dialogue = ledger_api_dialogues.create(
            counterparty=str(ledger_apis_connection.connection_id),
            performative=LedgerApiMessage.Performative.GET_TRANSACTION_RECEIPT,  # type: ignore
            ledger_id=ledger_id,
            address=address,
            transaction_digest=TransactionDigest(ledger_id="ethereum", body="tx_hash"),
        )
        envelope = Envelope(
            to=request.to,
            sender=request.sender,
            message=request,
        )

        with patch.object(
            ledger_apis_connection._ledger_dispatcher, "retry_attempts", retry_attempts
        ), patch.object(
            ledger_apis_connection._ledger_dispatcher, "retry_timeout", retry_timeout
        ), patch.object(
            Eth,
            "get_transaction_receipt",
            side_effect=lambda *_: time.sleep(blocking_duration),
        ) as get_transaction_receipt_mock:
            await ledger_apis_connection.send(envelope)

            try:
                await asyncio.wait_for(
                    ledger_apis_connection.receive(), timeout=blocking_duration
                )
            except asyncio.exceptions.TimeoutError:
                raise AssertionError(
                    "The retry strategy did not finish before the given `blocking_duration`, "
                    "which suggests that the ledger api's call was also blocked, "
                    "and the dispatcher was waiting for its response."
                )

            actual_times_called = get_transaction_receipt_mock.call_count
            assert (
                actual_times_called == expected_times_called
            ), f"Tried {actual_times_called} times, {expected_times_called} were expected!"
