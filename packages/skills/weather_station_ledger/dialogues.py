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
from typing import Any, Dict, Optional, cast

from aea.helpers.dialogue.base import DialogueLabel
from aea.helpers.dialogue.base import Dialogue as BaseDialogue
from aea.mail.base import Address
from aea.protocols.base import Message
from aea.protocols.fipa.message import FIPAMessage
from aea.protocols.oef.models import Description
from aea.skills.base import SharedClass

Action = Any
logger = logging.getLogger("aea.weather_station_ledger_skill")

STARTING_MESSAGE_ID = 1
STARTING_MESSAGE_TARGET = 0
PROPOSE_TARGET = STARTING_MESSAGE_ID
ACCEPT_TARGET = PROPOSE_TARGET + 1
MATCH_ACCEPT_TARGET = ACCEPT_TARGET + 1
DECLINED_PROPOSE_TARGET = PROPOSE_TARGET + 1
INFORM_TARGET = MATCH_ACCEPT_TARGET + 1


class Dialogue(BaseDialogue):
    """The dialogue class maintains state of a dialogue and manages it."""

    class EndState(Enum):
        """This class defines the end states of a dialogue."""

        SUCCESSFUL = 0
        DECLINED_PROPOSE = 1

    def __init__(self, dialogue_label: DialogueLabel, **kwargs) -> None:
        """
        Initialize a dialogue label.

        :param dialogue_label: the identifier of the dialogue

        :return: None
        """
        BaseDialogue.__init__(self, dialogue_label=dialogue_label)
        self.weather_data = None  # type: Optional[bytes]
        self.proposal = None  # type: Optional[Description]

    def is_expecting_accept(self) -> bool:
        """
        Check whether the dialogue is expecting an initial accept.

        :return: True if yes, False otherwise.
        """
        last_sent_message = self._outgoing_messages[-1] if len(self._outgoing_messages) > 0 else None  # type: Optional[Message]
        result = (last_sent_message is not None) and last_sent_message.get("performative") == FIPAMessage.Performative.PROPOSE
        return result

    def is_expecting_propose_decline(self) -> bool:
        """
        Check whether the dialogue is expecting an decline following a propose.

        :return: True if yes, False otherwise.
        """
        last_sent_message = self._outgoing_messages[-1] if len(self._outgoing_messages) > 0 else None  # type: Optional[Message]
        result = (last_sent_message is not None) and last_sent_message.get("performative") == FIPAMessage.Performative.PROPOSE
        return result

    def is_expecting_inform(self) -> bool:
        """
        Check whether the dialogue is expecting an inform.

        :return: True if yes, False otherwise.
        """
        last_sent_message = self._outgoing_messages[-1] if len(self._outgoing_messages) > 0 else None  # type: Optional[Message]
        result = (last_sent_message is not None) and last_sent_message.get("performative") == FIPAMessage.Performative.MATCH_ACCEPT_W_ADDRESS
        return result


class DialogueStats(object):
    """Class to handle statistics on the negotiation."""

    def __init__(self) -> None:
        """Initialize a StatsManager."""
        self._other_initiated = {Dialogue.EndState.SUCCESSFUL: 0,
                                 Dialogue.EndState.DECLINED_PROPOSE: 0}  # type: Dict[Dialogue.EndState, int]

    @property
    def other_initiated(self) -> Dict[Dialogue.EndState, int]:
        """Get the stats dictionary on other initiated dialogues."""
        return self._other_initiated

    def add_dialogue_endstate(self, end_state: Dialogue.EndState) -> None:
        """
        Add dialogue endstate stats.

        :param end_state: the end state of the dialogue

        :return: None
        """
        self._other_initiated[end_state] += 1


