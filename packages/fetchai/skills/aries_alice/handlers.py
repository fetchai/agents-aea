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
from typing import Dict, Optional, cast
from urllib.parse import urlparse

from aea.configurations.base import PublicId
from aea.protocols.base import Message
from aea.skills.base import Handler

from packages.fetchai.protocols.default.message import DefaultMessage
from packages.fetchai.protocols.http.message import HttpMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.aries_alice.dialogues import (
    DefaultDialogue,
    DefaultDialogues,
    HttpDialogue,
    HttpDialogues,
    OefSearchDialogue,
    OefSearchDialogues,
)
from packages.fetchai.skills.aries_alice.strategy import (
    ADMIN_COMMAND_RECEIVE_INVITE,
    AliceStrategy,
)


class AliceDefaultHandler(Handler):
    """This class represents alice's handler for default messages."""

    SUPPORTED_PROTOCOL = DefaultMessage.protocol_id  # type: Optional[PublicId]

    def __init__(self, **kwargs):
        """Initialize the handler."""
        super().__init__(**kwargs)

        self.handled_message = None

    def _handle_received_invite(self, invite_detail: Dict[str, str]) -> Optional[str]:
        """
        Prepare an invitation detail received from Faber_AEA to be send to the Alice ACA.

        :param invite_detail: the invitation detail
        :return: The prepared invitation detail
        """
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
                except binascii.Error as e:
                    self.context.logger.error("Invalid invitation:", str(e))
                except UnicodeDecodeError as e:
                    self.context.logger.error("Invalid invitation:", str(e))

            if details:
                try:
                    json.loads(details)
                    return details
                except json.JSONDecodeError as e:
                    self.context.logger.error("Invalid invitation:", str(e))

        self.context.logger.error("No details in the invitation detail:")
        return None

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
        default_dialogues = cast(DefaultDialogues, self.context.default_dialogues)

        strategy = cast(AliceStrategy, self.context.strategy)

        self.handled_message = message
        if message.performative == DefaultMessage.Performative.BYTES:
            http_dialogue = cast(
                Optional[DefaultDialogue], default_dialogues.update(message)
            )
            if http_dialogue is None:
                self.context.logger.exception(
                    "alice -> default_handler -> handle(): something went wrong when adding the incoming HTTP response message to the dialogue."
                )
                return
            content_bytes = message.content
            content = json.loads(content_bytes)
            self.context.logger.info("Received message content:" + str(content))
            if "@type" in content:
                details = self._handle_received_invite(content)
                self.context.behaviours.alice.send_http_request_message(
                    method="POST",
                    url=strategy.admin_url + ADMIN_COMMAND_RECEIVE_INVITE,
                    content=details,
                )

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass


class AliceHttpHandler(Handler):
    """This class represents alice's handler for HTTP messages."""

    SUPPORTED_PROTOCOL = HttpMessage.protocol_id  # type: Optional[PublicId]

    def __init__(self, **kwargs):
        """Initialize the handler."""
        super().__init__(**kwargs)

        self.connection_id = None  # type: Optional[str]
        self.is_connected_to_Faber = False

        self.handled_message = None

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
        message = cast(HttpMessage, message)
        http_dialogues = cast(HttpDialogues, self.context.http_dialogues)

        self.handled_message = message
        if message.performative == HttpMessage.Performative.REQUEST:  # webhook
            http_dialogue = cast(Optional[HttpDialogue], http_dialogues.update(message))
            if http_dialogue is None:
                self.context.logger.exception(
                    "alice -> http_handler -> handle() -> REQUEST: something went wrong when adding the incoming HTTP webhook request message to the dialogue."
                )
                return
            content_bytes = message.body
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
            http_dialogue = cast(Optional[HttpDialogue], http_dialogues.update(message))
            if http_dialogue is None:
                self.context.logger.exception(
                    "alice -> http_handler -> handle() -> RESPONSE: something went wrong when adding the incoming HTTP response message to the dialogue."
                )
                return
            content_bytes = message.body
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


class AliceOefSearchHandler(Handler):
    """This class implements an OEF search handler."""

    SUPPORTED_PROTOCOL = OefSearchMessage.protocol_id  # type: Optional[PublicId]

    def setup(self) -> None:
        """Call to setup the handler."""
        pass

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :return: None
        """
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

        :param oef_search_msg: the oef search message
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

        :param oef_search_msg: the oef search message
        :param oef_search_dialogue: the dialogue
        :return: None
        """
        self.context.logger.info(
            "received oef_search error message={} in dialogue={}.".format(
                oef_search_msg, oef_search_dialogue
            )
        )

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
