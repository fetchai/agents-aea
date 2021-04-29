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
"""This module contains the tests of the strategy class of the simple_aggregation skill."""

from pathlib import Path
from typing import cast

from aea.helpers.search.models import Description
from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.skills.simple_aggregation.strategy import (
    AGENT_PERSONALITY_MODEL,
    AGENT_REMOVE_SERVICE_MODEL,
    AGENT_SET_SERVICE_MODEL,
    AggregationStrategy,
)

from tests.conftest import ROOT_DIR


class TestAggregationStrategy(BaseSkillTestCase):
    """Test AggregationStrategy of simple_aggregation."""

    path_to_skill = Path(
        ROOT_DIR, "packages", "fetchai", "skills", "simple_aggregation"
    )

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.strategy = cast(AggregationStrategy, cls._skill.skill_context.strategy)

    def test_get_register_service_description(self):
        """Test the get_register_service_description method of the GenericStrategy class."""
        description = self.strategy.get_register_service_description()

        assert type(description) == Description
        assert description.data_model is AGENT_SET_SERVICE_MODEL
        assert description.values.get("key", "") == "service"
        assert description.values.get("value", "") == "generic_aggregation_service"

    def test_get_register_personality_description(self):
        """Test the get_register_personality_description method of the GenericStrategy class."""
        description = self.strategy.get_register_personality_description()

        assert type(description) == Description
        assert description.data_model is AGENT_PERSONALITY_MODEL
        assert description.values.get("piece", "") == "genus"
        assert description.values.get("value", "") == "data"

    def test_get_register_classification_description(self):
        """Test the get_register_classification_description method of the GenericStrategy class."""
        description = self.strategy.get_register_classification_description()

        assert type(description) == Description
        assert description.data_model is AGENT_PERSONALITY_MODEL
        assert description.values.get("piece", "") == "classification"
        assert description.values.get("value", "") == "agent"

    def test_get_unregister_service_description(self):
        """Test the get_unregister_service_description method of the GenericStrategy class."""
        description = self.strategy.get_unregister_service_description()

        assert type(description) == Description
        assert description.data_model is AGENT_REMOVE_SERVICE_MODEL
        assert description.values.get("key", "") == "service"
