# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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
from typing import Any, Deque, Dict, List, Optional, cast

from aea.connections.base import Connection, ConnectionStates
from aea.mail.base import Envelope
from aea.protocols.base import Message

from packages.fetchai.connections.ledger.base import CONNECTION_ID, RequestDispatcher
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

    def __init__(self, **kwargs: Any):
        """Initialize a connection to interact with a ledger APIs."""
        super().__init__(**kwargs)

        self._ledger_dispatcher: Optional[LedgerApiRequestDispatcher] = None
        self._contract_dispatcher: Optional[ContractApiRequestDispatcher] = None
        self._event_new_receiving_task: Optional[asyncio.Event] = None

        self.receiving_tasks: List[asyncio.Future] = []
        self.task_to_request: Dict[asyncio.Future, Envelope] = {}
        self.done_tasks: Deque[asyncio.Future] = deque()
        self.api_configs = self.configuration.config.get(
            "ledger_apis", {}
        )  # type: Dict[str, Dict[str, str]]

    @property
    def event_new_receiving_task(self) -> asyncio.Event:
        """Get the event to notify the 'receive' method of new receiving tasks."""
        return cast(asyncio.Event, self._event_new_receiving_task)

    async def connect(self) -> None:
        """Set up the connection."""

        if self.is_connected:  # pragma: nocover
            return

        self.state = ConnectionStates.connecting

        self._ledger_dispatcher = LedgerApiRequestDispatcher(
            self._state,
            loop=self.loop,
            api_configs=self.api_configs,
            logger=self.logger,
        )
        self._contract_dispatcher = ContractApiRequestDispatcher(
            self._state,
            loop=self.loop,
            api_configs=self.api_configs,
            logger=self.logger,
        )
        self._event_new_receiving_task = asyncio.Event()

        self.state = ConnectionStates.connected

    async def disconnect(self) -> None:
        """Tear down the connection."""
        if self.is_disconnected:  # pragma: nocover
            return

        self.state = ConnectionStates.disconnecting

        for task in self.receiving_tasks:
            if not task.cancelled():  # pragma: nocover
                task.cancel()
        self._ledger_dispatcher = None
        self._contract_dispatcher = None
        self._event_new_receiving_task = None

        self.state = ConnectionStates.disconnected

    async def send(self, envelope: "Envelope") -> None:
        """
        Send an envelope.

        :param envelope: the envelope to send.
        """
        task = self._schedule_request(envelope)
        self.receiving_tasks.append(task)
        self.task_to_request[task] = envelope
        self.event_new_receiving_task.set()

    def _schedule_request(self, envelope: Envelope) -> Task:
        """
        Schedule a ledger API request.

        :param envelope: the message.
        :return: task
        """
        dispatcher: RequestDispatcher
        if (
            envelope.protocol_specification_id
            == LedgerApiMessage.protocol_specification_id
        ):
            if self._ledger_dispatcher is None:  # pragma: nocover
                raise ValueError("No ledger dispatcher set.")
            dispatcher = self._ledger_dispatcher
        elif (
            envelope.protocol_specification_id
            == ContractApiMessage.protocol_specification_id
        ):
            if self._contract_dispatcher is None:  # pragma: nocover
                raise ValueError("No contract dispatcher set.")
            dispatcher = self._contract_dispatcher
        else:
            raise ValueError("Protocol not supported")

        task = dispatcher.dispatch(envelope)
        return task

    async def receive(self, *args: Any, **kwargs: Any) -> Optional["Envelope"]:
        """
        Receive an envelope. Blocking.

        :param args: positional arguments
        :param kwargs: keyword arguments
        :return: the envelope received, or None.
        """
        # if there are done tasks, return the result
        if len(self.done_tasks) > 0:  # pragma: nocover
            done_task = self.done_tasks.pop()
            return self._handle_done_task(done_task)

        if len(self.receiving_tasks) == 0:
            self.event_new_receiving_task.clear()
            await self.event_new_receiving_task.wait()

        # wait for completion of at least one receiving task
        done, _ = await asyncio.wait(
            self.receiving_tasks, return_when=asyncio.FIRST_COMPLETED
        )

        # pick one done task
        done_task = done.pop()

        # update done tasks
        self.done_tasks.extend([*done])

        return self._handle_done_task(done_task)

    def _handle_done_task(self, task: asyncio.Future) -> Optional[Envelope]:
        """
        Process a done receiving task.

        :param task: the done task.
        :return: the response envelope.
        """
        request = self.task_to_request.pop(task)
        self.receiving_tasks.remove(task)
        response_message: Optional[Message] = task.result()

        response_envelope = None
        if response_message is not None:
            response_envelope = Envelope(
                to=request.sender,
                sender=request.to,
                message=response_message,
                context=request.context,
            )
        return response_envelope
