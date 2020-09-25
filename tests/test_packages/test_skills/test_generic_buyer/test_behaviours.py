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
"""This module contains test case classes based on pytest for AEA end-to-end testing."""

from pathlib import Path
from typing import cast

from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.connections.ledger.base import CONNECTION_ID as LEDGER_PUBLIC_ID
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.skills.generic_buyer.behaviours import GenericSearchBehaviour
from packages.fetchai.skills.generic_buyer.strategy import GenericStrategy

from tests.conftest import ROOT_DIR


FETCHAI = "fetchai"


class TestSkillBehaviour(BaseSkillTestCase):
    """Test behaviours of generic buyer."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "generic_buyer")

    def test_search_behaviour_setup_a(self):
        """Test the setup method of the search behaviour."""
        outbox = self.skill.skill_context.outbox
        search_behaviour = cast(
            GenericSearchBehaviour, self.skill.skill_context.behaviours.search
        )

        assert outbox.empty()
        expected_performative = LedgerApiMessage.Performative.GET_BALANCE
        expected_counterparty = str(LEDGER_PUBLIC_ID)
        expected_ledger_id = FETCHAI
        expected_address = self.skill.skill_context.agent_address

        search_behaviour.setup()

        assert self.get_quantity_in_outbox() == 1
        actual_message = self.get_message_from_outbox()
        assert type(actual_message) == LedgerApiMessage
        assert actual_message.performative == expected_performative
        assert actual_message.to == expected_counterparty
        assert actual_message.ledger_id == expected_ledger_id
        assert actual_message.address == expected_address

    def test_search_behaviour_setup_b(self):
        """Test the setup method of the search behaviour."""
        outbox = self.skill.skill_context.outbox
        strategy = cast(GenericStrategy, self.skill.skill_context.strategy)
        strategy._is_ledger_tx = False
        search_behaviour = cast(
            GenericSearchBehaviour, self.skill.skill_context.behaviours.search
        )
        assert outbox.empty()
        assert not strategy.is_searching
        search_behaviour.setup()
        assert outbox.empty()
        assert strategy.is_searching
