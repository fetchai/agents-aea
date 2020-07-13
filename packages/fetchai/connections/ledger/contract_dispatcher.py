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

from aea.contracts import contract_registry
from aea.crypto.base import LedgerApi
from aea.crypto.registries import Registry
from aea.helpers.dialogue.base import (
    Dialogue as BaseDialogue,
    DialogueLabel as BaseDialogueLabel,
    Dialogues as BaseDialogues,
)
from aea.helpers.transaction.base import RawMessage, RawTransaction, State
from aea.protocols.base import Message

from packages.fetchai.connections.ledger.base import (
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
        """
        Infer the role of the agent from an incoming/outgoing first message.

        :param message: an incoming/outgoing first message
        :return: The role of the agent
        """
        return ContractApiDialogue.Role.LEDGER

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

    def __init__(self, *args, **kwargs):
        """Initialize the dispatcher."""
        super().__init__(*args, **kwargs)
        self._contract_api_dialogues = ContractApiDialogues()

    @property
    def dialogues(self) -> BaseDialogues:
        """Get the dialouges."""
        return self._contract_api_dialogues

    @property
    def contract_registry(self) -> Registry:
        """Get the contract registry."""
        return contract_registry

    def get_ledger_id(self, message: Message) -> str:
        """Get the ledger id."""
        assert isinstance(
            message, ContractApiMessage
        ), "argument is not a ContractApiMessage instance."
        message = cast(ContractApiMessage, message)
        return message.ledger_id

    def get_error_message(
        self, e: Exception, api: LedgerApi, message: Message, dialogue: BaseDialogue,
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
            code=500,
            message=str(e),
            data=b"",
        )
        response.counterparty = message.counterparty
        dialogue.update(response)
        return response

    def get_state(
        self,
        api: LedgerApi,
        message: ContractApiMessage,
        dialogue: ContractApiDialogue,
    ) -> ContractApiMessage:
        """
        Send the request 'get_state'.

        :param api: the API object.
        :param message: the Ledger API message
        :param dialogue: the contract API dialogue
        :return: None
        """
        contract = self.contract_registry.make(message.contract_id)
        method_to_call = getattr(contract, message.callable)
        try:
            data = method_to_call(api, message.contract_address, **message.kwargs.body)
            response = ContractApiMessage(
                performative=ContractApiMessage.Performative.STATE,
                message_id=message.message_id + 1,
                target=message.message_id,
                dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                state=State(message.ledger_id, data),
            )
            response.counterparty = message.counterparty
            dialogue.update(response)
        except Exception as e:  # pylint: disable=broad-except  # pragma: nocover
            response = self.get_error_message(e, api, message, dialogue)
        return response

    def get_deploy_transaction(
        self,
        api: LedgerApi,
        message: ContractApiMessage,
        dialogue: ContractApiDialogue,
    ) -> ContractApiMessage:
        """
        Send the request 'get_raw_transaction'.

        :param api: the API object.
        :param message: the Ledger API message
        :param dialogue: the contract API dialogue
        :return: None
        """
        contract = self.contract_registry.make(message.contract_id)
        method_to_call = getattr(contract, message.callable)
        try:
            tx = method_to_call(api, **message.kwargs.body)
            response = ContractApiMessage(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                message_id=message.message_id + 1,
                target=message.message_id,
                dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                raw_transaction=RawTransaction(message.ledger_id, tx),
            )
            response.counterparty = message.counterparty
            dialogue.update(response)
        except Exception as e:  # pylint: disable=broad-except  # pragma: nocover
            response = self.get_error_message(e, api, message, dialogue)
        return response

    def get_raw_transaction(
        self,
        api: LedgerApi,
        message: ContractApiMessage,
        dialogue: ContractApiDialogue,
    ) -> ContractApiMessage:
        """
        Send the request 'get_raw_transaction'.

        :param api: the API object.
        :param message: the Ledger API message
        :param dialogue: the contract API dialogue
        :return: None
        """
        contract = self.contract_registry.make(message.contract_id)
        method_to_call = getattr(contract, message.callable)
        try:
            tx = method_to_call(api, message.contract_address, **message.kwargs.body)
            response = ContractApiMessage(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                message_id=message.message_id + 1,
                target=message.message_id,
                dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                raw_transaction=RawTransaction(message.ledger_id, tx),
            )
            response.counterparty = message.counterparty
            dialogue.update(response)
        except Exception as e:  # pylint: disable=broad-except  # pragma: nocover
            response = self.get_error_message(e, api, message, dialogue)
        return response

    def get_raw_message(
        self,
        api: LedgerApi,
        message: ContractApiMessage,
        dialogue: ContractApiDialogue,
    ) -> ContractApiMessage:
        """
        Send the request 'get_raw_message'.

        :param api: the API object.
        :param message: the Ledger API message
        :param dialogue: the contract API dialogue
        :return: None
        """
        contract = self.contract_registry.make(message.contract_id)
        method_to_call = getattr(contract, message.callable)
        try:
            rm = method_to_call(api, message.contract_address, **message.kwargs.body)
            response = ContractApiMessage(
                performative=ContractApiMessage.Performative.RAW_MESSAGE,
                message_id=message.message_id + 1,
                target=message.message_id,
                dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                raw_message=RawMessage(message.ledger_id, rm),
            )
            response.counterparty = message.counterparty
            dialogue.update(response)
        except Exception as e:  # pylint: disable=broad-except  # pragma: nocover
            response = self.get_error_message(e, api, message, dialogue)
        return response
