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

from aea.protocols.state_update.message import StateUpdateMessage


class TestStateUpdateMessage:
    """Test the StateUpdateMessage."""

    def test_message_consistency(self):
        """Test for an error in consistency of a message."""
        currency_endowment = {"FET": 100}
        good_endowment = {"a_good": 2}
        exchange_params = {"FET": 10.0}
        utility_params = {"a_good": 20.0}
        tx_fee = 10
        assert StateUpdateMessage(
            performative=StateUpdateMessage.Performative.INITIALIZE,
            amount_by_currency_id=currency_endowment,
            quantities_by_good_id=good_endowment,
            exchange_params_by_currency_id=exchange_params,
            utility_params_by_good_id=utility_params,
            tx_fee=tx_fee,
        )
        currency_change = {"FET": 10}
        good_change = {"a_good": 1}
        stum = StateUpdateMessage(
            performative=StateUpdateMessage.Performative.APPLY,
            amount_by_currency_id=currency_change,
            quantities_by_good_id=good_change,
        )
        assert stum._is_consistent()
        assert len(stum.valid_performatives) == 2

    def test_message_inconsistency(self):
        """Test for an error in consistency of a message."""
        currency_endowment = {"FET": 100}
        good_endowment = {"a_good": 2}
        exchange_params = {"UNKNOWN": 10.0}
        utility_params = {"a_good": 20.0}
        tx_fee = 10
        stum = StateUpdateMessage(
            performative=StateUpdateMessage.Performative.INITIALIZE,
            amount_by_currency_id=currency_endowment,
            quantities_by_good_id=good_endowment,
            exchange_params_by_currency_id=exchange_params,
            utility_params_by_good_id=utility_params,
            tx_fee=tx_fee,
        )
        assert not stum._is_consistent()
