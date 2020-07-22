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
This module contains the classes required for t_protocol dialogue management.

- TProtocolDialogue: The dialogue class maintains state of a dialogue and manages it.
- TProtocolDialogues: The dialogues class keeps track of all dialogues.
"""

from abc import ABC
from typing import Dict, FrozenSet, Optional, cast

from aea.helpers.dialogue.base import Dialogue, DialogueLabel, Dialogues
from aea.mail.base import Address
from aea.protocols.base import Message

from tests.data.generator.t_protocol.message import TProtocolMessage


class TProtocolDialogue(Dialogue):
    """The t_protocol dialogue class maintains state of a dialogue and manages it."""

    INITIAL_PERFORMATIVES = frozenset(
        {
            TProtocolMessage.Performative.PERFORMATIVE_CT,
            TProtocolMessage.Performative.PERFORMATIVE_PT,
        }
    )
    TERMINAL_PERFORMATIVES = frozenset(
        {
            TProtocolMessage.Performative.PERFORMATIVE_MT,
            TProtocolMessage.Performative.PERFORMATIVE_O,
            TProtocolMessage.Performative.PERFORMATIVE_EMPTY_CONTENTS,
        }
    )
    VALID_REPLIES = {
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
            {TProtocolMessage.Performative.PERFORMATIVE_PMT}
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
        agent_address: Optional[Address] = None,
        role: Optional[Dialogue.Role] = None,
    ) -> None:
        """
        Initialize a dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param agent_address: the address of the agent for whom this dialogue is maintained
        :param role: the role of the agent this dialogue is maintained for
        :return: None
        """
        Dialogue.__init__(
            self,
            dialogue_label=dialogue_label,
            agent_address=agent_address,
            role=role,
            rules=Dialogue.Rules(
                cast(FrozenSet[Message.Performative], self.INITIAL_PERFORMATIVES),
                cast(FrozenSet[Message.Performative], self.TERMINAL_PERFORMATIVES),
                cast(
                    Dict[Message.Performative, FrozenSet[Message.Performative]],
                    self.VALID_REPLIES,
                ),
            ),
        )

    def is_valid(self, message: Message) -> bool:
        """
        Check whether 'message' is a valid next message in the dialogue.

        These rules capture specific constraints designed for dialogues which are instances of a concrete sub-class of this class.
        Override this method with your additional dialogue rules.

        :param message: the message to be validated
        :return: True if valid, False otherwise
        """
        return True


class TProtocolDialogues(Dialogues, ABC):
    """This class keeps track of all t_protocol dialogues."""

    END_STATES = frozenset(
        {
            TProtocolDialogue.EndState.END_STATE_1,
            TProtocolDialogue.EndState.END_STATE_2,
            TProtocolDialogue.EndState.END_STATE_3,
        }
    )

    def __init__(self, agent_address: Address) -> None:
        """
        Initialize dialogues.

        :param agent_address: the address of the agent for whom dialogues are maintained
        :return: None
        """
        Dialogues.__init__(
            self,
            agent_address=agent_address,
            end_states=cast(FrozenSet[Dialogue.EndState], self.END_STATES),
        )

    def create_dialogue(
        self, dialogue_label: DialogueLabel, role: Dialogue.Role,
    ) -> TProtocolDialogue:
        """
        Create an instance of {} dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param role: the role of the agent this dialogue is maintained for

        :return: the created dialogue
        """
        dialogue = TProtocolDialogue(
            dialogue_label=dialogue_label, agent_address=self.agent_address, role=role
        )
        return dialogue
