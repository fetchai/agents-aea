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

"""This package contains a scaffold of a behaviour."""
import datetime
import logging
from typing import cast, TYPE_CHECKING

from aea.decision_maker.messages.transaction import TransactionMessage
from aea.helpers.dialogue.base import DialogueLabel
from aea.protocols.fipa.message import FIPAMessage
from aea.protocols.fipa.serialization import FIPASerializer
from aea.protocols.oef.message import OEFMessage
from aea.protocols.oef.serialization import DEFAULT_OEF, OEFSerializer
from aea.skills.base import Behaviour

if TYPE_CHECKING:
    from packages.skills.weather_client_eth.dialogues import Dialogues
    from packages.skills.weather_client_eth.strategy import Strategy
else:
    from weather_client_eth.dialogues import Dialogues
    from weather_client_eth.strategy import Strategy

logger = logging.getLogger("aea.weather_client_ledger_skill")


class MySearchBehaviour(Behaviour):
    """This class scaffolds a behaviour."""

    def __init__(self, **kwargs):
        """Initialise the class."""
        super().__init__(**kwargs)
        self._search_id = 0

    def setup(self) -> None:
        """Implement the setup for the behaviour."""
        balance = self.context.ledger_apis.token_balance('fetchai', cast(str, self.context.agent_addresses.get('fetchai')))
        if balance > 0:
            logger.info("[{}]: starting balance on fetchai ledger={}.".format(self.context.agent_name, balance))
        else:
            logger.warning("[{}]: you have no starting balance on fetchai ledger!".format(self.context.agent_name))
            # TODO: deregister skill from filter

    def act(self) -> None:
        """
        Implement the act.

        :return: None
        """
        strategy = cast(Strategy, self.context.strategy)
        if strategy.is_searching and strategy.is_time_to_search():
            self._search_id += 1
            strategy.last_search_time = datetime.datetime.now()
            query = strategy.get_service_query()
            search_request = OEFMessage(oef_type=OEFMessage.Type.SEARCH_SERVICES,
                                        id=self._search_id,
                                        query=query)
            self.context.outbox.put_message(to=DEFAULT_OEF,
                                            sender=self.context.agent_public_key,
                                            protocol_id=OEFMessage.protocol_id,
                                            message=OEFSerializer().encode(search_request))

    def teardown(self) -> None:
        """
        Implement the task teardown.

        :return: None
        """
        balance = self.context.ledger_apis.token_balance('fetchai', cast(str, self.context.agent_addresses.get('fetchai')))
        logger.info("[{}]: ending balance on fetchai ledger={}.".format(self.context.agent_name, balance))


class MyTransactionBehaviour(Behaviour):
    """Implement the transaction behaviour."""

    def __init__(self, **kwargs):
        """Initialise the class."""
        super().__init__(**kwargs)
        self._received_tx_message = False

    def setup(self) -> None:
        """Implement the setup for the behaviour."""
        pass

    def act(self) -> None:
        """
        Implement the act.

        :return: None
        """
        if not self._received_tx_message and not self.context.message_in_queue.empty():
            tx_msg_response = self.context.message_in_queue.get_nowait()
            if tx_msg_response is not None and \
                    TransactionMessage.Performative(tx_msg_response.get("performative")) == TransactionMessage.Performative.ACCEPT:
                logger.info("[{}]: transaction was successful.".format(self.context.agent_name))
                json_data = {'transaction_digest': tx_msg_response.get("transaction_digest")}
                dialogue_label = DialogueLabel.from_json(tx_msg_response.get("dialogue_label"))
                dialogues = cast(Dialogues, self.context.dialogues)
                dialogue = dialogues.dialogues[dialogue_label]
                fipa_msg = cast(FIPAMessage, dialogue.last_incoming_message)
                new_message_id = cast(int, fipa_msg.get("message_id")) + 1
                new_target_id = cast(int, fipa_msg.get("target")) + 1
                dialogue_id = cast(int, fipa_msg.get("dialogue_id"))
                counterparty_pbk = dialogue.dialogue_label.dialogue_opponent_pbk
                inform_msg = FIPAMessage(message_id=new_message_id,
                                         dialogue_id=dialogue_id,
                                         target=new_target_id,
                                         performative=FIPAMessage.Performative.INFORM,
                                         json_data=json_data)
                dialogue.outgoing_extend(inform_msg)
                self.context.outbox.put_message(to=counterparty_pbk,
                                                sender=self.context.agent_public_key,
                                                protocol_id=FIPAMessage.protocol_id,
                                                message=FIPASerializer().encode(inform_msg))
                logger.info("[{}]: informing counterparty={} of transaction digest.".format(self.context.agent_name, counterparty_pbk[-5:]))
                self._received_tx_message = True
            else:
                logger.info("[{}]: transaction was not successful.".format(self.context.agent_name))

    def teardown(self) -> None:
        """
        Implement the task teardown.

        :return: None
        """
        pass
