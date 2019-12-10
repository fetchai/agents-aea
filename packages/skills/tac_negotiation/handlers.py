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
import pprint
import sys
from typing import Any, Dict, List, Optional, cast, TYPE_CHECKING, Tuple

from aea.configurations.base import ProtocolId
from aea.helpers.dialogue.base import DialogueLabel
from aea.skills.base import Handler
from aea.protocols.base import Message
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer
from aea.protocols.fipa.dialogues import FIPADialogue as Dialogue
from aea.protocols.fipa.message import FIPAMessage
from aea.protocols.fipa.serialization import FIPASerializer
from aea.protocols.oef.message import OEFMessage
from aea.protocols.oef.models import Query, Description
from aea.decision_maker.messages.transaction import TransactionMessage

if TYPE_CHECKING or "pytest" in sys.modules:
    from packages.skills.tac_negotiation.dialogues import Dialogues
    from packages.skills.tac_negotiation.helpers import generate_transaction_message, DEMAND_DATAMODEL_NAME
    from packages.skills.tac_negotiation.search import Search
    from packages.skills.tac_negotiation.strategy import Strategy
    from packages.skills.tac_negotiation.transactions import Transactions
else:
    from tac_negotiation_skill.dialogues import Dialogues
    from tac_negotiation_skill.helpers import generate_transaction_message, DEMAND_DATAMODEL_NAME
    from tac_negotiation_skill.search import Search
    from tac_negotiation_skill.strategy import Strategy
    from tac_negotiation_skill.transactions import Transactions

logger = logging.getLogger("aea.tac_negotiation_skill")


