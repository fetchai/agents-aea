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
"""This module contains the tests of the strategy class of the simple_service_registration skill."""

from pathlib import Path

import pytest

from aea.exceptions import AEAEnforceError
from aea.helpers.search.models import Description, Location
from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.skills.simple_service_registration.strategy import (
    AGENT_LOCATION_MODEL,
    AGENT_PERSONALITY_MODEL,
    AGENT_REMOVE_SERVICE_MODEL,
    AGENT_SET_SERVICE_MODEL,
    Strategy,
)

from tests.conftest import ROOT_DIR


class TestStrategy(BaseSkillTestCase):
    """Test Strategy of simple_service_registration."""

    path_to_skill = Path(
        ROOT_DIR, "packages", "fetchai", "skills", "simple_service_registration"
    )

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.location = {"longitude": 0.1270, "latitude": 51.5194}
        cls.service_data = {"key": "seller_service", "value": "generic_service"}

        cls.strategy = Strategy(
            location=cls.location,
            service_data=cls.service_data,
            name="strategy",
            skill_context=cls._skill.skill_context,
        )

    def test__init__(self):
        """Test the __init__ method of the Strategy class."""
        assert self.strategy._remove_service_data == {"key": self.service_data["key"]}

    def test__init__exception(self):
        """Test the __init__ method of the Strategy class where exception is raise."""
        incorrect_service_data_1 = {"key": "seller_service"}
        incorrect_service_data_2 = {
            "incorrect_key": "seller_service",
            "value": "generic_service",
        }
        incorrect_service_data_3 = {
            "key": "seller_service",
            "incorrect_key": "generic_service",
        }
        with pytest.raises(
            AEAEnforceError, match="service_data must contain keys `key` and `value`"
        ):
            Strategy(
                location=self.location, service_data=incorrect_service_data_1,
            )

        with pytest.raises(
            AEAEnforceError, match="service_data must contain keys `key` and `value`"
        ):
            Strategy(
                location=self.location, service_data=incorrect_service_data_2,
            )

        with pytest.raises(
            AEAEnforceError, match="service_data must contain keys `key` and `value`"
        ):
            Strategy(
                location=self.location, service_data=incorrect_service_data_3,
            )

    def test_get_location_description(self):
        """Test the get_location_description method of the Strategy class."""
        description = self.strategy.get_location_description()

        assert type(description) == Description
        assert description.data_model is AGENT_LOCATION_MODEL
        assert description.values.get("location", "") == Location(
            latitude=self.location["latitude"], longitude=self.location["longitude"]
        )

    def test_get_register_service_description(self):
        """Test the get_register_service_description method of the Strategy class."""
        description = self.strategy.get_register_service_description()

        assert type(description) == Description
        assert description.data_model is AGENT_SET_SERVICE_MODEL
        assert description.values.get("key", "") == self.service_data["key"]
        assert description.values.get("value", "") == self.service_data["value"]

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
        assert description.values.get("value", "") == "seller"

    def test_get_unregister_service_description(self):
        """Test the get_unregister_service_description method of the Strategy class."""
        description = self.strategy.get_unregister_service_description()

        assert type(description) == Description
        assert description.data_model is AGENT_REMOVE_SERVICE_MODEL
        assert description.values.get("key", "") == self.service_data["key"]
