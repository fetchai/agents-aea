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

"""This package contains the handlers for the aries_alice skill."""

import json
from typing import Dict, Optional, cast

from aea.configurations.base import ProtocolId
from aea.mail.base import EnvelopeContext
from aea.protocols.base import Message
from aea.protocols.default.message import DefaultMessage
from aea.skills.base import Handler

from packages.fetchai.connections.http_client.connection import (
    PUBLIC_ID as HTTP_CLIENT_CONNECTION_PUBLIC_ID,
)
from packages.fetchai.protocols.http.message import HttpMessage

DEFAULT_ADMIN_HOST = "127.0.0.1"
DEFAULT_ADMIN_PORT = 8031

ADMIN_COMMAND_RECEIVE_INVITE = "/connections/receive-invitation"


class DefaultHandler(Handler):
    """This class represents alice's handler for default messages."""

    SUPPORTED_PROTOCOL = DefaultMessage.protocol_id  # type: Optional[ProtocolId]

    def __init__(self, **kwargs):
        """Initialize the handler."""
        self.admin_host = kwargs.pop("admin_host", DEFAULT_ADMIN_HOST)
        self.admin_port = kwargs.pop("admin_port", DEFAULT_ADMIN_PORT)

        super().__init__(**kwargs)

        self.admin_url = "http://{}:{}".format(self.admin_host, self.admin_port)

        self.handled_message = None

    def _admin_post(self, path: str, content: Dict = None):
        # Request message & envelope
        request_http_message = HttpMessage(
            performative=HttpMessage.Performative.REQUEST,
            method="POST",
            url=self.admin_url + path,
            headers="",
            version="",
            bodyy=b"" if content is None else json.dumps(content).encode("utf-8"),
        )
        request_http_message.counterparty = self.admin_url
        self.context.outbox.put_message(
            message=request_http_message,
            context=EnvelopeContext(connection_id=HTTP_CLIENT_CONNECTION_PUBLIC_ID),
        )

    def setup(self) -> None:
        """
        Implement the setup.

        :return: None
        """
        pass

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to an envelope.

        :param message: the message
        :return: None
        """
        message = cast(DefaultMessage, message)
        self.handled_message = message
        if message.performative == DefaultMessage.Performative.BYTES:
            content_bytes = message.content
            content = json.loads(content_bytes)
            self.context.logger.info("Received message content:" + str(content))
            if "@type" in content:
                self._admin_post(ADMIN_COMMAND_RECEIVE_INVITE, content)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass


class HttpHandler(Handler):
    """This class represents alice's handler for HTTP messages."""

    SUPPORTED_PROTOCOL = HttpMessage.protocol_id  # type: Optional[ProtocolId]

    def __init__(self, **kwargs):
        """Initialize the handler."""
        self.admin_host = kwargs.pop("admin_host", DEFAULT_ADMIN_HOST)
        self.admin_port = kwargs.pop("admin_port", DEFAULT_ADMIN_PORT)

        super().__init__(**kwargs)

        self.admin_url = "http://{}:{}".format(self.admin_host, self.admin_port)
        self.connection_id = None  # type: Optional[str]
        self.is_connected_to_Faber = False

        self.handled_message = None

    def setup(self) -> None:
        """
        Implement the setup.

        :return: None
        """
        self.context.logger.info("My address is: " + self.context.agent_address)

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to an envelope.

        :param message: the message
        :return: None
        """
        message = cast(HttpMessage, message)
        self.handled_message = message
        if message.performative == HttpMessage.Performative.REQUEST:  # webhook
            content_bytes = message.bodyy
            content = json.loads(content_bytes)
            self.context.logger.info("Received webhook message content:" + str(content))
            if "connection_id" in content:
                if content["connection_id"] == self.connection_id:
                    if content["state"] == "active" and not self.is_connected_to_Faber:
                        self.context.logger.info("Connected to Faber")
                        self.is_connected_to_Faber = True
        elif (
            message.performative == HttpMessage.Performative.RESPONSE
        ):  # response to http_client request
            content_bytes = message.bodyy
            content = content_bytes.decode("utf-8")
            if "Error" in content:
                self.context.logger.error(
                    "Something went wrong after I sent the administrative command of 'invitation receive'"
                )
            else:
                self.context.logger.info(
                    "Received http response message content:" + str(content)
                )
                if "connection_id" in content:
                    connection = content
                    self.connection_id = content["connection_id"]
                    invitation = connection["invitation"]
                    self.context.logger.info("invitation response: " + str(connection))
                    self.context.logger.info("connection id: " + self.connection_id)  # type: ignore
                    self.context.logger.info("invitation: " + str(invitation))

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass
