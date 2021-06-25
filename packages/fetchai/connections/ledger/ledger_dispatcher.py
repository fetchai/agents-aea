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
import logging
import time
from typing import Any, cast

from aea.connections.base import ConnectionStates
from aea.crypto.base import LedgerApi
from aea.helpers.transaction.base import RawTransaction, State, TransactionDigest
from aea.protocols.base import Address, Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue
from aea.protocols.dialogue.base import Dialogues as BaseDialogues

from packages.fetchai.connections.ledger.base import CONNECTION_ID, RequestDispatcher
from packages.fetchai.protocols.ledger_api.custom_types import TransactionReceipt
from packages.fetchai.protocols.ledger_api.dialogues import LedgerApiDialogue
from packages.fetchai.protocols.ledger_api.dialogues import (
    LedgerApiDialogues as BaseLedgerApiDialogues,
)
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage


_default_logger = logging.getLogger(
    "aea.packages.fetchai.connections.ledger.ledger_dispatcher"
)


class LedgerApiDialogues(BaseLedgerApiDialogues):
    """The dialogues class keeps track of all dialogues."""

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize dialogues.

        :param kwargs: keyword arguments
        """

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> BaseDialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            # The ledger connection maintains the dialogue on behalf of the ledger
            return LedgerApiDialogue.Role.LEDGER

        BaseLedgerApiDialogues.__init__(
            self,
            self_address=str(CONNECTION_ID),
            role_from_first_message=role_from_first_message,
            **kwargs,
        )


class LedgerApiRequestDispatcher(RequestDispatcher):
    """Implement ledger API request dispatcher."""

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        """Initialize the dispatcher."""
        logger = kwargs.pop("logger", None)
        logger = logger if logger is not None else _default_logger
        super().__init__(logger, *args, **kwargs)
        self._ledger_api_dialogues = LedgerApiDialogues()

    def get_ledger_id(self, message: Message) -> str:
        """Get the ledger id from message."""
        if not isinstance(message, LedgerApiMessage):  # pragma: nocover
            raise ValueError("argument is not a LedgerApiMessage instance.")
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
        """Get the dialogues."""
        return self._ledger_api_dialogues

    def get_balance(
        self, api: LedgerApi, message: LedgerApiMessage, dialogue: LedgerApiDialogue,
    ) -> LedgerApiMessage:
        """
        Send the request 'get_balance'.

        :param api: the API object.
        :param message: the Ledger API message
        :param dialogue: the dialogue
        :return: the ledger api message
        """
        balance = api.get_balance(message.address)
        if balance is None:
            response = self.get_error_message(
                ValueError("No balance returned"), api, message, dialogue
            )
        else:
            response = cast(
                LedgerApiMessage,
                dialogue.reply(
                    performative=LedgerApiMessage.Performative.BALANCE,
                    target_message=message,
                    balance=balance,
                    ledger_id=message.ledger_id,
                ),
            )
        return response

    def get_state(
        self, api: LedgerApi, message: LedgerApiMessage, dialogue: LedgerApiDialogue,
    ) -> LedgerApiMessage:
        """
        Send the request 'get_state'.

        :param api: the API object.
        :param message: the Ledger API message
        :param dialogue: the dialogue
        :return: the ledger api message
        """
        result = api.get_state(message.callable, *message.args, **message.kwargs.body)
        if result is None:  # pragma: nocover
            response = self.get_error_message(
                ValueError("Failed to get state"), api, message, dialogue
            )
        else:
            response = cast(
                LedgerApiMessage,
                dialogue.reply(
                    performative=LedgerApiMessage.Performative.STATE,
                    target_message=message,
                    state=State(message.ledger_id, result),
                    ledger_id=message.ledger_id,
                ),
            )
        return response

    def get_raw_transaction(
        self, api: LedgerApi, message: LedgerApiMessage, dialogue: LedgerApiDialogue,
    ) -> LedgerApiMessage:
        """
        Send the request 'get_raw_transaction'.

        :param api: the API object.
        :param message: the Ledger API message
        :param dialogue: the dialogue
        :return: the ledger api message
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
            response = cast(
                LedgerApiMessage,
                dialogue.reply(
                    performative=LedgerApiMessage.Performative.RAW_TRANSACTION,
                    target_message=message,
                    raw_transaction=RawTransaction(
                        message.terms.ledger_id, raw_transaction
                    ),
                ),
            )
        return response

    def get_transaction_receipt(
        self, api: LedgerApi, message: LedgerApiMessage, dialogue: LedgerApiDialogue,
    ) -> LedgerApiMessage:
        """
        Send the request 'get_transaction_receipt'.

        :param api: the API object.
        :param message: the Ledger API message
        :param dialogue: the dialogue
        :return: the ledger api message
        """
        is_settled = False
        attempts = 0
        while (
            not is_settled
            and attempts < self.MAX_ATTEMPTS
            and self.connection_state.get() == ConnectionStates.connected
        ):
            time.sleep(self.TIMEOUT)
            transaction_receipt = api.get_transaction_receipt(
                message.transaction_digest.body
            )
            if transaction_receipt is not None:
                is_settled = api.is_transaction_settled(transaction_receipt)
            attempts += 1
        attempts = 0
        transaction = api.get_transaction(message.transaction_digest.body)
        while (
            transaction is None
            and attempts < self.MAX_ATTEMPTS
            and self.connection_state.get() == ConnectionStates.connected
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
                ValueError("No transaction returned"), api, message, dialogue
            )
        else:
            response = cast(
                LedgerApiMessage,
                dialogue.reply(
                    performative=LedgerApiMessage.Performative.TRANSACTION_RECEIPT,
                    target_message=message,
                    transaction_receipt=TransactionReceipt(
                        message.transaction_digest.ledger_id,
                        transaction_receipt,
                        transaction,
                    ),
                ),
            )
        return response

    def send_signed_transaction(
        self, api: LedgerApi, message: LedgerApiMessage, dialogue: LedgerApiDialogue,
    ) -> LedgerApiMessage:
        """
        Send the request 'send_signed_tx'.

        :param api: the API object.
        :param message: the Ledger API message
        :param dialogue: the dialogue
        :return: the ledger api message
        """
        transaction_digest = api.send_signed_transaction(
            message.signed_transaction.body
        )
        if transaction_digest is None:  # pragma: nocover
            response = self.get_error_message(
                ValueError("No transaction_digest returned"), api, message, dialogue
            )
        else:
            response = cast(
                LedgerApiMessage,
                dialogue.reply(
                    performative=LedgerApiMessage.Performative.TRANSACTION_DIGEST,
                    target_message=message,
                    transaction_digest=TransactionDigest(
                        message.signed_transaction.ledger_id, transaction_digest
                    ),
                ),
            )
        return response

    def get_error_message(
        self, e: Exception, api: LedgerApi, message: Message, dialogue: BaseDialogue,
    ) -> LedgerApiMessage:
        """
        Build an error message.

        :param e: the exception.
        :param api: the Ledger API.
        :param message: the request message.
        :param dialogue: the dialogue
        :return: an error message response.
        """
        message = cast(LedgerApiMessage, message)
        dialogue = cast(LedgerApiDialogue, dialogue)
        response = cast(
            LedgerApiMessage,
            dialogue.reply(
                performative=LedgerApiMessage.Performative.ERROR,
                target_message=message,
                code=500,
                message=str(e),
                data=b"",
            ),
        )
        return response
