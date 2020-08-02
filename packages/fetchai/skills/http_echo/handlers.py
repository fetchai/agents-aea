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

"""This module contains the handler for the 'http_echo' skill."""

import json
from typing import cast

from aea.protocols.base import Message
from aea.protocols.default import DefaultMessage
from aea.skills.base import Handler

from packages.fetchai.protocols.http.message import HttpMessage
from packages.fetchai.skills.http_echo.dialogues import (
    DefaultDialogues,
    HttpDialogue,
    HttpDialogues,
)


class HttpHandler(Handler):
    """This implements the echo handler."""

    SUPPORTED_PROTOCOL = HttpMessage.protocol_id

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
        http_msg = cast(HttpMessage, message)

        # recover dialogue
        http_dialogues = cast(HttpDialogues, self.context.http_dialogues)
        http_dialogue = cast(HttpDialogue, http_dialogues.update(http_msg))
        if http_dialogue is None:
            self._handle_unidentified_dialogue(http_msg)
            return

        # handle message
        if http_msg.performative == HttpMessage.Performative.REQUEST:
            self._handle_request(http_msg, http_dialogue)
        else:
            self._handle_invalid(http_msg, http_dialogue)

    def _handle_unidentified_dialogue(self, http_msg: HttpMessage) -> None:
        """
        Handle an unidentified dialogue.

        :param http_msg: the message
        """
        self.context.logger.info(
            "received invalid http message={}, unidentified dialogue.".format(http_msg)
        )
        default_dialogues = cast(DefaultDialogues, self.context.default_dialogues)
        default_msg = DefaultMessage(
            performative=DefaultMessage.Performative.ERROR,
            dialogue_reference=default_dialogues.new_self_initiated_dialogue_reference(),
            error_code=DefaultMessage.ErrorCode.INVALID_DIALOGUE,
            error_msg="Invalid dialogue.",
            error_data={"http_message": http_msg.encode()},
        )
        default_msg.counterparty = http_msg.counterparty
        default_dialogues.update(default_msg)
        self.context.outbox.put_message(message=default_msg)

    def _handle_request(
        self, http_msg: HttpMessage, http_dialogue: HttpDialogue
    ) -> None:
        """
        Handle a Http request.

        :param http_msg: the http message
        :param http_dialogue: the http dialogue
        :return: None
        """
        self.context.logger.info(
            "received http request with method={}, url={} and body={!r}".format(
                http_msg.method, http_msg.url, http_msg.bodyy,
            )
        )
        if http_msg.method == "get":
            self._handle_get(http_msg, http_dialogue)
        elif http_msg.method == "post":
            self._handle_post(http_msg, http_dialogue)

    def _handle_get(self, http_msg: HttpMessage, http_dialogue: HttpDialogue) -> None:
        """
        Handle a Http request of verb GET.

        :param http_msg: the http message
        :param http_dialogue: the http dialogue
        :return: None
        """
        http_response = HttpMessage(
            dialogue_reference=http_dialogue.dialogue_label.dialogue_reference,
            target=http_msg.message_id,
            message_id=http_msg.message_id + 1,
            performative=HttpMessage.Performative.RESPONSE,
            version=http_msg.version,
            status_code=200,
            status_text="Success",
            headers=http_msg.headers,
            bodyy=json.dumps({"tom": {"type": "cat", "age": 10}}).encode("utf-8"),
        )
        self.context.logger.info("responding with: {}".format(http_response))
        http_response.counterparty = http_msg.counterparty
        assert http_dialogue.update(http_response)
        self.context.outbox.put_message(message=http_response)

    def _handle_post(self, http_msg: HttpMessage, http_dialogue: HttpDialogue) -> None:
        """
        Handle a Http request of verb POST.

        :param http_msg: the http message
        :param http_dialogue: the http dialogue
        :return: None
        """
        http_response = HttpMessage(
            dialogue_reference=http_dialogue.dialogue_label.dialogue_reference,
            target=http_msg.message_id,
            message_id=http_msg.message_id + 1,
            performative=HttpMessage.Performative.RESPONSE,
            version=http_msg.version,
            status_code=200,
            status_text="Success",
            headers=http_msg.headers,
            bodyy=b"",
        )
        self.context.logger.info("responding with: {}".format(http_response))
        http_response.counterparty = http_msg.counterparty
        assert http_dialogue.update(http_response)
        self.context.outbox.put_message(message=http_response)

    def _handle_invalid(
        self, http_msg: HttpMessage, http_dialogue: HttpDialogue
    ) -> None:
        """
        Handle an invalid http message.

        :param http_msg: the http message
        :param http_dialogue: the http dialogue
        :return: None
        """
        self.context.logger.warning(
            "cannot handle http message of performative={} in dialogue={}.".format(
                http_msg.performative, http_dialogue
            )
        )

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass
