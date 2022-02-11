# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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

"""This module contains the handler for the 'echo' skill."""
from typing import cast

from aea.protocols.base import Message
from aea.skills.base import Handler

from packages.fetchai.protocols.default.message import DefaultMessage
from packages.fetchai.skills.echo.dialogues import DefaultDialogue, DefaultDialogues


class EchoHandler(Handler):
    """Echo handler."""

    SUPPORTED_PROTOCOL = DefaultMessage.protocol_id

    def setup(self) -> None:
        """Set up the handler."""
        self.context.logger.info("Echo Handler: setup method called.")

    def handle(self, message: Message) -> None:
        """
        Handle the message.

        :param message: the message.
        """
        default_message = cast(DefaultMessage, message)

        # recover dialogue
        default_dialogues = cast(DefaultDialogues, self.context.default_dialogues)
        default_dialogue = cast(DefaultDialogue, default_dialogues.update(message))

        if default_dialogue is None:
            self._handle_unidentified_dialogue(default_message)
            return

        # handle message
        if message.performative == DefaultMessage.Performative.BYTES:
            self._handle_bytes(default_message, default_dialogue)
        elif message.performative == DefaultMessage.Performative.ERROR:
            self._handle_error(default_message, default_dialogue)
        else:
            self._handle_invalid(default_message, default_dialogue)

    def teardown(self) -> None:
        """Teardown the handler."""
        self.context.logger.info("Echo Handler: teardown method called.")

    def _handle_unidentified_dialogue(self, message: DefaultMessage) -> None:
        """
        Handle unidentified dialogue.

        :param message: the message.
        """
        self.context.logger.info(
            "received invalid default message={}, unidentified dialogue.".format(
                message
            )
        )
        default_dialogues = cast(DefaultDialogues, self.context.default_dialogues)
        reply, _ = default_dialogues.create(
            counterparty=message.sender,
            performative=DefaultMessage.Performative.ERROR,
            error_code=DefaultMessage.ErrorCode.INVALID_DIALOGUE,
            error_msg="Invalid dialogue.",
            error_data={"default_message": message.encode()},
        )
        self.context.outbox.put_message(message=reply)

    def _handle_error(self, message: DefaultMessage, dialogue: DefaultDialogue) -> None:
        """
        Handle a message of error performative.

        :param message: the default message.
        :param dialogue: the dialogue.
        """
        self.context.logger.info(
            "received default error message={} in dialogue={}.".format(
                message, dialogue
            )
        )

    def _handle_bytes(self, message: DefaultMessage, dialogue: DefaultDialogue) -> None:
        """
        Handle a message of bytes performative.

        :param message: the default message.
        :param dialogue: the default dialogue.
        """
        self.context.logger.info(
            "Echo Handler: message={}, sender={}".format(message, message.sender)
        )
        reply = dialogue.reply(
            performative=DefaultMessage.Performative.BYTES,
            target_message=message,
            content=message.content,
        )
        self.context.outbox.put_message(message=reply)

    def _handle_invalid(
        self, message: DefaultMessage, dialogue: DefaultDialogue
    ) -> None:
        """
        Handle an invalid message.

        :param message: the message.
        :param dialogue: the dialogue.
        """
        self.context.logger.info(
            "received invalid message={} in dialogue={}.".format(message, dialogue)
        )
