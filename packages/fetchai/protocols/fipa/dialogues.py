# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 fetchai
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

- FipaDialogue: The dialogue class maintains state of a dialogue and manages it.
- FipaDialogues: The dialogues class keeps track of all dialogues.
"""

from abc import ABC
from typing import Callable, Dict, FrozenSet, Type, cast

from aea.common import Address
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue, DialogueLabel, Dialogues

from packages.fetchai.protocols.fipa.message import FipaMessage


class FipaDialogue(Dialogue):
    """The fipa dialogue class maintains state of a dialogue and manages it."""

    INITIAL_PERFORMATIVES: FrozenSet[Message.Performative] = frozenset(
        {FipaMessage.Performative.CFP}
    )
    TERMINAL_PERFORMATIVES: FrozenSet[Message.Performative] = frozenset(
        {FipaMessage.Performative.DECLINE, FipaMessage.Performative.END}
    )
    VALID_REPLIES: Dict[Message.Performative, FrozenSet[Message.Performative]] = {
        FipaMessage.Performative.ACCEPT: frozenset(
            {
                FipaMessage.Performative.DECLINE,
                FipaMessage.Performative.MATCH_ACCEPT,
                FipaMessage.Performative.MATCH_ACCEPT_W_INFORM,
            }
        ),
        FipaMessage.Performative.ACCEPT_W_INFORM: frozenset(
            {
                FipaMessage.Performative.DECLINE,
                FipaMessage.Performative.MATCH_ACCEPT,
                FipaMessage.Performative.MATCH_ACCEPT_W_INFORM,
            }
        ),
        FipaMessage.Performative.CFP: frozenset(
            {FipaMessage.Performative.PROPOSE, FipaMessage.Performative.DECLINE}
        ),
        FipaMessage.Performative.DECLINE: frozenset(),
        FipaMessage.Performative.END: frozenset(),
        FipaMessage.Performative.INFORM: frozenset(
            {FipaMessage.Performative.INFORM, FipaMessage.Performative.END}
        ),
        FipaMessage.Performative.MATCH_ACCEPT: frozenset(
            {FipaMessage.Performative.INFORM, FipaMessage.Performative.END}
        ),
        FipaMessage.Performative.MATCH_ACCEPT_W_INFORM: frozenset(
            {FipaMessage.Performative.INFORM, FipaMessage.Performative.END}
        ),
        FipaMessage.Performative.PROPOSE: frozenset(
            {
                FipaMessage.Performative.ACCEPT,
                FipaMessage.Performative.ACCEPT_W_INFORM,
                FipaMessage.Performative.DECLINE,
                FipaMessage.Performative.PROPOSE,
            }
        ),
    }

    class Role(Dialogue.Role):
        """This class defines the agent's role in a fipa dialogue."""

        BUYER = "buyer"
        SELLER = "seller"

    class EndState(Dialogue.EndState):
        """This class defines the end states of a fipa dialogue."""

        SUCCESSFUL = 0
        DECLINED_CFP = 1
        DECLINED_PROPOSE = 2
        DECLINED_ACCEPT = 3

    def __init__(
        self,
        dialogue_label: DialogueLabel,
        self_address: Address,
        role: Dialogue.Role,
        message_class: Type[FipaMessage] = FipaMessage,
    ) -> None:
        """
        Initialize a dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param self_address: the address of the entity for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for
        :param message_class: the message class used
        """
        Dialogue.__init__(
            self,
            dialogue_label=dialogue_label,
            message_class=message_class,
            self_address=self_address,
            role=role,
        )


class FipaDialogues(Dialogues, ABC):
    """This class keeps track of all fipa dialogues."""

    END_STATES = frozenset(
        {
            FipaDialogue.EndState.SUCCESSFUL,
            FipaDialogue.EndState.DECLINED_CFP,
            FipaDialogue.EndState.DECLINED_PROPOSE,
            FipaDialogue.EndState.DECLINED_ACCEPT,
        }
    )

    _keep_terminal_state_dialogues = True

    def __init__(
        self,
        self_address: Address,
        role_from_first_message: Callable[[Message, Address], Dialogue.Role],
        dialogue_class: Type[FipaDialogue] = FipaDialogue,
    ) -> None:
        """
        Initialize dialogues.

        :param self_address: the address of the entity for whom dialogues are maintained
        :param dialogue_class: the dialogue class used
        :param role_from_first_message: the callable determining role from first message
        """
        Dialogues.__init__(
            self,
            self_address=self_address,
            end_states=cast(FrozenSet[Dialogue.EndState], self.END_STATES),
            message_class=FipaMessage,
            dialogue_class=dialogue_class,
            role_from_first_message=role_from_first_message,
        )
