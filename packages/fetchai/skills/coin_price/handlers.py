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

"""This package contains handlers for the coin_price skill."""

import json
from typing import Optional, cast

from aea.configurations.base import PublicId
from aea.mail.base import EnvelopeContext
from aea.protocols.base import Message
from aea.skills.base import Handler

from packages.fetchai.protocols.http.message import HttpMessage
from packages.fetchai.protocols.prometheus.message import PrometheusMessage
from packages.fetchai.skills.coin_price.dialogues import (
    HttpDialogue,
    HttpDialogues,
    PrometheusDialogue,
    PrometheusDialogues,
)


class HttpHandler(Handler):
    """This class provides a simple http handler."""

    SUPPORTED_PROTOCOL = HttpMessage.protocol_id

    def __init__(self, **kwargs):
        """Initialize the handler."""
        super().__init__(**kwargs)

        self.handled_message = None
        self._http_server_id = None  # type: Optional[PublicId]

    def setup(self) -> None:
        """Set up the handler."""
        self.context.logger.info("setting up HttpHandler")

        # skill can be used with or without http server
        if (
            self.context.coin_price_model.use_http_server
        ):  # pylint: disable=import-outside-toplevel
            from packages.fetchai.connections.http_server.connection import (
                PUBLIC_ID as HTTP_SERVER_ID,
            )

            self._http_server_id = HTTP_SERVER_ID

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :return: None
        """

        message = cast(HttpMessage, message)

        # recover dialogue
        http_dialogues = cast(HttpDialogues, self.context.http_dialogues)
        http_dialogue = cast(HttpDialogue, http_dialogues.update(message))
        if http_dialogue is None:
            self._handle_unidentified_dialogue(message)
            return

        self.handled_message = message
        if (
            message.performative == HttpMessage.Performative.RESPONSE
            and message.status_code == 200
        ):
            self._handle_response(message)
        elif message.performative == HttpMessage.Performative.REQUEST:
            self._handle_request(message, http_dialogue)
        else:
            self.context.logger.info(
                "got unexpected http message: code = " + str(message.status_code)
            )

    def _handle_response(self, http_msg: HttpMessage) -> None:
        """
        Handle an Http response.

        :param http_msg: the http message
        :return: None
        """

        model = self.context.coin_price_model

        msg_body = json.loads(http_msg.body)
        price_result = msg_body.get(model.coin_id, None)

        if price_result is None:
            self.context.logger.info("failed to get price: unexpected result")
        else:
            price = price_result.get(model.currency, None)
            value = int(price * (10 ** model.decimals))

            if price is None:
                self.context.logger.info("failed to get price: no price listed")
            else:
                oracle_data = {
                    "value": value,
                    "decimals": model.decimals,
                }
                self.context.shared_state["oracle_data"] = oracle_data
                self.context.logger.info(
                    f"{model.coin_id} price = {price} {model.currency}"
                )
                if self.context.prometheus_dialogues.enabled:
                    self.context.behaviours.coin_price_behaviour.update_prometheus_metric(
                        "num_retrievals", "inc", 1.0, {}
                    )

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
                http_msg.method, http_msg.url, http_msg.body,
            )
        )

        if self._http_server_id:
            if http_msg.method == "get":
                self._handle_get(http_msg, http_dialogue)
            elif http_msg.method == "post":
                self._handle_post(http_msg, http_dialogue)
        else:
            self.context.logger.info("http server is not enabled.")

    def _handle_get(self, http_msg: HttpMessage, http_dialogue: HttpDialogue) -> None:
        """
        Handle a Http request of verb GET.

        :param http_msg: the http message
        :param http_dialogue: the http dialogue
        :return: None
        """
        http_response = http_dialogue.reply(
            performative=HttpMessage.Performative.RESPONSE,
            target_message=http_msg,
            version=http_msg.version,
            status_code=200,
            status_text="Success",
            headers=http_msg.headers,
            body=json.dumps(self.context.shared_state.get("oracle_data", "")).encode(
                "utf-8"
            ),
        )
        self.context.logger.info("responding with: {}".format(http_response))
        envelope_context = EnvelopeContext(connection_id=self._http_server_id)
        self.context.outbox.put_message(message=http_response, context=envelope_context)

        if self.context.prometheus_dialogues.enabled:
            self.context.behaviours.coin_price_behaviour.update_prometheus_metric(
                "num_requests", "inc", 1.0, {}
            )

    def _handle_post(self, http_msg: HttpMessage, http_dialogue: HttpDialogue) -> None:
        """
        Handle a Http request of verb POST.

        :param http_msg: the http message
        :param http_dialogue: the http dialogue
        :return: None
        """
        http_response = http_dialogue.reply(
            performative=HttpMessage.Performative.RESPONSE,
            target_message=http_msg,
            version=http_msg.version,
            status_code=200,
            status_text="Success",
            headers=http_msg.headers,
            body=b"",
        )
        self.context.logger.info("responding with: {}".format(http_response))
        self.context.outbox.put_message(message=http_response)

    def _handle_unidentified_dialogue(self, msg: Message) -> None:
        """
        Handle an unidentified dialogue.

        :param msg: the unidentified message to be handled
        :return: None
        """

        self.context.logger.info(
            "received invalid message={}, unidentified dialogue.".format(msg)
        )

    def teardown(self) -> None:
        """
        Teardown the handler.

        :return: None
        """
        pass


class PrometheusHandler(Handler):
    """This class handles responses from the prometheus server."""

    SUPPORTED_PROTOCOL = PrometheusMessage.protocol_id

    def __init__(self, **kwargs):
        """Initialize the handler."""
        super().__init__(**kwargs)

        self.handled_message = None

    def setup(self) -> None:
        """Set up the handler."""
        self.context.logger.info("setting up PrometheusHandler")

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :return: None
        """

        message = cast(PrometheusMessage, message)

        # recover dialogue
        prometheus_dialogues = cast(
            PrometheusDialogues, self.context.prometheus_dialogues
        )
        prometheus_dialogue = cast(
            PrometheusDialogue, prometheus_dialogues.update(message)
        )
        if prometheus_dialogue is None:
            self._handle_unidentified_dialogue(message)
            return

        self.handled_message = message
        if message.performative == PrometheusMessage.Performative.RESPONSE:
            self.context.logger.debug(
                f"Prometheus response ({message.code}): {message.message}"
            )
        else:
            self.context.logger.debug(
                f"got unexpected prometheus message: Performative = {PrometheusMessage.Performative}"
            )

    def _handle_unidentified_dialogue(self, msg: Message) -> None:
        """
        Handle an unidentified dialogue.

        :param msg: the unidentified message to be handled
        :return: None
        """

        self.context.logger.info(
            "received invalid message={}, unidentified dialogue.".format(msg)
        )

    def teardown(self) -> None:
        """
        Teardown the handler.

        :return: None
        """
        pass
