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

"""Test messages module for state_update protocol."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,redefined-builtin
from typing import List

from aea.test_tools.test_protocol import BaseProtocolMessagesTestCase

from packages.fetchai.protocols.state_update.message import StateUpdateMessage


class TestMessageStateUpdate(BaseProtocolMessagesTestCase):
    """Test for the 'state_update' protocol message."""

    MESSAGE_CLASS = StateUpdateMessage

    def build_messages(self) -> List[StateUpdateMessage]:  # type: ignore[override]
        """Build the messages to be used for testing."""
        return [
            StateUpdateMessage(
                performative=StateUpdateMessage.Performative.INITIALIZE,
                exchange_params_by_currency_id={"some str": 1.0},
                utility_params_by_good_id={"some str": 1.0},
                amount_by_currency_id={"some str": 12},
                quantities_by_good_id={"some str": 12},
            ),
            StateUpdateMessage(
                performative=StateUpdateMessage.Performative.APPLY,
                amount_by_currency_id={"some str": 12},
                quantities_by_good_id={"some str": 12},
            ),
            StateUpdateMessage(
                performative=StateUpdateMessage.Performative.END,
            ),
        ]

    def build_inconsistent(self) -> List[StateUpdateMessage]:  # type: ignore[override]
        """Build inconsistent messages to be used for testing."""
        return [
            StateUpdateMessage(
                performative=StateUpdateMessage.Performative.INITIALIZE,
                # skip content: exchange_params_by_currency_id
                utility_params_by_good_id={"some str": 1.4},
                amount_by_currency_id={"some str": 12},
                quantities_by_good_id={"some str": 12},
            ),
            StateUpdateMessage(
                performative=StateUpdateMessage.Performative.APPLY,
                # skip content: amount_by_currency_id
                quantities_by_good_id={"some str": 12},
            ),
        ]
