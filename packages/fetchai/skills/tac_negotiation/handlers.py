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
import time
from typing import Dict, Optional, Tuple, cast

from aea.configurations.base import ProtocolId, PublicId
from aea.helpers.dialogue.base import DialogueLabel
from aea.helpers.search.models import Query
from aea.protocols.base import Message
from aea.protocols.default.message import DefaultMessage
from aea.protocols.signing.message import SigningMessage
from aea.skills.base import Handler

from packages.fetchai.protocols.fipa.message import FipaMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.tac_negotiation.dialogues import Dialogue, Dialogues
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
            error_data={"fipa_message": msg.encode()},
        )
        default_msg.counterparty = msg.counterparty
        self.context.outbox.put_message(message=default_msg)

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
            query, cast(Dialogue.Role, dialogue.role)
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
                SigningMessage.Performative.SIGN_MESSAGE,
                proposal_description,
                dialogue.dialogue_label,
                cast(Dialogue.Role, dialogue.role),
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
        self.context.outbox.put_message(message=fipa_msg)

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
            SigningMessage.Performative.SIGN_MESSAGE,
            proposal_description,
            dialogue.dialogue_label,
            cast(Dialogue.Role, dialogue.role),
            self.context.agent_address,
        )

        if strategy.is_profitable_transaction(
            transaction_msg, role=cast(Dialogue.Role, dialogue.role)
        ):
            self.context.logger.info(
                "[{}]: Accepting propose (as {}).".format(
                    self.context.agent_name, dialogue.role
                )
            )
            transactions.add_locked_tx(
                transaction_msg, role=cast(Dialogue.Role, dialogue.role)
            )
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
        self.context.outbox.put_message(message=fipa_msg)

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

        if strategy.is_profitable_transaction(
            transaction_msg, role=cast(Dialogue.Role, dialogue.role)
        ):
            self.context.logger.info(
                "[{}]: locking the current state (as {}).".format(
                    self.context.agent_name, dialogue.role
                )
            )
            transactions.add_locked_tx(
                transaction_msg, role=cast(Dialogue.Role, dialogue.role)
            )
            if strategy.is_contract_tx:
                pass
                # contract = cast(ERC1155Contract, self.context.contracts.erc1155)
                # if not contract.is_deployed:
                #     ledger_api = self.context.ledger_apis.get_api(strategy.ledger_id)
                #     contract_address = self.context.shared_state.get(
                #         "erc1155_contract_address", None
                #     )
                #     assert (
                #         contract_address is not None
                #     ), "ERC1155Contract address not set!"
                # tx_nonce = transaction_msg.skill_callback_info.get("tx_nonce", None)
                # assert tx_nonce is not None, "tx_nonce must be provided"
                # transaction_msg = contract.get_hash_batch_transaction_msg(
                #     from_address=accept.counterparty,
                #     to_address=self.context.agent_address,  # must match self
                #     token_ids=[
                #         int(key)
                #         for key in transaction_msg.terms.quantities_by_good_id.keys()
                #     ]
                #     + [
                #         int(key)
                #         for key in transaction_msg.terms.amount_by_currency_id.keys()
                #     ],
                #     from_supplies=[
                #         quantity if quantity > 0 else 0
                #         for quantity in transaction_msg.terms.quantities_by_good_id.values()
                #     ]
                #     + [
                #         value if value > 0 else 0
                #         for value in transaction_msg.terms.amount_by_currency_id.values()
                #     ],
                #     to_supplies=[
                #         -quantity if quantity < 0 else 0
                #         for quantity in transaction_msg.terms.quantities_by_good_id.values()
                #     ]
                #     + [
                #         -value if value < 0 else 0
                #         for value in transaction_msg.terms.amount_by_currency_id.values()
                #     ],
                #     value=0,
                #     trade_nonce=int(tx_nonce),
                #     ledger_api=self.context.ledger_apis.get_api(strategy.ledger_id),
                #     skill_callback_id=self.context.skill_id,
                #     skill_callback_info={
                #         "dialogue_label": dialogue.dialogue_label.json
                #     },
                # )
            self.context.logger.info(
                "[{}]: sending tx_message={} to decison maker.".format(
                    self.context.agent_name, transaction_msg
                )
            )
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
            self.context.outbox.put_message(message=fipa_msg)

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
            strategy = cast(Strategy, self.context.strategy)
            if strategy.is_contract_tx:
                pass
                # contract = cast(ERC1155Contract, self.context.contracts.erc1155)
                # if not contract.is_deployed:
                #     ledger_api = self.context.ledger_apis.get_api(strategy.ledger_id)
                #     contract_address = self.context.shared_state.get(
                #         "erc1155_contract_address", None
                #     )
                #     assert (
                #         contract_address is not None
                #     ), "ERC1155Contract address not set!"
                #     contract.set_deployed_instance(
                #         ledger_api, cast(str, contract_address),
                #     )
                # strategy = cast(Strategy, self.context.strategy)
                # tx_nonce = transaction_msg.skill_callback_info.get("tx_nonce", None)
                # tx_signature = match_accept.info.get("tx_signature", None)
                # assert (
                #     tx_nonce is not None and tx_signature is not None
                # ), "tx_nonce or tx_signature not available"
                # transaction_msg = contract.get_atomic_swap_batch_transaction_msg(
                #     from_address=self.context.agent_address,
                #     to_address=match_accept.counterparty,
                #     token_ids=[
                #         int(key)
                #         for key in transaction_msg.terms.quantities_by_good_id.keys()
                #     ]
                #     + [
                #         int(key)
                #         for key in transaction_msg.terms.amount_by_currency_id.keys()
                #     ],
                #     from_supplies=[
                #         -quantity if quantity < 0 else 0
                #         for quantity in transaction_msg.terms.quantities_by_good_id.values()
                #     ]
                #     + [
                #         -value if value < 0 else 0
                #         for value in transaction_msg.terms.amount_by_currency_id.values()
                #     ],
                #     to_supplies=[
                #         quantity if quantity > 0 else 0
                #         for quantity in transaction_msg.terms.quantities_by_good_id.values()
                #     ]
                #     + [
                #         value if value > 0 else 0
                #         for value in transaction_msg.terms.amount_by_currency_id.values()
                #     ],
                #     value=0,
                #     trade_nonce=int(tx_nonce),
                #     ledger_api=self.context.ledger_apis.get_api(strategy.ledger_id),
                #     skill_callback_id=self.context.skill_id,
                #     signature=tx_signature,
                #     skill_callback_info={
                #         "dialogue_label": dialogue.dialogue_label.json
                #     },
                # )
            else:
                transaction_msg.set(
                    "skill_callback_ids",
                    [PublicId.from_str("fetchai/tac_participation:0.4.0")],
                )
                transaction_msg.set(
                    "skill_callback_info",
                    {
                        **transaction_msg.skill_callback_info,
                        **{
                            "tx_counterparty_signature": match_accept.info.get(
                                "tx_signature"
                            ),
                            "tx_counterparty_id": match_accept.info.get("tx_id"),
                        },
                    },
                )
            self.context.logger.info(
                "[{}]: sending tx_message={} to decison maker.".format(
                    self.context.agent_name, transaction_msg
                )
            )
            self.context.decision_maker_message_queue.put(transaction_msg)
        else:
            self.context.logger.warning(
                "[{}]: match_accept did not contain tx_signature and tx_id!".format(
                    self.context.agent_name
                )
            )


