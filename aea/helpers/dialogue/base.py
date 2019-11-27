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
from typing import Dict, List, Optional, cast

from aea.protocols.base import Message


class DialogueLabel:
    """The dialogue label class acts as an identifier for dialogues."""

    def __init__(self, dialogue_id: int, dialogue_opponent_pbk: str, dialogue_starter_pbk: str) -> None:
        """
        Initialize a dialogue label.

        :param dialogue_id: the id of the dialogue.
        :param dialogue_opponent_pbk: the pbk of the agent with which the dialogue is kept.
        :param dialogue_starter_pbk: the pbk of the agent which started the dialogue.

        :return: None
        """
        self._dialogue_id = dialogue_id
        self._dialogue_opponent_pbk = dialogue_opponent_pbk
        self._dialogue_starter_pbk = dialogue_starter_pbk

    @property
    def dialogue_id(self) -> int:
        """Get the dialogue id."""
        return self._dialogue_id

    @property
    def dialogue_opponent_pbk(self) -> str:
        """Get the public key of the dialogue opponent."""
        return self._dialogue_opponent_pbk

    @property
    def dialogue_starter_pbk(self) -> str:
        """Get the public key of the dialogue starter."""
        return self._dialogue_starter_pbk

    def __eq__(self, other) -> bool:
        """Check for equality between two DialogueLabel objects."""
        if type(other) == DialogueLabel:
            return self._dialogue_id == other.dialogue_id and self._dialogue_starter_pbk == other.dialogue_starter_pbk and self._dialogue_opponent_pbk == other.dialogue_opponent_pbk
        else:
            return False

    def __hash__(self) -> int:
        """Turn object into hash."""
        return hash((self.dialogue_id, self.dialogue_opponent_pbk, self.dialogue_starter_pbk))

    @property
    def json(self) -> Dict:
        """Return the JSON representation."""
        return {
            "dialogue_id": str(self.dialogue_id),
            "dialogue_opponent_pbk": self.dialogue_opponent_pbk,
            "dialogue_starter_pbk": self.dialogue_starter_pbk
        }

    @classmethod
    def from_json(cls, obj: Dict[str, str]) -> 'DialogueLabel':
        """Get dialogue label from json."""
        dialogue_label = DialogueLabel(
            int(cast(str, obj.get('dialogue_id'))),
            cast(str, obj.get('dialogue_opponent_pbk')),
            cast(str, obj.get('dialogue_starter_pbk'))
        )
        return dialogue_label


class Dialogue:
    """The dialogue class maintains state of a dialogue and manages it."""

    def __init__(self, dialogue_label: DialogueLabel) -> None:
        """
        Initialize a dialogue label.

        :param dialogue_label: the identifier of the dialogue

        :return: None
        """
        self._dialogue_label = dialogue_label
        self._is_self_initiated = dialogue_label.dialogue_opponent_pbk is not dialogue_label.dialogue_starter_pbk
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

    def outgoing_extend(self, message: 'Message') -> None:
        """
        Extend the list of messages which keeps track of outgoing messages.

        :param message: a message to be added
        :return: None
        """
        self._outgoing_messages.extend([message])

    def incoming_extend(self, message: 'Message') -> None:
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
        self._dialogue_id = 0

    @property
    def dialogues(self) -> Dict[DialogueLabel, Dialogue]:
        """Get dictionary of dialogues in which the agent is engaged in."""
        return self._dialogues

    @abstractmethod
    def is_permitted_for_new_dialogue(self, msg: Message, sender: str) -> bool:
        """
        Check whether an agent message is permitted for a new dialogue.

        :param msg: the agent message
        :param sender: the address of the sender

        :return: a boolean indicating whether the message is permitted for a new dialogue
        """

    @abstractmethod
    def is_belonging_to_registered_dialogue(self, msg: Message, sender: str, agent_pbk: str) -> bool:
        """
        Check whether an agent message is part of a registered dialogue.

        :param msg: the agent message
        :param sender: the address of the sender
        :param agent_pbk: the public key of the agent

        :return: boolean indicating whether the message belongs to a registered dialogue
        """

    @abstractmethod
    def get_dialogue(self, msg: Message, sender: str, agent_pbk: str) -> Dialogue:
        """
        Retrieve dialogue.

        :param msg: the agent message
        :param sender: the address of the sender
        :param agent_pbk: the public key of the agent

        :return: the dialogue
        """

    def _next_dialogue_id(self) -> int:
        """
        Increment the id and returns it.

        :return: the next id
        """
        self._dialogue_id += 1
        return self._dialogue_id
