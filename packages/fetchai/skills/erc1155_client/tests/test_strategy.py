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
"""This module contains the tests of the strategy class of the erc1155_client skill."""
# pylint: skip-file

from aea.helpers.search.models import Constraint, ConstraintType, Query

from packages.fetchai.skills.erc1155_client.strategy import (
    CONTRACT_ID,
    SIMPLE_SERVICE_MODEL,
)
from packages.fetchai.skills.erc1155_client.tests.intermediate_class import (
    ERC1155ClientTestCase,
)


class TestStrategy(ERC1155ClientTestCase):
    """Test Strategy of erc1155_client."""

    def test_properties(self):
        """Test the properties of Strategy class."""
        assert self.strategy.ledger_id == self.skill.skill_context.default_ledger_id
        assert self.strategy.contract_id == str(CONTRACT_ID)

    def test_get_location_and_service_query(self):
        """Test the get_location_and_service_query method of the Strategy class."""
        query = self.strategy.get_location_and_service_query()

        assert type(query) == Query
        assert len(query.constraints) == 2
        assert query.model is None

        location_constraint = Constraint(
            "location",
            ConstraintType(
                "distance", (self.strategy._agent_location, self.search_radius)
            ),
        )
        assert query.constraints[0] == location_constraint

        service_key_constraint = Constraint(
            self.search_query["search_key"],
            ConstraintType(
                self.search_query["constraint_type"],
                self.search_query["search_value"],
            ),
        )
        assert query.constraints[1] == service_key_constraint

    def test_get_service_query(self):
        """Test the get_service_query method of the Strategy class."""
        query = self.strategy.get_service_query()

        assert type(query) == Query
        assert len(query.constraints) == 1

        assert query.model == SIMPLE_SERVICE_MODEL

        service_key_constraint = Constraint(
            self.search_query["search_key"],
            ConstraintType(
                self.search_query["constraint_type"],
                self.search_query["search_value"],
            ),
        )
        assert query.constraints[0] == service_key_constraint
