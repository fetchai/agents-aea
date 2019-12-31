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

"""This module contains the handler for the 'ml_data_provider' skill."""
import logging
from typing import cast

from aea.protocols.base import Message
from aea.skills.base import Handler
from packages.protocols.ml_trade.message import MLTradeMessage
from packages.protocols.ml_trade.serialization import MLTradeSerializer
from packages.skills.ml_data_provider.strategy import Strategy

logger = logging.getLogger("aea.ml_data_provider")


class MLTradeHandler(Handler):
    """ML trade handler."""

    SUPPORTED_PROTOCOL = "ml_trade"

    def __init__(self, **kwargs):
        """Initialize the handler."""
        super().__init__(**kwargs)

    def setup(self) -> None:
        """Set up the handler."""
        logger.debug("MLTrade handler: setup method called.")

    def handle(self, message: Message) -> None:
        """
        Handle messages.

        :param message: the message
        :return: None
        """
        ml_msg = cast(MLTradeMessage, message)
        if ml_msg.performative == MLTradeMessage.Performative.CFT:
            self._handle_cft(ml_msg)
        elif ml_msg.performative == MLTradeMessage.Performative.ACCEPT:
            self._handle_accept(ml_msg)

    def _handle_cft(self, ml_trade_msg: MLTradeMessage) -> None:
        """
        Handle call for terms.

        :param ml_trade_msg: the ml trade message
        :return: None
        """
        query = ml_trade_msg.query
        logger.info("Got a Call for Terms from {}: query={}".format(ml_trade_msg.counterparty[-5:], query))
        strategy = cast(Strategy, self.context.strategy)
        if not strategy.is_matching_supply(query):
            return
        terms = strategy.generate_terms()
        logger.info("[{}]: sending to the address={} a Terms message: {}"
                    .format(self.context.agent_name, ml_trade_msg.counterparty[-5:], terms.values))
        terms_msg = MLTradeMessage(performative=MLTradeMessage.Performative.TERMS, terms=terms)
        self.context.outbox.put_message(to=ml_trade_msg.counterparty,
                                        sender=self.context.agent_address,
                                        protocol_id=MLTradeMessage.protocol_id,
                                        message=MLTradeSerializer().encode(terms_msg))

    def _handle_accept(self, ml_trade_msg: MLTradeMessage) -> None:
        """
        Handle accept.

        :param ml_trade_msg: the ml trade message
        :return: None
        """
        terms = ml_trade_msg.terms
        logger.info("Got an Accept from {}: {}".format(ml_trade_msg.counterparty[-5:], terms.values))
        strategy = cast(Strategy, self.context.strategy)
        if not strategy.is_valid_terms(terms):
            return
        batch_size = terms.values["batch_size"]
        data = strategy.sample_data(batch_size)
        logger.info("[{}]: sending to address={} a Data message: shape={}"
                    .format(self.context.agent_name, ml_trade_msg.counterparty[-5:], data[0].shape))
        data_msg = MLTradeMessage(performative=MLTradeMessage.Performative.DATA, terms=terms, data=data)
        self.context.outbox.put_message(to=ml_trade_msg.counterparty,
                                        sender=self.context.agent_address,
                                        protocol_id=MLTradeMessage.protocol_id,
                                        message=MLTradeSerializer().encode(data_msg))

    def teardown(self) -> None:
        """
        Teardown the handler.

        :return: None
        """
        logger.debug("MLTrade handler: teardown method called.")
