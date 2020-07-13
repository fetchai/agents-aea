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

"""This module contains the implementation of the ledger API request dispatcher."""
import time
from typing import cast

from aea.crypto.base import LedgerApi
from aea.helpers.dialogue.base import (
    Dialogue as BaseDialogue,
    DialogueLabel as BaseDialogueLabel,
    Dialogues as BaseDialogues,
)
from aea.helpers.transaction.base import RawTransaction, TransactionDigest
from aea.protocols.base import Message

from packages.fetchai.connections.ledger.base import (
    CONNECTION_ID,
    RequestDispatcher,
)
from packages.fetchai.protocols.ledger_api.custom_types import TransactionReceipt
from packages.fetchai.protocols.ledger_api.dialogues import LedgerApiDialogue
from packages.fetchai.protocols.ledger_api.dialogues import (
    LedgerApiDialogues as BaseLedgerApiDialogues,
)
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage


class LedgerApiDialogues(BaseLedgerApiDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize dialogues.

        :return: None
        """
        BaseLedgerApiDialogues.__init__(self, str(CONNECTION_ID))

    @staticmethod
    def role_from_first_message(message: Message) -> BaseDialogue.Role:
        """
        Infer the role of the agent from an incoming/outgoing first message.

        :param message: an incoming/outgoing first message
        :return: The role of the agent
        """
        return LedgerApiDialogue.Role.LEDGER

    def create_dialogue(
        self, dialogue_label: BaseDialogueLabel, role: BaseDialogue.Role,
    ) -> LedgerApiDialogue:
        """
        Create an instance of ledger API dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param role: the role of the agent this dialogue is maintained for

        :return: the created dialogue
        """
        dialogue = LedgerApiDialogue(
            dialogue_label=dialogue_label, agent_address=str(CONNECTION_ID), role=role,
        )
        return dialogue


class LedgerApiRequestDispatcher(RequestDispatcher):
    """Implement ledger API request dispatcher."""

    def __init__(self, *args, **kwargs):
        """Initialize the dispatcher."""
        super().__init__(*args, **kwargs)
        self._ledger_api_dialogues = LedgerApiDialogues()

    def get_ledger_id(self, message: Message) -> str:
        """Get the ledger id from message."""
        assert isinstance(
            message, LedgerApiMessage
        ), "argument is not a LedgerApiMessage instance."
        message = cast(LedgerApiMessage, message)
        if message.performative is LedgerApiMessage.Performative.GET_RAW_TRANSACTION:
            ledger_id = message.terms.ledger_id
        elif (
            message.performative
            is LedgerApiMessage.Performative.SEND_SIGNED_TRANSACTION
        ):
            ledger_id = message.signed_transaction.ledger_id
        elif (
            message.performative
            is LedgerApiMessage.Performative.GET_TRANSACTION_RECEIPT
        ):
            ledger_id = message.transaction_digest.ledger_id
        else:
            ledger_id = message.ledger_id
        return ledger_id

    @property
    def dialogues(self) -> BaseDialogues:
        """Get the dialouges."""
        return self._ledger_api_dialogues

    def get_balance(
        self, api: LedgerApi, message: LedgerApiMessage, dialogue: LedgerApiDialogue,
    ) -> LedgerApiMessage:
        """
        Send the request 'get_balance'.

        :param api: the API object.
        :param message: the Ledger API message
        :return: None
        """
        balance = api.get_balance(message.address)
        if balance is None:
            response = self.get_error_message(
                ValueError("No balance returned"), api, message, dialogue
            )
        else:
            response = LedgerApiMessage(
                performative=LedgerApiMessage.Performative.BALANCE,
                message_id=message.message_id + 1,
                target=message.message_id,
                dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                balance=balance,
                ledger_id=message.ledger_id,
            )
            response.counterparty = message.counterparty
            dialogue.update(response)
        return response

    def get_raw_transaction(
        self, api: LedgerApi, message: LedgerApiMessage, dialogue: LedgerApiDialogue,
    ) -> LedgerApiMessage:
        """
        Send the request 'get_raw_transaction'.

        :param api: the API object.
        :param message: the Ledger API message
        :return: None
        """
        raw_transaction = api.get_transfer_transaction(
            sender_address=message.terms.sender_address,
            destination_address=message.terms.counterparty_address,
            amount=message.terms.sender_payable_amount,
            tx_fee=message.terms.fee,
            tx_nonce=message.terms.nonce,
            **message.terms.kwargs,
        )
        if raw_transaction is None:
            response = self.get_error_message(
                ValueError("No raw transaction returned"), api, message, dialogue
            )
        else:
            response = LedgerApiMessage(
                performative=LedgerApiMessage.Performative.RAW_TRANSACTION,
                message_id=message.message_id + 1,
                target=message.message_id,
                dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                raw_transaction=RawTransaction(
                    message.terms.ledger_id, raw_transaction
                ),
            )
            response.counterparty = message.counterparty
            dialogue.update(response)
        return response

    def get_transaction_receipt(
        self, api: LedgerApi, message: LedgerApiMessage, dialogue: LedgerApiDialogue,
    ) -> LedgerApiMessage:
        """
        Send the request 'get_transaction_receipt'.

        :param api: the API object.
        :param message: the Ledger API message
        :return: None
        """
        is_settled = False
        attempts = 0
        while (
            not is_settled
            and attempts < self.MAX_ATTEMPTS
            and self.connection_status.is_connected
        ):
            time.sleep(self.TIMEOUT)
            transaction_receipt = api.get_transaction_receipt(
                message.transaction_digest.body
            )
            is_settled = api.is_transaction_settled(transaction_receipt)
            attempts += 1
        attempts = 0
        transaction = api.get_transaction(message.transaction_digest.body)
        while (
            transaction is None
            and attempts < self.MAX_ATTEMPTS
            and self.connection_status.is_connected
        ):
            time.sleep(self.TIMEOUT)
            transaction = api.get_transaction(message.transaction_digest.body)
            attempts += 1
        if not is_settled:  # pragma: nocover
            response = self.get_error_message(
                ValueError("Transaction not settled within timeout"),
                api,
                message,
                dialogue,
            )
        elif transaction_receipt is None:  # pragma: nocover
            response = self.get_error_message(
                ValueError("No transaction_receipt returned"), api, message, dialogue
            )
        elif transaction is None:  # pragma: nocover
            response = self.get_error_message(
                ValueError("No tx returned"), api, message, dialogue
            )
        else:
            response = LedgerApiMessage(
                performative=LedgerApiMessage.Performative.TRANSACTION_RECEIPT,
                message_id=message.message_id + 1,
                target=message.message_id,
                dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                transaction_receipt=TransactionReceipt(
                    message.transaction_digest.ledger_id,
                    transaction_receipt,
                    transaction,
                ),
            )
            response.counterparty = message.counterparty
            dialogue.update(response)
        return response

    def send_signed_transaction(
        self, api: LedgerApi, message: LedgerApiMessage, dialogue: LedgerApiDialogue,
    ) -> LedgerApiMessage:
        """
        Send the request 'send_signed_tx'.

        :param api: the API object.
        :param message: the Ledger API message
        :return: None
        """
        transaction_digest = api.send_signed_transaction(
            message.signed_transaction.body
        )
        if transaction_digest is None:  # pragma: nocover
            response = self.get_error_message(
                ValueError("No transaction_digest returned"), api, message, dialogue
            )
        else:
            response = LedgerApiMessage(
                performative=LedgerApiMessage.Performative.TRANSACTION_DIGEST,
                message_id=message.message_id + 1,
                target=message.message_id,
                dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                transaction_digest=TransactionDigest(
                    message.signed_transaction.ledger_id, transaction_digest
                ),
            )
            response.counterparty = message.counterparty
            dialogue.update(response)
        return response

    def get_error_message(
        self, e: Exception, api: LedgerApi, message: Message, dialogue: BaseDialogue,
    ) -> LedgerApiMessage:
        """
        Build an error message.

        :param e: the exception.
        :param api: the Ledger API.
        :param message: the request message.
        :return: an error message response.
        """
        message = cast(LedgerApiMessage, message)
        dialogue = cast(LedgerApiDialogue, dialogue)
        response = LedgerApiMessage(
            performative=LedgerApiMessage.Performative.ERROR,
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