class SigningHandler(Handler):
    """This class implements the transaction handler."""

    SUPPORTED_PROTOCOL = SigningMessage.protocol_id  # type: Optional[ProtocolId]

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
        tx_message = cast(SigningMessage, message)
        if tx_message.performative == SigningMessage.Performative.SIGNED_MESSAGE:
            self.context.logger.info(
                "[{}]: transaction confirmed by decision maker".format(
                    self.context.agent_name
                )
            )
            strategy = cast(Strategy, self.context.strategy)
            dialogue_label = DialogueLabel.from_json(
                cast(
                    Dict[str, str], tx_message.skill_callback_info.get("dialogue_label")
                )
            )
            dialogues = cast(Dialogues, self.context.dialogues)
            dialogue = dialogues.dialogues[dialogue_label]
            last_fipa_message = cast(FipaMessage, dialogue.last_incoming_message)
            if (
                last_fipa_message is not None
                and last_fipa_message.performative == FipaMessage.Performative.ACCEPT
            ):
                self.context.logger.info(
                    "[{}]: sending match accept to {}.".format(
                        self.context.agent_name,
                        dialogue.dialogue_label.dialogue_opponent_addr[-5:],
                    )
                )
                fipa_msg = FipaMessage(
                    performative=FipaMessage.Performative.MATCH_ACCEPT_W_INFORM,
                    message_id=last_fipa_message.message_id + 1,
                    dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                    target=last_fipa_message.message_id,
                    info={
                        "tx_signature": tx_message.signed_transaction,
                        "tx_id": tx_message.dialogue_reference[0],
                    },
                )
                fipa_msg.counterparty = dialogue.dialogue_label.dialogue_opponent_addr
                dialogue.update(fipa_msg)
                self.context.outbox.put_message(message=fipa_msg)
            elif (
                last_fipa_message is not None
                and last_fipa_message.performative
                == FipaMessage.Performative.MATCH_ACCEPT_W_INFORM
                and strategy.is_contract_tx
            ):
                self.context.logger.info(
                    "[{}]: sending atomic swap tx to ledger.".format(
                        self.context.agent_name
                    )
                )
                tx_signed = tx_message.signed_transaction
                tx_digest = self.context.ledger_apis.get_api(
                    strategy.ledger_id
                ).send_signed_transaction(tx_signed=tx_signed)
                # TODO; handle case when no tx_digest returned and remove loop
                assert tx_digest is not None, "Error when submitting tx."
                self.context.logger.info(
                    "[{}]: tx_digest={}.".format(self.context.agent_name, tx_digest)
                )
                count = 0
                while (
                    not self.context.ledger_apis.get_api(
                        strategy.ledger_id
                    ).is_transaction_settled(tx_digest)
                    and count < 20
                ):
                    self.context.logger.info(
                        "[{}]: waiting for tx to confirm. Sleeping for 3 seconds ...".format(
                            self.context.agent_name
                        )
                    )
                    time.sleep(3.0)
                    count += 1
                tx_receipt = self.context.ledger_apis.get_api(
                    strategy.ledger_id
                ).get_transaction_receipt(tx_digest=tx_digest)
                if tx_receipt is None:
                    self.context.logger.info(
                        "[{}]: Failed to get tx receipt for atomic swap.".format(
                            self.context.agent_name
                        )
                    )
                elif tx_receipt.status != 1:
                    self.context.logger.info(
                        "[{}]: Failed to conduct atomic swap.".format(
                            self.context.agent_name
                        )
                    )
                else:
                    self.context.logger.info(
                        "[{}]: Successfully conducted atomic swap. Transaction digest: {}".format(
                            self.context.agent_name, tx_digest
                        )
                    )
                    # contract = cast(ERC1155Contract, self.context.contracts.erc1155)
                    # result = contract.get_balances(
                    #     address=self.context.agent_address,
                    #     token_ids=[
                    #         int(key)
                    #         for key in tx_message.terms.quantities_by_good_id.keys()
                    #     ]
                    #     + [
                    #         int(key)
                    #         for key in tx_message.terms.amount_by_currency_id.keys()
                    #     ],
                    # )
                    result = 0
                    self.context.logger.info(
                        "[{}]: Current balances: {}".format(
                            self.context.agent_name, result
                        )
                    )
            else:
                self.context.logger.warning(
                    "[{}]: last message should be of performative accept or match accept.".format(
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
                self.context.outbox.put_message(message=fipa_msg)
        else:
            self.context.logger.info(
                "[{}]: found no {} agents on search_id={}, continue searching.".format(
                    self.context.agent_name, searched_for, search_id
                )
            )