class Dialogues(SharedClass):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize dialogues.

        :return: None
        """
        SharedClass.__init__(self, **kwargs)
        self._dialogues = {}  # type: Dict[DialogueLabel, Dialogue]
        self._dialogue_stats = DialogueStats()

    @property
    def dialogues(self) -> Dict[DialogueLabel, Dialogue]:
        """Get dictionary of dialogues in which the agent is engaged in."""
        return self._dialogues

    @property
    def dialogue_stats(self) -> DialogueStats:
        """Get the dialogue statistics."""
        return self._dialogue_stats

    def is_permitted_for_new_dialogue(self, fipa_msg: Message, sender: Address) -> bool:
        """
        Check whether a fipa message is permitted for a new dialogue.

        That is, the message has to
        - be a CFP, and
        - have the correct msg id and message target.

        :param message: the fipa message
        :param sender: the sender

        :return: a boolean indicating whether the message is permitted for a new dialogue
        """
        fipa_msg = cast(FIPAMessage, fipa_msg)
        msg_id = fipa_msg.get("message_id")
        target = fipa_msg.get("target")
        performative = fipa_msg.get("performative")

        result = performative == FIPAMessage.Performative.CFP \
            and msg_id == STARTING_MESSAGE_ID \
            and target == STARTING_MESSAGE_TARGET
        return result

    def is_belonging_to_registered_dialogue(self, fipa_msg: Message, sender: Address, agent_pbk: Address) -> bool:
        """
        Check whether an agent message is part of a registered dialogue.

        :param fipa_msg: the fipa message
        :param sender: the sender
        :param agent_pbk: the public key of the agent

        :return: boolean indicating whether the message belongs to a registered dialogue
        """
        dialogue_id = cast(int, fipa_msg.get("dialogue_id"))
        target = cast(int, fipa_msg.get("target"))
        performative = fipa_msg.get("performative")
        other_initiated_dialogue_label = DialogueLabel(dialogue_id, sender, sender)
        result = False
        if performative == FIPAMessage.Performative.ACCEPT:
            if target == ACCEPT_TARGET and other_initiated_dialogue_label in self.dialogues:
                other_initiated_dialogue = cast(Dialogue, self.dialogues[other_initiated_dialogue_label])
                result = other_initiated_dialogue.is_expecting_accept()
        elif performative == FIPAMessage.Performative.DECLINE:
            if target == DECLINED_PROPOSE_TARGET and other_initiated_dialogue_label in self.dialogues:
                other_initiated_dialogue = cast(Dialogue, self.dialogues[other_initiated_dialogue_label])
                result = other_initiated_dialogue.is_expecting_propose_decline()
        elif performative == FIPAMessage.Performative.INFORM:
            if target == INFORM_TARGET and other_initiated_dialogue_label in self.dialogues:
                other_initiated_dialogue = cast(Dialogue, self.dialogues[other_initiated_dialogue_label])
                result = other_initiated_dialogue.is_expecting_inform()
        return result

    def get_dialogue(self, fipa_msg: Message, sender: Address, agent_pbk: Address) -> Dialogue:
        """
        Retrieve dialogue.

        :param fipa_msg: the fipa message
        :param sender_pbk: the sender public key
        :param agent_pbk: the public key of the agent

        :return: the dialogue
        """
        dialogue_id = cast(int, fipa_msg.get("dialogue_id"))
        target = cast(int, fipa_msg.get("target"))
        performative = fipa_msg.get("performative")
        other_initiated_dialogue_label = DialogueLabel(dialogue_id, sender, sender)
        if performative == FIPAMessage.Performative.ACCEPT:
            if target == ACCEPT_TARGET and other_initiated_dialogue_label in self.dialogues:
                dialogue = self.dialogues[other_initiated_dialogue_label]
            else:
                raise ValueError('Should have found dialogue.')
        elif performative == FIPAMessage.Performative.DECLINE:
            if target == DECLINED_PROPOSE_TARGET and other_initiated_dialogue_label in self.dialogues:
                dialogue = self.dialogues[other_initiated_dialogue_label]
            else:
                raise ValueError('Should have found dialogue.')
        elif performative == FIPAMessage.Performative.INFORM:
            if target == INFORM_TARGET and other_initiated_dialogue_label in self.dialogues:
                dialogue = self.dialogues[other_initiated_dialogue_label]
        else:
            raise ValueError('Should have found dialogue.')
        dialogue = cast(Dialogue, dialogue)
        return dialogue

    def create_opponent_initiated(self, fipa_msg: FIPAMessage, sender: Address) -> Dialogue:
        """
        Save an opponent initiated dialogue.

        :param fipa_msg: the fipa message
        :param sender: the pbk of the sender

        :return: the created dialogue
        """
        dialogue_starter_pbk = sender
        dialogue_opponent_pbk = sender
        dialogue_id = cast(int, fipa_msg.get("dialogue_id"))
        dialogue_label = DialogueLabel(dialogue_id, dialogue_opponent_pbk, dialogue_starter_pbk)
        result = self._create(dialogue_label)
        return result

    def _create(self, dialogue_label: DialogueLabel) -> Dialogue:
        """
        Create a dialogue.

        :param dialogue_label: the dialogue label

        :return: the created dialogue
        """
        assert dialogue_label not in self.dialogues
        dialogue = Dialogue(dialogue_label)
        self.dialogues.update({dialogue_label: dialogue})
        return dialogue

    def reset(self) -> None:
        """
        Reset the dialogues.

        :return: None
        """
        self._dialogues = {}
        self._dialogue_stats = DialogueStats()
