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

"""This module contains the implementation of the contract API request dispatcher."""
from typing import cast

import aea
from aea.contracts import Contract
from aea.crypto.registries import Registry
from aea.helpers.dialogue.base import (
    Dialogue as BaseDialogue,
    DialogueLabel as BaseDialogueLabel,
    Dialogues as BaseDialogues,
)
from aea.mail.base import Envelope
from aea.protocols.base import Message

from packages.fetchai.connections.ledger_api.base import (
    CONNECTION_ID,
    RequestDispatcher,
)
from packages.fetchai.protocols.contract_api import ContractApiMessage
from packages.fetchai.protocols.contract_api.dialogues import ContractApiDialogue
from packages.fetchai.protocols.contract_api.dialogues import (
    ContractApiDialogues as BaseContractApiDialogues,
)


class ContractApiDialogues(BaseContractApiDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize dialogues.

        :return: None
        """
        BaseContractApiDialogues.__init__(self, str(CONNECTION_ID))

    @staticmethod
    def role_from_first_message(message: Message) -> BaseDialogue.Role:
        """Infer the role of the agent from an incoming/outgoing first message

        :param message: an incoming/outgoing first message
        :return: The role of the agent
        """
        return ContractApiDialogue.AgentRole.LEDGER

    def create_dialogue(
        self, dialogue_label: BaseDialogueLabel, role: BaseDialogue.Role,
    ) -> ContractApiDialogue:
        """
        Create an instance of contract API dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param role: the role of the agent this dialogue is maintained for

        :return: the created dialogue
        """
        dialogue = ContractApiDialogue(
            dialogue_label=dialogue_label, agent_address=str(CONNECTION_ID), role=role,
        )
        return dialogue


class ContractApiRequestDispatcher(RequestDispatcher):
    """Implement the contract API request dispatcher."""

    def __init__(self, **kwargs):
        """Initialize the dispatcher."""
        super().__init__(**kwargs)
        self._contract_api_dialogues = ContractApiDialogues()

    @property
    def dialogues(self) -> BaseDialogues:
        """Get the dialouges."""
        return self._contract_api_dialogues

    @property
    def registry(self) -> Registry:
        return aea.contracts.contract_registry

    def get_message(self, envelope: Envelope) -> Message:
        if isinstance(envelope.message, bytes):
            message = cast(
                ContractApiMessage,
                ContractApiMessage.serializer.decode(envelope.message_bytes),
            )
        else:
            message = cast(ContractApiMessage, envelope.message)
        return message

    def get_ledger_id(self, message: Message) -> str:
        assert isinstance(
            message, ContractApiMessage
        ), "argument is not a ContractApiMessage instance."
        message = cast(ContractApiMessage, message)
        return message.ledger_id

    def get_error_message(  # type: ignore
        self,
        e: Exception,
        api: Contract,
        message: ContractApiMessage,
        dialogue: ContractApiDialogue,
    ) -> ContractApiMessage:
        """
        Build an error message.

        :param e: the exception.
        :param api: the Ledger API.
        :param message: the request message.
        :return: an error message response.
        """
        response = ContractApiMessage(
            performative=ContractApiMessage.Performative.ERROR,
            message_id=message.message_id + 1,
            target=message.message_id,
            dialogue_reference=dialogue.dialogue_label.dialogue_reference,
            message=str(e),
        )
        response.counterparty = message.counterparty
        dialogue.update(response)
        return response
