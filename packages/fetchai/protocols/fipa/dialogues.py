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
This module contains the classes required for fipa dialogue management.

- DialogueLabel: The dialogue label class acts as an identifier for dialogues.
- Dialogue: The dialogue class maintains state of a dialogue and manages it.
- Dialogues: The dialogues class keeps track of all dialogues.
"""

from abc import ABC
from enum import Enum
from typing import Dict, FrozenSet, cast

from aea.helpers.dialogue.base import Dialogue, Dialogues
from aea.mail.base import Address
from aea.protocols.base import Message

from packages.fetchai.protocols.fipa.message import FipaMessage

VALID_REPLIES = {
    FipaMessage.Performative.ACCEPT: frozenset(
        [
            FipaMessage.Performative.MATCH_ACCEPT,
            FipaMessage.Performative.MATCH_ACCEPT_W_INFORM,
            FipaMessage.Performative.DECLINE,
        ]
    ),
    FipaMessage.Performative.ACCEPT_W_INFORM: frozenset(
        [
            FipaMessage.Performative.MATCH_ACCEPT,
            FipaMessage.Performative.MATCH_ACCEPT_W_INFORM,
            FipaMessage.Performative.DECLINE,
        ]
    ),
    FipaMessage.Performative.CFP: frozenset(
        [FipaMessage.Performative.PROPOSE, FipaMessage.Performative.DECLINE]
    ),
    FipaMessage.Performative.DECLINE: frozenset(),
    FipaMessage.Performative.INFORM: frozenset([FipaMessage.Performative.INFORM]),
    FipaMessage.Performative.MATCH_ACCEPT: frozenset([FipaMessage.Performative.INFORM]),
    FipaMessage.Performative.MATCH_ACCEPT_W_INFORM: frozenset(
        [FipaMessage.Performative.INFORM]
    ),
    FipaMessage.Performative.PROPOSE: frozenset(
        [
            FipaMessage.Performative.PROPOSE,
            FipaMessage.Performative.ACCEPT,
            FipaMessage.Performative.ACCEPT_W_INFORM,
            FipaMessage.Performative.DECLINE,
        ]
    ),
}  # type: Dict[FipaMessage.Performative, FrozenSet[FipaMessage.Performative]]


class FipaDialogue(Dialogue, ABC):
    """The fipa dialogue class maintains state of a dialogue and manages it."""

    class AgentRole(Dialogue.Role):
        """This class defines the agent's role in a fipa dialogue."""

        SELLER = "seller"
        BUYER = "buyer"

    class EndState(Dialogue.EndState):
        """This class defines the end states of a fipa dialogue."""

        SUCCESSFUL = 0
        DECLINED_CFP = 1
        DECLINED_PROPOSE = 2
        DECLINED_ACCEPT = 3

    def is_valid(self, message: Message) -> bool:
        """
        Check whether 'message' is a valid next message in the dialogue.

        These rules capture specific constraints designed for dialogues which are instances of a concrete sub-class of this class.
        Override this method with your additional dialogue rules.

        :param message: the message to be validated
        :return: True if valid, False otherwise
        """
        return True

    def initial_performative(self) -> FipaMessage.Performative:
        """
        Get the performative which the initial message in the dialogue must have.

        :return: the performative of the initial message
        """
        return FipaMessage.Performative.CFP

    def get_replies(self, performative: Enum) -> FrozenSet:
        """
        Given a 'performative', return the list of performatives which are its valid replies in a fipa dialogue

        :param performative: the performative in a message
        :return: list of valid performative replies
        """
        performative = cast(FipaMessage.Performative, performative)
        assert (
            performative in VALID_REPLIES
        ), "this performative '{}' is not supported".format(performative)
        return VALID_REPLIES[performative]


class FipaDialogueStats(object):
    """Class to handle statistics on fipa dialogues."""

    def __init__(self) -> None:
        """Initialize a StatsManager."""
        self._self_initiated = {
            FipaDialogue.EndState.SUCCESSFUL: 0,
            FipaDialogue.EndState.DECLINED_CFP: 0,
            FipaDialogue.EndState.DECLINED_PROPOSE: 0,
            FipaDialogue.EndState.DECLINED_ACCEPT: 0,
        }  # type: Dict[FipaDialogue.EndState, int]
        self._other_initiated = {
            FipaDialogue.EndState.SUCCESSFUL: 0,
            FipaDialogue.EndState.DECLINED_CFP: 0,
            FipaDialogue.EndState.DECLINED_PROPOSE: 0,
            FipaDialogue.EndState.DECLINED_ACCEPT: 0,
        }  # type: Dict[FipaDialogue.EndState, int]

    @property
    def self_initiated(self) -> Dict[FipaDialogue.EndState, int]:
        """Get the stats dictionary on self initiated dialogues."""
        return self._self_initiated

    @property
    def other_initiated(self) -> Dict[FipaDialogue.EndState, int]:
        """Get the stats dictionary on other initiated dialogues."""
        return self._other_initiated

    def add_dialogue_endstate(
        self, end_state: FipaDialogue.EndState, is_self_initiated: bool
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


class FipaDialogues(Dialogues, ABC):
    """This class keeps track of all fipa dialogues."""

    def __init__(self, agent_address: Address) -> None:
        """
        Initialize dialogues.

        :param agent_address: the address of the agent for whom dialogues are maintained
        :return: None
        """
        Dialogues.__init__(self, agent_address=agent_address)
        self._dialogue_stats = FipaDialogueStats()

    @property
    def dialogue_stats(self) -> FipaDialogueStats:
        """
        Get the dialogue statistics.

        :return: dialogue stats object
        """
        return self._dialogue_stats
