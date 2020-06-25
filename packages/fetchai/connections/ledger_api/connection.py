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
from asyncio import Task
from collections import deque
from concurrent.futures import Executor
from typing import Callable, Deque, Dict, List, Optional, cast

import aea
from aea.configurations.base import ConnectionConfig, PublicId
from aea.connections.base import Connection
from aea.crypto.base import LedgerApi
from aea.crypto.wallet import CryptoStore
from aea.identity.base import Identity
from aea.mail.base import Envelope

from packages.fetchai.protocols.ledger_api import LedgerApiMessage


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

        self._dispatcher = _RequestDispatcher(self.loop)

        self.receiving_tasks: List[asyncio.Future] = []
        self.task_to_request: Dict[asyncio.Future, Envelope] = {}
        self.done_tasks: Deque[asyncio.Future] = deque()

    async def connect(self) -> None:
        """Set up the connection."""
        self.connection_status.is_connected = True

    async def disconnect(self) -> None:
        """Tear down the connection."""
        for task in self.receiving_tasks:
            if not task.cancelled():
                task.cancel()

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
        api = aea.crypto.registries.make_ledger_api(message.ledger_id)
        task = self._dispatcher.dispatch(api, message)
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

        # wait for completion of at least one receiving task
        done, pending = await asyncio.wait(
            self.receiving_tasks, return_when=asyncio.FIRST_COMPLETED
        )

        if len(done) == 0:
            return None

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
        request_message = cast(LedgerApiMessage, request.message)
        response_message: Optional[LedgerApiMessage] = task.result()

        response_envelope = None
        if response_message is not None:
            response_envelope = Envelope(
                to=self.address,
                sender=request_message.ledger_id,
                protocol_id=response_message.protocol_id,
                message=response_message,
            )
        return response_envelope


class _RequestDispatcher:
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

    async def run_async(
        self, func: Callable[[LedgerApi, LedgerApiMessage], Task], *args
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
    ) -> Callable[[LedgerApi, LedgerApiMessage], Task]:
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
        performative = cast(LedgerApiMessage.Performative, message.performative)
        handler = self.get_handler(performative)
        return self.loop.create_task(self.run_async(handler, api, message))

    def get_balance(
        self, api: LedgerApi, message: LedgerApiMessage
    ) -> LedgerApiMessage:
        """
        Send the request 'get_balance'.

        :param api: the API object.
        :param message: the Ledger API message
        :return: None
        """
        balance = api.get_balance(message.address)
        response = LedgerApiMessage(
            LedgerApiMessage.Performative.BALANCE, amount=balance,
        )
        return response

    def get_transaction_receipt(
        self, api: LedgerApi, message: LedgerApiMessage
    ) -> LedgerApiMessage:
        """
        Send the request 'get_transaction_receipt'.

        :param api: the API object.
        :param message: the Ledger API message
        :return: None
        """
        tx_receipt = api.get_transaction_receipt(message.transaction_digest)
        return LedgerApiMessage(
            performative=LedgerApiMessage.Performative.TRANSACTION_RECEIPT,
            data=tx_receipt,
        )

    def send_signed_tx(
        self, api: LedgerApi, message: LedgerApiMessage
    ) -> LedgerApiMessage:
        """
        Send the request 'send_signed_tx'.

        :param api: the API object.
        :param message: the Ledger API message
        :return: None
        """
        tx_digest = api.send_signed_transaction(message.signed_transaction.any)
        return LedgerApiMessage(
            performative=LedgerApiMessage.Performative.TRANSACTION_DIGEST,
            digest=tx_digest,
        )

    def get_error_message(
        self, e: Exception, api: LedgerApi, message: LedgerApiMessage
    ) -> LedgerApiMessage:
        """
        Build an error message.

        :param e: the exception.
        :param api: the Ledger API.
        :param message: the request message.
        :return: an error message response.
        """
        response = LedgerApiMessage(
            performative=LedgerApiMessage.Performative.ERROR, message=str(e)
        )
        return response
