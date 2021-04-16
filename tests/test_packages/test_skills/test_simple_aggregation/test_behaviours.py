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
"""This module contains the tests of the behaviour classes of the advanced data request skill."""

import logging
from pathlib import Path
from typing import cast
from unittest.mock import patch

from aea_ledger_fetchai import FetchAICrypto

from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.protocols.aggregation.message import AggregationMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.simple_aggregation.behaviours import (
    AggregationBehaviour,
    DEFAULT_SIGNATURE,
    DEFAULT_SOURCE,
    SearchBehaviour,
)
from packages.fetchai.skills.simple_aggregation.strategy import AggregationStrategy

from tests.conftest import ROOT_DIR


DATA_REQUEST_OBS = {"some_quantity": {"value": 100, "decimals": 0}}
OBSERVATION = {
    "value": 100,
    "time": "some_time",
    "signature": DEFAULT_SIGNATURE,
    "source": DEFAULT_SOURCE,
}
LEDGER_ID = FetchAICrypto.identifier
PEERS = ("peer1", "peer2")


class TestAggregationBehaviour(BaseSkillTestCase):
    """Test aggregation behaviour of simple aggregation skill."""

    path_to_skill = Path(
        ROOT_DIR, "packages", "fetchai", "skills", "simple_aggregation"
    )

    @classmethod
    def setup(cls, **kwargs):
        """Setup the test class."""
        super().setup()
        cls.aggregation_behaviour = cast(
            AggregationBehaviour, cls._skill.skill_context.behaviours.aggregation,
        )
        cls.aggregation_strategy = cast(
            AggregationStrategy, cls.aggregation_behaviour.context.strategy,
        )
        cls.aggregation_strategy.url = "some_url"
        cls.aggregation_strategy._quantity_name = "some_quantity"
        cls.agent_address = cls.aggregation_behaviour.context.agent_addresses[LEDGER_ID]

    def test_act(self):
        """Test the act method of the aggregation behaviour."""

        strategy = cast(
            AggregationStrategy, self.aggregation_behaviour.context.strategy
        )

        with patch.object(
            self.aggregation_behaviour.context.logger, "log"
        ) as mock_logger:
            self.aggregation_behaviour.act()

        mock_logger.assert_any_call(
            logging.INFO, "No observation to send",
        )
        self.assert_quantity_in_outbox(0)

        # mock an observation
        self.aggregation_behaviour.context.shared_state[
            "observation"
        ] = DATA_REQUEST_OBS

        strategy.add_peers(PEERS)
        assert all([peer in strategy.peers for peer in PEERS])

        with patch.object(
            self.aggregation_behaviour.context.logger, "log"
        ) as mock_logger:
            self.aggregation_behaviour.act()

        mock_logger.assert_any_call(
            logging.INFO, f"sending observation to peer={PEERS[0]}",
        )
        mock_logger.assert_any_call(
            logging.INFO, f"sending observation to peer={PEERS[1]}",
        )

        obs = strategy.observation
        assert obs["value"] == OBSERVATION["value"]

        # test broadcast_observation
        self.assert_quantity_in_outbox(2)
        msg = cast(AggregationMessage, self.get_message_from_outbox())
        has_attributes, error_str = self.message_has_attributes(
            actual_message=msg,
            message_type=AggregationMessage,
            performative=AggregationMessage.Performative.OBSERVATION,
            value=100,
            source=DEFAULT_SOURCE,
            signature=DEFAULT_SIGNATURE,
        )
        assert has_attributes, error_str


class TestSearchBehaviour(BaseSkillTestCase):
    """Test search behaviour of simple aggregation skill."""

    path_to_skill = Path(
        ROOT_DIR, "packages", "fetchai", "skills", "simple_aggregation"
    )

    @classmethod
    def setup(cls, **kwargs):
        """Setup the test class."""
        super().setup()
        cls.search_behaviour = cast(
            SearchBehaviour, cls._skill.skill_context.behaviours.search,
        )
        cls.aggregation_strategy = cast(
            AggregationStrategy, cls.search_behaviour.context.strategy,
        )
        cls.aggregation_strategy.url = "some_url"
        cls.aggregation_strategy._quantity_name = "some_quantity"
        cls.agent_address = cls.search_behaviour.context.agent_addresses[LEDGER_ID]

    def test_setup(self):
        """Test the setup method of the search behaviour."""

        with patch.object(self.search_behaviour.context.logger, "log") as mock_logger:
            self.search_behaviour.setup()

        mock_logger.assert_any_call(
            logging.INFO, "registering agent on SOEF.",
        )
        mock_logger.assert_any_call(
            logging.INFO, "registering service on SOEF.",
        )

        descriptions = [
            self.aggregation_strategy.get_location_description(),
            self.aggregation_strategy.get_register_service_description(),
            self.aggregation_strategy.get_register_personality_description(),
            self.aggregation_strategy.get_register_classification_description(),
        ]

        # test SOEF messages
        self.assert_quantity_in_outbox(len(descriptions))
        for description in descriptions:
            msg = cast(OefSearchMessage, self.get_message_from_outbox())
            has_attributes, error_str = self.message_has_attributes(
                actual_message=msg,
                message_type=OefSearchMessage,
                performative=OefSearchMessage.Performative.REGISTER_SERVICE,
                service_description=description,
            )
            assert has_attributes, error_str

    def test_act(self):
        """Test the act method of the search behaviour."""

        query = self.aggregation_strategy.get_location_and_service_query()

        self.search_behaviour.act()

        # test SOEF search query
        self.assert_quantity_in_outbox(1)
        msg = cast(OefSearchMessage, self.get_message_from_outbox())
        has_attributes, error_str = self.message_has_attributes(
            actual_message=msg,
            message_type=OefSearchMessage,
            performative=OefSearchMessage.Performative.SEARCH_SERVICES,
            query=query,
        )
        assert has_attributes, error_str

    def test_teardown(self):
        """Test the teardown method of the search behaviour."""

        with patch.object(self.search_behaviour.context.logger, "log") as mock_logger:
            self.search_behaviour.teardown()

        mock_logger.assert_any_call(
            logging.INFO, "unregistering agent from SOEF.",
        )
        mock_logger.assert_any_call(
            logging.INFO, "unregistering service from SOEF.",
        )

        descriptions = [
            self.aggregation_strategy.get_unregister_service_description(),
            self.aggregation_strategy.get_location_description(),
        ]

        # test SOEF messages
        self.assert_quantity_in_outbox(len(descriptions))
        for description in descriptions:
            msg = cast(OefSearchMessage, self.get_message_from_outbox())
            has_attributes, error_str = self.message_has_attributes(
                actual_message=msg,
                message_type=OefSearchMessage,
                performative=OefSearchMessage.Performative.UNREGISTER_SERVICE,
                service_description=description,
            )
            assert has_attributes, error_str
