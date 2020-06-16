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
from typing import Callable, List, Optional, cast

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

        self.receiving_tasks: List[asyncio.Task] = []
        self.done_tasks = deque()

    async def connect(self) -> None:
        """Set up the connection."""

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
        if type(envelope.message) == bytes:
            message = LedgerApiMessage.serializer.decode(envelope.message)
        else:
            message = envelope.message
        message = cast(LedgerApiMessage, message)
        api = aea.crypto.registries.make_ledger_api(message.ledger_id)
        task = self._dispatcher.dispatch(api, message)
        self.receiving_tasks.append(task)

    async def receive(self, *args, **kwargs) -> Optional["Envelope"]:
        """
        Receive an envelope. Blocking.

        :return: the envelope received, or None.
        """
        # if there are done tasks, return the result
        if len(self.done_tasks) > 0:
            envelope = self.done_tasks.pop().result()
            return envelope

        # wait for completion of at least one receiving task
        done, pending = await asyncio.wait(
            self.receiving_tasks, return_when=asyncio.FIRST_COMPLETED
        )

        # pick one done task
        envelope = done.pop().result() if len(done) > 0 else None

        # update done tasks
        self.done_tasks.extend(done)
        # update receiving tasks
        self.receiving_tasks[:] = pending

        return envelope


class _RequestDispatcher:
    def __init__(
        self, loop: asyncio.AbstractEventLoop, executor: Optional[Executor] = None
    ):
        """
        Initialize the request dispatcher.

        :param loop: the asyncio loop.
        :param executor: an executor.
        """
        self.loop = loop
        self.executor = executor

    async def run_async(self, func: Callable, *args):
        """
        Run a function in executor.

        :param func: the function to execute.
        :param args: the arguments to pass to the function.
        :return: the return value of the function.
        """
        return await self.loop.run_in_executor(self.executor, func, *args)

    def get_handler(
        self, performative: LedgerApiMessage.Performative
    ) -> Callable[[LedgerApi, LedgerApiMessage], Task]:
        """
        Get the handler method, given the message performative.

        :param performative: the message performative.
        :return: the method that will send the request.
        """
        handler = getattr(self, performative.value, lambda *args, **kwargs: None)
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

    def get_balance(self, api: LedgerApi, message: LedgerApiMessage):
        """
        Send the request 'get_balance'.

        :param api: the API object.
        :param message: the Ledger API message
        :return: None
        """
        # TODO wrapping synchronous calls with multithreading to make it asynchronous.
        #   LedgerApi async APIs would solve that.
        return api.get_balance(message.address)

    def get_transaction_receipt(self, api: LedgerApi, message: LedgerApiMessage):
        """
        Send the request 'get_transaction_receipt'.

        :param api: the API object.
        :param message: the Ledger API message
        :return: None
        """
        return api.get_transaction_receipt(message.tx_digest)

    def send_signed_transaction(self, api: LedgerApi, message: LedgerApiMessage):
        """
        Send the request 'send_signed_transaction'.

        :param api: the API object.
        :param message: the Ledger API message
        :return: None
        """
        return api.send_signed_transaction(message.signed_tx)

    def is_transaction_settled(self, api: LedgerApi, message: LedgerApiMessage):
        """
        Send the request 'is_transaction_settled'.

        :param api: the API object.
        :param message: the Ledger API message
        :return: None
        """
        return api.is_transaction_settled(message.tx_digest)

    def is_transaction_valid(self, api: LedgerApi, message: LedgerApiMessage):
        """
        Send the request 'is_transaction_valid'.

        :param api: the API object.
        :param message: the Ledger API message
        :return: None
        """
        # TODO remove?
        # return api.is_transaction_valid(message.tx_digest)
