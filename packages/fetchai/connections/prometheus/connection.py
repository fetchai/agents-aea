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

"""Prometheus connection and channel."""

import asyncio
import logging
from typing import Any, Dict, Optional, Tuple, Union, cast

import aioprometheus  # type: ignore

from aea.common import Address
from aea.configurations.base import PublicId
from aea.connections.base import Connection, ConnectionStates
from aea.exceptions import enforce
from aea.mail.base import Envelope, Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue

from packages.fetchai.protocols.prometheus.dialogues import PrometheusDialogue
from packages.fetchai.protocols.prometheus.dialogues import (
    PrometheusDialogues as BasePrometheusDialogues,
)
from packages.fetchai.protocols.prometheus.message import PrometheusMessage


PUBLIC_ID = PublicId.from_str("fetchai/prometheus:0.8.0")

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9090
VALID_UPDATE_FUNCS = {"inc", "dec", "add", "sub", "set", "observe"}
VALID_METRIC_TYPES = {"Counter", "Gauge", "Histogram", "Summary"}


class PrometheusDialogues(BasePrometheusDialogues):
    """The dialogues class keeps track of all prometheus dialogues."""

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
            # The server connection maintains the dialogue on behalf of the agent
            return PrometheusDialogue.Role.SERVER

        BasePrometheusDialogues.__init__(
            self,
            self_address=str(PUBLIC_ID),
            role_from_first_message=role_from_first_message,
            **kwargs,
        )


class PrometheusChannel:
    """A wrapper for interacting with a prometheus server."""

    def __init__(
        self,
        address: Address,
        host: str,
        port: int,
        logger: Union[logging.Logger, logging.LoggerAdapter],
    ):
        """
        Initialize a prometheus channel.

        :param address: The address of the connection.
        :param host: The host at which to expose the metrics.
        :param port: The port at which to expose the metrics.
        :param logger: The logger.
        """
        self.address = address
        self.metrics = {}  # type: Dict[str, aioprometheus.Collector]
        self.logger = logger
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._queue: Optional[asyncio.Queue] = None
        self._dialogues = PrometheusDialogues()
        self._host = host
        self._port = port
        self._service = aioprometheus.Service()

    def _get_message_and_dialogue(
        self, envelope: Envelope
    ) -> Tuple[PrometheusMessage, Optional[PrometheusDialogue]]:
        """
        Get a message copy and dialogue related to this message.

        :param envelope: incoming envelope

        :return: Tuple[Message, Optional[Dialogue]]
        """
        message = cast(PrometheusMessage, envelope.message)
        dialogue = cast(Optional[PrometheusDialogue], self._dialogues.update(message))
        return message, dialogue

    @property
    def queue(self) -> asyncio.Queue:
        """Check queue is set and return queue."""
        if self._queue is None:  # pragma: nocover
            raise ValueError("Channel is not connected")
        return self._queue

    async def connect(self) -> None:
        """Start prometheus http server."""
        if self._queue:  # pragma: nocover
            return None
        self._loop = asyncio.get_event_loop()
        self._queue = asyncio.Queue()
        await self._service.start(addr=self._host, port=self._port)

    async def send(self, envelope: Envelope) -> None:
        """
        Process the envelopes to prometheus.

        :param envelope: envelope
        """
        sender = envelope.sender
        self.logger.debug("Processing message from {}: {}".format(sender, envelope))
        if (
            envelope.protocol_specification_id
            != PrometheusMessage.protocol_specification_id
        ):
            raise ValueError(
                f"Protocol {envelope.protocol_specification_id} is not valid for prometheus."
            )
        await self._handle_prometheus_message(envelope)

    async def _handle_prometheus_message(self, envelope: Envelope) -> None:
        """
        Handle messages to prometheus.

        :param envelope: the envelope
        """
        enforce(
            isinstance(envelope.message, PrometheusMessage),
            "Message not of type PrometheusMessage",
        )
        message, dialogue = self._get_message_and_dialogue(envelope)

        if dialogue is None:
            self.logger.warning(
                "Could not create dialogue from message={}".format(message)
            )
            return

        if message.performative == PrometheusMessage.Performative.ADD_METRIC:
            response = await self._handle_add_metric(message)
        elif message.performative == PrometheusMessage.Performative.UPDATE_METRIC:
            response = await self._handle_update_metric(message)
        else:  # pragma: nocover
            self.logger.warning("Unrecognized performative for PrometheusMessage")
            return

        response_code, response_msg = cast(Tuple[int, str], response)

        msg = dialogue.reply(
            performative=PrometheusMessage.Performative.RESPONSE,
            target_message=message,
            code=response_code,
            message=response_msg,
        )
        envelope = Envelope(to=msg.to, sender=msg.sender, message=msg)
        await self._send(envelope)

    async def _handle_add_metric(self, message: PrometheusMessage) -> Tuple[int, str]:
        """Handle add metric message.

        :param message: the message to handle.
        :return: the response code and response message.
        """
        if message.title in self.metrics:
            response_code = 409
            response_msg = "Metric already exists."
        else:
            metric_type = getattr(aioprometheus, message.type, None)
            if metric_type is None or message.type not in VALID_METRIC_TYPES:
                response_code = 404
                response_msg = f"{message.type} is not a recognized prometheus metric."
            else:
                self.metrics[message.title] = metric_type(
                    message.title, message.description, message.labels
                )
                self._service.register(self.metrics[message.title])
                response_code = 200
                response_msg = (
                    f"New {message.type} successfully added: {message.title}."
                )

        return response_code, response_msg

    async def _handle_update_metric(
        self, message: PrometheusMessage
    ) -> Tuple[int, str]:
        """Handle update metric message.

        :param message: the message to handle.
        :return: the response code and response message.
        """
        metric = message.title
        if metric not in self.metrics:
            response_code = 404
            response_msg = f"Metric {metric} not found."
        else:
            update_func = getattr(self.metrics[metric], message.callable, None)
            if update_func is None:
                response_code = 400
                response_msg = (
                    f"Update function {message.callable} not found for metric {metric}."
                )
            else:
                if message.callable in VALID_UPDATE_FUNCS:
                    # Update the metric ("inc" and "dec" do not take "value" argument)
                    if message.callable in {"inc", "dec"}:
                        update_func(message.labels)
                    else:
                        update_func(message.labels, message.value)
                    response_code = 200
                    response_msg = f"Metric {metric} successfully updated."
                else:
                    response_code = 400
                    response_msg = f"Failed to update metric {metric}: {message.callable} is not a valid update function."

        return response_code, response_msg

    async def _send(self, envelope: Envelope) -> None:
        """Send a message.

        :param envelope: the envelope
        """
        await self.queue.put(envelope)

    async def disconnect(self) -> None:
        """Disconnect."""
        if self._queue is not None:
            await self._queue.put(None)
            self._queue = None
        await self._service.stop()

    async def get(self) -> Optional[Envelope]:
        """Get incoming envelope."""
        return await self.queue.get()


