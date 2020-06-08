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
from aea.skills.base import Handler

from packages.fetchai.protocols.http.message import HttpMessage


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
        if http_msg.performative == HttpMessage.Performative.REQUEST:
            self.context.logger.info(
                "[{}] received http request with method={}, url={} and body={!r}".format(
                    self.context.agent_name,
                    http_msg.method,
                    http_msg.url,
                    http_msg.bodyy,
                )
            )
            if http_msg.method == "get":
                self._handle_get(http_msg)
            elif http_msg.method == "post":
                self._handle_post(http_msg)
        else:
            self.context.logger.info(
                "[{}] received response ({}) unexpectedly!".format(
                    self.context.agent_name, http_msg
                )
            )

    def _handle_get(self, http_msg: HttpMessage) -> None:
        """
        Handle a Http request of verb GET.

        :param http_msg: the http message
        :return: None
        """
        http_response = HttpMessage(
            dialogue_reference=http_msg.dialogue_reference,
            target=http_msg.message_id,
            message_id=http_msg.message_id + 1,
            performative=HttpMessage.Performative.RESPONSE,
            version=http_msg.version,
            status_code=200,
            status_text="Success",
            headers=http_msg.headers,
            bodyy=json.dumps({"tom": {"type": "cat", "age": 10}}).encode("utf-8"),
        )
        self.context.logger.info(
            "[{}] responding with: {}".format(self.context.agent_name, http_response)
        )
        http_response.counterparty = http_msg.counterparty
        self.context.outbox.put_message(message=http_response)

    def _handle_post(self, http_msg: HttpMessage) -> None:
        """
        Handle a Http request of verb POST.

        :param http_msg: the http message
        :return: None
        """
        http_response = HttpMessage(
            dialogue_reference=http_msg.dialogue_reference,
            target=http_msg.message_id,
            message_id=http_msg.message_id + 1,
            performative=HttpMessage.Performative.RESPONSE,
            version=http_msg.version,
            status_code=200,
            status_text="Success",
            headers=http_msg.headers,
            bodyy=b"",
        )
        self.context.logger.info(
            "[{}] responding with: {}".format(self.context.agent_name, http_response)
        )
        http_response.counterparty = http_msg.counterparty
        self.context.outbox.put_message(message=http_response)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass
