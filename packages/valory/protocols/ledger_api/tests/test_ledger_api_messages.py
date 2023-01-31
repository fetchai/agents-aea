# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 valory
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

"""Test messages module for ledger_api protocol."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,redefined-builtin
from typing import List

from aea.test_tools.test_protocol import BaseProtocolMessagesTestCase

from packages.valory.protocols.ledger_api.custom_types import (
    Kwargs,
    RawTransaction,
    SignedTransaction,
    State,
    Terms,
    TransactionDigest,
    TransactionReceipt,
)
from packages.valory.protocols.ledger_api.message import LedgerApiMessage


LEDGER_ID = "ethereum"


class TestMessageLedgerApi(BaseProtocolMessagesTestCase):
    """Test for the 'ledger_api' protocol message."""

    MESSAGE_CLASS = LedgerApiMessage

    ledger_id = LEDGER_ID
    terms = Terms(
        ledger_id=ledger_id,
        sender_address="sender_address",
        counterparty_address="counterparty_address",
        amount_by_currency_id={},
        quantities_by_good_id={},
        nonce="nonce_stub",
    )

    def build_messages(self) -> List[LedgerApiMessage]:  # type: ignore[override]
        """Build the messages to be used for testing."""
        return [
            LedgerApiMessage(
                performative=LedgerApiMessage.Performative.GET_BALANCE,
                ledger_id="some str",
                address="some str",
            ),
            LedgerApiMessage(
                performative=LedgerApiMessage.Performative.GET_RAW_TRANSACTION,
                terms=self.terms,
            ),
            LedgerApiMessage(
                performative=LedgerApiMessage.Performative.SEND_SIGNED_TRANSACTION,
                signed_transaction=SignedTransaction(
                    "some_ledger_id", {"body": "some_body"}
                ),
            ),
            LedgerApiMessage(
                performative=LedgerApiMessage.Performative.GET_TRANSACTION_RECEIPT,
                transaction_digest=TransactionDigest("some_ledger_id", "some_body"),
                retry_timeout=12,
                retry_attempts=12,
            ),
            LedgerApiMessage(
                performative=LedgerApiMessage.Performative.BALANCE,
                ledger_id="some str",
                balance=12,
            ),
            LedgerApiMessage(
                performative=LedgerApiMessage.Performative.RAW_TRANSACTION,
                raw_transaction=RawTransaction("some_ledger_id", {"body": "some_body"}),
            ),
            LedgerApiMessage(
                performative=LedgerApiMessage.Performative.TRANSACTION_DIGEST,
                transaction_digest=TransactionDigest("some_ledger_id", "some_body"),
            ),
            LedgerApiMessage(
                performative=LedgerApiMessage.Performative.TRANSACTION_RECEIPT,
                transaction_receipt=TransactionReceipt(
                    "some_ledger_id",
                    {"key": "some_receipt"},
                    {"key": "some_transaction"},
                ),
            ),
            LedgerApiMessage(
                performative=LedgerApiMessage.Performative.GET_STATE,
                ledger_id="some str",
                callable="some str",
                args=("some str",),
                kwargs=Kwargs({}),
            ),
            LedgerApiMessage(
                performative=LedgerApiMessage.Performative.STATE,
                ledger_id="some str",
                state=State(ledger_id=LEDGER_ID, body={}),  # check it please!
            ),
            LedgerApiMessage(
                performative=LedgerApiMessage.Performative.ERROR,
                code=12,
                message="some str",
                data=b"some_bytes",
            ),
        ]

    def build_inconsistent(self) -> List[LedgerApiMessage]:  # type: ignore[override]
        """Build inconsistent messages to be used for testing."""
        return [
            LedgerApiMessage(
                performative=LedgerApiMessage.Performative.GET_BALANCE,
                # skip content: ledger_id
                address="some str",
            ),
            LedgerApiMessage(
                performative=LedgerApiMessage.Performative.GET_RAW_TRANSACTION,
                # skip content: terms
            ),
            LedgerApiMessage(
                performative=LedgerApiMessage.Performative.SEND_SIGNED_TRANSACTION,
                # skip content: signed_transaction
            ),
            LedgerApiMessage(
                performative=LedgerApiMessage.Performative.GET_TRANSACTION_RECEIPT,
                # skip content: transaction_digest
                retry_timeout=12,
                retry_attempts=12,
            ),
            LedgerApiMessage(
                performative=LedgerApiMessage.Performative.BALANCE,
                # skip content: ledger_id
                balance=12,
            ),
            LedgerApiMessage(
                performative=LedgerApiMessage.Performative.RAW_TRANSACTION,
                # skip content: raw_transaction
            ),
            LedgerApiMessage(
                performative=LedgerApiMessage.Performative.TRANSACTION_DIGEST,
                # skip content: transaction_digest
            ),
            LedgerApiMessage(
                performative=LedgerApiMessage.Performative.TRANSACTION_RECEIPT,
                # skip content: transaction_receipt
            ),
            LedgerApiMessage(
                performative=LedgerApiMessage.Performative.GET_STATE,
                # skip content: ledger_id
                callable="some str",
                args=("some str",),
                kwargs=Kwargs({}),
            ),
            LedgerApiMessage(
                performative=LedgerApiMessage.Performative.STATE,
                # skip content: ledger_id
                state=State(ledger_id=LEDGER_ID, body={}),
            ),
            LedgerApiMessage(
                performative=LedgerApiMessage.Performative.ERROR,
                # skip content: code
                message="some str",
                data=b"some_bytes",
            ),
        ]
