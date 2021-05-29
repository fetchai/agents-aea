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
"""This module contains the tests of the strategy class of the aries_alice skill."""

from aea.helpers.search.generic import (
    AGENT_LOCATION_MODEL,
    AGENT_PERSONALITY_MODEL,
    AGENT_REMOVE_SERVICE_MODEL,
    AGENT_SET_SERVICE_MODEL,
)
from aea.helpers.search.models import Description, Location

from tests.test_packages.test_skills.test_aries_alice.intermediate_class import (
    AriesAliceTestCase,
)


class TestStrategy(AriesAliceTestCase):
    """Test Strategy of aries_alice."""

    def test_properties(self):
        """Test the properties of Strategy class."""
        assert self.strategy.admin_host == self.admin_host
        assert self.strategy.admin_port == self.admin_port
        assert self.strategy.admin_url == f"http://{self.admin_host}:{self.admin_port}"

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
        """Test the get_register_personality_description method of the Strategy class."""
        description = self.strategy.get_register_personality_description()

        assert type(description) == Description
        assert description.data_model is AGENT_PERSONALITY_MODEL
        assert description.values.get("piece", "") == self.personality_data["piece"]
        assert description.values.get("value", "") == self.personality_data["value"]

    def test_get_register_classification_description(self):
        """Test the get_register_classification_description method of the Strategy class."""
        description = self.strategy.get_register_classification_description()

        assert type(description) == Description
        assert description.data_model is AGENT_PERSONALITY_MODEL
        assert description.values.get("piece", "") == self.classification["piece"]
        assert description.values.get("value", "") == self.classification["value"]

    def test_get_unregister_service_description(self):
        """Test the get_unregister_service_description method of the Strategy class."""
        description = self.strategy.get_unregister_service_description()

        assert type(description) == Description
        assert description.data_model is AGENT_REMOVE_SERVICE_MODEL
        assert description.values.get("key", "") == self.service_data["key"]
