# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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
import re
from typing import FrozenSet, Tuple, Type, cast
from unittest.mock import Mock, patch

import pytest

from aea.common import Address
from aea.configurations.base import PublicId
from aea.exceptions import AEAEnforceError
from aea.helpers.storage.generic_storage import Storage
from aea.protocols.base import Message
from aea.protocols.dialogue.base import BasicDialoguesStorage
from aea.protocols.dialogue.base import Dialogue as BaseDialogue
from aea.protocols.dialogue.base import DialogueLabel, DialogueMessage, DialogueStats
from aea.protocols.dialogue.base import Dialogues as BaseDialogues
from aea.protocols.dialogue.base import (
    InvalidDialogueMessage,
    PersistDialoguesStorage,
    PersistDialoguesStorageWithOffloading,
    find_caller_object,
)
from aea.skills.base import SkillComponent

from packages.fetchai.protocols.default.custom_types import ErrorCode
from packages.fetchai.protocols.default.message import DefaultMessage
from packages.fetchai.protocols.state_update.message import StateUpdateMessage

from tests.common.utils import wait_for_condition


class Dialogue(BaseDialogue):
    """This concrete class defines a dialogue."""

    INITIAL_PERFORMATIVES = frozenset({DefaultMessage.Performative.BYTES})
    TERMINAL_PERFORMATIVES = frozenset({DefaultMessage.Performative.ERROR})
    VALID_REPLIES = {
        DefaultMessage.Performative.BYTES: frozenset(
            {DefaultMessage.Performative.BYTES, DefaultMessage.Performative.ERROR}
        ),
        DefaultMessage.Performative.ERROR: frozenset(),
    }

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
        self_address: Address = "agent 1",
        role: BaseDialogue.Role = Role.ROLE1,
    ) -> None:
        """
        Initialize a dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param self_address: the address of the entity for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for
        :return: None
        """
        BaseDialogue.__init__(
            self,
            dialogue_label=dialogue_label,
            self_address=self_address,
            role=role,
            message_class=message_class,
        )


class Dialogues(BaseDialogues):
    """This class gives a concrete definition of dialogues."""

    END_STATES = frozenset(
        {Dialogue.EndState.SUCCESSFUL, Dialogue.EndState.FAILED}
    )  # type: FrozenSet[BaseDialogue.EndState]

    def __init__(
        self,
        self_address: Address,
        message_class=DefaultMessage,
        dialogue_class=Dialogue,
        keep_terminal_state_dialogues=None,
    ) -> None:
        """
        Initialize dialogues.

        :param self_address: the address of the entity for whom dialogues are maintained
        :return: None
        """

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return Dialogue.Role.ROLE1

        BaseDialogues.__init__(
            self,
            self_address=self_address,
            end_states=cast(FrozenSet[BaseDialogue.EndState], self.END_STATES),
            message_class=message_class,
            dialogue_class=dialogue_class,
            role_from_first_message=role_from_first_message,
            keep_terminal_state_dialogues=keep_terminal_state_dialogues,
        )


def test_dialogue_message_python():
    """Test DiallogueMessage."""
    dialogue_message = DialogueMessage(DefaultMessage.Performative.BYTES)
    assert isinstance(dialogue_message.performative, Message.Performative)

    assert dialogue_message.performative == DefaultMessage.Performative.BYTES
    assert dialogue_message.contents == {}
    assert dialogue_message.is_incoming is None
    assert dialogue_message.target is None


