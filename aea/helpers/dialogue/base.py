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

import itertools
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, FrozenSet, List, Optional, Tuple, cast

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


class Dialogue(ABC):
    """The dialogue class maintains state of a dialogue and manages it."""

    STARTING_MESSAGE_ID = 1
    STARTING_TARGET = 0

    class Role(Enum):
        """This class defines the agent's role in a dialogue."""

        def __str__(self):
            """Get the string representation."""
            return self.value

    class EndState(Enum):
        """This class defines the end states of a dialogue."""

        def __str__(self):
            """Get the string representation."""
            return self.value

    def __init__(
        self,
        dialogue_label: DialogueLabel,
        agent_address: Optional[Address] = None,
        role: Optional[Role] = None,
    ) -> None:
        """
        Initialize a dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param agent_address: the address of the agent for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for

        :return: None
        """
        self._agent_address = agent_address
        self._dialogue_label = dialogue_label
        self._role = role

        self._is_self_initiated = (
            dialogue_label.dialogue_opponent_addr
            is not dialogue_label.dialogue_starter_addr
        )

        self._outgoing_messages = []  # type: List[Message]
        self._incoming_messages = []  # type: List[Message]

    @property
    def dialogue_label(self) -> DialogueLabel:
        """
        Get the dialogue label.

        :return: The dialogue label
        """
        return self._dialogue_label

    @property
    def agent_address(self) -> Address:
        """
        Get the address of the agent for whom this dialogues is maintained.

        :return: the agent address
        """
        assert self._agent_address is not None, "agent_address is not set."
        return self._agent_address

    @agent_address.setter
    def agent_address(self, agent_address: Address) -> None:
        """
        Set the address of the agent for whom this dialogues is maintained.

        :param: the agent address
        """
        self._agent_address = agent_address

    @property
    def role(self) -> "Role":
        """
        Get the agent's role in the dialogue.

        :return: the agent's role
        """
        assert self._role is not None, "Role is not set."
        return self._role

    @role.setter
    def role(self, role: "Role") -> None:
        """
        Set the agent's role in the dialogue.

        :param role: the agent's role
        :return: None
        """
        self._role = role

    @property
    def is_self_initiated(self) -> bool:
        """
        Check whether the agent initiated the dialogue.

        :return: True if the agent initiated the dialogue, False otherwise
        """
        return self._is_self_initiated

    @property
    def last_incoming_message(self) -> Optional[Message]:
        """
        Get the last incoming message.

        :return: the last incoming message if it exists, None otherwise
        """
        return self._incoming_messages[-1] if len(self._incoming_messages) > 0 else None

    @property
    def last_outgoing_message(self) -> Optional[Message]:
        """
        Get the last outgoing message.

        :return: the last outgoing message if it exists, None otherwise
        """
        return self._outgoing_messages[-1] if len(self._outgoing_messages) > 0 else None

    @property
    def last_message(self) -> Optional[Message]:
        """
        Get the last message.

        :return: the last message if it exists, None otherwise
        """
        last_message = None  # type: Optional[Message]
        if (
            self.last_incoming_message is not None
            and self.last_outgoing_message is not None
        ):
            last_message = (
                self.last_outgoing_message
                if self.last_outgoing_message.message_id
                > self.last_incoming_message.message_id
                else self.last_incoming_message
            )
        elif self.last_incoming_message is not None:
            last_message = self.last_incoming_message
        elif self.last_outgoing_message is not None:
            last_message = self.last_outgoing_message

        return last_message

    def get_message(self, message_id_to_find: int) -> Optional[Message]:
        """
        Get the message whose id is 'message_id'.

        :param message_id_to_find: the id of the message
        :return: the message if it exists, None otherwise
        """

        result = None  # type: Optional[Message]
        list_of_all_messages = self._outgoing_messages + self._incoming_messages
        for message in list_of_all_messages:
            if message.message_id == message_id_to_find:
                result = message
                break

        return result

    @property
    def is_empty(self) -> bool:
        """
        Check whether the dialogue is empty

        :return: True if empty, False otherwise
        """
        return len(self._outgoing_messages) == 0 and len(self._incoming_messages) == 0

    def update(self, message: Message) -> bool:
        """
        Extend the list of incoming/outgoing messages with 'message', if 'message' is valid

        :param message: a message to be added
        :return: True if message successfully added, false otherwise
        """
        is_extendable = self.is_valid_next_message(message)
        if is_extendable:
            if message.is_incoming:
                self._update_self_initiated_dialogue_label_on_second_message(message)
                self._incoming_messages.extend([message])
            else:
                self._outgoing_messages.extend([message])
        return is_extendable

    def _update_self_initiated_dialogue_label_on_second_message(
        self, second_message: Message
    ) -> None:
        """
        Update this (self initiated) dialogue's dialogue_label with a complete dialogue reference from counterparty's first message

        :param second_message: The second message in the dialogue (the first by the counterparty)
        :return: None
        """
        dialogue_reference = cast(
            Tuple[str, str], second_message.get("dialogue_reference")
        )
        self_initiated_dialogue_reference = (dialogue_reference[0], "")
        self_initiated_dialogue_label = DialogueLabel(
            self_initiated_dialogue_reference,
            second_message.counterparty,
            self.agent_address,
        )

        if not self.is_empty:
            message_id = second_message.message_id

            if (
                self.dialogue_label == self_initiated_dialogue_label
                and self.last_message.message_id == 1  # type: ignore
                and message_id == 2
                and second_message.is_incoming
            ):
                updated_dialogue_label = DialogueLabel(
                    dialogue_reference,
                    self_initiated_dialogue_label.dialogue_opponent_addr,
                    self_initiated_dialogue_label.dialogue_starter_addr,
                )
                self._dialogue_label = updated_dialogue_label

    def is_valid_next_message(self, message: Message) -> bool:
        """
        Check whether 'message' is a valid next message in this dialogue.

        The evaluation of a message validity involves performing several categories of checks.
        Each category of checks resides in a separate method.

        Currently, basic rules are fundamental structural constraints,
        additional rules are applied for the time being, and more specific rules are captured in the is_valid method.

        :param message: the message to be validated
        :return: True if yes, False otherwise.
        """
        return (
            self._basic_rules(message)
            and self._additional_rules(message)
            and self.is_valid(message)
        )

    def _basic_rules(self, message: Message) -> bool:
        """
        Check whether 'message' is a valid next message in the dialogue, according to basic rules.

        These rules are designed to be fundamental to all dialogues, and enforce the following:

         - message ids are consistent
         - targets are consistent
         - message targets are according to the reply structure of performatives

        :param message: the message to be validated
        :return: True if valid, False otherwise.
        """
        message_id = message.message_id
        target = cast(int, message.get("target"))
        performative = message.get("performative")

        if self.is_empty:
            result = (
                message_id == Dialogue.STARTING_MESSAGE_ID
                and target == Dialogue.STARTING_TARGET
                and performative == self.initial_performative()
            )
        else:
            last_message_id = self.last_message.message_id  # type: ignore
            target_message = self.get_message(target)
            if target_message is not None:
                target_performative = target_message.get("performative")
                result = (
                    message_id == last_message_id + 1
                    and 1 <= target <= last_message_id
                    and performative in self.reply(target_performative)
                )
            else:
                result = False
        return result

    def _additional_rules(self, message: Message) -> bool:
        """
        Check whether 'message' is a valid next message in the dialogue, according to additional rules.

        These rules are designed to be less fundamental than basic rules and subject to change.
        Currently the following is enforced:

         - A message targets the message strictly before it in the dialogue

        :param message: the message to be validated
        :return: True if valid, False otherwise.
        """
        if self.is_empty:
            result = True
        else:
            target = cast(int, message.get("target"))
            last_target = self.last_message.target  # type: ignore
            result = target == last_target + 1
        return result

    @abstractmethod
    def initial_performative(self):
        """
        Get the performative which the initial message in the dialogue must have

        :return: the performative of the initial message
        """

    @abstractmethod
    def reply(self, performative) -> FrozenSet:
        """
        Given a `performative`, return the list of performatives which are its valid replies in a dialogue

        :param performative: the performative in a message
        :return: list of valid performative replies
        """

    @abstractmethod
    def is_valid(self, message: Message) -> bool:
        """
        Check whether 'message' is a valid next message in the dialogue.

        These rules capture specific constraints designed for dialogues which are instance of a concrete sub-class of this class.

        :param message: the message to be validated
        :return: True if valid, False otherwise.
        """

    @staticmethod
    @abstractmethod
    def role_from_first_message(message: Message) -> "Role":
        """
        Infer the role of the agent from an incoming or outgoing first message

        :param message: an incoming/outgoing first message
        :return: the agent's role
        """

    @staticmethod
    @abstractmethod
    def from_args(
        dialogue_label: DialogueLabel,
        agent_address: Address,
        role: Optional[Role] = None,
    ) -> "Dialogue":
        """
        Instantiate an object of this class from the above arguments

        :param dialogue_label: the identifier of the dialogue
        :param agent_address: the address of the agent for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for

        :return: The role of the agent
        """

    @staticmethod
    def _interleave(list_1, list_2) -> List:
        all_elements = [
            element
            for element in itertools.chain(*itertools.zip_longest(list_1, list_2))
            if element is not None
        ]

        return all_elements

    def __str__(self) -> str:
        """
        Get the string representation.

        :return: The string representation of the dialogue
        """
        representation = "Dialogue Label: " + str(self.dialogue_label) + "\n"

        if self.is_self_initiated:
            all_messages = self._interleave(
                self._outgoing_messages, self._incoming_messages
            )
        else:
            all_messages = self._interleave(
                self._incoming_messages, self._outgoing_messages
            )

        for msg in all_messages:
            representation += str(msg.performative) + "( )\n"

        representation = representation[:-1]
        return representation

    # ToDo the following methods are left for backwards compatibility reasons and are unsafe to use. They will be removed in the future
    def outgoing_extend(self, message: Message) -> None:
        """
        UNSAFE TO USE - IS DEPRECATED - USE update(message) METHOD INSTEAD
        Extend the list of outgoing messages with 'message'

        :param message: a message to be added
        :return: None
        """
        self._outgoing_messages.extend([message])

    def incoming_extend(self, message: Message) -> None:
        """
        UNSAFE TO USE - IS DEPRECATED - USE update(message) METHOD INSTEAD
        Extend the list of incoming messages with 'message'

        :param message: a message to be added
        :return: None
        """
        self._incoming_messages.extend([message])


