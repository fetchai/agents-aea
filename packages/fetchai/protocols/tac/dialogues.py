# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021 fetchai
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
This module contains the classes required for tac dialogue management.

- TacDialogue: The dialogue class maintains state of a dialogue and manages it.
- TacDialogues: The dialogues class keeps track of all dialogues.
"""

from abc import ABC
from typing import Callable, FrozenSet, Type, cast

from aea.common import Address
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue, DialogueLabel, Dialogues

from packages.fetchai.protocols.tac.message import TacMessage


class TacDialogue(Dialogue):
    """The tac dialogue class maintains state of a dialogue and manages it."""

    INITIAL_PERFORMATIVES = frozenset({TacMessage.Performative.REGISTER})
    TERMINAL_PERFORMATIVES = frozenset({TacMessage.Performative.CANCELLED})
    VALID_REPLIES = {
        TacMessage.Performative.CANCELLED: frozenset(),
        TacMessage.Performative.GAME_DATA: frozenset(
            {
                TacMessage.Performative.TRANSACTION,
                TacMessage.Performative.TRANSACTION_CONFIRMATION,
                TacMessage.Performative.CANCELLED,
            }
        ),
        TacMessage.Performative.REGISTER: frozenset(
            {
                TacMessage.Performative.TAC_ERROR,
                TacMessage.Performative.GAME_DATA,
                TacMessage.Performative.CANCELLED,
                TacMessage.Performative.UNREGISTER,
            }
        ),
        TacMessage.Performative.TAC_ERROR: frozenset(
            {
                TacMessage.Performative.TRANSACTION,
                TacMessage.Performative.TRANSACTION_CONFIRMATION,
                TacMessage.Performative.CANCELLED,
            }
        ),
        TacMessage.Performative.TRANSACTION: frozenset(
            {
                TacMessage.Performative.TRANSACTION,
                TacMessage.Performative.TRANSACTION_CONFIRMATION,
                TacMessage.Performative.TAC_ERROR,
                TacMessage.Performative.CANCELLED,
            }
        ),
        TacMessage.Performative.TRANSACTION_CONFIRMATION: frozenset(
            {
                TacMessage.Performative.TRANSACTION,
                TacMessage.Performative.TRANSACTION_CONFIRMATION,
                TacMessage.Performative.CANCELLED,
            }
        ),
        TacMessage.Performative.UNREGISTER: frozenset(
            {TacMessage.Performative.TAC_ERROR}
        ),
    }

    class Role(Dialogue.Role):
        """This class defines the agent's role in a tac dialogue."""

        CONTROLLER = "controller"
        PARTICIPANT = "participant"

    class EndState(Dialogue.EndState):
        """This class defines the end states of a tac dialogue."""

        SUCCESSFUL = 0
        FAILED = 1

    def __init__(
        self,
        dialogue_label: DialogueLabel,
        self_address: Address,
        role: Dialogue.Role,
        message_class: Type[TacMessage] = TacMessage,
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


class TacDialogues(Dialogues, ABC):
    """This class keeps track of all tac dialogues."""

    END_STATES = frozenset(
        {TacDialogue.EndState.SUCCESSFUL, TacDialogue.EndState.FAILED}
    )

    _keep_terminal_state_dialogues = True

    def __init__(
        self,
        self_address: Address,
        role_from_first_message: Callable[[Message, Address], Dialogue.Role],
        dialogue_class: Type[TacDialogue] = TacDialogue,
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
            message_class=TacMessage,
            dialogue_class=dialogue_class,
            role_from_first_message=role_from_first_message,
        )