class TestDialogueLabel:
    """Test for DialogueLabel."""

    @classmethod
    def setup(cls):
        """Initialise the environment to test DialogueLabel."""
        cls.agent_address = "agent 1"
        cls.opponent_address = "agent 2"
        cls.dialogue_starter_ref = str(1)
        cls.dialogue_label = DialogueLabel(
            dialogue_reference=(
                cls.dialogue_starter_ref,
                Dialogue.UNASSIGNED_DIALOGUE_REFERENCE,
            ),
            dialogue_opponent_addr=cls.opponent_address,
            dialogue_starter_addr=cls.agent_address,
        )

    def test_all_methods(self):
        """Test the DialogueLabel."""
        assert self.dialogue_label.dialogue_reference == (
            self.dialogue_starter_ref,
            Dialogue.UNASSIGNED_DIALOGUE_REFERENCE,
        )
        assert (
            self.dialogue_label.dialogue_starter_reference == self.dialogue_starter_ref
        )
        assert (
            self.dialogue_label.dialogue_responder_reference
            == Dialogue.UNASSIGNED_DIALOGUE_REFERENCE
        )
        assert self.dialogue_label.dialogue_opponent_addr == self.opponent_address
        assert self.dialogue_label.dialogue_starter_addr == self.agent_address
        assert str(self.dialogue_label) == "{}_{}_{}_{}".format(
            self.dialogue_label.dialogue_starter_reference,
            self.dialogue_label.dialogue_responder_reference,
            self.dialogue_label.dialogue_opponent_addr,
            self.dialogue_label.dialogue_starter_addr,
        )

        dialogue_label_eq = DialogueLabel(
            dialogue_reference=(
                self.dialogue_starter_ref,
                Dialogue.UNASSIGNED_DIALOGUE_REFERENCE,
            ),
            dialogue_opponent_addr=self.opponent_address,
            dialogue_starter_addr=self.agent_address,
        )

        assert dialogue_label_eq == self.dialogue_label

        dialogue_label_not_eq = "This is a test"

        assert not dialogue_label_not_eq == self.dialogue_label

        assert hash(dialogue_label_eq) == hash(self.dialogue_label)

        assert self.dialogue_label.json == dict(
            dialogue_starter_reference=self.dialogue_starter_ref,
            dialogue_responder_reference=Dialogue.UNASSIGNED_DIALOGUE_REFERENCE,
            dialogue_opponent_addr=self.opponent_address,
            dialogue_starter_addr=self.agent_address,
        )
        assert DialogueLabel.from_json(self.dialogue_label.json) == self.dialogue_label
        assert DialogueLabel.from_str(str(self.dialogue_label)) == self.dialogue_label
        assert not self.dialogue_label.is_complete()

        (
            incomplete_dialogue_label,
            complete_dialogue_label,
        ) = self.dialogue_label.get_both_versions()
        assert incomplete_dialogue_label.dialogue_reference == (
            self.dialogue_label.dialogue_starter_reference,
            Dialogue.UNASSIGNED_DIALOGUE_REFERENCE,
        )
        assert complete_dialogue_label is None


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

        # convenient messages to reuse across tests
        cls.valid_message_1_by_self = DefaultMessage(
            dialogue_reference=(str(1), ""),
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        cls.valid_message_1_by_self.sender = cls.agent_address
        cls.valid_message_1_by_self.to = cls.opponent_address

        cls.valid_message_2_by_other = DefaultMessage(
            dialogue_reference=(str(1), str(1)),
            message_id=-1,
            target=1,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello back",
        )
        cls.valid_message_2_by_other.sender = cls.opponent_address
        cls.valid_message_2_by_other.to = cls.agent_address

        cls.valid_message_3_by_self = DefaultMessage(
            dialogue_reference=(str(1), str(1)),
            message_id=2,
            target=-1,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello back 2",
        )
        cls.valid_message_3_by_self.sender = cls.agent_address
        cls.valid_message_3_by_self.to = cls.opponent_address

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
        assert self.dialogue.dialogue_labels == {self.dialogue_label}
        assert self.dialogue.self_address == self.agent_address

        assert self.dialogue.role == Dialogue.Role.ROLE1
        assert str(self.dialogue.role) == "role1"

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
        assert self.dialogue.message_class == DefaultMessage

        assert self.dialogue.is_self_initiated

        assert self.dialogue.last_incoming_message is None
        assert self.dialogue.last_outgoing_message is None
        assert self.dialogue.last_message is None

        assert self.dialogue.is_empty

    def test_counterparty_from_message(self):
        """Test the 'counterparty_from_message' method."""
        assert (
            self.dialogue._counterparty_from_message(self.valid_message_1_by_self)
            == self.opponent_address
        )
        assert (
            self.dialogue._counterparty_from_message(self.valid_message_2_by_other)
            == self.opponent_address
        )

    def test_is_message_by_self(self):
        """Test the 'is_message_by_self' method."""
        assert self.dialogue._is_message_by_self(self.valid_message_1_by_self)
        assert not self.dialogue._is_message_by_self(self.valid_message_2_by_other)

    def test_is_message_by_other(self):
        """Test the 'is_message_by_other' method."""
        assert not self.dialogue._is_message_by_other(self.valid_message_1_by_self)
        assert self.dialogue._is_message_by_other(self.valid_message_2_by_other)

    def test_try_get_message(self):
        """Test the 'try_get_message' method."""
        assert (
            self.dialogue.get_message_by_id(self.valid_message_1_by_self.message_id)
            is None
        )
        self.dialogue._update(self.valid_message_1_by_self)
        assert (
            self.dialogue.get_message_by_id(self.valid_message_1_by_self.message_id)
            == self.valid_message_1_by_self
        )

        assert (
            self.dialogue.get_message_by_id(self.valid_message_2_by_other.message_id)
            is None
        )
        self.dialogue._update(self.valid_message_2_by_other)
        assert (
            self.dialogue.get_message_by_id(self.valid_message_2_by_other.message_id)
            == self.valid_message_2_by_other
        )

    def test_has_message_id(self):
        """Test the 'has_message_id' method."""
        assert self.dialogue._has_message_id(1) is False

        self.dialogue._update(self.valid_message_1_by_self)
        assert self.dialogue._has_message_id(1) is True

        assert self.dialogue._has_message_id(2) is False

    def test_update_positive(self):
        """Positive test for the 'update' method."""
        self.dialogue._update(self.valid_message_1_by_self)
        assert self.dialogue.last_outgoing_message == self.valid_message_1_by_self

    def test_update_positive_multiple_messages_by_self(self):
        """Positive test for the 'update' method: multiple messages by self is sent to the dialogue."""
        self.dialogue._update(self.valid_message_1_by_self)

        valid_message_2_by_self = DefaultMessage(
            dialogue_reference=(str(1), ""),
            message_id=2,
            target=1,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello back",
        )
        valid_message_2_by_self.sender = self.agent_address
        valid_message_2_by_self.to = self.opponent_address

        self.dialogue._update(valid_message_2_by_self)

        assert self.dialogue.last_message.message_id == 2

    def test_terminal_state_callback(self):
        """Test dialogue terminal state callback works."""
        called = False

        def callback(dialogue):
            nonlocal called
            called = True

        self.dialogue.add_terminal_state_callback(callback)
        self.dialogue._update(self.valid_message_1_by_self)

        self.dialogue.reply(
            target_message=self.valid_message_1_by_self,
            performative=DefaultMessage.Performative.ERROR,
            error_code=ErrorCode.UNSUPPORTED_PROTOCOL,
            error_msg="oops",
            error_data={},
        )

        assert called

    def test_update_negative_is_valid_next_message_fails(self):
        """Negative test for the 'update' method: input message is invalid with respect to the dialogue."""
        invalid_message_1_by_self = DefaultMessage(
            dialogue_reference=(str(1), ""),
            message_id=200,
            target=1,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        invalid_message_1_by_self.sender = self.agent_address
        invalid_message_1_by_self.to = self.opponent_address

        with pytest.raises(
            InvalidDialogueMessage,
            match=r"Message .* is invalid with respect to this dialogue. Error: Invalid message_id. Expected .*. Found 200.",
        ):
            self.dialogue._update(invalid_message_1_by_self)

        assert self.dialogue.last_outgoing_message is None

    def test_update_dialogue_negative_message_does_not_belong_to_dialogue(self):
        """Negative test for the 'update' method in dialogue with wrong message not belonging to dialogue."""
        invalid_message_1_by_self = DefaultMessage(
            dialogue_reference=(str(2), ""),
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        invalid_message_1_by_self.sender = self.agent_address
        invalid_message_1_by_self.to = self.opponent_address

        with pytest.raises(InvalidDialogueMessage) as cm:
            self.dialogue._update(invalid_message_1_by_self)
        assert str(cm.value) == (
            "The message 1 does not belong to this dialogue."
            "The dialogue reference of the message is {}, while the dialogue reference of the dialogue is {}".format(
                invalid_message_1_by_self.dialogue_reference,
                self.dialogue.dialogue_label.dialogue_reference,
            )
        )
        assert self.dialogue.is_empty

    def test_is_belonging_to_dialogue(self):
        """Test for the '_is_belonging_to_dialogue' method"""
        valid_message_2_by_self = DefaultMessage(
            dialogue_reference=(str(2), ""),
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        valid_message_2_by_self.sender = self.agent_address
        valid_message_2_by_self.to = self.opponent_address

        assert self.dialogue._is_belonging_to_dialogue(self.valid_message_1_by_self)
        assert not self.dialogue._is_belonging_to_dialogue(valid_message_2_by_self)

    def test_reply_positive(self):
        """Positive test for the 'reply' method."""
        self.dialogue._update(self.valid_message_1_by_self)

        self.dialogue.reply(
            target_message=self.valid_message_1_by_self,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello Back",
        )

        assert self.dialogue.last_message.message_id == 2

    def test_reply_negative_empty_dialogue(self):
        """Negative test for the 'reply' method: target message is not in the dialogue."""
        with pytest.raises(ValueError) as cm:
            self.dialogue.reply(
                target_message=self.valid_message_1_by_self,
                performative=DefaultMessage.Performative.BYTES,
                content=b"Hello Back",
            )
        assert str(cm.value) == "Cannot reply in an empty dialogue!"
        assert self.dialogue.is_empty

    def test_reply_negative_target_does_not_exist(self):
        """Negative test for the 'reply' method: target is not in the dialogue."""
        self.dialogue._update(self.valid_message_1_by_self)
        with pytest.raises(ValueError) as cm:
            self.dialogue.reply(
                target=10,
                performative=DefaultMessage.Performative.BYTES,
                content=b"Hello Back",
            )
        assert str(cm.value) == "No target message found!"

    def test_reply_negative_target_message_target_mismatch(self):
        """Negative test for the 'reply' method: target message and target provided but do not match."""
        self.dialogue._update(self.valid_message_1_by_self)
        assert self.dialogue.last_message.message_id == 1

        with pytest.raises(AEAEnforceError) as cm:
            self.dialogue.reply(
                target_message=self.valid_message_1_by_self,
                target=2,
                performative=DefaultMessage.Performative.BYTES,
                content=b"Hello Back",
            )
        assert str(cm.value) == "The provided target and target_message do not match."
        assert self.dialogue.last_message.message_id == 1

    def test_reply_negative_invalid_target(self):
        """Negative test for the 'reply' method: target message is not in the dialogue."""
        self.dialogue._update(self.valid_message_1_by_self)
        assert self.dialogue.last_message.message_id == 1

        invalid_message_1_by_self = DefaultMessage(
            dialogue_reference=(str(1), ""),
            message_id=2,
            target=1,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello There",
        )
        invalid_message_1_by_self.sender = self.agent_address
        invalid_message_1_by_self.to = self.opponent_address

        with pytest.raises(AEAEnforceError) as cm:
            self.dialogue.reply(
                target_message=invalid_message_1_by_self,
                performative=DefaultMessage.Performative.BYTES,
                content=b"Hello Back",
            )
        assert str(cm.value) == "The target message does not exist in this dialogue."
        assert self.dialogue.last_message.message_id == 1

    def test_is_valid_next_message_positive(self):
        """Positive test for the 'validate_next_message' method"""
        self.dialogue._update(self.valid_message_1_by_self)
        self.dialogue._update(self.valid_message_2_by_other)

        result, msg = self.dialogue._validate_next_message(self.valid_message_3_by_self)
        assert result is True
        assert msg == "Message is valid with respect to this dialogue."

    def test_is_valid_next_message_negative_basic_validation_fails(self):
        """Negative test for the 'validate_next_message' method: basic_validation method fails"""
        invalid_message_1_by_self = DefaultMessage(
            dialogue_reference=(str(1), ""),
            message_id=2,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        invalid_message_1_by_self.sender = self.agent_address
        invalid_message_1_by_self.to = self.opponent_address

        result, msg = self.dialogue._validate_next_message(invalid_message_1_by_self)
        assert result is False
        assert msg == "Invalid message_id. Expected 1. Found 2."

    def test_is_valid_next_message_negative_additional_validation_fails(self):
        """Negative test for the 'validate_next_message' method: additional_validation method fails"""
        self.dialogue._update(self.valid_message_1_by_self)
        self.dialogue._update(self.valid_message_2_by_other)

        invalid_message_3_by_self = DefaultMessage(
            dialogue_reference=(str(1), str(1)),
            message_id=2,
            target=3,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello back 2",
        )
        invalid_message_3_by_self.sender = self.agent_address
        invalid_message_3_by_self.to = self.opponent_address

        result, msg = self.dialogue._validate_next_message(invalid_message_3_by_self)
        assert result is False
        assert "Invalid target" in msg

    def test_is_valid_next_message_negative_is_valid_fails(self):
        """Negative test for the 'validate_next_message' method: is_valid method fails"""

        def failing_custom_validation(self, message: Message) -> Tuple[bool, str]:
            return False, "some reason"

        with patch.object(
            self.dialogue.__class__, "_custom_validation", failing_custom_validation
        ):
            result, msg = self.dialogue._validate_next_message(
                self.valid_message_1_by_self
            )

        assert result is False
        assert msg == "some reason"

    def test_basic_validation_positive(self):
        """Positive test for the '_basic_validation' method."""
        result, msg = self.dialogue._basic_validation(self.valid_message_1_by_self)
        assert result is True
        assert msg == "The initial message passes basic validation."

        self.dialogue._update(self.valid_message_1_by_self)

        result, msg = self.dialogue._basic_validation(self.valid_message_2_by_other)
        assert result is True
        assert msg == "The non-initial message passes basic validation."

    def test_basic_validation_negative_initial_message_invalid(self):
        """Negative test for the '_basic_validation' method: initial message is invalid."""
        invalid_message_1_by_self = DefaultMessage(
            dialogue_reference=(str(1), ""),
            message_id=2,
            target=1,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        invalid_message_1_by_self.sender = self.agent_address
        invalid_message_1_by_self.to = self.opponent_address

        assert self.dialogue.is_empty
        result, msg = self.dialogue._basic_validation(invalid_message_1_by_self)
        assert result is False
        assert msg == "Invalid message_id. Expected 1. Found 2."

    @patch.object(BaseDialogue, "_validate_message_id", return_value=None)
    def test_basic_validation_negative_non_initial_message_invalid(self, *mocks):
        """Negative test for the '_basic_validation' method: non-initial message is invalid."""
        self.dialogue._update(self.valid_message_1_by_self)

        invalid_message_2_by_other = DefaultMessage(
            dialogue_reference=(str(1), str(1)),
            message_id=-1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello back",
        )
        invalid_message_2_by_other.sender = self.opponent_address
        invalid_message_2_by_other.to = self.agent_address

        result, msg = self.dialogue._basic_validation(invalid_message_2_by_other)
        assert result is False
        assert msg == "Invalid target. Expected a non-zero integer. Found 0."

    def test_basic_validation_initial_message_positive(self):
        """Positive test for the '_basic_validation_initial_message' method."""
        result, msg = self.dialogue._basic_validation_initial_message(
            self.valid_message_1_by_self
        )
        assert result is True
        assert msg == "The initial message passes basic validation."

    def test_basic_validation_initial_message_negative_invalid_dialogue_reference(self):
        """Negative test for the '_basic_validation' method: input message has invalid dialogue reference."""
        invalid_message_1_by_self = DefaultMessage(
            dialogue_reference=(str(2), ""),
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        invalid_message_1_by_self.sender = self.agent_address
        invalid_message_1_by_self.to = self.opponent_address

        result, msg = self.dialogue._basic_validation_initial_message(
            invalid_message_1_by_self
        )
        assert result is False
        assert msg == "Invalid dialogue_reference[0]. Expected 1. Found 2."

    def test_basic_validation_initial_message_negative_invalid_message_id(self):
        """Negative test for the '_basic_validation' method: input message has invalid message id."""
        invalid_message_1_by_self = DefaultMessage(
            dialogue_reference=(str(1), ""),
            message_id=200,
            target=1,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        invalid_message_1_by_self.sender = self.agent_address
        invalid_message_1_by_self.to = self.opponent_address

        result, msg = self.dialogue._basic_validation_initial_message(
            invalid_message_1_by_self
        )
        assert result is False
        assert re.match("Invalid message_id. Expected .*. Found 200.", msg)

    def test_basic_validation_initial_message_negative_invalid_target(self):
        """Negative test for the '_basic_validation_initial_message' method: input message has invalid target."""
        invalid_message_1_by_self = DefaultMessage(
            dialogue_reference=(str(1), ""),
            message_id=1,
            target=1,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        invalid_message_1_by_self.sender = self.agent_address
        invalid_message_1_by_self.to = self.opponent_address

        result, msg = self.dialogue._basic_validation_initial_message(
            invalid_message_1_by_self
        )
        assert result is False
        assert msg == "Invalid target. Expected 0. Found 1."

    def test_basic_validation_initial_message_negative_invalid_performative(self):
        """Negative test for the '_basic_validation_initial_message' method: input message has invalid performative."""
        invalid_initial_msg = DefaultMessage(
            dialogue_reference=(str(1), ""),
            performative=DefaultMessage.Performative.ERROR,
            error_code=DefaultMessage.ErrorCode.INVALID_MESSAGE,
            error_msg="some_error_message",
            error_data={"some_data": b"some_bytes"},
        )
        invalid_initial_msg.sender = self.agent_address
        invalid_initial_msg.to = self.opponent_address

        result, msg = self.dialogue._basic_validation_initial_message(
            invalid_initial_msg
        )
        assert result is False
        assert (
            msg
            == "Invalid initial performative. Expected one of {}. Found error.".format(
                self.dialogue.rules.initial_performatives
            )
        )

    def test_basic_validation_non_initial_message_positive(self):
        """Positive test for the '_basic_validation_non_initial_message' method."""
        self.dialogue._update(self.valid_message_1_by_self)

        result, msg = self.dialogue._basic_validation_non_initial_message(
            self.valid_message_2_by_other
        )
        assert result is True
        assert msg == "The non-initial message passes basic validation."

    def test_basic_validation_non_initial_message_negative_invalid_dialogue_reference(
        self,
    ):
        """Negative test for the '_basic_validation_non_initial_message' method: input message has invalid dialogue reference."""
        self.dialogue._update(self.valid_message_1_by_self)

        invalid_message_2_by_other = DefaultMessage(
            dialogue_reference=(str(2), str(1)),
            message_id=2,
            target=1,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello back",
        )
        invalid_message_2_by_other.sender = self.opponent_address
        invalid_message_2_by_other.to = self.agent_address

        result, msg = self.dialogue._basic_validation_non_initial_message(
            invalid_message_2_by_other
        )
        assert result is False
        assert msg == "Invalid dialogue_reference[0]. Expected 1. Found 2."

    def test_basic_validation_non_initial_message_negative_invalid_message_id(self):
        """Negative test for the '_basic_validation_non_initial_message' method: input message has invalid message id."""
        self.dialogue._update(self.valid_message_1_by_self)

        invalid_message_2_by_other = DefaultMessage(
            dialogue_reference=(str(1), str(1)),
            message_id=1000500000,
            target=1,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello back",
        )
        invalid_message_2_by_other.sender = self.opponent_address
        invalid_message_2_by_other.to = self.agent_address

        result, msg = self.dialogue._basic_validation_non_initial_message(
            invalid_message_2_by_other
        )
        assert result is False
        assert re.match("Invalid message_id. Expected .*. Found 1000500000", msg)

    @patch.object(BaseDialogue, "_validate_message_id", return_value=None)
    def test_basic_validation_non_initial_message_negative_invalid_target_1(
        self, *mocks
    ):
        """Negative test for the '_basic_validation_non_initial_message' method: input message has target less than 1."""
        self.dialogue._update(self.valid_message_1_by_self)

        invalid_message_2_by_other = DefaultMessage(
            dialogue_reference=(str(1), str(1)),
            message_id=2,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello back",
        )
        invalid_message_2_by_other.sender = self.opponent_address
        invalid_message_2_by_other.to = self.agent_address

        result, msg = self.dialogue._basic_validation_non_initial_message(
            invalid_message_2_by_other
        )
        assert result is False
        assert msg == "Invalid target. Expected a non-zero integer. Found 0."

    def test_basic_validation_non_initial_message_negative_invalid_target_2(self):
        """Negative test for the '_basic_validation_non_initial_message' method: input message has target greater than the id of the last existing message."""
        self.dialogue._update(self.valid_message_1_by_self)

        invalid_message_2_by_other = DefaultMessage(
            dialogue_reference=(str(1), str(1)),
            message_id=-1,
            target=2,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello back",
        )
        invalid_message_2_by_other.sender = self.opponent_address
        invalid_message_2_by_other.to = self.agent_address

        result, msg = self.dialogue._basic_validation_non_initial_message(
            invalid_message_2_by_other
        )
        assert result is False
        assert "Invalid target. Expected a value less than " in msg

    @patch.object(BaseDialogue, "_validate_message_id", return_value=None)
    def test_basic_validation_non_initial_message_negative_invalid_performative(
        self, *mocks
    ):
        """Negative test for the '_basic_validation_non_initial_message' method: input message has invalid performative."""
        self.dialogue._update(self.valid_message_1_by_self)

        invalid_message_2_by_other = StateUpdateMessage(
            dialogue_reference=(str(1), str(1)),
            message_id=Mock(),
            target=1,
            performative=StateUpdateMessage.Performative.APPLY,
            amount_by_currency_id={},
            quantities_by_good_id={},
        )
        invalid_message_2_by_other.sender = self.opponent_address
        invalid_message_2_by_other.to = self.agent_address

        result, msg = self.dialogue._basic_validation_non_initial_message(
            invalid_message_2_by_other
        )
        assert result is False
        assert msg == "Invalid performative. Expected one of {}. Found {}.".format(
            self.dialogue.rules.get_valid_replies(
                self.valid_message_1_by_self.performative
            ),
            invalid_message_2_by_other.performative,
        )

    def test_update_dialogue_label_positive(self):
        """Positive test for the 'update_dialogue_label' method."""
        self.dialogue._update(self.valid_message_1_by_self)

        new_label = DialogueLabel(
            (str(1), str(1)), self.valid_message_1_by_self.to, self.agent_address
        )
        self.dialogue._update_dialogue_label(new_label)

        assert self.dialogue.dialogue_label == new_label

    def test_update_dialogue_label_negative_invalid_existing_label(self):
        """Negative test for the 'update_dialogue_label' method: existing dialogue reference is invalid."""
        self.dialogue._update(self.valid_message_1_by_self)
        self.dialogue._update(self.valid_message_2_by_other)

        new_label = DialogueLabel(
            (str(1), str(1)), self.valid_message_1_by_self.to, self.agent_address
        )
        self.dialogue._update_dialogue_label(new_label)
        assert self.dialogue.dialogue_label == new_label

        new_label = DialogueLabel(
            (str(1), str(2)), self.valid_message_1_by_self.to, self.agent_address
        )
        with pytest.raises(AEAEnforceError) as cm:
            self.dialogue._update_dialogue_label(new_label)
        assert str(cm.value) == "Dialogue label cannot be updated."

        assert self.dialogue.dialogue_label != new_label

    def test_update_dialogue_label_negative_invalid_input_label(self):
        """Negative test for the 'update_dialogue_label' method: input dialogue label's dialogue reference is invalid."""
        self.dialogue._update(self.valid_message_1_by_self)

        new_label = DialogueLabel(
            (str(2), ""), self.valid_message_1_by_self.to, self.agent_address
        )
        with pytest.raises(AEAEnforceError) as cm:
            self.dialogue._update_dialogue_label(new_label)
        assert str(cm.value) == "Dialogue label cannot be updated."
        assert self.dialogue.dialogue_label != new_label

    def test___str__1(self):
        """Test the '__str__' method: dialogue is self initiated"""
        self.dialogue._update(self.valid_message_1_by_self)
        self.dialogue._update(self.valid_message_2_by_other)

        self.dialogue._update(self.valid_message_3_by_self)

        dialogue_str = "Dialogue Label:\n1__agent 2_agent 1\nMessages:\nmessage_id=1, target=0, performative=bytes\nmessage_id=-1, target=1, performative=bytes\nmessage_id=2, target=-1, performative=bytes\n"

        assert str(self.dialogue) == dialogue_str

    def test___str__2(self):
        """Test the '__str__' method: dialogue is other initiated"""
        valid_message_1_by_other = DefaultMessage(
            dialogue_reference=(str(1), ""),
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        valid_message_1_by_other.sender = self.opponent_address
        valid_message_1_by_other.to = self.agent_address

        self.dialogue_opponent_started._update(valid_message_1_by_other)

        valid_message_2_by_self = DefaultMessage(
            dialogue_reference=(str(1), str(1)),
            message_id=-1,
            target=1,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello back",
        )
        valid_message_2_by_self.sender = self.agent_address
        valid_message_2_by_self.to = self.opponent_address

        self.dialogue_opponent_started._update(valid_message_2_by_self)

        valid_message_3_by_other = DefaultMessage(
            dialogue_reference=(str(1), str(1)),
            message_id=2,
            target=-1,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello back 2",
        )
        valid_message_3_by_other.sender = self.opponent_address
        valid_message_3_by_other.to = self.agent_address

        self.dialogue_opponent_started._update(valid_message_3_by_other)

        dialogue_str = "Dialogue Label:\n1_1_agent 2_agent 2\nMessages:\nmessage_id=1, target=0, performative=bytes\nmessage_id=-1, target=1, performative=bytes\nmessage_id=2, target=-1, performative=bytes\n"

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

    def setup(self):
        """Initialise the environment to test Dialogue."""
        self.agent_address = "agent 1"
        self.opponent_address = "agent 2"
        self.dialogue_label = DialogueLabel(
            dialogue_reference=(str(1), ""),
            dialogue_opponent_addr=self.opponent_address,
            dialogue_starter_addr=self.agent_address,
        )
        self.dialogue = Dialogue(dialogue_label=self.dialogue_label)
        self.own_dialogues = Dialogues(self.agent_address)
        self.opponent_dialogues = Dialogues(self.opponent_address)

        # convenient messages to reuse across tests
        self.valid_message_1_by_self = DefaultMessage(
            dialogue_reference=(str(1), ""),
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        self.valid_message_1_by_self.sender = self.agent_address
        self.valid_message_1_by_self.to = self.opponent_address

        self.valid_message_2_by_other = DefaultMessage(
            dialogue_reference=(str(1), str(1)),
            message_id=2,
            target=1,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello back",
        )
        self.valid_message_2_by_other.sender = self.opponent_address
        self.valid_message_2_by_other.to = self.agent_address

    def test_dialogues_properties(self):
        """Test dialogue properties."""
        assert (
            self.own_dialogues._dialogues_storage._dialogues_by_dialogue_label == dict()
        )
        assert self.own_dialogues.self_address == self.agent_address
        assert self.own_dialogues.dialogue_stats.other_initiated == {
            Dialogue.EndState.SUCCESSFUL: 0,
            Dialogue.EndState.FAILED: 0,
        }
        assert self.own_dialogues.dialogue_stats.self_initiated == {
            Dialogue.EndState.SUCCESSFUL: 0,
            Dialogue.EndState.FAILED: 0,
        }
        assert self.own_dialogues.message_class == DefaultMessage
        assert self.own_dialogues.dialogue_class == Dialogue

    def test_counterparty_from_message(self):
        """Test the 'counterparty_from_message' method."""
        assert (
            self.own_dialogues._counterparty_from_message(self.valid_message_1_by_self)
            == self.opponent_address
        )
        assert (
            self.own_dialogues._counterparty_from_message(self.valid_message_2_by_other)
            == self.opponent_address
        )

    def test_is_message_by_self(self):
        """Test the 'is_message_by_self' method."""
        assert self.own_dialogues._is_message_by_self(self.valid_message_1_by_self)
        assert not self.own_dialogues._is_message_by_self(self.valid_message_2_by_other)

    def test_is_message_by_other(self):
        """Test the 'is_message_by_other' method."""
        assert not self.own_dialogues._is_message_by_other(self.valid_message_1_by_self)
        assert self.own_dialogues._is_message_by_other(self.valid_message_2_by_other)

    def test_new_self_initiated_dialogue_reference(self):
        """Test the 'new_self_initiated_dialogue_reference' method."""
        self_initiated_ref = self.own_dialogues.new_self_initiated_dialogue_reference()
        assert (
            isinstance(self_initiated_ref[0], str)
            and self_initiated_ref[0] != ""
            and len(self_initiated_ref[0]) == DialogueLabel.NONCE_BYTES_NB * 2
        )
        assert self_initiated_ref[1] == ""
        self_initiated_ref_2 = (
            self.own_dialogues.new_self_initiated_dialogue_reference()
        )
        assert self_initiated_ref_2 != self_initiated_ref

    def test_create_positive(self):
        """Positive test for the 'create' method."""
        assert (
            len(self.own_dialogues._dialogues_storage._dialogues_by_dialogue_label) == 0
        )
        self.own_dialogues.create(
            self.opponent_address, DefaultMessage.Performative.BYTES, content=b"Hello"
        )
        assert (
            len(self.own_dialogues._dialogues_storage._dialogues_by_dialogue_label) == 1
        )

    def test_create_negative_incorrect_performative_content_combination(self):
        """Negative test for the 'create' method: invalid performative and content combination (i.e. invalid message)."""
        assert (
            len(self.own_dialogues._dialogues_storage._dialogues_by_dialogue_label) == 0
        )
        with pytest.raises(
            ValueError, match="Invalid initial performative. Expected one of"
        ):
            self.own_dialogues.create(
                self.opponent_address,
                DefaultMessage.Performative.ERROR,
                content=b"Hello",
            )
        assert (
            len(self.own_dialogues._dialogues_storage._dialogues_by_dialogue_label) == 0
        )

    def test_update_positive_new_dialogue_by_other(self):
        """Positive test for the 'update' method: the input message is for a new dialogue dialogue by other."""
        valid_message_1_by_other = DefaultMessage(
            dialogue_reference=(str(1), ""),
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        valid_message_1_by_other.sender = self.opponent_address
        valid_message_1_by_other.to = self.agent_address

        assert (
            len(self.own_dialogues._dialogues_storage._dialogues_by_dialogue_label) == 0
        )

        dialogue = self.own_dialogues.update(valid_message_1_by_other)

        assert (
            len(self.own_dialogues._dialogues_storage._dialogues_by_dialogue_label) == 1
        )
        assert dialogue is not None
        assert dialogue.last_message.dialogue_reference == (str(1), "")
        assert dialogue.last_message.message_id == 1
        assert dialogue.last_message.target == 0
        assert dialogue.last_message.performative == DefaultMessage.Performative.BYTES
        assert dialogue.last_message.content == b"Hello"

    def test_update_positive_existing_dialogue(self):
        """Positive test for the 'update' method: the input message is for an existing dialogue."""
        msg, dialogue = self.own_dialogues.create(
            self.opponent_address, DefaultMessage.Performative.BYTES, content=b"Hello"
        )

        dialogue_reference = (
            msg.dialogue_reference[0],
            self.opponent_dialogues._generate_dialogue_nonce(),
        )
        valid_message_2_by_other = DefaultMessage(
            dialogue_reference=dialogue_reference,
            message_id=dialogue.get_incoming_next_message_id(),
            target=msg.message_id,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello back",
        )
        valid_message_2_by_other.sender = self.opponent_address
        valid_message_2_by_other.to = self.agent_address

        assert (
            len(self.own_dialogues._dialogues_storage._dialogues_by_dialogue_label) == 1
        )

        dialogue = self.own_dialogues.update(valid_message_2_by_other)

        assert (
            len(self.own_dialogues._dialogues_storage._dialogues_by_dialogue_label) == 1
        )
        assert dialogue is not None
        assert dialogue.last_message.dialogue_reference == dialogue_reference
        assert dialogue.last_message.message_id == valid_message_2_by_other.message_id
        assert dialogue.last_message.target == valid_message_2_by_other.target
        assert dialogue.last_message.performative == DefaultMessage.Performative.BYTES
        assert dialogue.last_message.content == b"Hello back"

    def test_update_positive_existing_dialogue_2(self):
        """Positive test for the 'update' method: the input message is for an existing dialogue from the original sender."""
        msg_1, dialogue = self.own_dialogues.create(
            self.opponent_address, DefaultMessage.Performative.BYTES, content=b"Hello"
        )

        opponent_dialogue_1 = self.opponent_dialogues.update(msg_1)

        msg_2 = dialogue.reply(
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello again",
        )

        opponent_dialogue_2 = self.opponent_dialogues.update(msg_2)

        assert opponent_dialogue_1 == opponent_dialogue_2

    def test_update_negative_invalid_label(self):
        """Negative test for the 'update' method: dialogue is not extendable with the input message."""
        invalid_message_1_by_other = DefaultMessage(
            dialogue_reference=("", ""),
            message_id=0,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        invalid_message_1_by_other.sender = self.opponent_address
        invalid_message_1_by_other.to = self.agent_address

        assert not self.own_dialogues.update(invalid_message_1_by_other)

    def test_update_negative_new_dialogue_by_self(self):
        """Negative test for the 'update' method: the message is not by the counterparty."""
        assert (
            len(self.own_dialogues._dialogues_storage._dialogues_by_dialogue_label) == 0
        )

        with pytest.raises(AEAEnforceError) as cm:
            self.own_dialogues.update(self.valid_message_1_by_self)
        assert (
            str(cm.value)
            == "Invalid 'update' usage. Update must only be used with a message by another agent."
        )

        assert (
            len(self.own_dialogues._dialogues_storage._dialogues_by_dialogue_label) == 0
        )

    def test_update_negative_no_to(self):
        """Negative test for the 'update' method: the 'to' field of the input message is not set."""
        invalid_message_1_by_other = DefaultMessage(
            dialogue_reference=(str(1), ""),
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        invalid_message_1_by_other.sender = self.opponent_address

        assert (
            len(self.own_dialogues._dialogues_storage._dialogues_by_dialogue_label) == 0
        )

        with pytest.raises(AEAEnforceError) as cm:
            self.own_dialogues.update(invalid_message_1_by_other)
        assert str(cm.value) == "The message's 'to' field is not set {}".format(
            invalid_message_1_by_other
        )

        assert (
            len(self.own_dialogues._dialogues_storage._dialogues_by_dialogue_label) == 0
        )

    def test_update_negative_no_sender(self):
        """Negative test for the 'update' method: the 'sender' field of the input message is not set."""
        invalid_message_1_by_other = DefaultMessage(
            dialogue_reference=(str(1), ""),
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        invalid_message_1_by_other.to = self.agent_address

        assert (
            len(self.own_dialogues._dialogues_storage._dialogues_by_dialogue_label) == 0
        )

        with pytest.raises(AEAEnforceError) as cm:
            self.own_dialogues.update(invalid_message_1_by_other)
        assert (
            str(cm.value)
            == "Invalid 'update' usage. Update must only be used with a message by another agent."
        )

        assert (
            len(self.own_dialogues._dialogues_storage._dialogues_by_dialogue_label) == 0
        )

    def test_update_negative_no_matching_to(self):
        """Negative test for the 'update' method: the 'to' field of the input message does not match self address."""
        invalid_message_1_by_other = DefaultMessage(
            dialogue_reference=(str(1), ""),
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        invalid_message_1_by_other.to = self.agent_address + "wrong_stuff"
        invalid_message_1_by_other.sender = self.opponent_address

        assert (
            len(self.own_dialogues._dialogues_storage._dialogues_by_dialogue_label) == 0
        )

        with pytest.raises(AEAEnforceError) as cm:
            self.own_dialogues.update(invalid_message_1_by_other)
        assert (
            str(cm.value)
            == "Message to and dialogue self address do not match. Got 'to=agent 1wrong_stuff' expected 'to=agent 1'."
        )

        assert (
            len(self.own_dialogues._dialogues_storage._dialogues_by_dialogue_label) == 0
        )

    def test_update_negative_invalid_message(self):
        """Negative test for the 'update' method: the message is invalid."""
        invalid_message_1_by_other = DefaultMessage(
            dialogue_reference=(str(1), ""),
            performative=DefaultMessage.Performative.ERROR,
            error_code=DefaultMessage.ErrorCode.INVALID_MESSAGE,
            error_msg="some_error_message",
            error_data={"some_data": b"some_bytes"},
        )
        invalid_message_1_by_other.sender = self.opponent_address
        invalid_message_1_by_other.to = self.agent_address

        assert (
            len(self.own_dialogues._dialogues_storage._dialogues_by_dialogue_label) == 0
        )

        dialogue = self.own_dialogues.update(invalid_message_1_by_other)

        assert dialogue is None

        assert (
            len(self.own_dialogues._dialogues_storage._dialogues_by_dialogue_label) == 0
        )

    def test_update_negative_existing_dialogue_non_nonexistent(self):
        """Negative test for the 'update' method: the dialogue referred by the input message does not exist."""
        _, dialogue = self.own_dialogues.create(
            self.opponent_address, DefaultMessage.Performative.BYTES, content=b"Hello"
        )

        invalid_message_2_by_other = DefaultMessage(
            dialogue_reference=(str(2), str(1)),
            message_id=2,
            target=1,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello back",
        )
        invalid_message_2_by_other.sender = self.opponent_address
        invalid_message_2_by_other.to = self.agent_address

        updated_dialogue = self.own_dialogues.update(invalid_message_2_by_other)

        assert updated_dialogue is None
        last_message = self.own_dialogues._dialogues_storage.get(
            dialogue.dialogue_label
        ).last_message
        assert (
            last_message.dialogue_reference[0] != ""
            and last_message.dialogue_reference[1] == ""
        )
        assert (
            self.own_dialogues._dialogues_storage.get(
                dialogue.dialogue_label
            ).last_message.message_id
            == 1
        )
        assert (
            self.own_dialogues._dialogues_storage.get(
                dialogue.dialogue_label
            ).last_message.target
            == 0
        )
        assert (
            self.own_dialogues._dialogues_storage.get(
                dialogue.dialogue_label
            ).last_message.performative
            == DefaultMessage.Performative.BYTES
        )
        assert (
            self.own_dialogues._dialogues_storage.get(
                dialogue.dialogue_label
            ).last_message.content
            == b"Hello"
        )

    def test_complete_dialogue_reference_positive(
        self,
    ):
        """Positive test for the '_complete_dialogue_reference' method."""
        msg, dialogue = self.own_dialogues.create(
            self.opponent_address, DefaultMessage.Performative.BYTES, content=b"Hello"
        )

        valid_message_2_by_other = DefaultMessage(
            dialogue_reference=(
                msg.dialogue_reference[0],
                self.opponent_dialogues._generate_dialogue_nonce(),
            ),
            message_id=2,
            target=1,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello back",
        )
        valid_message_2_by_other.sender = self.opponent_address
        valid_message_2_by_other.to = self.agent_address

        self.own_dialogues._complete_dialogue_reference(valid_message_2_by_other)

        assert (
            self.own_dialogues._dialogues_storage.get(
                dialogue.dialogue_label
            ).dialogue_label.dialogue_reference
            == valid_message_2_by_other.dialogue_reference
        )

    def test_complete_dialogue_reference_negative_incorrect_reference(
        self,
    ):
        """Negative test for the '_complete_dialogue_reference' method: the input message has invalid dialogue reference."""
        msg, dialogue = self.own_dialogues.create(
            self.opponent_address, DefaultMessage.Performative.BYTES, content=b"Hello"
        )

        wrong_own_ref = (
            "wrong reference"  # if correct, would be  msg.dialogue_reference[0]
        )
        valid_message_2_by_other = DefaultMessage(
            dialogue_reference=(
                wrong_own_ref,
                self.opponent_dialogues._generate_dialogue_nonce(),
            ),
            message_id=msg.message_id + 1,
            target=msg.message_id,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello back",
        )
        valid_message_2_by_other.sender = self.opponent_address
        valid_message_2_by_other.to = self.agent_address

        self.own_dialogues._complete_dialogue_reference(valid_message_2_by_other)
        assert (
            self.own_dialogues._dialogues_storage.get(
                dialogue.dialogue_label
            ).dialogue_label.dialogue_reference
            == msg.dialogue_reference
        )

    def test_get_dialogue_positive_1(self):
        """Positive test for the 'get_dialogue' method: the dialogue is self initiated and the second message is by the other agent."""
        msg, dialogue = self.own_dialogues.create(
            self.opponent_address, DefaultMessage.Performative.BYTES, content=b"Hello"
        )

        valid_message_2_by_other = DefaultMessage(
            dialogue_reference=(
                msg.dialogue_reference[0],
                self.opponent_dialogues._generate_dialogue_nonce(),
            ),
            message_id=msg.message_id + 1,
            target=msg.message_id,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello back",
        )
        valid_message_2_by_other.sender = self.opponent_address
        valid_message_2_by_other.to = self.agent_address

        self.own_dialogues._complete_dialogue_reference(valid_message_2_by_other)

        assert (
            self.own_dialogues._dialogues_storage.get(
                dialogue.dialogue_label
            ).dialogue_label.dialogue_reference
            == valid_message_2_by_other.dialogue_reference
        )

        retrieved_dialogue = self.own_dialogues.get_dialogue(valid_message_2_by_other)

        assert retrieved_dialogue.dialogue_label == dialogue.dialogue_label

    def test_get_dialogue_positive_2(self):
        """Positive test for the 'get_dialogue' method: the dialogue is other initiated and the second message is by this agent."""
        valid_message_1_by_other = DefaultMessage(
            dialogue_reference=(str(1), ""),
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        valid_message_1_by_other.sender = self.opponent_address
        valid_message_1_by_other.to = self.agent_address

        dialogue = self.own_dialogues.update(valid_message_1_by_other)

        valid_message_2_by_other = DefaultMessage(
            dialogue_reference=dialogue.dialogue_label.dialogue_reference,
            message_id=valid_message_1_by_other.message_id + 1,
            target=valid_message_1_by_other.message_id,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello back",
        )
        valid_message_2_by_other.sender = self.agent_address
        valid_message_2_by_other.to = self.opponent_address

        retrieved_dialogue = self.own_dialogues.get_dialogue(valid_message_2_by_other)

        assert retrieved_dialogue is not None
        assert retrieved_dialogue.dialogue_label == dialogue.dialogue_label

    @patch.object(BaseDialogue, "_validate_message_id", return_value=None)
    def test_get_dialogue_negative_invalid_reference(self, *mocks):
        """Negative test for the 'get_dialogue' method: the input message has invalid dialogue reference."""
        msg, dialogue = self.own_dialogues.create(
            self.opponent_address, DefaultMessage.Performative.BYTES, content=b"Hello"
        )

        valid_message_2_by_other = DefaultMessage(
            dialogue_reference=(
                msg.dialogue_reference[0],
                self.opponent_dialogues._generate_dialogue_nonce(),
            ),
            message_id=msg.message_id + 1,
            target=msg.message_id,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello back",
        )
        valid_message_2_by_other.sender = self.opponent_address
        valid_message_2_by_other.to = self.agent_address

        dialogue = self.own_dialogues.update(valid_message_2_by_other)
        assert dialogue is not None

        invalid_message_3_by_self = DefaultMessage(
            dialogue_reference=(str(2), str(1)),
            message_id=2,
            target=1,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello back",
        )
        invalid_message_3_by_self.sender = self.agent_address
        invalid_message_3_by_self.to = self.opponent_address

        retrieved_dialogue = self.own_dialogues.get_dialogue(invalid_message_3_by_self)

        assert retrieved_dialogue is None

    def test_get_latest_label(self):
        """Positive test for the 'get_latest_label' method."""
        pass

    def test_get_dialogue_from_label_positive(self):
        """Positive test for the 'get_dialogue_from_label' method."""
        _, dialogue = self.own_dialogues.create(
            self.opponent_address, DefaultMessage.Performative.BYTES, content=b"Hello"
        )

        retrieved_dialogue = self.own_dialogues.get_dialogue_from_label(
            dialogue.dialogue_label
        )
        assert retrieved_dialogue.dialogue_label == dialogue.dialogue_label

    def test_get_dialogue_from_label_negative_incorrect_input_label(self):
        """Negative test for the 'get_dialogue_from_label' method: the input dialogue label does not exist."""
        _, dialogue = self.own_dialogues.create(
            self.opponent_address, DefaultMessage.Performative.BYTES, content=b"Hello"
        )

        incorrect_label = DialogueLabel(
            (str(1), "error"), self.opponent_address, self.agent_address
        )

        retrieved_dialogue = self.own_dialogues.get_dialogue_from_label(incorrect_label)
        assert retrieved_dialogue is None

    def test_create_self_initiated_positive(self):
        """Positive test for the '_create_self_initiated' method."""
        assert (
            len(self.own_dialogues._dialogues_storage._dialogues_by_dialogue_label) == 0
        )

        self.own_dialogues._create_self_initiated(
            self.opponent_address, (str(1), ""), Dialogue.Role.ROLE1
        )
        assert (
            len(self.own_dialogues._dialogues_storage._dialogues_by_dialogue_label) == 1
        )

    def test_create_self_initiated_negative_invalid_dialogue_reference(self):
        """Negative test for the '_create_self_initiated' method: invalid dialogue reference"""
        pass

    def test_create_opponent_initiated_positive(self):
        """Positive test for the '_create_opponent_initiated' method."""
        assert (
            len(self.own_dialogues._dialogues_storage._dialogues_by_dialogue_label) == 0
        )

        self.own_dialogues._create_opponent_initiated(
            self.opponent_address, (str(1), ""), Dialogue.Role.ROLE2
        )
        assert (
            len(self.own_dialogues._dialogues_storage._dialogues_by_dialogue_label) == 1
        )

    def test_create_opponent_initiated_negative_invalid_input_dialogue_reference(self):
        """Negative test for the '_create_opponent_initiated' method: input dialogue label has invalid dialogue reference."""
        assert (
            len(self.own_dialogues._dialogues_storage._dialogues_by_dialogue_label) == 0
        )

        try:
            self.own_dialogues._create_opponent_initiated(
                self.opponent_address, ("", str(1)), Dialogue.Role.ROLE2
            )
            result = True
        except AEAEnforceError:
            result = False

        assert not result
        assert (
            len(self.own_dialogues._dialogues_storage._dialogues_by_dialogue_label) == 0
        )

    def test_create_with_message(self):
        """Positive test for create with message."""
        msg = DefaultMessage(
            dialogue_reference=self.own_dialogues.new_self_initiated_dialogue_reference(),
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        self.own_dialogues.create_with_message("opponent", msg)

    def test__create_positive(self):
        """Positive test for the '_create' method."""
        pass

    def test__create_negative_incomplete_dialogue_label_present(self):
        """Negative test for the '_create' method: incomplete dialogue label already present."""
        pass

    def test__create_negative_dialogue_label_present(self):
        """Negative test for the '_create' method: dialogue label already present."""
        pass

    def test_generate_dialogue_nonce(self):
        """Test the '_generate_dialogue_nonce' method."""
        nonce = self.own_dialogues._generate_dialogue_nonce()
        assert (
            isinstance(nonce, str)
            and nonce != ""
            and len(nonce) == DialogueLabel.NONCE_BYTES_NB * 2
        )
        second_nonce = self.own_dialogues._generate_dialogue_nonce()
        assert nonce != second_nonce

    def test_get_dialogues_with_counterparty(self):
        """Test get dialogues with counterparty."""
        assert (
            self.own_dialogues.get_dialogues_with_counterparty(self.opponent_address)
            == []
        )
        _, dialogue = self.own_dialogues.create(
            self.opponent_address, DefaultMessage.Performative.BYTES, content=b"Hello"
        )
        assert self.own_dialogues.get_dialogues_with_counterparty(
            self.opponent_address
        ) == [dialogue]

    def test_setup(self):
        """Test dialogues.setup()."""
        self.own_dialogues.setup()

    def test_teardown(self):
        """Test dialogues.teardown()."""
        self.own_dialogues.teardown()


class TestPersistDialoguesStorage:
    """Test PersistDialoguesStorage."""

    def setup(self):
        """Initialise the environment to test PersistDialogueStorage."""
        self.agent_address = "agent 1"
        self.opponent_address = "agent 2"
        self.dialogues = Dialogues(
            self.agent_address, keep_terminal_state_dialogues=True
        )
        self.dialogues._dialogues_storage = PersistDialoguesStorage(self.dialogues)
        self.skill_component = Mock()
        self.skill_component.name = "test_component"
        self.skill_component.skill_id = PublicId("test", "test", "0.1.0")

        self.dialogue_label = DialogueLabel(
            dialogue_reference=(str(1), ""),
            dialogue_opponent_addr=self.opponent_address,
            dialogue_starter_addr=self.agent_address,
        )
        self.generic_storage = Storage("sqlite://:memory:", threaded=True)
        self.generic_storage.start()
        wait_for_condition(lambda: self.generic_storage.is_connected, timeout=10)
        self.skill_component.context.storage = self.generic_storage

    def teardown(self):
        """Tear down the environment to test PersistDialogueStorage."""
        self.generic_storage.stop()
        self.generic_storage.wait_completed(sync=True, timeout=10)

    def test_dialogue_serialize_deserialize(self):
        """Test dialogue dumped and restored."""
        msg = DefaultMessage(
            dialogue_reference=self.dialogues.new_self_initiated_dialogue_reference(),
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        dialogue = self.dialogues.create_with_message("opponent", msg)
        data = dialogue.json()
        dialogue_restored = dialogue.__class__.from_json(dialogue.message_class, data)
        assert dialogue == dialogue_restored

    def test_dump_restore(self):
        """Test dump and load methods of the persists storage."""
        dialogues_storage = PersistDialoguesStorage(self.dialogues)
        dialogues_storage._skill_component = self.skill_component
        self.dialogues._dialogues_storage = dialogues_storage
        dialogues_storage._incomplete_to_complete_dialogue_labels[
            self.dialogue_label
        ] = self.dialogue_label
        self.dialogues.create(
            self.opponent_address, DefaultMessage.Performative.BYTES, content=b"Hello"
        )
        msg, dialogue = self.dialogues.create(
            self.opponent_address, DefaultMessage.Performative.BYTES, content=b"Hello2"
        )
        dialogue.reply(
            target_message=msg,
            performative=DefaultMessage.Performative.ERROR,
            error_code=ErrorCode.UNSUPPORTED_PROTOCOL,
            error_msg="oops",
            error_data={},
        )
        assert dialogues_storage.dialogues_in_terminal_state
        assert dialogues_storage.dialogues_in_active_state
        assert dialogues_storage._dialogue_by_address
        assert dialogues_storage._incomplete_to_complete_dialogue_labels
        dialogues_storage.teardown()

        dialogues_storage_restored = PersistDialoguesStorage(self.dialogues)
        dialogues_storage_restored._skill_component = self.skill_component
        dialogues_storage_restored.setup()

        assert len(dialogues_storage._dialogue_by_address) == len(
            dialogues_storage_restored._dialogue_by_address
        )

        assert len(dialogues_storage._dialogue_by_address) == len(
            dialogues_storage_restored._dialogue_by_address
        )

        assert (
            dialogues_storage._incomplete_to_complete_dialogue_labels
            == dialogues_storage_restored._incomplete_to_complete_dialogue_labels
        )
        assert set(
            [str(i.dialogue_label) for i in dialogues_storage.dialogues_in_active_state]
        ) == set(
            [
                str(i.dialogue_label)
                for i in dialogues_storage_restored.dialogues_in_active_state
            ]
        )
        assert set(
            [
                str(i.dialogue_label)
                for i in dialogues_storage.dialogues_in_terminal_state
            ]
        ) == set(
            [
                str(i.dialogue_label)
                for i in dialogues_storage_restored.dialogues_in_terminal_state
            ]
        )

        # test remove from storage on storeage.remove
        assert dialogues_storage_restored._terminal_dialogues_collection
        dialogue_label = dialogues_storage.dialogues_in_terminal_state[0].dialogue_label
        assert dialogues_storage_restored._terminal_dialogues_collection.get(
            str(dialogue_label)
        )
        dialogues_storage_restored.remove(dialogue_label)
        assert (
            dialogues_storage_restored._terminal_dialogues_collection.get(
                str(dialogue_label)
            )
            is None
        )

    def test_cleanup(self):
        """Test storage cleanup."""
        dialogues_storage = PersistDialoguesStorage(self.dialogues)
        dialogues_storage._skill_component = self.skill_component
        self.dialogues._dialogues_storage = dialogues_storage
        dialogues_storage._incomplete_to_complete_dialogue_labels[
            self.dialogue_label
        ] = self.dialogue_label
        self.dialogues.create(
            self.opponent_address, DefaultMessage.Performative.BYTES, content=b"Hello"
        )
        msg, dialogue = self.dialogues.create(
            self.opponent_address, DefaultMessage.Performative.BYTES, content=b"Hello2"
        )
        dialogue.reply(
            target_message=msg,
            performative=DefaultMessage.Performative.ERROR,
            error_code=ErrorCode.UNSUPPORTED_PROTOCOL,
            error_msg="oops",
            error_data={},
        )
        assert dialogues_storage._dialogues_by_dialogue_label
        assert dialogues_storage._dialogue_by_address
        assert dialogues_storage._incomplete_to_complete_dialogue_labels
        assert dialogues_storage._terminal_state_dialogues_labels

        self.dialogues._dialogues_storage.cleanup()

        assert not dialogues_storage._dialogues_by_dialogue_label
        assert not dialogues_storage._dialogue_by_address
        assert not dialogues_storage._incomplete_to_complete_dialogue_labels
        assert not dialogues_storage._terminal_state_dialogues_labels


class TestPersistDialoguesStorageOffloading:
    """Test PersistDialoguesStorage."""

    def setup(self):
        """Initialise the environment to test PersistDialogueStorage."""
        self.agent_address = "agent 1"
        self.opponent_address = "agent 2"
        self.dialogues = Dialogues(
            self.agent_address, keep_terminal_state_dialogues=True
        )
        self.skill_component = Mock()
        self.skill_component.name = "test_component"
        self.skill_component.skill_id = PublicId("test", "test", "0.1.0")

        self.dialogue_label = DialogueLabel(
            dialogue_reference=(str(1), ""),
            dialogue_opponent_addr=self.opponent_address,
            dialogue_starter_addr=self.agent_address,
        )
        self.generic_storage = Storage("sqlite://:memory:", threaded=True)
        self.generic_storage.start()
        wait_for_condition(lambda: self.generic_storage.is_connected, timeout=10)
        self.skill_component.context.storage = self.generic_storage

    def teardown(self):
        """Tear down the environment to test PersistDialogueStorage."""
        self.generic_storage.stop()
        self.generic_storage.wait_completed(sync=True, timeout=10)

    def test_dump_restore(self):
        """Test dump and load methods of the persists storage."""
        dialogues_storage = PersistDialoguesStorageWithOffloading(self.dialogues)
        dialogues_storage._skill_component = self.skill_component
        self.dialogues._dialogues_storage = dialogues_storage
        dialogues_storage._incomplete_to_complete_dialogue_labels[
            self.dialogue_label
        ] = self.dialogue_label
        self.dialogues.create(
            self.opponent_address, DefaultMessage.Performative.BYTES, content=b"Hello"
        )
        msg, dialogue = self.dialogues.create(
            self.opponent_address, DefaultMessage.Performative.BYTES, content=b"Hello2"
        )
        dialogue.reply(
            target_message=msg,
            performative=DefaultMessage.Performative.ERROR,
            error_code=ErrorCode.UNSUPPORTED_PROTOCOL,
            error_msg="oops",
            error_data={},
        )
        assert dialogues_storage.dialogues_in_terminal_state
        assert dialogues_storage.dialogues_in_active_state
        assert dialogues_storage._dialogue_by_address
        assert dialogues_storage._incomplete_to_complete_dialogue_labels
        dialogues_by_addr = dialogues_storage.get_dialogues_with_counterparty(
            dialogue.dialogue_label.dialogue_opponent_addr
        )
        dialogues_storage.teardown()

        dialogues_storage_restored = PersistDialoguesStorageWithOffloading(
            self.dialogues
        )
        dialogues_storage_restored._skill_component = self.skill_component
        dialogues_storage_restored.setup()

        assert len(dialogues_storage._dialogue_by_address) == len(
            dialogues_storage_restored._dialogue_by_address
        )

        assert (
            dialogues_storage._incomplete_to_complete_dialogue_labels
            == dialogues_storage_restored._incomplete_to_complete_dialogue_labels
        )
        assert set(
            [str(i.dialogue_label) for i in dialogues_storage.dialogues_in_active_state]
        ) == set(
            [
                str(i.dialogue_label)
                for i in dialogues_storage_restored.dialogues_in_active_state
            ]
        )
        assert set(
            [
                str(i.dialogue_label)
                for i in dialogues_storage.dialogues_in_terminal_state
            ]
        ) == set(
            [
                str(i.dialogue_label)
                for i in dialogues_storage_restored.dialogues_in_terminal_state
            ]
        )

        dialogue_label = dialogues_storage.dialogues_in_terminal_state[0].dialogue_label

        assert len(dialogues_by_addr) == len(
            dialogues_storage_restored.get_dialogues_with_counterparty(
                dialogue.dialogue_label.dialogue_opponent_addr
            )
        )
        # check get and cache
        assert not dialogues_storage_restored._terminal_state_dialogues_labels
        assert dialogues_storage_restored.get(dialogue_label) is not None
        assert dialogues_storage_restored._terminal_state_dialogues_labels

        # test remove from storage on storeage.remove
        assert dialogues_storage_restored._terminal_dialogues_collection
        assert (
            dialogues_storage_restored._terminal_dialogues_collection.get(
                str(dialogue_label)
            )
            is not None
        )
        dialogues_storage_restored.remove(dialogue_label)
        assert (
            dialogues_storage_restored._terminal_dialogues_collection.get(
                str(dialogue_label)
            )
            is None
        )
        assert dialogues_storage_restored.get(dialogue_label) is None


class TestBaseDialoguesStorage:
    """Test PersistDialoguesStorage."""

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

        # convenient messages to reuse across tests
        cls.valid_message_1_by_self = DefaultMessage(
            dialogue_reference=(str(1), ""),
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        cls.valid_message_1_by_self.sender = cls.agent_address
        cls.valid_message_1_by_self.to = cls.opponent_address

        cls.storage = BasicDialoguesStorage(Mock())

    def test_dialogues_in_terminal_state_kept(self):
        """Test dialogues in terminal state handled properly."""
        assert not self.storage._incomplete_to_complete_dialogue_labels
        self.storage.add(self.dialogue)
        assert self.storage.dialogues_in_active_state
        assert not self.storage.dialogues_in_terminal_state
        assert len(self.storage._incomplete_to_complete_dialogue_labels) == 1

        self.dialogue._update(self.valid_message_1_by_self)
        self.dialogue.reply(
            target_message=self.valid_message_1_by_self,
            performative=DefaultMessage.Performative.ERROR,
            error_code=ErrorCode.UNSUPPORTED_PROTOCOL,
            error_msg="oops",
            error_data={},
        )

        assert not self.storage.dialogues_in_active_state
        assert self.storage.dialogues_in_terminal_state

        self.storage.remove(self.dialogue.dialogue_label)
        assert not self.storage.dialogues_in_active_state
        assert not self.storage.dialogues_in_terminal_state
        assert (
            self.dialogue.dialogue_label.get_incomplete_version()
            not in self.storage._incomplete_to_complete_dialogue_labels
        )
        assert (
            self.dialogue.dialogue_label
            not in self.storage._terminal_state_dialogues_labels
        )
        assert (
            self.dialogue.dialogue_label.get_incomplete_version()
            not in self.storage._terminal_state_dialogues_labels
        )
        assert (
            self.dialogue.dialogue_label
            not in self.storage._dialogues_by_dialogue_label
        )
        assert (
            self.dialogue.dialogue_label.get_incomplete_version()
            not in self.storage._dialogues_by_dialogue_label
        )
        assert (
            len(
                self.storage._dialogue_by_address[
                    self.dialogue.dialogue_label.dialogue_opponent_addr
                ]
            )
            == 0
        )

    def test_dialogues_in_terminal_state_removed(self):
        """Test dialogues in terminal state handled properly."""
        self.storage._dialogues.is_keep_dialogues_in_terminal_state = False
        self.storage.add(self.dialogue)
        assert self.storage.dialogues_in_active_state
        assert not self.storage.dialogues_in_terminal_state

        self.dialogue._update(self.valid_message_1_by_self)
        self.dialogue.reply(
            target_message=self.valid_message_1_by_self,
            performative=DefaultMessage.Performative.ERROR,
            error_code=ErrorCode.UNSUPPORTED_PROTOCOL,
            error_msg="oops",
            error_data={},
        )

        assert not self.storage.dialogues_in_active_state
        assert not self.storage.dialogues_in_terminal_state
        assert (
            self.dialogue.dialogue_label.get_incomplete_version()
            not in self.storage._incomplete_to_complete_dialogue_labels
        )
        assert (
            self.dialogue.dialogue_label
            not in self.storage._terminal_state_dialogues_labels
        )
        assert (
            self.dialogue.dialogue_label.get_incomplete_version()
            not in self.storage._terminal_state_dialogues_labels
        )
        assert (
            self.dialogue.dialogue_label
            not in self.storage._dialogues_by_dialogue_label
        )
        assert (
            self.dialogue.dialogue_label.get_incomplete_version()
            not in self.storage._dialogues_by_dialogue_label
        )
        assert (
            len(
                self.storage._dialogue_by_address[
                    self.dialogue.dialogue_label.dialogue_opponent_addr
                ]
            )
            == 0
        )

    def teardown(self):
        """Tear down the environment to test BaseDialogueStorage."""


def test_find_caller_object():
    """Test find_caller_object."""

    class CustomSkillComponent(SkillComponent):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.storage = PersistDialoguesStorage(self)

        def setup(self):
            pass

        def teardown(self):
            pass

        @classmethod
        def parse_module(cls, *args, **kwargs):
            pass

    skill_component = CustomSkillComponent(Mock(), Mock(), Mock())
    assert skill_component.storage._skill_component == skill_component

    class CustomObject:
        def __init__(self, *args, **kwargs):
            self.component = find_caller_object(SkillComponent)

    custom_object = CustomObject()
    assert custom_object.component is None


def test_dialogues_keep_terminal_state_dialogues():
    """Test Dialogues keep_terminal_state_dialogues option."""
    initial = Dialogues._keep_terminal_state_dialogues
    dialogues = Dialogues(Mock(), keep_terminal_state_dialogues=True)
    assert dialogues.is_keep_dialogues_in_terminal_state is True
    assert Dialogues._keep_terminal_state_dialogues == initial

    dialogues = Dialogues(Mock(), keep_terminal_state_dialogues=False)
    assert dialogues.is_keep_dialogues_in_terminal_state is False
    assert Dialogues._keep_terminal_state_dialogues == initial
