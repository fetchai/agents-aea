# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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
"""This module contains a test for aea.test_tools.test_cases."""

from pathlib import Path
from typing import cast

import pytest

from aea.exceptions import AEAEnforceError
from aea.mail.base import Address
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue, DialogueLabel, DialogueMessage
from aea.skills.base import Skill
from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.protocols.default.message import DefaultMessage
from packages.fetchai.protocols.fipa.dialogues import FipaDialogue
from packages.fetchai.protocols.fipa.dialogues import FipaDialogues as BaseFipaDialogues
from packages.fetchai.protocols.fipa.message import FipaMessage

from tests.conftest import ROOT_DIR


class TestSkillTestCase(BaseSkillTestCase):
    """Test case for BaseSkillTestCase."""

    path_to_skill = Path(ROOT_DIR, "tests", "data", "dummy_skill")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        cls.behaviour_arg_1 = 2
        cls.behaviour_arg_2 = "3"

        config_overrides = {
            "behaviours": {
                "dummy": {
                    "args": {
                        "behaviour_arg_1": cls.behaviour_arg_1,
                        "behaviour_arg_2": cls.behaviour_arg_2,
                    }
                }
            },
        }
        cls.shared_state_key = "some_shared_state_key"
        cls.shared_state_value = "some_shared_state_value"
        cls.shared_state = {cls.shared_state_key: cls.shared_state_value}

        super().setup(
            config_overrides=config_overrides,
            shared_state=cls.shared_state,
            dm_context_kwargs={},
        )

    def test_setup(self):
        """Test the setup() class method."""
        assert self.skill.skill_context.agent_address == "test_agent_address"
        assert self.skill.skill_context.agent_name == "test_agent_name"
        assert (
            self.skill.skill_context.search_service_address
            == "dummy_author/dummy_search_skill:0.1.0"
        )
        assert (
            self.skill.skill_context.decision_maker_address
            == "dummy_decision_maker_address"
        )
        assert "dummy" in self.skill.behaviours.keys()
        assert "dummy" in self.skill.handlers.keys()
        assert "dummy_internal" in self.skill.handlers.keys()
        assert "dummy" in self.skill.models.keys()

        assert (
            self.skill.skill_context._agent_context.shared_state[self.shared_state_key]
            == self.shared_state_value
        )

        assert (
            self.skill.skill_context.behaviours.dummy.kwargs["behaviour_arg_1"]
            == self.behaviour_arg_1
        )
        assert (
            self.skill.skill_context.behaviours.dummy.kwargs["behaviour_arg_2"]
            == self.behaviour_arg_2
        )

    def test_properties(self):
        """Test the properties."""
        assert isinstance(self.skill, Skill)
        assert self.skill.behaviours.get("dummy") is not None

    def test_get_quantity_in_outbox(self):
        """Test the get_quantity_in_outbox method."""
        assert self.get_quantity_in_outbox() == 0

        dummy_message = DefaultMessage(
            performative=DefaultMessage.Performative.BYTES, content="dummy"
        )
        dummy_message.to = "some_to"
        dummy_message.sender = "some_sender"
        self.skill.skill_context.outbox.put_message(dummy_message)

        assert self.get_quantity_in_outbox() == 1

    def test_get_message_from_outbox(self):
        """Test the get_message_from_outbox method."""
        assert self.get_message_from_outbox() is None

        dummy_message_1 = DefaultMessage(
            performative=DefaultMessage.Performative.BYTES, content="dummy_1"
        )
        dummy_message_1.to = "some_to_1"
        dummy_message_1.sender = "some_sender_1"
        self.skill.skill_context.outbox.put_message(dummy_message_1)

        dummy_message_2 = DefaultMessage(
            performative=DefaultMessage.Performative.BYTES, content="dummy_2"
        )
        dummy_message_2.to = "some_to_2"
        dummy_message_2.sender = "some_sender_2"
        self.skill.skill_context.outbox.put_message(dummy_message_2)

        assert self.get_message_from_outbox() == dummy_message_1
        assert self.get_message_from_outbox() == dummy_message_2

    def test_drop_messages_from_outbox(self):
        """Test the drop_messages_from_outbox method."""
        assert self.get_quantity_in_outbox() == 0
        self.drop_messages_from_outbox(5)
        assert self.get_quantity_in_outbox() == 0

        dummy_message_1 = DefaultMessage(
            performative=DefaultMessage.Performative.BYTES, content="dummy_2"
        )
        dummy_message_1.to = "some_to_1"
        dummy_message_1.sender = "some_sender_1"
        self.skill.skill_context.outbox.put_message(dummy_message_1)

        dummy_message_2 = DefaultMessage(
            performative=DefaultMessage.Performative.BYTES, content="dummy_2"
        )
        dummy_message_2.to = "some_to_2"
        dummy_message_2.sender = "some_sender_2"
        self.skill.skill_context.outbox.put_message(dummy_message_2)

        dummy_message_3 = DefaultMessage(
            performative=DefaultMessage.Performative.BYTES, content="dummy_2"
        )
        dummy_message_3.to = "some_to_3"
        dummy_message_3.sender = "some_sender_3"
        self.skill.skill_context.outbox.put_message(dummy_message_3)

        assert self.get_quantity_in_outbox() == 3

        self.drop_messages_from_outbox(2)

        assert self.get_quantity_in_outbox() == 1
        assert self.get_message_from_outbox() == dummy_message_3

    def test_get_quantity_in_decision_maker_inbox(self):
        """Test the get_quantity_in_decision_maker_inbox method."""
        assert self.get_quantity_in_decision_maker_inbox() == 0

        dummy_message = DefaultMessage(
            performative=DefaultMessage.Performative.BYTES, content="dummy"
        )
        dummy_message.to = "some_to"
        dummy_message.sender = "some_sender"
        self.skill.skill_context.decision_maker_message_queue.put(dummy_message)

        assert self.get_quantity_in_decision_maker_inbox() == 1

    def test_get_message_from_decision_maker_inbox(self):
        """Test the get_message_from_decision_maker_inbox method."""
        assert self.get_message_from_decision_maker_inbox() is None

        dummy_message_1 = DefaultMessage(
            performative=DefaultMessage.Performative.BYTES, content="dummy_1"
        )
        dummy_message_1.to = "some_to_1"
        dummy_message_1.sender = "some_sender_1"
        self.skill.skill_context.decision_maker_message_queue.put(dummy_message_1)

        dummy_message_2 = DefaultMessage(
            performative=DefaultMessage.Performative.BYTES, content="dummy_2"
        )
        dummy_message_2.to = "some_to_2"
        dummy_message_2.sender = "some_sender_2"
        self.skill.skill_context.decision_maker_message_queue.put(dummy_message_2)

        assert self.get_message_from_decision_maker_inbox() == dummy_message_1
        assert self.get_message_from_decision_maker_inbox() == dummy_message_2

    def test_drop_messages_from_decision_maker_inbox(self):
        """Test the drop_messages_from_decision_maker_inbox method."""
        assert self.get_quantity_in_decision_maker_inbox() == 0
        self.drop_messages_from_decision_maker_inbox(5)
        assert self.get_quantity_in_decision_maker_inbox() == 0

        dummy_message_1 = Message()
        dummy_message_1.to = "some_to_1"
        dummy_message_1.sender = "some_sender_1"
        self.skill.skill_context.decision_maker_message_queue.put(dummy_message_1)

        dummy_message_2 = Message()
        dummy_message_2.to = "some_to_2"
        dummy_message_2.sender = "some_sender_2"
        self.skill.skill_context.decision_maker_message_queue.put(dummy_message_2)

        dummy_message_3 = Message()
        dummy_message_3.to = "some_to_3"
        dummy_message_3.sender = "some_sender_3"
        self.skill.skill_context.decision_maker_message_queue.put(dummy_message_3)

        assert self.get_quantity_in_decision_maker_inbox() == 3

        self.drop_messages_from_decision_maker_inbox(2)

        assert self.get_quantity_in_decision_maker_inbox() == 1
        assert self.get_message_from_decision_maker_inbox() == dummy_message_3

    def test_assert_quantity_in_outbox(self):
        """Test the assert_quantity_in_outbox method."""
        with pytest.raises(
            AssertionError,
            match=f"Invalid number of messages in outbox. Expected {1}. Found {0}.",
        ):
            self.assert_quantity_in_outbox(1)

        dummy_message = DefaultMessage(
            performative=DefaultMessage.Performative.BYTES, content="dummy"
        )
        dummy_message.to = "some_to"
        dummy_message.sender = "some_sender"
        self.skill.skill_context.outbox.put_message(dummy_message)

        self.assert_quantity_in_outbox(1)

    def test_assert_quantity_in_decision_making_queue(self):
        """Test the assert_quantity_in_decision_making_queue method."""
        with pytest.raises(
            AssertionError,
            match=f"Invalid number of messages in decision maker queue. Expected {1}. Found {0}.",
        ):
            self.assert_quantity_in_decision_making_queue(1)

        dummy_message = DefaultMessage(
            performative=DefaultMessage.Performative.BYTES, content="dummy_1"
        )
        dummy_message.to = "some_to_1"
        dummy_message.sender = "some_sender_1"
        self.skill.skill_context.decision_maker_message_queue.put(dummy_message)

        self.assert_quantity_in_decision_making_queue(1)

    def test_positive_message_has_attributes_valid_type(self):
        """Test the message_has_attributes method where the message is of the specified type."""
        dummy_message = FipaMessage(
            dialogue_reference=("0", "0"),
            message_id=1,
            performative=FipaMessage.Performative.CFP,
            target=0,
            query="some_query",
        )
        dummy_message.to = "some_to"
        dummy_message.sender = "some_sender"

        valid_has_attribute, valid_has_attribute_msg = self.message_has_attributes(
            actual_message=dummy_message,
            message_type=FipaMessage,
            message_id=1,
            performative=FipaMessage.Performative.CFP,
            target=0,
            query="some_query",
            to="some_to",
            sender="some_sender",
        )
        assert valid_has_attribute
        assert (
            valid_has_attribute_msg
            == "The message has the provided expected attributes."
        )

    def test_negative_message_has_attributes_invalid_message_id(self):
        """Negative test for message_has_attributes method where the message id does NOT match."""
        dummy_message = FipaMessage(
            dialogue_reference=("0", "0"),
            message_id=1,
            performative=FipaMessage.Performative.CFP,
            target=0,
            query="some_query",
        )
        dummy_message.to = "some_to"
        dummy_message.sender = "some_sender"

        invalid_has_attribute, invalid_has_attribute_msg = self.message_has_attributes(
            actual_message=dummy_message,
            message_type=FipaMessage,
            message_id=2,
            performative=FipaMessage.Performative.CFP,
            target=0,
            query="some_query",
            to="some_to",
            sender="some_sender",
        )
        assert not invalid_has_attribute
        assert (
            invalid_has_attribute_msg
            == "The 'message_id' fields do not match. Actual 'message_id': 1. Expected 'message_id': 2"
        )

    def test_negative_message_has_attributes_invalid_type(self):
        """Test the message_has_attributes method where the message is NOT of the specified type."""
        dummy_message = FipaMessage(
            dialogue_reference=("0", "0"),
            message_id=1,
            performative=FipaMessage.Performative.CFP,
            target=0,
            query="some_query",
        )
        dummy_message.to = "some_to"
        dummy_message.sender = "some_sender"

        valid_has_attribute, valid_has_attribute_msg = self.message_has_attributes(
            actual_message=dummy_message,
            message_type=DefaultMessage,
            message_id=1,
            performative=FipaMessage.Performative.CFP,
            target=0,
            query="some_query",
            to="some_to",
            sender="some_sender",
        )
        assert not valid_has_attribute
        assert (
            valid_has_attribute_msg
            == f"The message types do not match. Actual type: {FipaMessage}. Expected type: {DefaultMessage}"
        )

        invalid_has_attribute, invalid_has_attribute_msg = self.message_has_attributes(
            actual_message=dummy_message,
            message_type=FipaMessage,
            message_id=2,
            performative=FipaMessage.Performative.CFP,
            target=0,
            query="some_query",
            to="some_to",
            sender="some_sender",
        )
        assert not invalid_has_attribute
        assert (
            invalid_has_attribute_msg
            == "The 'message_id' fields do not match. Actual 'message_id': 1. Expected 'message_id': 2"
        )

    def test_build_incoming_message(self):
        """Test the build_incoming_message method."""
        message_type = FipaMessage
        performative = FipaMessage.Performative.CFP
        dialogue_reference = ("1", "1")
        to = "some_to"
        query = "some_query"
        incoming_message = self.build_incoming_message(
            message_type=message_type,
            performative=performative,
            dialogue_reference=dialogue_reference,
            to=to,
            query=query,
        )

        assert type(incoming_message) == message_type
        incoming_message = cast(FipaMessage, incoming_message)
        assert incoming_message.dialogue_reference == dialogue_reference
        assert incoming_message.message_id == 1
        assert incoming_message.target == 0
        assert incoming_message.performative == performative
        assert incoming_message.query == query
        assert incoming_message.sender == "counterparty"
        assert incoming_message.to == to

    def test_positive_build_incoming_message_for_skill_dialogue(self):
        """Positive test for build_incoming_message_for_skill_dialogue method."""
        fipa_dialogues = FipaDialogues(
            self_address=self.skill.skill_context.agent_address
        )
        base_msg, dialogue = fipa_dialogues.create(
            counterparty="some_counterparty",
            performative=FipaMessage.Performative.CFP,
            query="some_query",
        )

        performative = FipaMessage.Performative.PROPOSE
        proposal = "some_proposal"
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=dialogue,
            performative=performative,
            proposal=proposal,
        )

        assert type(incoming_message) == FipaMessage
        incoming_message = cast(FipaMessage, incoming_message)
        assert (
            incoming_message.dialogue_reference
            == dialogue.dialogue_label.dialogue_reference
        )
        assert incoming_message.message_id != base_msg.message_id
        assert incoming_message.target == base_msg.message_id
        assert incoming_message.performative == performative
        assert incoming_message.proposal == proposal
        assert incoming_message.sender == dialogue.dialogue_label.dialogue_opponent_addr
        assert incoming_message.to == dialogue.self_address

    def test_negative_build_incoming_message_for_skill_dialogue_dialogue_is_none(self):
        """Negative test for build_incoming_message_for_skill_dialogue method where the provided dialogue is None."""
        performative = FipaMessage.Performative.PROPOSE
        proposal = "some_proposal"

        with pytest.raises(AEAEnforceError, match="dialogue cannot be None."):
            self.build_incoming_message_for_skill_dialogue(
                dialogue=None,
                performative=performative,
                proposal=proposal,
            )

    def test_negative_build_incoming_message_for_skill_dialogue_dialogue_is_empty(self):
        """Negative test for build_incoming_message_for_skill_dialogue method where the provided dialogue is empty."""
        performative = FipaMessage.Performative.PROPOSE
        proposal = "some_proposal"

        fipa_dialogues = FipaDialogues(
            self_address=self.skill.skill_context.agent_address
        )
        dialogue = fipa_dialogues._create_self_initiated(
            dialogue_opponent_addr="some_counterparty",
            dialogue_reference=("0", ""),
            role=FipaDialogue.Role.BUYER,
        )

        with pytest.raises(AEAEnforceError, match="dialogue cannot be empty."):
            self.build_incoming_message_for_skill_dialogue(
                dialogue=dialogue,
                performative=performative,
                proposal=proposal,
            )

    def test_provide_unspecified_fields(self):
        """Test the _provide_unspecified_fields method."""
        dialogue_message_unspecified = DialogueMessage(
            FipaMessage.Performative.ACCEPT, {}
        )

        is_incoming, target = self._provide_unspecified_fields(
            dialogue_message_unspecified, last_is_incoming=False
        )
        assert is_incoming is True
        assert target is None

        dialogue_message_specified = DialogueMessage(
            FipaMessage.Performative.ACCEPT, {}, False, 4
        )

        is_incoming, target = self._provide_unspecified_fields(
            dialogue_message_specified, last_is_incoming=True
        )
        assert is_incoming is False
        assert target == 4

    def test_non_initial_incoming_message_dialogue_reference(self):
        """Test the _non_initial_incoming_message_dialogue_reference method."""
        dialogue_incomplete_ref = FipaDialogue(
            DialogueLabel(("2", ""), "opponent", "self_address"),
            "self_address",
            FipaDialogue.Role.BUYER,
        )
        reference_incomplete = self._non_initial_incoming_message_dialogue_reference(
            dialogue_incomplete_ref
        )
        assert reference_incomplete[1] != ""

        dialogue_complete_ref = FipaDialogue(
            DialogueLabel(("2", "7"), "opponent", "self_address"),
            "self_address",
            FipaDialogue.Role.BUYER,
        )
        reference_complete = self._non_initial_incoming_message_dialogue_reference(
            dialogue_complete_ref
        )
        assert reference_complete[1] == "7"

    def test_extract_message_fields(self):
        """Test the _extract_message_fields method."""
        expected_performative = FipaMessage.Performative.ACCEPT
        expected_contents = {}
        expected_is_incoming = False
        expected_target = 4
        dialogue_message = DialogueMessage(
            expected_performative,
            expected_contents,
            expected_is_incoming,
            expected_target,
        )

        (
            actual_performative,
            actual_contents,
            actual_message_id,
            actual_is_incoming,
            actual_target,
        ) = self._extract_message_fields(
            message=dialogue_message, index=3, last_is_incoming=True
        )

        assert actual_message_id == 4
        assert actual_target == expected_target
        assert actual_performative == expected_performative
        assert actual_contents == expected_contents
        assert actual_is_incoming == expected_is_incoming

    def test_prepare_skill_dialogue_valid_self_initiated(self):
        """Positive test for prepare_skill_dialogue method with a valid dialogue initiated by self."""
        fipa_dialogues = FipaDialogues(
            self_address=self.skill.skill_context.agent_address
        )
        dialogue_messages = (
            DialogueMessage(FipaMessage.Performative.CFP, {"query": "some_query"}),
            DialogueMessage(
                FipaMessage.Performative.PROPOSE, {"proposal": "some_proposal"}
            ),
            DialogueMessage(
                FipaMessage.Performative.PROPOSE,
                {"proposal": "some_counter_proposal_1"},
            ),
            DialogueMessage(
                FipaMessage.Performative.PROPOSE,
                {"proposal": "some_counter_proposal_2"},
            ),
            DialogueMessage(
                FipaMessage.Performative.PROPOSE,
                {"proposal": "some_counter_proposal_3"},
            ),
            DialogueMessage(
                FipaMessage.Performative.PROPOSE,
                {"proposal": "some_counter_proposal_4"},
            ),
            DialogueMessage(FipaMessage.Performative.ACCEPT, {}),
            DialogueMessage(
                FipaMessage.Performative.MATCH_ACCEPT_W_INFORM, {"info": "some_info"}
            ),
        )
        dialogue = self.prepare_skill_dialogue(
            fipa_dialogues,
            dialogue_messages,
            "counterparty",
        )

        assert type(dialogue) == FipaDialogue
        assert dialogue.is_self_initiated
        assert len(dialogue._outgoing_messages) == 4
        assert len(dialogue._incoming_messages) == 4
        assert dialogue._incoming_messages[1].proposal == "some_counter_proposal_2"
        assert dialogue._incoming_messages[3].info == "some_info"

    def test_prepare_skill_dialogue_valid_opponent_initiated(self):
        """Positive test for prepare_skill_dialogue method with a valid dialogue initiated by the opponent."""
        fipa_dialogues = FipaDialogues(
            self_address=self.skill.skill_context.agent_address
        )
        dialogue_messages = (
            DialogueMessage(
                FipaMessage.Performative.CFP, {"query": "some_query"}, True
            ),
            DialogueMessage(
                FipaMessage.Performative.PROPOSE, {"proposal": "some_proposal"}
            ),
            DialogueMessage(
                FipaMessage.Performative.PROPOSE,
                {"proposal": "some_counter_proposal_1"},
            ),
            DialogueMessage(
                FipaMessage.Performative.PROPOSE,
                {"proposal": "some_counter_proposal_2"},
            ),
            DialogueMessage(
                FipaMessage.Performative.PROPOSE,
                {"proposal": "some_counter_proposal_3"},
            ),
            DialogueMessage(
                FipaMessage.Performative.PROPOSE,
                {"proposal": "some_counter_proposal_4"},
            ),
            DialogueMessage(FipaMessage.Performative.ACCEPT, {}),
            DialogueMessage(
                FipaMessage.Performative.MATCH_ACCEPT_W_INFORM, {"info": "some_info"}
            ),
        )
        dialogue = self.prepare_skill_dialogue(
            fipa_dialogues,
            dialogue_messages,
            "counterparty",
        )

        assert type(dialogue) == FipaDialogue
        assert not dialogue.is_self_initiated
        assert len(dialogue._outgoing_messages) == 4
        assert len(dialogue._incoming_messages) == 4
        assert dialogue._outgoing_messages[1].proposal == "some_counter_proposal_2"
        assert dialogue._outgoing_messages[-1].info == "some_info"

    def test_negative_prepare_skill_dialogue_invalid_opponent_initiated(self):
        """Negative test for prepare_skill_dialogue method with an invalid dialogue initiated by the opponent."""
        fipa_dialogues = FipaDialogues(
            self_address=self.skill.skill_context.agent_address
        )
        dialogue_messages = (
            DialogueMessage(
                FipaMessage.Performative.PROPOSE, {"proposal": "some_proposal"}, True
            ),
            DialogueMessage(
                FipaMessage.Performative.PROPOSE,
                {"proposal": "some_counter_proposal_1"},
            ),
            DialogueMessage(
                FipaMessage.Performative.PROPOSE,
                {"proposal": "some_counter_proposal_2"},
            ),
            DialogueMessage(
                FipaMessage.Performative.PROPOSE,
                {"proposal": "some_counter_proposal_3"},
            ),
            DialogueMessage(
                FipaMessage.Performative.PROPOSE,
                {"proposal": "some_counter_proposal_4"},
            ),
            DialogueMessage(FipaMessage.Performative.ACCEPT, {}),
            DialogueMessage(
                FipaMessage.Performative.MATCH_ACCEPT_W_INFORM, {"info": "some_info"}
            ),
        )
        with pytest.raises(
            AEAEnforceError, match="Cannot update the dialogue with message number 1"
        ):
            self.prepare_skill_dialogue(
                fipa_dialogues,
                dialogue_messages,
                "counterparty",
            )

    def test_negative_prepare_skill_dialogue_empty_messages(self):
        """Negative test for prepare_skill_dialogue method where the list of DialogueMessages is emoty."""
        fipa_dialogues = FipaDialogues(
            self_address=self.skill.skill_context.agent_address
        )
        dialogue_messages = tuple()

        with pytest.raises(
            AEAEnforceError, match="the list of messages must be positive."
        ):
            self.prepare_skill_dialogue(
                fipa_dialogues,
                dialogue_messages,
                "counterparty",
            )

    def test_negative_prepare_skill_dialogue_invalid(self):
        """Negative test for prepare_skill_dialogue method with an invalid dialogue (a message has invalid target)."""
        fipa_dialogues = FipaDialogues(
            self_address=self.skill.skill_context.agent_address
        )
        dialogue_messages = (
            DialogueMessage(FipaMessage.Performative.CFP, {"query": "some_query"}),
            DialogueMessage(
                FipaMessage.Performative.PROPOSE,
                {"proposal": "some_proposal"},
                target=2,
            ),
        )

        with pytest.raises(
            AEAEnforceError, match="Cannot update the dialogue with message number .*"
        ):
            self.prepare_skill_dialogue(
                fipa_dialogues,
                dialogue_messages,
                "counterparty",
            )


class FipaDialogues(BaseFipaDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, self_address: Address, **kwargs) -> None:
        """
        Initialize dialogues.

        :return: None
        """

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> Dialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return FipaDialogue.Role.BUYER

        BaseFipaDialogues.__init__(
            self,
            self_address=self_address,
            role_from_first_message=role_from_first_message,
            dialogue_class=FipaDialogue,
        )
