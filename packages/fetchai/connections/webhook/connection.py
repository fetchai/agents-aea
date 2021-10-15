# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2020 Fetch.AI Limited
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
"""Webhook connection and channel."""

import asyncio
import json
import logging
from asyncio import CancelledError
from typing import Any, Optional, cast

from aiohttp import web  # type: ignore

from aea.common import Address
from aea.configurations.base import PublicId
from aea.connections.base import Connection, ConnectionStates
from aea.mail.base import Envelope
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue as BaseDialogue

from packages.fetchai.protocols.http.dialogues import HttpDialogue
from packages.fetchai.protocols.http.dialogues import HttpDialogues as BaseHttpDialogues
from packages.fetchai.protocols.http.message import HttpMessage


SUCCESS = 200
NOT_FOUND = 404
REQUEST_TIMEOUT = 408
SERVER_ERROR = 500
PUBLIC_ID = PublicId.from_str("fetchai/webhook:0.19.0")

_default_logger = logging.getLogger("aea.packages.fetchai.connections.webhook")

RequestId = str


class HttpDialogues(BaseHttpDialogues):
    """The dialogues class keeps track of all http dialogues."""

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
            # The webhook connection maintains the dialogue on behalf of the server
            return HttpDialogue.Role.SERVER

        BaseHttpDialogues.__init__(
            self,
            self_address=str(WebhookConnection.connection_id),
            role_from_first_message=role_from_first_message,
            **kwargs,
        )


class WebhookChannel:
    """A wrapper for a Webhook."""

    def __init__(
        self,
        agent_address: Address,
        webhook_address: Address,
        webhook_port: int,
        webhook_url_path: str,
        connection_id: PublicId,
        target_skill_id: PublicId,
        logger: logging.Logger = _default_logger,
    ):
        """
        Initialize a webhook channel.

        :param agent_address: the address of the agent
        :param webhook_address: webhook hostname / IP address
        :param webhook_port: webhook port number
        :param webhook_url_path: the url path to receive webhooks from
        :param connection_id: the connection id
        :param target_skill_id: the skill id which should receive the http messages
        :param logger: the logger
        """
        self.agent_address = agent_address

        self.webhook_address = webhook_address
        self.webhook_port = webhook_port
        self.webhook_url_path = webhook_url_path
        self.target_skill_id = target_skill_id

        self.webhook_site = None  # type: Optional[web.TCPSite]
        self.runner = None  # type: Optional[web.AppRunner]
        self.app = None  # type: Optional[web.Application]

        self.is_stopped = True

        self.connection_id = connection_id
        self.in_queue = None  # type: Optional[asyncio.Queue]  # pragma: no cover
        self.logger = logger
        self.logger.info("Initialised a webhook channel")
        self._dialogues = HttpDialogues()

    async def connect(self) -> None:
        """
        Connect the webhook.

        Connects the webhook via the webhook_address and webhook_port parameters
        """
        if self.is_stopped:
            self.app = web.Application()
            self.app.add_routes(
                [web.post(self.webhook_url_path, self._receive_webhook)]
            )
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            self.webhook_site = web.TCPSite(
                self.runner, self.webhook_address, self.webhook_port
            )
            await self.webhook_site.start()
            self.is_stopped = False

    async def disconnect(self) -> None:
        """
        Disconnect.

        Shut-off and cleanup the webhook site, the runner and the web app, then stop the channel.
        """
        if self.webhook_site is None or self.runner is None or self.app is None:
            raise ValueError(
                "Application not connected, call connect first!"
            )  # pragma: nocover

        if not self.is_stopped:
            await self.webhook_site.stop()
            await self.runner.shutdown()
            await self.runner.cleanup()
            await self.app.shutdown()
            await self.app.cleanup()
            self.logger.info("Webhook app is shutdown.")
            self.is_stopped = True

    async def _receive_webhook(self, request: web.Request) -> web.Response:
        """
        Receive a webhook request.

        Get webhook request, turn it to envelop and send it to the agent to be picked up.

        :param request: the webhook request
        :return: Http response with a 200 code
        """
        webhook_envelop = await self.to_envelope(request)
        self.in_queue.put_nowait(webhook_envelop)  # type: ignore
        return web.Response(status=200)

    async def send(self, envelope: Envelope) -> None:
        """
        Send an envelope.

        Sending envelopes via the webhook is not possible!

        :param envelope: the envelope
        """
        self.logger.warning(
            "Dropping envelope={} as sending via the webhook is not possible!".format(
                envelope
            )
        )

    async def to_envelope(self, request: web.Request) -> Envelope:
        """
        Convert a webhook request object into an Envelope containing an HttpMessage `from the 'http' Protocol`.

        :param request: the webhook request
        :return: The envelop representing the webhook request
        """
        payload_bytes = await request.read()
        version = str(request.version[0]) + "." + str(request.version[1])

        http_message, _ = self._dialogues.create(
            counterparty=str(self.target_skill_id),
            performative=HttpMessage.Performative.REQUEST,
            method=request.method,
            url=str(request.url),
            version=version,
            headers=json.dumps(dict(request.headers)),
            body=payload_bytes if payload_bytes is not None else b"",
        )
        envelope = Envelope(
            to=http_message.to, sender=http_message.sender, message=http_message,
        )
        return envelope


