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

from aea.decision_maker.messages.state_update import StateUpdateMessage


class TestStateUpdateMessage:
    """Test the StateUpdateMessage."""

    def test_message_consistency(self):
        """Test for an error in consistency of a message."""
        with pytest.raises(AssertionError):
            good_endowment = {"FET": 2}
            currency_endowment = {"FET": 100.0}
            utility_params = {"Unknown": 20.0}
            exchange_params = {"FET": 10.0}
            assert StateUpdateMessage(currency_endowment=currency_endowment, good_endowment=good_endowment,
                                      utility_params=utility_params, exchange_params=exchange_params)
