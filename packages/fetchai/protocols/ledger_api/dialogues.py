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
This module contains the classes required for ledger_api dialogue management.

- LedgerApiDialogue: The dialogue class maintains state of a dialogue and manages it.
- LedgerApiDialogues: The dialogues class keeps track of all dialogues.
"""

from abc import ABC
from typing import Callable, Dict, FrozenSet, Type, cast

from aea.common import Address
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue, DialogueLabel, Dialogues

from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage


class LedgerApiDialogue(Dialogue):
    """The ledger_api dialogue class maintains state of a dialogue and manages it."""

    INITIAL_PERFORMATIVES: FrozenSet[Message.Performative] = frozenset(
        {
            LedgerApiMessage.Performative.GET_BALANCE,
            LedgerApiMessage.Performative.GET_STATE,
            LedgerApiMessage.Performative.GET_RAW_TRANSACTION,
            LedgerApiMessage.Performative.SEND_SIGNED_TRANSACTION,
            LedgerApiMessage.Performative.GET_TRANSACTION_RECEIPT,
        }
    )
    TERMINAL_PERFORMATIVES: FrozenSet[Message.Performative] = frozenset(
        {
            LedgerApiMessage.Performative.BALANCE,
            LedgerApiMessage.Performative.STATE,
            LedgerApiMessage.Performative.TRANSACTION_RECEIPT,
            LedgerApiMessage.Performative.ERROR,
        }
    )
    VALID_REPLIES: Dict[Message.Performative, FrozenSet[Message.Performative]] = {
        LedgerApiMessage.Performative.BALANCE: frozenset(),
        LedgerApiMessage.Performative.ERROR: frozenset(),
        LedgerApiMessage.Performative.GET_BALANCE: frozenset(
            {LedgerApiMessage.Performative.BALANCE, LedgerApiMessage.Performative.ERROR}
        ),
        LedgerApiMessage.Performative.GET_RAW_TRANSACTION: frozenset(
            {
                LedgerApiMessage.Performative.RAW_TRANSACTION,
                LedgerApiMessage.Performative.ERROR,
            }
        ),
        LedgerApiMessage.Performative.GET_STATE: frozenset(
            {LedgerApiMessage.Performative.STATE, LedgerApiMessage.Performative.ERROR}
        ),
        LedgerApiMessage.Performative.GET_TRANSACTION_RECEIPT: frozenset(
            {
                LedgerApiMessage.Performative.TRANSACTION_RECEIPT,
                LedgerApiMessage.Performative.ERROR,
            }
        ),
        LedgerApiMessage.Performative.RAW_TRANSACTION: frozenset(
            {LedgerApiMessage.Performative.SEND_SIGNED_TRANSACTION}
        ),
        LedgerApiMessage.Performative.SEND_SIGNED_TRANSACTION: frozenset(
            {
                LedgerApiMessage.Performative.TRANSACTION_DIGEST,
                LedgerApiMessage.Performative.ERROR,
            }
        ),
        LedgerApiMessage.Performative.STATE: frozenset(),
        LedgerApiMessage.Performative.TRANSACTION_DIGEST: frozenset(
            {LedgerApiMessage.Performative.GET_TRANSACTION_RECEIPT}
        ),
        LedgerApiMessage.Performative.TRANSACTION_RECEIPT: frozenset(),
    }

    class Role(Dialogue.Role):
        """This class defines the agent's role in a ledger_api dialogue."""

        AGENT = "agent"
        LEDGER = "ledger"

    class EndState(Dialogue.EndState):
        """This class defines the end states of a ledger_api dialogue."""

        SUCCESSFUL = 0

    def __init__(
        self,
        dialogue_label: DialogueLabel,
        self_address: Address,
        role: Dialogue.Role,
        message_class: Type[LedgerApiMessage] = LedgerApiMessage,
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


class LedgerApiDialogues(Dialogues, ABC):
    """This class keeps track of all ledger_api dialogues."""

    END_STATES = frozenset({LedgerApiDialogue.EndState.SUCCESSFUL})

    _keep_terminal_state_dialogues = False

    def __init__(
        self,
        self_address: Address,
        role_from_first_message: Callable[[Message, Address], Dialogue.Role],
        dialogue_class: Type[LedgerApiDialogue] = LedgerApiDialogue,
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
            message_class=LedgerApiMessage,
            dialogue_class=dialogue_class,
            role_from_first_message=role_from_first_message,
        )
