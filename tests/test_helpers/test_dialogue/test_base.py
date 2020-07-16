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

"""This module contains the tests for the helper module."""

from typing import Dict, FrozenSet, Optional, cast

from aea.helpers.dialogue.base import Dialogue as BaseDialogue
from aea.helpers.dialogue.base import DialogueLabel
from aea.helpers.dialogue.base import Dialogues as BaseDialogues
from aea.mail.base import Address
from aea.protocols.base import Message
from aea.protocols.default.message import DefaultMessage


class Dialogue(BaseDialogue):

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
        """This class defines the agent's role in a fipa dialogue."""

        ROLE1 = "role1"
        ROLE2 = "role2"

    def __init__(
        self,
        dialogue_label: DialogueLabel,
        message_class=DefaultMessage,
        agent_address: Optional[Address] = "agent 1",
        role: Optional[BaseDialogue.Role] = Role.ROLE1,
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

    END_STATES = frozenset({})  # type: FrozenSet[BaseDialogue.EndState]

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
        BaseDialogues.__init__(
            self,
            agent_address=agent_address,
            end_states=cast(FrozenSet[BaseDialogue.EndState], self.END_STATES),
            message_class=message_class,
            dialogue_class=dialogue_class,
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

    @staticmethod
    def role_from_first_message(message: Message) -> BaseDialogue.Role:
        """
        Infer the role of the agent from an incoming or outgoing first message

        :param message: an incoming/outgoing first message
        :return: the agent's role
        """
        pass


class TestDialogueLabel:
    """Test the dialogue/base.py."""

    @classmethod
    def setup(cls):
        """Initialise the class."""
        cls.dialogue_label = DialogueLabel(
            dialogue_reference=(str(0), ""),
            dialogue_opponent_addr="agent 2",
            dialogue_starter_addr="agent 1",
        )

    def test_dialogue_label(self):
        """Test the dialogue_label."""
        assert self.dialogue_label.dialogue_reference == (str(0), "")
        assert self.dialogue_label.dialogue_starter_reference == str(0)
        assert self.dialogue_label.dialogue_responder_reference == ""
        assert self.dialogue_label.dialogue_opponent_addr == "agent 2"
        assert self.dialogue_label.dialogue_starter_addr == "agent 1"
        assert str(self.dialogue_label) == "{}_{}_{}_{}".format(
            self.dialogue_label.dialogue_starter_reference,
            self.dialogue_label.dialogue_responder_reference,
            self.dialogue_label.dialogue_opponent_addr,
            self.dialogue_label.dialogue_starter_addr,
        )

        dialogue_label_eq = DialogueLabel(
            dialogue_reference=(str(0), ""),
            dialogue_opponent_addr="agent 2",
            dialogue_starter_addr="agent 1",
        )

        assert dialogue_label_eq == self.dialogue_label

        dialogue_label_not_eq = "This is a test"

        assert not dialogue_label_not_eq == self.dialogue_label

        assert hash(dialogue_label_eq) == hash(self.dialogue_label)

        assert self.dialogue_label.json == dict(
            dialogue_starter_reference=str(0),
            dialogue_responder_reference="",
            dialogue_opponent_addr="agent 2",
            dialogue_starter_addr="agent 1",
        )
        assert DialogueLabel.from_json(self.dialogue_label.json) == self.dialogue_label


class TestDialogueBase:
    """Test the dialogue/base.py."""

    @classmethod
    def setup(cls):
        """Initialise the class."""
        cls.dialogue_label = DialogueLabel(
            dialogue_reference=(str(0), ""),
            dialogue_opponent_addr="agent 2",
            dialogue_starter_addr="agent 1",
        )
        cls.dialogue = Dialogue(dialogue_label=cls.dialogue_label)

    def test_dialogue_properties(self):
        """Test the dialogue."""
        assert self.dialogue.dialogue_label == self.dialogue_label
        assert self.dialogue.agent_address == "agent 1"

        self.dialogue.agent_address = "this agent's address"
        assert self.dialogue.agent_address == "this agent's address"

        assert self.dialogue.role == Dialogue.Role.ROLE1

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
        """Test the dialogue."""
        valid_initial_msg = DefaultMessage(
            dialogue_reference=(str(0), ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        valid_initial_msg.counterparty = "agent 2"

        assert self.dialogue.update(valid_initial_msg)
        assert self.dialogue.last_outgoing_message == valid_initial_msg

    def test_update_negative_not_is_extendible(self):
        """Test the dialogue."""
        invalid_message_id = DefaultMessage(
            dialogue_reference=(str(0), ""),
            message_id=0,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        invalid_message_id.counterparty = "agent 2"

        assert not self.dialogue.update(invalid_message_id)
        assert self.dialogue.last_outgoing_message is None

    def test_update_self_initiated_dialogue_label_on_second_message_positive(self):
        valid_initial_msg = DefaultMessage(
            dialogue_reference=(str(0), ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        valid_initial_msg.counterparty = "agent 2"
        valid_initial_msg._is_incoming = False

        assert self.dialogue.update(valid_initial_msg)

        valid_second_msg = DefaultMessage(
            dialogue_reference=(str(0), str(1)),
            message_id=2,
            target=1,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello Back",
        )
        valid_second_msg.counterparty = "agent 2"
        valid_second_msg._is_incoming = True

        try:
            self.dialogue._update_self_initiated_dialogue_label_on_second_message(
                valid_second_msg
            )
            result = True
        except Exception:
            result = False

        assert result

    def test_update_self_initiated_dialogue_label_on_second_message_negative_empty_dialogue(
        self,
    ):
        initial_msg = DefaultMessage(
            dialogue_reference=(str(0), ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        initial_msg.counterparty = "agent 2"
        initial_msg._is_incoming = False

        try:
            self.dialogue._update_self_initiated_dialogue_label_on_second_message(
                initial_msg
            )
            result = True
        except Exception:
            result = False

        assert not result

    def test_update_self_initiated_dialogue_label_on_second_message_negative_not_second_message(
        self,
    ):
        initial_msg = DefaultMessage(
            dialogue_reference=(str(0), ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        initial_msg.counterparty = "agent 2"
        initial_msg._is_incoming = False

        assert self.dialogue.update(initial_msg)

        second_msg = DefaultMessage(
            dialogue_reference=(str(0), str(1)),
            message_id=2,
            target=1,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello back",
        )
        second_msg.counterparty = "agent 2"
        second_msg._is_incoming = True

        assert self.dialogue.update(second_msg)

        third_msg = DefaultMessage(
            dialogue_reference=(str(0), str(1)),
            message_id=3,
            target=2,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello back 2",
        )
        third_msg.counterparty = "agent 2"
        third_msg._is_incoming = False

        try:
            self.dialogue._update_self_initiated_dialogue_label_on_second_message(
                third_msg
            )
            result = True
        except Exception:
            result = False

        assert not result

    def test_reply_positive(self):
        """Test the dialogue."""
        initial_msg = DefaultMessage(
            dialogue_reference=(str(0), ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        initial_msg.counterparty = "agent 2"
        initial_msg._is_incoming = False

        assert self.dialogue.update(initial_msg)

        self.dialogue.reply(
            target_message=initial_msg,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello Back",
        )

        assert self.dialogue.last_message.message_id == 2

    def test_reply_negative_invalid_target(self):
        """Test the dialogue."""
        initial_msg = DefaultMessage(
            dialogue_reference=(str(0), ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        initial_msg.counterparty = "agent 2"
        initial_msg._is_incoming = False

        assert self.dialogue.update(initial_msg)

        invalid_initial_msg = DefaultMessage(
            dialogue_reference=(str(0), ""),
            message_id=2,
            target=1,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello There",
        )
        invalid_initial_msg.counterparty = "agent 2"
        invalid_initial_msg._is_incoming = False

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
        """Test the dialogue."""
        valid_initial_msg = DefaultMessage(
            dialogue_reference=(str(0), ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        valid_initial_msg.counterparty = "agent 2"

        assert self.dialogue._basic_rules(valid_initial_msg)

    def test_basic_rules_negative_initial_message_invalid_dialogue_reference(self):
        """Test the dialogue."""
        invalid_initial_msg = DefaultMessage(
            dialogue_reference=(str(1), ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        invalid_initial_msg.counterparty = "agent 2"

        assert not self.dialogue._basic_rules(invalid_initial_msg)

    def test_basic_rules_negative_initial_message_invalid_message_id(self):
        """Test the dialogue."""
        invalid_initial_msg = DefaultMessage(
            dialogue_reference=(str(0), ""),
            message_id=2,
            target=1,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        invalid_initial_msg.counterparty = "agent 2"

        assert not self.dialogue._basic_rules(invalid_initial_msg)

    def test_basic_rules_negative_initial_message_invalid_target(self):
        """Test the dialogue."""
        invalid_initial_msg = DefaultMessage(
            dialogue_reference=(str(0), ""),
            message_id=1,
            target=1,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        invalid_initial_msg.counterparty = "agent 2"

        assert not self.dialogue._basic_rules(invalid_initial_msg)

    def test_basic_rules_negative_initial_message_invalid_performative(self):
        """Test the dialogue."""
        invalid_initial_msg = DefaultMessage(
            dialogue_reference=(str(0), ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.ERROR,
            error_code=DefaultMessage.ErrorCode.INVALID_MESSAGE,
            error_msg="some_error_message",
            error_data={"some_data": b"some_bytes"},
        )
        invalid_initial_msg.counterparty = "agent 2"

        assert not self.dialogue._basic_rules(invalid_initial_msg)

    def test_basic_rules_negative_non_initial_message_invalid_dialogue_reference(self):
        """Test the dialogue."""
        valid_initial_msg = DefaultMessage(
            dialogue_reference=(str(0), ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        valid_initial_msg.counterparty = "agent 2"
        valid_initial_msg._is_incoming = False

        assert self.dialogue.update(valid_initial_msg)

        invalid_msg = DefaultMessage(
            dialogue_reference=(str(1), str(1)),
            message_id=2,
            target=1,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello back",
        )
        invalid_msg.counterparty = "agent 2"

        assert not self.dialogue._basic_rules(invalid_msg)

    def test_basic_rules_negative_non_initial_message_invalid_message_id(self):
        """Test the dialogue."""
        valid_initial_msg = DefaultMessage(
            dialogue_reference=(str(0), ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        valid_initial_msg.counterparty = "agent 2"
        valid_initial_msg._is_incoming = False

        assert self.dialogue.update(valid_initial_msg)

        invalid_msg = DefaultMessage(
            dialogue_reference=(str(0), str(1)),
            message_id=3,
            target=1,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello back",
        )
        invalid_msg.counterparty = "agent 2"

        assert not self.dialogue._basic_rules(invalid_msg)

    def test_basic_rules_negative_non_initial_message_invalid_target(self):
        """Test the dialogue."""
        valid_initial_msg = DefaultMessage(
            dialogue_reference=(str(0), ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        valid_initial_msg.counterparty = "agent 2"
        valid_initial_msg._is_incoming = False

        assert self.dialogue.update(valid_initial_msg)

        invalid_msg = DefaultMessage(
            dialogue_reference=(str(0), str(1)),
            message_id=2,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello back",
        )
        invalid_msg.counterparty = "agent 2"

        assert not self.dialogue._basic_rules(invalid_msg)

    # ToDo change to another Message class to test invalid non-initial performative
    # since default message does not provide this
    # def test_basic_rules_negative_non_initial_message_invalid_performative(self):
    #     """Test the dialogue."""
    #     valid_initial_msg = DefaultMessage(
    #         dialogue_reference=(str(0), ""),
    #         message_id=1,
    #         target=0,
    #         performative=DefaultMessage.Performative.BYTES,
    #         content=b"Hello",
    #     )
    #     valid_initial_msg.counterparty = "agent 2"
    #     valid_initial_msg._is_incoming = False
    #
    #     assert self.dialogue.update(valid_initial_msg)
    #
    #     invalid_msg = DefaultMessage(
    #         dialogue_reference=(str(0), str(1)),
    #         message_id=1,
    #         target=0,
    #         performative=DefaultMessage.Performative.ERROR,
    #         error_code=DefaultMessage.ErrorCode.INVALID_MESSAGE,
    #         error_msg="some_error_message",
    #         error_data={"some_data": b"some_bytes"},
    #     )
    #     invalid_msg.counterparty = "agent 2"
    #
    #     assert not self.dialogue._basic_rules(invalid_msg)

    def test_additional_rules_positive(self):
        """Test the dialogue."""
        valid_initial_msg = DefaultMessage(
            dialogue_reference=(str(0), ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        valid_initial_msg.counterparty = "agent 2"
        valid_initial_msg._is_incoming = False

        assert self.dialogue.update(valid_initial_msg)

        valid_second_msg = DefaultMessage(
            dialogue_reference=(str(0), str(1)),
            message_id=2,
            target=1,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello back",
        )
        valid_second_msg.counterparty = "agent 2"
        valid_second_msg._is_incoming = True

        assert self.dialogue.update(valid_second_msg)

        valid_third_msg = DefaultMessage(
            dialogue_reference=(str(0), str(1)),
            message_id=3,
            target=2,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello back 2",
        )
        valid_third_msg.counterparty = "agent 2"
        valid_third_msg._is_incoming = False

        assert self.dialogue._additional_rules(valid_third_msg)

    def test_additional_rules_negative_invalid_target(self):
        """Test the dialogue."""
        valid_initial_msg = DefaultMessage(
            dialogue_reference=(str(0), ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        valid_initial_msg.counterparty = "agent 2"
        valid_initial_msg._is_incoming = False

        assert self.dialogue.update(valid_initial_msg)

        valid_second_msg = DefaultMessage(
            dialogue_reference=(str(0), str(1)),
            message_id=2,
            target=1,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello back",
        )
        valid_second_msg.counterparty = "agent 2"
        valid_second_msg._is_incoming = True

        assert self.dialogue.update(valid_second_msg)

        invalid_third_msg = DefaultMessage(
            dialogue_reference=(str(0), str(1)),
            message_id=3,
            target=1,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello back 2",
        )
        invalid_third_msg.counterparty = "agent 2"
        invalid_third_msg._is_incoming = False

        assert not self.dialogue._additional_rules(invalid_third_msg)

    def test_update_dialogue_label_positive(self):
        """Test the dialogue."""
        valid_initial_msg = DefaultMessage(
            dialogue_reference=(str(0), ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        valid_initial_msg.counterparty = "agent 2"
        valid_initial_msg._is_incoming = False

        assert self.dialogue.update(valid_initial_msg)

        new_label = DialogueLabel(
            (str(0), str(1)), valid_initial_msg.counterparty, "agent 1"
        )
        self.dialogue.update_dialogue_label(new_label)

        assert self.dialogue.dialogue_label == new_label

    def test_update_dialogue_label_negative_invalid_existing_label(self):
        """Test the dialogue."""
        valid_initial_msg = DefaultMessage(
            dialogue_reference=(str(0), ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        valid_initial_msg.counterparty = "agent 2"
        valid_initial_msg._is_incoming = False

        assert self.dialogue.update(valid_initial_msg)

        valid_second_msg = DefaultMessage(
            dialogue_reference=(str(0), str(1)),
            message_id=2,
            target=1,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello back",
        )
        valid_second_msg.counterparty = "agent 2"
        valid_second_msg._is_incoming = True

        assert self.dialogue.update(valid_second_msg)

        new_label = DialogueLabel(
            (str(0), str(2)), valid_initial_msg.counterparty, "agent 1"
        )
        try:
            self.dialogue.update_dialogue_label(new_label)
            result = True
        except AssertionError:
            result = False

        assert not result and self.dialogue.dialogue_label != new_label

    def test_update_dialogue_label_negative_invalid_input_label(self):
        """Test the dialogue."""
        valid_initial_msg = DefaultMessage(
            dialogue_reference=(str(0), ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        valid_initial_msg.counterparty = "agent 2"
        valid_initial_msg._is_incoming = False

        assert self.dialogue.update(valid_initial_msg)

        new_label = DialogueLabel(
            (str(1), ""), valid_initial_msg.counterparty, "agent 1"
        )
        try:
            self.dialogue.update_dialogue_label(new_label)
            result = True
        except AssertionError:
            result = False

        assert not result and self.dialogue.dialogue_label != new_label

    def test___str__(self):
        valid_initial_msg = DefaultMessage(
            dialogue_reference=(str(0), ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        valid_initial_msg.counterparty = "agent 2"
        valid_initial_msg._is_incoming = False

        assert self.dialogue.update(valid_initial_msg)

        valid_second_msg = DefaultMessage(
            dialogue_reference=(str(0), str(1)),
            message_id=2,
            target=1,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello back",
        )
        valid_second_msg.counterparty = "agent 2"
        valid_second_msg._is_incoming = True

        assert self.dialogue.update(valid_second_msg)

        valid_third_msg = DefaultMessage(
            dialogue_reference=(str(0), str(1)),
            message_id=3,
            target=2,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello back 2",
        )
        valid_third_msg.counterparty = "agent 2"
        valid_third_msg._is_incoming = False

        assert self.dialogue.update(valid_third_msg)

        dialogue_str = (
            "Dialogue Label: 0_1_agent 2_agent 1\nbytes( )\nbytes( )\nbytes( )"
        )

        assert str(self.dialogue) == dialogue_str


class TestDialoguesBase:
    """Test the dialogue/base.py."""

    @classmethod
    def setup(cls):
        """Initialise the class."""
        cls.dialogue_label = DialogueLabel(
            dialogue_reference=(str(0), ""),
            dialogue_opponent_addr="agent 2",
            dialogue_starter_addr="agent 1",
        )
        cls.dialogue = Dialogue(dialogue_label=cls.dialogue_label)
        cls.dialogues = Dialogues("agent 1")

    def test_constructor(self):
        """Test the dialogues."""
        assert isinstance(self.dialogues.dialogues, Dict)
        id = self.dialogues._next_dialogue_nonce()
        assert id > 0

    def test_dialogues_properties(self):
        """Test dialogues properties."""
        assert self.dialogues.dialogues == dict()
        assert self.dialogues.agent_address == "agent 1"
        assert self.dialogues.dialogue_stats.other_initiated == dict()
        assert self.dialogues.dialogue_stats.self_initiated == dict()

    def test_new_self_initiated_dialogue_reference(self):
        assert self.dialogues.new_self_initiated_dialogue_reference() == ("1", "")

        self.dialogues._create_opponent_initiated(
            "agent 2", ("1", ""), Dialogue.Role.ROLE1
        )
        assert self.dialogues.new_self_initiated_dialogue_reference() == ("2", "")

    def test_create_positive(self):
        assert len(self.dialogues.dialogues) == 0
        self.dialogues.create(
            "agent 2", DefaultMessage.Performative.BYTES, content=b"Hello"
        )
        assert len(self.dialogues.dialogues) == 1

    def test_create_negative_incorrect_performative_content_combination(self):
        assert len(self.dialogues.dialogues) == 0
        try:
            self.dialogues.create(
                "agent 2", DefaultMessage.Performative.ERROR, content=b"Hello"
            )
        except Exception:
            pass
        assert len(self.dialogues.dialogues) == 0
