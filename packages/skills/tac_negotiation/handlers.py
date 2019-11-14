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
from typing import List, Optional, cast, TYPE_CHECKING

from aea.configurations.base import ProtocolId
from aea.mail.base import Envelope
from aea.skills.base import Handler
from aea.protocols.base import Message
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer
from aea.protocols.fipa.message import FIPAMessage
from aea.protocols.fipa.serialization import FIPASerializer
from aea.protocols.oef.message import OEFMessage
from aea.protocols.oef.models import Query, Description
from aea.decision_maker.messages.transaction import TransactionMessage

if TYPE_CHECKING:
    from packages.skills.tac_negotiation.dialogues import Dialogue, Dialogues
    from packages.skills.tac_negotiation.helpers import generate_transaction_id
    from packages.skills.tac_negotiation.search import Search
    from packages.skills.tac_negotiation.strategy import Strategy
    from packages.skills.tac_negotiation.transactions import Transactions
else:
    from tac_negotiation_skill.dialogues import Dialogue, Dialogues
    from tac_negotiation_skill.helpers import generate_transaction_id
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

    def handle(self, message: Message, sender: str) -> None:
        """
        Dispatch message to relevant handler and respond.

        :param message: the message
        :param sender: the sender
        :return: None
        """
        fipa_msg = cast(FIPAMessage, message)
        fipa_msg_performative = fipa_msg.get("performative")

        logger.debug("[{}]: Identifying dialogue of FIPAMessage={}".format(self.context.agent_name, fipa_msg))
        dialogues = cast(Dialogues, self.context.dialogues)
        if dialogues.is_belonging_to_registered_dialogue(fipa_msg, sender, self.context.agent_public_key):
            dialogue = dialogues.get_dialogue(fipa_msg, sender, self.context.agent_public_key)
            dialogue.incoming_extend(fipa_msg)
        elif dialogues.is_permitted_for_new_dialogue(fipa_msg, sender):
            dialogue = dialogues.create_opponent_initiated(fipa_msg, sender)
            dialogue.incoming_extend(fipa_msg)
        else:
            logger.debug("[{}]: Unidentified dialogue.".format(self.context.agent_name))
            default_msg = DefaultMessage(type=DefaultMessage.Type.BYTES, content=b'This message belongs to an unidentified dialogue.')
            msg_bytes = DefaultSerializer().encode(default_msg)
            self.context.outbox.put_message(to=sender, sender=self.context.agent_public_key, protocol_id=DefaultMessage.protocol_id, message=msg_bytes)
            return

        logger.debug("[{}]: Handling FIPAMessage of performative={}".format(self.context.agent_name, fipa_msg_performative))
        fipa_msg = cast(FIPAMessage, fipa_msg)
        if fipa_msg_performative == FIPAMessage.Performative.CFP:
            self._on_cfp(fipa_msg, dialogue)
        elif fipa_msg_performative == FIPAMessage.Performative.PROPOSE:
            self._on_propose(fipa_msg, dialogue)
        elif fipa_msg_performative == FIPAMessage.Performative.DECLINE:
            self._on_decline(fipa_msg, dialogue)
        elif fipa_msg_performative == FIPAMessage.Performative.ACCEPT:
            self._on_accept(fipa_msg, dialogue)
        elif fipa_msg_performative == FIPAMessage.Performative.MATCH_ACCEPT:
            self._on_match_accept(fipa_msg, dialogue)
        # elif fipa_msg_performative == FIPAMessage.Performative.INFORM:
        #     self._on_inform(fipa_msg, dialogue)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        dialogues = cast(Dialogues, self.context.dialogues)
        dialogues.reset()

    def _on_cfp(self, cfp: FIPAMessage, dialogue: Dialogue) -> None:
        """
        Handle a CFP.

        :param cfp: the fipa message containing the CFP
        :param dialogue: the dialogue

        :return: None
        """
        strategy = cast(Strategy, self.context.strategy)
        transactions = cast(Transactions, self.context.transactions)
        ownership_state_after_locks = transactions.ownership_state_after_locks(self.context.ownership_state, is_seller=dialogue.is_seller)
        own_service_description = strategy.get_own_service_description(ownership_state_after_locks, is_supply=dialogue.is_seller)
        new_msg_id = cast(int, cfp.get("message_id")) + 1
        cfp_query = cfp.get("query")
        cfp_query = cast(Query, cfp_query)
        decline = False
        if not cfp_query.check(own_service_description):
            decline = True
            logger.debug("[{}]: Current holdings do not satisfy CFP query.".format(self.context.agent_name))
        else:
            proposal_description = strategy.get_proposal_for_query(cfp_query, self.context.preferences, ownership_state_after_locks, is_seller=dialogue.is_seller, tx_fee=1)
            if proposal_description is None:
                decline = True
                logger.debug("[{}]: Current strategy does not generate proposal that satisfies CFP query.".format(self.context.agent_name))

        if decline:
            logger.debug("[{}]: sending to {} a Decline{}".format(self.context.agent_name, dialogue.dialogue_label.dialogue_opponent_pbk,
                                                                  pprint.pformat({
                                                                      "msg_id": new_msg_id,
                                                                      "dialogue_id": cfp.get("dialogue_id"),
                                                                      "origin": dialogue.dialogue_label.dialogue_opponent_pbk,
                                                                      "target": cfp.get("target")
                                                                  })))
            msg = FIPAMessage(message_id=new_msg_id, dialogue_id=cfp.get("dialogue_id"), performative=FIPAMessage.Performative.DECLINE, target=cfp.get("message_id"))
            dialogue.outgoing_extend(msg)
            msg_bytes = FIPASerializer().encode(msg)
            result = Envelope(to=dialogue.dialogue_label.dialogue_opponent_pbk, sender=self.context.agent_public_key, protocol_id=FIPAMessage.protocol_id, message=msg_bytes)
            dialogues = cast(Dialogues, self.context.dialogues)
            dialogues.dialogue_stats.add_dialogue_endstate(Dialogue.EndState.DECLINED_CFP, dialogue.is_self_initiated)
        else:
            assert proposal_description is not None
            transaction_id = generate_transaction_id(self.context.agent_public_key, dialogue.dialogue_label.dialogue_opponent_pbk, dialogue.dialogue_label, dialogue.is_seller)
            transaction_msg = TransactionMessage(performative=TransactionMessage.Performative.PROPOSE,
                                                 skill_id="tac_negotiation_skill",
                                                 transaction_id=transaction_id,
                                                 sender=self.context.agent_public_key,
                                                 counterparty=dialogue.dialogue_label.dialogue_opponent_pbk,
                                                 currency_pbk='FET',
                                                 amount=proposal_description.values['amount'],
                                                 is_sender_buyer=not dialogue.is_seller,
                                                 sender_tx_fee=1,
                                                 counterparty_tx_fee=1,
                                                 quantities_by_good_pbk=proposal_description.values['description'])
            transactions = cast(Transactions, self.context.transactions)
            transactions.add_pending_proposal(dialogue.dialogue_label, new_msg_id, transaction_msg)
            logger.debug("[{}]: sending to {} a Propose{}".format(self.context.agent_name, dialogue.dialogue_label.dialogue_opponent_pbk,
                                                                  pprint.pformat({
                                                                      "msg_id": new_msg_id,
                                                                      "dialogue_id": cfp.get("dialogue_id"),
                                                                      "origin": dialogue.dialogue_label.dialogue_opponent_pbk,
                                                                      "target": cfp.get("message_id"),
                                                                      "propose": proposal_description.values
                                                                  })))
            msg = FIPAMessage(performative=FIPAMessage.Performative.PROPOSE, message_id=new_msg_id, dialogue_id=cfp.get("dialogue_id"), target=cfp.get("message_id"), proposal=[proposal_description])
            dialogue.outgoing_extend(msg)
            msg_bytes = FIPASerializer().encode(msg)
            result = Envelope(to=dialogue.dialogue_label.dialogue_opponent_pbk, sender=self.context.agent_public_key, protocol_id=FIPAMessage.protocol_id, message=msg_bytes)
        self.context.outbox.put(result)

    def _on_propose(self, propose: FIPAMessage, dialogue: Dialogue) -> None:
        """
        Handle a Propose.

        :param propose: the message containing the Propose
        :param dialogue: the dialogue
        :return: None
        """
        logger.debug("[{}]: on propose as {}.".format(self.context.agent_name, dialogue.role))
        proposals = cast(List[Description], propose.get("proposal"))
        for num, proposal_description in enumerate(proposals):
            if num > 0: continue  # TODO: allow for dialogue branching with multiple proposals
            transaction_id = generate_transaction_id(self.context.agent_public_key, dialogue.dialogue_label.dialogue_opponent_pbk, dialogue.dialogue_label, dialogue.is_seller)
            transaction_msg = TransactionMessage(performative=TransactionMessage.Performative.PROPOSE,
                                                 skill_id="tac_negotiation_skill",
                                                 transaction_id=transaction_id,
                                                 sender=self.context.agent_public_key,
                                                 counterparty=dialogue.dialogue_label.dialogue_opponent_pbk,
                                                 currency_pbk='FET',
                                                 amount=proposal_description.values['amount'],
                                                 is_sender_buyer=not dialogue.is_seller,
                                                 sender_tx_fee=1,
                                                 counterparty_tx_fee=1,
                                                 quantities_by_good_pbk=proposal_description.values['description'])
            new_msg_id = cast(int, propose.get("message_id")) + 1
            strategy = cast(Strategy, self.context.strategy)
            transactions = cast(Transactions, self.context.transactions)
            ownership_state_after_locks = transactions.ownership_state_after_locks(self.context.ownership_state, is_seller=dialogue.is_seller)
            if strategy.is_profitable_transaction(self.context.preferences, ownership_state_after_locks, transaction_msg):
                logger.debug("[{}]: Accepting propose (as {}).".format(self.context.agent_name, dialogue.role))
                transactions.add_locked_tx(transaction_msg, as_seller=dialogue.is_seller)
                transactions.add_pending_initial_acceptance(dialogue.dialogue_label, new_msg_id, transaction_msg)
                msg = FIPAMessage(message_id=new_msg_id, dialogue_id=propose.get("dialogue_id"), target=propose.get("message_id"), performative=FIPAMessage.Performative.ACCEPT)
                dialogue.outgoing_extend(msg)
                msg_bytes = FIPASerializer().encode(msg)
                result = Envelope(to=dialogue.dialogue_label.dialogue_opponent_pbk, sender=self.context.agent_public_key, protocol_id=FIPAMessage.protocol_id, message=msg_bytes)
            else:
                logger.debug("[{}]: Declining propose (as {})".format(self.context.agent_name, dialogue.role))
                msg = FIPAMessage(message_id=new_msg_id, dialogue_id=propose.get("dialogue_id"), target=propose.get("message_id"), performative=FIPAMessage.Performative.DECLINE)
                dialogue.outgoing_extend(msg)
                msg_bytes = FIPASerializer().encode(msg)
                result = Envelope(to=dialogue.dialogue_label.dialogue_opponent_pbk, sender=self.context.agent_public_key, protocol_id=FIPAMessage.protocol_id, message=msg_bytes)
                dialogues = cast(Dialogues, self.context.dialogues)
                dialogues.dialogue_stats.add_dialogue_endstate(Dialogue.EndState.DECLINED_PROPOSE, dialogue.is_self_initiated)
        self.context.outbox.put(result)

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
        transactions = cast(Transactions, self.context.transactions)
        assert dialogue.dialogue_label in transactions.pending_proposals \
            and accept.get("target") in transactions.pending_proposals[dialogue.dialogue_label]
        logger.debug("[{}]: on_accept: msg_id={}, dialogue_id={}, origin={}, target={}"
                     .format(self.context.agent_name, accept.get("message_id"), accept.get("dialogue_id"), dialogue.dialogue_label.dialogue_opponent_pbk, accept.get("target")))
        new_msg_id = cast(int, accept.get("message_id")) + 1
        transaction_msg = transactions.pop_pending_proposal(dialogue.dialogue_label, cast(int, accept.get("target")))
        strategy = cast(Strategy, self.context.strategy)
        ownership_state_after_locks = transactions.ownership_state_after_locks(self.context.ownership_state, is_seller=dialogue.is_seller)
        if strategy.is_profitable_transaction(self.context.preferences, ownership_state_after_locks, transaction_msg):
            logger.debug("[{}]: Locking the current state (as {}).".format(self.context.agent_name, dialogue.role))
            transactions.add_locked_tx(transaction_msg, as_seller=dialogue.is_seller)
            self.context.decision_maker_message_queue.put(transaction_msg)
        else:
            logger.debug("[{}]: Decline the accept (as {}).".format(self.context.agent_name, dialogue.role))
            msg = FIPAMessage(message_id=new_msg_id, dialogue_id=accept.get("dialogue_id"), target=accept.get("message_id"), performative=FIPAMessage.Performative.DECLINE)
            dialogue.outgoing_extend(msg)
            msg_bytes = FIPASerializer().encode(msg)
            result = Envelope(to=dialogue.dialogue_label.dialogue_opponent_pbk, sender=self.context.agent_public_key, protocol_id=FIPAMessage.protocol_id, message=msg_bytes)
            dialogues = cast(Dialogues, self.context.dialogues)
            dialogues.dialogue_stats.add_dialogue_endstate(Dialogue.EndState.DECLINED_ACCEPT, dialogue.is_self_initiated)
            self.context.outbox.put(result)

    def _on_match_accept(self, match_accept: FIPAMessage, dialogue: Dialogue) -> None:
        """
        Handle a matching Accept.

        :param match_accept: the MatchAccept message
        :param dialogue: the dialogue
        :return: None
        """
        transactions = cast(Transactions, self.context.transactions)
        assert dialogue.dialogue_label in transactions.pending_initial_acceptances \
            and match_accept.get("target") in transactions.pending_initial_acceptances[dialogue.dialogue_label]
        logger.debug("[{}]: on_match_accept: msg_id={}, dialogue_id={}, origin={}, target={}"
                     .format(self.context.agent_name, match_accept.get("message_id"), match_accept.get("dialogue_id"), dialogue.dialogue_label.dialogue_opponent_pbk, match_accept.get("target")))
        transaction_msg = transactions.pop_pending_initial_acceptance(dialogue.dialogue_label, cast(int, match_accept.get("target")))
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

    def handle(self, message: Message, sender: str) -> None:
        """
        Dispatch message to relevant handler and respond.

        :param message: the message
        :param sender: the sender
        :return: None
        """
        # msg = FIPAMessage(message_id=new_msg_id, dialogue_id=accept.get("dialogue_id"), target=accept.get("message_id"), performative=FIPAMessage.Performative.MATCH_ACCEPT)
        # dialogue.outgoing_extend(msg)
        # msg_bytes = FIPASerializer().encode(msg)
        # result = Envelope(to=dialogue.dialogue_label.dialogue_opponent_pbk, sender=self.context.agent_public_key, protocol_id=FIPAMessage.protocol_id, message=msg_bytes)

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
            search_id = oef_msg.get("id")
            search = cast(Search, self.context.search)
            if search_id in search.ids_for_sellers:
                self._handle_search(agents, is_searching_for_sellers=True)
            elif search_id in search.ids_for_buyers:
                self._handle_search(agents, is_searching_for_sellers=False)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass

    def _handle_search(self, agents: List[str], is_searching_for_sellers: bool) -> None:
        """
        Handle the search response.

        :param agents: the agents returned by the search
        :param is_searching_for_sellers: whether the agent is searching for sellers
        :return: None
        """
        searched_for = 'sellers' if is_searching_for_sellers else 'buyers'
        if len(agents) > 0:
            logger.info("[{}]: found potential {} agents={}.".format(self.context.agent_name, searched_for, list(map(lambda x: x[-5:], agents))))
            strategy = cast(Strategy, self.context.strategy)
            dialogues = cast(Dialogues, self.context.dialogues)
            transactions = cast(Transactions, self.context.transactions)
            ownership_state_after_locks = transactions.ownership_state_after_locks(self.context.ownership_state, is_seller=not is_searching_for_sellers)
            query = strategy.get_own_services_query(ownership_state_after_locks, is_searching_for_sellers)
            for opponent_pbk in agents:
                dialogue = dialogues.create_self_initiated(opponent_pbk, self.context.agent_public_key, not is_searching_for_sellers)
                logger.info("[{}]: sending CFP to agent={}".format(self.context.agent_name, opponent_pbk[-5:]))
                cfp_msg = FIPAMessage(message_id=FIPAMessage.STARTING_MESSAGE_ID,
                                      dialogue_id=dialogue.dialogue_label.dialogue_id,
                                      performative=FIPAMessage.Performative.CFP,
                                      target=FIPAMessage.STARTING_TARGET,
                                      query=query)
                dialogue.outgoing_extend(cfp_msg)
                self.context.outbox.put_message(to=opponent_pbk,
                                                sender=self.context.agent_public_key,
                                                protocol_id=FIPAMessage.protocol_id,
                                                message=FIPASerializer().encode(cfp_msg))
        else:
            logger.info("[{}]: found no {} agents, continue searching.".format(self.context.agent_name, searched_for))
