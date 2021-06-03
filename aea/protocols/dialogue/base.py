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
import inspect
import secrets
import sys
from collections import defaultdict, namedtuple
from enum import Enum
from inspect import signature
from typing import (
    Any,
    Callable,
    Dict,
    FrozenSet,
    Iterable,
    List,
    Optional,
    Set,
    Tuple,
    Type,
    cast,
)

from aea.common import Address
from aea.exceptions import AEAEnforceError, enforce
from aea.helpers.base import cached_property
from aea.helpers.storage.generic_storage import SyncCollection
from aea.protocols.base import Message
from aea.skills.base import SkillComponent


if sys.version_info[0] < 3 or (sys.version_info[0] == 3 and sys.version_info[1] < 7):
    DialogueMessage = namedtuple(  # pragma: no cover
        "DialogueMessage",
        ["performative", "contents", "is_incoming", "target"],
        rename=False,
        module="aea.protocols.dialogues.base",
    )
    DialogueMessage.__new__.__defaults__ = (dict(), None, None)  # pragma: no cover
else:
    DialogueMessage = namedtuple(  # pylint: disable=unexpected-keyword-arg
        "DialogueMessage",
        ["performative", "contents", "is_incoming", "target"],
        rename=False,
        defaults=[dict(), None, None],
        module="aea.protocols.dialogues.base",
    )


class InvalidDialogueMessage(Exception):
    """Exception for adding invalid message to a dialogue."""


class DialogueLabel:
    """The dialogue label class acts as an identifier for dialogues."""

    __slots__ = (
        "_dialogue_reference",
        "_dialogue_opponent_addr",
        "_dialogue_starter_addr",
    )

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

    def __eq__(self, other: Any) -> bool:
        """Check for equality between two DialogueLabel objects."""
        return (
            isinstance(other, DialogueLabel)
            and self.dialogue_reference == other.dialogue_reference
            and self.dialogue_opponent_addr == other.dialogue_opponent_addr
            and self.dialogue_starter_addr == other.dialogue_starter_addr
        )

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

    def __str__(self) -> str:
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


class _DialogueMeta(type):
    """
    Metaclass for Dialogue.

    Creates class level Rules instance to share among instances
    """

    def __new__(cls, name: str, bases: Tuple[Type], dct: Dict) -> "_DialogueMeta":
        """Construct a new type."""
        # set class level `_rules`
        dialogue_cls: Type[Dialogue] = super().__new__(cls, name, bases, dct)
        dialogue_cls._rules = dialogue_cls.Rules(
            dialogue_cls.INITIAL_PERFORMATIVES,
            dialogue_cls.TERMINAL_PERFORMATIVES,
            dialogue_cls.VALID_REPLIES,
        )

        return dialogue_cls


