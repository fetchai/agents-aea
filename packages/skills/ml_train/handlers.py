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
from typing import cast, TYPE_CHECKING, Optional, List

from aea.configurations.base import ProtocolId
from aea.decision_maker.messages.transaction import TransactionMessage
from aea.protocols.base import Message
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer
from aea.protocols.oef.message import OEFMessage
from aea.skills.base import Handler

if TYPE_CHECKING or "pytest" in sys.modules:
    from packages.protocols.ml_trade.message import MLTradeMessage
    from packages.protocols.ml_trade.serialization import MLTradeSerializer
    from packages.skills.ml_train.strategy import Strategy
    # from packages.skills.ml_train.tasks import MLTask
else:
    from ml_trade_protocol.message import MLTradeMessage
    from ml_trade_protocol.serialization import MLTradeSerializer
    from ml_train_skill.strategy import Strategy
    # from gym_skill.tasks import GymTask

logger = logging.getLogger("aea.ml_train_skill")


class TrainHandler(Handler):
    """Gym handler."""

    SUPPORTED_PROTOCOL = "default"

    def __init__(self, **kwargs):
        """Initialize the handler."""
        logger.info("TrainHandler.__init__: arguments: {}".format(kwargs))
        super().__init__(**kwargs)

    def setup(self) -> None:
        """Set up the handler."""
        logger.info("Train handler: setup method called.")

    def handle(self, message: Message, sender: str) -> None:
        """
        Handle messages.

        :param message: the message
        :param sender: the sender
        :return: None
        """
        default_message = cast(DefaultMessage, message)
        ml_msg = MLTradeSerializer().decode(default_message.get("content"))
        ml_msg = cast(MLTradeMessage, ml_msg)
        ml_msg_performative = MLTradeMessage.Performative(ml_msg.get("performative"))
        if ml_msg_performative == MLTradeMessage.Performative.TERMS:
            self._handle_terms(ml_msg, sender)

    def _handle_terms(self, msg: MLTradeMessage, sender: str):
        """Handle the terms of the request."""
        logger.debug("Received terms message from {}: {}".format(sender, msg.body))
        # tx_msg = TransactionMessage(performative=TransactionMessage.Performative.PROPOSE,
        #                             skill_id="weather_client_ledger",
        #                             transaction_id="transaction0",
        #                             sender=self.context.agent_public_keys[ledger_id],
        #                             counterparty=address,
        #                             is_sender_buyer=True,
        #                             currency_pbk=proposal.values['currency_pbk'],
        #                             amount=proposal.values['price'],
        #                             sender_tx_fee=strategy.max_buyer_tx_fee,
        #                             counterparty_tx_fee=proposal.values['seller_tx_fee'],
        #                             quantities_by_good_pbk={},
        #                             dialogue_label=dialogue.dialogue_label.json,
        #                             ledger_id=ledger_id)
        # self.context.decision_maker_message_queue.put_nowait(tx_msg)
        # logger.info("[{}]: proposing the transaction to the decision maker. Waiting for confirmation ...".format(
        #     self.context.agent_name))

    def teardown(self) -> None:
        """
        Teardown the handler.

        :return: None
        """
        logger.info("Train handler: teardown method called.")


class OEFHandler(Handler):
    """This class scaffolds a handler."""

    SUPPORTED_PROTOCOL = OEFMessage.protocol_id  # type: Optional[ProtocolId]

    def setup(self) -> None:
        """Call to setup the handler."""
        pass

    def handle(self, message: Message, sender: str) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :param sender: the sender
        :return: None
        """
        # convenience representations
        oef_msg = cast(OEFMessage, message)
        oef_msg_type = OEFMessage.Type(oef_msg.get("type"))

        if oef_msg_type is OEFMessage.Type.SEARCH_RESULT:
            agents = cast(List[str], oef_msg.get("agents"))
            self._handle_search(agents)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass

    def _handle_search(self, agents: List[str]) -> None:
        """
        Handle the search response.

        :param agents: the agents returned by the search
        :return: None
        """
        if len(agents) > 0:
            logger.info("[{}]: found agents={}, stopping search.".format(self.context.agent_name, list(map(lambda x: x[-5:], agents))))
            strategy = cast(Strategy, self.context.strategy)
            # stopping search
            # strategy.is_searching = False
            # pick first agent found
            opponent_pbk = agents[0]
            query = strategy.get_service_query()
            logger.info("[{}]: sending CFT to agent={}".format(self.context.agent_name, opponent_pbk[-5:]))
            cft_msg = MLTradeMessage(performative=MLTradeMessage.Performative.CFT, query=query)
            ml_msg_bytes = MLTradeSerializer().encode(cft_msg)
            default_msg = DefaultMessage(type=DefaultMessage.Type.BYTES, content=ml_msg_bytes)
            self.context.outbox.put_message(to=opponent_pbk,
                                            sender=self.context.agent_public_key,
                                            protocol_id=DefaultMessage.protocol_id,
                                            message=DefaultSerializer().encode(default_msg))
        else:
            logger.info("[{}]: found no agents, continue searching.".format(self.context.agent_name))


class MyTransactionHandler(Handler):
    """Implement the transaction handler."""

    SUPPORTED_PROTOCOL = TransactionMessage.protocol_id  # type: Optional[ProtocolId]

    def setup(self) -> None:
        """Implement the setup for the handler."""
        pass

    def handle(self, message: Message, sender: str) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :param sender: the sender
        :return: None
        """
        pass

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass
