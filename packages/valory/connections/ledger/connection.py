# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2023 Valory AG
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
from typing import Any, Dict, Optional

from aea.configurations.base import PublicId
from aea.connections.base import Connection, ConnectionStates
from aea.mail.base import Envelope
from aea.protocols.base import Message

from packages.valory.connections.ledger.base import RequestDispatcher
from packages.valory.connections.ledger.contract_dispatcher import (
    ContractApiRequestDispatcher,
)
from packages.valory.connections.ledger.ledger_dispatcher import (
    LedgerApiRequestDispatcher,
)
from packages.valory.protocols.contract_api import ContractApiMessage
from packages.valory.protocols.ledger_api import LedgerApiMessage


PUBLIC_ID = PublicId.from_str("valory/ledger:0.19.0")


class LedgerConnection(Connection):
    """Proxy to the functionality of the SDK or API."""

    connection_id = PUBLIC_ID
    TIMEOUT = 3
    MAX_ATTEMPTS = 120

    def __init__(self, **kwargs: Any):
        """Initialize a connection to interact with a ledger APIs."""
        super().__init__(**kwargs)

        self._ledger_dispatcher: Optional[LedgerApiRequestDispatcher] = None
        self._contract_dispatcher: Optional[ContractApiRequestDispatcher] = None
        self._response_envelopes: Optional[asyncio.Queue] = None

        self.task_to_request: Dict[asyncio.Future, Envelope] = {}
        self.api_configs = self.configuration.config.get(
            "ledger_apis", {}
        )  # type: Dict[str, Dict[str, str]]
        self.request_retry_attempts = self.configuration.config.get(
            "retry_attempts", self.MAX_ATTEMPTS
        )
        self.request_retry_timeout = self.configuration.config.get(
            "retry_timeout", self.TIMEOUT
        )

    @property
    def response_envelopes(self) -> asyncio.Queue:
        """Get the response envelopes. Only intended to be accessed when connected."""
        if self._response_envelopes is None:
            raise ValueError(
                "`asyncio.Queue` for `_response_envelopes` not set. Is the ledger connection active?"
            )
        return self._response_envelopes

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
            retry_attempts=self.request_retry_attempts,
            retry_timeout=self.request_retry_timeout,
            connection_id=self.connection_id,
        )
        self._contract_dispatcher = ContractApiRequestDispatcher(
            self._state,
            loop=self.loop,
            api_configs=self.api_configs,
            logger=self.logger,
            retry_attempts=self.request_retry_attempts,
            retry_timeout=self.request_retry_timeout,
            connection_id=self.connection_id,
        )

        self._response_envelopes = asyncio.Queue()
        self.state = ConnectionStates.connected

    async def disconnect(self) -> None:
        """Tear down the connection."""
        if self.is_disconnected:  # pragma: nocover
            return

        self.state = ConnectionStates.disconnecting

        for task in self.task_to_request.keys():
            if not task.cancelled():  # pragma: nocover
                task.cancel()
        self._ledger_dispatcher = None
        self._contract_dispatcher = None
        self._response_envelopes = None

        self.state = ConnectionStates.disconnected

    async def send(self, envelope: "Envelope") -> None:
        """
        Send an envelope.

        :param envelope: the envelope to send.
        """
        task = self._schedule_request(envelope)
        task.add_done_callback(self._handle_done_task)
        self.task_to_request[task] = envelope

    def _schedule_request(self, envelope: Envelope) -> asyncio.Task:
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

        :param args: the arguments
        :param kwargs: the keyword arguments
        :return: the envelope received, or None.
        """
        return await self.response_envelopes.get()

    def _handle_done_task(self, task: asyncio.Future) -> None:
        """
        Process a done receiving task.

        :param task: the done task.
        """
        request = self.task_to_request.pop(task)
        response_message: Optional[Message] = task.result()

        response_envelope = None
        if response_message is not None:
            response_envelope = Envelope(
                to=request.sender,
                sender=request.to,
                message=response_message,
                context=request.context,
            )

        # not handling `asyncio.QueueFull` exception, because the maxsize we defined for the Queue is infinite
        self.response_envelopes.put_nowait(response_envelope)
