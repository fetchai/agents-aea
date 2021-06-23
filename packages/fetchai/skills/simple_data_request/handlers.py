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

"""This package contains a handler to process HTTP responses."""

from typing import Any, cast

from aea.protocols.base import Message
from aea.skills.base import Handler

from packages.fetchai.protocols.http.message import HttpMessage
from packages.fetchai.skills.simple_data_request.dialogues import (
    HttpDialogue,
    HttpDialogues,
)


class HttpHandler(Handler):
    """This class represents the handler for HTTP messages."""

    SUPPORTED_PROTOCOL = HttpMessage.protocol_id

    def __init__(self, **kwargs: Any):
        """
        Initialize the handler.

        :param kwargs: keyword arguments
        """
        self.shared_state_key = kwargs.pop("shared_state_key", None)
        if self.shared_state_key is None:
            raise ValueError("No shared_state_key provided!")
        super().__init__(**kwargs)

    def setup(self) -> None:
        """Implement the setup."""

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to an envelope.

        :param message: the message
        """
        http_msg = cast(HttpMessage, message)

        # recover dialogue
        http_dialogues = cast(HttpDialogues, self.context.http_dialogues)
        http_dialogue = cast(HttpDialogue, http_dialogues.update(http_msg))
        if http_dialogue is None:
            self._handle_unidentified_dialogue(http_msg)
            return

        # handle message (only process responses, we do not expect requests)
        if http_msg.performative == HttpMessage.Performative.RESPONSE:
            self._handle_response(http_msg, http_dialogue)
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

    def _handle_response(
        self, http_msg: HttpMessage, http_dialogue: HttpDialogue
    ) -> None:
        """
        Handle a http response.

        :param http_msg: the message
        :param http_dialogue: the dialogue object
        """
        self.context.logger.debug(
            "received http response={} in dialogue={}.".format(http_msg, http_dialogue)
        )
        data_received = http_msg.body

        # save the data in the shared state to make it accessible to other skills
        self.context.logger.info(
            "updating shared_state with received data={!r}!".format(data_received)
        )
        self.context.shared_state[self.shared_state_key] = data_received

    def _handle_invalid(
        self, http_msg: HttpMessage, http_dialogue: HttpDialogue
    ) -> None:
        """
        Handle a http message of invalid performative.

        :param http_msg: the message
        :param http_dialogue: the dialogue object
        """
        self.context.logger.warning(
            "cannot handle http message of performative={} in dialogue={}.".format(
                http_msg.performative, http_dialogue
            )
        )

    def teardown(self) -> None:
        """Implement the handler teardown."""
