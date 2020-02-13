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

"""
This module contains the classes required for dialogue management.

- DialogueLabel: The dialogue label class acts as an identifier for dialogues.
- Dialogue: The dialogue class maintains state of a dialogue and manages it.
- Dialogues: The dialogues class keeps track of all dialogues.
"""

from abc import abstractmethod
from typing import Dict, List, Optional, Tuple, cast

from aea.mail.base import Address
from aea.protocols.base import Message


class DialogueLabel:
    """The dialogue label class acts as an identifier for dialogues."""

    def __init__(
        self,
        dialogue_reference: Tuple[str, str],
        dialogue_opponent_addr: Address,
        dialogue_starter_addr: Address,
    ) -> None:
        """
        Initialize a dialogue label.

        :param dialogue_reference: the reference of the dialogue.
        :param dialogue_opponent_addr: the addr of the agent with which the dialogue is kept.
        :param dialogue_starter_addr: the addr of the agent which started the dialogue.

        :return: None
        """
        self._dialogue_reference = dialogue_reference
        self._dialogue_opponent_addr = dialogue_opponent_addr
        self._dialogue_starter_addr = dialogue_starter_addr

    @property
    def dialogue_reference(self) -> Tuple[str, str]:
        """Get the dialogue reference."""
        return self._dialogue_reference

    @property
    def dialogue_starter_reference(self) -> str:
        """Get the dialogue starter reference."""
        return self._dialogue_reference[0]

    @property
    def dialogue_responder_reference(self) -> str:
        """Get the dialogue responder reference."""
        return self._dialogue_reference[1]

    @property
    def dialogue_opponent_addr(self) -> str:
        """Get the address of the dialogue opponent."""
        return self._dialogue_opponent_addr

    @property
    def dialogue_starter_addr(self) -> str:
        """Get the address of the dialogue starter."""
        return self._dialogue_starter_addr

    def __eq__(self, other) -> bool:
        """Check for equality between two DialogueLabel objects."""
        if type(other) == DialogueLabel:
            return (
                self.dialogue_reference == other.dialogue_reference
                and self.dialogue_starter_addr == other.dialogue_starter_addr
                and self.dialogue_opponent_addr == other.dialogue_opponent_addr
            )
        else:
            return False

    def __hash__(self) -> int:
        """Turn object into hash."""
        return hash(
            (
                self.dialogue_reference,
                self.dialogue_opponent_addr,
                self.dialogue_starter_addr,
            )
        )

    @property
    def json(self) -> Dict:
        """Return the JSON representation."""
        return {
            "dialogue_starter_reference": self.dialogue_starter_reference,
            "dialogue_responder_reference": self.dialogue_responder_reference,
            "dialogue_opponent_addr": self.dialogue_opponent_addr,
            "dialogue_starter_addr": self.dialogue_starter_addr,
        }

    @classmethod
    def from_json(cls, obj: Dict[str, str]) -> "DialogueLabel":
        """Get dialogue label from json."""
        dialogue_label = DialogueLabel(
            (
                cast(str, obj.get("dialogue_starter_reference")),
                cast(str, obj.get("dialogue_responder_reference")),
            ),
            cast(str, obj.get("dialogue_opponent_addr")),
            cast(str, obj.get("dialogue_starter_addr")),
        )
        return dialogue_label

    def __str__(self):
        """Get the string representation."""
        return "{}_{}_{}_{}".format(
            self.dialogue_starter_reference,
            self.dialogue_responder_reference,
            self.dialogue_opponent_addr,
            self.dialogue_starter_addr,
        )


class Dialogue:
    """The dialogue class maintains state of a dialogue and manages it."""

    def __init__(self, dialogue_label: DialogueLabel) -> None:
        """
        Initialize a dialogue label.

        :param dialogue_label: the identifier of the dialogue

        :return: None
        """
        self._dialogue_label = dialogue_label
        self._is_self_initiated = (
            dialogue_label.dialogue_opponent_addr
            is not dialogue_label.dialogue_starter_addr
        )
        self._outgoing_messages = []  # type: List[Message]
        self._incoming_messages = []  # type: List[Message]

    @property
    def dialogue_label(self) -> DialogueLabel:
        """Get the dialogue lable."""
        return self._dialogue_label

    @property
    def is_self_initiated(self) -> bool:
        """Check whether the agent initiated the dialogue."""
        return self._is_self_initiated

    @property
    def last_incoming_message(self) -> Optional[Message]:
        """Get the last incoming message."""
        return self._incoming_messages[-1] if len(self._incoming_messages) > 0 else None

    @property
    def last_outgoing_message(self) -> Optional[Message]:
        """Get the last incoming message."""
        return self._outgoing_messages[-1] if len(self._outgoing_messages) > 0 else None

    def outgoing_extend(self, message: "Message") -> None:
        """
        Extend the list of messages which keeps track of outgoing messages.

        :param message: a message to be added
        :return: None
        """
        self._outgoing_messages.extend([message])

    def incoming_extend(self, message: "Message") -> None:
        """
        Extend the list of messages which keeps track of incoming messages.

        :param messages: a message to be added
        :return: None
        """
        self._incoming_messages.extend([message])


class Dialogues:
    """The dialogues class keeps track of all dialogues."""

    def __init__(self) -> None:
        """
        Initialize dialogues.

        :return: None
        """
        self._dialogues = {}  # type: Dict[DialogueLabel, Dialogue]
        self._dialogue_nonce = 0

    @property
    def dialogues(self) -> Dict[DialogueLabel, Dialogue]:
        """Get dictionary of dialogues in which the agent is engaged in."""
        return self._dialogues

    @abstractmethod
    def is_permitted_for_new_dialogue(self, msg: Message) -> bool:
        """
        Check whether an agent message is permitted for a new dialogue.

        :param msg: the agent message

        :return: a boolean indicating whether the message is permitted for a new dialogue
        """

    @abstractmethod
    def is_belonging_to_registered_dialogue(
        self, msg: Message, agent_addr: Address
    ) -> bool:
        """
        Check whether an agent message is part of a registered dialogue.

        :param msg: the agent message
        :param agent_addr: the address of the agent

        :return: boolean indicating whether the message belongs to a registered dialogue
        """

    @abstractmethod
    def get_dialogue(self, msg: Message, agent_addr: Address) -> Dialogue:
        """
        Retrieve dialogue.

        :param msg: the agent message
        :param agent_addr: the address of the agent

        :return: the dialogue
        """

    def _next_dialogue_nonce(self) -> int:
        """
        Increment the nonce and returns it.

        :return: the next nonce
        """
        self._dialogue_nonce += 1
        return self._dialogue_nonce
