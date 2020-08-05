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

from aea.configurations.base import ProtocolId
from aea.mail.base import Address, EnvelopeContext
from aea.protocols.base import Message
from aea.protocols.default.message import DefaultMessage
from aea.skills.base import Handler

from packages.fetchai.connections.p2p_libp2p.connection import (
    PUBLIC_ID as P2P_CONNECTION_PUBLIC_ID,
)
from packages.fetchai.protocols.http.message import HttpMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.aries_faber.dialogues import (
    DefaultDialogues,
    HttpDialogue,
    HttpDialogues,
    OefSearchDialogue,
    OefSearchDialogues,
)
from packages.fetchai.skills.aries_faber.strategy import FaberStrategy

SUPPORT_REVOCATION = False

ADMIN_COMMAND_CREATE_INVITATION = "/connections/create-invitation"
ADMIN_COMMAND_STATUS = "/status"


class FaberHTTPHandler(Handler):
    """This class represents faber's handler for default messages."""

    SUPPORTED_PROTOCOL = HttpMessage.protocol_id  # type: Optional[ProtocolId]

    def __init__(self, **kwargs):
        """Initialize the handler."""
        super().__init__(**kwargs)

        self.connection_id = None  # type: Optional[str]
        self.is_connected_to_Alice = False

        self.handled_message = None

    @property
    def admin_url(self) -> str:
        """Get the admin URL."""
        return self.context.behaviours.faber.admin_url

    @property
    def alice_address(self) -> Address:
        """Get Alice's address."""
        return self.context.behaviours.faber.alice_address

    def _admin_post(self, path: str, content: Dict = None) -> None:
        # Request message & envelope
        http_dialogues = cast(HttpDialogues, self.context.http_dialogues)
        request_http_message = HttpMessage(
            dialogue_reference=http_dialogues.new_self_initiated_dialogue_reference(),
            performative=HttpMessage.Performative.REQUEST,
            method="POST",
            url=self.admin_url + path,
            headers="",
            version="",
            bodyy=b"" if content is None else json.dumps(content).encode("utf-8"),
        )
        request_http_message.counterparty = self.admin_url
        http_dialogue = http_dialogues.update(request_http_message)
        if http_dialogue is not None:
            self.context.outbox.put_message(message=request_http_message)
        else:
            self.context.logger.exception(
                "something went wrong when sending a HTTP message."
            )

    def _send_message(self, content: Dict) -> None:
        # message & envelope
        default_dialogues = cast(DefaultDialogues, self.context.default_dialogues)
        message = DefaultMessage(
            dialogue_reference=default_dialogues.new_self_initiated_dialogue_reference(),
            performative=DefaultMessage.Performative.BYTES,
            content=json.dumps(content).encode("utf-8"),
        )
        message.counterparty = self.alice_address
        context = EnvelopeContext(connection_id=P2P_CONNECTION_PUBLIC_ID)

        default_dialogue = default_dialogues.update(message)
        if default_dialogue is not None:
            self.context.outbox.put_message(message=message, context=context)
        else:
            self.context.logger.exception(
                "something went wrong when sending a default message."
            )

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
        http_dialogues = cast(HttpDialogues, self.context.http_dialogues)

        self.handled_message = message
        if (
            message.performative == HttpMessage.Performative.RESPONSE
            and message.status_code == 200
        ):  # response to http request
            http_dialogue = cast(Optional[HttpDialogue], http_dialogues.update(message))
            if http_dialogue is None:
                self.context.logger.exception(
                    "faber -> http_handler -> handle() -> RESPONSE: "
                    "something went wrong when adding the incoming HTTP response message to the dialogue."
                )
                return

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
                self.context.logger.info("connection id: " + self.connection_id)  # type: ignore
                self.context.logger.info("invitation: " + str(invitation))
                self.context.logger.info(
                    "Sent invitation to Alice. Waiting for the invitation from Alice to finalise the connection..."
                )
                self._send_message(invitation)
        elif (
            message.performative == HttpMessage.Performative.REQUEST
        ):  # webhook request
            http_dialogue = cast(Optional[HttpDialogue], http_dialogues.update(message))
            if http_dialogue is None:
                self.context.logger.exception(
                    "something went wrong when adding the incoming HTTP webhook request message to the dialogue."
                )
                return
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


class FaberOefSearchHandler(Handler):
    """This class implements an OEF search handler."""

    SUPPORTED_PROTOCOL = OefSearchMessage.protocol_id  # type: Optional[ProtocolId]

    def setup(self) -> None:
        """Call to setup the handler."""
        pass

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :return: None
        """
        self.context.logger.info("Handling SOEF message...")
        oef_search_msg = cast(OefSearchMessage, message)

        # recover dialogue
        oef_search_dialogues = cast(
            OefSearchDialogues, self.context.oef_search_dialogues
        )
        oef_search_dialogue = cast(
            Optional[OefSearchDialogue], oef_search_dialogues.update(oef_search_msg)
        )
        if oef_search_dialogue is None:
            self._handle_unidentified_dialogue(oef_search_msg)
            return

        # handle message
        if oef_search_msg.performative is OefSearchMessage.Performative.OEF_ERROR:
            self._handle_error(oef_search_msg, oef_search_dialogue)
        elif oef_search_msg.performative is OefSearchMessage.Performative.SEARCH_RESULT:
            self._handle_search(oef_search_msg)
        else:
            self._handle_invalid(oef_search_msg, oef_search_dialogue)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass

    def _handle_unidentified_dialogue(self, oef_search_msg: OefSearchMessage) -> None:
        """
        Handle an unidentified dialogue.

        :param oef_search_msg: the oef search message to be handled
        :return: None
        """
        self.context.logger.info(
            "received invalid oef_search message={}, unidentified dialogue.".format(
                oef_search_msg
            )
        )

    def _handle_error(
        self, oef_search_msg: OefSearchMessage, oef_search_dialogue: OefSearchDialogue
    ) -> None:
        """
        Handle an oef search message.

        :param oef_search_msg: the oef search message to be handled
        :param oef_search_dialogue: the dialogue
        :return: None
        """
        self.context.logger.info(
            "received oef_search error message={} in dialogue={}.".format(
                oef_search_msg, oef_search_dialogue
            )
        )

    def _handle_search(self, oef_search_msg: OefSearchMessage) -> None:
        """
        Handle the search response.

        :param oef_search_msg: the oef search message to be handled
        :return: None
        """
        if len(oef_search_msg.agents) != 1:
            self.context.logger.info(
                "did not find Alice. found {} agents. continue searching.".format(
                    len(oef_search_msg.agents)
                )
            )
            return

        self.context.logger.info(
            "found Alice with address {}, stopping search.".format(
                oef_search_msg.agents[0]
            )
        )
        strategy = cast(FaberStrategy, self.context.strategy)
        strategy.is_searching = False  # stopping search

        # set alice address
        self.context.behaviours.faber.alice_address = oef_search_msg.agents[0]

        # check ACA is running
        self.context.behaviours.faber.admin_get(ADMIN_COMMAND_STATUS)

    def _handle_invalid(
        self, oef_search_msg: OefSearchMessage, oef_search_dialogue: OefSearchDialogue
    ) -> None:
        """
        Handle an oef search message.

        :param oef_search_msg: the oef search message
        :param oef_search_dialogue: the dialogue
        :return: None
        """
        self.context.logger.warning(
            "cannot handle oef_search message of performative={} in dialogue={}.".format(
                oef_search_msg.performative, oef_search_dialogue,
            )
        )