class FIPANegotiationHandler(Handler):
    """This class implements the fipa negotiation handler."""

    SUPPORTED_PROTOCOL = FIPAMessage.protocol_id  # type: Optional[ProtocolId]

    def setup(self) -> None:
        """
        Implement the setup.

        :return: None
        """
        pass

    def handle(self, message: Message) -> None:
        """
        Dispatch message to relevant handler and respond.

        :param message: the message
        :return: None
        """
        fipa_msg = cast(FIPAMessage, message)

        logger.debug("[{}]: Identifying dialogue of FIPAMessage={}".format(self.context.agent_name, fipa_msg))
        dialogues = cast(Dialogues, self.context.dialogues)
        if dialogues.is_belonging_to_registered_dialogue(fipa_msg, self.context.agent_public_key):
            dialogue = cast(Dialogue, dialogues.get_dialogue(fipa_msg, self.context.agent_public_key))
            dialogue.incoming_extend(fipa_msg)
        elif dialogues.is_permitted_for_new_dialogue(fipa_msg):
            query = cast(Query, fipa_msg.get("query"))
            assert query.model is not None, "Query has no data model."
            is_seller = query.model.name == DEMAND_DATAMODEL_NAME
            dialogue = cast(Dialogue, dialogues.create_opponent_initiated(message.counterparty, cast(Tuple[str, str], fipa_msg.get('dialogue_reference')), is_seller))
            dialogue.incoming_extend(fipa_msg)
        else:
            logger.debug("[{}]: Unidentified dialogue.".format(self.context.agent_name))
            default_msg = DefaultMessage(type=DefaultMessage.Type.BYTES,
                                         content=b'This message belongs to an unidentified dialogue.')
            self.context.outbox.put_message(to=fipa_msg.counterparty,
                                            sender=self.context.agent_public_key,
                                            protocol_id=DefaultMessage.protocol_id,
                                            message=DefaultSerializer().encode(default_msg))
            return

        fipa_msg_performative = fipa_msg.get("performative")
        logger.debug("[{}]: Handling FIPAMessage of performative={}".format(self.context.agent_name,
                                                                            fipa_msg_performative))
        if fipa_msg_performative == FIPAMessage.Performative.CFP:
            self._on_cfp(fipa_msg, dialogue)
        elif fipa_msg_performative == FIPAMessage.Performative.PROPOSE:
            self._on_propose(fipa_msg, dialogue)
        elif fipa_msg_performative == FIPAMessage.Performative.DECLINE:
            self._on_decline(fipa_msg, dialogue)
        elif fipa_msg_performative == FIPAMessage.Performative.ACCEPT:
            self._on_accept(fipa_msg, dialogue)
        elif fipa_msg_performative == FIPAMessage.Performative.MATCH_ACCEPT_W_INFORM:
            self._on_match_accept(fipa_msg, dialogue)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass

    def _on_cfp(self, cfp: FIPAMessage, dialogue: Dialogue) -> None:
        """
        Handle a CFP.

        :param cfp: the fipa message containing the CFP
        :param dialogue: the dialogue

        :return: None
        """
        new_msg_id = cast(int, cfp.get("message_id")) + 1
        query = cast(Query, cfp.get("query"))
        strategy = cast(Strategy, self.context.strategy)
        proposal_description = strategy.get_proposal_for_query(query, dialogue.is_seller)

        if proposal_description is None:
            logger.debug("[{}]: sending to {} a Decline{}".format(self.context.agent_name, dialogue.dialogue_label.dialogue_opponent_pbk[-5:],
                                                                  pprint.pformat({
                                                                      "msg_id": new_msg_id,
                                                                      "dialogue_id": cfp.get("dialogue_id"),
                                                                      "origin": dialogue.dialogue_label.dialogue_opponent_pbk[-5:],
                                                                      "target": cfp.get("target")
                                                                  })))
            fipa_msg = FIPAMessage(performative=FIPAMessage.Performative.DECLINE,
                                   message_id=new_msg_id,
                                   dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                                   target=cfp.get("message_id"))
            dialogues = cast(Dialogues, self.context.dialogues)
            dialogues.dialogue_stats.add_dialogue_endstate(Dialogue.EndState.DECLINED_CFP, dialogue.is_self_initiated)
        else:
            transaction_msg = generate_transaction_message(proposal_description, dialogue.dialogue_label, dialogue.is_seller, self.context.agent_public_key)
            transactions = cast(Transactions, self.context.transactions)
            transactions.add_pending_proposal(dialogue.dialogue_label, new_msg_id, transaction_msg)
            logger.info("[{}]: sending to {} a Propose{}".format(self.context.agent_name, dialogue.dialogue_label.dialogue_opponent_pbk[-5:],
                                                                 pprint.pformat({
                                                                     "msg_id": new_msg_id,
                                                                     "dialogue_id": cfp.get("dialogue_id"),
                                                                     "origin": dialogue.dialogue_label.dialogue_opponent_pbk[-5:],
                                                                     "target": cfp.get("message_id"),
                                                                     "propose": proposal_description.values
                                                                 })))
            fipa_msg = FIPAMessage(performative=FIPAMessage.Performative.PROPOSE,
                                   message_id=new_msg_id,
                                   dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                                   target=cfp.get("message_id"),
                                   proposal=[proposal_description])
        dialogue.outgoing_extend(fipa_msg)
        self.context.outbox.put_message(to=dialogue.dialogue_label.dialogue_opponent_pbk,
                                        sender=self.context.agent_public_key,
                                        protocol_id=FIPAMessage.protocol_id,
                                        message=FIPASerializer().encode(fipa_msg))

    def _on_propose(self, propose: FIPAMessage, dialogue: Dialogue) -> None:
        """
        Handle a Propose.

        :param propose: the message containing the Propose
        :param dialogue: the dialogue
        :return: None
        """
        new_msg_id = cast(int, propose.get("message_id")) + 1
        strategy = cast(Strategy, self.context.strategy)
        proposals = cast(List[Description], propose.get("proposal"))
        logger.debug("[{}]: on Propose as {}.".format(self.context.agent_name, dialogue.role))

        for num, proposal_description in enumerate(proposals):
            if num > 0: continue  # TODO: allow for dialogue branching with multiple proposals
            transaction_msg = generate_transaction_message(proposal_description, dialogue.dialogue_label, dialogue.is_seller, self.context.agent_public_key)

            if strategy.is_profitable_transaction(transaction_msg, is_seller=dialogue.is_seller):
                logger.info("[{}]: Accepting propose (as {}).".format(self.context.agent_name, dialogue.role))
                transactions = cast(Transactions, self.context.transactions)
                transactions.add_locked_tx(transaction_msg, as_seller=dialogue.is_seller)
                transactions.add_pending_initial_acceptance(dialogue.dialogue_label, new_msg_id, transaction_msg)
                fipa_msg = FIPAMessage(performative=FIPAMessage.Performative.ACCEPT,
                                       message_id=new_msg_id,
                                       dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                                       target=propose.get("message_id"))
            else:
                logger.info("[{}]: Declining propose (as {})".format(self.context.agent_name, dialogue.role))
                fipa_msg = FIPAMessage(performative=FIPAMessage.Performative.DECLINE,
                                       message_id=new_msg_id,
                                       dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                                       target=propose.get("message_id"))
                dialogues = cast(Dialogues, self.context.dialogues)
                dialogues.dialogue_stats.add_dialogue_endstate(Dialogue.EndState.DECLINED_PROPOSE, dialogue.is_self_initiated)
            dialogue.outgoing_extend(fipa_msg)
            self.context.outbox.put_message(to=dialogue.dialogue_label.dialogue_opponent_pbk,
                                            sender=self.context.agent_public_key,
                                            protocol_id=FIPAMessage.protocol_id,
                                            message=FIPASerializer().encode(fipa_msg))

    def _on_decline(self, decline: FIPAMessage, dialogue: Dialogue) -> None:
        """
        Handle a Decline.

        :param decline: the Decline message
        :param dialogue: the dialogue
        :return: None
        """
        logger.debug("[{}]: on_decline: msg_id={}, dialogue_id={}, origin={}, target={}"
                     .format(self.context.agent_name, decline.get("message_id"), decline.get("dialogue_id"), dialogue.dialogue_label.dialogue_opponent_pbk, decline.get("target")))
        target = decline.get("target")
        dialogues = cast(Dialogues, self.context.dialogues)

        if target == 1:
            dialogues.dialogue_stats.add_dialogue_endstate(Dialogue.EndState.DECLINED_CFP, dialogue.is_self_initiated)
        elif target == 2:
            dialogues.dialogue_stats.add_dialogue_endstate(Dialogue.EndState.DECLINED_PROPOSE, dialogue.is_self_initiated)
            transactions = cast(Transactions, self.context.transactions)
            transaction_msg = transactions.pop_pending_proposal(dialogue.dialogue_label, target)
        elif target == 3:
            dialogues.dialogue_stats.add_dialogue_endstate(Dialogue.EndState.DECLINED_ACCEPT, dialogue.is_self_initiated)
            transactions = cast(Transactions, self.context.transactions)
            transaction_msg = transactions.pop_pending_initial_acceptance(dialogue.dialogue_label, target)
            transactions.pop_locked_tx(transaction_msg)

    def _on_accept(self, accept: FIPAMessage, dialogue: Dialogue) -> None:
        """
        Handle an Accept.

        :param accept: the Accept message
        :param dialogue: the dialogue
        :return: None
        """
        logger.debug("[{}]: on_accept: msg_id={}, dialogue_id={}, origin={}, target={}"
                     .format(self.context.agent_name, accept.get("message_id"), accept.get("dialogue_id"), dialogue.dialogue_label.dialogue_opponent_pbk, accept.get("target")))
        new_msg_id = cast(int, accept.get("message_id")) + 1
        transactions = cast(Transactions, self.context.transactions)
        transaction_msg = transactions.pop_pending_proposal(dialogue.dialogue_label, cast(int, accept.get("target")))
        strategy = cast(Strategy, self.context.strategy)

        if strategy.is_profitable_transaction(transaction_msg, is_seller=dialogue.is_seller):
            logger.info("[{}]: locking the current state (as {}).".format(self.context.agent_name, dialogue.role))
            transactions.add_locked_tx(transaction_msg, as_seller=dialogue.is_seller)
            transaction_msg.set('performative', TransactionMessage.Performative.SIGN)
            transaction_msg.set('skill_ids', ['tac_negotiation'])
            self.context.decision_maker_message_queue.put(transaction_msg)
        else:
            logger.debug("[{}]: decline the Accept (as {}).".format(self.context.agent_name, dialogue.role))
            fipa_msg = FIPAMessage(performative=FIPAMessage.Performative.DECLINE,
                                   message_id=new_msg_id,
                                   dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                                   target=accept.get("message_id"), )
            dialogue.outgoing_extend(fipa_msg)
            dialogues = cast(Dialogues, self.context.dialogues)
            dialogues.dialogue_stats.add_dialogue_endstate(Dialogue.EndState.DECLINED_ACCEPT, dialogue.is_self_initiated)
            self.context.outbox.put_message(to=dialogue.dialogue_label.dialogue_opponent_pbk,
                                            sender=self.context.agent_public_key,
                                            protocol_id=FIPAMessage.protocol_id,
                                            message=FIPASerializer().encode(fipa_msg))

    def _on_match_accept(self, match_accept: FIPAMessage, dialogue: Dialogue) -> None:
        """
        Handle a matching Accept.

        :param match_accept: the MatchAccept message
        :param dialogue: the dialogue
        :return: None
        """
        logger.debug("[{}]: on_match_accept: msg_id={}, dialogue_id={}, origin={}, target={}"
                     .format(self.context.agent_name, match_accept.get("message_id"), match_accept.get("dialogue_id"), dialogue.dialogue_label.dialogue_opponent_pbk, match_accept.get("target")))
        transactions = cast(Transactions, self.context.transactions)
        transaction_msg = transactions.pop_pending_initial_acceptance(dialogue.dialogue_label, cast(int, match_accept.get("target")))
        # update skill id to route back to tac participation skill
        logger.info("[{}]: proposing tx to decision maker.".format(self.context.agent_name))
        transaction_msg.set('performative', TransactionMessage.Performative.SIGN)
        transaction_msg.set('skill_ids', ['tac_participation'])
        self.context.decision_maker_message_queue.put(transaction_msg)


