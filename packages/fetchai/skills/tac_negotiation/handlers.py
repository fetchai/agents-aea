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
from packages.fetchai.skills.tac_negotiation.dialogues import (
    FipaDialogue,
    FipaDialogues,
    OefSearchDialogue,
    OefSearchDialogues,
    SigningDialogue,
    SigningDialogues,
)
from packages.fetchai.skills.tac_negotiation.search import Search
from packages.fetchai.skills.tac_negotiation.strategy import Strategy
from packages.fetchai.skills.tac_negotiation.transactions import Transactions


class FipaNegotiationHandler(Handler):
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
        dialogues = cast(FipaDialogues, self.context.dialogues)
        fipa_dialogue = cast(FipaDialogue, dialogues.update(fipa_msg))
        if fipa_dialogue is None:
            self._handle_unidentified_dialogue(fipa_msg)
            return

        self.context.logger.debug(
            "handling FipaMessage of performative={}".format(fipa_msg.performative)
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
        self.context.logger.info("unidentified dialogue.")
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

    def _on_cfp(self, cfp: FipaMessage, dialogue: FipaDialogue) -> None:
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
            query, cast(FipaDialogue.Role, dialogue.role)
        )

        if proposal_description is None:
            self.context.logger.debug(
                "sending to {} a Decline{}".format(
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
            dialogues = cast(FipaDialogues, self.context.dialogues)
            dialogues.dialogue_stats.add_dialogue_endstate(
                FipaDialogue.EndState.DECLINED_CFP, dialogue.is_self_initiated
            )
        else:
            transactions = cast(Transactions, self.context.transactions)
            transaction_msg = transactions.generate_transaction_message(
                SigningMessage.Performative.SIGN_MESSAGE,
                proposal_description,
                dialogue.dialogue_label,
                cast(FipaDialogue.Role, dialogue.role),
                self.context.agent_address,
            )
            transactions.add_pending_proposal(
                dialogue.dialogue_label, new_msg_id, transaction_msg
            )
            self.context.logger.info(
                "sending to {} a Propose {}".format(
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

    def _on_propose(self, propose: FipaMessage, dialogue: FipaDialogue) -> None:
        """
        Handle a Propose.

        :param propose: the message containing the Propose
        :param dialogue: the dialogue
        :return: None
        """
        new_msg_id = propose.message_id + 1
        strategy = cast(Strategy, self.context.strategy)
        proposal_description = propose.proposal
        self.context.logger.debug("on Propose as {}.".format(dialogue.role))
        transactions = cast(Transactions, self.context.transactions)
        transaction_msg = transactions.generate_transaction_message(
            SigningMessage.Performative.SIGN_MESSAGE,
            proposal_description,
            dialogue.dialogue_label,
            cast(FipaDialogue.Role, dialogue.role),
            self.context.agent_address,
        )

        if strategy.is_profitable_transaction(
            transaction_msg, role=cast(FipaDialogue.Role, dialogue.role)
        ):
            self.context.logger.info("accepting propose (as {}).".format(dialogue.role))
            transactions.add_locked_tx(
                transaction_msg, role=cast(FipaDialogue.Role, dialogue.role)
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
            self.context.logger.info("declining propose (as {})".format(dialogue.role))
            fipa_msg = FipaMessage(
                performative=FipaMessage.Performative.DECLINE,
                message_id=new_msg_id,
                dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                target=propose.message_id,
            )
            dialogues = cast(FipaDialogues, self.context.dialogues)
            dialogues.dialogue_stats.add_dialogue_endstate(
                FipaDialogue.EndState.DECLINED_PROPOSE, dialogue.is_self_initiated
            )
        fipa_msg.counterparty = propose.counterparty
        dialogue.update(fipa_msg)
        self.context.outbox.put_message(message=fipa_msg)

    def _on_decline(self, decline: FipaMessage, dialogue: FipaDialogue) -> None:
        """
        Handle a Decline.

        :param decline: the Decline message
        :param dialogue: the dialogue
        :return: None
        """
        self.context.logger.debug(
            "on_decline: msg_id={}, dialogue_reference={}, origin={}, target={}".format(
                decline.message_id,
                decline.dialogue_reference,
                dialogue.dialogue_label.dialogue_opponent_addr,
                decline.target,
            )
        )
        target = decline.target
        dialogues = cast(FipaDialogues, self.context.dialogues)

        if target == 1:
            dialogues.dialogue_stats.add_dialogue_endstate(
                FipaDialogue.EndState.DECLINED_CFP, dialogue.is_self_initiated
            )
        elif target == 2:
            dialogues.dialogue_stats.add_dialogue_endstate(
                FipaDialogue.EndState.DECLINED_PROPOSE, dialogue.is_self_initiated
            )
            transactions = cast(Transactions, self.context.transactions)
            transaction_msg = transactions.pop_pending_proposal(
                dialogue.dialogue_label, target
            )
        elif target == 3:
            dialogues.dialogue_stats.add_dialogue_endstate(
                FipaDialogue.EndState.DECLINED_ACCEPT, dialogue.is_self_initiated
            )
            transactions = cast(Transactions, self.context.transactions)
            transaction_msg = transactions.pop_pending_initial_acceptance(
                dialogue.dialogue_label, target
            )
            transactions.pop_locked_tx(transaction_msg)

    def _on_accept(self, accept: FipaMessage, dialogue: FipaDialogue) -> None:
        """
        Handle an Accept.

        :param accept: the Accept message
        :param dialogue: the dialogue
        :return: None
        """
        self.context.logger.debug(
            "on_accept: msg_id={}, dialogue_reference={}, origin={}, target={}".format(
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
            transaction_msg, role=cast(FipaDialogue.Role, dialogue.role)
        ):
            self.context.logger.info(
                "locking the current state (as {}).".format(dialogue.role)
            )
            transactions.add_locked_tx(
                transaction_msg, role=cast(FipaDialogue.Role, dialogue.role)
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
                "sending tx_message={} to decison maker.".format(transaction_msg)
            )
            self.context.decision_maker_message_queue.put(transaction_msg)
        else:
            self.context.logger.debug(
                "decline the Accept (as {}).".format(dialogue.role)
            )
            fipa_msg = FipaMessage(
                performative=FipaMessage.Performative.DECLINE,
                message_id=new_msg_id,
                dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                target=accept.message_id,
            )
            fipa_msg.counterparty = accept.counterparty
            dialogue.update(fipa_msg)
            dialogues = cast(FipaDialogues, self.context.dialogues)
            dialogues.dialogue_stats.add_dialogue_endstate(
                FipaDialogue.EndState.DECLINED_ACCEPT, dialogue.is_self_initiated
            )
            self.context.outbox.put_message(message=fipa_msg)

    def _on_match_accept(
        self, match_accept: FipaMessage, dialogue: FipaDialogue
    ) -> None:
        """
        Handle a matching Accept.

        :param match_accept: the MatchAccept message
        :param dialogue: the dialogue
        :return: None
        """
        self.context.logger.debug(
            "on_match_accept: msg_id={}, dialogue_reference={}, origin={}, target={}".format(
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
                    [PublicId.from_str("fetchai/tac_participation:0.5.0")],
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
                "sending tx_message={} to decison maker.".format(transaction_msg)
            )
            self.context.decision_maker_message_queue.put(transaction_msg)
        else:
            self.context.logger.warning(
                "match_accept did not contain tx_signature and tx_id!"
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
        signing_msg = cast(SigningMessage, message)

        # recover dialogue
        signing_dialogues = cast(SigningDialogues, self.context.signing_dialogues)
        signing_dialogue = cast(
            Optional[SigningDialogue], signing_dialogues.update(signing_msg)
        )
        if signing_dialogue is None:
            self._handle_unidentified_dialogue(signing_msg)
            return

        # handle message
        if signing_msg.performative is SigningMessage.Performative.SIGNED_TRANSACTION:
            self._handle_signed_message(signing_msg, signing_dialogue)
        elif signing_msg.performative is SigningMessage.Performative.ERROR:
            self._handle_error(signing_msg, signing_dialogue)
        else:
            self._handle_invalid(signing_msg, signing_dialogue)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass

    def _handle_unidentified_dialogue(self, signing_msg: SigningMessage) -> None:
        """
        Handle an unidentified dialogue.

        :param msg: the message
        """
        self.context.logger.info(
            "received invalid signing message={}, unidentified dialogue.".format(
                signing_msg
            )
        )

    def _handle_signed_message(
        self, signing_msg: SigningMessage, signing_dialogue: SigningDialogue
    ) -> None:
        """
        Handle an oef search message.

        :param signing_msg: the signing message
        :param signing_dialogue: the dialogue
        :return: None
        """
        self.context.logger.info("transaction confirmed by decision maker")
        strategy = cast(Strategy, self.context.strategy)
        dialogue_label = DialogueLabel.from_json(
            cast(Dict[str, str], signing_msg.skill_callback_info.get("dialogue_label"))
        )
        dialogues = cast(FipaDialogues, self.context.dialogues)
        dialogue = dialogues.dialogues[dialogue_label]
        last_fipa_message = cast(FipaMessage, dialogue.last_incoming_message)
        if (
            last_fipa_message is not None
            and last_fipa_message.performative == FipaMessage.Performative.ACCEPT
        ):
            self.context.logger.info(
                "sending match accept to {}.".format(
                    dialogue.dialogue_label.dialogue_opponent_addr[-5:],
                )
            )
            fipa_msg = FipaMessage(
                performative=FipaMessage.Performative.MATCH_ACCEPT_W_INFORM,
                message_id=last_fipa_message.message_id + 1,
                dialogue_reference=dialogue.dialogue_label.dialogue_reference,
                target=last_fipa_message.message_id,
                info={
                    "tx_signature": signing_msg.signed_transaction,
                    "tx_id": signing_msg.dialogue_reference[0],
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
            self.context.logger.info("sending atomic swap tx to ledger.")
            tx_signed = signing_msg.signed_transaction
            tx_digest = self.context.ledger_apis.get_api(
                strategy.ledger_id
            ).send_signed_transaction(tx_signed=tx_signed)
            # TODO; handle case when no tx_digest returned and remove loop
            assert tx_digest is not None, "Error when submitting tx."
            self.context.logger.info("tx_digest={}.".format(tx_digest))
            count = 0
            while (
                not self.context.ledger_apis.get_api(
                    strategy.ledger_id
                ).is_transaction_settled(tx_digest)
                and count < 20
            ):
                self.context.logger.info(
                    "waiting for tx to confirm. Sleeping for 3 seconds ..."
                )
                time.sleep(3.0)
                count += 1
            tx_receipt = self.context.ledger_apis.get_api(
                strategy.ledger_id
            ).get_transaction_receipt(tx_digest=tx_digest)
            if tx_receipt is None:
                self.context.logger.info("failed to get tx receipt for atomic swap.")
            elif tx_receipt.status != 1:
                self.context.logger.info("failed to conduct atomic swap.")
            else:
                self.context.logger.info(
                    "successfully conducted atomic swap. Transaction digest: {}".format(
                        tx_digest
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
                self.context.logger.info("current balances: {}".format(result))
        else:
            self.context.logger.warning(
                "last message should be of performative accept or match accept."
            )

    def _handle_error(
        self, signing_msg: SigningMessage, signing_dialogue: SigningDialogue
    ) -> None:
        """
        Handle an oef search message.

        :param signing_msg: the signing message
        :param signing_dialogue: the dialogue
        :return: None
        """
        self.context.logger.info(
            "transaction signing was not successful. Error_code={} in dialogue={}".format(
                signing_msg.error_code, signing_dialogue
            )
        )

    def _handle_invalid(
        self, signing_msg: SigningMessage, signing_dialogue: SigningDialogue
    ) -> None:
        """
        Handle an oef search message.

        :param signing_msg: the signing message
        :param signing_dialogue: the dialogue
        :return: None
        """
        self.context.logger.warning(
            "cannot handle signing message of performative={} in dialogue={}.".format(
                signing_msg.performative, signing_dialogue
            )
        )


class OefSearchHandler(Handler):
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
        oef_search_msg = cast(OefSearchMessage, message)

        # recover dialogue
        oef_search_dialogues = cast(
            OefSearchDialogues, self.context.oef_search_dialogues
        )
        oef_search_dialogue = cast(
            Optional[OefSearchDialogue], oef_search_dialogues.update(oef_search_msg)
        )
        if oef_search_dialogue is None:
            self._handle_unidentified_dialogue(oef_search_msg)
            return

        # handle message
        if oef_search_msg.performative == OefSearchMessage.Performative.SEARCH_RESULT:
            self._on_search_result(oef_search_msg, oef_search_dialogue)
        elif oef_search_msg.performative == OefSearchMessage.Performative.OEF_ERROR:
            self._on_oef_error(oef_search_msg, oef_search_dialogue)
        else:
            self._handle_invalid(oef_search_msg, oef_search_dialogue)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass

    def _handle_unidentified_dialogue(self, oef_search_msg: OefSearchMessage) -> None:
        """
        Handle an unidentified dialogue.

        :param msg: the message
        """
        self.context.logger.warning(
            "received invalid oef_search message={}, unidentified dialogue.".format(
                oef_search_msg
            )
        )

    def _on_oef_error(
        self, oef_search_msg: OefSearchMessage, oef_search_dialogue: OefSearchDialogue
    ) -> None:
        """
        Handle an OEF error message.

        :param oef_search_msg: the oef search msg
        :param oef_search_dialogue: the dialogue
        :return: None
        """
        self.context.logger.warning(
            "received OEF Search error: dialogue_reference={}, oef_error_operation={}".format(
                oef_search_msg.dialogue_reference, oef_search_msg.oef_error_operation,
            )
        )

    def _on_search_result(
        self, oef_search_msg: OefSearchMessage, oef_search_dialogue: OefSearchDialogue
    ) -> None:
        """
        Split the search results from the OEF search node.

        :param oef_search_msg: the search result
        :param oef_search_dialogue: the dialogue
        :return: None
        """
        agents = list(oef_search_msg.agents)
        search_id = int(oef_search_msg.dialogue_reference[0])
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
                "found potential {} agents={} on search_id={}.".format(
                    searched_for, list(map(lambda x: x[-5:], agents)), search_id,
                )
            )
            strategy = cast(Strategy, self.context.strategy)
            dialogues = cast(FipaDialogues, self.context.dialogues)
            query = strategy.get_own_services_query(
                is_searching_for_sellers, is_search_query=False
            )

            for opponent_addr in agents:
                self.context.logger.info(
                    "sending CFP to agent={}".format(opponent_addr[-5:])
                )
                fipa_msg = FipaMessage(
                    dialogue_reference=dialogues.new_self_initiated_dialogue_reference(),
                    performative=FipaMessage.Performative.CFP,
                    query=query,
                )
                fipa_msg.counterparty = opponent_addr
                dialogues.update(fipa_msg)
                self.context.outbox.put_message(message=fipa_msg)
        else:
            self.context.logger.info(
                "found no {} agents on search_id={}, continue searching.".format(
                    searched_for, search_id
                )
            )

    def _handle_invalid(
        self, oef_search_msg: OefSearchMessage, oef_search_dialogue: OefSearchDialogue
    ) -> None:
        """
        Handle an oef search message.

        :param oef_search_msg: the oef search message
        :param oef_search_dialogue: the dialogue
        :return: None
        """
        self.context.logger.warning(
            "cannot handle oef_search message of performative={} in dialogue={}.".format(
                oef_search_msg.performative, oef_search_dialogue,
            )
        )
