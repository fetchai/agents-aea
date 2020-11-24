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

"""This package contains handlers for the fetch_beacon skill."""

import json
from typing import cast

from vyper.utils import keccak256

from aea.protocols.base import Message
from aea.skills.base import Handler

from packages.fetchai.protocols.http.message import HttpMessage
from packages.fetchai.skills.fetch_beacon.dialogues import HttpDialogue, HttpDialogues


class HttpHandler(Handler):
    """This class provides a simple http handler."""

    SUPPORTED_PROTOCOL = HttpMessage.protocol_id

    def __init__(self, **kwargs):
        """Initialize the handler."""
        super().__init__(**kwargs)
        self.received_http_count = 0
        self.handled_message = None

    def setup(self) -> None:
        """Set up the handler."""
        self.context.logger.info("setting up HttpHandler")

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
        else:
            self.context.logger.info(
                "got unexpected http response: code = " + str(message.status_code)
            )

    def _handle_response(self, message: HttpMessage) -> None:
        """
        Handle an http response.

        :param msg: the http message to be handled
        :return: None
        """

        msg_body = json.loads(message.body)

        # get entropy and block data
        entropy = (
            msg_body.get("result", {})
            .get("block", {})
            .get("header", {})
            .get("entropy", {})
            .get("group_signature", {})
        )
        block_hash = msg_body.get("result", {}).get("block_id", {}).get("hash", {})
        block_height = int(
            msg_body.get("result", {})
            .get("block", {})
            .get("header", {})
            .get("height", {})
        )

        if entropy is None:
            self.context.logger.info("entropy not present")
        else:
            beacon_data = {
                "entropy": keccak256(entropy.encode("utf-8")),
                "block_hash": bytes.fromhex(block_hash),
                "block_height": block_height,
            }
            self.context.logger.info(
                "Beacon info: "
                + str({"block_height": block_height, "entropy": entropy})
            )
            self.context.shared_state["oracle_data"] = beacon_data

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
        self.context.logger.info("tearing down HttpHandler")
