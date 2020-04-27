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

"""This package contains the handlers for the faber_alice skill."""

import json
from typing import Dict, Optional, cast

from aea.configurations.base import ProtocolId, PublicId
from aea.mail.base import Envelope, EnvelopeContext
from aea.protocols.base import Message
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer
from aea.skills.base import Handler

from packages.fetchai.protocols.http.message import HttpMessage
from packages.fetchai.protocols.http.serialization import HttpSerializer

HTTP_PROTOCOL_PUBLIC_ID = HttpMessage.protocol_id
DEFAULT_PROTOCOL_PUBLIC_ID = DefaultMessage.protocol_id
OEF_CONNECTION_PUBLIC_ID = PublicId("fetchai", "oef", "0.2.0")

DEFAULT_ADMIN_HOST = "127.0.0.1"
DEFAULT_ADMIN_PORT = 8021
SUPPORT_REVOCATION = False

ADMIN_COMMAND_CREATE_INVITATION = "/connections/create-invitation"


class HTTPHandler(Handler):
    """This class represents faber's handler for default messages."""

    SUPPORTED_PROTOCOL = HttpMessage.protocol_id  # type: Optional[ProtocolId]

    def __init__(self, **kwargs):
        """Initialize the handler."""
        self.admin_host = kwargs.pop("admin_host", DEFAULT_ADMIN_HOST)
        self.admin_port = kwargs.pop("admin_port", DEFAULT_ADMIN_PORT)
        self.alice_id = kwargs.pop("alice_id")

        super().__init__(**kwargs)

        self.admin_url = "http://{}:{}".format(self.admin_host, self.admin_port)
        self.connection_id = None  # type: Optional[str]
        self.is_connected_to_Alice = False

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
        self.context.outbox.put_message(
            to=self.admin_url,
            sender=self.context.agent_address,
            protocol_id=HTTP_PROTOCOL_PUBLIC_ID,
            message=HttpSerializer().encode(request_http_message),
        )

    def send_message(self, content: Dict):
        # message & envelope
        message = DefaultMessage(
            performative=DefaultMessage.Performative.BYTES,
            content=json.dumps(content).encode("utf-8"),
        )
        context = EnvelopeContext(connection_id=OEF_CONNECTION_PUBLIC_ID)
        envelope = Envelope(
            to=self.alice_id,
            sender=self.context.agent_address,
            protocol_id=DEFAULT_PROTOCOL_PUBLIC_ID,
            context=context,
            message=DefaultSerializer().encode(message),
        )
        self.context.outbox.put(envelope)

    def setup(self) -> None:
        """
        Implement the setup.

        :return: None
        """
        pass  # pragma: no cover

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to an envelope.

        :param message: the message
        :return: None
        """
        message = cast(HttpMessage, message)
        self.handled_message = message
        if (
            message.performative == HttpMessage.Performative.RESPONSE
            and message.status_code == 200
        ):  # response to http request
            content_bytes = message.bodyy  # type: ignore
            content = json.loads(content_bytes)
            self.context.logger.info("Received message: " + str(content))
            if "version" in content:  # response to /status
                self._admin_post(ADMIN_COMMAND_CREATE_INVITATION)
            elif "connection_id" in content:
                connection = content
                self.connection_id = content["connection_id"]
                invitation = connection["invitation"]
                self.context.logger.info("connection: " + str(connection))
                self.context.logger.info("connection id: " + self.connection_id)
                self.context.logger.info("invitation: " + str(invitation))
                self.context.logger.info(
                    "Sent invitation to Alice. Waiting for the invitation from Alice to finalise the connection..."
                )
                self.send_message(invitation)
        elif (
            message.performative == HttpMessage.Performative.REQUEST
        ):  # webhook request
            content_bytes = message.bodyy
            content = json.loads(content_bytes)
            self.context.logger.info("Received webhook message content:" + str(content))
            if "connection_id" in content:
                if content["connection_id"] == self.connection_id:
                    if content["state"] == "active" and not self.is_connected_to_Alice:
                        self.context.logger.info("Connected to Alice")
                        self.is_connected_to_Alice = True

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass
