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

"""This module contains tests for transaction."""

from aea.configurations.base import PublicId
from aea.decision_maker.messages.transaction import TransactionMessage


class TestTransaction:
    """Test the transaction module."""

    def test_message_consistency(self):
        """Test for an error in consistency of a message."""
        assert TransactionMessage(
            performative=TransactionMessage.Performative.SUCCESSFUL_SETTLEMENT,
            skill_callback_ids=[PublicId.from_str("author/skill:0.1.0")],
            tx_id="transaction0",
            tx_sender_addr="pk1",
            tx_counterparty_addr="pk2",
            tx_amount_by_currency_id={"FET": -2},
            tx_sender_fee=0,
            tx_counterparty_fee=0,
            tx_quantities_by_good_id={"GOOD_ID": 10},
            ledger_id="fetchai",
            info={"some_string": [1, 2]},
            tx_digest="some_string",
        )
        tx_msg = TransactionMessage(
            performative=TransactionMessage.Performative.SUCCESSFUL_SETTLEMENT,
            skill_callback_ids=[PublicId.from_str("author/skill:0.1.0")],
            tx_id="transaction0",
            tx_sender_addr="pk1",
            tx_counterparty_addr="pk2",
            tx_amount_by_currency_id={"FET": -2},
            tx_sender_fee=0,
            tx_counterparty_fee=0,
            tx_quantities_by_good_id={"GOOD_ID": 10},
            ledger_id="ethereum",
            info={"some_string": [1, 2]},
            tx_digest="some_string",
        )
        assert not tx_msg._is_consistent()
        tx_msg = TransactionMessage(
            performative=TransactionMessage.Performative.SUCCESSFUL_SETTLEMENT,
            skill_callback_ids=[PublicId.from_str("author/skill:0.1.0")],
            tx_id="transaction0",
            tx_sender_addr="pk",
            tx_counterparty_addr="pk",
            tx_amount_by_currency_id={"Unknown": 2},
            tx_sender_fee=0,
            tx_counterparty_fee=0,
            tx_quantities_by_good_id={"Unknown": 10},
            ledger_id="fetchai",
            info={"info": "info_value"},
        )
        assert not tx_msg._is_consistent()