class Dialogue(metaclass=_DialogueMeta):
    """The dialogue class maintains state of a dialogue and manages it."""

    STARTING_MESSAGE_ID = 1
    STARTING_TARGET = 0
    UNASSIGNED_DIALOGUE_REFERENCE = ""

    INITIAL_PERFORMATIVES = frozenset()  # type: FrozenSet[Message.Performative]
    TERMINAL_PERFORMATIVES = frozenset()  # type: FrozenSet[Message.Performative]
    VALID_REPLIES = (
        dict()
    )  # type: Dict[Message.Performative, FrozenSet[Message.Performative]]

    __slots__ = (
        "_self_address",
        "_dialogue_label",
        "_role",
        "_message_class",
        "_outgoing_messages",
        "_incoming_messages",
        "_terminal_state_callbacks",
        "_last_message_id",
        "_ordered_message_ids",
    )

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

        def __str__(self) -> str:
            """Get the string representation."""
            return str(self.value)

    class EndState(Enum):
        """This class defines the end states of a dialogue."""

        def __str__(self) -> str:
            """Get the string representation."""
            return str(self.value)

    _rules: Optional[Rules] = None

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
        :param message_class: the message class used
        :param self_address: the address of the entity for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for
        """
        self._self_address = self_address
        self._dialogue_label = dialogue_label
        self._role = role

        self._outgoing_messages = []  # type: List[Message]
        self._incoming_messages = []  # type: List[Message]

        enforce(
            issubclass(message_class, Message),
            "Message class provided not a subclass of `Message`.",
        )
        self._message_class = message_class
        self._terminal_state_callbacks: Set[Callable[["Dialogue"], None]] = set()
        self._last_message_id: Optional[int] = None
        self._ordered_message_ids: List[int] = []

    def add_terminal_state_callback(self, fn: Callable[["Dialogue"], None]) -> None:
        """
        Add callback to be called on dialogue reach terminal state.

        :param fn: callable to be called with one argument: Dialogue
        """
        self._terminal_state_callbacks.add(fn)

    def __eq__(self, other: Any) -> bool:
        """Compare two dialogues."""
        return (
            type(self) == type(other)  # pylint: disable=unidiomatic-typecheck
            and self.dialogue_label == other.dialogue_label
            and self.message_class == other.message_class
            and self._incoming_messages == other._incoming_messages
            and self._outgoing_messages == other._outgoing_messages
            and self._ordered_message_ids == other._ordered_message_ids
            and self.role == other.role
            and self.self_address == other.self_address
        )

    def json(self) -> dict:
        """Get json representation of the dialogue."""
        data = {
            "dialogue_label": self._dialogue_label.json,
            "self_address": self.self_address,
            "role": self._role.value,
            "incoming_messages": [i.json() for i in self._incoming_messages],
            "outgoing_messages": [i.json() for i in self._outgoing_messages],
            "last_message_id": self._last_message_id,
            "ordered_message_ids": self._ordered_message_ids,
        }
        return data

    @classmethod
    def from_json(cls, message_class: Type[Message], data: dict) -> "Dialogue":
        """
        Create a dialogue instance with all messages from json data.

        :param message_class: type of message used with this dialogue
        :param data: dict with data exported with Dialogue.to_json() method

        :return: Dialogue instance
        """
        try:
            obj = cls(
                dialogue_label=DialogueLabel.from_json(data["dialogue_label"]),
                message_class=message_class,
                self_address=Address(data["self_address"]),
                role=cls.Role(data["role"]),
            )
            obj._incoming_messages = [  # pylint: disable=protected-access
                message_class.from_json(i) for i in data["incoming_messages"]
            ]
            obj._outgoing_messages = [  # pylint: disable=protected-access
                message_class.from_json(i) for i in data["outgoing_messages"]
            ]
            last_message_id = int(data["last_message_id"])
            obj._last_message_id = last_message_id  # pylint: disable=protected-access
            obj._ordered_message_ids = [  # pylint: disable=protected-access
                int(el) for el in data["ordered_message_ids"]
            ]
            return obj
        except KeyError:  # pragma: nocover
            raise ValueError(f"Dialogue representation is invalid: {data}")

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
        return self.dialogue_label.get_incomplete_version()

    @property
    def dialogue_labels(self) -> Set[DialogueLabel]:
        """
        Get the dialogue labels (incomplete and complete, if it exists).

        :return: the dialogue labels
        """
        return {self.dialogue_label, self.incomplete_dialogue_label}

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
    def message_class(self) -> Type[Message]:
        """
        Get the message class.

        :return: the message class
        """
        return self._message_class

    @property
    def is_self_initiated(self) -> bool:
        """
        Check whether the agent initiated the dialogue.

        :return: True if the agent initiated the dialogue, False otherwise
        """
        return (
            self.dialogue_label.dialogue_opponent_addr
            is not self.dialogue_label.dialogue_starter_addr
        )

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
        if self._last_message_id is None:
            return None

        if (
            self.last_incoming_message
            and self.last_incoming_message.message_id == self._last_message_id
        ):
            return self.last_incoming_message
        return self.last_outgoing_message

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

    def _has_message_id(self, message_id: int) -> bool:
        """
        Check whether a message with the supplied message id exists in this dialogue.

        :param message_id: the message id
        :return: True if message with that id exists in this dialogue, False otherwise
        """
        return self.get_message_by_id(message_id) is not None

    def _update(self, message: Message) -> None:
        """
        Extend the list of incoming/outgoing messages with 'message', if 'message' belongs to dialogue and is valid.

        :param message: a message to be added
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
            self._outgoing_messages.append(message)
        else:
            self._incoming_messages.append(message)

        self._last_message_id = message.message_id
        self._ordered_message_ids.append(message.message_id)

        if message.performative in self.rules.terminal_performatives:
            for fn in self._terminal_state_callbacks:
                fn(self)

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
        target: Optional[int] = None,
        **kwargs: Any,
    ) -> Message:
        """
        Reply to the 'target_message' in this dialogue with a message with 'performative', and contents from kwargs.

        Note if no target_message is provided, the last message in the dialogue will be replied to.

        :param target_message: the message to reply to.
        :param target: the id of the message to reply to.
        :param performative: the performative of the reply message.
        :param kwargs: the content of the reply message.

        :return: the reply message if it was successfully added as a reply, None otherwise.
        """
        last_message = self.last_message
        if last_message is None:
            raise ValueError("Cannot reply in an empty dialogue!")

        if target_message is None and target is not None:
            target_message = self.get_message_by_id(target)
        elif target_message is None and target is None:
            target_message = last_message
            target = last_message.message_id
        elif target_message is not None and target is None:
            target = target_message.message_id
        elif target_message is not None and target is not None:
            if target != target_message.message_id:
                raise AEAEnforceError(
                    "The provided target and target_message do not match."
                )

        if target_message is None:
            raise ValueError("No target message found!")
        enforce(
            self._has_message_id(target),  # type: ignore
            "The target message does not exist in this dialogue.",
        )

        reply = self._message_class(
            dialogue_reference=self.dialogue_label.dialogue_reference,
            message_id=self.get_outgoing_next_message_id(),
            target=target,
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

        err = self._validate_message_target(message)
        if err:
            return False, err

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

        if dialogue_reference[0] != self.dialogue_label.dialogue_reference[0]:
            return (
                False,
                "Invalid dialogue_reference[0]. Expected {}. Found {}.".format(
                    self.dialogue_label.dialogue_reference[0], dialogue_reference[0]
                ),
            )

        err = self._validate_message_id(message)
        if err:
            return False, err

        err = self._validate_message_target(message)
        if err:
            return False, err

        return True, "The non-initial message passes basic validation."

    def _validate_message_target(self, message: Message) -> Optional[str]:
        """Check message target corresponds to messages in the dialogue, if not return error string."""
        target = message.target
        performative = message.performative

        if message.message_id == self.STARTING_MESSAGE_ID:
            # for initial message!
            if target == self.STARTING_TARGET:
                # no need to check in details
                return None
            return "Invalid target. Expected 0. Found {}.".format(target)

        if (
            message.message_id != self.STARTING_MESSAGE_ID
            and target == self.STARTING_TARGET
        ):
            return "Invalid target. Expected a non-zero integer. Found {}.".format(
                target
            )

        # quick target check.
        latest_ids: List[int] = []

        if self.last_incoming_message:
            latest_ids.append(abs(self.last_incoming_message.message_id))

        if self.last_outgoing_message:
            latest_ids.append(abs(self.last_outgoing_message.message_id))

        if abs(target) > max(latest_ids):
            return "Invalid target. Expected a value less than or equal to abs({}). Found abs({}).".format(
                max(latest_ids), abs(target)
            )

        # detailed target check
        target_message = self.get_message_by_id(target)

        if not target_message:
            return "Invalid target {}. target_message can not be found.".format(
                target
            )  # pragma: nocover

        target_performative = target_message.performative
        if performative not in self.rules.get_valid_replies(target_performative):
            return "Invalid performative. Expected one of {}. Found {}.".format(
                self.rules.get_valid_replies(target_performative), performative
            )

        return None

    def _validate_message_id(self, message: Message) -> Optional[str]:
        """Check message id corresponds to message id sequences, if not return error string."""
        is_outgoing = message.to != self.self_address

        # This assumes that messages sent by the opponent are sent in the right order.
        if is_outgoing:
            next_message_id = self.get_outgoing_next_message_id()
        else:
            next_message_id = self.get_incoming_next_message_id()

        # we know what is the next message id for incoming and outgoing!
        if message.message_id != next_message_id:
            return "Invalid message_id. Expected {}. Found {}.".format(
                next_message_id, message.message_id
            )

        return None

    def get_message_by_id(self, message_id: int) -> Optional[Message]:
        """Get message by id, if not presents return None."""
        if self.is_empty:
            return None

        if message_id == 0:
            raise ValueError("message_id == 0 is invalid!")  # pragma: nocover

        if bool(message_id > 0) == self.is_self_initiated:
            messages_list = self._outgoing_messages
        else:
            messages_list = self._incoming_messages

        if len(messages_list) == 0:
            return None

        if abs(message_id) > abs(messages_list[-1].message_id):
            return None

        return messages_list[abs(message_id) - 1]

    def get_outgoing_next_message_id(self) -> int:
        """Get next outgoing message id."""
        next_message_id = Dialogue.STARTING_MESSAGE_ID

        if self.last_outgoing_message:
            next_message_id = abs(self.last_outgoing_message.message_id) + 1

        if not self.is_self_initiated:
            next_message_id = 0 - next_message_id

        return next_message_id

    def get_incoming_next_message_id(self) -> int:
        """Get next incoming message id."""
        next_message_id = Dialogue.STARTING_MESSAGE_ID

        if self.last_incoming_message:
            next_message_id = abs(self.last_incoming_message.message_id) + 1

        if self.is_self_initiated:
            next_message_id = 0 - next_message_id

        return next_message_id

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

    def __str__(self) -> str:
        """
        Get the string representation.

        :return: The string representation of the dialogue
        """
        representation = f"Dialogue Label:\n{self.dialogue_label}\nMessages:\n"

        for msg_id in self._ordered_message_ids:
            msg = self.get_message_by_id(msg_id)
            if msg is None:  # pragma: nocover
                raise ValueError("Dialogue inconsistent! Missing message.")
            representation += f"message_id={msg.message_id}, target={msg.target}, performative={msg.performative}\n"
        return representation


class DialogueStats:
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
        """
        if is_self_initiated:
            enforce(end_state in self._self_initiated, "End state not present!")
            self._self_initiated[end_state] += 1
        else:
            enforce(end_state in self._other_initiated, "End state not present!")
            self._other_initiated[end_state] += 1


def find_caller_object(object_type: Type) -> Any:
    """Find caller object of certain type in the call stack."""
    caller_object = None
    for frame_info in inspect.stack():
        frame_self = frame_info.frame.f_locals.get("self", None)
        if not frame_self:
            continue

        if not isinstance(frame_self, object_type):
            continue
        caller_object = frame_self
    return caller_object


class BasicDialoguesStorage:
    """Dialogues state storage."""

    def __init__(self, dialogues: "Dialogues") -> None:
        """Init dialogues storage."""
        self._dialogues_by_dialogue_label = {}  # type: Dict[DialogueLabel, Dialogue]
        self._dialogue_by_address = defaultdict(
            list
        )  # type: Dict[Address, List[Dialogue]]
        self._incomplete_to_complete_dialogue_labels = (
            {}
        )  # type: Dict[DialogueLabel, DialogueLabel]
        self._dialogues = dialogues
        self._terminal_state_dialogues_labels: Set[DialogueLabel] = set()

    @property
    def dialogues_in_terminal_state(self) -> List["Dialogue"]:
        """Get all dialogues in terminal state."""
        return list(
            filter(
                None,
                [
                    self._dialogues_by_dialogue_label.get(i)
                    for i in self._terminal_state_dialogues_labels
                ],
            )
        )

    @property
    def dialogues_in_active_state(self) -> List["Dialogue"]:
        """Get all dialogues in active state."""
        active_dialogues = (
            set(self._dialogues_by_dialogue_label.keys())
            - self._terminal_state_dialogues_labels
        )
        return list(
            filter(
                None,
                [self._dialogues_by_dialogue_label.get(i) for i in active_dialogues],
            )
        )

    @property
    def is_terminal_dialogues_kept(self) -> bool:
        """Return True if dialogues should stay after terminal state."""
        return self._dialogues.is_keep_dialogues_in_terminal_state

    def dialogue_terminal_state_callback(self, dialogue: "Dialogue") -> None:
        """Method to be called on dialogue terminal state reached."""
        if self.is_terminal_dialogues_kept:
            self._terminal_state_dialogues_labels.add(dialogue.dialogue_label)
        else:
            self.remove(dialogue.dialogue_label)

    def setup(self) -> None:
        """Set up dialogue storage."""

    def teardown(self) -> None:
        """Tear down dialogue storage."""

    def add(self, dialogue: Dialogue) -> None:
        """
        Add dialogue to storage.

        :param dialogue: dialogue to add.
        """
        dialogue.add_terminal_state_callback(self.dialogue_terminal_state_callback)
        self._dialogues_by_dialogue_label[dialogue.dialogue_label] = dialogue
        self._dialogue_by_address[
            dialogue.dialogue_label.dialogue_opponent_addr
        ].append(dialogue)

    def _add_terminal_state_dialogue(self, dialogue: Dialogue) -> None:
        """
        Add terminal state dialogue to storage.

        :param dialogue: dialogue to add.
        """
        self.add(dialogue)
        self._terminal_state_dialogues_labels.add(dialogue.dialogue_label)

    def remove(self, dialogue_label: DialogueLabel) -> None:
        """
        Remove dialogue from storage by it's label.

        :param dialogue_label: label of the dialogue to remove
        """
        dialogue = self._dialogues_by_dialogue_label.pop(dialogue_label, None)

        self._incomplete_to_complete_dialogue_labels.pop(dialogue_label, None)

        if dialogue_label in self._terminal_state_dialogues_labels:
            self._terminal_state_dialogues_labels.remove(dialogue_label)

        if dialogue:
            self._dialogue_by_address[dialogue_label.dialogue_opponent_addr].remove(
                dialogue
            )

    def get(self, dialogue_label: DialogueLabel) -> Optional[Dialogue]:
        """
        Get dialogue stored by it's label.

        :param dialogue_label: label of the dialogue
        :return: dialogue if presents or None
        """
        return self._dialogues_by_dialogue_label.get(dialogue_label, None)

    def get_dialogues_with_counterparty(self, counterparty: Address) -> List[Dialogue]:
        """
        Get the dialogues by address.

        :param counterparty: the counterparty
        :return: The dialogues with the counterparty.
        """
        return self._dialogue_by_address.get(counterparty, [])

    def is_in_incomplete(self, dialogue_label: DialogueLabel) -> bool:
        """Check dialogue label presents in list of incomplete."""
        return dialogue_label in self._incomplete_to_complete_dialogue_labels

    def set_incomplete_dialogue(
        self,
        incomplete_dialogue_label: DialogueLabel,
        complete_dialogue_label: DialogueLabel,
    ) -> None:
        """Set incomplete dialogue label."""
        self._incomplete_to_complete_dialogue_labels[
            incomplete_dialogue_label
        ] = complete_dialogue_label

    def is_dialogue_present(self, dialogue_label: DialogueLabel) -> bool:
        """Check dialogue with label specified presents in storage."""
        return dialogue_label in self._dialogues_by_dialogue_label

    def get_latest_label(self, dialogue_label: DialogueLabel) -> DialogueLabel:
        """Get latest label for dialogue."""
        return self._incomplete_to_complete_dialogue_labels.get(
            dialogue_label, dialogue_label
        )


class PersistDialoguesStorage(BasicDialoguesStorage):
    """
    Persist dialogues storage.

    Uses generic storage to load/save dialogues data on setup/teardown.
    """

    INCOMPLETE_DIALOGUES_OBJECT_NAME = "incomplete_dialogues"
    TERMINAL_STATE_DIALOGUES_COLLECTTION_SUFFIX = "_terminal"

    def __init__(self, dialogues: "Dialogues") -> None:
        """Init dialogues storage."""
        super().__init__(dialogues)

        self._skill_component: Optional[SkillComponent] = self.get_skill_component()

    @staticmethod
    def get_skill_component() -> Optional[SkillComponent]:
        """Get skill component dialogues storage constructed for."""
        caller_object = find_caller_object(SkillComponent)
        if not caller_object:  # pragma: nocover
            return None
        return caller_object

    def _get_collection_name(self) -> Optional[str]:
        """Generate collection name based on the dialogues class name and skill component."""
        if not self._skill_component:  # pragma: nocover
            return None
        return "_".join(
            [
                self._skill_component.skill_id.author,
                self._skill_component.skill_id.name,
                self._skill_component.name,
                self._skill_component.__class__.__name__,
                self._dialogues.__class__.__name__,
            ]
        )

    def _get_collection_instance(self, col_name: str) -> Optional[SyncCollection]:
        """Get sync collection if generic storage available."""
        if (
            not self._skill_component or not self._skill_component.context.storage
        ):  # pragma: nocover
            return None
        return self._skill_component.context.storage.get_sync_collection(col_name)

    @cached_property
    def _terminal_dialogues_collection(self) -> Optional[SyncCollection]:
        col_name = self._get_collection_name()
        if not col_name:
            return None
        col_name = f"{col_name}{self.TERMINAL_STATE_DIALOGUES_COLLECTTION_SUFFIX}"
        return self._get_collection_instance(col_name)

    @cached_property
    def _active_dialogues_collection(self) -> Optional[SyncCollection]:
        col_name = self._get_collection_name()
        if not col_name:
            return None
        return self._get_collection_instance(col_name)

    def _dump(self) -> None:
        """Dump dialogues storage to the generic storage."""
        if (
            not self._active_dialogues_collection
            or not self._terminal_dialogues_collection
        ):
            return  # pragma: nocover

        self._dump_incomplete_dialogues_labels(self._active_dialogues_collection)
        self._dump_dialogues(
            self.dialogues_in_active_state, self._active_dialogues_collection
        )
        self._dump_dialogues(
            self.dialogues_in_terminal_state, self._terminal_dialogues_collection
        )

    def _dump_incomplete_dialogues_labels(self, collection: SyncCollection) -> None:
        """Dump incomplete labels."""
        collection.put(
            self.INCOMPLETE_DIALOGUES_OBJECT_NAME,
            self._incomplete_dialogues_labels_to_json(),
        )

    def _load_incomplete_dialogues_labels(self, collection: SyncCollection) -> None:
        """Load and set incomplete dialogue labels."""
        incomplete_dialogues_data = collection.get(
            self.INCOMPLETE_DIALOGUES_OBJECT_NAME
        )
        if incomplete_dialogues_data is not None:
            incomplete_dialogues_data = cast(List, incomplete_dialogues_data)
            self._set_incomplete_dialogues_labels_from_json(incomplete_dialogues_data)

    def _load_dialogues(self, collection: SyncCollection) -> Iterable[Dialogue]:
        """Load dialogues from collection."""
        if not collection:  # pragma: nocover
            return
        for label, dialogue_data in collection.list():
            if label == self.INCOMPLETE_DIALOGUES_OBJECT_NAME:
                continue
            dialogue_data = cast(Dict, dialogue_data)
            yield self._dialogue_from_json(dialogue_data)

    def _dialogue_from_json(self, dialogue_data: dict) -> "Dialogue":
        return self._dialogues.dialogue_class.from_json(
            self._dialogues.message_class, dialogue_data
        )

    @staticmethod
    def _dump_dialogues(
        dialogues: Iterable[Dialogue], collection: SyncCollection
    ) -> None:
        """Dump dialogues to collection."""
        for dialogue in dialogues:
            collection.put(str(dialogue.dialogue_label), dialogue.json())

    def _load(self) -> None:
        """Dump dialogues and incomplete dialogues labels from the generic storage."""
        if (
            not self._active_dialogues_collection
            or not self._terminal_dialogues_collection
        ):
            return  # pragma: nocover

        self._load_incomplete_dialogues_labels(self._active_dialogues_collection)
        self._load_active_dialogues()
        self._load_terminated_dialogues()

    def _load_active_dialogues(self) -> None:
        """Load active dialogues from storage."""
        for dialogue in self._load_dialogues(self._active_dialogues_collection):
            self.add(dialogue)

    def _load_terminated_dialogues(self) -> None:
        """Load terminated dialogues from storage."""
        for dialogue in self._load_dialogues(self._terminal_dialogues_collection):
            self._add_terminal_state_dialogue(dialogue)

    def _incomplete_dialogues_labels_to_json(self) -> List:
        """Dump incomplete_to_complete_dialogue_labels to json friendly dict."""
        return [
            [k.json, v.json]
            for k, v in self._incomplete_to_complete_dialogue_labels.items()
        ]

    def _set_incomplete_dialogues_labels_from_json(self, data: List) -> None:
        """Set incomplete_to_complete_dialogue_labels from json friendly dict."""
        self._incomplete_to_complete_dialogue_labels = {
            DialogueLabel.from_json(k): DialogueLabel.from_json(v) for k, v in data
        }

    def setup(self) -> None:
        """Set up dialogue storage."""
        if not self._skill_component:  # pragma: nocover
            return
        self._load()

    def teardown(self) -> None:
        """Tear down dialogue storage."""
        if not self._skill_component:  # pragma: nocover
            return
        self._dump()

    def remove(self, dialogue_label: DialogueLabel) -> None:
        """Remove dialogue from memory and persistent storage."""
        if dialogue_label in self._terminal_state_dialogues_labels:
            collection = self._terminal_dialogues_collection
        else:
            collection = self._active_dialogues_collection

        super().remove(dialogue_label)

        if collection:
            collection.remove(str(dialogue_label))


class PersistDialoguesStorageWithOffloading(PersistDialoguesStorage):
    """Dialogue Storage with dialogues offloading."""

    def dialogue_terminal_state_callback(self, dialogue: "Dialogue") -> None:
        """Call on dialogue reaches terminal state."""
        if (
            not self.is_terminal_dialogues_kept
            or not self._terminal_dialogues_collection
        ):  # pragma: nocover
            super().dialogue_terminal_state_callback(dialogue)
            return

        # do offloading
        # push to storage
        self._terminal_dialogues_collection.put(
            str(dialogue.dialogue_label), dialogue.json()
        )
        # remove from memory
        self.remove(dialogue.dialogue_label)

    def get(self, dialogue_label: DialogueLabel) -> Optional[Dialogue]:
        """Try to get dialogue by label from memory or persists storage."""
        dialogue = super().get(dialogue_label)
        if dialogue:
            return dialogue

        dialogue = self._get_dialogue_from_collection(
            dialogue_label, self._terminal_dialogues_collection
        )
        if dialogue:
            # get dialogue from terminal state collection and cache it
            self._add_terminal_state_dialogue(dialogue)
            return dialogue
        return None

    def _get_dialogue_from_collection(
        self, dialogue_label: "DialogueLabel", collection: SyncCollection
    ) -> Optional[Dialogue]:
        """
        Get dialogue by label from collection.

        :param dialogue_label: label for lookup
        :param collection: collection with dialogues
        :return: dialogue if exists
        """
        if not collection:
            return None
        dialogue_data = collection.get(str(dialogue_label))
        if not dialogue_data:
            return None
        dialogue_data = cast(Dict, dialogue_data)
        return self._dialogue_from_json(dialogue_data)

    def _load_terminated_dialogues(self) -> None:
        """Skip terminated dialogues loading, cause it's offloaded."""

    def _get_dialogues_by_address_from_collection(
        self, address: Address, collection: SyncCollection
    ) -> List["Dialogue"]:
        """
        Get all dialogues with opponent address from specified collection.

        :param address: address for lookup.
        :param: collection: collection to get dialogues from.

        :return: list of dialogues
        """
        if not collection:
            return []

        return [
            self._dialogue_from_json(cast(Dict, i[1]))
            for i in collection.find("dialogue_label.dialogue_opponent_addr", address)
        ]

    def get_dialogues_with_counterparty(self, counterparty: Address) -> List[Dialogue]:
        """
        Get the dialogues by address.

        :param counterparty: the counterparty
        :return: The dialogues with the counterparty.
        """
        dialogues = (
            self._get_dialogues_by_address_from_collection(
                counterparty, self._active_dialogues_collection
            )
            + self._get_dialogues_by_address_from_collection(
                counterparty, self._terminal_dialogues_collection
            )
            + super().get_dialogues_with_counterparty(counterparty)
        )
        return self._unique_dialogues_by_label(dialogues)

    @staticmethod
    def _unique_dialogues_by_label(dialogues: List[Dialogue]) -> List[Dialogue]:
        """Filter list of dialogues by unique dialogue label."""
        return list(
            {dialogue.dialogue_label: dialogue for dialogue in dialogues}.values()
        )

    @property
    def dialogues_in_terminal_state(self) -> List["Dialogue"]:
        """Get all dialogues in terminal state."""
        dialogues = super().dialogues_in_terminal_state + list(
            self._load_dialogues(self._terminal_dialogues_collection)
        )
        return self._unique_dialogues_by_label(dialogues)


class Dialogues:
    """The dialogues class keeps track of all dialogues for an agent."""

    _keep_terminal_state_dialogues = False

    def __init__(
        self,
        self_address: Address,
        end_states: FrozenSet[Dialogue.EndState],
        message_class: Type[Message],
        dialogue_class: Type[Dialogue],
        role_from_first_message: Callable[[Message, Address], Dialogue.Role],
        keep_terminal_state_dialogues: Optional[bool] = None,
    ) -> None:
        """
        Initialize dialogues.

        :param self_address: the address of the entity for whom dialogues are maintained
        :param end_states: the list of dialogue endstates
        :param message_class: the message class used
        :param dialogue_class: the dialogue class used
        :param role_from_first_message: the callable determining role from first message
        :param keep_terminal_state_dialogues: specify do dialogues in terminal state should stay or not
        """

        self._dialogues_storage = PersistDialoguesStorageWithOffloading(self)
        self._self_address = self_address
        self._dialogue_stats = DialogueStats(end_states)

        if keep_terminal_state_dialogues is not None:
            self._keep_terminal_state_dialogues = keep_terminal_state_dialogues

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
    def is_keep_dialogues_in_terminal_state(self) -> bool:
        """Is required to keep dialogues in terminal state."""
        return self._keep_terminal_state_dialogues

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

    @property
    def message_class(self) -> Type[Message]:
        """
        Get the message class.

        :return: the message class
        """
        return self._message_class

    @property
    def dialogue_class(self) -> Type[Dialogue]:
        """
        Get the dialogue class.

        :return: the dialogue class
        """
        return self._dialogue_class

    def get_dialogues_with_counterparty(self, counterparty: Address) -> List[Dialogue]:
        """
        Get the dialogues by address.

        :param counterparty: the counterparty
        :return: The dialogues with the counterparty.
        """
        return self._dialogues_storage.get_dialogues_with_counterparty(counterparty)

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

    @classmethod
    def new_self_initiated_dialogue_reference(cls) -> Tuple[str, str]:
        """
        Return a dialogue label for a new self initiated dialogue.

        :return: the next nonce
        """
        return cls._generate_dialogue_nonce(), Dialogue.UNASSIGNED_DIALOGUE_REFERENCE

    def create(
        self, counterparty: Address, performative: Message.Performative, **kwargs: Any,
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
            self._dialogues_storage.remove(dialogue.dialogue_label)
            raise ValueError(
                f"Cannot create a dialogue with the specified performative and contents. {e}"
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
        enforce(
            message.to == self.self_address,
            f"Message to and dialogue self address do not match. Got 'to={message.to}' expected 'to={self.self_address}'.",
        )

        dialogue_reference = message.dialogue_reference

        is_invalid_label = (
            dialogue_reference[0] == Dialogue.UNASSIGNED_DIALOGUE_REFERENCE
            and dialogue_reference[1] == Dialogue.UNASSIGNED_DIALOGUE_REFERENCE
        )
        is_new_dialogue = (
            dialogue_reference[0] != Dialogue.UNASSIGNED_DIALOGUE_REFERENCE
            and dialogue_reference[1] == Dialogue.UNASSIGNED_DIALOGUE_REFERENCE
            and message.message_id == Dialogue.STARTING_MESSAGE_ID
        )
        is_incomplete_label_and_non_initial_msg = (
            dialogue_reference[0] != Dialogue.UNASSIGNED_DIALOGUE_REFERENCE
            and dialogue_reference[1] == Dialogue.UNASSIGNED_DIALOGUE_REFERENCE
            and message.message_id
            not in (Dialogue.STARTING_MESSAGE_ID, Dialogue.STARTING_TARGET)
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
                    self._dialogues_storage.remove(dialogue.dialogue_label)
        else:
            # couldn't find the dialogue referenced by the message
            result = None
        return result

    def _complete_dialogue_reference(self, message: Message) -> None:
        """
        Update a self initiated dialogue label with a complete dialogue reference from counterparty's first message.

        :param message: A message in the dialogue (the first by the counterparty with a complete reference)
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

        if self._dialogues_storage.is_dialogue_present(
            incomplete_dialogue_label
        ) and not self._dialogues_storage.is_in_incomplete(incomplete_dialogue_label):
            dialogue = self._dialogues_storage.get(incomplete_dialogue_label)
            if not dialogue:  # pragma: nocover
                raise ValueError("no dialogue found")
            self._dialogues_storage.remove(incomplete_dialogue_label)
            final_dialogue_label = DialogueLabel(
                complete_dialogue_reference,
                incomplete_dialogue_label.dialogue_opponent_addr,
                incomplete_dialogue_label.dialogue_starter_addr,
            )
            dialogue._update_dialogue_label(  # pylint: disable=protected-access
                final_dialogue_label
            )
            self._dialogues_storage.add(dialogue)
            self._dialogues_storage.set_incomplete_dialogue(
                incomplete_dialogue_label, final_dialogue_label
            )

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

        self_initiated_dialogue = self.get_dialogue_from_label(
            self_initiated_dialogue_label
        )
        other_initiated_dialogue = self.get_dialogue_from_label(
            other_initiated_dialogue_label
        )

        result = self_initiated_dialogue or other_initiated_dialogue
        return result

    def _get_latest_label(self, dialogue_label: DialogueLabel) -> DialogueLabel:
        """
        Retrieve the latest dialogue label if present otherwise return same label.

        :param dialogue_label: the dialogue label
        :return: the dialogue label
        """
        return self._dialogues_storage.get_latest_label(dialogue_label)

    def get_dialogue_from_label(
        self, dialogue_label: DialogueLabel
    ) -> Optional[Dialogue]:
        """
        Retrieve a dialogue based on its label.

        :param dialogue_label: the dialogue label
        :return: the dialogue if present
        """
        return self._dialogues_storage.get(dialogue_label)

    def _create_self_initiated(
        self,
        dialogue_opponent_addr: Address,
        dialogue_reference: Tuple[str, str],
        role: Dialogue.Role,
    ) -> Dialogue:
        """
        Create a self initiated dialogue.

        :param dialogue_opponent_addr: the address of the agent with which the dialogue is kept.
        :param dialogue_reference: the reference of the dialogue
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
            not self._dialogues_storage.is_in_incomplete(incomplete_dialogue_label),
            "Incomplete dialogue label already present.",
        )
        if complete_dialogue_label is None:
            dialogue_label = incomplete_dialogue_label
        else:
            self._dialogues_storage.set_incomplete_dialogue(
                incomplete_dialogue_label, complete_dialogue_label
            )
            dialogue_label = complete_dialogue_label
        enforce(
            not self._dialogues_storage.is_dialogue_present(dialogue_label),
            "Dialogue label already present in dialogues.",
        )
        dialogue = self._dialogue_class(
            dialogue_label=dialogue_label,
            message_class=self._message_class,
            self_address=self.self_address,
            role=role,
        )
        self._dialogues_storage.add(dialogue)
        return dialogue

    @staticmethod
    def _generate_dialogue_nonce() -> str:
        """
        Generate the nonce and return it.

        :return: the next nonce
        """
        return secrets.token_hex(DialogueLabel.NONCE_BYTES_NB)

    def setup(self) -> None:
        """Set  up."""
        self._dialogues_storage.setup()
        super_obj = super()
        if hasattr(super_obj, "setup"):  # pragma: nocover
            super_obj.setup()  # type: ignore  # pylint: disable=no-member

    def teardown(self) -> None:
        """Tear down."""
        self._dialogues_storage.teardown()
        super_obj = super()
        if hasattr(super_obj, "teardown"):  # pragma: nocover
            super_obj.teardown()  # type: ignore  # pylint: disable=no-member
