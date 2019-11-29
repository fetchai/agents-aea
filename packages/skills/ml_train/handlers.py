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
from typing import cast, TYPE_CHECKING, Optional, List, Dict

from aea.configurations.base import ProtocolId
from aea.decision_maker.messages.transaction import TransactionMessage
from aea.helpers.dialogue.base import DialogueLabel
from aea.protocols.base import Message
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer
from aea.protocols.oef.message import OEFMessage
from aea.protocols.oef.models import Description
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

    SUPPORTED_PROTOCOL = "ml_trade"

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
        ml_msg = cast(MLTradeMessage, message)
        ml_msg_performative = MLTradeMessage.Performative(ml_msg.get("performative"))
        if ml_msg_performative == MLTradeMessage.Performative.TERMS:
            self._handle_terms(ml_msg, sender)

    def _handle_terms(self, msg: MLTradeMessage, sender: str):
        """Handle the terms of the request."""
        terms = cast(Description, msg.body.get("terms"))
        logger.debug("Received terms message from {}: terms={}".format(sender, terms.values))

        ledger_id = terms.values["ledger_id"]
        amount = terms.values["price"]
        address = terms.values["address"]

        tx_msg = TransactionMessage(performative=TransactionMessage.Performative.PROPOSE,
                                    skill_id=self.context._skill.config.name,
                                    transaction_id="transaction0",
                                    sender=self.context.agent_public_keys[ledger_id],
                                    counterparty=address,
                                    is_sender_buyer=True,
                                    currency_pbk=terms.values['currency_pbk'],
                                    amount=amount,
                                    sender_tx_fee=self.context.strategy.max_tx_fee,
                                    counterparty_tx_fee=terms.values["seller_tx_fee"],
                                    # TODO the following parameter should be removed and refactored properly.
                                    quantities_by_good_pbk={},
                                    ledger_id=ledger_id,
                                    # this is used to retrieve the opponent address later
                                    dialogue_label=DialogueLabel(('',''), sender, self.context.agent_public_key).json,
                                    # this is used to send the terms later - because the seller is stateless and must know
                                    # what terms have been accepted
                                    terms=terms)
        self.context.decision_maker_message_queue.put_nowait(tx_msg)
        logger.info("[{}]: proposing the transaction to the decision maker. Waiting for confirmation ...".format(self.context.agent_name))

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
            strategy.is_searching = False
            # pick first agent found
            opponent_pbk = agents[0]
            query = strategy.get_service_query()
            logger.info("[{}]: sending CFT to agent={}".format(self.context.agent_name, opponent_pbk[-5:]))
            cft_msg = MLTradeMessage(performative=MLTradeMessage.Performative.CFT, query=query)
            self.context.outbox.put_message(to=opponent_pbk,
                                            sender=self.context.agent_public_key,
                                            protocol_id=MLTradeMessage.protocol_id,
                                            message=MLTradeSerializer().encode(cft_msg))
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
        tx_msg_response = cast(TransactionMessage, message)
        if tx_msg_response is not None and TransactionMessage.Performative(tx_msg_response.get("performative")) == TransactionMessage.Performative.ACCEPT:
            logger.info("[{}]: transaction was successful.".format(self.context.agent_name))
            transaction_digest = tx_msg_response.body["transaction_digest"]
            terms = tx_msg_response.body["terms"]
            dialogue_label = DialogueLabel.from_json(cast(Dict[str, str], tx_msg_response.body["dialogue_label"]))
            counterparty_pbk = dialogue_label.dialogue_opponent_pbk
            ml_accept = MLTradeMessage(
                performative=MLTradeMessage.Performative.ACCEPT,
                tx_digest=transaction_digest,
                terms=terms
            )
            self.context.outbox.put_message(to=counterparty_pbk,
                                            sender=self.context.agent_public_key,
                                            protocol_id=MLTradeMessage.protocol_id,
                                            message=MLTradeSerializer().encode(ml_accept))
            logger.info("[{}]: Sending accept to counterparty={} with transaction digest={} and terms={}."
                        .format(self.context.agent_name, counterparty_pbk[-5:], transaction_digest, terms))
        else:
            logger.info("[{}]: transaction was not successful.".format(self.context.agent_name))

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass
