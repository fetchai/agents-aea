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
"""This module contains the tests of the handler classes of the simple_data_request skill."""

import logging
import statistics
from pathlib import Path
from typing import cast
from unittest.mock import patch

from aea.protocols.dialogue.base import DialogueMessage
from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.protocols.aggregation.message import AggregationMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.simple_aggregation.behaviours import (
    DEFAULT_SIGNATURE,
    DEFAULT_SOURCE,
)
from packages.fetchai.skills.simple_aggregation.dialogues import (
    AggregationDialogues,
    OefSearchDialogues,
)
from packages.fetchai.skills.simple_aggregation.handlers import (
    AggregationHandler,
    OefSearchHandler,
    get_observation_from_message,
)
from packages.fetchai.skills.simple_aggregation.strategy import AggregationStrategy

from tests.conftest import ROOT_DIR


class TestAggregationHandler(BaseSkillTestCase):
    """Test aggregation handler of simple_aggregation skill."""

    path_to_skill = Path(
        ROOT_DIR, "packages", "fetchai", "skills", "simple_aggregation"
    )
    is_agent_to_agent_messages = False

    @classmethod
    def setup(cls, **kwargs):
        """Setup the test class."""
        super().setup()
        cls.aggregation_handler = cast(
            AggregationHandler, cls._skill.skill_context.handlers.aggregation
        )
        cls.logger = cls._skill.skill_context.logger

        cls.aggregation_strategy = cast(
            AggregationStrategy, cls._skill.skill_context.strategy,
        )

        cls.aggregation_dialogues = cast(
            AggregationDialogues, cls._skill.skill_context.aggregation_dialogues
        )

    def test_setup(self):
        """Test the setup method of the aggregation handler."""
        assert self.aggregation_handler.setup() is None
        self.assert_quantity_in_outbox(0)

    def test_handle_observation(self):
        """Test the _handle_observation method of the aggregation handler to a valid observation."""

        self.aggregation_strategy._quantity_name = "some_quantity"

        sender = "some_sender_address"
        sender_value = 100
        my_value = 50
        values = [float(my_value), float(sender_value)]
        aggregate = getattr(statistics, self.aggregation_strategy._aggregation_function)
        incoming_message = self.build_incoming_message(
            message_type=AggregationMessage,
            performative=AggregationMessage.Performative.OBSERVATION,
            sender=sender,
            to=self._skill.skill_context.agent_address,
            value=sender_value,
            time="some_time",
            source=DEFAULT_SOURCE,
            signature=DEFAULT_SIGNATURE,
        )

        self.aggregation_strategy.add_peers((sender,))
        assert sender in self.aggregation_strategy._peers

        self.aggregation_strategy.make_observation(my_value, "some_time")

        # handle message with logging
        with patch.object(self.logger, "log") as mock_logger:
            self.aggregation_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO, f"received observation from sender={sender[-5:]}"
        )

        expected_aggregation = {"some_quantity": {"value": aggregate(values), "decimals": 0}}

        obs = get_observation_from_message(incoming_message)
        assert len(self.aggregation_strategy._observations) == 2
        assert self.aggregation_strategy._observations[sender] == obs
        assert self.aggregation_strategy._aggregation == aggregate(values)
        assert self.aggregation_handler.context.shared_state[
            "aggregation"
        ] == expected_aggregation

        mock_logger.assert_any_call(logging.INFO, f"Observations: {values}")
        mock_logger.assert_any_call(
            logging.INFO,
            f"Aggregation ({self.aggregation_strategy._aggregation_function}): {self.aggregation_strategy._aggregation}",
        )

    def test_handle_aggregation(self):
        """Test the _handle_aggregation method of the aggregation handler to a valid aggregation."""

        sender = "some_sender_address"
        sender_value = 75
        incoming_message = self.build_incoming_message(
            message_type=AggregationMessage,
            performative=AggregationMessage.Performative.AGGREGATION,
            sender=sender,
            to=self._skill.skill_context.agent_address,
            value=sender_value,
            time="some_time",
            contributors=(sender, "some_other_peer"),
            signature=DEFAULT_SIGNATURE,
        )

        # handle message with logging
        with patch.object(self.logger, "log") as mock_logger:
            self.aggregation_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO, f"received aggregation from sender={sender[-5:]}"
        )

    def test_handle_unidentified_dialogue(self):
        """Test the _handle_response method of the aggregation handler to an unidentified dialogue."""
        # setup
        incoming_message = self.build_incoming_message(
            message_type=OefSearchMessage,
            performative=OefSearchMessage.Performative.SEARCH_SERVICES,
            query=self.aggregation_strategy.get_location_and_service_query(),
            sender="some_sender",
            to=self._skill.skill_context.agent_address,
        )

        # handle message with logging
        with patch.object(self.logger, "log") as mock_logger:
            self.aggregation_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received invalid aggregation message={incoming_message}, unidentified dialogue.",
        )

    def test_teardown(self):
        """Test the teardown method of the aggregation handler."""
        assert self.aggregation_handler.teardown() is None
        self.assert_quantity_in_outbox(0)


