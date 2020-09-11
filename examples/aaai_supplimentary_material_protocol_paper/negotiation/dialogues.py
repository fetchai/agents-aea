# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2020 AAAI_paper_authors
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
This module contains the classes required for negotiation dialogue management.

- NegotiationDialogue: The dialogue class maintains state of a dialogue and manages it.
- NegotiationDialogues: The dialogues class keeps track of all dialogues.
"""

from abc import ABC
from typing import Callable, FrozenSet, Type, cast

from aea.common import Address
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue, DialogueLabel, Dialogues

from packages.AAAI_paper_authors.protocols.negotiation.message import NegotiationMessage


class NegotiationDialogue(Dialogue):
    """The negotiation dialogue class maintains state of a dialogue and manages it."""

    INITIAL_PERFORMATIVES = frozenset({NegotiationMessage.Performative.CFP})
    TERMINAL_PERFORMATIVES = frozenset(
        {
            NegotiationMessage.Performative.ACCEPT,
            NegotiationMessage.Performative.DECLINE,
        }
    )
    VALID_REPLIES = {
        NegotiationMessage.Performative.ACCEPT: frozenset(),
        NegotiationMessage.Performative.CFP: frozenset(
            {
                NegotiationMessage.Performative.PROPOSE,
                NegotiationMessage.Performative.DECLINE,
            }
        ),
        NegotiationMessage.Performative.DECLINE: frozenset(),
        NegotiationMessage.Performative.PROPOSE: frozenset(
            {
                NegotiationMessage.Performative.PROPOSE,
                NegotiationMessage.Performative.ACCEPT,
                NegotiationMessage.Performative.DECLINE,
            }
        ),
    }

    class Role(Dialogue.Role):
        """This class defines the agent's role in a negotiation dialogue."""

        BUYER = "buyer"
        SELLER = "seller"

    class EndState(Dialogue.EndState):
        """This class defines the end states of a negotiation dialogue."""

        AGREEMENT_REACHED = 0
        AGREEMENT_NOT_REACHED = 1

    def __init__(
        self,
        dialogue_label: DialogueLabel,
        self_address: Address,
        role: Dialogue.Role,
        message_class: Type[NegotiationMessage] = NegotiationMessage,
    ) -> None:
        """
        Initialize a dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param self_address: the address of the entity for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for
        :return: None
        """
        Dialogue.__init__(
            self,
            dialogue_label=dialogue_label,
            message_class=message_class,
            self_address=self_address,
            role=role,
        )


class NegotiationDialogues(Dialogues, ABC):
    """This class keeps track of all negotiation dialogues."""

    END_STATES = frozenset(
        {
            NegotiationDialogue.EndState.AGREEMENT_REACHED,
            NegotiationDialogue.EndState.AGREEMENT_NOT_REACHED,
        }
    )

    def __init__(
        self,
        self_address: Address,
        role_from_first_message: Callable[[Message, Address], Dialogue.Role],
        dialogue_class: Type[NegotiationDialogue] = NegotiationDialogue,
    ) -> None:
        """
        Initialize dialogues.

        :param self_address: the address of the entity for whom dialogues are maintained
        :return: None
        """
        Dialogues.__init__(
            self,
            self_address=self_address,
            end_states=cast(FrozenSet[Dialogue.EndState], self.END_STATES),
            message_class=NegotiationMessage,
            dialogue_class=dialogue_class,
            role_from_first_message=role_from_first_message,
        )
