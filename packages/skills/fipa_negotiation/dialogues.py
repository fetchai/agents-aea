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

from enum import Enum
import logging
from typing import Any, Dict, List, Optional

from aea.helpers.dialogue.base import DialogueLabel
from aea.helpers.dialogue.base import Dialogue as BaseDialogue
from aea.helpers.dialogue.base import Dialogues as BaseDialogues
from aea.mail.base import Address
from aea.protocols.base.message import Message
from aea.protocols.fipa.message import FIPAMessage

Action = Any
logger = logging.getLogger(__name__)

STARTING_MESSAGE_ID = 1
STARTING_MESSAGE_TARGET = 0
PROPOSE_TARGET = STARTING_MESSAGE_ID
ACCEPT_TARGET = PROPOSE_TARGET + 1
MATCH_ACCEPT_TARGET = ACCEPT_TARGET + 1
DECLINED_CFP_TARGET = STARTING_MESSAGE_ID
DECLINED_PROPOSE_TARGET = PROPOSE_TARGET + 1
DECLINED_ACCEPT_TARGET = ACCEPT_TARGET + 1


class Dialogue(BaseDialogue):
    """The dialogue class maintains state of a dialogue and manages it."""

    class EndState(Enum):
        """This class defines the end states of a dialogue."""

        SUCCESSFUL = 0
        DECLINED_CFP = 1
        DECLINED_PROPOSE = 2
        DECLINED_ACCEPT = 3

    def __init__(self, dialogue_label: DialogueLabel, is_seller: bool) -> None:
        """
        Initialize a dialogue label.

        :param dialogue_label: the identifier of the dialogue
        :param is_seller: indicates whether the agent associated with the dialogue is a seller or buyer

        :return: None
        """
        BaseDialogue.__init__(self, dialogue_label=dialogue_label)
        self._is_seller = is_seller
        self._role = 'seller' if is_seller else 'buyer'
        self._outgoing_messages = []  # type: List[Message]
        self._outgoing_messages_controller = []  # type: List[Message]
        self._incoming_messages = []  # type: List[Message]

    @property
    def dialogue_label(self) -> DialogueLabel:
        """Get the dialogue lable."""
        return self._dialogue_label

    @property
    def is_seller(self) -> bool:
        """Check whether the agent acts as the seller in this dialogue."""
        return self._is_seller

    @property
    def role(self) -> str:
        """Get role of agent in dialogue."""
        return self._role

    def outgoing_extend(self, messages: List[Message]) -> None:
        """
        Extend the list of messages which keeps track of outgoing messages.

        :param messages: a list of messages to be added
        :return: None
        """
        self._outgoing_messages.extend(messages)

    def incoming_extend(self, messages: List[Message]) -> None:
        """
        Extend the list of messages which keeps track of incoming messages.

        :param messages: a list of messages to be added
        :return: None
        """
        self._incoming_messages.extend(messages)

    def is_expecting_propose(self) -> bool:
        """
        Check whether the dialogue is expecting a propose.

        :return: True if yes, False otherwise.
        """
        last_sent_message = self._outgoing_messages[-1] if len(self._outgoing_messages) > 0 else None  # type: Optional[Message]
        result = (last_sent_message is not None) and last_sent_message.get("performative") == FIPAMessage.Performative.CFP
        return result

    def is_expecting_initial_accept(self) -> bool:
        """
        Check whether the dialogue is expecting an initial accept.

        :return: True if yes, False otherwise.
        """
        last_sent_message = self._outgoing_messages[-1] if len(self._outgoing_messages) > 0 else None  # type: Optional[Message]
        result = (last_sent_message is not None) and last_sent_message.get("performative") == FIPAMessage.Performative.PROPOSE
        return result

    def is_expecting_matching_accept(self) -> bool:
        """
        Check whether the dialogue is expecting a matching accept.

        :return: True if yes, False otherwise.
        """
        last_sent_message = self._outgoing_messages[-1] if len(self._outgoing_messages) > 0 else None  # type: Optional[Message]
        result = (last_sent_message is not None) and last_sent_message.get("performative") == FIPAMessage.Performative.ACCEPT
        return result

    def is_expecting_cfp_decline(self) -> bool:
        """
        Check whether the dialogue is expecting an decline following a cfp.

        :return: True if yes, False otherwise.
        """
        last_sent_message = self._outgoing_messages[-1] if len(self._outgoing_messages) > 0 else None  # type: Optional[Message]
        result = (last_sent_message is not None) and last_sent_message.get("performative") == FIPAMessage.Performative.CFP
        return result

    def is_expecting_propose_decline(self) -> bool:
        """
        Check whether the dialogue is expecting an decline following a propose.

        :return: True if yes, False otherwise.
        """
        last_sent_message = self._outgoing_messages[-1] if len(self._outgoing_messages) > 0 else None  # type: Optional[Message]
        result = (last_sent_message is not None) and last_sent_message.get("performative") == FIPAMessage.Performative.PROPOSE
        return result

    def is_expecting_accept_decline(self) -> bool:
        """
        Check whether the dialogue is expecting an decline following an accept.

        :return: True if yes, False otherwise.
        """
        last_sent_message = self._outgoing_messages[-1] if len(self._outgoing_messages) > 0 else None  # type: Optional[Message]
        result = (last_sent_message is not None) and last_sent_message.get("performative") == FIPAMessage.Performative.ACCEPT
        return result


