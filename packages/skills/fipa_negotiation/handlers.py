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
from typing import Optional

from aea.configurations.base import ProtocolId
from aea.mail.base import Envelope
from aea.skills.base import Handler
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer
from aea.protocols.fipa.message import FIPAMessage
from aea.protocols.fipa.serialization import FIPASerializer

from fipa_negotiation_skill.dialogues import Dialogue

logger = logging.getLogger(__name__)


class FIPANegotiationHandler(Handler):
    """This class implements the fipa negotiation handler."""

    SUPPORTED_PROTOCOL = FIPAMessage.protocol_id  # type: Optional[ProtocolId]

    def handle_envelope(self, envelope: Envelope) -> None:
        """
        Dispatch envelope to relevant handler and respond.

        :param envelope: the envelope
        :return: None
        """
        fipa_msg = FIPASerializer().decode(envelope.message)
        fipa_msg_performative = fipa_msg.get("performative")  # FIPAMessage.Performative(fipa_msg.get("performative"))

        logger.debug("[{}]: Identifying dialogue of FIPAMessage={}".format(self.context.agent_name, fipa_msg))
        if self.context.dialogues.is_belonging_to_registered_dialogue(fipa_msg, envelope.sender, self.context.agent_public_key):
            dialogue = self.context.dialogues.get_dialogue(fipa_msg, envelope.sender, self.context.agent_public_key)
            dialogue.incoming_extend([fipa_msg])
        elif self.context.dialogues.is_permitted_for_new_dialogue(fipa_msg, envelope.sender):
            dialogue = self.context.dialogues.create_opponent_initiated(fipa_msg, envelope.sender)
        else:
            logger.debug("[{}]: Unidentified dialogue.".format(self.context.agent_name))
            default_msg = DefaultMessage(type=DefaultMessage.Type.BYTES, content=b'This message belongs to an unidentified dialogue.')
            msg_bytes = DefaultSerializer().encode(default_msg)
            self.context.outbox.put_message(to=envelope.sender, sender=self.context.agent_public_key, protocol_id=DefaultMessage.protocol_id, message=msg_bytes)
            return

        logger.debug("[{}]: Handling FIPAMessage of performative={}".format(self.context.agent_name, fipa_msg_performative))
        if fipa_msg_performative == FIPAMessage.Performative.CFP:
            response = self._on_cfp(fipa_msg, dialogue)
        elif fipa_msg_performative == FIPAMessage.Performative.PROPOSE:
            response = self._on_propose(fipa_msg, dialogue)
        elif fipa_msg_performative == FIPAMessage.Performative.DECLINE:
            response = self._on_decline(fipa_msg, dialogue)
        elif fipa_msg_performative == FIPAMessage.Performative.ACCEPT:
            response = self._on_accept(fipa_msg, dialogue)
        elif fipa_msg_performative == FIPAMessage.Performative.MATCH_ACCEPT:
            response = self._on_match_accept(fipa_msg, dialogue)
        self.context.outbox.put(response)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        self.context.dialogues.reset()

    def _on_cfp(self, cfp: FIPAMessage, dialogue: Dialogue) -> Envelope:
        """
        Handle a CFP.

        :param cfp: the fipa message containing the CFP
        :param dialogue: the dialogue

        :return: a Propose or a Decline
        """
        own_service_description = self.context.strategy.get_own_service_description(is_supply=dialogue.is_seller)
        new_msg_id = cfp.get("id") + 1
        decline = False
        cfp_services = json.loads(cfp.get("query").decode('utf-8'))
        if not self.context.strategy.is_compatible(cfp_services, goods_description): #operate on object instead?
            decline = True
            logger.debug("[{}]: Current holdings do not satisfy CFP query.".format(self.context.agent_name))
        else:
            proposal = self.context.strategy.generate_proposal(cfp_services, dialogue.is_seller)
            if proposal is None:
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
            msg = FIPAMessage(message_id=new_msg_id, dialogue_id=cfp.get("dialogue_id"), performative=FIPAMessage.Performative.DECLINE, target=cfp.get("id"))
            dialogue.outgoing_extend([msg])
            msg_bytes = FIPASerializer().encode(msg)
            result = Envelope(to=dialogue.dialogue_label.dialogue_opponent_pbk, sender=self.context.agent_public_key, protocol_id=FIPAMessage.protocol_id, message=msg_bytes)
            self.context.dialogues.dialogue_stats.add_dialogue_endstate(Dialogue.EndState.DECLINED_CFP, dialogue.is_self_initiated)
        else:
            proposal = cast(Description, proposal)
            transaction_id = generate_transaction_id(self.crypto.public_key, dialogue.dialogue_label.dialogue_opponent_pbk, dialogue.dialogue_label, dialogue.is_seller)
            transaction = TransactionMessage(transaction_id=transaction_id,
                                             sender=self.context.agent_public_key,
                                             counterparty=dialogue.dialogue_label.dialogue_opponent_pbk,
                                             is_sender_buyer=not dialogue.is_seller,
                                             amount=proposal.amount,
                                             quantities_by_good_pbkproposal=proposal)
            self.context.transactions.add_pending_proposal(dialogue.dialogue_label, new_msg_id, transaction)
            logger.debug("[{}]: sending to {} a Propose{}".format(self.context.agent_name, dialogue.dialogue_label.dialogue_opponent_pbk,
                                                                  pprint.pformat({
                                                                      "msg_id": new_msg_id,
                                                                      "dialogue_id": cfp.get("dialogue_id"),
                                                                      "origin": dialogue.dialogue_label.dialogue_opponent_pbk,
                                                                      "target": cfp.get("id"),
                                                                      "propose": proposal.values
                                                                  })))
            msg = FIPAMessage(performative=FIPAMessage.Performative.PROPOSE, message_id=new_msg_id, dialogue_id=cfp.get("dialogue_id"), target=cfp.get("id"), proposal=[proposal])
            dialogue.outgoing_extend([msg])
            msg_bytes = FIPASerializer().encode(msg)
            result = Envelope(to=dialogue.dialogue_label.dialogue_opponent_pbk, sender=self.context.agent_public_key, protocol_id=FIPAMessage.protocol_id, message=msg_bytes)
        return result

    def _on_propose(self, propose: FIPAMessage, dialogue: Dialogue) -> Envelope:
        """
        Handle a Propose.

        :param propose: the message containing the Propose
        :param dialogue: the dialogue
        :return: an Accept or a Decline in an envelope
        """
        logger.debug("[{}]: on propose as {}.".format(self.agent_name, dialogue.role))
        proposal = propose.get("proposal")[0]
        transaction_id = generate_transaction_id(self.context.agent_public_key, dialogue.dialogue_label.dialogue_opponent_pbk, dialogue.dialogue_label, dialogue.is_seller)
        transaction = Transaction.from_proposal(proposal=proposal,
                                                transaction_id=transaction_id,
                                                is_sender_buyer=not dialogue.is_seller,
                                                counterparty=dialogue.dialogue_label.dialogue_opponent_pbk,
                                                sender=self.context.agent_public_key)
        new_msg_id = propose.get("id") + 1
        is_profitable_transaction, propose_log_msg = self.context.game_instance.is_profitable_transaction(transaction, dialogue)
        logger.debug(propose_log_msg)
        if is_profitable_transaction:
            logger.debug("[{}]: Accepting propose (as {}).".format(self.context.agent_name, dialogue.role))
            self.context.game_instance.transaction_manager.add_locked_tx(transaction, as_seller=dialogue.is_seller)
            self.context.game_instance.transaction_manager.add_pending_initial_acceptance(dialogue.dialogue_label, new_msg_id, transaction)
            msg = FIPAMessage(message_id=new_msg_id, dialogue_id=propose.get("dialogue_id"), target=propose.get("id"), performative=FIPAMessage.Performative.ACCEPT)
            dialogue.outgoing_extend([msg])
            msg_bytes = FIPASerializer().encode(msg)
            result = Envelope(to=dialogue.dialogue_label.dialogue_opponent_pbk, sender=self.context.agent_public_key, protocol_id=FIPAMessage.protocol_id, message=msg_bytes)
        else:
            logger.debug("[{}]: Declining propose (as {})".format(self.context.agent_name, dialogue.role))
            msg = FIPAMessage(message_id=new_msg_id, dialogue_id=propose.get("dialogue_id"), target=propose.get("id"), performative=FIPAMessage.Performative.DECLINE)
            dialogue.outgoing_extend([msg])
            msg_bytes = FIPASerializer().encode(msg)
            result = Envelope(to=dialogue.dialogue_label.dialogue_opponent_pbk, sender=self.context.agent_public_key, protocol_id=FIPAMessage.protocol_id, message=msg_bytes)
            self.context.game_instance.stats_manager.add_dialogue_endstate(Dialogue.EndState.DECLINED_PROPOSE, dialogue.is_self_initiated)
        return result

    def _on_decline(self, decline: FIPAMessage, dialogue: Dialogue) -> None:
        """
        Handle a Decline.

        :param decline: the Decline message
        :param dialogue: the dialogue
        :return: None
        """
        logger.debug("[{}]: on_decline: msg_id={}, dialogue_id={}, origin={}, target={}"
                     .format(self.agent_name, decline.get("id"), decline.get("dialogue_id"), dialogue.dialogue_label.dialogue_opponent_pbk, decline.get("target")))
        target = decline.get("target")
        if target == 1:
            self.context.dialogues.dialogue_stats.add_dialogue_endstate(Dialogue.EndState.DECLINED_CFP, dialogue.is_self_initiated)
        elif target == 2:
            self.context.dialogues.dialogue_stats.add_dialogue_endstate(Dialogue.EndState.DECLINED_PROPOSE, dialogue.is_self_initiated)
            transaction = self.context.game_instance.transaction_manager.pop_pending_proposal(dialogue.dialogue_label, target)
            if self.context.game_instance.strategy.is_world_modeling:
                self.context.game_instance.world_state.update_on_declined_propose(transaction)
        elif target == 3:
            self.context.dialogues.dialogue_stats.add_dialogue_endstate(Dialogue.EndState.DECLINED_ACCEPT, dialogue.is_self_initiated)
            transaction = self.context.transaction_manager.pop_pending_initial_acceptance(dialogue.dialogue_label, target)
            self.context.game_instance.transaction_manager.pop_locked_tx(transaction.transaction_id)
        return None

    def _on_accept(self, accept: FIPAMessage, dialogue: Dialogue) -> Envelope:
        """
        Handle an Accept.

        :param accept: the Accept message
        :param dialogue: the dialogue
        :return: a Decline, or an Accept in an envelope
        """
        # assert accept.get("performative") == FIPAMessage.Performative.ACCEPT \
        #     and dialogue.dialogue_label in self.game_instance.transaction_manager.pending_proposals \
        #     and accept.get("target") in self.game_instance.transaction_manager.pending_proposals[dialogue.dialogue_label]
        logger.debug("[{}]: on_accept: msg_id={}, dialogue_id={}, origin={}, target={}"
                     .format(self.context.agent_name, accept.get("id"), accept.get("dialogue_id"), dialogue.dialogue_label.dialogue_opponent_pbk, accept.get("target")))
        new_msg_id = accept.get("id") + 1
        transaction = self.context.game_instance.transaction_manager.pop_pending_proposal(dialogue.dialogue_label, accept.get("target"))
        is_profitable_transaction, accept_log_msg = self.context.game_instance.is_profitable_transaction(transaction, dialogue)
        logger.debug(accept_log_msg)
        if is_profitable_transaction:
            if self.context.game_instance.strategy.is_world_modeling:
                self.context.game_instance.world_state.update_on_initial_accept(transaction)
            logger.debug("[{}]: Locking the current state (as {}).".format(self.context.agent_name, dialogue.role))
            self.context.game_instance.transaction_manager.add_locked_tx(transaction, as_seller=dialogue.is_seller)
            self.context.transaction_queue.put(transaction)
            msg = FIPAMessage(message_id=new_msg_id, dialogue_id=accept.get("dialogue_id"), target=accept.get("id"), performative=FIPAMessage.Performative.MATCH_ACCEPT)
            dialogue.outgoing_extend([msg])
            msg_bytes = FIPASerializer().encode(msg)
            result = Envelope(to=dialogue.dialogue_label.dialogue_opponent_pbk, sender=self.context.agent_public_key, protocol_id=FIPAMessage.protocol_id, message=msg_bytes)
        else:
            logger.debug("[{}]: Decline the accept (as {}).".format(self.agent_name, dialogue.role))

            msg = FIPAMessage(message_id=new_msg_id, dialogue_id=accept.get("dialogue_id"), target=accept.get("id"), performative=FIPAMessage.Performative.DECLINE)
            dialogue.outgoing_extend([msg])
            msg_bytes = FIPASerializer().encode(msg)
            result = Envelope(to=dialogue.dialogue_label.dialogue_opponent_pbk, sender=self.context.agent_public_key, protocol_id=FIPAMessage.protocol_id, message=msg_bytes)
            self.context.game_instance.stats_manager.add_dialogue_endstate(Dialogue.EndState.DECLINED_ACCEPT, dialogue.is_self_initiated)
        return result

    def _on_match_accept(self, match_accept: FIPAMessage, dialogue: Dialogue) -> None:
        """
        Handle a matching Accept.

        :param match_accept: the MatchAccept message
        :param dialogue: the dialogue
        :return: None
        """
        # assert match_accept.get("performative") == FIPAMessage.Performative.MATCH_ACCEPT \
        #     and dialogue.dialogue_label in self.game_instance.transaction_manager.pending_initial_acceptances \
        #     and match_accept.get("target") in self.game_instance.transaction_manager.pending_initial_acceptances[dialogue.dialogue_label]
        logger.debug("[{}]: on_match_accept: msg_id={}, dialogue_id={}, origin={}, target={}"
                     .format(self.context.agent_name, match_accept.get("id"), match_accept.get("dialogue_id"), dialogue.dialogue_label.dialogue_opponent_pbk, match_accept.get("target")))
        transaction = self.context.game_instance.transaction_manager.pop_pending_initial_acceptance(dialogue.dialogue_label, match_accept.get("target"))
        self.context.transaction_queue.put(transaction)
        return None
