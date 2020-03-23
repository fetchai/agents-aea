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

import pprint
from typing import Dict, List, Optional, cast

from aea.configurations.base import ProtocolId
from aea.decision_maker.messages.transaction import TransactionMessage
from aea.helpers.dialogue.base import DialogueLabel
from aea.helpers.search.models import Query
from aea.protocols.base import Message
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer
from aea.skills.base import Handler

from packages.fetchai.protocols.fipa.dialogues import FIPADialogue as Dialogue
from packages.fetchai.protocols.fipa.message import FIPAMessage
from packages.fetchai.protocols.fipa.serialization import FIPASerializer
from packages.fetchai.protocols.oef.message import OefSearchMessage
from packages.fetchai.skills.tac_negotiation.dialogues import Dialogues
from packages.fetchai.skills.tac_negotiation.helpers import SUPPLY_DATAMODEL_NAME
from packages.fetchai.skills.tac_negotiation.search import Search
from packages.fetchai.skills.tac_negotiation.strategy import Strategy
from packages.fetchai.skills.tac_negotiation.transactions import Transactions


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

        dialogue = self._try_to_recover_dialogue(fipa_msg)
        if dialogue is None:
            return

        self.context.logger.debug(
            "[{}]: Handling FIPAMessage of performative={}".format(
                self.context.agent_name, fipa_msg.performative
            )
        )
        if fipa_msg.performative == FIPAMessage.Performative.CFP:
            self._on_cfp(fipa_msg, dialogue)
        elif fipa_msg.performative == FIPAMessage.Performative.PROPOSE:
            self._on_propose(fipa_msg, dialogue)
        elif fipa_msg.performative == FIPAMessage.Performative.DECLINE:
            self._on_decline(fipa_msg, dialogue)
        elif fipa_msg.performative == FIPAMessage.Performative.ACCEPT:
            self._on_accept(fipa_msg, dialogue)
        elif fipa_msg.performative == FIPAMessage.Performative.MATCH_ACCEPT_W_INFORM:
            self._on_match_accept(fipa_msg, dialogue)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass

    def _try_to_recover_dialogue(self, fipa_msg: FIPAMessage) -> Optional[Dialogue]:
        """
        Try to recover the dialogue based on the fipa message.

        :param fipa_msg: the fipa message
        :return: the dialogue or None
        """
        self.context.logger.debug(
            "[{}]: Identifying dialogue of FIPAMessage={}".format(
                self.context.agent_name, fipa_msg
            )
        )
        dialogues = cast(Dialogues, self.context.dialogues)
        if dialogues.is_belonging_to_registered_dialogue(
            fipa_msg, self.context.agent_address
        ):
            dialogue = cast(
                Dialogue, dialogues.get_dialogue(fipa_msg, self.context.agent_address)
            )
            dialogue.incoming_extend(fipa_msg)
            return dialogue
        elif dialogues.is_permitted_for_new_dialogue(fipa_msg):
            query = cast(Query, fipa_msg.query)
            if query.model is not None:
                is_seller = (
                    query.model.name == SUPPLY_DATAMODEL_NAME
                )  # the counterparty is querying for supply
                dialogue = cast(
                    Dialogue,
                    dialogues.create_opponent_initiated(
                        fipa_msg.counterparty, fipa_msg.dialogue_reference, is_seller
                    ),
                )
                dialogue.incoming_extend(fipa_msg)
                return dialogue
            else:
                self.context.logger.warning(
                    "[{}]: Query has no data model, ignoring CFP!".format(
                        self.context.agent_name
                    )
                )
                return None
        else:
            self.context.logger.debug(
                "[{}]: Unidentified dialogue.".format(self.context.agent_name)
            )
            default_msg = DefaultMessage(
                dialogue_reference=("", ""),
                message_id=1,
                target=0,
                performative=DefaultMessage.Performative.BYTES,
                content=b"This message belongs to an unidentified dialogue.",
            )
            self.context.outbox.put_message(
                to=fipa_msg.counterparty,
                sender=self.context.agent_address,
                protocol_id=DefaultMessage.protocol_id,
                message=DefaultSerializer().encode(default_msg),
            )
            return None

    def _on_cfp(self, cfp: FIPAMessage, dialogue: Dialogue) -> None:
        """
        Handle a CFP.

        :param cfp: the fipa message containing the CFP
        :param dialogue: the dialogue

        :return: None
        """
        new_msg_id = cfp.message_id + 1
        query = cast(Query, cfp.query)
        strategy = cast(Strategy, self.context.strategy)
        proposal_description = strategy.get_proposal_for_query(
            query, dialogue.is_seller
        )

        if proposal_description is None:
            self.context.logger.debug(
                "[{}]: sending to {} a Decline{}".format(
                    self.context.agent_name,
                    dialogue.dialogue_label.dialogue_opponent_addr[-5:],
                    pprint.pformat(
                        {
                            "msg_id": new_msg_id,
                            "dialogue_reference": cfp.dialogue_reference,
                            "origin": dialogue.dialogue_label.dialogue_opponent_addr[
                                -5:
                            ],
                            "target": cfp.target,
                        }
                    ),
                )
            )
            fipa_msg = FIPAMessage(
                performative=FIPAMessage.Performative.DECLINE,
                message_id=new_msg_id,
                dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                target=cfp.message_id,
            )
            dialogues = cast(Dialogues, self.context.dialogues)
            dialogues.dialogue_stats.add_dialogue_endstate(
                Dialogue.EndState.DECLINED_CFP, dialogue.is_self_initiated
            )
        else:
            transactions = cast(Transactions, self.context.transactions)
            transaction_msg = transactions.generate_transaction_message(
                TransactionMessage.Performative.PROPOSE_FOR_SIGNING,
                proposal_description,
                dialogue.dialogue_label,
                dialogue.is_seller,
                self.context.agent_address,
            )
            transactions.add_pending_proposal(
                dialogue.dialogue_label, new_msg_id, transaction_msg
            )
            self.context.logger.info(
                "[{}]: sending to {} a Propose{}".format(
                    self.context.agent_name,
                    dialogue.dialogue_label.dialogue_opponent_addr[-5:],
                    pprint.pformat(
                        {
                            "msg_id": new_msg_id,
                            "dialogue_reference": cfp.dialogue_reference,
                            "origin": dialogue.dialogue_label.dialogue_opponent_addr[
                                -5:
                            ],
                            "target": cfp.message_id,
                            "propose": proposal_description.values,
                        }
                    ),
                )
            )
            fipa_msg = FIPAMessage(
                performative=FIPAMessage.Performative.PROPOSE,
                message_id=new_msg_id,
                dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                target=cfp.message_id,
                proposal=[proposal_description],
            )
        dialogue.outgoing_extend(fipa_msg)
        self.context.outbox.put_message(
            to=dialogue.dialogue_label.dialogue_opponent_addr,
            sender=self.context.agent_address,
            protocol_id=FIPAMessage.protocol_id,
            message=FIPASerializer().encode(fipa_msg),
        )

    def _on_propose(self, propose: FIPAMessage, dialogue: Dialogue) -> None:
        """
        Handle a Propose.

        :param propose: the message containing the Propose
        :param dialogue: the dialogue
        :return: None
        """
        new_msg_id = propose.message_id + 1
        strategy = cast(Strategy, self.context.strategy)
        proposals = propose.proposal
        self.context.logger.debug(
            "[{}]: on Propose as {}.".format(self.context.agent_name, dialogue.role)
        )

        for num, proposal_description in enumerate(proposals):
            if num > 0:
                continue  # TODO: allow for dialogue branching with multiple proposals
            transactions = cast(Transactions, self.context.transactions)
            transaction_msg = transactions.generate_transaction_message(
                TransactionMessage.Performative.PROPOSE_FOR_SIGNING,
                proposal_description,
                dialogue.dialogue_label,
                dialogue.is_seller,
                self.context.agent_address,
            )

            if strategy.is_profitable_transaction(
                transaction_msg, is_seller=dialogue.is_seller
            ):
                self.context.logger.info(
                    "[{}]: Accepting propose (as {}).".format(
                        self.context.agent_name, dialogue.role
                    )
                )
                transactions.add_locked_tx(
                    transaction_msg, as_seller=dialogue.is_seller
                )
                transactions.add_pending_initial_acceptance(
                    dialogue.dialogue_label, new_msg_id, transaction_msg
                )
                fipa_msg = FIPAMessage(
                    performative=FIPAMessage.Performative.ACCEPT,
                    message_id=new_msg_id,
                    dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                    target=propose.message_id,
                )
            else:
                self.context.logger.info(
                    "[{}]: Declining propose (as {})".format(
                        self.context.agent_name, dialogue.role
                    )
                )
                fipa_msg = FIPAMessage(
                    performative=FIPAMessage.Performative.DECLINE,
                    message_id=new_msg_id,
                    dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                    target=propose.message_id,
                )
                dialogues = cast(Dialogues, self.context.dialogues)
                dialogues.dialogue_stats.add_dialogue_endstate(
                    Dialogue.EndState.DECLINED_PROPOSE, dialogue.is_self_initiated
                )
            dialogue.outgoing_extend(fipa_msg)
            self.context.outbox.put_message(
                to=dialogue.dialogue_label.dialogue_opponent_addr,
                sender=self.context.agent_address,
                protocol_id=FIPAMessage.protocol_id,
                message=FIPASerializer().encode(fipa_msg),
            )

    def _on_decline(self, decline: FIPAMessage, dialogue: Dialogue) -> None:
        """
        Handle a Decline.

        :param decline: the Decline message
        :param dialogue: the dialogue
        :return: None
        """
        self.context.logger.debug(
            "[{}]: on_decline: msg_id={}, dialogue_reference={}, origin={}, target={}".format(
                self.context.agent_name,
                decline.message_id,
                decline.dialogue_reference,
                dialogue.dialogue_label.dialogue_opponent_addr,
                decline.target,
            )
        )
        target = decline.target
        dialogues = cast(Dialogues, self.context.dialogues)

        if target == 1:
            dialogues.dialogue_stats.add_dialogue_endstate(
                Dialogue.EndState.DECLINED_CFP, dialogue.is_self_initiated
            )
        elif target == 2:
            dialogues.dialogue_stats.add_dialogue_endstate(
                Dialogue.EndState.DECLINED_PROPOSE, dialogue.is_self_initiated
            )
            transactions = cast(Transactions, self.context.transactions)
            transaction_msg = transactions.pop_pending_proposal(
                dialogue.dialogue_label, target
            )
        elif target == 3:
            dialogues.dialogue_stats.add_dialogue_endstate(
                Dialogue.EndState.DECLINED_ACCEPT, dialogue.is_self_initiated
            )
            transactions = cast(Transactions, self.context.transactions)
            transaction_msg = transactions.pop_pending_initial_acceptance(
                dialogue.dialogue_label, target
            )
            transactions.pop_locked_tx(transaction_msg)

    def _on_accept(self, accept: FIPAMessage, dialogue: Dialogue) -> None:
        """
        Handle an Accept.

        :param accept: the Accept message
        :param dialogue: the dialogue
        :return: None
        """
        self.context.logger.debug(
            "[{}]: on_accept: msg_id={}, dialogue_reference={}, origin={}, target={}".format(
                self.context.agent_name,
                accept.message_id,
                accept.dialogue_reference,
                dialogue.dialogue_label.dialogue_opponent_addr,
                accept.target,
            )
        )
        new_msg_id = accept.message_id + 1
        transactions = cast(Transactions, self.context.transactions)
        transaction_msg = transactions.pop_pending_proposal(
            dialogue.dialogue_label, accept.target
        )
        strategy = cast(Strategy, self.context.strategy)

        if strategy.is_profitable_transaction(
            transaction_msg, is_seller=dialogue.is_seller
        ):
            self.context.logger.info(
                "[{}]: locking the current state (as {}).".format(
                    self.context.agent_name, dialogue.role
                )
            )
            transactions.add_locked_tx(transaction_msg, as_seller=dialogue.is_seller)
            self.context.decision_maker_message_queue.put(transaction_msg)
        else:
            self.context.logger.debug(
                "[{}]: decline the Accept (as {}).".format(
                    self.context.agent_name, dialogue.role
                )
            )
            fipa_msg = FIPAMessage(
                performative=FIPAMessage.Performative.DECLINE,
                message_id=new_msg_id,
                dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                target=accept.message_id,
            )
            dialogue.outgoing_extend(fipa_msg)
            dialogues = cast(Dialogues, self.context.dialogues)
            dialogues.dialogue_stats.add_dialogue_endstate(
                Dialogue.EndState.DECLINED_ACCEPT, dialogue.is_self_initiated
            )
            self.context.outbox.put_message(
                to=dialogue.dialogue_label.dialogue_opponent_addr,
                sender=self.context.agent_address,
                protocol_id=FIPAMessage.protocol_id,
                message=FIPASerializer().encode(fipa_msg),
            )

    def _on_match_accept(self, match_accept: FIPAMessage, dialogue: Dialogue) -> None:
        """
        Handle a matching Accept.

        :param match_accept: the MatchAccept message
        :param dialogue: the dialogue
        :return: None
        """
        self.context.logger.debug(
            "[{}]: on_match_accept: msg_id={}, dialogue_reference={}, origin={}, target={}".format(
                self.context.agent_name,
                match_accept.message_id,
                match_accept.dialogue_reference,
                dialogue.dialogue_label.dialogue_opponent_addr,
                match_accept.target,
            )
        )
        if (match_accept.info.get("tx_signature") is not None) and (
            match_accept.info.get("tx_id") is not None
        ):
            transactions = cast(Transactions, self.context.transactions)
            transaction_msg = transactions.pop_pending_initial_acceptance(
                dialogue.dialogue_label, match_accept.target
            )
            transaction_msg.set("skill_callback_ids", ["tac_participation"])
            transaction_msg.set(
                "info",
                {
                    **transaction_msg.info,
                    **{
                        "tx_counterparty_signature": match_accept.info.get(
                            "tx_signature"
                        ),
                        "tx_counterparty_id": match_accept.info.get("tx_id"),
                    },
                },
            )
            self.context.decision_maker_message_queue.put(transaction_msg)
        else:
            self.context.logger.warning(
                "[{}]: match_accept did not contain tx_signature and tx_id!".format(
                    self.context.agent_name
                )
            )


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
        :return: None
        """
        tx_message = cast(TransactionMessage, message)
        if (
            tx_message.performative
            == TransactionMessage.Performative.SUCCESSFUL_SIGNING
        ):
            self.context.logger.info(
                "[{}]: transaction confirmed by decision maker".format(
                    self.context.agent_name
                )
            )
            info = tx_message.info
            dialogue_label = DialogueLabel.from_json(
                cast(Dict[str, str], info.get("dialogue_label"))
            )
            dialogues = cast(Dialogues, self.context.dialogues)
            dialogue = dialogues.dialogues[dialogue_label]
            fipa_message = cast(FIPAMessage, dialogue.last_incoming_message)
            if (
                fipa_message is not None
                and fipa_message.performative == FIPAMessage.Performative.ACCEPT
            ):
                self.context.logger.info(
                    "[{}]: sending match accept to {}.".format(
                        self.context.agent_name,
                        dialogue.dialogue_label.dialogue_opponent_addr[-5:],
                    )
                )
                fipa_msg = FIPAMessage(
                    performative=FIPAMessage.Performative.MATCH_ACCEPT_W_INFORM,
                    message_id=fipa_message.message_id + 1,
                    dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                    target=fipa_message.message_id,
                    info={
                        "tx_signature": tx_message.tx_signature,
                        "tx_id": tx_message.tx_id,
                    },
                )
                dialogue.outgoing_extend(fipa_msg)
                self.context.outbox.put_message(
                    to=dialogue.dialogue_label.dialogue_opponent_addr,
                    sender=self.context.agent_address,
                    protocol_id=FIPAMessage.protocol_id,
                    message=FIPASerializer().encode(fipa_msg),
                )
            else:
                self.context.logger.warning(
                    "[{}]: last message should be of performative accept.".format(
                        self.context.agent_name
                    )
                )
        else:
            self.context.logger.info(
                "[{}]: transaction was not successful.".format(self.context.agent_name)
            )

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass


class OEFSearchHandler(Handler):
    """This class implements the oef search handler."""

    SUPPORTED_PROTOCOL = OefSearchMessage.protocol_id  # type: Optional[ProtocolId]

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
        :return: None
        """
        # convenience representations
        oef_msg = cast(OefSearchMessage, message)

        if oef_msg.performative is OefSearchMessage.Performative.SEARCH_RESULT:
            agents = oef_msg.agents
            search_id = oef_msg.message_id
            search = cast(Search, self.context.search)
            if self.context.agent_address in agents:
                agents.remove(self.context.agent_address)
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

    def _handle_search(
        self, agents: List[str], search_id: int, is_searching_for_sellers: bool
    ) -> None:
        """
        Handle the search response.

        :param agents: the agents returned by the search
        :param is_searching_for_sellers: whether the agent is searching for sellers
        :return: None
        """
        searched_for = "sellers" if is_searching_for_sellers else "buyers"
        if len(agents) > 0:
            self.context.logger.info(
                "[{}]: found potential {} agents={} on search_id={}.".format(
                    self.context.agent_name,
                    searched_for,
                    list(map(lambda x: x[-5:], agents)),
                    search_id,
                )
            )
            strategy = cast(Strategy, self.context.strategy)
            dialogues = cast(Dialogues, self.context.dialogues)
            query = strategy.get_own_services_query(is_searching_for_sellers)

            for opponent_addr in agents:
                dialogue = dialogues.create_self_initiated(
                    opponent_addr,
                    self.context.agent_address,
                    not is_searching_for_sellers,
                )
                self.context.logger.info(
                    "[{}]: sending CFP to agent={}".format(
                        self.context.agent_name, opponent_addr[-5:]
                    )
                )
                fipa_msg = FIPAMessage(
                    message_id=FIPAMessage.STARTING_MESSAGE_ID,
                    dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                    performative=FIPAMessage.Performative.CFP,
                    target=FIPAMessage.STARTING_TARGET,
                    query=query,
                )
                dialogue.outgoing_extend(fipa_msg)
                self.context.outbox.put_message(
                    to=opponent_addr,
                    sender=self.context.agent_address,
                    protocol_id=FIPAMessage.protocol_id,
                    message=FIPASerializer().encode(fipa_msg),
                )
        else:
            self.context.logger.info(
                "[{}]: found no {} agents on search_id={}, continue searching.".format(
                    self.context.agent_name, searched_for, search_id
                )
            )
