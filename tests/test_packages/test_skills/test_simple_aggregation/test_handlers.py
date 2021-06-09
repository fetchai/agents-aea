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

from aea.helpers.search.models import Attribute, DataModel, Description, Location
from aea.protocols.dialogue.base import DialogueMessage
from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.protocols.aggregation.message import AggregationMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.simple_aggregation.behaviours import (
    DEFAULT_SIGNATURE,
    DEFAULT_SOURCE,
    SearchBehaviour,
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

        expected_aggregation = {"value": aggregate(values), "decimals": 0}
        aggregated_key = (
            "some_quantity" + "_" + self.aggregation_strategy._aggregation_function
        )

        obs = get_observation_from_message(incoming_message)
        assert len(self.aggregation_strategy._observations) == 2
        assert self.aggregation_strategy._observations[sender] == obs
        assert self.aggregation_strategy._aggregation == aggregate(values)
        assert (
            self.aggregation_handler.context.shared_state[aggregated_key]
            == expected_aggregation
        )

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
        cls.service_registration_behaviour = cast(
            SearchBehaviour, cls._skill.skill_context.behaviours.search,
        )

        cls.register_location_description = Description(
            {"location": Location(51.5194, 0.1270)},
            data_model=DataModel(
                "location_agent", [Attribute("location", Location, True)]
            ),
        )
        cls.list_of_messages_register_location = (
            DialogueMessage(
                OefSearchMessage.Performative.REGISTER_SERVICE,
                {"service_description": cls.register_location_description},
                is_incoming=False,
            ),
        )

        cls.register_service_description = Description(
            {"key": "some_key", "value": "some_value"},
            data_model=DataModel(
                "set_service_key",
                [Attribute("key", str, True), Attribute("value", str, True)],
            ),
        )
        cls.list_of_messages_register_service = (
            DialogueMessage(
                OefSearchMessage.Performative.REGISTER_SERVICE,
                {"service_description": cls.register_service_description},
                is_incoming=False,
            ),
        )

        cls.register_genus_description = Description(
            {"piece": "genus", "value": "some_value"},
            data_model=DataModel(
                "personality_agent",
                [Attribute("piece", str, True), Attribute("value", str, True)],
            ),
        )
        cls.list_of_messages_register_genus = (
            DialogueMessage(
                OefSearchMessage.Performative.REGISTER_SERVICE,
                {"service_description": cls.register_genus_description},
                is_incoming=False,
            ),
        )

        cls.register_classification_description = Description(
            {"piece": "classification", "value": "some_value"},
            data_model=DataModel(
                "personality_agent",
                [Attribute("piece", str, True), Attribute("value", str, True)],
            ),
        )
        cls.list_of_messages_register_classification = (
            DialogueMessage(
                OefSearchMessage.Performative.REGISTER_SERVICE,
                {"service_description": cls.register_classification_description},
                is_incoming=False,
            ),
        )

        cls.register_invalid_description = Description(
            {"piece": "classification", "value": "some_value"},
            data_model=DataModel(
                "some_different_name",
                [Attribute("piece", str, True), Attribute("value", str, True)],
            ),
        )
        cls.list_of_messages_register_invalid = (
            DialogueMessage(
                OefSearchMessage.Performative.REGISTER_SERVICE,
                {"service_description": cls.register_invalid_description},
                is_incoming=False,
            ),
        )

        cls.unregister_description = Description(
            {"key": "seller_service"},
            data_model=DataModel("remove", [Attribute("key", str, True)]),
        )
        cls.list_of_messages_unregister = (
            DialogueMessage(
                OefSearchMessage.Performative.UNREGISTER_SERVICE,
                {"service_description": cls.unregister_description},
                is_incoming=False,
            ),
        )

        cls.list_of_messages_search = (
            DialogueMessage(
                OefSearchMessage.Performative.SEARCH_SERVICES,
                {"query": cls.strategy.get_location_and_service_query()},
                is_incoming=False,
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

    def test_handle_success_i(self):
        """Test the _handle_success method of the oef_search handler where the oef success targets register_service WITH location_agent data model description."""
        # setup
        oef_dialogue = self.prepare_skill_dialogue(
            dialogues=self.oef_dialogues,
            messages=self.list_of_messages_register_location[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=oef_dialogue,
            performative=OefSearchMessage.Performative.SUCCESS,
            agents_info=OefSearchMessage.AgentsInfo({"address": {"key": "value"}}),
        )

        # operation
        with patch.object(self.oef_search_handler.context.logger, "log") as mock_logger:
            with patch.object(
                self.service_registration_behaviour, "register_service",
            ) as mock_reg:
                self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received oef_search success message={incoming_message} in dialogue={oef_dialogue}.",
        )
        mock_reg.assert_called_once()

    def test_handle_success_ii(self):
        """Test the _handle_success method of the oef_search handler where the oef success targets register_service WITH set_service_key data model description."""
        # setup
        oef_dialogue = self.prepare_skill_dialogue(
            dialogues=self.oef_dialogues,
            messages=self.list_of_messages_register_service[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=oef_dialogue,
            performative=OefSearchMessage.Performative.SUCCESS,
            agents_info=OefSearchMessage.AgentsInfo({"address": {"key": "value"}}),
        )

        # operation
        with patch.object(self.oef_search_handler.context.logger, "log") as mock_logger:
            with patch.object(
                self.service_registration_behaviour, "register_genus",
            ) as mock_reg:
                self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received oef_search success message={incoming_message} in dialogue={oef_dialogue}.",
        )
        mock_reg.assert_called_once()

    def test_handle_success_iii(self):
        """Test the _handle_success method of the oef_search handler where the oef success targets register_service WITH personality_agent data model and genus value description."""
        # setup
        oef_dialogue = self.prepare_skill_dialogue(
            dialogues=self.oef_dialogues,
            messages=self.list_of_messages_register_genus[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=oef_dialogue,
            performative=OefSearchMessage.Performative.SUCCESS,
            agents_info=OefSearchMessage.AgentsInfo({"address": {"key": "value"}}),
        )

        # operation
        with patch.object(self.oef_search_handler.context.logger, "log") as mock_logger:
            with patch.object(
                self.service_registration_behaviour, "register_classification",
            ) as mock_reg:
                self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received oef_search success message={incoming_message} in dialogue={oef_dialogue}.",
        )
        mock_reg.assert_called_once()

    def test_handle_success_iv(self):
        """Test the _handle_success method of the oef_search handler where the oef success targets register_service WITH personality_agent data model and classification value description."""
        # setup
        oef_dialogue = self.prepare_skill_dialogue(
            dialogues=self.oef_dialogues,
            messages=self.list_of_messages_register_classification[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=oef_dialogue,
            performative=OefSearchMessage.Performative.SUCCESS,
            agents_info=OefSearchMessage.AgentsInfo({"address": {"key": "value"}}),
        )

        # operation
        with patch.object(self.oef_search_handler.context.logger, "log") as mock_logger:
            self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received oef_search success message={incoming_message} in dialogue={oef_dialogue}.",
        )
        mock_logger.assert_any_call(
            logging.INFO,
            "the agent, with its genus and classification, and its service are successfully registered on the SOEF.",
        )

    def test_handle_success_v(self):
        """Test the _handle_success method of the oef_search handler where the oef successtargets unregister_service."""
        # setup
        oef_dialogue = self.prepare_skill_dialogue(
            dialogues=self.oef_dialogues,
            messages=self.list_of_messages_register_invalid[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=oef_dialogue,
            performative=OefSearchMessage.Performative.SUCCESS,
            agents_info=OefSearchMessage.AgentsInfo({"address": {"key": "value"}}),
        )

        # operation
        with patch.object(self.oef_search_handler.context.logger, "log") as mock_logger:
            self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received oef_search success message={incoming_message} in dialogue={oef_dialogue}.",
        )
        mock_logger.assert_any_call(
            logging.WARNING,
            f"received soef SUCCESS message as a reply to the following unexpected message: {oef_dialogue.get_message_by_id(incoming_message.target)}",
        )

    def test_handle_error_i(self):
        """Test the _handle_error method of the oef_search handler where the oef error targets register_service."""
        # setup
        oef_dialogue = self.prepare_skill_dialogue(
            dialogues=self.oef_dialogues,
            messages=self.list_of_messages_register_location[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=oef_dialogue,
            performative=OefSearchMessage.Performative.OEF_ERROR,
            oef_error_operation=OefSearchMessage.OefErrorOperation.SEARCH_SERVICES,
        )

        # operation
        with patch.object(self.oef_search_handler.context.logger, "log") as mock_logger:
            self.oef_search_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_outbox(0)

        mock_logger.assert_any_call(
            logging.INFO,
            f"received oef_search error message={incoming_message} in dialogue={oef_dialogue}.",
        )
        assert (
            self.service_registration_behaviour.failed_registration_msg
            == oef_dialogue.get_message_by_id(incoming_message.target)
        )

    def test_handle_error_ii(self):
        """Test the _handle_error method of the oef_search handler where the oef error does NOT target register_service."""
        # setup
        oef_dialogue = self.prepare_skill_dialogue(
            dialogues=self.oef_dialogues, messages=self.list_of_messages_unregister[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=oef_dialogue,
            performative=OefSearchMessage.Performative.OEF_ERROR,
            oef_error_operation=OefSearchMessage.OefErrorOperation.SEARCH_SERVICES,
        )

        # operation
        with patch.object(self.oef_search_handler.context.logger, "log") as mock_logger:
            self.oef_search_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_outbox(0)

        mock_logger.assert_any_call(
            logging.INFO,
            f"received oef_search error message={incoming_message} in dialogue={oef_dialogue}.",
        )

        assert self.service_registration_behaviour.failed_registration_msg is None

    def test_handle_search_no_agents(self):
        """Test the _handle_search method of the oef_search handler."""
        # setup
        oef_dialogue = self.prepare_skill_dialogue(
            dialogues=self.oef_dialogues, messages=self.list_of_messages_search[:1],
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
            dialogues=self.oef_dialogues, messages=self.list_of_messages_search[:1],
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
