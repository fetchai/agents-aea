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
"""This module contains the tests of the strategy class of the simple_service_search skill."""

from pathlib import Path

from aea.helpers.search.models import Constraint, ConstraintType, Query
from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.skills.simple_service_search.strategy import Strategy

from tests.conftest import ROOT_DIR


class TestStrategy(BaseSkillTestCase):
    """Test Strategy of simple_service_search."""

    path_to_skill = Path(
        ROOT_DIR, "packages", "fetchai", "skills", "simple_service_search"
    )

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.mocked_name_of_data = "some_name_for_data"
        cls.mocked_data_1 = (
            b'[{"type_1": "data_1", "type_2": "data_2", "type_3": "data_3"}]'
        )
        cls.mocked_data_2 = (
            b'{"type_1": "data_1", "type_2": "data_2", "type_3": "data_3"}'
        )
        cls.mocked_data_3 = b"some_non_jason_data"

        cls.search_query = {
            "search_key": "seller_service",
            "search_value": "generic_service",
            "constraint_type": "==",
        }
        cls.search_location = {"longitude": 0.1270, "latitude": 51.5194}
        cls.search_radius = 5.0
        cls.shared_state_key = "agents_found"

        cls.strategy = Strategy(
            search_query=cls.search_query,
            search_location=cls.search_location,
            search_radius=cls.search_radius,
            shared_storage_key=cls.shared_state_key,
            name="strategy",
            skill_context=cls._skill.skill_context,
        )

    def test_simple_properties(self):
        """Test simple properties of the Strategy class."""
        assert self.strategy.shared_storage_key == self.shared_state_key

    def test_get_query(self):
        """Test the get_query method of the Strategy class."""
        query = self.strategy.get_query()

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
                self.search_query["constraint_type"], self.search_query["search_value"],
            ),
        )
        assert query.constraints[1] == service_key_constraint