class PrometheusConnection(Connection):
    """Proxy to the functionality of prometheus."""

    connection_id = PUBLIC_ID

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize a connection to a local prometheus server.

        :param kwargs: the keyword arguments of the parent class.
        """
        super().__init__(**kwargs)

        self.host = cast(str, self.configuration.config.get("host", DEFAULT_HOST))
        self.port = cast(int, self.configuration.config.get("port", DEFAULT_PORT))
        self.channel = PrometheusChannel(
            self.address, self.host, self.port, self.logger
        )

    async def connect(self) -> None:
        """Connect to prometheus server via prometheus channel."""
        if self.is_connected:  # pragma: nocover
            return

        with self._connect_context():
            self.channel.logger = self.logger
            self.state = ConnectionStates.connecting
            await self.channel.connect()
            self.state = ConnectionStates.connected

    async def disconnect(self) -> None:
        """Disconnect from prometheus server."""
        if self.is_disconnected:  # pragma: nocover
            return

        self.state = ConnectionStates.disconnecting
        await self.channel.disconnect()
        self.state = ConnectionStates.disconnected

    async def send(self, envelope: Envelope) -> None:
        """
        Send an envelope.

        :param envelope: the envelop
        """
        self._ensure_connected()
        await self.channel.send(envelope)

    async def receive(self, *args: Any, **kwargs: Any) -> Optional["Envelope"]:
        """
        Receive an envelope.

        :param args: positional arguments
        :param kwargs: keyword arguments
        :return: The received envelope or None
        """
        self._ensure_connected()
        try:
            envelope = await self.channel.get()
            return envelope
        except asyncio.CancelledError:  # pragma: no cover
            return None
