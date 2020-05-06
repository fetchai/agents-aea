# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2020 fetchai
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
This module contains the classes required for two_party_negotiation dialogue management.

- DialogueLabel: The dialogue label class acts as an identifier for dialogues.
- Dialogue: The dialogue class maintains state of a dialogue and manages it.
- Dialogues: The dialogues class keeps track of all dialogues.
"""

from enum import Enum
from typing import Dict, List, Tuple, Union, cast

from aea.helpers.dialogue.base import Dialogue, DialogueLabel, Dialogues
from aea.mail.base import Address
from aea.protocols.base import Message

from packages.fetchai.protocols.two_party_negotiation.message import (
    TwoPartyNegotiationMessage,
)

REPLY = {
    "cfp": ["propose", "decline"],
    "propose": ["accept", "decline"],
    "accept": ["decline", "match_accept"],
    "decline": [],
    "match_accept": [],
}


class TwoPartyNegotiationDialogue(Dialogue):
    """The two_party_negotiation dialogue class maintains state of a dialogue and manages it."""

    STARTING_MESSAGE_ID = 1
    STARTING_TARGET = 0

    class EndState(Enum):
        """This class defines the end states of a dialogue."""

        SUCCESSFUL = 0
        DECLINED_CFP = 1
        DECLINED_PROPOSE = 2
        DECLINED_ACCEPT = 3

    class AgentRole(Enum):
        """This class defines the agent's role in the dialogue."""

        SELLER = "seller"
        BUYER = "buyer"

    def __init__(
        self, dialogue_label: DialogueLabel, is_seller: bool, **kwargs
    ) -> None:
        """
        Initialize a dialogue label.

        :param dialogue_label: the identifier of the dialogue.
        :param is_seller: indicates whether the agent associated with the dialogue is a seller or buyer

        :return: None
        """
        super().__init__(self, dialogue_label=dialogue_label)
        self._is_seller = is_seller
        self._role = (
            TwoPartyNegotiationDialogue.AgentRole.SELLER
            if is_seller
            else TwoPartyNegotiationDialogue.AgentRole.BUYER
        )

    @property
    def is_seller(self) -> bool:
        """Check whether the agent acts as the seller in this dialogue."""
        return self._is_seller

    @property
    def role(self) -> "TwoPartyNegotiationDialogue.AgentRole":
        """Get role of agent in dialogue."""
        return self._role

    def is_valid_next_message(self, two_party_negotiation_msg: Message) -> bool:
        """Check that the message is consistent with respect to the two_party_negotiation dialogue according to the protocol."""
        two_party_negotiation_msg = cast(
            TwoPartyNegotiationMessage, two_party_negotiation_msg
        )
        this_message_id = two_party_negotiation_msg.message_id
        this_target = two_party_negotiation_msg.target
        this_performative = two_party_negotiation_msg.performative
        last_outgoing_message = cast(
            TwoPartyNegotiationMessage, self.last_outgoing_message
        )
        if last_outgoing_message is None:
            result = (
                this_message_id == TwoPartyNegotiationDialogue.STARTING_MESSAGE_ID
                and this_target == TwoPartyNegotiationDialogue.STARTING_TARGET
                and this_performative == TwoPartyNegotiationMessage.Performative.CFP
            )
        else:
            last_message_id = last_outgoing_message.message_id
            last_target = last_outgoing_message.target
            last_performative = last_outgoing_message.performative
            result = (
                this_message_id == last_message_id + 1
                and this_target == last_target + 1
                and last_performative in REPLY[this_performative]
            )
        return result

    def assign_final_dialogue_label(self, final_dialogue_label: DialogueLabel) -> None:
        """
        Assign the final dialogue label.

        :param final_dialogue_label: the final dialogue label
        :return: None
        """
        assert (
            self.dialogue_label.dialogue_starter_reference
            == final_dialogue_label.dialogue_starter_reference
        )
        assert self.dialogue_label.dialogue_responder_reference == ""
        assert final_dialogue_label.dialogue_responder_reference != ""
        assert (
            self.dialogue_label.dialogue_opponent_addr
            == final_dialogue_label.dialogue_opponent_addr
        )
        assert (
            self.dialogue_label.dialogue_starter_addr
            == final_dialogue_label.dialogue_starter_addr
        )
        self._dialogue_label = final_dialogue_label


class TwoPartyNegotiationDialogueStats(object):
    """Class to handle statistics for two_party_negotiation dialogues."""

    def __init__(self) -> None:
        """Initialize a StatsManager."""
        self._self_initiated = {
            TwoPartyNegotiationDialogue.EndState.SUCCESSFUL: 0,
            TwoPartyNegotiationDialogue.EndState.DECLINED_CFP: 0,
            TwoPartyNegotiationDialogue.EndState.DECLINED_PROPOSE: 0,
            TwoPartyNegotiationDialogue.EndState.DECLINED_ACCEPT: 0,
        }  # type: Dict[TwoPartyNegotiationDialogue.EndState, int]
        self._other_initiated = {
            TwoPartyNegotiationDialogue.EndState.SUCCESSFUL: 0,
            TwoPartyNegotiationDialogue.EndState.DECLINED_CFP: 0,
            TwoPartyNegotiationDialogue.EndState.DECLINED_PROPOSE: 0,
            TwoPartyNegotiationDialogue.EndState.DECLINED_ACCEPT: 0,
        }  # type: Dict[TwoPartyNegotiationDialogue.EndState, int]

    @property
    def self_initiated(self) -> Dict[TwoPartyNegotiationDialogue.EndState, int]:
        """Get the stats dictionary on self initiated dialogues."""
        return self._self_initiated

    @property
    def other_initiated(self) -> Dict[TwoPartyNegotiationDialogue.EndState, int]:
        """Get the stats dictionary on other initiated dialogues."""
        return self._other_initiated

    def add_dialogue_endstate(
        self, end_state: TwoPartyNegotiationDialogue.EndState, is_self_initiated: bool
    ) -> None:
        """
        Add dialogue endstate stats.

        :param end_state: the end state of the dialogue
        :param is_self_initiated: whether the dialogue is initiated by the agent or the opponent

        :return: None
        """
        if is_self_initiated:
            self._self_initiated[end_state] += 1
        else:
            self._other_initiated[end_state] += 1


