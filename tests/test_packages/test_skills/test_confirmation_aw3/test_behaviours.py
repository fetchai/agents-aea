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
"""This module contains the tests of the behaviour classes of the confirmation aw3 skill."""

from pathlib import Path
from typing import cast
from unittest.mock import patch

from aea.helpers.search.models import (
    Attribute,
    Constraint,
    ConstraintType,
    DataModel,
    Query,
)

from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.confirmation_aw3.behaviours import SearchBehaviour
from packages.fetchai.skills.confirmation_aw3.strategy import Strategy

from tests.conftest import ROOT_DIR
from tests.test_packages.test_skills.test_confirmation_aw3.intermediate_class import (
    ConfirmationAW3TestCase,
)


class TestSearchBehaviour(ConfirmationAW3TestCase):
    """Test search behaviour of confirmation aw3."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "confirmation_aw3")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()

        cls.search_behaviour = cast(
            SearchBehaviour, cls._skill.skill_context.behaviours.search
        )
        cls.strategy = cast(Strategy, cls._skill.skill_context.strategy)

    def test_act(self):
        """Test the act method of the transaction behaviour."""
        # setup
        self.strategy.is_searching = True

        mock_query = Query(
            [Constraint("some_attribute", ConstraintType("==", "some_service"))],
            DataModel(
                "some_name",
                [
                    Attribute(
                        "some_attribute", str, False, "Some attribute descriptions."
                    )
                ],
            ),
        )

        # operation
        with patch.object(self.strategy, "update_search_query_params") as mock_update:
            with patch.object(
                self.strategy, "get_location_and_service_query", return_value=mock_query
            ):
                self.search_behaviour.act()

        # after
        self.assert_quantity_in_outbox(1)

        mock_update.assert_called_once()

        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=OefSearchMessage,
            performative=OefSearchMessage.Performative.SEARCH_SERVICES,
            to=self.skill.skill_context.search_service_address,
            sender=str(self.skill.skill_context.skill_id),
            query=mock_query,
        )
        assert has_attributes, error_str
