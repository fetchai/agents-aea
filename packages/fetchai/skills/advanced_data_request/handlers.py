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

"""This package contains handlers for the advanced_data_request skill."""

import json
from typing import Any, Dict, Optional, SupportsFloat, cast

from aea.configurations.base import PublicId
from aea.protocols.base import Message
from aea.skills.base import Handler

from packages.fetchai.protocols.http.message import HttpMessage
from packages.fetchai.protocols.prometheus.message import PrometheusMessage
from packages.fetchai.skills.advanced_data_request.dialogues import (
    HttpDialogue,
    HttpDialogues,
    PrometheusDialogue,
    PrometheusDialogues,
)


def find(dotted_path: str, data: Dict[str, Any]) -> Optional[Any]:
    """Find entry at dotted_path in data"""

    keys = dotted_path.split(".")
    value = data
    for key in keys:
        value = value.get(key, {})
    return None if value == {} else value


def is_number(value: SupportsFloat) -> bool:
    """Test if value is a number"""
    if value is None:
        return False
    try:
        float(value)
        return True
    except ValueError:
        return False


class HttpHandler(Handler):
    """This class provides a simple http handler."""

    SUPPORTED_PROTOCOL = HttpMessage.protocol_id

    def __init__(self, **kwargs: Any):
        """Initialize the handler."""
        super().__init__(**kwargs)

        self._http_server_id = None  # type: Optional[PublicId]

    def setup(self) -> None:
        """Set up the handler."""
        self.context.logger.info("setting up HttpHandler")

        # skill can be used with or without http server
        if (
            self.context.advanced_data_request_model.use_http_server
        ):  # pylint: disable=import-outside-toplevel
            from packages.fetchai.connections.http_server.connection import (
                PUBLIC_ID as HTTP_SERVER_ID,
            )

            self._http_server_id = HTTP_SERVER_ID

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        """

        message = cast(HttpMessage, message)

        # recover dialogue
        http_dialogues = cast(HttpDialogues, self.context.http_dialogues)
        http_dialogue = cast(HttpDialogue, http_dialogues.update(message))
        if http_dialogue is None:
            self._handle_unidentified_dialogue(message)
            return

        if (
            message.performative == HttpMessage.Performative.RESPONSE
            and message.status_code == 200
        ):
            self._handle_response(message)
        elif message.performative == HttpMessage.Performative.REQUEST:
            self._handle_request(message, http_dialogue)
        else:
            self.context.logger.info(
                f"got unexpected http message: code = {message.status_code}"
            )

    def _handle_response(self, http_msg: HttpMessage) -> None:
        """
        Handle an Http response.

        :param http_msg: the http message
        """

        model = self.context.advanced_data_request_model

        msg_body = json.loads(http_msg.body)

        success = False
        for output in model.outputs:
            json_path = output["json_path"]

            # find desired output data in msg_body
            value = cast(SupportsFloat, find(json_path, msg_body))

            # if value is a numeric type, store it as fixed-point with number of decimals
            if is_number(value):
                float_value = float(value)
                int_value = int(float_value * 10 ** model.decimals)
                observation = {
                    output["name"]: {"value": int_value, "decimals": model.decimals}
                }
            elif isinstance(value, str):
                observation = {output["name"]: {"value": value}}
            else:
                self.context.logger.warning(
                    f"No valid output for {output['name']} found in response."
                )
                continue
            success = True
            self.context.shared_state.update(observation)
            self.context.logger.info(f"Observation: {observation}")

        if success and self.context.prometheus_dialogues.enabled:
            metric_name = "num_retrievals"
            self.context.behaviours.advanced_data_request_behaviour.update_prometheus_metric(
                metric_name, "inc", 1.0, {}
            )

    def _handle_request(
        self, http_msg: HttpMessage, http_dialogue: HttpDialogue
    ) -> None:
        """
        Handle a Http request.

        :param http_msg: the http message
        :param http_dialogue: the http dialogue
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
                self.context.logger.info("method 'post' is not supported.")
        else:
            self.context.logger.info("http server is not enabled.")

    def _handle_get(self, http_msg: HttpMessage, http_dialogue: HttpDialogue) -> None:
        """
        Handle a Http request of verb GET.

        :param http_msg: the http message
        :param http_dialogue: the http dialogue
        """
        model = self.context.advanced_data_request_model
        outputs = [output["name"] for output in model.outputs]
        data = {
            key: value
            for (key, value) in self.context.shared_state.items()
            if key in outputs
        }

        http_response = http_dialogue.reply(
            performative=HttpMessage.Performative.RESPONSE,
            target_message=http_msg,
            version=http_msg.version,
            status_code=200,
            status_text="Success",
            headers=http_msg.headers,
            body=json.dumps(data).encode("utf-8"),
        )
        self.context.logger.info("responding with: {}".format(http_response))
        self.context.outbox.put_message(message=http_response)

        if self.context.prometheus_dialogues.enabled:
            metric_name = "num_requests"
            self.context.behaviours.advanced_data_request_behaviour.update_prometheus_metric(
                metric_name, "inc", 1.0, {}
            )

    def _handle_unidentified_dialogue(self, msg: Message) -> None:
        """
        Handle an unidentified dialogue.

        :param msg: the unidentified message to be handled
        """
        self.context.logger.info(
            "received invalid message={}, unidentified dialogue.".format(msg)
        )

    def teardown(self) -> None:
        """Teardown the handler."""


class PrometheusHandler(Handler):
    """This class handles responses from the prometheus server."""

    SUPPORTED_PROTOCOL = PrometheusMessage.protocol_id

    def setup(self) -> None:
        """Set up the handler."""
        self.context.logger.info("setting up PrometheusHandler")

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
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

        if message.performative == PrometheusMessage.Performative.RESPONSE:
            self.context.logger.debug(
                f"Prometheus response ({message.code}): {message.message}"
            )
        else:  # pragma: nocover
            self.context.logger.debug(
                f"got unexpected prometheus message: Performative = {PrometheusMessage.Performative}"
            )

    def _handle_unidentified_dialogue(self, msg: Message) -> None:
        """
        Handle an unidentified dialogue.

        :param msg: the unidentified message to be handled
        """

        self.context.logger.info(
            "received invalid message={}, unidentified dialogue.".format(msg)
        )

    def teardown(self) -> None:
        """Teardown the handler."""
