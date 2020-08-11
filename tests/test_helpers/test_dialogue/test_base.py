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

"""This module contains the tests for the dialogue/base.py module."""

from typing import Dict, FrozenSet, Type, cast

import pytest

from aea.helpers.dialogue.base import Dialogue as BaseDialogue
from aea.helpers.dialogue.base import DialogueLabel, DialogueStats
from aea.helpers.dialogue.base import Dialogues as BaseDialogues
from aea.mail.base import Address
from aea.protocols.base import Message
from aea.protocols.default.message import DefaultMessage


class Dialogue(BaseDialogue):
    """This concrete class defines a dialogue."""

    INITIAL_PERFORMATIVES = frozenset(
        {DefaultMessage.Performative.BYTES}
    )  # type: FrozenSet[DefaultMessage.Performative]
    TERMINAL_PERFORMATIVES = frozenset(
        {DefaultMessage.Performative.ERROR}
    )  # type: FrozenSet[DefaultMessage.Performative]
    VALID_REPLIES = {
        DefaultMessage.Performative.BYTES: frozenset(
            {DefaultMessage.Performative.BYTES, DefaultMessage.Performative.ERROR}
        ),
        DefaultMessage.Performative.ERROR: frozenset(),
    }  # type: Dict[DefaultMessage.Performative, FrozenSet[DefaultMessage.Performative]]

    class Role(BaseDialogue.Role):
        """This class defines the agent's role in this dialogue."""

        ROLE1 = "role1"
        ROLE2 = "role2"

    class EndState(BaseDialogue.EndState):
        """This class defines the end states of this dialogue."""

        SUCCESSFUL = 0
        FAILED = 1

    def __init__(
        self,
        dialogue_label: DialogueLabel,
        message_class: Type[Message] = DefaultMessage,
        agent_address: Address = "agent 1",
        role: BaseDialogue.Role = Role.ROLE1,
    ) -> None:
        """
        Initialize a dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param agent_address: the address of the agent for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for
        :return: None
        """
        BaseDialogue.__init__(
            self,
            dialogue_label=dialogue_label,
            agent_address=agent_address,
            role=role,
            message_class=message_class,
            rules=BaseDialogue.Rules(
                cast(FrozenSet[Message.Performative], self.INITIAL_PERFORMATIVES),
                cast(FrozenSet[Message.Performative], self.TERMINAL_PERFORMATIVES),
                cast(
                    Dict[Message.Performative, FrozenSet[Message.Performative]],
                    self.VALID_REPLIES,
                ),
            ),
        )

    def is_valid(self, message: Message) -> bool:
        """
        Check whether 'message' is a valid next message in the dialogue.

        These rules capture specific constraints designed for dialogues which are instance of a concrete sub-class of this class.

        :param message: the message to be validated
        :return: True if valid, False otherwise.
        """
        return True


class Dialogues(BaseDialogues):
    """This class gives a concrete definition of dialogues."""

    END_STATES = frozenset(
        {Dialogue.EndState.SUCCESSFUL, Dialogue.EndState.FAILED}
    )  # type: FrozenSet[BaseDialogue.EndState]

    def __init__(
        self,
        agent_address: Address,
        message_class=DefaultMessage,
        dialogue_class=Dialogue,
    ) -> None:
        """
        Initialize dialogues.

        :param agent_address: the address of the agent for whom dialogues are maintained
        :return: None
        """

        def role_from_first_message(message: Message) -> BaseDialogue.Role:
            """
            Infer the role of the agent from an incoming or outgoing first message

            :param message: an incoming/outgoing first message
            :return: the agent's role
            """
            return Dialogue.Role.ROLE1

        BaseDialogues.__init__(
            self,
            agent_address=agent_address,
            end_states=cast(FrozenSet[BaseDialogue.EndState], self.END_STATES),
            message_class=message_class,
            dialogue_class=dialogue_class,
            role_from_first_message=role_from_first_message,
        )

    def create_dialogue(
        self, dialogue_label: DialogueLabel, role: BaseDialogue.Role,
    ) -> Dialogue:
        """
        Create a dialogue instance.

        :param dialogue_label: the identifier of the dialogue
        :param role: the role of the agent this dialogue is maintained for

        :return: the created dialogue
        """
        pass