class Dialogues:
    """The dialogues class keeps track of all dialogues for an agent."""

    def __init__(self, agent_address: Address = "") -> None:
        """
        Initialize dialogues.

        :param agent_address: the address of the agent for whom dialogues are maintained
        :return: None
        """
        self._dialogues = {}  # type: Dict[DialogueLabel, Dialogue]
        self._agent_address = agent_address
        self._dialogue_nonce = 0

    @property
    def dialogues(self) -> Dict[DialogueLabel, Dialogue]:
        """Get dictionary of dialogues in which the agent engages."""
        return self._dialogues

    @property
    def agent_address(self) -> Address:
        """Get the address of the agent for whom dialogues are maintained."""
        assert self._agent_address != "", "agent_address is not set."
        return self._agent_address

    def new_self_initiated_dialogue_reference(self) -> Tuple[str, str]:
        """
        Return a dialogue label for a new self initiated dialogue

        :return: the next nonce
        """
        return str(self._dialogue_nonce + 1), ""

    def update(self, message: Message) -> Optional[Dialogue]:
        """
        Update the state of dialogues with a new message.

        If the message is for a new dialogue, a new dialogue is created with 'message' as its first message and returned.
        If the message is addressed to an existing dialogue, the dialogue is retrieved, extended with this message and returned.
        If there are any errors, e.g. the message dialogue reference does not exists or the message is invalid w.r.t. the dialogue, return None.

        :param message: a new message
        :return: the new or existing dialogue the message is intended for, or None in case of any errors.
        """
        dialogue_reference = cast(Tuple[str, str], message.get("dialogue_reference"))

        if (  # new dialogue by other
            dialogue_reference[0] != ""
            and dialogue_reference[1] == ""
            and message.is_incoming
        ):
            dialogue = self._create_opponent_initiated(
                dialogue_opponent_addr=message.counterparty,
                dialogue_reference=dialogue_reference,
                role=Dialogue.role_from_first_message(message),
            )  # type: Optional[Dialogue]
        elif (  # new dialogue by self
            dialogue_reference[0] != ""
            and dialogue_reference[1] == ""
            and not message.is_incoming
        ):
            assert (
                message.counterparty is not None
            ), "The message counter-party field is not set {}".format(message)
            dialogue = self._create_self_initiated(
                dialogue_opponent_addr=message.counterparty,
                role=Dialogue.role_from_first_message(message),
            )
        else:  # existing dialogue
            self._update_self_initiated_dialogue_label_on_second_message(message)
            dialogue = self._get_dialogue(message)

        if dialogue is not None:
            dialogue.update(message)
            result = dialogue  # type: Optional[Dialogue]
        else:  # couldn't find the dialogue
            result = None

        return result

    def _update_self_initiated_dialogue_label_on_second_message(
        self, second_message: Message
    ) -> None:
        """
        Update a self initiated dialogue label with a complete dialogue reference from counterparty's first message

        :param second_message: The second message in the dialogue (the first by the counterparty in a self initiated dialogue)
        :return: None
        """
        dialogue_reference = cast(
            Tuple[str, str], second_message.get("dialogue_reference")
        )

        self_initiated_dialogue_reference = (dialogue_reference[0], "")
        self_initiated_dialogue_label = DialogueLabel(
            self_initiated_dialogue_reference,
            second_message.counterparty,
            self.agent_address,
        )

        if self_initiated_dialogue_label in self.dialogues:
            self_initiated_dialogue = self.dialogues[self_initiated_dialogue_label]
            self.dialogues.pop(self_initiated_dialogue_label)
            final_dialogue_label = DialogueLabel(
                dialogue_reference,
                self_initiated_dialogue_label.dialogue_opponent_addr,
                self_initiated_dialogue_label.dialogue_starter_addr,
            )
            self_initiated_dialogue._dialogue_label = final_dialogue_label
            assert self_initiated_dialogue.dialogue_label not in self.dialogues
            self.dialogues.update(
                {self_initiated_dialogue.dialogue_label: self_initiated_dialogue}
            )

    def _get_dialogue(self, message: Message) -> Optional[Dialogue]:
        """
        Retrieve the dialogue 'message' belongs to.

        :param message: a message
        :return: the dialogue, or None in case such a dialogue does not exist
        """
        dialogue_reference = cast(Tuple[str, str], message.get("dialogue_reference"))
        counterparty = message.counterparty

        self_initiated_dialogue_label = DialogueLabel(
            dialogue_reference, counterparty, self.agent_address
        )
        other_initiated_dialogue_label = DialogueLabel(
            dialogue_reference, counterparty, counterparty
        )

        if other_initiated_dialogue_label in self.dialogues:
            result = self.dialogues[
                other_initiated_dialogue_label
            ]  # type: Optional[Dialogue]
        elif self_initiated_dialogue_label in self.dialogues:
            result = self.dialogues[self_initiated_dialogue_label]
        else:
            result = None

        return result

    def _create_self_initiated(
        self, dialogue_opponent_addr: Address, role: Dialogue.Role,
    ) -> Dialogue:
        """
        Create a self initiated dialogue.

        :param dialogue_opponent_addr: the pbk of the agent with which the dialogue is kept.
        :param role: the agent's role

        :return: the created dialogue.
        """
        dialogue_reference = (str(self._next_dialogue_nonce()), "")
        dialogue_label = DialogueLabel(
            dialogue_reference, dialogue_opponent_addr, self.agent_address
        )
        dialogue = self._create_dialogue(dialogue_label=dialogue_label, role=role)
        self.dialogues.update({dialogue_label: dialogue})
        return dialogue

    def _create_opponent_initiated(
        self,
        dialogue_opponent_addr: Address,
        dialogue_reference: Tuple[str, str],
        role: Dialogue.Role,
    ) -> Dialogue:
        """
        Create an opponent initiated dialogue.

        :param dialogue_opponent_addr: the address of the agent with which the dialogue is kept.
        :param dialogue_reference: the reference of the dialogue.
        :param role: the agent's role

        :return: the created dialogue
        """
        assert (
            dialogue_reference[0] != "" and dialogue_reference[1] == ""
        ), "Cannot initiate dialogue with preassigned dialogue_responder_reference!"
        new_dialogue_reference = (
            dialogue_reference[0],
            str(self._next_dialogue_nonce()),
        )
        dialogue_label = DialogueLabel(
            new_dialogue_reference, dialogue_opponent_addr, dialogue_opponent_addr
        )

        assert dialogue_label not in self.dialogues
        dialogue = self._create_dialogue(dialogue_label=dialogue_label, role=role)
        self.dialogues.update({dialogue_label: dialogue})

        return dialogue

    @abstractmethod
    def _create_dialogue(
        self, dialogue_label: DialogueLabel, role: Dialogue.Role,
    ) -> Dialogue:
        """
        Create a dialogue.

        :param dialogue: the address of the agent with which the dialogue is kept.
        :param role: the agent's role

        :return: the created dialogue
        """

    def _next_dialogue_nonce(self) -> int:
        """
        Increment the nonce and return it.

        :return: the next nonce
        """
        self._dialogue_nonce += 1
        return self._dialogue_nonce

    # TODO the following method is left for backwards compatibility reasons and will be removed in the future
    def is_belonging_to_registered_dialogue(
        self, msg: Message, agent_addr: Address
    ) -> bool:
        """
        DEPRECATED

        Check whether an agent message is part of a registered dialogue.

        :param msg: the agent message
        :param agent_addr: the address of the agent

        :return: boolean indicating whether the message belongs to a registered dialogue
        """
        pass

    # TODO the following method is left for backwards compatibility reasons and will be removed in the future
    def is_permitted_for_new_dialogue(self, msg: Message) -> bool:
        """
        DEPRECATED

        Check whether an agent message is permitted for a new dialogue.

        :param msg: the agent message
        :return: a boolean indicating whether the message is permitted for a new dialogue
        """
        pass
