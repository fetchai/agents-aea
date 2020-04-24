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

import base64
import binascii
import json
from typing import Dict, Optional

from aea.configurations.base import ProtocolId, PublicId
from aea.mail.base import Envelope, EnvelopeContext
from aea.protocols.base import Message
from aea.protocols.default.message import DefaultMessage
from aea.skills.base import Handler

from packages.fetchai.protocols.http.message import HttpMessage
from packages.fetchai.protocols.http.serialization import HttpSerializer

from urllib.parse import urlparse

HTTP_CONNECTION_PUBLIC_ID = PublicId("fetchai", "http_client", "0.1.0")

HTTP_PROTOCOL_PUBLIC_ID = PublicId("fetchai", "http", "0.1.0")
DEFAULT_ADMIN_HOST = "127.0.0.1"
DEFAULT_ADMIN_PORT = 8031


class AriesDemoDefaultHandler(Handler):
    """This class represents alice's handler for default messages."""

    SUPPORTED_PROTOCOL = DefaultMessage.protocol_id  # type: Optional[ProtocolId]

    def __init__(self, **kwargs):
        """Initialize the handler."""
        self.admin_host = kwargs.pop("admin_host", DEFAULT_ADMIN_HOST)
        self.admin_port = kwargs.pop("admin_port", DEFAULT_ADMIN_PORT)

        super().__init__(**kwargs)

        self.admin_url = "http://{}:{}".format(self.admin_host, self.admin_port)

        self.kwargs = kwargs
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
        context = EnvelopeContext(connection_id=HTTP_CONNECTION_PUBLIC_ID)
        envelope = Envelope(
            to="Alice_ACA",
            sender=self.context.agent_address,
            protocol_id=HTTP_PROTOCOL_PUBLIC_ID,
            context=context,
            message=HttpSerializer().encode(request_http_message),
        )
        self.context.outbox.put(envelope)

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
        if message.performative == DefaultMessage.Performative.BYTES:
            content_bytes = message.content
            content = json.loads(content_bytes)
            self.context.logger.info("Received message content:" + str(content))
            if "@type" in content:
                # self.handle_received_invite(content)
                self._admin_post("/connections/receive-invitation", content)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass

    def handle_received_invite(self, invite_detail: Dict):
        import pdb;pdb.set_trace()
        for details in invite_detail:
            try:
                url = urlparse(details)
                query = url.query
                if query and "c_i=" in query:
                    pos = query.index("c_i=") + 4
                    b64_invite = query[pos:]
                else:
                    b64_invite = details
            except ValueError:
                b64_invite = details

            if b64_invite:
                try:
                    padlen = 4 - len(b64_invite) % 4
                    if padlen <= 2:
                        b64_invite += "=" * padlen
                    invite_json = base64.urlsafe_b64decode(b64_invite)
                    details = invite_json.decode("utf-8")
                except binascii.Error:
                    pass
                except UnicodeDecodeError:
                    pass

            if details:
                try:
                    json.loads(details)
                    break
                except json.JSONDecodeError as e:
                    self.context.logger.error("Invalid invitation:", str(e))

        self._admin_post("/connections/receive-invitation", details)


class AriesDemoHttpHandler(Handler):
    """This class represents alice's handler for HTTP messages."""

    SUPPORTED_PROTOCOL = HttpMessage.protocol_id  # type: Optional[ProtocolId]

    def __init__(self, **kwargs):
        """Initialize the handler."""
        self.admin_host = kwargs.pop("admin_host", DEFAULT_ADMIN_HOST)
        self.admin_port = kwargs.pop("admin_port", DEFAULT_ADMIN_PORT)

        super().__init__(**kwargs)

        self.admin_url = "http://{}:{}".format(self.admin_host, self.admin_port)
        self.connection_id = ""
        self.is_connected_to_Faber = False

        self.kwargs = kwargs
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
            to="Alice_ACA",
            sender=self.context.agent_address,
            protocol_id=HTTP_PROTOCOL_PUBLIC_ID,
            message=HttpSerializer().encode(request_http_message),
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
        if message.performative == HttpMessage.Performative.REQUEST:  # webhook
            content_bytes = message.bodyy
            content = json.loads(content_bytes)
            self.context.logger.info("Received webhook message content:" + str(content))
            if "connection_id" in content:
                if content["connection_id"] == self.connection_id:
                    if content["state"] == "active" and not self.is_connected_to_Faber:
                        self.context.logger.info("Connected to Faber")
                        self.is_connected_to_Faber = True
        elif message.performative == HttpMessage.Performative.RESPONSE:  # response to http_client request
            content_bytes = message.bodyy
            content = content_bytes.decode("utf-8")
            if "Error" in content:
                self.context.logger.error("Something went wrong after I sent the administrative command of 'invitation receive'")
            else:
                self.context.logger.info("Received http response message content:" + str(content))
                if "connection_id" in content:
                    connection = content
                    self.connection_id = content["connection_id"]
                    invitation = connection["invitation"]
                    self.context.logger.info("invitation response: " + str(connection))
                    self.context.logger.info("connection id: " + self.connection_id)
                    self.context.logger.info("invitation: " + str(invitation))

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass
