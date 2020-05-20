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
from typing import Dict, Optional, Tuple, cast

from aea.configurations.base import ProtocolId, PublicId
from aea.decision_maker.messages.transaction import TransactionMessage
from aea.helpers.dialogue.base import DialogueLabel
from aea.helpers.search.models import Query
from aea.protocols.base import Message
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer
from aea.skills.base import Handler

from packages.fetchai.protocols.fipa.dialogues import FipaDialogue as Dialogue
from packages.fetchai.protocols.fipa.message import FipaMessage
from packages.fetchai.protocols.fipa.serialization import FipaSerializer
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.tac_negotiation.dialogues import Dialogues
from packages.fetchai.skills.tac_negotiation.search import Search
from packages.fetchai.skills.tac_negotiation.strategy import Strategy
from packages.fetchai.skills.tac_negotiation.transactions import Transactions


class FIPANegotiationHandler(Handler):
    """This class implements the fipa negotiation handler."""

    SUPPORTED_PROTOCOL = FipaMessage.protocol_id  # type: Optional[ProtocolId]

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
        fipa_msg = cast(FipaMessage, message)

        # recover dialogue
        dialogues = cast(Dialogues, self.context.dialogues)
        fipa_dialogue = cast(Dialogue, dialogues.update(fipa_msg))
        if fipa_dialogue is None:
            self._handle_unidentified_dialogue(fipa_msg)
            return

        self.context.logger.debug(
            "[{}]: Handling FipaMessage of performative={}".format(
                self.context.agent_name, fipa_msg.performative
            )
        )
        if fipa_msg.performative == FipaMessage.Performative.CFP:
            self._on_cfp(fipa_msg, fipa_dialogue)
        elif fipa_msg.performative == FipaMessage.Performative.PROPOSE:
            self._on_propose(fipa_msg, fipa_dialogue)
        elif fipa_msg.performative == FipaMessage.Performative.DECLINE:
            self._on_decline(fipa_msg, fipa_dialogue)
        elif fipa_msg.performative == FipaMessage.Performative.ACCEPT:
            self._on_accept(fipa_msg, fipa_dialogue)
        elif fipa_msg.performative == FipaMessage.Performative.MATCH_ACCEPT_W_INFORM:
            self._on_match_accept(fipa_msg, fipa_dialogue)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass

    def _handle_unidentified_dialogue(self, msg: FipaMessage) -> None:
        """
        Handle an unidentified dialogue.

        Respond to the sender with a default message containing the appropriate error information.

        :param msg: the message

        :return: None
        """
        self.context.logger.info(
            "[{}]: unidentified dialogue.".format(self.context.agent_name)
        )
        default_msg = DefaultMessage(
            dialogue_reference=("", ""),
            message_id=1,
            target=0,
            performative=DefaultMessage.Performative.ERROR,
            error_code=DefaultMessage.ErrorCode.INVALID_DIALOGUE,
            error_msg="Invalid dialogue.",
            error_data={"fipa_message": b""},
        )  # TODO: send FipaSerializer().encode(msg)
        self.context.outbox.put_message(
            to=msg.counterparty,
            sender=self.context.agent_address,
            protocol_id=DefaultMessage.protocol_id,
            message=DefaultSerializer().encode(default_msg),
        )

    def _on_cfp(self, cfp: FipaMessage, dialogue: Dialogue) -> None:
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
            query, cast(Dialogue.AgentRole, dialogue.role)
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
            fipa_msg = FipaMessage(
                performative=FipaMessage.Performative.DECLINE,
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
                cast(Dialogue.AgentRole, dialogue.role),
                self.context.agent_address,
            )
            transactions.add_pending_proposal(
                dialogue.dialogue_label, new_msg_id, transaction_msg
            )
            self.context.logger.info(
                "[{}]: sending to {} a Propose {}".format(
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
            fipa_msg = FipaMessage(
                performative=FipaMessage.Performative.PROPOSE,
                message_id=new_msg_id,
                dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                target=cfp.message_id,
                proposal=proposal_description,
            )
        fipa_msg.counterparty = cfp.counterparty
        dialogue.update(fipa_msg)
        self.context.outbox.put_message(
            to=dialogue.dialogue_label.dialogue_opponent_addr,
            sender=self.context.agent_address,
            protocol_id=FipaMessage.protocol_id,
            message=FipaSerializer().encode(fipa_msg),
        )

    def _on_propose(self, propose: FipaMessage, dialogue: Dialogue) -> None:
        """
        Handle a Propose.

        :param propose: the message containing the Propose
        :param dialogue: the dialogue
        :return: None
        """
        new_msg_id = propose.message_id + 1
        strategy = cast(Strategy, self.context.strategy)
        proposal_description = propose.proposal
        self.context.logger.debug(
            "[{}]: on Propose as {}.".format(self.context.agent_name, dialogue.role)
        )
        transactions = cast(Transactions, self.context.transactions)
        transaction_msg = transactions.generate_transaction_message(
            TransactionMessage.Performative.PROPOSE_FOR_SIGNING,
            proposal_description,
            dialogue.dialogue_label,
            cast(Dialogue.AgentRole, dialogue.role),
            self.context.agent_address,
        )

        if strategy.is_profitable_transaction(transaction_msg, role=cast(Dialogue.AgentRole, dialogue.role)):
            self.context.logger.info(
                "[{}]: Accepting propose (as {}).".format(
                    self.context.agent_name, dialogue.role
                )
            )
            transactions.add_locked_tx(transaction_msg, role=cast(Dialogue.AgentRole, dialogue.role))
            transactions.add_pending_initial_acceptance(
                dialogue.dialogue_label, new_msg_id, transaction_msg
            )
            fipa_msg = FipaMessage(
                performative=FipaMessage.Performative.ACCEPT,
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
            fipa_msg = FipaMessage(
                performative=FipaMessage.Performative.DECLINE,
                message_id=new_msg_id,
                dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                target=propose.message_id,
            )
            dialogues = cast(Dialogues, self.context.dialogues)
            dialogues.dialogue_stats.add_dialogue_endstate(
                Dialogue.EndState.DECLINED_PROPOSE, dialogue.is_self_initiated
            )
        fipa_msg.counterparty = propose.counterparty
        dialogue.update(fipa_msg)
        self.context.outbox.put_message(
            to=dialogue.dialogue_label.dialogue_opponent_addr,
            sender=self.context.agent_address,
            protocol_id=FipaMessage.protocol_id,
            message=FipaSerializer().encode(fipa_msg),
        )

    def _on_decline(self, decline: FipaMessage, dialogue: Dialogue) -> None:
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

    def _on_accept(self, accept: FipaMessage, dialogue: Dialogue) -> None:
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

        if strategy.is_profitable_transaction(transaction_msg, role=cast(Dialogue.AgentRole, dialogue.role)):
            self.context.logger.info(
                "[{}]: locking the current state (as {}).".format(
                    self.context.agent_name, dialogue.role
                )
            )
            transactions.add_locked_tx(transaction_msg, role=cast(Dialogue.AgentRole, dialogue.role))
            self.context.decision_maker_message_queue.put(transaction_msg)
        else:
            self.context.logger.debug(
                "[{}]: decline the Accept (as {}).".format(
                    self.context.agent_name, dialogue.role
                )
            )
            fipa_msg = FipaMessage(
                performative=FipaMessage.Performative.DECLINE,
                message_id=new_msg_id,
                dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                target=accept.message_id,
            )
            fipa_msg.counterparty = accept.counterparty
            dialogue.update(fipa_msg)
            dialogues = cast(Dialogues, self.context.dialogues)
            dialogues.dialogue_stats.add_dialogue_endstate(
                Dialogue.EndState.DECLINED_ACCEPT, dialogue.is_self_initiated
            )
            self.context.outbox.put_message(
                to=dialogue.dialogue_label.dialogue_opponent_addr,
                sender=self.context.agent_address,
                protocol_id=FipaMessage.protocol_id,
                message=FipaSerializer().encode(fipa_msg),
            )

    def _on_match_accept(self, match_accept: FipaMessage, dialogue: Dialogue) -> None:
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
            transaction_msg.set(
                "skill_callback_ids",
                [PublicId.from_str("fetchai/tac_participation:0.1.0")],
            )
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
            fipa_message = cast(FipaMessage, dialogue.last_incoming_message)
            if (
                fipa_message is not None
                and fipa_message.performative == FipaMessage.Performative.ACCEPT
            ):
                self.context.logger.info(
                    "[{}]: sending match accept to {}.".format(
                        self.context.agent_name,
                        dialogue.dialogue_label.dialogue_opponent_addr[-5:],
                    )
                )
                fipa_msg = FipaMessage(
                    performative=FipaMessage.Performative.MATCH_ACCEPT_W_INFORM,
                    message_id=fipa_message.message_id + 1,
                    dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                    target=fipa_message.message_id,
                    info={
                        "tx_signature": tx_message.signed_payload.get("tx_signature"),
                        "tx_id": tx_message.tx_id,
                    },
                )
                dialogue.outgoing_extend(fipa_msg)
                self.context.outbox.put_message(
                    to=dialogue.dialogue_label.dialogue_opponent_addr,
                    sender=self.context.agent_address,
                    protocol_id=FipaMessage.protocol_id,
                    message=FipaSerializer().encode(fipa_msg),
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
            agents = list(oef_msg.agents)
            search_id = int(oef_msg.dialogue_reference[0])
            search = cast(Search, self.context.search)
            if self.context.agent_address in agents:
                agents.remove(self.context.agent_address)
            agents_less_self = tuple(agents)
            if search_id in search.ids_for_sellers:
                self._handle_search(
                    agents_less_self, search_id, is_searching_for_sellers=True
                )
            elif search_id in search.ids_for_buyers:
                self._handle_search(
                    agents_less_self, search_id, is_searching_for_sellers=False
                )

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass

    def _handle_search(
        self, agents: Tuple[str, ...], search_id: int, is_searching_for_sellers: bool
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
            query = strategy.get_own_services_query(
                is_searching_for_sellers, is_search_query=False
            )

            for opponent_addr in agents:
                self.context.logger.info(
                    "[{}]: sending CFP to agent={}".format(
                        self.context.agent_name, opponent_addr[-5:]
                    )
                )
                fipa_msg = FipaMessage(
                    message_id=Dialogue.STARTING_MESSAGE_ID,
                    dialogue_reference=dialogues.new_self_initiated_dialogue_reference(),
                    performative=FipaMessage.Performative.CFP,
                    target=Dialogue.STARTING_TARGET,
                    query=query,
                )
                fipa_msg.counterparty = opponent_addr
                dialogues.update(fipa_msg)
                self.context.outbox.put_message(
                    to=opponent_addr,
                    sender=self.context.agent_address,
                    protocol_id=FipaMessage.protocol_id,
                    message=FipaSerializer().encode(fipa_msg),
                )
        else:
            self.context.logger.info(
                "[{}]: found no {} agents on search_id={}, continue searching.".format(
                    self.context.agent_name, searched_for, search_id
                )
            )