class TwoPartyNegotiationDialogues(Dialogues):
    """This class keeps track of all {} dialogues."""

    def __init__(self) -> None:
        """
        Initialize dialogues.

        :return: None
        """
        super().__init__(self)
        self._initiated_dialogues = (
            {}
        )  # type: Dict[DialogueLabel, TwoPartyNegotiationDialogue]
        self._dialogues_as_seller = (
            {}
        )  # type: Dict[DialogueLabel, TwoPartyNegotiationDialogue]
        self._dialogues_as_buyer = (
            {}
        )  # type: Dict[DialogueLabel, TwoPartyNegotiationDialogue]
        self._dialogue_stats = TwoPartyNegotiationDialogueStats()

    @property
    def dialogues_as_seller(self) -> Dict[DialogueLabel, TwoPartyNegotiationDialogue]:
        """Get dictionary of dialogues in which the agent acts as a seller."""
        return self._dialogues_as_seller

    @property
    def dialogues_as_buyer(self) -> Dict[DialogueLabel, TwoPartyNegotiationDialogue]:
        """Get dictionary of dialogues in which the agent acts as a buyer."""
        return self._dialogues_as_buyer

    @property
    def dialogue_stats(self) -> TwoPartyNegotiationDialogueStats:
        """Get the dialogue statistics."""
        return self._dialogue_stats

    def get_dialogue(
        self, two_party_negotiation_msg: Message, agent_addr: Address
    ) -> Dialogue:
        """
        Given a message addressed to a specific dialogue, retrieve this dialogue if the message is a valid next move.

        :param two_party_negotiation_msg: the message
        :param agent_addr: the address of the agent

        :return: the dialogue
        """
        result = None
        two_party_negotiation_msg = cast(
            TwoPartyNegotiationMessage, two_party_negotiation_msg
        )
        dialogue_reference = two_party_negotiation_msg.dialogue_reference
        self_initiated_dialogue_label = DialogueLabel(
            dialogue_reference, two_party_negotiation_msg.counterparty, agent_addr
        )
        other_initiated_dialogue_label = DialogueLabel(
            dialogue_reference,
            two_party_negotiation_msg.counterparty,
            two_party_negotiation_msg.counterparty,
        )
        if other_initiated_dialogue_label in self.dialogues:
            other_initiated_dialogue = cast(
                TwoPartyNegotiationDialogue,
                self.dialogues[other_initiated_dialogue_label],
            )
            if other_initiated_dialogue.is_valid_next_message(
                two_party_negotiation_msg
            ):
                result = other_initiated_dialogue
        if self_initiated_dialogue_label in self.dialogues:
            self_initiated_dialogue = cast(
                TwoPartyNegotiationDialogue,
                self.dialogues[self_initiated_dialogue_label],
            )
            if self_initiated_dialogue.is_valid_next_message(two_party_negotiation_msg):
                result = self_initiated_dialogue
        if result is None:
            raise ValueError("Should have found dialogue.")
        return result

    def create_self_initiated(
        self,
        dialogue_opponent_addr: Address,
        dialogue_starter_addr: Address,
        is_seller: bool,
    ) -> Dialogue:
        """
        Create a self initiated dialogue.

        :param dialogue_opponent_addr: the pbk of the agent with which the dialogue is kept.
        :param dialogue_starter_addr: the pbk of the agent which started the dialogue
        :param is_seller: boolean indicating the agent role

        :return: the created dialogue.
            """
        dialogue_reference = (str(self._next_dialogue_nonce()), "")
        dialogue_label = DialogueLabel(
            dialogue_reference, dialogue_opponent_addr, dialogue_starter_addr
        )
        dialogue = TwoPartyNegotiationDialogue(dialogue_label, is_seller)
        self._initiated_dialogues.update({dialogue_label: dialogue})
        return dialogue

    def create_opponent_initiated(
        self,
        dialogue_opponent_addr: Address,
        dialogue_reference: Tuple[str, str],
        is_seller: bool,
    ) -> Dialogue:
        """
        Save an opponent initiated dialogue.

        :param dialogue_opponent_addr: the address of the agent with which the dialogue is kept.
        :param dialogue_reference: the reference of the dialogue.
        :param is_seller: keeps track if the counterparty is a seller.
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
        result = self._create(dialogue_label, is_seller)
        return result

    def _create(
        self, dialogue_label: DialogueLabel, is_seller: bool
    ) -> TwoPartyNegotiationDialogue:
        """
        Create a dialogue.

        :param dialogue_label: the dialogue label
        :param is_seller: boolean indicating the agent role

        :return: the created dialogue
        """
        assert dialogue_label not in self.dialogues
        dialogue = TwoPartyNegotiationDialogue(dialogue_label, is_seller)
        if is_seller:
            assert dialogue_label not in self.dialogues_as_seller
            self._dialogues_as_seller.update({dialogue_label: dialogue})
        else:
            assert dialogue_label not in self.dialogues_as_buyer
            self._dialogues_as_buyer.update({dialogue_label: dialogue})
        self.dialogues.update({dialogue_label: dialogue})
        return dialogue
