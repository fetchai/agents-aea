# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 fetchai
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

"""Test dialogues module for state_update protocol."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,redefined-builtin
from aea.test_tools.test_protocol import BaseProtocolDialoguesTestCase

from packages.fetchai.protocols.state_update.dialogues import (
    StateUpdateDialogue,
    StateUpdateDialogues,
)
from packages.fetchai.protocols.state_update.message import StateUpdateMessage


class TestDialoguesStateUpdate(BaseProtocolDialoguesTestCase):
    """Test for the 'state_update' protocol dialogues."""

    MESSAGE_CLASS = StateUpdateMessage

    DIALOGUE_CLASS = StateUpdateDialogue

    DIALOGUES_CLASS = StateUpdateDialogues

    ROLE_FOR_THE_FIRST_MESSAGE = StateUpdateDialogue.Role.DECISION_MAKER  # CHECK

    def make_message_content(self) -> dict:
        """Make a dict with message contruction content for dialogues.create."""
        return dict(
            performative=StateUpdateMessage.Performative.INITIALIZE,
            exchange_params_by_currency_id={"some str": 1.4},
            utility_params_by_good_id={"some str": 1.4},
            amount_by_currency_id={"some str": 12},
            quantities_by_good_id={"some str": 12},
        )
