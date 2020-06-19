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

    INITIAL_PERFORMATIVES = frozenset({})  # type: FrozenSet[Message.Performative]
    TERMINAL_PERFORMATIVES = frozenset({})  # type: FrozenSet[Message.Performative]
    VALID_REPLIES = (
        {}
    )  # type: Dict[Message.Performative, FrozenSet[Message.Performative]]

    def __init__(
        self,
        dialogue_label: DialogueLabel,
        agent_address: Optional[Address] = None,
        role: Optional[BaseDialogue.Role] = None,
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
        pass


class Dialogues(BaseDialogues):

    END_STATES = frozenset({})  # type: FrozenSet[BaseDialogue.EndState]

    def __init__(self, agent_address: Address) -> None:
        """
        Initialize dialogues.

        :param agent_address: the address of the agent for whom dialogues are maintained
        :return: None
        """
        BaseDialogues.__init__(
            self,
            agent_address=agent_address,
            end_states=cast(FrozenSet[BaseDialogue.EndState], self.END_STATES),
        )

    def create_dialogue(
        self, dialogue_label: DialogueLabel, role: Dialogue.Role,
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


class TestDialogueBase:
    """Test the dialogue/base.py."""

    @classmethod
    def setup(cls):
        """Initialise the class."""
        cls.dialogue_label = DialogueLabel(
            dialogue_reference=(str(0), ""),
            dialogue_opponent_addr="opponent",
            dialogue_starter_addr="starter",
        )
        cls.dialogue = Dialogue(dialogue_label=cls.dialogue_label)
        cls.dialogues = Dialogues("address")

    def test_dialogue_label(self):
        """Test the dialogue_label."""
        assert self.dialogue_label.dialogue_starter_reference == str(0)
        assert self.dialogue_label.dialogue_responder_reference == ""
        assert self.dialogue_label.dialogue_opponent_addr == "opponent"
        assert self.dialogue_label.dialogue_starter_addr == "starter"
        assert str(self.dialogue_label) == "{}_{}_{}_{}".format(
            self.dialogue_label.dialogue_starter_reference,
            self.dialogue_label.dialogue_responder_reference,
            self.dialogue_label.dialogue_opponent_addr,
            self.dialogue_label.dialogue_starter_addr,
        )

        dialogue_label2 = DialogueLabel(
            dialogue_reference=(str(0), ""),
            dialogue_opponent_addr="opponent",
            dialogue_starter_addr="starter",
        )

        assert dialogue_label2 == self.dialogue_label

        dialogue_label3 = "This is a test"

        assert not dialogue_label3 == self.dialogue_label

        assert hash(self.dialogue_label) == hash(self.dialogue.dialogue_label)

        assert self.dialogue_label.json == dict(
            dialogue_starter_reference=str(0),
            dialogue_responder_reference="",
            dialogue_opponent_addr="opponent",
            dialogue_starter_addr="starter",
        )
        assert DialogueLabel.from_json(self.dialogue_label.json) == self.dialogue_label

    def test_dialogue(self):
        """Test the dialogue."""
        assert self.dialogue.is_self_initiated
        msg = DefaultMessage(
            dialogue_reference=("", ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.BYTES,
            content=b"Hello",
        )
        msg.counterparty = "my_agent"
        assert self.dialogue.last_incoming_message is None
        assert self.dialogue.last_outgoing_message is None

        self.dialogue._outgoing_messages.extend([msg])
        assert self.dialogue.last_outgoing_message == msg

        self.dialogue._incoming_messages.extend([msg])
        assert self.dialogue.last_incoming_message == msg

    def test_dialogues(self):
        """Test the dialogues."""
        assert isinstance(self.dialogues.dialogues, Dict)
        id = self.dialogues._next_dialogue_nonce()
        assert id > 0
