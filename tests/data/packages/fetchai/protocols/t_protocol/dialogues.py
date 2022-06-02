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
This module contains the classes required for t_protocol dialogue management.

- TProtocolDialogue: The dialogue class maintains state of a dialogue and manages it.
- TProtocolDialogues: The dialogues class keeps track of all dialogues.
"""

from abc import ABC
from typing import Callable, Dict, FrozenSet, Type, cast

from aea.common import Address
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue, DialogueLabel, Dialogues

from tests.data.packages.fetchai.protocols.t_protocol.message import TProtocolMessage


class TProtocolDialogue(Dialogue):
    """The t_protocol dialogue class maintains state of a dialogue and manages it."""

    INITIAL_PERFORMATIVES: FrozenSet[Message.Performative] = frozenset(
        {
            TProtocolMessage.Performative.PERFORMATIVE_CT,
            TProtocolMessage.Performative.PERFORMATIVE_PT,
        }
    )
    TERMINAL_PERFORMATIVES: FrozenSet[Message.Performative] = frozenset(
        {
            TProtocolMessage.Performative.PERFORMATIVE_MT,
            TProtocolMessage.Performative.PERFORMATIVE_O,
        }
    )
    VALID_REPLIES: Dict[Message.Performative, FrozenSet[Message.Performative]] = {
        TProtocolMessage.Performative.PERFORMATIVE_CT: frozenset(
            {TProtocolMessage.Performative.PERFORMATIVE_PCT}
        ),
        TProtocolMessage.Performative.PERFORMATIVE_EMPTY_CONTENTS: frozenset(
            {TProtocolMessage.Performative.PERFORMATIVE_EMPTY_CONTENTS}
        ),
        TProtocolMessage.Performative.PERFORMATIVE_MT: frozenset(),
        TProtocolMessage.Performative.PERFORMATIVE_O: frozenset(),
        TProtocolMessage.Performative.PERFORMATIVE_PCT: frozenset(
            {
                TProtocolMessage.Performative.PERFORMATIVE_MT,
                TProtocolMessage.Performative.PERFORMATIVE_O,
            }
        ),
        TProtocolMessage.Performative.PERFORMATIVE_PMT: frozenset(
            {
                TProtocolMessage.Performative.PERFORMATIVE_MT,
                TProtocolMessage.Performative.PERFORMATIVE_O,
            }
        ),
        TProtocolMessage.Performative.PERFORMATIVE_PT: frozenset(
            {
                TProtocolMessage.Performative.PERFORMATIVE_PT,
                TProtocolMessage.Performative.PERFORMATIVE_PMT,
            }
        ),
    }

    class Role(Dialogue.Role):
        """This class defines the agent's role in a t_protocol dialogue."""

        ROLE_1 = "role_1"
        ROLE_2 = "role_2"

    class EndState(Dialogue.EndState):
        """This class defines the end states of a t_protocol dialogue."""

        END_STATE_1 = 0
        END_STATE_2 = 1
        END_STATE_3 = 2

    def __init__(
        self,
        dialogue_label: DialogueLabel,
        self_address: Address,
        role: Dialogue.Role,
        message_class: Type[TProtocolMessage] = TProtocolMessage,
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


class TProtocolDialogues(Dialogues, ABC):
    """This class keeps track of all t_protocol dialogues."""

    END_STATES = frozenset(
        {
            TProtocolDialogue.EndState.END_STATE_1,
            TProtocolDialogue.EndState.END_STATE_2,
            TProtocolDialogue.EndState.END_STATE_3,
        }
    )

    _keep_terminal_state_dialogues = True

    def __init__(
        self,
        self_address: Address,
        role_from_first_message: Callable[[Message, Address], Dialogue.Role],
        dialogue_class: Type[TProtocolDialogue] = TProtocolDialogue,
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
            message_class=TProtocolMessage,
            dialogue_class=dialogue_class,
            role_from_first_message=role_from_first_message,
        )
