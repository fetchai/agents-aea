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

"""This module contains the handler for the 'gym' skill."""
import logging
import sys
from typing import cast, TYPE_CHECKING, Optional

from aea.configurations.base import ProtocolId
from aea.decision_maker.messages.transaction import TransactionMessage
from aea.protocols.base import Message
from aea.skills.base import Handler

if TYPE_CHECKING or "pytest" in sys.modules:
    from packages.protocols.ml_trade.message import MLTradeMessage
    from packages.skills.ml_data_provider.strategy import Strategy
else:
    from ml_trade_protocol.message import MLTradeMessage
    from ml_data_provider_skill.strategy import Strategy

logger = logging.getLogger("aea.ml_data_provider")


class MLTradeHandler(Handler):
    """Gym handler."""

    SUPPORTED_PROTOCOL = "ml_trade"

    def __init__(self, **kwargs):
        """Initialize the handler."""
        logger.info("MLTradeHandler.__init__: arguments: {}".format(kwargs))
        super().__init__(**kwargs)

    def setup(self) -> None:
        """Set up the handler."""
        logger.info("MLTrade handler: setup method called.")

    def handle(self, message: Message, sender: str) -> None:
        """
        Handle messages.

        :param message: the message
        :param sender: the sender
        :return: None
        """
        ml_msg = cast(MLTradeMessage, message)
        ml_msg_performative = MLTradeMessage.Performative(ml_msg.get("performative"))
        if ml_msg_performative == MLTradeMessage.Performative.CFT:
            self._handle_cft(ml_msg, sender)

    def _handle_cft(self, ml_msg, sender):
        """Handle call for terms."""
        logger.debug("Got a Call for Terms from {}: {}".format(sender, ml_msg))
        query = ml_msg.get("query")
        strategy = cast(Strategy, self.context.strategy)

    def teardown(self) -> None:
        """
        Teardown the handler.

        :return: None
        """
        logger.info("MLTrade gandler: teardown method called.")

