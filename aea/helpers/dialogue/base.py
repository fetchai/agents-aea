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
from typing import Callable, Dict, FrozenSet, List, Optional, Tuple, Type, cast

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
    OPPONENT_STARTER_REFERENCE = ""

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
            assert (
                performative in self.valid_replies
            ), "this performative '{}' is not supported".format(performative)
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
        message_class: Optional[Type[Message]] = None,
        agent_address: Optional[Address] = None,
        role: Optional[Role] = None,
        rules: Optional[Rules] = None,
    ) -> None:
        """
        Initialize a dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param agent_address: the address of the agent for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for
        :param rules: the rules of the dialogue

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
        self._rules = rules

        if message_class is not None:
            assert issubclass(message_class, Message)
        self._message_class = message_class

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
    def rules(self) -> "Rules":
        """
        Get the dialogue rules.

        :return: the rules
        """
        assert self._rules is not None, "Rules is not set."
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
        Check whether the dialogue is empty.

        :return: True if empty, False otherwise
        """
        return len(self._outgoing_messages) == 0 and len(self._incoming_messages) == 0

    def update(self, message: Message) -> bool:
        """
        Extend the list of incoming/outgoing messages with 'message', if 'message' is valid.

        :param message: a message to be added
        :return: True if message successfully added, false otherwise
        """
        if (
            message.is_incoming
            and self.last_message is not None
            and self.last_message.message_id == self.STARTING_MESSAGE_ID
            and self.dialogue_label.dialogue_reference[1]
            == self.OPPONENT_STARTER_REFERENCE
        ):
            self._update_self_initiated_dialogue_label_on_second_message(message)

        counterparty = None  # type: Optional[str]
        try:
            counterparty = message.counterparty
        except AssertionError:
            message.counterparty = self.dialogue_label.dialogue_opponent_addr

        if counterparty is not None:
            assert (
                message.counterparty == self.dialogue_label.dialogue_opponent_addr
            ), "The counterparty specified in the message is different from the opponent in this dialogue."

        is_extendable = self.is_valid_next_message(message)
        if is_extendable:
            if message.is_incoming:
                self._incoming_messages.extend([message])
            else:
                self._outgoing_messages.extend([message])
        return is_extendable

    def reply(self, target_message: Message, performative, **kwargs) -> Message:
        """
        Reply to the 'target_message' in this dialogue with a message with 'performative', and contents from kwargs.

        :param target_message: the message to reply to.
        :param performative: the performative of the reply message.
        :param kwargs: the content of the reply message.

        :return: the reply message if it was successfully added as a reply, None otherwise.
        """
        assert (
            self._message_class is not None
        ), "No 'message_class' argument was provided to this class on construction."
        assert self.last_message is not None, "Cannot reply in an empty dialogue!"

        reply = self._message_class(
            dialogue_reference=self.dialogue_label.dialogue_reference,
            message_id=self.last_message.message_id + 1,
            target=target_message.message_id,
            performative=performative,
            **kwargs,
        )
        reply.counterparty = self.dialogue_label.dialogue_opponent_addr
        result = self.update(reply)

        if result:
            return reply
        else:
            raise Exception("Invalid message from performative and contents.")

    def _update_self_initiated_dialogue_label_on_second_message(
        self, second_message: Message
    ) -> None:
        """
        Update this (self initiated) dialogue's dialogue_label with a complete dialogue reference from counterparty's first message.

        :param second_message: The second message in the dialogue (the first by the counterparty)
        :return: None
        """
        dialogue_reference = second_message.dialogue_reference

        self_initiated_dialogue_reference = (
            dialogue_reference[0],
            self.OPPONENT_STARTER_REFERENCE,
        )
        self_initiated_dialogue_label = DialogueLabel(
            self_initiated_dialogue_reference,
            second_message.counterparty,
            self.agent_address,
        )

        if self.last_message is not None:
            if (
                self.dialogue_label == self_initiated_dialogue_label
                and self.last_message.message_id == 1
                and second_message.message_id == 2
                and second_message.is_incoming
            ):
                updated_dialogue_label = DialogueLabel(
                    dialogue_reference,
                    self_initiated_dialogue_label.dialogue_opponent_addr,
                    self_initiated_dialogue_label.dialogue_starter_addr,
                )
                self.update_dialogue_label(updated_dialogue_label)
            else:
                raise Exception(
                    "Invalid call to update dialogue's reference. This call must be made only after receiving dialogue's second message by the counterparty."
                )
        else:
            raise Exception(
                "Cannot update dialogue's reference after the first message."
            )

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
        dialogue_reference = message.dialogue_reference
        message_id = message.message_id
        target = message.target
        performative = message.performative

        if self.last_message is None:
            result = (
                dialogue_reference[0] == self.dialogue_label.dialogue_reference[0]
                and message_id == Dialogue.STARTING_MESSAGE_ID
                and target == Dialogue.STARTING_TARGET
                and performative in self.rules.initial_performatives
            )
        else:
            last_message_id = self.last_message.message_id
            target_message = self.get_message(target)
            if target_message is not None:
                target_performative = target_message.performative
                result = (
                    dialogue_reference[0] == self.dialogue_label.dialogue_reference[0]
                    and message_id == last_message_id + 1
                    and 1 <= target <= last_message_id
                    and performative
                    in self.rules.get_valid_replies(target_performative)
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
        if self.last_message is None:
            result = True
        else:
            target = message.target
            last_target = self.last_message.target
            result = target == last_target + 1
        return result

    def update_dialogue_label(self, final_dialogue_label: DialogueLabel) -> None:
        """
        Update the dialogue label of the dialogue.

        :param final_dialogue_label: the final dialogue label
        """
        assert (
            self.dialogue_label.dialogue_reference[1] == self.OPPONENT_STARTER_REFERENCE
            and final_dialogue_label.dialogue_reference[1]
            != self.OPPONENT_STARTER_REFERENCE
        ), "Dialogue label cannot be updated."
        self._dialogue_label = final_dialogue_label

    @abstractmethod
    def is_valid(self, message: Message) -> bool:
        """
        Check whether 'message' is a valid next message in the dialogue.

        These rules capture specific constraints designed for dialogues which are instance of a concrete sub-class of this class.

        :param message: the message to be validated
        :return: True if valid, False otherwise.
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
            assert end_state in self._self_initiated, "End state not present!"
            self._self_initiated[end_state] += 1
        else:
            assert end_state in self._other_initiated, "End state not present!"
            self._other_initiated[end_state] += 1


class Dialogues(ABC):
    """The dialogues class keeps track of all dialogues for an agent."""

    def __init__(
        self,
        agent_address: Address,
        end_states: FrozenSet[Dialogue.EndState],
        message_class: Optional[Type[Message]] = None,
        dialogue_class: Optional[Type[Dialogue]] = None,
        role_from_first_message: Optional[Callable[[Message], Dialogue.Role]] = None,
    ) -> None:
        """
        Initialize dialogues.

        :param agent_address: the address of the agent for whom dialogues are maintained
        :param end_states: the list of dialogue endstates
        :return: None
        """
        self._dialogues = {}  # type: Dict[DialogueLabel, Dialogue]
        self._agent_address = agent_address
        self._dialogue_nonce = 0
        self._dialogue_stats = DialogueStats(end_states)

        if message_class is not None:
            assert issubclass(message_class, Message)
        self._message_class = message_class

        if dialogue_class is not None:
            assert issubclass(dialogue_class, Dialogue)
        self._dialogue_class = dialogue_class

        if role_from_first_message is not None:
            self._role_from_first_message = role_from_first_message
        else:
            self._role_from_first_message = (
                self.role_from_first_message
            )  # pragma: no cover

    @property
    def dialogues(self) -> Dict[DialogueLabel, Dialogue]:
        """Get dictionary of dialogues in which the agent engages."""
        return self._dialogues

    @property
    def agent_address(self) -> Address:
        """Get the address of the agent for whom dialogues are maintained."""
        assert self._agent_address != "", "agent_address is not set."
        return self._agent_address

    @property
    def dialogue_stats(self) -> DialogueStats:
        """
        Get the dialogue statistics.

        :return: dialogue stats object
        """
        return self._dialogue_stats

    def new_self_initiated_dialogue_reference(self) -> Tuple[str, str]:
        """
        Return a dialogue label for a new self initiated dialogue.

        :return: the next nonce
        """
        return str(self._dialogue_nonce + 1), Dialogue.OPPONENT_STARTER_REFERENCE

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
        assert (
            self._message_class is not None
        ), "No 'message_class' argument was provided to this class on construction."

        initial_message = self._message_class(
            dialogue_reference=self.new_self_initiated_dialogue_reference(),
            message_id=Dialogue.STARTING_MESSAGE_ID,
            target=Dialogue.STARTING_TARGET,
            performative=performative,
            **kwargs,
        )
        initial_message.counterparty = counterparty

        dialogue = self._create_self_initiated(
            dialogue_opponent_addr=counterparty,
            role=self._role_from_first_message(initial_message),
        )

        successfully_updated = dialogue.update(initial_message)

        if not successfully_updated:
            self._dialogues.pop(dialogue.dialogue_label)
            self._dialogue_nonce -= 1
            raise Exception(
                "Cannot create the a dialogue with the specified performative and contents."
            )

        return initial_message, dialogue

    def update(self, message: Message) -> Optional[Dialogue]:
        """
        Update the state of dialogues with a new incoming message.

        If the message is for a new dialogue, a new dialogue is created with 'message' as its first message, and returned.
        If the message is addressed to an existing dialogue, the dialogue is retrieved, extended with this message and returned.
        If there are any errors, e.g. the message dialogue reference does not exists or the message is invalid w.r.t. the dialogue, return None.

        :param message: a new message
        :return: the new or existing dialogue the message is intended for, or None in case of any errors.
        """
        dialogue_reference = message.dialogue_reference

        if (  # new dialogue by other
            dialogue_reference[0] != Dialogue.OPPONENT_STARTER_REFERENCE
            and dialogue_reference[1] == Dialogue.OPPONENT_STARTER_REFERENCE
            and message.is_incoming
        ):
            dialogue = self._create_opponent_initiated(
                dialogue_opponent_addr=message.counterparty,
                dialogue_reference=dialogue_reference,
                role=self._role_from_first_message(message),
            )  # type: Optional[Dialogue]
        elif (  # new dialogue by self
            dialogue_reference[0] != Dialogue.OPPONENT_STARTER_REFERENCE
            and dialogue_reference[1] == Dialogue.OPPONENT_STARTER_REFERENCE
            and not message.is_incoming
        ):
            assert (
                message.counterparty is not None
            ), "The message counter-party field is not set {}".format(message)
            dialogue = self._create_self_initiated(
                dialogue_opponent_addr=message.counterparty,
                role=self._role_from_first_message(message),
            )
        else:  # existing dialogue
            self._update_self_initiated_dialogue_label_on_second_message(message)
            dialogue = self.get_dialogue(message)

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
        Update a self initiated dialogue label with a complete dialogue reference from counterparty's first message.

        :param second_message: The second message in the dialogue (the first by the counterparty in a self initiated dialogue)
        :return: None
        """
        dialogue_reference = second_message.dialogue_reference
        self_initiated_dialogue_reference = (
            dialogue_reference[0],
            Dialogue.OPPONENT_STARTER_REFERENCE,
        )
        self_initiated_dialogue_label = DialogueLabel(
            self_initiated_dialogue_reference,
            second_message.counterparty,
            self.agent_address,
        )

        if self_initiated_dialogue_label in self.dialogues:
            self_initiated_dialogue = self.dialogues.pop(self_initiated_dialogue_label)
            final_dialogue_label = DialogueLabel(
                dialogue_reference,
                self_initiated_dialogue_label.dialogue_opponent_addr,
                self_initiated_dialogue_label.dialogue_starter_addr,
            )
            self_initiated_dialogue.update_dialogue_label(final_dialogue_label)
            assert (
                self_initiated_dialogue.dialogue_label not in self.dialogues
            ), "DialogueLabel already present."
            self.dialogues.update(
                {self_initiated_dialogue.dialogue_label: self_initiated_dialogue}
            )

    def get_dialogue(self, message: Message) -> Optional[Dialogue]:
        """
        Retrieve the dialogue 'message' belongs to.

        :param message: a message
        :return: the dialogue, or None in case such a dialogue does not exist
        """
        dialogue_reference = message.dialogue_reference
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

    def get_dialogue_from_label(
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
        self, dialogue_opponent_addr: Address, role: Dialogue.Role,
    ) -> Dialogue:
        """
        Create a self initiated dialogue.

        :param dialogue_opponent_addr: the pbk of the agent with which the dialogue is kept.
        :param role: the agent's role

        :return: the created dialogue.
        """
        dialogue_reference = (
            str(self._next_dialogue_nonce()),
            Dialogue.OPPONENT_STARTER_REFERENCE,
        )
        dialogue_label = DialogueLabel(
            dialogue_reference, dialogue_opponent_addr, self.agent_address
        )
        if self._message_class is not None and self._dialogue_class is not None:
            dialogue = self._dialogue_class(
                dialogue_label=dialogue_label,
                message_class=self._message_class,
                agent_address=self.agent_address,
                role=role,
            )
        else:
            dialogue = self.create_dialogue(
                dialogue_label=dialogue_label, role=role,
            )  # pragma: no cover
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
            dialogue_reference[0] != Dialogue.OPPONENT_STARTER_REFERENCE
            and dialogue_reference[1] == Dialogue.OPPONENT_STARTER_REFERENCE
        ), "Cannot initiate dialogue with preassigned dialogue_responder_reference!"
        new_dialogue_reference = (
            dialogue_reference[0],
            str(self._next_dialogue_nonce()),
        )
        dialogue_label = DialogueLabel(
            new_dialogue_reference, dialogue_opponent_addr, dialogue_opponent_addr
        )

        assert dialogue_label not in self.dialogues
        if self._message_class is not None and self._dialogue_class is not None:
            dialogue = self._dialogue_class(
                dialogue_label=dialogue_label,
                message_class=self._message_class,
                agent_address=self.agent_address,
                role=role,
            )
        else:
            dialogue = self.create_dialogue(
                dialogue_label=dialogue_label, role=role,
            )  # pragma: no cover
        self.dialogues.update({dialogue_label: dialogue})

        return dialogue

    @abstractmethod
    def create_dialogue(
        self, dialogue_label: DialogueLabel, role: Dialogue.Role,
    ) -> Dialogue:
        """
        THIS METHOD IS DEPRECATED AND WILL BE REMOVED IN THE NEXT VERSION. USE THE NEW CONSTRUCTOR ARGUMENTS INSTEAD.

        Create a dialogue instance.

        :param dialogue_label: the identifier of the dialogue
        :param role: the role of the agent this dialogue is maintained for

        :return: the created dialogue
        """

    @staticmethod
    def role_from_first_message(message: Message) -> Dialogue.Role:
        """
        Infer the role of the agent from an incoming or outgoing first message.

        :param message: an incoming/outgoing first message
        :return: the agent's role
        """
        pass  # pragma: no cover

    def _next_dialogue_nonce(self) -> int:
        """
        Increment the nonce and return it.

        :return: the next nonce
        """
        self._dialogue_nonce += 1
        return self._dialogue_nonce
