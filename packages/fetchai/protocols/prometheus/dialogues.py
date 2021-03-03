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
This module contains the classes required for prometheus dialogue management.

- PrometheusDialogue: The dialogue class maintains state of a dialogue and manages it.
- PrometheusDialogues: The dialogues class keeps track of all dialogues.
"""

from abc import ABC
from typing import Callable, FrozenSet, Type, cast

from aea.common import Address
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue, DialogueLabel, Dialogues

from packages.fetchai.protocols.prometheus.message import PrometheusMessage


class PrometheusDialogue(Dialogue):
    """The prometheus dialogue class maintains state of a dialogue and manages it."""

    INITIAL_PERFORMATIVES = frozenset(
        {
            PrometheusMessage.Performative.ADD_METRIC,
            PrometheusMessage.Performative.UPDATE_METRIC,
        }
    )
    TERMINAL_PERFORMATIVES = frozenset({PrometheusMessage.Performative.RESPONSE})
    VALID_REPLIES = {
        PrometheusMessage.Performative.ADD_METRIC: frozenset(
            {PrometheusMessage.Performative.RESPONSE}
        ),
        PrometheusMessage.Performative.RESPONSE: frozenset(),
        PrometheusMessage.Performative.UPDATE_METRIC: frozenset(
            {PrometheusMessage.Performative.RESPONSE}
        ),
    }

    class Role(Dialogue.Role):
        """This class defines the agent's role in a prometheus dialogue."""

        AGENT = "agent"
        SERVER = "server"

    class EndState(Dialogue.EndState):
        """This class defines the end states of a prometheus dialogue."""

        SUCCESSFUL = 0

    def __init__(
        self,
        dialogue_label: DialogueLabel,
        self_address: Address,
        role: Dialogue.Role,
        message_class: Type[PrometheusMessage] = PrometheusMessage,
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


class PrometheusDialogues(Dialogues, ABC):
    """This class keeps track of all prometheus dialogues."""

    END_STATES = frozenset({PrometheusDialogue.EndState.SUCCESSFUL})

    _keep_terminal_state_dialogues = False

    def __init__(
        self,
        self_address: Address,
        role_from_first_message: Callable[[Message, Address], Dialogue.Role],
        dialogue_class: Type[PrometheusDialogue] = PrometheusDialogue,
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
            message_class=PrometheusMessage,
            dialogue_class=dialogue_class,
            role_from_first_message=role_from_first_message,
        )
