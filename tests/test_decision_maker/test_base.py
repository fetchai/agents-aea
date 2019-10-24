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

"""This module contains tests for decision_maker."""
from queue import Queue

import pytest

from aea.decision_maker.base import OwnershipState, Preferences, DecisionMaker
from aea.mail.base import OutBox  # , Envelope

MAX_REACTIONS = 10

class TestDecisionMakerBase:
    """Test the base.py for DecisionMaker."""
    @classmethod
    def setup(cls):
        """Initialise the class."""
        cls.ownership_state = OwnershipState()
        cls.preferences = Preferences()
        cls.outbox = OutBox(Queue())
        cls.decision_maker = DecisionMaker(MAX_REACTIONS, cls.outbox)

    def test_properties(self):
        """Test the assertion error for currency_holdings."""
        with pytest.raises(AssertionError):
            self.ownership_state.currency_holdings