class WebhookConnection(Connection):
    """Proxy to the functionality of a webhook."""

    connection_id = PUBLIC_ID

    def __init__(self, **kwargs: Any) -> None:
        """Initialize a web hook connection."""
        super().__init__(**kwargs)
        webhook_address = cast(str, self.configuration.config.get("webhook_address"))
        webhook_port = cast(int, self.configuration.config.get("webhook_port"))
        webhook_url_path = cast(str, self.configuration.config.get("webhook_url_path"))
        target_skill_id_ = cast(
            Optional[str], self.configuration.config.get("target_skill_id")
        )
        if (
            webhook_address is None
            or webhook_port is None
            or webhook_url_path is None
            or target_skill_id_ is None
        ):
            raise ValueError(  # pragma: nocover
                "webhook_address, webhook_port, webhook_url_path and target_skill_id must be set!"
            )
        target_skill_id = PublicId.try_from_str(target_skill_id_)
        if target_skill_id is None:  # pragma: nocover
            raise ValueError("Provided target_skill_id is not a valid public id.")
        self.channel = WebhookChannel(
            agent_address=self.address,
            webhook_address=webhook_address,
            webhook_port=webhook_port,
            webhook_url_path=webhook_url_path,
            connection_id=self.connection_id,
            target_skill_id=target_skill_id,
            logger=self.logger,
        )

    async def connect(self) -> None:
        """Connect to a HTTP server."""
        if self.is_connected:  # pragma: nocover
            return

        with self._connect_context():
            self.channel.logger = self.logger
            self.channel.in_queue = asyncio.Queue()
            await self.channel.connect()

    async def disconnect(self) -> None:
        """Disconnect from a HTTP server."""
        if self.is_disconnected:  # pragma: nocover
            return

        self.state = ConnectionStates.disconnecting
        await self.channel.disconnect()
        self.state = ConnectionStates.disconnected

    async def send(self, envelope: "Envelope") -> None:
        """
        Send does nothing. Webhooks only receive.

        :param envelope: the envelop
        """
        self._ensure_connected()
        if self.channel.in_queue is None:
            raise ValueError("Channel in queue not set.")  # pragma: nocover
        await self.channel.send(envelope)

    async def receive(self, *args: Any, **kwargs: Any) -> Optional["Envelope"]:
        """
        Receive an envelope.

        :param args: positional arguments
        :param kwargs: keyword arguments
        :return: the envelope received, or None.
        """
        self._ensure_connected()
        if self.channel.in_queue is None:
            raise ValueError("Channel in queue not set.")  # pragma: nocover
        try:
            envelope = await self.channel.in_queue.get()
            if envelope is None:
                return None  # pragma: no cover
            return envelope
        except CancelledError:  # pragma: no cover
            return None
