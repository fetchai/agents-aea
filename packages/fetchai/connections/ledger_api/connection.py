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

"""Scaffold connection and channel."""
import asyncio
import time
from asyncio import Task
from collections import deque
from concurrent.futures import Executor
from typing import Callable, Deque, Dict, List, Optional, cast

import aea
from aea.configurations.base import ConnectionConfig, PublicId
from aea.connections.base import Connection
from aea.crypto.base import LedgerApi
from aea.crypto.wallet import CryptoStore
from aea.helpers.dialogue.base import Dialogue as BaseDialogue
from aea.helpers.dialogue.base import DialogueLabel as BaseDialogueLabel
from aea.helpers.transaction.base import RawTransaction
from aea.identity.base import Identity
from aea.mail.base import Envelope
from aea.protocols.base import Message

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
        BaseLedgerApiDialogues.__init__(self, str(LedgerApiConnection.connection_id))

    @staticmethod
    def role_from_first_message(message: Message) -> BaseDialogue.Role:
        """Infer the role of the agent from an incoming/outgoing first message

        :param message: an incoming/outgoing first message
        :return: The role of the agent
        """
        return LedgerApiDialogue.AgentRole.LEDGER

    def create_dialogue(
        self, dialogue_label: BaseDialogueLabel, role: BaseDialogue.Role,
    ) -> LedgerApiDialogue:
        """
        Create an instance of fipa dialogue.

        :param dialogue_label: the identifier of the dialogue
        :param role: the role of the agent this dialogue is maintained for

        :return: the created dialogue
        """
        dialogue = LedgerApiDialogue(
            dialogue_label=dialogue_label,
            agent_address=str(LedgerApiConnection.connection_id),
            role=role,
        )
        return dialogue


class _RequestDispatcher:

    TIMEOUT = 3
    MAX_ATTEMPTS = 120

    def __init__(
        self,
        loop: Optional[asyncio.AbstractEventLoop],
        executor: Optional[Executor] = None,
    ):
        """
        Initialize the request dispatcher.

        :param loop: the asyncio loop.
        :param executor: an executor.
        """
        self.loop = loop if loop is not None else asyncio.get_event_loop()
        self.executor = executor
        self.ledger_api_dialogues = LedgerApiDialogues()

    async def run_async(
        self,
        func: Callable[[LedgerApi, LedgerApiMessage, LedgerApiDialogue], Task],
        *args
    ):
        """
        Run a function in executor.

        :param func: the function to execute.
        :param args: the arguments to pass to the function.
        :return: the return value of the function.
        """
        try:
            response = await self.loop.run_in_executor(self.executor, func, *args)
            return response
        except Exception as e:
            return self.get_error_message(e, *args)

    def get_handler(
        self, performative: LedgerApiMessage.Performative
    ) -> Callable[[LedgerApi, LedgerApiMessage, LedgerApiDialogue], Task]:
        """
        Get the handler method, given the message performative.

        :param performative: the message performative.
        :return: the method that will send the request.
        """
        handler = getattr(self, performative.value, lambda *args, **kwargs: None)
        if handler is None:
            raise Exception("Performative not recognized.")
        return handler

    def dispatch(self, api: LedgerApi, message: LedgerApiMessage) -> Task:
        """
        Dispatch the request to the right sender handler.

        :param api: the ledger api.
        :param message: the request message.
        :return: an awaitable.
        """
        message.is_incoming = True
        dialogue = self.ledger_api_dialogues.update(message)
        assert dialogue is not None, "No dialogue created."
        performative = cast(LedgerApiMessage.Performative, message.performative)
        handler = self.get_handler(performative)
        return self.loop.create_task(self.run_async(handler, api, message, dialogue))

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
        while not is_settled and attempts < self.MAX_ATTEMPTS:
            time.sleep(self.TIMEOUT)
            transaction_receipt = api.get_transaction_receipt(
                message.transaction_digest
            )
            is_settled = api.is_transaction_settled(transaction_receipt)
            attempts += 1
        attempts = 0
        transaction = api.get_transaction(message.transaction_digest)
        while transaction is None and attempts < self.MAX_ATTEMPTS:
            time.sleep(self.TIMEOUT)
            transaction = api.get_transaction(message.transaction_digest)
            attempts += 1
        if not is_settled:
            response = self.get_error_message(
                ValueError("Transaction not settled within timeout"),
                api,
                message,
                dialogue,
            )
        elif transaction_receipt is None:
            response = self.get_error_message(
                ValueError("No transaction_receipt returned"), api, message, dialogue
            )
        elif transaction is None:
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
                    message.ledger_id, transaction_receipt, transaction
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
        if transaction_digest is None:
            response = self.get_error_message(
                ValueError("No transaction_digest returned"), api, message, dialogue
            )
        else:
            response = LedgerApiMessage(
                performative=LedgerApiMessage.Performative.TRANSACTION_DIGEST,
                message_id=message.message_id + 1,
                target=message.message_id,
                dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                ledger_id=message.signed_transaction.ledger_id,
                transaction_digest=transaction_digest,
            )
            response.counterparty = message.counterparty
            dialogue.update(response)
        return response

    def get_error_message(
        self,
        e: Exception,
        api: LedgerApi,
        message: LedgerApiMessage,
        dialogue: LedgerApiDialogue,
    ) -> LedgerApiMessage:
        """
        Build an error message.

        :param e: the exception.
        :param api: the Ledger API.
        :param message: the request message.
        :return: an error message response.
        """
        response = LedgerApiMessage(
            performative=LedgerApiMessage.Performative.ERROR,
            message_id=message.message_id + 1,
            target=message.message_id,
            dialogue_reference=dialogue.dialogue_label.dialogue_reference,
            message=str(e),
        )
        response.counterparty = message.counterparty
        dialogue.update(response)
        return response


