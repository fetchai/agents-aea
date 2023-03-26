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

"""This module contains tests for transaction."""
# pylint: skip-file

from typing import List, Type

from aea_ledger_cosmos import CosmosCrypto

from aea.helpers.transaction.base import (
    RawMessage,
    RawTransaction,
    SignedMessage,
    SignedTransaction,
    Terms,
)
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue
from aea.protocols.dialogue.base import Dialogues
from aea.test_tools.test_protocol import (
    BaseProtocolDialoguesTestCase,
    BaseProtocolMessagesTestCase,
)

from packages.open_aea.protocols.signing.dialogues import (
    SigningDialogue as BaseSigningDialogue,
)
from packages.open_aea.protocols.signing.dialogues import (
    SigningDialogues as BaseSigningDialogues,
)
from packages.open_aea.protocols.signing.message import SigningMessage


class TestMessages(BaseProtocolMessagesTestCase):
    """Base class to test message construction for the protocol."""

    MESSAGE_CLASS = SigningMessage

    ledger_id = CosmosCrypto.identifier
    terms = Terms(
        ledger_id=ledger_id,
        sender_address="address1",
        counterparty_address="address2",
        amount_by_currency_id={"FET": -2},
        quantities_by_good_id={"good_id": 10},
        is_sender_payable_tx_fee=True,
        nonce="transaction nonce",
    )

    def build_messages(self) -> List[SigningMessage]:  # type: ignore[override]
        """Build the messages to be used for testing."""
        return [
            SigningMessage(
                performative=SigningMessage.Performative.SIGN_TRANSACTION,
                terms=self.terms,
                raw_transaction=RawTransaction(self.ledger_id, {"tx": "transaction"}),
            ),
            SigningMessage(
                performative=SigningMessage.Performative.SIGN_MESSAGE,
                terms=self.terms,
                raw_message=RawMessage(self.ledger_id, b"message"),
            ),
            SigningMessage(
                performative=SigningMessage.Performative.SIGNED_TRANSACTION,
                message_id=2,
                target=1,
                signed_transaction=SignedTransaction(
                    self.ledger_id, {"sig": "signature"}
                ),
            ),
            SigningMessage(
                performative=SigningMessage.Performative.SIGNED_MESSAGE,
                message_id=2,
                target=1,
                signed_message=SignedMessage(self.ledger_id, "message"),
            ),
            SigningMessage(
                performative=SigningMessage.Performative.ERROR,
                message_id=2,
                target=1,
                error_code=SigningMessage.ErrorCode.UNSUCCESSFUL_MESSAGE_SIGNING,
            ),
        ]

    def build_inconsistent(self) -> List[SigningMessage]:  # type: ignore[override]
        """Build inconsistent messages to be used for testing."""
        return [
            SigningMessage(
                performative=SigningMessage.Performative.SIGN_TRANSACTION,
                terms=self.terms,
            ),
            SigningMessage(
                performative=SigningMessage.Performative.SIGN_TRANSACTION,
                raw_transaction=RawTransaction(self.ledger_id, {"tx": "transaction"}),
            ),
            SigningMessage(
                performative=SigningMessage.Performative.ERROR,
                message_id=2,
                target=1,
            ),
        ]


class TestDialogues(BaseProtocolDialoguesTestCase):
    """Test dialogues."""

    MESSAGE_CLASS: Type[Message] = SigningMessage
    DIALOGUE_CLASS: Type[BaseDialogue] = BaseSigningDialogue
    DIALOGUES_CLASS: Type[Dialogues] = BaseSigningDialogues
    ROLE_FOR_THE_FIRST_MESSAGE = BaseSigningDialogue.Role.SKILL

    def make_message_content(self) -> dict:
        """Make a dict with message contruction content for dialogues.create."""
        return dict(
            performative=SigningMessage.Performative.SIGN_TRANSACTION,
            terms=Terms(
                ledger_id="ledger_id",
                sender_address="address1",
                counterparty_address="address2",
                amount_by_currency_id={"FET": -2},
                quantities_by_good_id={"good_id": 10},
                is_sender_payable_tx_fee=True,
                nonce="transaction nonce",
            ),
            raw_transaction=RawTransaction("ledger_id", {"tx": "transaction"}),
        )