class TestDialogueLabel:
    """Test for DialogueLabel."""

    @classmethod
    def setup(cls):
        """Initialise the environment to test DialogueLabel."""
        cls.agent_address = "agent 1"
        cls.opponent_address = "agent 2"
        cls.dialogue_label = DialogueLabel(
            dialogue_reference=(str(1), ""),
            dialogue_opponent_addr=cls.opponent_address,
            dialogue_starter_addr=cls.agent_address,
        )

    def test_all_methods(self):
        """Test the DialogueLabel."""
        assert self.dialogue_label.dialogue_reference == (str(1), "")
        assert self.dialogue_label.dialogue_starter_reference == str(1)
        assert self.dialogue_label.dialogue_responder_reference == ""
        assert self.dialogue_label.dialogue_opponent_addr == self.opponent_address
        assert self.dialogue_label.dialogue_starter_addr == self.agent_address
        assert str(self.dialogue_label) == "{}_{}_{}_{}".format(
            self.dialogue_label.dialogue_starter_reference,
            self.dialogue_label.dialogue_responder_reference,
            self.dialogue_label.dialogue_opponent_addr,
            self.dialogue_label.dialogue_starter_addr,
        )

        dialogue_label_eq = DialogueLabel(
            dialogue_reference=(str(1), ""),
            dialogue_opponent_addr=self.opponent_address,
            dialogue_starter_addr=self.agent_address,
        )

        assert dialogue_label_eq == self.dialogue_label

        dialogue_label_not_eq = "This is a test"

        assert not dialogue_label_not_eq == self.dialogue_label

        assert hash(dialogue_label_eq) == hash(self.dialogue_label)

        assert self.dialogue_label.json == dict(
            dialogue_starter_reference=str(1),
            dialogue_responder_reference="",
            dialogue_opponent_addr=self.opponent_address,
            dialogue_starter_addr=self.agent_address,
        )
        assert DialogueLabel.from_json(self.dialogue_label.json) == self.dialogue_label
        assert DialogueLabel.from_str(str(self.dialogue_label)) == self.dialogue_label


