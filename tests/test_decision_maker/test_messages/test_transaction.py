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
import pytest

from aea.decision_maker.messages.transaction import TransactionMessage


class TestTransaction:
    """Test the transaction module."""

    def test_message_consistency(self):
        """Test for an error in consistency of a message."""
        TransactionMessage(performative="performative",
                           skill_ids=["default"],
                           transaction_id="transaction0",
                           sender="pk1",
                           counterparty="pk2",
                           is_sender_buyer=True,
                           currency_pbk="FET",
                           amount=2,
                           sender_tx_fee=0,
                           counterparty_tx_fee=0,
                           ledger_id="fetchai",
                           quantities_by_good_pbk={"Unknown": 10},
                           info={'some_string': [1, 2]},
                           transaction_digest='some_string')
        with pytest.raises(AssertionError):
            TransactionMessage(performative="performative",
                               skill_ids=["default"],
                               transaction_id="transaction0",
                               sender="pk",
                               counterparty="pk",
                               is_sender_buyer=True,
                               currency_pbk="Unknown",
                               amount=2,
                               sender_tx_fee=0,
                               counterparty_tx_fee=0,
                               ledger_id="fetchai",
                               quantities_by_good_pbk={"Unknown": 10})

    def test_matches(self):
        """Test if the transaction matches with another transaction."""
        msg = TransactionMessage(performative=TransactionMessage.Performative.ACCEPT,
                                 skill_ids=["default"],
                                 transaction_id="transaction0",
                                 sender="agent_1",
                                 counterparty="pk",
                                 is_sender_buyer=True,
                                 currency_pbk="FET",
                                 amount=2,
                                 sender_tx_fee=0,
                                 counterparty_tx_fee=0,
                                 ledger_id="fetchai",
                                 quantities_by_good_pbk={"FET": 10})
        assert not msg.matches(msg), "It shouldn't match since it is the same message."
        assert msg == msg, "It should be equal since is the same message."

        mirrored_message = TransactionMessage(performative=TransactionMessage.Performative.ACCEPT,
                                              skill_ids=["default"],
                                              transaction_id="transaction0",
                                              sender="pk",
                                              counterparty="agent_1",
                                              is_sender_buyer=False,
                                              currency_pbk="FET",
                                              amount=2,
                                              sender_tx_fee=0,
                                              counterparty_tx_fee=0,
                                              ledger_id="fetchai",
                                              quantities_by_good_pbk={"FET": 10})

        assert msg.matches(mirrored_message), "It should match since the messages mirror each other"