class Dialogues(BaseDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self) -> None:
        """
        Initialize dialogues.

        :return: None
        """
        BaseDialogues.__init__(self)
        self._dialogues_as_seller = {}  # type: Dict[DialogueLabel, Dialogue]
        self._dialogues_as_buyer = {}  # type: Dict[DialogueLabel, Dialogue]

    @property
    def dialogues_as_seller(self) -> Dict[DialogueLabel, Dialogue]:
        """Get dictionary of dialogues in which the agent acts as a seller."""
        return self._dialogues_as_seller

    @property
    def dialogues_as_buyer(self) -> Dict[DialogueLabel, Dialogue]:
        """Get dictionary of dialogues in which the agent acts as a buyer."""
        return self._dialogues_as_buyer

    def is_permitted_for_new_dialogue(self, message: Message, known_pbks: List[str], sender: Address) -> bool:
        """
        Check whether an agent message is permitted for a new dialogue.

        That is, the message has to
        - be a CFP,
        - have the correct msg id and message target, and
        - be from a known public key.

        :param message: the agent message
        :param known_pbks: the list of known public keys

        :return: a boolean indicating whether the message is permitted for a new dialogue
        """
        msg_id = message.get("id")
        target = message.get("target")
        performative = message.get("performative")

        result = performative == FIPAMessage.Performative.CFP \
            and msg_id == STARTING_MESSAGE_ID\
            and target == STARTING_MESSAGE_TARGET \
            and (sender in known_pbks)
        return result

    def is_belonging_to_registered_dialogue(self, message: Message, agent_pbk: Address, sender: Address) -> bool:
        """
        Check whether an agent message is part of a registered dialogue.

        :param message: the agent message
        :param agent_pbk: the public key of the agent

        :return: boolean indicating whether the message belongs to a registered dialogue
        """
        dialogue_id = message.get("dialogue_id")
        opponent = sender
        target = message.get("target")
        performative = message.get("performative")
        self_initiated_dialogue_label = DialogueLabel(dialogue_id, opponent, agent_pbk)
        other_initiated_dialogue_label = DialogueLabel(dialogue_id, opponent, opponent)
        result = False
        if performative == FIPAMessage.Performative.PROPOSE and target == PROPOSE_TARGET and self_initiated_dialogue_label in self.dialogues:
            self_initiated_dialogue = self.dialogues[self_initiated_dialogue_label]
            result = self_initiated_dialogue.is_expecting_propose()
        elif performative == FIPAMessage.Performative.ACCEPT:
            if target == ACCEPT_TARGET and other_initiated_dialogue_label in self.dialogues:
                other_initiated_dialogue = self.dialogues[other_initiated_dialogue_label]
                result = other_initiated_dialogue.is_expecting_initial_accept()
        elif performative == FIPAMessage.Performative.MATCH_ACCEPT:
            if target == MATCH_ACCEPT_TARGET and self_initiated_dialogue_label in self.dialogues:
                self_initiated_dialogue = self.dialogues[self_initiated_dialogue_label]
                result = self_initiated_dialogue.is_expecting_matching_accept()
        elif performative == FIPAMessage.Performative.DECLINE:
            if target == DECLINED_CFP_TARGET and self_initiated_dialogue_label in self.dialogues:
                self_initiated_dialogue = self.dialogues[self_initiated_dialogue_label]
                result = self_initiated_dialogue.is_expecting_cfp_decline()
            elif target == DECLINED_PROPOSE_TARGET and other_initiated_dialogue_label in self.dialogues:
                other_initiated_dialogue = self.dialogues[other_initiated_dialogue_label]
                result = other_initiated_dialogue.is_expecting_propose_decline()
            elif target == DECLINED_ACCEPT_TARGET and self_initiated_dialogue_label in self.dialogues:
                self_initiated_dialogue = self.dialogues[self_initiated_dialogue_label]
                result = self_initiated_dialogue.is_expecting_accept_decline()
        return result

    def get_dialogue(self, message: Message, sender: Address, agent_pbk: Address) -> Dialogue:
        """
        Retrieve dialogue.

        :param message: the agent message
        :param agent_pbk: the public key of the agent

        :return: the dialogue
        """
        dialogue_id = message.get("dialogue_id")
        opponent = sender
        target = message.get("target")
        performative = message.get("performative")
        self_initiated_dialogue_label = DialogueLabel(dialogue_id, opponent, agent_pbk)
        other_initiated_dialogue_label = DialogueLabel(dialogue_id, opponent, opponent)
        if performative == FIPAMessage.Performative.PROPOSE and target == PROPOSE_TARGET and self_initiated_dialogue_label in self.dialogues:
            dialogue = self.dialogues[self_initiated_dialogue_label]
        elif performative == FIPAMessage.Performative.ACCEPT:
            if target == ACCEPT_TARGET and other_initiated_dialogue_label in self.dialogues:
                dialogue = self.dialogues[other_initiated_dialogue_label]
            else:
                raise ValueError('Should have found dialogue.')
        elif performative == FIPAMessage.Performative.MATCH_ACCEPT:
            if target == MATCH_ACCEPT_TARGET and self_initiated_dialogue_label in self.dialogues:
                dialogue = self.dialogues[self_initiated_dialogue_label]
            else:
                raise ValueError('Should have found dialogue.')
        elif performative == FIPAMessage.Performative.DECLINE:
            if target == DECLINED_CFP_TARGET and self_initiated_dialogue_label in self.dialogues:
                dialogue = self.dialogues[self_initiated_dialogue_label]
            elif target == DECLINED_PROPOSE_TARGET and other_initiated_dialogue_label in self.dialogues:
                dialogue = self.dialogues[other_initiated_dialogue_label]
            elif target == DECLINED_ACCEPT_TARGET and self_initiated_dialogue_label in self.dialogues:
                dialogue = self.dialogues[self_initiated_dialogue_label]
            else:
                raise ValueError('Should have found dialogue.')
        else:
            raise ValueError('Should have found dialogue.')
        return dialogue

    def create_self_initiated(self, dialogue_opponent_pbk: Address, dialogue_starter_pbk: Address, is_seller: bool) -> Dialogue:
        """
        Create a self initiated dialogue.

        :param dialogue_opponent_pbk: the pbk of the agent with which the dialogue is kept.
        :param dialogue_starter_pbk: the pbk of the agent which started the dialogue
        :param is_seller: boolean indicating the agent role

        :return: the created dialogue.
        """
        dialogue_label = DialogueLabel(self._next_dialogue_id(), dialogue_opponent_pbk, dialogue_starter_pbk)
        result = self._create(dialogue_label, is_seller)
        return result

    def create_opponent_initiated(self, dialogue_opponent_pbk: Address, dialogue_id: int, is_seller: bool) -> Dialogue:
        """
        Save an opponent initiated dialogue.

        :param dialogue_opponent_pbk: the pbk of the agent with which the dialogue is kept.
        :param dialogue_id: the id of the dialogue
        :param is_seller: boolean indicating the agent role

        :return: the created dialogue
        """
        dialogue_starter_pbk = dialogue_opponent_pbk
        dialogue_label = DialogueLabel(dialogue_id, dialogue_opponent_pbk, dialogue_starter_pbk)
        result = self._create(dialogue_label, is_seller)
        return result

    def _create(self, dialogue_label: DialogueLabel, is_seller: bool) -> Dialogue:
        """
        Create a dialogue.

        :param dialogue_label: the dialogue label
        :param is_seller: boolean indicating the agent role

        :return: the created dialogue
        """
        assert dialogue_label not in self.dialogues
        dialogue = Dialogue(dialogue_label, is_seller)
        if is_seller:
            assert dialogue_label not in self.dialogues_as_seller
            self._dialogues_as_seller.update({dialogue_label: dialogue})
        else:
            assert dialogue_label not in self.dialogues_as_buyer
            self._dialogues_as_buyer.update({dialogue_label: dialogue})
        self.dialogues.update({dialogue_label: dialogue})
        return dialogue