class TransactionHandler(Handler):
    """This class implements the transaction handler."""

    SUPPORTED_PROTOCOL = TransactionMessage.protocol_id  # type: Optional[ProtocolId]

    def setup(self) -> None:
        """
        Implement the setup.

        :return: None
        """
        pass

    def handle(self, message: Message) -> None:
        """
        Dispatch message to relevant handler and respond.

        :param message: the message
        :param sender: the sender
        :return: None
        """
        tx_message = cast(TransactionMessage, message)
        if TransactionMessage.Performative(tx_message.get("performative")) == TransactionMessage.Performative.ACCEPT:
            logger.info("[{}]: transaction confirmed by decision maker".format(self.context.agent_name))
            info = cast(Dict[str, Any], tx_message.get("info"))
            dialogue_label = DialogueLabel.from_json(cast(Dict[str, str], info.get("dialogue_label")))
            dialogues = cast(Dialogues, self.context.dialogues)
            dialogue = dialogues.dialogues[dialogue_label]
            tac_message = dialogue.last_incoming_message
            if tac_message is not None and tac_message.get("performative") == FIPAMessage.Performative.ACCEPT:
                logger.info("[{}]: sending match accept to {}.".format(self.context.agent_name, dialogue.dialogue_label.dialogue_opponent_pbk[-5:]))
                fipa_msg = FIPAMessage(performative=FIPAMessage.Performative.MATCH_ACCEPT_W_INFORM,
                                       message_id=cast(int, tac_message.get("message_id")) + 1,
                                       dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                                       target=cast(int, tac_message.get("message_id")),
                                       info={"address": tx_message.get("address"), "signature": tx_message.get("signature")})
                dialogue.outgoing_extend(fipa_msg)
                self.context.outbox.put_message(to=dialogue.dialogue_label.dialogue_opponent_pbk,
                                                sender=self.context.agent_public_key,
                                                protocol_id=FIPAMessage.protocol_id,
                                                message=FIPASerializer().encode(fipa_msg))
            else:
                logger.warning("[{}]: last message should be of performative accept.".format(self.context.agent_name))
        else:
            logger.info("[{}]: transaction was not successful.".format(self.context.agent_name))

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass


