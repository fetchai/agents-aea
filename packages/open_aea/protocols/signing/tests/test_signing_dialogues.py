# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 open_aea
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

"""Test dialogues module for signing protocol."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,redefined-builtin
from aea.test_tools.test_protocol import BaseProtocolDialoguesTestCase

from packages.open_aea.protocols.signing.custom_types import RawTransaction, Terms
from packages.open_aea.protocols.signing.dialogues import (
    SigningDialogue,
    SigningDialogues,
)
from packages.open_aea.protocols.signing.message import SigningMessage


class TestDialoguesSigning(BaseProtocolDialoguesTestCase):
    """Test for the 'signing' protocol dialogues."""

    MESSAGE_CLASS = SigningMessage

    DIALOGUE_CLASS = SigningDialogue

    DIALOGUES_CLASS = SigningDialogues

    ROLE_FOR_THE_FIRST_MESSAGE = SigningDialogue.Role.DECISION_MAKER  # CHECK

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
