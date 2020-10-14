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
"""This module contains the tests of the behaviour classes of the generic buyer skill."""

from pathlib import Path
from typing import cast

from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.connections.ledger.base import CONNECTION_ID as LEDGER_PUBLIC_ID
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.generic_buyer.behaviours import GenericSearchBehaviour
from packages.fetchai.skills.generic_buyer.strategy import GenericStrategy

from tests.conftest import ROOT_DIR


FETCHAI = "fetchai"


class TestSkillBehaviour(BaseSkillTestCase):
    """Test behaviours of generic buyer."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "generic_buyer")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.search_behaviour = cast(
            GenericSearchBehaviour, cls._skill.skill_context.behaviours.search
        )
        cls.strategy = cast(GenericStrategy, cls._skill.skill_context.strategy)

    def test_setup_is_ledger_tx(self):
        """Test the setup method of the search behaviour where is_ledger_tx is True."""
        # operation
        self.search_behaviour.setup()

        # after
        self.assert_quantity_in_outbox(1)
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=LedgerApiMessage,
            performative=LedgerApiMessage.Performative.GET_BALANCE,
            to=str(LEDGER_PUBLIC_ID),
            sender=self.skill.skill_context.agent_address,
            ledger_id=FETCHAI,
            address=self.skill.skill_context.agent_address,
        )
        assert has_attributes, error_str

    def test_setup_not_is_ledger_tx(self):
        """Test the setup method of the search behaviour where is_ledger_tx is False."""
        # setup
        self.strategy._is_ledger_tx = False

        # before
        assert not self.strategy.is_searching

        # operation
        self.search_behaviour.setup()

        # after
        assert self.strategy.is_searching

    def test_act_is_searching(self):
        """Test the act method of the search behaviour where is_searching is True."""
        # setup
        self.strategy._is_searching = True

        # operation
        self.search_behaviour.act()

        # after
        self.assert_quantity_in_outbox(1)
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=OefSearchMessage,
            performative=OefSearchMessage.Performative.SEARCH_SERVICES,
            to=self.skill.skill_context.search_service_address,
            sender=self.skill.skill_context.agent_address,
            query=self.skill.skill_context.strategy.get_location_and_service_query(),
        )
        assert has_attributes, error_str

    def test_act_not_is_searching(self):
        """Test the act method of the search behaviour where is_searching is False."""
        # setup
        self.strategy._is_searching = False

        # operation
        self.search_behaviour.act()

        # after
        self.assert_quantity_in_outbox(0)

    def test_teardown(self):
        """Test the teardown method of the search behaviour."""
        assert self.search_behaviour.teardown() is None
        self.assert_quantity_in_outbox(0)
