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

"""Test dialogues module for ledger_api protocol."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,redefined-builtin
from aea.test_tools.test_protocol import BaseProtocolDialoguesTestCase

from packages.valory.protocols.ledger_api.dialogues import (
    LedgerApiDialogue,
    LedgerApiDialogues,
)
from packages.valory.protocols.ledger_api.message import LedgerApiMessage


class TestDialoguesLedgerApi(BaseProtocolDialoguesTestCase):
    """Test for the 'ledger_api' protocol dialogues."""

    MESSAGE_CLASS = LedgerApiMessage

    DIALOGUE_CLASS = LedgerApiDialogue

    DIALOGUES_CLASS = LedgerApiDialogues

    ROLE_FOR_THE_FIRST_MESSAGE = LedgerApiDialogue.Role.AGENT  # CHECK

    def make_message_content(self) -> dict:
        """Make a dict with message contruction content for dialogues.create."""
        return dict(
            performative=LedgerApiMessage.Performative.GET_BALANCE,
            ledger_id="some str",
            address="some str",
        )
