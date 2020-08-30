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
import secrets
from abc import ABC
from enum import Enum
from inspect import signature
from typing import Callable, Dict, FrozenSet, List, Optional, Set, Tuple, Type, cast

from aea.common import Address
from aea.exceptions import enforce
from aea.protocols.base import Message


class InvalidDialogueMessage(Exception):
    """Exception for adding invalid message to a dialogue."""


class DialogueLabel:
    """The dialogue label class acts as an identifier for dialogues."""

    NONCE_BYTES_NB = 32

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
        if isinstance(other, DialogueLabel):
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

    def get_incomplete_version(self) -> "DialogueLabel":
        """Get the incomplete version of the label."""
        dialogue_label = DialogueLabel(
            (self.dialogue_starter_reference, Dialogue.UNASSIGNED_DIALOGUE_REFERENCE),
            self.dialogue_opponent_addr,
            self.dialogue_starter_addr,
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

    @classmethod
    def from_str(cls, obj: str) -> "DialogueLabel":
        """Get the dialogue label from string representation."""
        (
            dialogue_starter_reference,
            dialogue_responder_reference,
            dialogue_opponent_addr,
            dialogue_starter_addr,
        ) = obj.split("_")
        dialogue_label = DialogueLabel(
            (dialogue_starter_reference, dialogue_responder_reference),
            dialogue_opponent_addr,
            dialogue_starter_addr,
        )
        return dialogue_label


class Dialogue(ABC):
    """The dialogue class maintains state of a dialogue and manages it."""

    STARTING_MESSAGE_ID = 1
    STARTING_TARGET = 0
    UNASSIGNED_DIALOGUE_REFERENCE = ""

    INITIAL_PERFORMATIVES = frozenset()  # type: FrozenSet[Message.Performative]
    TERMINAL_PERFORMATIVES = frozenset()  # type: FrozenSet[Message.Performative]
    VALID_REPLIES = (
        dict()
    )  # type: Dict[Message.Performative, FrozenSet[Message.Performative]]

    class Rules:
        """This class defines the rules for the dialogue."""

        def __init__(
            self,
            initial_performatives: FrozenSet[Message.Performative],
            terminal_performatives: FrozenSet[Message.Performative],
            valid_replies: Dict[Message.Performative, FrozenSet[Message.Performative]],
        ) -> None:
            """
            Initialize a dialogue.

            :param initial_performatives: the set of all initial performatives.
            :param terminal_performatives: the set of all terminal performatives.
            :param valid_replies: the reply structure of speech-acts.

            :return: None
            """
            self._initial_performatives = initial_performatives
            self._terminal_performatives = terminal_performatives
            self._valid_replies = valid_replies

        @property
        def initial_performatives(self) -> FrozenSet[Message.Performative]:
            """
            Get the performatives one of which the terminal message in the dialogue must have.

            :return: the valid performatives of an terminal message
            """
            return self._initial_performatives

        @property
        def terminal_performatives(self) -> FrozenSet[Message.Performative]:
            """
            Get the performatives one of which the terminal message in the dialogue must have.

            :return: the valid performatives of an terminal message
            """
            return self._terminal_performatives

        @property
        def valid_replies(
            self,
        ) -> Dict[Message.Performative, FrozenSet[Message.Performative]]:
            """
            Get all the valid performatives which are a valid replies to performatives.

            :return: the full valid reply structure.
            """
            return self._valid_replies

        def get_valid_replies(
            self, performative: Message.Performative
        ) -> FrozenSet[Message.Performative]:
            """
            Given a `performative`, return the list of performatives which are its valid replies in a dialogue.

            :param performative: the performative in a message
            :return: list of valid performative replies
            """
            enforce(
                performative in self.valid_replies,
                "this performative '{}' is not supported".format(performative),
            )
            return self.valid_replies[performative]

    class Role(Enum):
        """This class defines the agent's role in a dialogue."""

        def __str__(self):
            """Get the string representation."""
            return str(self.value)

    class EndState(Enum):
        """This class defines the end states of a dialogue."""

        def __str__(self):
            """Get the string representation."""
            return str(self.value)

    def __init__(
        self,
        dialogue_label: DialogueLabel,
        message_class: Type[Message],
        self_address: Address,
        role: Role,
    ) -> None:
        """
        Initialize a dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param self_address: the address of the entity for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for

        :return: None
        """
        self._self_address = self_address
        self._incomplete_dialogue_label = dialogue_label.get_incomplete_version()
        self._dialogue_label = dialogue_label
        self._role = role
        self._rules = self.Rules(
            self.INITIAL_PERFORMATIVES, self.TERMINAL_PERFORMATIVES, self.VALID_REPLIES
        )

        self._is_self_initiated = (
            dialogue_label.dialogue_opponent_addr
            is not dialogue_label.dialogue_starter_addr
        )

        self._outgoing_messages = []  # type: List[Message]
        self._incoming_messages = []  # type: List[Message]

        enforce(
            issubclass(message_class, Message),
            "Message class provided not a subclass of `Message`.",
        )
        self._message_class = message_class

    @property
    def dialogue_label(self) -> DialogueLabel:
        """
        Get the dialogue label.

        :return: The dialogue label
        """
        return self._dialogue_label

    @property
    def incomplete_dialogue_label(self) -> DialogueLabel:
        """
        Get the dialogue label.

        :return: The incomplete dialogue label
        """
        return self._incomplete_dialogue_label

    @property
    def dialogue_labels(self) -> Set[DialogueLabel]:
        """
        Get the dialogue labels (incomplete and complete, if it exists)

        :return: the dialogue labels
        """
        return {self._dialogue_label, self._incomplete_dialogue_label}

    @property
    def self_address(self) -> Address:
        """
        Get the address of the entity for whom this dialogues is maintained.

        :return: the address of this entity
        """
        if self._self_address is None:  # pragma: nocover
            raise ValueError("self_address is not set.")
        return self._self_address

    @property
    def role(self) -> "Role":
        """
        Get the agent's role in the dialogue.

        :return: the agent's role
        """
        if self._role is None:  # pragma: nocover
            raise ValueError("Role is not set.")
        return self._role

    @property
    def rules(self) -> "Rules":
        """
        Get the dialogue rules.

        :return: the rules
        """
        if self._rules is None:  # pragma: nocover
            raise ValueError("Rules is not set.")
        return self._rules

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

    @property
    def is_empty(self) -> bool:
        """
        Check whether the dialogue is empty.

        :return: True if empty, False otherwise
        """
        return len(self._outgoing_messages) == 0 and len(self._incoming_messages) == 0

    def _counterparty_from_message(self, message: Message) -> Address:
        """
        Determine the counterparty of the agent in the dialogue from a message.

        :param message: the message
        :return: The address of the counterparty
        """
        counterparty = (
            message.to if self._is_message_by_self(message) else message.sender
        )
        return counterparty

    def _is_message_by_self(self, message: Message) -> bool:
        """
        Check whether the message is by this agent or not.

        :param message: the message
        :return: True if message is by this agent, False otherwise
        """
        return message.sender == self.self_address

    def _is_message_by_other(self, message: Message) -> bool:
        """
        Check whether the message is by the counterparty agent in this dialogue or not.

        :param message: the message
        :return: True if message is by the counterparty agent in this dialogue, False otherwise
        """
        return not self._is_message_by_self(message)

    def _try_get_message(self, message_id: int) -> Optional[Message]:
        """
        Try to get the message whose id is 'message_id'.

        :param message_id: the id of the message
        :return: the message if it exists, None otherwise
        """
        result = None  # type: Optional[Message]
        list_of_all_messages = self._outgoing_messages + self._incoming_messages
        for message in list_of_all_messages:
            if message.message_id == message_id:
                result = message
                break
        return result

    def _get_message(self, message_id: int) -> Message:
        """
        Get the message whose id is 'message_id'.

        :param message_id: the id of the message
        :return: the message
        :raises: AssertionError if message is not present
        """
        message = self._try_get_message(message_id)
        if message is None:
            raise ValueError("Message not present.")
        return message

    def _has_message(self, message: Message) -> bool:
        """
        Check whether a message exists in this dialogue.

        :param message: the message
        :return: True if message exists in this dialogue, False otherwise
        """
        if self.is_empty:
            return False

        if not self._has_message_id(message.message_id):
            return False

        retrieved_message = self._get_message(message.message_id)
        return message == retrieved_message

    def _has_message_id(self, message_id: int) -> bool:
        """
        Check whether a message with the supplied message id exists in this dialogue.

        :param message_id: the message id
        :return: True if message with that id exists in this dialogue, False otherwise
        """
        if self.is_empty:
            return False

        return self.STARTING_MESSAGE_ID <= message_id <= self.last_message.message_id  # type: ignore

    def _update(self, message: Message) -> None:
        """
        Extend the list of incoming/outgoing messages with 'message', if 'message' belongs to dialogue and is valid.

        :param message: a message to be added
        :return: None
        :raises: InvalidDialogueMessage: if message does not belong to this dialogue, or if message is invalid
        """
        if not message.has_sender:
            message.sender = self.self_address  # pragma: nocover

        if not self._is_belonging_to_dialogue(message):
            raise InvalidDialogueMessage(
                "The message {} does not belong to this dialogue."
                "The dialogue reference of the message is {}, while the dialogue reference of the dialogue is {}".format(
                    message.message_id,
                    message.dialogue_reference,
                    self.dialogue_label.dialogue_reference,
                )
            )

        is_valid_result, validation_message = self._validate_next_message(message)

        if not is_valid_result:
            raise InvalidDialogueMessage(
                "Message {} is invalid with respect to this dialogue. Error: {}".format(
                    message.message_id, validation_message,
                )
            )

        if self._is_message_by_self(message):
            self._outgoing_messages.extend([message])
        else:
            self._incoming_messages.extend([message])

    def _is_belonging_to_dialogue(self, message: Message) -> bool:
        """
        Check if the message is belonging to the dialogue.

        :param message: the message
        :return: True if message is part of the dialogue, False otherwise
        """
        opponent = self._counterparty_from_message(message)
        if self.is_self_initiated:
            self_initiated_dialogue_label = DialogueLabel(
                (
                    message.dialogue_reference[0],
                    Dialogue.UNASSIGNED_DIALOGUE_REFERENCE,
                ),
                opponent,
                self.self_address,
            )
            result = self_initiated_dialogue_label in self.dialogue_labels
        else:
            other_initiated_dialogue_label = DialogueLabel(
                message.dialogue_reference, opponent, opponent,
            )
            result = other_initiated_dialogue_label in self.dialogue_labels
        return result

    def reply(
        self,
        performative: Message.Performative,
        target_message: Optional[Message] = None,
        **kwargs,
    ) -> Message:
        """
        Reply to the 'target_message' in this dialogue with a message with 'performative', and contents from kwargs.

        Note if no target_message is provided, the last message in the dialogue will be replied to.

        :param target_message: the message to reply to.
        :param performative: the performative of the reply message.
        :param kwargs: the content of the reply message.

        :return: the reply message if it was successfully added as a reply, None otherwise.
        """
        last_message = self.last_message
        if last_message is None:
            raise ValueError("Cannot reply in an empty dialogue!")

        if target_message is None:
            target_message = last_message
        else:
            enforce(
                self._has_message(
                    target_message  # type: ignore
                ),
                "The target message does not exist in this dialogue.",
            )

        reply = self._message_class(
            dialogue_reference=self.dialogue_label.dialogue_reference,
            message_id=last_message.message_id + 1,
            target=target_message.message_id,
            performative=performative,
            **kwargs,
        )
        reply.sender = self.self_address
        reply.to = self.dialogue_label.dialogue_opponent_addr

        self._update(reply)

        return reply

    def _validate_next_message(self, message: Message) -> Tuple[bool, str]:
        """
        Check whether 'message' is a valid next message in this dialogue.

        The evaluation of a message validity involves performing several categories of checks.
        Each category of checks resides in a separate method.

        Currently, basic rules are general fundamental structural constraints,
        additional rules are applied for the time being, and more specific rules to each dialogue are captured in the is_valid method.

        :param message: the message to be validated
        :return: Boolean result, and associated message.
        """
        is_basic_validated, msg_basic_validation = self._basic_validation(message)
        if not is_basic_validated:
            return False, msg_basic_validation

        (
            result_additional_validation,
            msg_additional_validation,
        ) = self._additional_validation(message)
        if not result_additional_validation:
            return False, msg_additional_validation

        result_is_valid, msg_is_valid = self._custom_validation(message)
        if not result_is_valid:
            return False, msg_is_valid

        return True, "Message is valid with respect to this dialogue."

    def _basic_validation(self, message: Message) -> Tuple[bool, str]:
        """
        Check whether 'message' is a valid next message in the dialogue, according to basic rules.

        This method redirects the checks to two other methods based on whether the message
        is the first in the dialogue or not.

        :param message: the message to be validated
        :return: Boolean result, and associated message.
        """
        if self.is_empty:  # initial message
            return self._basic_validation_initial_message(message)

        return self._basic_validation_non_initial_message(message)

    def _basic_validation_initial_message(self, message: Message) -> Tuple[bool, str]:
        """
        Check whether an initial 'message' is a valid next message in the dialogue, according to basic rules.

        These rules are designed to be fundamental to all dialogues, and enforce the following:

         - message ids are consistent
         - targets are consistent
         - message targets are according to the reply structure of performatives

        :param message: the message to be validated
        :return: Boolean result, and associated message.
        """
        dialogue_reference = message.dialogue_reference
        message_id = message.message_id
        target = message.target
        performative = message.performative

        if dialogue_reference[0] != self.dialogue_label.dialogue_reference[0]:
            return (
                False,
                "Invalid dialogue_reference[0]. Expected {}. Found {}.".format(
                    self.dialogue_label.dialogue_reference[0], dialogue_reference[0]
                ),
            )

        if message_id != Dialogue.STARTING_MESSAGE_ID:
            return (
                False,
                "Invalid message_id. Expected {}. Found {}.".format(
                    Dialogue.STARTING_MESSAGE_ID, message_id
                ),
            )

        if target != Dialogue.STARTING_TARGET:
            return (
                False,
                "Invalid target. Expected {}. Found {}.".format(
                    Dialogue.STARTING_TARGET, target
                ),
            )

        if performative not in self.rules.initial_performatives:
            return (
                False,
                "Invalid initial performative. Expected one of {}. Found {}.".format(
                    self.rules.initial_performatives, performative
                ),
            )

        return True, "The initial message passes basic validation."

    def _basic_validation_non_initial_message(
        self, message: Message
    ) -> Tuple[bool, str]:
        """
        Check whether a non-initial 'message' is a valid next message in the dialogue, according to basic rules.

        These rules are designed to be fundamental to all dialogues, and enforce the following:

         - message ids are consistent
         - targets are consistent
         - message targets are according to the reply structure of performatives

        :param message: the message to be validated
        :return: Boolean result, and associated message.
        """
        dialogue_reference = message.dialogue_reference
        message_id = message.message_id
        target = message.target
        performative = message.performative

        if dialogue_reference[0] != self.dialogue_label.dialogue_reference[0]:
            return (
                False,
                "Invalid dialogue_reference[0]. Expected {}. Found {}.".format(
                    self.dialogue_label.dialogue_reference[0], dialogue_reference[0]
                ),
            )

        last_message_id = self.last_message.message_id  # type: ignore
        if message_id != last_message_id + 1:
            return (
                False,
                "Invalid message_id. Expected {}. Found {}.".format(
                    last_message_id + 1, message_id
                ),
            )
        if target < 1:
            return (
                False,
                "Invalid target. Expected a value greater than or equal to 1. Found {}.".format(
                    target
                ),
            )
        if last_message_id < target:
            return (
                False,
                "Invalid target. Expected a value less than or equal to {}. Found {}.".format(
                    last_message_id, target
                ),
            )

        target_message = self._get_message(target)
        target_performative = target_message.performative
        if performative not in self.rules.get_valid_replies(target_performative):
            return (
                False,
                "Invalid performative. Expected one of {}. Found {}.".format(
                    self.rules.get_valid_replies(target_performative), performative
                ),
            )

        return True, "The non-initial message passes basic validation."

    def _additional_validation(self, message: Message) -> Tuple[bool, str]:
        """
        Check whether 'message' is a valid next message in the dialogue, according to additional rules.

        These rules are designed to be less fundamental than basic rules and subject to change.
        Currently the following is enforced:

         - A message targets the message strictly before it in the dialogue

        :param message: the message to be validated
        :return: Boolean result, and associated message.
        """
        if self.is_empty:
            return True, "The message passes additional validation."

        last_target = self.last_message.target  # type: ignore
        if message.target == last_target + 1:
            return True, "The message passes additional validation."

        return (
            False,
            "Invalid target. Expected {}. Found {}.".format(
                last_target + 1, message.target
            ),
        )

    def _update_dialogue_label(self, final_dialogue_label: DialogueLabel) -> None:
        """
        Update the dialogue label of the dialogue.

        :param final_dialogue_label: the final dialogue label
        """
        enforce(
            self.dialogue_label.dialogue_reference[1]
            == self.UNASSIGNED_DIALOGUE_REFERENCE
            and final_dialogue_label.dialogue_reference[1]
            != self.UNASSIGNED_DIALOGUE_REFERENCE,
            "Dialogue label cannot be updated.",
        )
        self._dialogue_label = final_dialogue_label

    def _custom_validation(  # pylint: disable=no-self-use,unused-argument
        self, message: Message
    ) -> Tuple[bool, str]:
        """
        Check whether 'message' is a valid next message in the dialogue.

        These rules capture specific constraints designed for dialogues which are instance of a concrete sub-class of this class.

        :param message: the message to be validated
        :return: True if valid, False otherwise.
        """
        return True, "The message passes custom validation."

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


class DialogueStats(ABC):
    """Class to handle statistics on default dialogues."""

    def __init__(self, end_states: FrozenSet[Dialogue.EndState]) -> None:
        """
        Initialize a StatsManager.

        :param end_states: the list of dialogue endstates
        """
        self._self_initiated = {
            e: 0 for e in end_states
        }  # type: Dict[Dialogue.EndState, int]
        self._other_initiated = {
            e: 0 for e in end_states
        }  # type: Dict[Dialogue.EndState, int]

    @property
    def self_initiated(self) -> Dict[Dialogue.EndState, int]:
        """Get the stats dictionary on self initiated dialogues."""
        return self._self_initiated

    @property
    def other_initiated(self) -> Dict[Dialogue.EndState, int]:
        """Get the stats dictionary on other initiated dialogues."""
        return self._other_initiated

    def add_dialogue_endstate(
        self, end_state: Dialogue.EndState, is_self_initiated: bool
    ) -> None:
        """
        Add dialogue endstate stats.

        :param end_state: the end state of the dialogue
        :param is_self_initiated: whether the dialogue is initiated by the agent or the opponent

        :return: None
        """
        if is_self_initiated:
            enforce(end_state in self._self_initiated, "End state not present!")
            self._self_initiated[end_state] += 1
        else:
            enforce(end_state in self._other_initiated, "End state not present!")
            self._other_initiated[end_state] += 1


class Dialogues(ABC):
    """The dialogues class keeps track of all dialogues for an agent."""

    def __init__(
        self,
        self_address: Address,
        end_states: FrozenSet[Dialogue.EndState],
        message_class: Type[Message],
        dialogue_class: Type[Dialogue],
        role_from_first_message: Callable[[Message, Address], Dialogue.Role],
    ) -> None:
        """
        Initialize dialogues.

        :param self_address: the address of the entity for whom dialogues are maintained
        :param end_states: the list of dialogue endstates
        :return: None
        """
        self._dialogues_by_dialogue_label = {}  # type: Dict[DialogueLabel, Dialogue]
        self._dialogue_by_address = {}  # type: Dict[Address, List[Dialogue]]
        self._incomplete_to_complete_dialogue_labels = (
            {}
        )  # type: Dict[DialogueLabel, DialogueLabel]
        self._self_address = self_address
        self._dialogue_stats = DialogueStats(end_states)

        enforce(
            issubclass(message_class, Message),
            "message_class is not a subclass of Message.",
        )
        self._message_class = message_class

        enforce(
            issubclass(dialogue_class, Dialogue),
            "dialogue_class is not a subclass of Dialogue.",
        )
        self._dialogue_class = dialogue_class

        # Note the following might be too restrictive; if the supplied role_from_first_message function
        # does not have the type hinting for its parameter or its return value, the second and third checks
        # below would fail.
        sig = signature(role_from_first_message)
        parameter_length = len(sig.parameters.keys())
        enforce(
            parameter_length == 2,
            "Invalid number of parameters for role_from_first_message. Expected 2. Found {}.".format(
                parameter_length
            ),
        )
        parameter_1_type = list(sig.parameters.values())[0].annotation
        enforce(
            parameter_1_type == Message,
            "Invalid type for the first parameter of role_from_first_message. Expected 'Message'. Found {}.".format(
                parameter_1_type
            ),
        )
        parameter_2_type = list(sig.parameters.values())[1].annotation
        enforce(
            parameter_2_type == Address,
            "Invalid type for the second parameter of role_from_first_message. Expected 'Address'. Found {}.".format(
                parameter_2_type
            ),
        )
        return_type = sig.return_annotation
        enforce(
            return_type == Dialogue.Role,
            "Invalid return type for role_from_first_message. Expected 'Dialogue.Role'. Found {}.".format(
                return_type
            ),
        )
        self._role_from_first_message = role_from_first_message

    @property
    def dialogues(self) -> Dict[DialogueLabel, Dialogue]:
        """Get dictionary of dialogues in which the agent engages."""
        return self._dialogues_by_dialogue_label

    @property
    def self_address(self) -> Address:
        """Get the address of the agent for whom dialogues are maintained."""
        enforce(self._self_address != "", "self_address is not set.")
        return self._self_address

    @property
    def dialogue_stats(self) -> DialogueStats:
        """
        Get the dialogue statistics.

        :return: dialogue stats object
        """
        return self._dialogue_stats

    def get_dialogues_with_counterparty(self, counterparty: Address) -> List[Dialogue]:
        """
        Get the dialogues by address.

        :param counterparty: the counterparty
        :return: The dialogues with the counterparty.
        """
        return self._dialogue_by_address.get(counterparty, [])

    def _is_message_by_self(self, message: Message) -> bool:
        """
        Check whether the message is by this agent or not.

        :param message: the message
        :return: True if message is by this agent, False otherwise
        """
        return message.sender == self.self_address

    def _is_message_by_other(self, message: Message) -> bool:
        """
        Check whether the message is by the counterparty agent in this dialogue or not.

        :param message: the message
        :return: True if message is by the counterparty agent in this dialogue, False otherwise
        """
        return not self._is_message_by_self(message)

    def _counterparty_from_message(self, message: Message) -> Address:
        """
        Determine the counterparty of the agent in the dialogue from a message.

        :param message: the message
        :return: The address of the counterparty
        """
        counterparty = (
            message.to if self._is_message_by_self(message) else message.sender
        )
        return counterparty

    def new_self_initiated_dialogue_reference(self) -> Tuple[str, str]:
        """
        Return a dialogue label for a new self initiated dialogue.

        :return: the next nonce
        """
        return self._generate_dialogue_nonce(), Dialogue.UNASSIGNED_DIALOGUE_REFERENCE

    def create(
        self, counterparty: Address, performative: Message.Performative, **kwargs,
    ) -> Tuple[Message, Dialogue]:
        """
        Create a dialogue with 'counterparty', with an initial message whose performative is 'performative' and contents are from 'kwargs'.

        :param counterparty: the counterparty of the dialogue.
        :param performative: the performative of the initial message.
        :param kwargs: the content of the initial message.

        :return: the initial message and the dialogue.
        """
        initial_message = self._message_class(
            dialogue_reference=self.new_self_initiated_dialogue_reference(),
            message_id=Dialogue.STARTING_MESSAGE_ID,
            target=Dialogue.STARTING_TARGET,
            performative=performative,
            **kwargs,
        )
        initial_message.sender = self.self_address
        initial_message.to = counterparty

        dialogue = self._create_dialogue(counterparty, initial_message)

        return initial_message, dialogue

    def create_with_message(
        self, counterparty: Address, initial_message: Message
    ) -> Dialogue:
        """
        Create a dialogue with 'counterparty', with an initial message provided.

        :param counterparty: the counterparty of the dialogue.
        :param initial_message: the initial_message.

        :return: the initial message and the dialogue.
        """
        enforce(
            not initial_message.has_sender,
            "The message's 'sender' field is already set {}".format(initial_message),
        )
        enforce(
            not initial_message.has_to,
            "The message's 'to' field is already set {}".format(initial_message),
        )
        initial_message.sender = self.self_address
        initial_message.to = counterparty

        dialogue = self._create_dialogue(counterparty, initial_message)

        return dialogue

    def _create_dialogue(
        self, counterparty: Address, initial_message: Message
    ) -> Dialogue:
        """
        Create a dialogue from an initial message provided.

        :param counterparty: the counterparty of the dialogue.
        :param initial_message: the initial_message.

        :return: the dialogue.
        """
        dialogue = self._create_self_initiated(
            dialogue_opponent_addr=counterparty,
            dialogue_reference=initial_message.dialogue_reference,
            role=self._role_from_first_message(initial_message, self.self_address),
        )

        try:
            dialogue._update(initial_message)  # pylint: disable=protected-access
        except InvalidDialogueMessage as e:
            self._dialogues_by_dialogue_label.pop(dialogue.dialogue_label)
            raise SyntaxError(
                "Cannot create a dialogue with the specified performative and contents."
            ) from e
        return dialogue

    def update(self, message: Message) -> Optional[Dialogue]:
        """
        Update the state of dialogues with a new incoming message.

        If the message is for a new dialogue, a new dialogue is created with 'message' as its first message, and returned.
        If the message is addressed to an existing dialogue, the dialogue is retrieved, extended with this message and returned.
        If there are any errors, e.g. the message dialogue reference does not exists or the message is invalid w.r.t. the dialogue, return None.

        :param message: a new incoming message
        :return: the new or existing dialogue the message is intended for, or None in case of any errors.
        """
        enforce(
            message.has_sender and self._is_message_by_other(message),
            "Invalid 'update' usage. Update must only be used with a message by another agent.",
        )
        enforce(
            message.has_to, "The message's 'to' field is not set {}".format(message)
        )

        dialogue_reference = message.dialogue_reference

        is_invalid_label = (
            dialogue_reference[0] == Dialogue.UNASSIGNED_DIALOGUE_REFERENCE
            and dialogue_reference[1] == Dialogue.UNASSIGNED_DIALOGUE_REFERENCE
        )
        is_new_dialogue = (
            dialogue_reference[0] != Dialogue.UNASSIGNED_DIALOGUE_REFERENCE
            and dialogue_reference[1] == Dialogue.UNASSIGNED_DIALOGUE_REFERENCE
            and message.message_id == 1
        )
        is_incomplete_label_and_non_initial_msg = (
            dialogue_reference[0] != Dialogue.UNASSIGNED_DIALOGUE_REFERENCE
            and dialogue_reference[1] == Dialogue.UNASSIGNED_DIALOGUE_REFERENCE
            and message.message_id > 1
        )

        if is_invalid_label:
            dialogue = None  # type: Optional[Dialogue]
        elif is_new_dialogue:  # initial message for new dialogue
            dialogue = self._create_opponent_initiated(
                dialogue_opponent_addr=message.sender,
                dialogue_reference=dialogue_reference,
                role=self._role_from_first_message(message, self.self_address),
            )
        elif is_incomplete_label_and_non_initial_msg:
            # we can allow a dialogue to have incomplete reference
            # as multiple messages can be sent before one is received with complete reference
            dialogue = self.get_dialogue(message)
        else:  # non-initial message for existing dialogue
            self._complete_dialogue_reference(message)
            dialogue = self.get_dialogue(message)

        if dialogue is not None:
            try:
                dialogue._update(message)  # pylint: disable=protected-access
                result = dialogue  # type: Optional[Dialogue]
            except InvalidDialogueMessage:
                # invalid message for the dialogue found
                result = None
                if (
                    is_new_dialogue
                ):  # remove the newly created dialogue if the initial message is invalid
                    self._dialogues_by_dialogue_label.pop(dialogue.dialogue_label)
        else:
            # couldn't find the dialogue referenced by the message
            result = None

        return result

    def _complete_dialogue_reference(self, message: Message) -> None:
        """
        Update a self initiated dialogue label with a complete dialogue reference from counterparty's first message.

        :param message: A message in the dialogue (the first by the counterparty with a complete reference)
        :return: None
        """
        complete_dialogue_reference = message.dialogue_reference
        enforce(
            complete_dialogue_reference[0] != Dialogue.UNASSIGNED_DIALOGUE_REFERENCE
            and complete_dialogue_reference[1]
            != Dialogue.UNASSIGNED_DIALOGUE_REFERENCE,
            "Only complete dialogue references allowed.",
        )

        incomplete_dialogue_reference = (
            complete_dialogue_reference[0],
            Dialogue.UNASSIGNED_DIALOGUE_REFERENCE,
        )
        incomplete_dialogue_label = DialogueLabel(
            incomplete_dialogue_reference, message.sender, self.self_address,
        )

        if (
            incomplete_dialogue_label in self.dialogues
            and incomplete_dialogue_label
            not in self._incomplete_to_complete_dialogue_labels
        ):
            dialogue = self.dialogues.pop(incomplete_dialogue_label)
            final_dialogue_label = DialogueLabel(
                complete_dialogue_reference,
                incomplete_dialogue_label.dialogue_opponent_addr,
                incomplete_dialogue_label.dialogue_starter_addr,
            )
            dialogue._update_dialogue_label(  # pylint: disable=protected-access
                final_dialogue_label
            )
            self.dialogues.update({dialogue.dialogue_label: dialogue})
            self._incomplete_to_complete_dialogue_labels[
                incomplete_dialogue_label
            ] = final_dialogue_label

    def get_dialogue(self, message: Message) -> Optional[Dialogue]:
        """
        Retrieve the dialogue 'message' belongs to.

        :param message: a message
        :return: the dialogue, or None in case such a dialogue does not exist
        """
        self_initiated_dialogue_label = DialogueLabel(
            message.dialogue_reference,
            self._counterparty_from_message(message),
            self.self_address,
        )
        other_initiated_dialogue_label = DialogueLabel(
            message.dialogue_reference,
            self._counterparty_from_message(message),
            self._counterparty_from_message(message),
        )

        self_initiated_dialogue_label = self._get_latest_label(
            self_initiated_dialogue_label
        )
        other_initiated_dialogue_label = self._get_latest_label(
            other_initiated_dialogue_label
        )

        self_initiated_dialogue = self._get_dialogue_from_label(
            self_initiated_dialogue_label
        )
        other_initiated_dialogue = self._get_dialogue_from_label(
            other_initiated_dialogue_label
        )

        result = self_initiated_dialogue or other_initiated_dialogue
        return result

    def _get_latest_label(self, dialogue_label: DialogueLabel) -> DialogueLabel:
        """
        Retrieve the latest dialogue label if present otherwise return same label.

        :param dialogue_label: the dialogue label
        :return dialogue_label: the dialogue label
        """
        result = self._incomplete_to_complete_dialogue_labels.get(
            dialogue_label, dialogue_label
        )
        return result

    def _get_dialogue_from_label(
        self, dialogue_label: DialogueLabel
    ) -> Optional[Dialogue]:
        """
        Retrieve a dialogue based on its label.

        :param dialogue_label: the dialogue label
        :return: the dialogue if present
        """
        result = self.dialogues.get(dialogue_label, None)
        return result

    def _create_self_initiated(
        self,
        dialogue_opponent_addr: Address,
        dialogue_reference: Tuple[str, str],
        role: Dialogue.Role,
    ) -> Dialogue:
        """
        Create a self initiated dialogue.

        :param dialogue_opponent_addr: the pbk of the agent with which the dialogue is kept.
        :param role: the agent's role

        :return: the created dialogue.
        """
        enforce(
            dialogue_reference[0] != Dialogue.UNASSIGNED_DIALOGUE_REFERENCE
            and dialogue_reference[1] == Dialogue.UNASSIGNED_DIALOGUE_REFERENCE,
            "Cannot initiate dialogue with preassigned dialogue_responder_reference!",
        )
        incomplete_dialogue_label = DialogueLabel(
            dialogue_reference, dialogue_opponent_addr, self.self_address
        )
        dialogue = self._create(incomplete_dialogue_label, role)
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
        enforce(
            dialogue_reference[0] != Dialogue.UNASSIGNED_DIALOGUE_REFERENCE
            and dialogue_reference[1] == Dialogue.UNASSIGNED_DIALOGUE_REFERENCE,
            "Cannot initiate dialogue with preassigned dialogue_responder_reference!",
        )
        incomplete_dialogue_label = DialogueLabel(
            dialogue_reference, dialogue_opponent_addr, dialogue_opponent_addr
        )
        new_dialogue_reference = (
            dialogue_reference[0],
            self._generate_dialogue_nonce(),
        )
        complete_dialogue_label = DialogueLabel(
            new_dialogue_reference, dialogue_opponent_addr, dialogue_opponent_addr
        )
        dialogue = self._create(
            incomplete_dialogue_label, role, complete_dialogue_label
        )
        return dialogue

    def _create(
        self,
        incomplete_dialogue_label: DialogueLabel,
        role: Dialogue.Role,
        complete_dialogue_label: Optional[DialogueLabel] = None,
    ) -> Dialogue:
        """
        Create a dialogue from label and role.

        :param incomplete_dialogue_label: the dialogue label (incomplete)
        :param role: the agent's role
        :param complete_dialogue_label: the dialogue label (complete)

        :return: the created dialogue
        """
        enforce(
            incomplete_dialogue_label
            not in self._incomplete_to_complete_dialogue_labels,
            "Incomplete dialogue label already present.",
        )
        if complete_dialogue_label is None:
            dialogue_label = incomplete_dialogue_label
        else:
            self._incomplete_to_complete_dialogue_labels[
                incomplete_dialogue_label
            ] = complete_dialogue_label
            dialogue_label = complete_dialogue_label
        enforce(
            dialogue_label not in self.dialogues,
            "Dialogue label already present in dialogues.",
        )
        dialogue = self._dialogue_class(
            dialogue_label=dialogue_label,
            message_class=self._message_class,
            self_address=self.self_address,
            role=role,
        )
        self.dialogues.update({dialogue_label: dialogue})
        if (
            self._dialogue_by_address.get(dialogue_label.dialogue_opponent_addr, None)
            is None
        ):
            self._dialogue_by_address[dialogue_label.dialogue_opponent_addr] = []
        self._dialogue_by_address[dialogue_label.dialogue_opponent_addr].append(
            dialogue
        )
        return dialogue

    @staticmethod
    def _generate_dialogue_nonce() -> str:
        """
        Generate the nonce and return it.

        :return: the next nonce
        """
        return secrets.token_hex(DialogueLabel.NONCE_BYTES_NB)
