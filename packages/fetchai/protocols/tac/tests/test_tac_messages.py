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

"""Test messages module for tac protocol."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,redefined-builtin
from typing import List

from aea.test_tools.test_protocol import BaseProtocolMessagesTestCase

from packages.fetchai.protocols.tac.custom_types import ErrorCode
from packages.fetchai.protocols.tac.message import TacMessage


class TestMessageTac(BaseProtocolMessagesTestCase):
    """Test for the 'tac' protocol message."""

    MESSAGE_CLASS = TacMessage

    def build_messages(self) -> List[TacMessage]:  # type: ignore[override]
        """Build the messages to be used for testing."""
        return [
            TacMessage(
                performative=TacMessage.Performative.REGISTER,
                agent_name="some str",
            ),
            TacMessage(
                performative=TacMessage.Performative.UNREGISTER,
            ),
            TacMessage(
                performative=TacMessage.Performative.TRANSACTION,
                transaction_id="some str",
                ledger_id="some str",
                sender_address="some str",
                counterparty_address="some str",
                amount_by_currency_id={"some str": 12},
                fee_by_currency_id={"some str": 12},
                quantities_by_good_id={"some str": 12},
                nonce="some str",
                sender_signature="some str",
                counterparty_signature="some str",
            ),
            TacMessage(
                performative=TacMessage.Performative.CANCELLED,
            ),
            TacMessage(
                performative=TacMessage.Performative.GAME_DATA,
                amount_by_currency_id={"some str": 12},
                exchange_params_by_currency_id={"some str": 1.0},
                quantities_by_good_id={"some str": 12},
                utility_params_by_good_id={"some str": 1.0},
                fee_by_currency_id={"some str": 12},
                agent_addr_to_name={"some str": "some str"},
                currency_id_to_name={"some str": "some str"},
                good_id_to_name={"some str": "some str"},
                version_id="some str",
                info={"some str": "some str"},
            ),
            TacMessage(
                performative=TacMessage.Performative.TRANSACTION_CONFIRMATION,
                transaction_id="some str",
                amount_by_currency_id={"some str": 12},
                quantities_by_good_id={"some str": 12},
            ),
            TacMessage(
                performative=TacMessage.Performative.TAC_ERROR,
                error_code=ErrorCode.TRANSACTION_NOT_MATCHING,
                info={"some str": "some str"},
            ),
        ]

    def build_inconsistent(self) -> List[TacMessage]:  # type: ignore[override]
        """Build inconsistent messages to be used for testing."""
        return [
            TacMessage(
                performative=TacMessage.Performative.REGISTER,
                # skip content: agent_name
            ),
            TacMessage(
                performative=TacMessage.Performative.TRANSACTION,
                # skip content: transaction_id
                ledger_id="some str",
                sender_address="some str",
                counterparty_address="some str",
                amount_by_currency_id={"some str": 12},
                fee_by_currency_id={"some str": 12},
                quantities_by_good_id={"some str": 12},
                nonce="some str",
                sender_signature="some str",
                counterparty_signature="some str",
            ),
            TacMessage(
                performative=TacMessage.Performative.GAME_DATA,
                # skip content: amount_by_currency_id
                exchange_params_by_currency_id={"some str": 1.4},
                quantities_by_good_id={"some str": 12},
                utility_params_by_good_id={"some str": 1.4},
                fee_by_currency_id={"some str": 12},
                agent_addr_to_name={"some str": "some str"},
                currency_id_to_name={"some str": "some str"},
                good_id_to_name={"some str": "some str"},
                version_id="some str",
                info={"some str": "some str"},
            ),
            TacMessage(
                performative=TacMessage.Performative.TRANSACTION_CONFIRMATION,
                # skip content: transaction_id
                amount_by_currency_id={"some str": 12},
                quantities_by_good_id={"some str": 12},
            ),
            TacMessage(
                performative=TacMessage.Performative.TAC_ERROR,
                # skip content: error_code
                info={"some str": "some str"},
            ),
        ]
