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

"""This package contains a scaffold of a handler."""

import logging
from typing import Optional, cast, TYPE_CHECKING

from aea.configurations.base import ProtocolId
from aea.protocols.base import Message
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer
from aea.protocols.fipa.message import FIPAMessage
from aea.protocols.fipa.serialization import FIPASerializer
from aea.protocols.oef.models import Description, Query
from aea.skills.base import Handler

if TYPE_CHECKING:
    from packages.skills.carpark_detection.dialogues import Dialogue, Dialogues
    from packages.skills.carpark_detection.strategy import Strategy
else:
    from carpark_detection_skill.dialogues import Dialogue, Dialogues
    from carpark_detection_skill.strategy import Strategy

logger = logging.getLogger("aea.carpark_detection_skill")


class FIPAHandler(Handler):
    """This class scaffolds a handler."""

    SUPPORTED_PROTOCOL = FIPAMessage.protocol_id  # type: Optional[ProtocolId]

    def setup(self) -> None:
        """Implement the setup for the handler."""
        pass

    def handle(self, message: Message, sender: str) -> None:
        """
        Implement the reaction to an message.

        :param message: the message
        :param sender: the sender
        :return: None
        """
        # convenience representations
        fipa_msg = cast(FIPAMessage, message)
        msg_performative = FIPAMessage.Performative(fipa_msg.get('performative'))
        message_id = cast(int, fipa_msg.get('message_id'))
        dialogue_id = cast(int, fipa_msg.get('dialogue_id'))

        # recover dialogue
        dialogues = cast(Dialogues, self.context.dialogues)
        if dialogues.is_belonging_to_registered_dialogue(fipa_msg, sender, self.context.agent_public_key):
            dialogue = dialogues.get_dialogue(fipa_msg, sender, self.context.agent_public_key)
            dialogue.incoming_extend(fipa_msg)
        elif dialogues.is_permitted_for_new_dialogue(fipa_msg, sender):
            dialogue = dialogues.create_opponent_initiated(fipa_msg, sender)
            dialogue.incoming_extend(fipa_msg)
        else:
            self._handle_unidentified_dialogue(fipa_msg, sender)
            return

        # handle message
        if msg_performative == FIPAMessage.Performative.CFP:
            self._handle_cfp(fipa_msg, sender, message_id, dialogue_id, dialogue)
        elif msg_performative == FIPAMessage.Performative.DECLINE:
            self._handle_decline(fipa_msg, sender, message_id, dialogue_id, dialogue)
        elif msg_performative == FIPAMessage.Performative.ACCEPT:
            self._handle_accept(fipa_msg, sender, message_id, dialogue_id, dialogue)
        elif msg_performative == FIPAMessage.Performative.INFORM:
            self._handle_inform(fipa_msg, sender, message_id, dialogue_id, dialogue)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass

    def _handle_unidentified_dialogue(self, msg: FIPAMessage, sender: str) -> None:
        """
        Handle an unidentified dialogue.

        :param msg: the message
        :param sender: the sender
        """
        logger.info("[{}]: unidentified dialogue.".format(self.context.agent_name))
        default_msg = DefaultMessage(type=DefaultMessage.Type.ERROR,
                                     error_code=DefaultMessage.ErrorCode.INVALID_DIALOGUE.value,
                                     error_msg="Invalid dialogue.",
                                     error_data="fipa_message")  # FIPASerializer().encode(msg)
        self.context.outbox.put_message(to=sender,
                                        sender=self.context.agent_public_key,
                                        protocol_id=DefaultMessage.protocol_id,
                                        message=DefaultSerializer().encode(default_msg))

    def _handle_cfp(self, msg: FIPAMessage, sender: str, message_id: int, dialogue_id: int, dialogue: Dialogue) -> None:
        """
        Handle the CFP.

        :param msg: the message
        :param sender: the sender
        :param message_id: the message id
        :param dialogue_id: the dialogue id
        :param dialogue: the dialogue object
        :return: None
        """
        new_message_id = message_id + 1
        new_target = message_id
        logger.info("[{}]: received CFP from sender={}".format(self.context.agent_name, sender))
        query = cast(Query, msg.get("query"))
        strategy = cast(Strategy, self.context.strategy)

        if strategy.is_matching_supply(query):
            proposal, carpark_data = strategy.generate_proposal_and_data(query)
            dialogue.carpark_data = carpark_data
            dialogue.proposal = proposal
            logger.info("[{}]: sending sender={} a proposal={}".format(self.context.agent_name,
                                                                       sender,
                                                                       proposal.values))
            proposal_msg = FIPAMessage(message_id=new_message_id,
                                       dialogue_id=dialogue_id,
                                       target=new_target,
                                       performative=FIPAMessage.Performative.PROPOSE,
                                       proposal=[proposal])
            dialogue.outgoing_extend(proposal_msg)
            self.context.outbox.put_message(to=sender,
                                            sender=self.context.agent_public_key,
                                            protocol_id=FIPAMessage.protocol_id,
                                            message=FIPASerializer().encode(proposal_msg))
        else:
            logger.info("[{}]: declined the CFP from sender={}".format(self.context.agent_name, sender))
            decline_msg = FIPAMessage(message_id=new_message_id,
                                      dialogue_id=dialogue_id,
                                      target=new_target,
                                      performative=FIPAMessage.Performative.DECLINE)
            dialogue.outgoing_extend(decline_msg)
            self.context.outbox.put_message(to=sender,
                                            sender=self.context.agent_public_key,
                                            protocol_id=FIPAMessage.protocol_id,
                                            message=FIPASerializer().encode(decline_msg))

    def _handle_decline(self, msg: FIPAMessage, sender: str, message_id: int, dialogue_id: int, dialogue: Dialogue) -> None:
        """
        Handle the Decline.

        :param msg: the message
        :param sender: the sender
        :param message_id: the message id
        :param dialogue_id: the dialogue id
        :param dialogue: the dialogue object
        :return: None
        """
        logger.info("[{}]: received DECLINE from sender={}".format(self.context.agent_name, sender))
        dialogues = cast(Dialogues, self.context.dialogues)
        dialogues.dialogue_stats.add_dialogue_endstate(Dialogue.EndState.DECLINED_PROPOSE)

    def _handle_accept(self, msg: FIPAMessage, sender: str, message_id: int, dialogue_id: int, dialogue: Dialogue) -> None:
        """
        Handle the Accept.

        :param msg: the message
        :param sender: the sender
        :param message_id: the message id
        :param dialogue_id: the dialogue id
        :param dialogue: the dialogue object
        :return: None
        """
        new_message_id = message_id + 1
        new_target = message_id
        logger.info("[{}]: received ACCEPT from sender={}".format(self.context.agent_name, sender))

        logger.info("[{}]: sending MATCH_ACCEPT_W_ADDRESS to sender={}".format(self.context.agent_name, sender))
        match_accept_msg = FIPAMessage(message_id=new_message_id,
                                       dialogue_id=dialogue_id,
                                       target=new_target,
                                       performative=FIPAMessage.Performative.MATCH_ACCEPT_W_ADDRESS,
                                       address=self.context.agent_addresses['fetchai'])
        dialogue.outgoing_extend(match_accept_msg)
        self.context.outbox.put_message(to=sender,
                                        sender=self.context.agent_public_key,
                                        protocol_id=FIPAMessage.protocol_id,
                                        message=FIPASerializer().encode(match_accept_msg))

    def _handle_inform(self, msg: FIPAMessage, sender: str, message_id: int, dialogue_id: int, dialogue: Dialogue) -> None:
        """
        Handle the Accept.

        :param msg: the message
        :param sender: the sender
        :param message_id: the message id
        :param dialogue_id: the dialogue id
        :param dialogue: the dialogue object
        :return: None
        """
        new_message_id = message_id + 1
        new_target = message_id
        logger.info("[{}]: received INFORM from sender={}".format(self.context.agent_name, sender))

        json_data = cast(dict, msg.get("json_data"))
        if "transaction_digest" in json_data.keys():
            tx_digest = json_data['transaction_digest']
            logger.info("[{}]: checking whether transaction={} has been received ...".format(self.context.agent_name,
                                                                                             tx_digest))
            proposal = cast(Description, dialogue.proposal)
            total_price = proposal.values.get("price")
            # watch ledger for transaction (this setup assumes the carpark client trusts the carpark station)
            fetchai_ledger_api = self.context.ledger_apis.get('fetchai')
            # TODO:
            fetchai_ledger_api.is_tx_settled(tx_digest, total_price)  # type: ignore
            if self.context.is_tx_settled(tx_digest, total_price):
                token_balance = self.context.get_balance()
                logger.info("[{}]: transaction={} settled, new balance={}. Sending data ...".format(self.context.agent_name,
                                                                                                    tx_digest,
                                                                                                    token_balance))
                inform_msg = FIPAMessage(message_id=new_message_id,
                                         dialogue_id=dialogue_id,
                                         target=new_target,
                                         performative=FIPAMessage.Performative.INFORM,
                                         json_data=dialogue.carpark_data)
                dialogue.outgoing_extend(inform_msg)
                self.context.outbox.put_message(to=sender,
                                                sender=self.context.agent_public_key,
                                                protocol_id=FIPAMessage.protocol_id,
                                                message=FIPASerializer().encode(inform_msg))
                dialogues = cast(Dialogues, self.context.dialogues)
                dialogues.dialogue_stats.add_dialogue_endstate(Dialogue.EndState.SUCCESSFUL)
            else:
                logger.info("[{}]: transaction={} not settled, aborting".format(self.context.agent_name,
                                                                                tx_digest))
        else:
            logger.info("[{}]: did not receive transaction digest from sender={}.".format(self.context.agent_name, sender))
