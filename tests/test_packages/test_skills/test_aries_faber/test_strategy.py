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
"""This module contains the tests of the strategy class of the aries_faber skill."""

import pytest

from aea.exceptions import AEAEnforceError
from aea.helpers.search.models import Constraint, ConstraintType, Query

from tests.test_packages.test_skills.test_aries_faber.intermediate_class import (
    AriesFaberTestCase,
)


class TestStrategy(AriesFaberTestCase):
    """Test Strategy of aries_faber."""

    def test_properties(self):
        """Test the properties of Strategy class."""
        assert self.strategy.admin_host == self.admin_host
        assert self.strategy.admin_port == self.admin_port
        assert self.strategy.ledger_url == self.ledger_url
        assert self.strategy.admin_url == f"http://{self.admin_host}:{self.admin_port}"
        assert self.strategy.alice_aea_address == ""
        self.strategy.alice_aea_address = "some_address"
        assert self.strategy.alice_aea_address == "some_address"
        assert self.strategy.is_searching is False
        with pytest.raises(AEAEnforceError, match="Can only set bool on is_searching!"):
            self.strategy.is_searching = "some_value"
        self.strategy.is_searching = True
        assert self.strategy.is_searching is True

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
                self.search_query["constraint_type"], self.search_query["search_value"],
            ),
        )
        assert query.constraints[1] == service_key_constraint