class TestDialogueBase:
    """Test for Dialogue."""

    @classmethod
    def setup(cls):
        """Initialise the environment to test Dialogue."""
        cls.incomplete_reference = (str(1), "")
        cls.complete_reference = (str(1), str(1))
        cls.opponent_address = "agent 2"
        cls.agent_address = "agent 1"
        cls.dialogue_label = DialogueLabel(
            dialogue_reference=cls.incomplete_reference,
            dialogue_opponent_addr=cls.opponent_address,
            dialogue_starter_addr=cls.agent_address,
        )
        cls.dialogue = Dialogue(dialogue_label=cls.dialogue_label)
        cls.dialogue_label_opponent_started = DialogueLabel(
            dialogue_reference=cls.complete_reference,
            dialogue_opponent_addr=cls.opponent_address,
            dialogue_starter_addr=cls.opponent_address,
        )
        cls.dialogue_opponent_started = Dialogue(
            dialogue_label=cls.dialogue_label_opponent_started
        )

    def test_inner_classes(self):
        """Test the inner classes: Role and EndStates."""
        assert str(Dialogue.Role.ROLE1) == "role1"
        assert str(Dialogue.Role.ROLE2) == "role2"
        assert str(Dialogue.EndState.SUCCESSFUL) == "0"
        assert str(Dialogue.EndState.FAILED) == "1"

    def test_dialogue_properties(self):
        """Test dialogue properties."""
        assert self.dialogue.dialogue_label == self.dialogue_label
        assert self.dialogue.incomplete_dialogue_label == self.dialogue_label
        assert self.dialogue.agent_address == self.agent_address

        self.dialogue.agent_address = "this agent's address"
        assert self.dialogue.agent_address == "this agent's address"

        assert self.dialogue.role == Dialogue.Role.ROLE1
        assert str(self.dialogue.role) == "role1"

        self.dialogue.role = Dialogue.Role.ROLE2
        assert self.dialogue.role == Dialogue.Role.ROLE2

        assert self.dialogue.rules.initial_performatives == frozenset(
            {DefaultMessage.Performative.BYTES}
        )
        assert self.dialogue.rules.terminal_performatives == frozenset(
            {DefaultMessage.Performative.ERROR}
        )
        assert self.dialogue.rules.valid_replies == {
            DefaultMessage.Performative.BYTES: frozenset(
                {DefaultMessage.Performative.BYTES, DefaultMessage.Performative.ERROR}
            ),
            DefaultMessage.Performative.ERROR: frozenset(),
        }
        assert self.dialogue.rules.get_valid_replies(
            DefaultMessage.Performative.BYTES
        ) == frozenset(
            {DefaultMessage.Performative.BYTES, DefaultMessage.Performative.ERROR}
        )
        assert self.dialogue.rules.get_valid_replies(
            DefaultMessage.Performative.ERROR
        ) == frozenset({})

        assert self.dialogue.is_self_initiated

        assert self.dialogue.last_incoming_message is None
        assert self.dialogue.last_outgoing_message is None
        assert self.dialogue.last_message is None
        assert self.dialogue.get_message(3) is None
        assert self.dialogue.is_empty

    def test_update_positive(self):
        """Positive test for the 'update' method."""
        valid_initial_msg = DefaultMessage(
            dialogue_reference=(str(1), ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        valid_initial_msg.to = self.opponent_address

        assert self.dialogue.update(valid_initial_msg)
        assert self.dialogue.last_outgoing_message == valid_initial_msg

    def test_update_sets_missing_sender(self):
        """Test the 'update' method sets the missing counterparty field of the input message."""
        valid_initial_msg = DefaultMessage(
            dialogue_reference=(str(1), ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        valid_initial_msg.to = self.opponent_address

        assert self.dialogue.update(valid_initial_msg)
        assert self.dialogue.last_outgoing_message == valid_initial_msg
        assert (
            self.dialogue.last_outgoing_message.sender
            == self.dialogue.dialogue_label.dialogue_starter_addr
        )

    def test_update_negative_not_is_extendible(self):
        """Negative test for the 'update' method: dialogue is not extendable with the input message."""
        invalid_message_id = DefaultMessage(
            dialogue_reference=(str(1), ""),
            message_id=0,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        invalid_message_id.to = self.opponent_address

        assert not self.dialogue.update(invalid_message_id)
        assert self.dialogue.last_outgoing_message is None

    def test_reply_positive(self):
        """Positive test for the 'reply' method."""
        initial_msg = DefaultMessage(
            dialogue_reference=(str(1), ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        initial_msg.sender = self.agent_address
        initial_msg.to = self.opponent_address

        assert self.dialogue.update(initial_msg)

        self.dialogue.reply(
            target_message=initial_msg,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello Back",
        )

        assert self.dialogue.last_message.message_id == 2

    def test_reply_negative_invalid_target(self):
        """Negative test for the 'reply' method: target message is not in the dialogue."""
        initial_msg = DefaultMessage(
            dialogue_reference=(str(1), ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        initial_msg.sender = self.agent_address
        initial_msg.to = self.opponent_address

        assert self.dialogue.update(initial_msg)

        invalid_initial_msg = DefaultMessage(
            dialogue_reference=(str(1), ""),
            message_id=2,
            target=1,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello There",
        )
        invalid_initial_msg.sender = self.agent_address
        invalid_initial_msg.to = self.opponent_address

        try:
            self.dialogue.reply(
                target_message=invalid_initial_msg,
                performative=DefaultMessage.Performative.BYTES,
                content=b"Hello Back",
            )
            result = True
        except Exception:
            result = False

        assert not result

    def test_basic_rules_positive(self):
        """Positive test for the '_basic_rules' method."""
        valid_initial_msg = DefaultMessage(
            dialogue_reference=(str(1), ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        valid_initial_msg.sender = self.agent_address
        valid_initial_msg.to = self.opponent_address

        assert self.dialogue._basic_rules(valid_initial_msg)

    def test_basic_rules_negative_initial_message_invalid_dialogue_reference(self):
        """Negative test for the '_basic_rules' method: input message is the first message with invalid dialogue reference."""
        invalid_initial_msg = DefaultMessage(
            dialogue_reference=(str(2), ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        invalid_initial_msg.sender = self.agent_address
        invalid_initial_msg.to = self.opponent_address

        assert not self.dialogue._basic_rules(invalid_initial_msg)

    def test_basic_rules_negative_initial_message_invalid_message_id(self):
        """Negative test for the '_basic_rules' method: input message is the first message with invalid message id."""
        invalid_initial_msg = DefaultMessage(
            dialogue_reference=(str(1), ""),
            message_id=2,
            target=1,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        invalid_initial_msg.sender = self.agent_address
        invalid_initial_msg.to = self.opponent_address

        assert not self.dialogue._basic_rules(invalid_initial_msg)

    def test_basic_rules_negative_initial_message_invalid_target(self):
        """Negative test for the '_basic_rules' method: input message is the first message with invalid target."""
        invalid_initial_msg = DefaultMessage(
            dialogue_reference=(str(1), ""),
            message_id=1,
            target=1,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        invalid_initial_msg.sender = self.agent_address
        invalid_initial_msg.to = self.opponent_address

        assert not self.dialogue._basic_rules(invalid_initial_msg)

    def test_basic_rules_negative_initial_message_invalid_performative(self):
        """Negative test for the '_basic_rules' method: input message is the first message with invalid performative."""
        invalid_initial_msg = DefaultMessage(
            dialogue_reference=(str(1), ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.ERROR,
            error_code=DefaultMessage.ErrorCode.INVALID_MESSAGE,
            error_msg="some_error_message",
            error_data={"some_data": b"some_bytes"},
        )
        invalid_initial_msg.sender = self.agent_address
        invalid_initial_msg.to = self.opponent_address

        assert not self.dialogue._basic_rules(invalid_initial_msg)

    def test_basic_rules_negative_non_initial_message_invalid_dialogue_reference(self):
        """Negative test for the '_basic_rules' method: input message is not the first message, and its dialogue reference is invalid."""
        valid_initial_msg = DefaultMessage(
            dialogue_reference=(str(1), ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        valid_initial_msg.sender = self.agent_address
        valid_initial_msg.to = self.opponent_address

        assert self.dialogue.update(valid_initial_msg)

        invalid_msg = DefaultMessage(
            dialogue_reference=(str(2), str(1)),
            message_id=2,
            target=1,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello back",
        )
        invalid_msg.sender = self.opponent_address
        invalid_msg.to = self.agent_address

        assert not self.dialogue._basic_rules(invalid_msg)

    def test_basic_rules_negative_non_initial_message_invalid_message_id(self):
        """Negative test for the '_basic_rules' method: input message is not the first message, and its message id is invalid."""
        valid_initial_msg = DefaultMessage(
            dialogue_reference=(str(1), ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        valid_initial_msg.sender = self.agent_address
        valid_initial_msg.to = self.opponent_address

        assert self.dialogue.update(valid_initial_msg)

        invalid_msg = DefaultMessage(
            dialogue_reference=(str(1), str(1)),
            message_id=3,
            target=1,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello back",
        )
        valid_initial_msg.sender = self.opponent_address
        invalid_msg.to = self.agent_address

        assert not self.dialogue._basic_rules(invalid_msg)

    def test_basic_rules_negative_non_initial_message_invalid_target(self):
        """Negative test for the '_basic_rules' method: input message is not the first message, and its target is invalid."""
        valid_initial_msg = DefaultMessage(
            dialogue_reference=(str(1), ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        valid_initial_msg.sender = self.agent_address
        valid_initial_msg.to = self.opponent_address

        assert self.dialogue.update(valid_initial_msg)

        invalid_msg = DefaultMessage(
            dialogue_reference=(str(1), str(1)),
            message_id=2,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello back",
        )
        invalid_msg.sender = self.opponent_address
        invalid_msg.to = self.agent_address

        assert not self.dialogue._basic_rules(invalid_msg)

    def test_basic_rules_negative_non_initial_message_invalid_performative(self):
        """Negative test for the '_basic_rules' method: input message is not the first message, and its performative is invalid."""
        pytest.skip(
            "to test this, the test Dialogue model must be changed to have an invalid non-initial performative."
        )

    def test_additional_rules_positive(self):
        """Positive test for the '_additional_rules' method."""
        valid_initial_msg = DefaultMessage(
            dialogue_reference=(str(1), ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        valid_initial_msg.sender = self.agent_address
        valid_initial_msg.to = self.opponent_address

        assert self.dialogue.update(valid_initial_msg)

        valid_second_msg = DefaultMessage(
            dialogue_reference=(str(1), str(1)),
            message_id=2,
            target=1,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello back",
        )
        valid_second_msg.sender = self.opponent_address
        valid_second_msg.to = self.agent_address

        assert self.dialogue.update(valid_second_msg)

        valid_third_msg = DefaultMessage(
            dialogue_reference=(str(1), str(1)),
            message_id=3,
            target=2,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello back 2",
        )
        valid_third_msg.sender = self.agent_address
        valid_third_msg.to = self.opponent_address

        assert self.dialogue._additional_rules(valid_third_msg)

    def test_additional_rules_negative_invalid_target(self):
        """Negative test for the '_additional_rules' method: input message has invalid target (its target is not the last message of the dialogue)."""
        valid_initial_msg = DefaultMessage(
            dialogue_reference=(str(1), ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        valid_initial_msg.sender = self.agent_address
        valid_initial_msg.to = self.opponent_address

        assert self.dialogue.update(valid_initial_msg)

        valid_second_msg = DefaultMessage(
            dialogue_reference=(str(1), str(1)),
            message_id=2,
            target=1,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello back",
        )
        valid_second_msg.sender = self.opponent_address
        valid_second_msg.to = self.agent_address

        assert self.dialogue.update(valid_second_msg)

        invalid_third_msg = DefaultMessage(
            dialogue_reference=(str(1), str(1)),
            message_id=3,
            target=1,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello back 2",
        )
        invalid_third_msg.sender = self.agent_address
        invalid_third_msg.to = self.opponent_address

        assert not self.dialogue._additional_rules(invalid_third_msg)

    def test_update_dialogue_label_positive(self):
        """Positive test for the 'update_dialogue_label' method."""
        valid_initial_msg = DefaultMessage(
            dialogue_reference=(str(1), ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        valid_initial_msg.sender = self.agent_address
        valid_initial_msg.to = self.opponent_address

        assert self.dialogue.update(valid_initial_msg)

        new_label = DialogueLabel(
            (str(1), str(1)), valid_initial_msg.to, self.agent_address
        )
        self.dialogue.update_dialogue_label(new_label)

        assert self.dialogue.dialogue_label == new_label

    def test_update_dialogue_negative(self):
        """Positive test for the 'update' method in dialogue with wrong message not belonging to dialogue."""
        valid_initial_msg = DefaultMessage(
            dialogue_reference=(str(2), ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        valid_initial_msg.sender = self.agent_address
        valid_initial_msg.to = self.opponent_address

        assert not self.dialogue.update(valid_initial_msg)

    def test_update_dialogue_label_negative_invalid_existing_label(self):
        """Negative test for the 'update_dialogue_label' method: existing dialogue reference is invalid."""
        incomplete_reference = (str(1), "")
        valid_initial_msg = DefaultMessage(
            dialogue_reference=incomplete_reference,
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        valid_initial_msg.sender = self.agent_address
        valid_initial_msg.to = self.opponent_address

        assert self.dialogue.update(valid_initial_msg)

        complete_reference = (str(1), str(1))
        valid_second_msg = DefaultMessage(
            dialogue_reference=complete_reference,
            message_id=2,
            target=1,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello back",
        )
        valid_second_msg.sender = self.opponent_address
        valid_second_msg.to = self.agent_address

        assert self.dialogue.update(valid_second_msg)

        new_label = DialogueLabel(
            complete_reference, valid_initial_msg.to, self.agent_address
        )
        self.dialogue.update_dialogue_label(new_label)
        assert self.dialogue.dialogue_label == new_label

        new_label = DialogueLabel(
            (str(1), str(2)), valid_initial_msg.to, self.agent_address
        )
        with pytest.raises(AssertionError):
            self.dialogue.update_dialogue_label(new_label)

        assert self.dialogue.dialogue_label != new_label

    def test_update_dialogue_label_negative_invalid_input_label(self):
        """Negative test for the 'update_dialogue_label' method: input dialogue label's dialogue reference is invalid."""
        valid_initial_msg = DefaultMessage(
            dialogue_reference=(str(1), ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        valid_initial_msg.sender = self.agent_address
        valid_initial_msg.to = self.opponent_address

        assert self.dialogue.update(valid_initial_msg)

        new_label = DialogueLabel(
            (str(2), ""), valid_initial_msg.to, self.agent_address
        )
        try:
            self.dialogue.update_dialogue_label(new_label)
            result = True
        except AssertionError:
            result = False

        assert not result
        assert self.dialogue.dialogue_label != new_label

    def test_interleave(self):
        """Test the '_interleave' method."""
        list_1 = [1, 3, 5, 7]
        list_2 = [2, 4, 6, 8]
        assert Dialogue._interleave(list_1, list_2) == [1, 2, 3, 4, 5, 6, 7, 8]

        list_3 = [1, 3, 4]
        list_4 = [2]
        assert Dialogue._interleave(list_3, list_4) == [1, 2, 3, 4]

    def test___str__1(self):
        """Test the '__str__' method: dialogue is self initiated"""
        valid_initial_msg = DefaultMessage(
            dialogue_reference=(str(1), ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        valid_initial_msg.sender = self.agent_address
        valid_initial_msg.to = self.opponent_address

        dialogue = self.dialogue.update(valid_initial_msg)
        assert dialogue is not None

        valid_second_msg = DefaultMessage(
            dialogue_reference=(str(1), str(1)),
            message_id=2,
            target=1,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello back",
        )
        valid_second_msg.sender = self.opponent_address
        valid_second_msg.to = self.agent_address

        dialogue = self.dialogue.update(valid_second_msg)
        assert dialogue is not None

        valid_third_msg = DefaultMessage(
            dialogue_reference=(str(1), str(1)),
            message_id=3,
            target=2,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello back 2",
        )
        valid_third_msg.sender = self.agent_address
        valid_third_msg.to = self.opponent_address

        assert self.dialogue.update(valid_third_msg)

        dialogue_str = (
            "Dialogue Label: 1__agent 2_agent 1\nbytes( )\nbytes( )\nbytes( )"
        )

        assert str(self.dialogue) == dialogue_str

    def test___str__2(self):
        """Test the '__str__' method: dialogue is other initiated"""
        valid_initial_msg = DefaultMessage(
            dialogue_reference=(str(1), ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        valid_initial_msg.sender = self.opponent_address
        valid_initial_msg.to = self.agent_address

        assert self.dialogue_opponent_started.update(valid_initial_msg)

        valid_second_msg = DefaultMessage(
            dialogue_reference=(str(1), str(1)),
            message_id=2,
            target=1,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello back",
        )
        valid_second_msg.sender = self.agent_address
        valid_second_msg.to = self.opponent_address

        assert self.dialogue_opponent_started.update(valid_second_msg)

        valid_third_msg = DefaultMessage(
            dialogue_reference=(str(1), str(1)),
            message_id=3,
            target=2,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello back 2",
        )
        valid_third_msg.sender = self.opponent_address
        valid_third_msg.to = self.agent_address

        assert self.dialogue_opponent_started.update(valid_third_msg)

        dialogue_str = (
            "Dialogue Label: 1_1_agent 2_agent 2\nbytes( )\nbytes( )\nbytes( )"
        )

        assert str(self.dialogue_opponent_started) == dialogue_str


class TestDialogueStats:
    """Test for DialogueStats."""

    @classmethod
    def setup(cls):
        """Initialise the environment to test DialogueStats."""
        cls.agent_address = "agent 1"
        cls.opponent_address = "agent 2"
        cls.dialogue_label = DialogueLabel(
            dialogue_reference=(str(1), ""),
            dialogue_opponent_addr=cls.opponent_address,
            dialogue_starter_addr=cls.agent_address,
        )
        cls.dialogue = Dialogue(dialogue_label=cls.dialogue_label)
        end_states = frozenset(
            {Dialogue.EndState.SUCCESSFUL, Dialogue.EndState.FAILED}
        )  # type: FrozenSet[BaseDialogue.EndState]
        cls.dialogue_stats = DialogueStats(end_states)

    def test_properties(self):
        """Test dialogue properties."""
        assert isinstance(self.dialogue_stats.self_initiated, dict)
        assert self.dialogue_stats.self_initiated == {
            Dialogue.EndState.SUCCESSFUL: 0,
            Dialogue.EndState.FAILED: 0,
        }
        assert self.dialogue_stats.other_initiated == {
            Dialogue.EndState.SUCCESSFUL: 0,
            Dialogue.EndState.FAILED: 0,
        }

    def test_add_dialogue_endstate(self):
        """Test for the 'add_dialogue_endstate' method."""
        assert self.dialogue_stats.self_initiated == {
            Dialogue.EndState.SUCCESSFUL: 0,
            Dialogue.EndState.FAILED: 0,
        }
        assert self.dialogue_stats.other_initiated == {
            Dialogue.EndState.SUCCESSFUL: 0,
            Dialogue.EndState.FAILED: 0,
        }

        self.dialogue_stats.add_dialogue_endstate(Dialogue.EndState.SUCCESSFUL, True)
        assert self.dialogue_stats.self_initiated == {
            Dialogue.EndState.SUCCESSFUL: 1,
            Dialogue.EndState.FAILED: 0,
        }
        assert self.dialogue_stats.other_initiated == {
            Dialogue.EndState.SUCCESSFUL: 0,
            Dialogue.EndState.FAILED: 0,
        }

        self.dialogue_stats.add_dialogue_endstate(Dialogue.EndState.FAILED, False)
        assert self.dialogue_stats.self_initiated == {
            Dialogue.EndState.SUCCESSFUL: 1,
            Dialogue.EndState.FAILED: 0,
        }
        assert self.dialogue_stats.other_initiated == {
            Dialogue.EndState.SUCCESSFUL: 0,
            Dialogue.EndState.FAILED: 1,
        }


class TestDialoguesBase:
    """Test for Dialogues."""

    @classmethod
    def setup(cls):
        """Initialise the environment to test Dialogue."""
        cls.agent_address = "agent 1"
        cls.opponent_address = "agent 2"
        cls.dialogue_label = DialogueLabel(
            dialogue_reference=(str(1), ""),
            dialogue_opponent_addr=cls.opponent_address,
            dialogue_starter_addr=cls.agent_address,
        )
        cls.dialogue = Dialogue(dialogue_label=cls.dialogue_label)
        cls.dialogues = Dialogues(cls.agent_address)

    def test_dialogues_properties(self):
        """Test dialogue properties."""
        assert self.dialogues.dialogues == dict()
        assert self.dialogues.agent_address == self.agent_address
        assert self.dialogues.dialogue_stats.other_initiated == {
            Dialogue.EndState.SUCCESSFUL: 0,
            Dialogue.EndState.FAILED: 0,
        }
        assert self.dialogues.dialogue_stats.self_initiated == {
            Dialogue.EndState.SUCCESSFUL: 0,
            Dialogue.EndState.FAILED: 0,
        }

    def test_new_self_initiated_dialogue_reference(self):
        """Test the 'new_self_initiated_dialogue_reference' method."""
        nonce = self.dialogues._dialogue_nonce
        assert self.dialogues.new_self_initiated_dialogue_reference() == (
            str(nonce + 1),
            "",
        )

        self.dialogues._create_opponent_initiated(
            self.opponent_address, ("1", ""), Dialogue.Role.ROLE1
        )  # increments dialogue nonce
        assert self.dialogues.new_self_initiated_dialogue_reference() == (
            str(nonce + 3),
            "",
        )

    def test_create_positive(self):
        """Positive test for the 'create' method."""
        assert len(self.dialogues.dialogues) == 0
        self.dialogues.create(
            self.opponent_address, DefaultMessage.Performative.BYTES, content=b"Hello"
        )
        assert len(self.dialogues.dialogues) == 1

    def test_create_negative_incorrect_performative_content_combination(self):
        """Negative test for the 'create' method: invalid performative and content combination (i.e. invalid message)."""
        assert len(self.dialogues.dialogues) == 0
        try:
            self.dialogues.create(
                self.opponent_address,
                DefaultMessage.Performative.ERROR,
                content=b"Hello",
            )
            result = True
        except Exception:
            result = False

        assert not result
        assert len(self.dialogues.dialogues) == 0

    def test_update_negative_invalid_label(self):
        """Negative test for the 'update' method: dialogue is not extendable with the input message."""
        invalid_message_id = DefaultMessage(
            dialogue_reference=("", ""),
            message_id=0,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        invalid_message_id.sender = self.agent_address
        invalid_message_id.to = self.opponent_address

        assert not self.dialogues.update(invalid_message_id)

    def test_update_positive_new_dialogue_by_other(self):
        """Positive test for the 'update' method: the input message is for a new dialogue dialogue by other."""
        initial_msg = DefaultMessage(
            dialogue_reference=(str(1), ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        initial_msg.sender = self.agent_address
        initial_msg.to = self.opponent_address

        assert len(self.dialogues.dialogues) == 0

        dialogue = self.dialogues.update(initial_msg)

        assert len(self.dialogues.dialogues) == 1
        assert dialogue is not None
        assert dialogue.last_message.dialogue_reference == (str(1), "")
        assert dialogue.last_message.message_id == 1
        assert dialogue.last_message.target == 0
        assert dialogue.last_message.performative == DefaultMessage.Performative.BYTES
        assert dialogue.last_message.content == b"Hello"

    def test_update_positive_new_dialogue_by_self(self):
        """Positive test for the 'update' method: the input message is for a new dialogue dialogue by self."""
        initial_msg = DefaultMessage(
            dialogue_reference=(str(1), ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        initial_msg.sender = self.agent_address
        initial_msg.to = self.opponent_address

        assert len(self.dialogues.dialogues) == 0

        dialogue = self.dialogues.update(initial_msg)

        assert len(self.dialogues.dialogues) == 1
        assert dialogue is not None
        assert dialogue.last_message.dialogue_reference == (str(1), "")
        assert dialogue.last_message.message_id == 1
        assert dialogue.last_message.target == 0
        assert dialogue.last_message.performative == DefaultMessage.Performative.BYTES
        assert dialogue.last_message.content == b"Hello"

    def test_update_positive_existing_dialogue(self):
        """Positive test for the 'update' method: the input message is for an existing dialogue."""
        self.dialogues.create(
            self.opponent_address, DefaultMessage.Performative.BYTES, content=b"Hello"
        )

        second_msg = DefaultMessage(
            dialogue_reference=(str(1), str(1)),
            message_id=2,
            target=1,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello back",
        )
        second_msg.sender = self.opponent_address
        second_msg.to = self.agent_address

        assert len(self.dialogues.dialogues) == 1

        dialogue = self.dialogues.update(second_msg)

        assert len(self.dialogues.dialogues) == 1
        assert dialogue is not None
        assert dialogue.last_message.dialogue_reference == (str(1), str(1))
        assert dialogue.last_message.message_id == 2
        assert dialogue.last_message.target == 1
        assert dialogue.last_message.performative == DefaultMessage.Performative.BYTES
        assert dialogue.last_message.content == b"Hello back"

    def test_update_positive_multiple_messages_by_self(self):
        """Positive test for the 'update' method: multiple messages by self is sent to the dialogue."""
        initial_msg = DefaultMessage(
            dialogue_reference=(str(1), ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        initial_msg.sender = self.agent_address
        initial_msg.to = self.opponent_address

        dialogue = self.dialogues.update(initial_msg)

        second_msg = DefaultMessage(
            dialogue_reference=(str(1), ""),
            message_id=2,
            target=1,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello back",
        )
        second_msg.sender = self.agent_address
        second_msg.to = self.opponent_address

        retrieved_dialogue = self.dialogues.update(second_msg)

        assert retrieved_dialogue.dialogue_label == dialogue.dialogue_label

    def test_update_negative_new_dialogue_by_self_no_to(self):
        """Negative test for the 'update' method: the 'to' field of the input message is not set."""
        initial_msg = DefaultMessage(
            dialogue_reference=(str(1), ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        initial_msg.sender = self.agent_address

        assert len(self.dialogues.dialogues) == 0

        with pytest.raises(ValueError):
            self.dialogues.update(initial_msg)

        assert len(self.dialogues.dialogues) == 0

    def test_update_negative_new_dialogue_by_self_no_sender(self):
        """Negative test for the 'update' method: the 'sender' field of the input message is not set."""
        initial_msg = DefaultMessage(
            dialogue_reference=(str(1), ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        initial_msg.to = self.opponent_address

        assert len(self.dialogues.dialogues) == 0

        with pytest.raises(ValueError):
            self.dialogues.update(initial_msg)

        assert len(self.dialogues.dialogues) == 0

    def test_update_negative_existing_dialogue_non_nonexistent(self):
        """Negative test for the 'update' method: the dialogue referred by the input message does not exist."""
        _, dialogue = self.dialogues.create(
            self.opponent_address, DefaultMessage.Performative.BYTES, content=b"Hello"
        )

        second_msg = DefaultMessage(
            dialogue_reference=(str(2), str(1)),
            message_id=2,
            target=1,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello back",
        )
        second_msg.sender = self.opponent_address
        second_msg.to = self.agent_address

        updated_dialogue = self.dialogues.update(second_msg)

        assert updated_dialogue is None
        assert self.dialogues.dialogues[
            dialogue.dialogue_label
        ].last_message.dialogue_reference == (str(1), "")
        assert (
            self.dialogues.dialogues[dialogue.dialogue_label].last_message.message_id
            == 1
        )
        assert (
            self.dialogues.dialogues[dialogue.dialogue_label].last_message.target == 0
        )
        assert (
            self.dialogues.dialogues[dialogue.dialogue_label].last_message.performative
            == DefaultMessage.Performative.BYTES
        )
        assert (
            self.dialogues.dialogues[dialogue.dialogue_label].last_message.content
            == b"Hello"
        )

    def test_update_self_initiated_dialogue_label_on_message_with_complete_reference_positive(
        self,
    ):
        """Positive test for the '_update_self_initiated_dialogue_label_on_message_with_complete_reference' method."""
        _, dialogue = self.dialogues.create(
            self.opponent_address, DefaultMessage.Performative.BYTES, content=b"Hello"
        )

        second_msg = DefaultMessage(
            dialogue_reference=(str(1), str(1)),
            message_id=2,
            target=1,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello back",
        )
        second_msg.sender = self.opponent_address
        second_msg.to = self.agent_address

        self.dialogues._update_self_initiated_dialogue_label_on_message_with_complete_reference(
            second_msg
        )

        assert self.dialogues.dialogues[
            dialogue.dialogue_label
        ].dialogue_label.dialogue_reference == (str(1), str(1))

    def test_update_self_initiated_dialogue_label_on_message_with_complete_reference_negative_incorrect_reference(
        self,
    ):
        """Negative test for the '_update_self_initiated_dialogue_label_on_message_with_complete_reference' method: the input message has invalid dialogue reference."""
        _, dialogue = self.dialogues.create(
            self.opponent_address, DefaultMessage.Performative.BYTES, content=b"Hello"
        )

        second_msg = DefaultMessage(
            dialogue_reference=(str(2), str(1)),
            message_id=2,
            target=1,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello back",
        )
        second_msg.sender = self.opponent_address
        second_msg.to = self.agent_address

        self.dialogues._update_self_initiated_dialogue_label_on_message_with_complete_reference(
            second_msg
        )

        assert self.dialogues.dialogues[
            dialogue.dialogue_label
        ].dialogue_label.dialogue_reference == (str(1), "")

    def test_get_dialogue_positive_1(self):
        """Positive test for the 'get_dialogue' method: the dialogue is self initiated and the second message is by the other agent."""
        _, dialogue = self.dialogues.create(
            self.opponent_address, DefaultMessage.Performative.BYTES, content=b"Hello"
        )

        second_msg = DefaultMessage(
            dialogue_reference=(str(1), str(1)),
            message_id=2,
            target=1,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello back",
        )
        second_msg.sender = self.opponent_address
        second_msg.to = self.agent_address

        self.dialogues._update_self_initiated_dialogue_label_on_message_with_complete_reference(
            second_msg
        )

        assert self.dialogues.dialogues[
            dialogue.dialogue_label
        ].dialogue_label.dialogue_reference == (str(1), str(1))

        retrieved_dialogue = self.dialogues.get_dialogue(second_msg)

        assert retrieved_dialogue.dialogue_label == dialogue.dialogue_label

    def test_get_dialogue_positive_2(self):
        """Positive test for the 'get_dialogue' method: the dialogue is other initiated and the second message is by this agent."""
        initial_msg = DefaultMessage(
            dialogue_reference=(str(1), ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        initial_msg.sender = self.opponent_address
        initial_msg.to = self.agent_address

        dialogue = self.dialogues.update(initial_msg)

        second_msg = DefaultMessage(
            dialogue_reference=(str(1), str(1)),
            message_id=2,
            target=1,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello back",
        )
        second_msg.sender = self.agent_address
        second_msg.to = self.opponent_address

        retrieved_dialogue = self.dialogues.get_dialogue(second_msg)

        assert retrieved_dialogue.dialogue_label == dialogue.dialogue_label

    def test_get_dialogue_negative_invalid_reference(self):
        """Negative test for the 'get_dialogue' method: the inpute message has invalid dialogue reference."""
        _, dialogue = self.dialogues.create(
            self.opponent_address, DefaultMessage.Performative.BYTES, content=b"Hello"
        )

        second_msg = DefaultMessage(
            dialogue_reference=(str(1), str(1)),
            message_id=2,
            target=1,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello back",
        )
        second_msg.sender = self.opponent_address
        second_msg.to = self.agent_address

        dialogue = self.dialogues.update(second_msg)
        assert dialogue is not None

        third_msg = DefaultMessage(
            dialogue_reference=(str(2), str(1)),
            message_id=2,
            target=1,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello back",
        )
        third_msg.sender = self.agent_address
        third_msg.to = self.opponent_address

        retrieved_dialogue = self.dialogues.get_dialogue(third_msg)

        assert retrieved_dialogue is None

    def test_get_dialogue_from_label_positive(self):
        """Positive test for the 'get_dialogue_from_label' method."""
        _, dialogue = self.dialogues.create(
            self.opponent_address, DefaultMessage.Performative.BYTES, content=b"Hello"
        )

        retrieved_dialogue = self.dialogues.get_dialogue_from_label(
            dialogue.dialogue_label
        )
        assert retrieved_dialogue.dialogue_label == dialogue.dialogue_label

    def test_get_dialogue_from_label_negative_incorrect_input_label(self):
        """Negative test for the 'get_dialogue_from_label' method: the input dialogue label does not exist."""
        _, dialogue = self.dialogues.create(
            self.opponent_address, DefaultMessage.Performative.BYTES, content=b"Hello"
        )

        incorrect_label = DialogueLabel(
            (str(1), "error"), self.opponent_address, self.agent_address
        )

        retrieved_dialogue = self.dialogues.get_dialogue_from_label(incorrect_label)
        assert retrieved_dialogue is None

    def test_create_self_initiated_positive(self):
        """Positive test for the '_create_self_initiated' method."""
        assert len(self.dialogues.dialogues) == 0

        self.dialogues._create_self_initiated(
            self.opponent_address, (str(1), ""), Dialogue.Role.ROLE1
        )
        assert len(self.dialogues.dialogues) == 1

    def test_create_opponent_initiated_positive(self):
        """Positive test for the '_create_opponent_initiated' method."""
        assert len(self.dialogues.dialogues) == 0

        self.dialogues._create_opponent_initiated(
            self.opponent_address, (str(1), ""), Dialogue.Role.ROLE2
        )
        assert len(self.dialogues.dialogues) == 1

    def test_create_opponent_initiated_negative_invalid_input_dialogue_reference(self):
        """Negative test for the '_create_opponent_initiated' method: input dialogue label has invalid dialogue reference."""
        assert len(self.dialogues.dialogues) == 0

        try:
            self.dialogues._create_opponent_initiated(
                self.opponent_address, ("", str(1)), Dialogue.Role.ROLE2
            )
            result = True
        except AssertionError:
            result = False

        assert not result
        assert len(self.dialogues.dialogues) == 0

    def test_next_dialogue_nonce(self):
        """Test the '_next_dialogue_nonce' method."""
        assert self.dialogues._dialogue_nonce == 0
        assert self.dialogues._next_dialogue_nonce() == 1
        assert self.dialogues._dialogue_nonce == 1
