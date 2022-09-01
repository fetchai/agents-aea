# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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
"""This module contains the tests of the behaviour classes of the erc1155_client skill."""
# pylint: skip-file

from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.erc1155_client.behaviours import LEDGER_API_ADDRESS
from packages.fetchai.skills.erc1155_client.tests.intermediate_class import (
    ERC1155ClientTestCase,
)


class TestSearchBehaviour(ERC1155ClientTestCase):
    """Test search behaviour of erc1155_client."""

    def test_setup(self):
        """Test the setup method of the search behaviour."""
        # operation
        self.search_behaviour.setup()

        # after
        self.assert_quantity_in_outbox(1)
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=LedgerApiMessage,
            performative=LedgerApiMessage.Performative.GET_BALANCE,
            to=LEDGER_API_ADDRESS,
            sender=str(self.skill.public_id),
            ledger_id=self.strategy.ledger_id,
            address=self.skill.skill_context.agent_address,
        )
        assert has_attributes, error_str

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
            sender=str(self.skill.public_id),
            query=self.skill.skill_context.strategy.get_location_and_service_query(),
        )
        assert has_attributes, error_str

    def test_act_not_is_searching(self):
        """Test the act method of the search behaviour where is_searching is False."""
        # setup
        self.strategy.is_searching = False

        # operation
        self.search_behaviour.act()

        # after
        self.assert_quantity_in_outbox(0)

    def test_teardown(self):
        """Test the teardown method of the search behaviour."""
        assert self.search_behaviour.teardown() is None
        self.assert_quantity_in_outbox(0)