class TestOefSearchHandler(BaseSkillTestCase):
    """Test oef search handler of simple aggregation skill."""

    path_to_skill = Path(
        ROOT_DIR, "packages", "fetchai", "skills", "simple_aggregation"
    )
    is_agent_to_agent_messages = False

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.oef_search_handler = cast(
            OefSearchHandler, cls._skill.skill_context.handlers.oef_search
        )
        cls.strategy = cast(AggregationStrategy, cls._skill.skill_context.strategy,)
        cls.oef_dialogues = cast(
            OefSearchDialogues, cls._skill.skill_context.oef_search_dialogues
        )
        cls.list_of_messages = (
            DialogueMessage(
                OefSearchMessage.Performative.SEARCH_SERVICES,
                {"query": cls.strategy.get_location_and_service_query()},
            ),
        )

    def test_setup(self):
        """Test the setup method of the oef_search handler."""
        assert self.oef_search_handler.setup() is None
        self.assert_quantity_in_outbox(0)

    def test_handle_unidentified_dialogue(self):
        """Test the _handle_unidentified_dialogue method of the oef_search handler."""
        # setup
        incorrect_dialogue_reference = ("", "")
        incoming_message = self.build_incoming_message(
            message_type=OefSearchMessage,
            dialogue_reference=incorrect_dialogue_reference,
            performative=OefSearchMessage.Performative.SEARCH_SERVICES,
            query=self.strategy.get_location_and_service_query(),
        )

        # operation
        with patch.object(self.oef_search_handler.context.logger, "log") as mock_logger:
            self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received invalid oef_search message={incoming_message}, unidentified dialogue.",
        )

    def test_handle_error(self):
        """Test the _handle_error method of the oef_search handler."""
        # setup
        oef_dialogue = self.prepare_skill_dialogue(
            dialogues=self.oef_dialogues, messages=self.list_of_messages[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=oef_dialogue,
            performative=OefSearchMessage.Performative.OEF_ERROR,
            oef_error_operation=OefSearchMessage.OefErrorOperation.UNREGISTER_SERVICE,
        )

        # operation
        with patch.object(self.oef_search_handler.context.logger, "log") as mock_logger:
            self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received oef_search error message={incoming_message} in dialogue={oef_dialogue}.",
        )

    def test_handle_search_no_agents(self):
        """Test the _handle_search method of the oef_search handler."""
        # setup
        oef_dialogue = self.prepare_skill_dialogue(
            dialogues=self.oef_dialogues, messages=self.list_of_messages[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=oef_dialogue,
            performative=OefSearchMessage.Performative.SEARCH_RESULT,
            agents=tuple(),
            agents_info=OefSearchMessage.AgentsInfo({}),
        )

        # operation
        with patch.object(self.oef_search_handler.context.logger, "log") as mock_logger:
            self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"found no agents in dialogue={oef_dialogue}, continue searching.",
        )

    def test_handle_search_found_agents(self):
        """Test the _handle_search method of the oef_search handler."""
        # setup
        oef_dialogue = self.prepare_skill_dialogue(
            dialogues=self.oef_dialogues, messages=self.list_of_messages[:1],
        )
        agents = ("agnt1", "agnt2")
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=oef_dialogue,
            performative=OefSearchMessage.Performative.SEARCH_RESULT,
            agents=agents,
            agents_info=OefSearchMessage.AgentsInfo(
                {"agent_1": {"key_1": "value_1"}, "agent_2": {"key_2": "value_2"}}
            ),
        )

        # operation
        with patch.object(self.oef_search_handler.context.logger, "log") as mock_logger:
            self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(logging.INFO, f"found agents={list(agents)}.")

        assert len(self.strategy._peers) == 2
        for agent in agents:
            assert agent in self.strategy._peers

    def test_handle_invalid(self):
        """Test the _handle_invalid method of the oef_search handler."""
        # setup
        invalid_performative = OefSearchMessage.Performative.UNREGISTER_SERVICE
        incoming_message = self.build_incoming_message(
            message_type=OefSearchMessage,
            dialogue_reference=("1", ""),
            performative=invalid_performative,
            service_description=self.strategy.get_unregister_service_description(),
        )

        # operation
        with patch.object(self.oef_search_handler.context.logger, "log") as mock_logger:
            self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.WARNING,
            f"cannot handle oef_search message of performative={invalid_performative} in dialogue={self.oef_dialogues.get_dialogue(incoming_message)}.",
        )

    def test_teardown(self):
        """Test the teardown method of the oef_search handler."""
        assert self.oef_search_handler.teardown() is None
        self.assert_quantity_in_outbox(0)