class LedgerApiConnection(Connection):
    """Proxy to the functionality of the SDK or API."""

    connection_id = PublicId.from_str("fetchai/ledger_api:0.1.0")

    def __init__(
        self,
        configuration: ConnectionConfig,
        identity: Identity,
        crypto_store: CryptoStore,
    ):
        """
        Initialize a connection to interact with a ledger APIs.

        :param configuration: the connection configuration.
        :param crypto_store: object to access the connection crypto objects.
        :param identity: the identity object.
        """
        super().__init__(
            configuration=configuration, crypto_store=crypto_store, identity=identity
        )

        self._dispatcher = None  # type: Optional[_RequestDispatcher]

        self.receiving_tasks: List[asyncio.Future] = []
        self.task_to_request: Dict[asyncio.Future, Envelope] = {}
        self.done_tasks: Deque[asyncio.Future] = deque()

    @property
    def dispatcher(self) -> _RequestDispatcher:
        """Get the dispatcher."""
        assert self._dispatcher is not None, "_RequestDispatcher not set!"
        return self._dispatcher

    async def connect(self) -> None:
        """Set up the connection."""
        self._dispatcher = _RequestDispatcher(self.loop)
        self.connection_status.is_connected = True

    async def disconnect(self) -> None:
        """Tear down the connection."""
        for task in self.receiving_tasks:
            if not task.cancelled():
                task.cancel()
        self.connection_status.is_connected = False
        self._dispatcher = None

    async def send(self, envelope: "Envelope") -> None:
        """
        Send an envelope.

        :param envelope: the envelope to send.
        :return: None
        """
        if isinstance(envelope.message, bytes):
            message = cast(
                LedgerApiMessage,
                LedgerApiMessage.serializer.decode(envelope.message_bytes),
            )
        else:
            message = cast(LedgerApiMessage, envelope.message)
        if message.performative is LedgerApiMessage.Performative.GET_RAW_TRANSACTION:
            ledger_id = message.terms.ledger_id
        elif (
            message.performative
            is LedgerApiMessage.Performative.SEND_SIGNED_TRANSACTION
        ):
            ledger_id = message.signed_transaction.ledger_id
        else:
            ledger_id = message.ledger_id
        api = aea.crypto.registries.make_ledger_api(ledger_id)
        task = self.dispatcher.dispatch(api, message)
        self.receiving_tasks.append(task)
        self.task_to_request[task] = envelope

    async def receive(self, *args, **kwargs) -> Optional["Envelope"]:
        """
        Receive an envelope. Blocking.

        :return: the envelope received, or None.
        """
        # if there are done tasks, return the result
        if len(self.done_tasks) > 0:
            done_task = self.done_tasks.pop()
            return self._handle_done_task(done_task)

        if not self.receiving_tasks:
            return None

        # wait for completion of at least one receiving task
        done, pending = await asyncio.wait(
            self.receiving_tasks, return_when=asyncio.FIRST_COMPLETED
        )

        # pick one done task
        done_task = done.pop()

        # update done tasks
        self.done_tasks.extend([*done])
        # update receiving tasks
        self.receiving_tasks[:] = pending

        return self._handle_done_task(done_task)

    def _handle_done_task(self, task: asyncio.Future) -> Optional[Envelope]:
        """
        Process a done receiving task.

        :param task: the done task.
        :return: the reponse envelope.
        """
        request = self.task_to_request.pop(task)
        response_message: Optional[LedgerApiMessage] = task.result()

        response_envelope = None
        if response_message is not None:
            response_envelope = Envelope(
                to=request.sender,
                sender=request.to,
                protocol_id=response_message.protocol_id,
                message=response_message,
            )
        return response_envelope
