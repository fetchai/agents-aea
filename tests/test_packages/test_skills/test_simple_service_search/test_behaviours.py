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
"""This module contains the tests of the behaviour class of the simple_service_search skill."""

import logging
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
from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.simple_service_search.behaviours import (
    ServiceSearchBehaviour,
)
from packages.fetchai.skills.simple_service_search.strategy import Strategy

from tests.conftest import ROOT_DIR


class TestServiceSearchBehaviour(BaseSkillTestCase):
    """Test service_search behaviour of simple_service_search."""

    path_to_skill = Path(
        ROOT_DIR, "packages", "fetchai", "skills", "simple_service_search"
    )
    is_agent_to_agent_messages = False

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.search_behaviour = cast(
            ServiceSearchBehaviour, cls._skill.skill_context.behaviours.service_search
        )
        cls.strategy = cast(Strategy, cls._skill.skill_context.strategy)
        cls.logger = cls._skill.skill_context.logger

        cls.query = Query(
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

    def test_setup(self):
        """Test the setup method of the service_search behaviour."""
        assert self.search_behaviour.setup() is None
        self.assert_quantity_in_outbox(0)

    def test_act(self):
        """Test the act method of the service_search behaviour."""
        # operation
        with patch.object(self.strategy, "get_query", return_value=self.query):
            with patch.object(self.logger, "log") as mock_logger:
                self.search_behaviour.act()

        # after
        self.assert_quantity_in_outbox(1)

        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=OefSearchMessage,
            performative=OefSearchMessage.Performative.SEARCH_SERVICES,
            to=self.skill.skill_context.search_service_address,
            sender=str(self.skill.skill_context.skill_id),
            query=self.query,
        )
        assert has_attributes, error_str

        mock_logger.assert_any_call(
            logging.INFO, "sending search request to OEF search node"
        )

    def test_teardown(self):
        """Test the teardown method of the service_search behaviour."""
        assert self.search_behaviour.teardown() is None
        self.assert_quantity_in_outbox(0)
