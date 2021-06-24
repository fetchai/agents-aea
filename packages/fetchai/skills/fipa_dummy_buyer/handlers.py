# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
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
"""This package contains handlers for the fipa dummy buyer skill."""
from typing import Optional, cast

from aea.configurations.base import PublicId
from aea.protocols.base import Message
from aea.skills.base import Handler

from packages.fetchai.protocols.fipa.message import FipaMessage
from packages.fetchai.skills.fipa_dummy_buyer.dialogues import FipaDialogues


class FipaBuyerHandler(Handler):
    """This class implements a FIPA handler."""

    SUPPORTED_PROTOCOL = FipaMessage.protocol_id  # type: Optional[PublicId]

    def setup(self) -> None:
        """Implement the setup."""

    def handle(self, message: Message) -> None:
        """Handle an evelope."""
        dialogues = cast(FipaDialogues, self.context.fipa_dialogues)
        if message.performative == FipaMessage.Performative.PROPOSE:
            buyer_dialogue = dialogues.update(message)
            if not buyer_dialogue:
                self.context.logger.error("error on propose message dialogue update")
                return
            # got a message, switch off initializer
            self.context.behaviours.initializer.is_enabled = False
            accept_msg = buyer_dialogue.reply(
                performative=FipaMessage.Performative.ACCEPT, target_message=message
            )
            self.context.outbox.put_message(message=accept_msg)
        elif message.performative == FipaMessage.Performative.MATCH_ACCEPT:
            buyer_dialogue = dialogues.update(message)
            if not buyer_dialogue:
                self.context.logger.error(
                    "error on MATCH_ACCEPT message dialogue update"
                )
                return
            end_msg = buyer_dialogue.reply(
                performative=FipaMessage.Performative.END, target_message=message
            )
            self.context.outbox.put_message(message=end_msg)
            self.context.logger.info("FIPA INTERACTION COMPLETE")
        else:
            self.context.logger.error(
                f"unsupported performative: {message.performative}"
            )

    def teardown(self) -> None:
        """Implement the handler teardown."""