class OEFSearchHandler(Handler):
    """This class implements the oef search handler."""

    SUPPORTED_PROTOCOL = OEFMessage.protocol_id  # type: Optional[ProtocolId]

    def setup(self) -> None:
        """
        Implement the setup.

        :return: None
        """
        pass

    def handle(self, message: Message) -> None:
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
            search_id = cast(int, oef_msg.get("id"))
            search = cast(Search, self.context.search)
            if self.context.agent_public_key in agents:
                agents.remove(self.context.agent_public_key)
            if search_id in search.ids_for_sellers:
                self._handle_search(agents, search_id, is_searching_for_sellers=True)
            elif search_id in search.ids_for_buyers:
                self._handle_search(agents, search_id, is_searching_for_sellers=False)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass

    def _handle_search(self, agents: List[str], search_id: int, is_searching_for_sellers: bool) -> None:
        """
        Handle the search response.

        :param agents: the agents returned by the search
        :param is_searching_for_sellers: whether the agent is searching for sellers
        :return: None
        """
        searched_for = 'sellers' if is_searching_for_sellers else 'buyers'
        if len(agents) > 0:
            logger.info("[{}]: found potential {} agents={} on search_id={}.".format(self.context.agent_name, searched_for, list(map(lambda x: x[-5:], agents)), search_id))
            strategy = cast(Strategy, self.context.strategy)
            dialogues = cast(Dialogues, self.context.dialogues)
            query = strategy.get_own_services_query(is_searching_for_sellers)

            for opponent_pbk in agents:
                dialogue = dialogues.create_self_initiated(opponent_pbk, self.context.agent_public_key, not is_searching_for_sellers)
                logger.info("[{}]: sending CFP to agent={}".format(self.context.agent_name, opponent_pbk[-5:]))
                fipa_msg = FIPAMessage(message_id=FIPAMessage.STARTING_MESSAGE_ID,
                                       dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                                       performative=FIPAMessage.Performative.CFP,
                                       target=FIPAMessage.STARTING_TARGET,
                                       query=query)
                dialogue.outgoing_extend(fipa_msg)
                self.context.outbox.put_message(to=opponent_pbk,
                                                sender=self.context.agent_public_key,
                                                protocol_id=FIPAMessage.protocol_id,
                                                message=FIPASerializer().encode(fipa_msg))
        else:
            logger.info("[{}]: found no {} agents on search_id={}, continue searching.".format(self.context.agent_name, searched_for, search_id))
