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
from concurrent.futures.thread import ThreadPoolExecutor
from typing import Deque, Dict, List, Optional

from aea.connections.base import Connection
from aea.mail.base import Envelope
from aea.protocols.base import Message

from packages.fetchai.connections.ledger.base import (
    CONNECTION_ID,
    RequestDispatcher,
)
from packages.fetchai.connections.ledger.contract_dispatcher import (
    ContractApiRequestDispatcher,
)
from packages.fetchai.connections.ledger.ledger_dispatcher import (
    LedgerApiRequestDispatcher,
)
from packages.fetchai.protocols.contract_api import ContractApiMessage
from packages.fetchai.protocols.ledger_api import LedgerApiMessage


class LedgerConnection(Connection):
    """Proxy to the functionality of the SDK or API."""

    connection_id = CONNECTION_ID

    def __init__(self, **kwargs):
        """
        Initialize a connection to interact with a ledger APIs.

        """
        super().__init__(**kwargs)

        # TODO make the max number of workers configurable
        self._executor: Optional[ThreadPoolExecutor] = None
        self._ledger_dispatcher: Optional[LedgerApiRequestDispatcher] = None
        self._contract_dispatcher: Optional[ContractApiRequestDispatcher] = None

        self.receiving_tasks: List[asyncio.Future] = []
        self.task_to_request: Dict[asyncio.Future, Envelope] = {}
        self.done_tasks: Deque[asyncio.Future] = deque()
        self.api_configs = self.configuration.config.get(
            "ledger_apis", {}
        )  # type: Dict[str, Dict[str, str]]

    async def connect(self) -> None:
        """Set up the connection."""
        self._executor = ThreadPoolExecutor(max_workers=None)
        self._ledger_dispatcher = LedgerApiRequestDispatcher(
            loop=self.loop,
            executor=self._executor,
            api_configs=self.api_configs,
        )
        self._contract_dispatcher = ContractApiRequestDispatcher(
            loop=self.loop,
            executor=self._executor,
            api_configs=self.api_configs,
        )
        self.connection_status.is_connected = True

    async def disconnect(self) -> None:
        """Tear down the connection."""
        self.connection_status.is_connected = False
        for task in self.receiving_tasks:
            if not task.cancelled():
                task.cancel()
        self._executor.shutdown(wait=True)
        self._executor = None
        self._ledger_dispatcher = None
        self._contract_dispatcher = None

    async def send(self, envelope: "Envelope") -> None:
        """
        Send an envelope.

        :param envelope: the envelope to send.
        :return: None
        """
        if self.connection_status.is_connected:
            task = await self._schedule_request(envelope)
            self.receiving_tasks.append(task)
            self.task_to_request[task] = envelope

    async def _schedule_request(self, envelope: Envelope) -> Task:
        """
        Schedule a ledger API request.

        :param envelope: the message.
        :return: None
        """
        dispatcher: RequestDispatcher
        if envelope.protocol_id == LedgerApiMessage.protocol_id:
            assert self._ledger_dispatcher is not None
            dispatcher = self._ledger_dispatcher
        elif envelope.protocol_id == ContractApiMessage.protocol_id:
            assert self._contract_dispatcher is not None
            dispatcher = self._contract_dispatcher
        else:
            raise ValueError("Protocol not supported")

        task = dispatcher.dispatch(envelope)
        return task

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
        response_message: Optional[Message] = task.result()

        response_envelope = None
        if response_message is not None:
            response_envelope = Envelope(
                to=request.sender,
                sender=request.to,
                protocol_id=response_message.protocol_id,
                message=response_message,
            )
        return response_envelope
