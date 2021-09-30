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

from collections import OrderedDict
from typing import Optional, Tuple, cast

from aea_ledger_ethereum import EthereumApi
from aea_ledger_fetchai import FetchAIApi

from aea.configurations.base import PublicId
from aea.crypto.ledger_apis import LedgerApis
from aea.exceptions import enforce
from aea.helpers.transaction.base import RawMessage, RawTransaction
from aea.protocols.base import Message
from aea.protocols.dialogue.base import DialogueLabel
from aea.skills.base import Handler

from packages.fetchai.connections.ledger.base import (
    CONNECTION_ID as LEDGER_CONNECTION_PUBLIC_ID,
)
from packages.fetchai.protocols.contract_api.message import ContractApiMessage
from packages.fetchai.protocols.cosm_trade.message import CosmTradeMessage
from packages.fetchai.protocols.default.message import DefaultMessage
from packages.fetchai.protocols.fipa.message import FipaMessage
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.protocols.signing.message import SigningMessage
from packages.fetchai.skills.tac_negotiation.behaviours import (
    GoodsRegisterAndSearchBehaviour,
)
from packages.fetchai.skills.tac_negotiation.dialogues import (
    ContractApiDialogue,
    ContractApiDialogues,
    CosmTradeDialogue,
    CosmTradeDialogues,
    DefaultDialogues,
    FipaDialogue,
    FipaDialogues,
    LedgerApiDialogue,
    LedgerApiDialogues,
    OefSearchDialogue,
    OefSearchDialogues,
    SigningDialogue,
    SigningDialogues,
)
from packages.fetchai.skills.tac_negotiation.strategy import Strategy
from packages.fetchai.skills.tac_negotiation.transactions import Transactions


LEDGER_API_ADDRESS = str(LEDGER_CONNECTION_PUBLIC_ID)


class FipaNegotiationHandler(Handler):
    """This class implements the fipa negotiation handler."""

    SUPPORTED_PROTOCOL = FipaMessage.protocol_id  # type: Optional[PublicId]

    def setup(self) -> None:
        """Implement the setup."""

    def handle(self, message: Message) -> None:
        """
        Dispatch message to relevant handler and respond.

        :param message: the message
        """
        fipa_msg = cast(FipaMessage, message)

        # recover dialogue
        fipa_dialogues = cast(FipaDialogues, self.context.fipa_dialogues)
        fipa_dialogue = cast(FipaDialogue, fipa_dialogues.update(fipa_msg))
        if fipa_dialogue is None:
            self._handle_unidentified_dialogue(fipa_msg)
            return

        self.context.logger.info(
            "received {} from {} (as {}), message={}".format(
                fipa_msg.performative.value,
                fipa_msg.sender[-5:],
                fipa_dialogue.role,
                fipa_msg,
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
        """Implement the handler teardown."""

    def _handle_unidentified_dialogue(self, fipa_msg: FipaMessage) -> None:
        """
        Handle an unidentified dialogue.

        Respond to the sender with a default message containing the appropriate error information.

        :param fipa_msg: the message
        """
        self.context.logger.info(
            "received invalid fipa message={}, unidentified dialogue.".format(fipa_msg)
        )
        default_dialogues = cast(DefaultDialogues, self.context.default_dialogues)
        default_msg, _ = default_dialogues.create(
            counterparty=fipa_msg.sender,
            performative=DefaultMessage.Performative.ERROR,
            error_code=DefaultMessage.ErrorCode.INVALID_DIALOGUE,
            error_msg="Invalid dialogue.",
            error_data={"fipa_message": fipa_msg.encode()},
        )
        self.context.outbox.put_message(message=default_msg)

    def _on_cfp(self, cfp: FipaMessage, fipa_dialogue: FipaDialogue) -> None:
        """
        Handle a CFP.

        :param cfp: the fipa message containing the CFP
        :param fipa_dialogue: the fipa_dialogue
        """
        strategy = cast(Strategy, self.context.strategy)
        proposal = strategy.get_proposal_for_query(
            cfp.query, cast(FipaDialogue.Role, fipa_dialogue.role)
        )
        if proposal is None:
            fipa_msg = fipa_dialogue.reply(
                performative=FipaMessage.Performative.DECLINE, target_message=cfp,
            )
            fipa_dialogues = cast(FipaDialogues, self.context.fipa_dialogues)
            fipa_dialogues.dialogue_stats.add_dialogue_endstate(
                FipaDialogue.EndState.DECLINED_CFP, fipa_dialogue.is_self_initiated
            )
        else:
            transactions = cast(Transactions, self.context.transactions)
            fipa_msg = fipa_dialogue.reply(
                performative=FipaMessage.Performative.PROPOSE,
                target_message=cfp,
                proposal=proposal,
            )
            fipa_dialogue.terms = strategy.terms_from_proposal(
                proposal,
                self.context.agent_address,
                cfp.sender,
                cast(FipaDialogue.Role, fipa_dialogue.role),
            )
            transactions.add_pending_proposal(
                fipa_dialogue.dialogue_label, fipa_msg.message_id, fipa_dialogue.terms
            )
        self.context.logger.info(
            "sending {} to {} (as {}), message={}".format(
                fipa_msg.performative, fipa_msg.to[-5:], fipa_dialogue.role, fipa_msg
            )
        )
        self.context.outbox.put_message(message=fipa_msg)

    def _on_propose(self, propose: FipaMessage, fipa_dialogue: FipaDialogue) -> None:
        """
        Handle a Propose.

        :param propose: the message containing the Propose
        :param fipa_dialogue: the fipa_dialogue
        """
        strategy = cast(Strategy, self.context.strategy)
        fipa_dialogue.terms = strategy.terms_from_proposal(
            propose.proposal,
            self.context.agent_address,
            propose.sender,
            cast(FipaDialogue.Role, fipa_dialogue.role),
        )
        transactions = cast(Transactions, self.context.transactions)
        if strategy.is_profitable_transaction(
            fipa_dialogue.terms, role=cast(FipaDialogue.Role, fipa_dialogue.role)
        ):
            fipa_msg = fipa_dialogue.reply(
                performative=FipaMessage.Performative.ACCEPT, target_message=propose,
            )
            transactions.add_locked_tx(
                fipa_dialogue.terms, role=cast(FipaDialogue.Role, fipa_dialogue.role)
            )
            transactions.add_pending_initial_acceptance(
                fipa_dialogue.dialogue_label, fipa_msg.message_id, fipa_dialogue.terms
            )
        else:
            fipa_msg = fipa_dialogue.reply(
                performative=FipaMessage.Performative.DECLINE, target_message=propose,
            )
            fipa_dialogues = cast(FipaDialogues, self.context.fipa_dialogues)
            fipa_dialogues.dialogue_stats.add_dialogue_endstate(
                FipaDialogue.EndState.DECLINED_PROPOSE, fipa_dialogue.is_self_initiated
            )
        self.context.logger.info(
            "sending {} to {} (as {}), message={}".format(
                fipa_msg.performative, fipa_msg.to[-5:], fipa_dialogue.role, fipa_msg
            )
        )
        self.context.outbox.put_message(message=fipa_msg)

    def _on_decline(self, decline: FipaMessage, fipa_dialogue: FipaDialogue) -> None:
        """
        Handle a Decline.

        :param decline: the Decline message
        :param fipa_dialogue: the fipa_dialogue
        """
        fipa_dialogues = cast(FipaDialogues, self.context.fipa_dialogues)

        target_message = fipa_dialogue.get_message_by_id(decline.target)

        if not target_message:
            raise ValueError("Can not find target message!")  # pragma: nocover

        declined_performative = target_message.performative
        if declined_performative == FipaMessage.Performative.CFP:
            fipa_dialogues.dialogue_stats.add_dialogue_endstate(
                FipaDialogue.EndState.DECLINED_CFP, fipa_dialogue.is_self_initiated
            )
        if declined_performative == FipaMessage.Performative.PROPOSE:
            fipa_dialogues.dialogue_stats.add_dialogue_endstate(
                FipaDialogue.EndState.DECLINED_PROPOSE, fipa_dialogue.is_self_initiated
            )
            transactions = cast(Transactions, self.context.transactions)
            terms = transactions.pop_pending_proposal(
                fipa_dialogue.dialogue_label, decline.target
            )
        if declined_performative == FipaMessage.Performative.ACCEPT:
            fipa_dialogues.dialogue_stats.add_dialogue_endstate(
                FipaDialogue.EndState.DECLINED_ACCEPT, fipa_dialogue.is_self_initiated
            )
            transactions = cast(Transactions, self.context.transactions)
            terms = transactions.pop_pending_initial_acceptance(
                fipa_dialogue.dialogue_label, decline.target
            )
            transactions.pop_locked_tx(terms)

    def _on_accept(self, accept: FipaMessage, fipa_dialogue: FipaDialogue) -> None:
        """
        Handle an Accept.

        :param accept: the Accept message
        :param fipa_dialogue: the fipa_dialogue
        """
        transactions = cast(Transactions, self.context.transactions)
        terms = transactions.pop_pending_proposal(
            fipa_dialogue.dialogue_label, accept.target
        )
        strategy = cast(Strategy, self.context.strategy)
        if strategy.is_profitable_transaction(
            terms, role=cast(FipaDialogue.Role, fipa_dialogue.role)
        ):
            transactions.add_locked_tx(
                terms, role=cast(FipaDialogue.Role, fipa_dialogue.role)
            )
            if strategy.is_contract_tx:
                if strategy.ledger_id == EthereumApi.identifier:
                    contract_api_dialogues = cast(
                        ContractApiDialogues, self.context.contract_api_dialogues
                    )
                    (
                        contract_api_msg,
                        contract_api_dialogue,
                    ) = contract_api_dialogues.create(
                        counterparty=LEDGER_API_ADDRESS,
                        performative=ContractApiMessage.Performative.GET_RAW_MESSAGE,
                        ledger_id=strategy.ledger_id,
                        contract_id=strategy.contract_id,
                        contract_address=strategy.contract_address,
                        callable="get_hash_batch",
                        kwargs=ContractApiMessage.Kwargs(
                            strategy.kwargs_from_terms(
                                fipa_dialogue.terms, is_from_terms_sender=False
                            )
                        ),
                    )
                    contract_api_dialogue = cast(
                        ContractApiDialogue, contract_api_dialogue
                    )
                    contract_api_dialogue.associated_fipa_dialogue = fipa_dialogue
                    self.context.logger.info(
                        "requesting batch transaction hash, sending {} to {}, message={}".format(
                            contract_api_msg.performative,
                            strategy.contract_id,
                            contract_api_msg,
                        )
                    )
                    self.context.outbox.put_message(message=contract_api_msg)
                elif strategy.ledger_id == FetchAIApi.identifier:
                    public_key = self.context.public_keys.get(strategy.ledger_id, None)
                    if public_key is None:
                        self.context.logger.info(
                            f"Agent has no public key for {strategy.ledger_id}."
                        )
                        return
                    fipa_msg = fipa_dialogue.reply(
                        performative=FipaMessage.Performative.MATCH_ACCEPT_W_INFORM,
                        info={"public_key": public_key},
                    )
                    self.context.outbox.put_message(message=fipa_msg)
                    self.context.logger.info(
                        "sending {} to {} (as {}), message={}.".format(
                            fipa_msg.performative.value,
                            fipa_msg.to[-5:],
                            fipa_dialogue.role,
                            fipa_msg,
                        )
                    )
                else:
                    enforce(False, f"Unidentified ledger id: {strategy.ledger_id}")
            else:
                signing_dialogues = cast(
                    SigningDialogues, self.context.signing_dialogues
                )
                raw_message = RawMessage(
                    ledger_id=terms.ledger_id, body=terms.sender_hash.encode("utf-8")
                )
                signing_msg, signing_dialogue = signing_dialogues.create(
                    counterparty=self.context.decision_maker_address,
                    performative=SigningMessage.Performative.SIGN_MESSAGE,
                    terms=terms,
                    raw_message=raw_message,
                )
                signing_dialogue = cast(SigningDialogue, signing_dialogue)
                signing_dialogue.associated_fipa_dialogue = fipa_dialogue
                self.context.logger.info(
                    "requesting signature, sending {} to decision_maker, message={}".format(
                        signing_msg.performative, signing_msg,
                    )
                )
                self.context.decision_maker_message_queue.put(signing_msg)
        else:
            fipa_msg = fipa_dialogue.reply(
                performative=FipaMessage.Performative.DECLINE, target_message=accept,
            )
            dialogues = cast(FipaDialogues, self.context.fipa_dialogues)
            dialogues.dialogue_stats.add_dialogue_endstate(
                FipaDialogue.EndState.DECLINED_ACCEPT, fipa_dialogue.is_self_initiated
            )
            self.context.logger.info(
                "sending {} to {} (as {}), message={}".format(
                    fipa_msg.performative,
                    fipa_msg.to[-5:],
                    fipa_dialogue.role,
                    fipa_msg,
                )
            )
            self.context.outbox.put_message(message=fipa_msg)

    def _on_match_accept(
        self, match_accept: FipaMessage, fipa_dialogue: FipaDialogue
    ) -> None:
        """
        Handle a matching Accept.

        :param match_accept: the MatchAccept message
        :param fipa_dialogue: the fipa_dialogue
        """
        strategy = cast(Strategy, self.context.strategy)
        if strategy.is_contract_tx:
            if strategy.ledger_id == FetchAIApi.identifier:
                counterparty_public_key = match_accept.info.get("public_key", None)
                if counterparty_public_key is None:
                    self.context.logger.info(
                        f"{match_accept.performative} did not contain counterparty public_key!"
                    )
                    return
                sender_public_key = self.context.public_keys.get(
                    strategy.ledger_id, None
                )
                if sender_public_key is None:
                    self.context.logger.info(
                        f"Agent has no public key for {strategy.ledger_id}."
                    )
                    return
                contract_api_dialogues = cast(
                    ContractApiDialogues, self.context.contract_api_dialogues
                )
                contract_api_msg, contract_api_dialogue = contract_api_dialogues.create(
                    counterparty=LEDGER_API_ADDRESS,
                    performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,
                    ledger_id=strategy.ledger_id,
                    contract_id=strategy.contract_id,
                    contract_address=strategy.contract_address,
                    callable="get_atomic_swap_batch_transaction",
                    kwargs=ContractApiMessage.Kwargs(
                        strategy.kwargs_from_terms(
                            fipa_dialogue.terms,
                            sender_public_key=sender_public_key,
                            counterparty_public_key=counterparty_public_key,
                        )
                    ),
                )
                contract_api_dialogue = cast(ContractApiDialogue, contract_api_dialogue)
                contract_api_dialogue.associated_fipa_dialogue = fipa_dialogue
                self.context.logger.info(
                    "requesting batch atomic swap transaction, sending {} to {}, message={}".format(
                        contract_api_msg.performative,
                        strategy.contract_id,
                        contract_api_msg,
                    )
                )
                self.context.outbox.put_message(message=contract_api_msg)
            elif strategy.ledger_id == EthereumApi.identifier:
                counterparty_signature = match_accept.info.get("signature")
                if counterparty_signature is None:
                    self.context.logger.info(
                        f"{match_accept.performative} did not contain counterparty signature!"
                    )
                    return
                fipa_dialogue.counterparty_signature = counterparty_signature
                contract_api_dialogues = cast(
                    ContractApiDialogues, self.context.contract_api_dialogues
                )
                contract_api_msg, contract_api_dialogue = contract_api_dialogues.create(
                    counterparty=LEDGER_API_ADDRESS,
                    performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,
                    ledger_id=strategy.ledger_id,
                    contract_id=strategy.contract_id,
                    contract_address=strategy.contract_address,
                    callable="get_atomic_swap_batch_transaction",
                    kwargs=ContractApiMessage.Kwargs(
                        strategy.kwargs_from_terms(
                            fipa_dialogue.terms, signature=counterparty_signature,
                        )
                    ),
                )
                contract_api_dialogue = cast(ContractApiDialogue, contract_api_dialogue)
                contract_api_dialogue.associated_fipa_dialogue = fipa_dialogue
                self.context.logger.info(
                    "requesting batch atomic swap transaction, sending {} to {}, message={}".format(
                        contract_api_msg.performative,
                        strategy.contract_id,
                        contract_api_msg,
                    )
                )
                self.context.outbox.put_message(message=contract_api_msg)
            else:
                enforce(False, f"Unidentified ledger id: {strategy.ledger_id}")
        else:
            counterparty_signature = match_accept.info.get("signature")
            if counterparty_signature is None:
                self.context.logger.info(
                    f"{match_accept.performative} did not contain counterparty signature!"
                )
                return
            fipa_dialogue.counterparty_signature = counterparty_signature
            transactions = cast(Transactions, self.context.transactions)
            terms = transactions.pop_pending_initial_acceptance(
                fipa_dialogue.dialogue_label, match_accept.target
            )
            signing_dialogues = cast(SigningDialogues, self.context.signing_dialogues)
            raw_message = RawMessage(
                ledger_id=terms.ledger_id, body=terms.sender_hash.encode("utf-8")
            )
            signing_msg, signing_dialogue = signing_dialogues.create(
                counterparty=self.context.decision_maker_address,
                performative=SigningMessage.Performative.SIGN_MESSAGE,
                terms=terms,
                raw_message=raw_message,
            )
            signing_dialogue = cast(SigningDialogue, signing_dialogue)
            signing_dialogue.associated_fipa_dialogue = fipa_dialogue
            self.context.logger.info(
                "requesting signature, sending {} to decision_maker, message={}".format(
                    signing_msg.performative, signing_msg,
                )
            )
            self.context.decision_maker_message_queue.put(signing_msg)


class CosmTradeHandler(Handler):
    """This class implements the cosm_trade negotiation handler."""

    SUPPORTED_PROTOCOL = CosmTradeMessage.protocol_id  # type: Optional[PublicId]

    def setup(self) -> None:
        """Implement the setup."""

    def handle(self, message: Message) -> None:
        """
        Dispatch message to relevant handler and respond.

        :param message: the message
        """
        strategy = cast(Strategy, self.context.strategy)
        enforce(
            strategy.is_contract_tx,
            "A cosm_trade dialogue is only used in the contract-based TAC",
        )
        enforce(
            strategy.ledger_id == FetchAIApi.identifier,
            "A cosm_trade dialogue is only used in the fetchai-based TAC",
        )

        cosm_trade_msg = cast(CosmTradeMessage, message)

        # recover dialogue
        cosm_trade_dialogues = cast(
            CosmTradeDialogues, self.context.cosm_trade_dialogues
        )
        cosm_trade_dialogue = cast(
            CosmTradeDialogue, cosm_trade_dialogues.update(cosm_trade_msg)
        )
        if cosm_trade_dialogue is None:
            self._handle_unidentified_dialogue(cosm_trade_msg)
            return

        self.context.logger.info(
            "received {} from {} (as {}), message={}".format(
                cosm_trade_msg.performative.value,
                cosm_trade_msg.sender[-5:],
                cosm_trade_dialogue.role,
                cosm_trade_msg,
            )
        )
        if (
            cosm_trade_msg.performative
            == CosmTradeMessage.Performative.INFORM_SIGNED_TRANSACTION
        ):
            self._on_signed_tx(cosm_trade_msg, cosm_trade_dialogue)
        elif cosm_trade_msg.performative == CosmTradeMessage.Performative.ERROR:
            self._on_error(cosm_trade_msg, cosm_trade_dialogue)
        elif cosm_trade_msg.performative == CosmTradeMessage.Performative.END:
            self._on_end(cosm_trade_msg, cosm_trade_dialogue)

    def teardown(self) -> None:
        """Implement the handler teardown."""

    def _handle_unidentified_dialogue(self, cosm_trade_msg: CosmTradeMessage) -> None:
        """
        Handle an unidentified dialogue.

        Respond to the sender with a default message containing the appropriate error information.

        :param cosm_trade_msg: the message
        """
        self.context.logger.info(
            "received invalid cosm_trade message={}, unidentified dialogue.".format(
                cosm_trade_msg
            )
        )
        default_dialogues = cast(DefaultDialogues, self.context.default_dialogues)
        default_msg, _ = default_dialogues.create(
            counterparty=cosm_trade_msg.sender,
            performative=DefaultMessage.Performative.ERROR,
            error_code=DefaultMessage.ErrorCode.INVALID_DIALOGUE,
            error_msg="Invalid dialogue.",
            error_data={"cosm_trade_message": cosm_trade_msg.encode()},
        )
        self.context.outbox.put_message(message=default_msg)

    def _on_signed_tx(
        self, inform_signed_tx: CosmTradeMessage, cosm_trade_dialogue: CosmTradeDialogue
    ) -> None:
        """
        Handle a Propose.

        :param inform_signed_tx: the message containing the signed transaction
        :param cosm_trade_dialogue: the cosm_trade_dialogue
        """
        tx_signed_by_the_other_party = inform_signed_tx.signed_transaction
        self.context.logger.info(
            "received inform_signed_tx with signed_tx={}".format(
                tx_signed_by_the_other_party
            )
        )

        fipa_dialogue_ref = inform_signed_tx.fipa_dialogue_id
        if fipa_dialogue_ref is None:
            self.context.logger.info(
                "inform_signed_tx must contain fipa dialogue reference."
            )
            return

        fipa_dialogues = cast(FipaDialogues, self.context.fipa_dialogues)
        dialogue_label = DialogueLabel(
            cast(Tuple[str, str], fipa_dialogue_ref),
            inform_signed_tx.sender,
            inform_signed_tx.sender,
        )
        fipa_dialogue = cast(
            FipaDialogue, fipa_dialogues.get_dialogue_from_label(dialogue_label)
        )

        signing_dialogues = cast(SigningDialogues, self.context.signing_dialogues)
        signing_msg, signing_dialogue = signing_dialogues.create(
            counterparty=self.context.decision_maker_address,
            performative=SigningMessage.Performative.SIGN_TRANSACTION,
            raw_transaction=RawTransaction(
                ledger_id=tx_signed_by_the_other_party.ledger_id,
                body=tx_signed_by_the_other_party.body,
            ),
            terms=fipa_dialogue.terms,
        )
        signing_dialogue = cast(SigningDialogue, signing_dialogue)
        signing_dialogue.associated_fipa_dialogue = fipa_dialogue
        signing_dialogue.associated_cosm_trade_dialogue = cosm_trade_dialogue
        self.context.decision_maker_message_queue.put_nowait(signing_msg)
        self.context.logger.info(
            "proposing the transaction to the decision maker. Waiting for confirmation ..."
        )

    def _on_error(
        self, error_msg: CosmTradeMessage, cosm_trade_dialogue: CosmTradeDialogue
    ) -> None:
        """
        Handle an Error.

        :param error_msg: the Error message
        :param cosm_trade_dialogue: the cosm_trade_dialogue
        """
        self.context.logger.info(
            "received cosm_trade_api error message={} in dialogue={}.".format(
                error_msg, cosm_trade_dialogue
            )
        )
        cosm_trade_dialogues = cast(
            CosmTradeDialogues, self.context.cosm_trade_dialogues
        )
        cosm_trade_dialogues.dialogue_stats.add_dialogue_endstate(
            CosmTradeDialogue.EndState.FAILED, cosm_trade_dialogue.is_self_initiated
        )

    def _on_end(
        self, end_msg: CosmTradeMessage, cosm_trade_dialogue: CosmTradeDialogue
    ) -> None:
        """
        Handle an End.

        :param end_msg: the Accept message
        :param cosm_trade_dialogue: the fipa_dialogue
        """
        self.context.logger.info(
            "received cosm_trade_api end message={} in dialogue={}.".format(
                end_msg, cosm_trade_dialogue
            )
        )
        cosm_trade_dialogues = cast(
            CosmTradeDialogues, self.context.cosm_trade_dialogues
        )
        cosm_trade_dialogues.dialogue_stats.add_dialogue_endstate(
            CosmTradeDialogue.EndState.SUCCESSFUL, cosm_trade_dialogue.is_self_initiated
        )


class SigningHandler(Handler):
    """This class implements the transaction handler."""

    SUPPORTED_PROTOCOL = SigningMessage.protocol_id  # type: Optional[PublicId]

    def setup(self) -> None:
        """Implement the setup."""

    def handle(self, message: Message) -> None:
        """
        Dispatch message to relevant handler and respond.

        :param message: the message
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

        self.context.logger.info(
            "received {} from decision_maker, message={}".format(
                signing_msg.performative.value, signing_msg,
            )
        )
        # handle message
        if signing_msg.performative is SigningMessage.Performative.SIGNED_MESSAGE:
            self._handle_signed_message(signing_msg, signing_dialogue)
        elif signing_msg.performative is SigningMessage.Performative.SIGNED_TRANSACTION:
            self._handle_signed_transaction(signing_msg, signing_dialogue)
        elif signing_msg.performative is SigningMessage.Performative.ERROR:
            self._handle_error(signing_msg, signing_dialogue)
        else:
            self._handle_invalid(signing_msg, signing_dialogue)

    def teardown(self) -> None:
        """Implement the handler teardown."""

    def _handle_unidentified_dialogue(self, signing_msg: SigningMessage) -> None:
        """
        Handle an unidentified dialogue.

        :param signing_msg: the message
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
        """
        fipa_dialogue = signing_dialogue.associated_fipa_dialogue
        last_fipa_message = cast(FipaMessage, fipa_dialogue.last_incoming_message)
        enforce(last_fipa_message is not None, "last message not recovered.")
        if last_fipa_message.performative == FipaMessage.Performative.ACCEPT:
            fipa_msg = fipa_dialogue.reply(
                performative=FipaMessage.Performative.MATCH_ACCEPT_W_INFORM,
                target_message=last_fipa_message,
                info={"signature": signing_msg.signed_message.body},
            )
            self.context.outbox.put_message(message=fipa_msg)
            self.context.logger.info(
                "sending {} to {} (as {}), message={}.".format(
                    fipa_msg.performative.value,
                    fipa_msg.to[-5:],
                    fipa_dialogue.role,
                    fipa_msg,
                )
            )
        elif (
            last_fipa_message.performative
            == FipaMessage.Performative.MATCH_ACCEPT_W_INFORM
        ):
            counterparty_signature = fipa_dialogue.counterparty_signature
            tx_id = fipa_dialogue.terms.sender_hash
            if "transactions" not in self.context.shared_state.keys():
                self.context.shared_state["transactions"] = OrderedDict()
            tx = {
                "terms": fipa_dialogue.terms,
                "sender_signature": signing_msg.signed_message.body,
                "counterparty_signature": counterparty_signature,
            }
            self.context.shared_state["transactions"][tx_id] = tx
            self.context.logger.info(f"sending transaction to controller, tx={tx}.")
        else:
            enforce(
                False, "last message should be of performative accept or match accept."
            )

    def _handle_signed_transaction(  # pylint: disable=unused-argument
        self, signing_msg: SigningMessage, signing_dialogue: SigningDialogue
    ) -> None:
        """
        Handle an oef search message.

        :param signing_msg: the signing message
        :param signing_dialogue: the dialogue
        """
        strategy = cast(Strategy, self.context.strategy)
        if not strategy.is_contract_tx:
            self.context.logger.warning(
                "signed transaction handler only for contract case."
            )
            return

        cosm_trade_dialogue = signing_dialogue.associated_cosm_trade_dialogue
        if cosm_trade_dialogue is not None:
            # tx is now signed by both parties, submit to ledger
            ledger_api_dialogues = cast(
                LedgerApiDialogues, self.context.ledger_api_dialogues
            )
            ledger_api_msg, ledger_api_dialogue = ledger_api_dialogues.create(
                counterparty=LEDGER_API_ADDRESS,
                performative=LedgerApiMessage.Performative.SEND_SIGNED_TRANSACTION,
                signed_transaction=signing_msg.signed_transaction,
            )
            ledger_api_dialogue = cast(LedgerApiDialogue, ledger_api_dialogue)
            ledger_api_dialogue.associated_signing_dialogue = signing_dialogue
            self.context.logger.info(
                "sending {} to ledger {}, message={}".format(
                    ledger_api_msg.performative, strategy.ledger_id, ledger_api_msg,
                )
            )
            self.context.outbox.put_message(message=ledger_api_msg)
            return

        fipa_dialogue = signing_dialogue.associated_fipa_dialogue
        last_fipa_message = cast(FipaMessage, fipa_dialogue.last_incoming_message)
        enforce(last_fipa_message is not None, "last message not recovered.")
        if last_fipa_message.performative == FipaMessage.Performative.ACCEPT:
            fipa_msg = fipa_dialogue.reply(
                performative=FipaMessage.Performative.MATCH_ACCEPT_W_INFORM,
                target_message=last_fipa_message,
                info={"tx_signature": signing_msg.signed_transaction},
            )
            self.context.logger.info(
                "sending {} to {} (as {}), message={}.".format(
                    fipa_msg.performative.value,
                    fipa_msg.to[-5:],
                    fipa_dialogue.role,
                    fipa_msg,
                )
            )
            self.context.outbox.put_message(message=fipa_msg)
        elif (
            last_fipa_message.performative
            == FipaMessage.Performative.MATCH_ACCEPT_W_INFORM
        ):
            if strategy.ledger_id == EthereumApi.identifier:
                ledger_api_dialogues = cast(
                    LedgerApiDialogues, self.context.ledger_api_dialogues
                )
                ledger_api_msg, ledger_api_dialogue = ledger_api_dialogues.create(
                    counterparty=LEDGER_API_ADDRESS,
                    performative=LedgerApiMessage.Performative.SEND_SIGNED_TRANSACTION,
                    signed_transaction=signing_msg.signed_transaction,
                )
                ledger_api_dialogue = cast(LedgerApiDialogue, ledger_api_dialogue)
                ledger_api_dialogue.associated_signing_dialogue = signing_dialogue
                self.context.logger.info(
                    "sending {} to ledger {}, message={}".format(
                        ledger_api_msg.performative, strategy.ledger_id, ledger_api_msg,
                    )
                )
                self.context.outbox.put_message(message=ledger_api_msg)
            elif strategy.ledger_id == FetchAIApi.identifier:
                # send the constructed and signed tx to the other party to sign
                cosm_trade_dialogues = cast(
                    CosmTradeDialogues, self.context.cosm_trade_dialogues
                )
                cosm_trade_msg, _ = cosm_trade_dialogues.create(
                    counterparty=signing_dialogue.associated_fipa_dialogue.dialogue_label.dialogue_opponent_addr,
                    performative=CosmTradeMessage.Performative.INFORM_SIGNED_TRANSACTION,
                    signed_transaction=signing_msg.signed_transaction,
                    fipa_dialogue_id=signing_dialogue.associated_fipa_dialogue.dialogue_label.dialogue_reference,
                )
                self.context.logger.info(
                    "sending {} to {}, message={}.".format(
                        cosm_trade_msg.performative.value,
                        cosm_trade_msg.to[-5:],
                        cosm_trade_msg,
                    )
                )
                self.context.outbox.put_message(message=cosm_trade_msg)
            else:
                enforce(False, f"Unidentified ledger id: {strategy.ledger_id}")
        else:
            enforce(
                False, "last message should be of performative accept or match accept."
            )

    def _handle_error(
        self, signing_msg: SigningMessage, signing_dialogue: SigningDialogue
    ) -> None:
        """
        Handle an oef search message.

        :param signing_msg: the signing message
        :param signing_dialogue: the dialogue
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
        """
        self.context.logger.warning(
            "cannot handle signing message of performative={} in dialogue={}.".format(
                signing_msg.performative, signing_dialogue
            )
        )


class LedgerApiHandler(Handler):
    """Implement the ledger api handler."""

    SUPPORTED_PROTOCOL = LedgerApiMessage.protocol_id  # type: Optional[PublicId]

    def setup(self) -> None:
        """Implement the setup for the handler."""

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        """
        ledger_api_msg = cast(LedgerApiMessage, message)

        # recover dialogue
        ledger_api_dialogues = cast(
            LedgerApiDialogues, self.context.ledger_api_dialogues
        )
        ledger_api_dialogue = cast(
            Optional[LedgerApiDialogue], ledger_api_dialogues.update(ledger_api_msg)
        )
        if ledger_api_dialogue is None:
            self._handle_unidentified_dialogue(ledger_api_msg)
            return

        # handle message
        if ledger_api_msg.performative is LedgerApiMessage.Performative.BALANCE:
            self._handle_balance(ledger_api_msg)
        elif (
            ledger_api_msg.performative
            is LedgerApiMessage.Performative.TRANSACTION_DIGEST
        ):
            self._handle_transaction_digest(ledger_api_msg, ledger_api_dialogue)
        elif (
            ledger_api_msg.performative
            is LedgerApiMessage.Performative.TRANSACTION_RECEIPT
        ):
            self._handle_transaction_receipt(ledger_api_msg)
        elif ledger_api_msg.performative == LedgerApiMessage.Performative.ERROR:
            self._handle_error(ledger_api_msg, ledger_api_dialogue)
        else:
            self._handle_invalid(ledger_api_msg, ledger_api_dialogue)

    def teardown(self) -> None:
        """Implement the handler teardown."""

    def _handle_unidentified_dialogue(self, ledger_api_msg: LedgerApiMessage) -> None:
        """
        Handle an unidentified dialogue.

        :param ledger_api_msg: the message
        """
        self.context.logger.info(
            "received invalid ledger_api message={}, unidentified dialogue.".format(
                ledger_api_msg
            )
        )

    def _handle_balance(self, ledger_api_msg: LedgerApiMessage) -> None:
        """
        Handle a message of balance performative.

        :param ledger_api_msg: the ledger api message
        """
        self.context.logger.info(
            "starting balance on {} ledger={}.".format(
                ledger_api_msg.ledger_id, ledger_api_msg.balance,
            )
        )

    def _handle_transaction_digest(
        self, ledger_api_msg: LedgerApiMessage, ledger_api_dialogue: LedgerApiDialogue
    ) -> None:
        """
        Handle a message of transaction_digest performative.

        :param ledger_api_msg: the ledger api message
        :param ledger_api_dialogue: the ledger api dialogue
        """
        self.context.logger.info(
            "transaction was successfully submitted. Transaction digest={}".format(
                ledger_api_msg.transaction_digest
            )
        )
        msg = ledger_api_dialogue.reply(
            performative=LedgerApiMessage.Performative.GET_TRANSACTION_RECEIPT,
            target_message=ledger_api_msg,
            transaction_digest=ledger_api_msg.transaction_digest,
        )
        self.context.outbox.put_message(message=msg)
        self.context.logger.info("requesting transaction receipt.")

    def _handle_transaction_receipt(self, ledger_api_msg: LedgerApiMessage) -> None:
        """
        Handle a message of transaction_receipt performative.

        :param ledger_api_msg: the ledger api message
        """
        is_transaction_successful = LedgerApis.is_transaction_settled(
            ledger_api_msg.transaction_receipt.ledger_id,
            ledger_api_msg.transaction_receipt.receipt,
        )
        if is_transaction_successful:
            self.context.logger.info(
                "transaction was successfully settled. Transaction receipt={}".format(
                    ledger_api_msg.transaction_receipt
                )
            )
        else:
            self.context.logger.error(
                "transaction failed. Transaction receipt={}".format(
                    ledger_api_msg.transaction_receipt
                )
            )

    def _handle_error(
        self, ledger_api_msg: LedgerApiMessage, ledger_api_dialogue: LedgerApiDialogue
    ) -> None:
        """
        Handle a message of error performative.

        :param ledger_api_msg: the ledger api message
        :param ledger_api_dialogue: the ledger api dialogue
        """
        self.context.logger.info(
            "received ledger_api error message={} in dialogue={}.".format(
                ledger_api_msg, ledger_api_dialogue
            )
        )

    def _handle_invalid(
        self, ledger_api_msg: LedgerApiMessage, ledger_api_dialogue: LedgerApiDialogue
    ) -> None:
        """
        Handle a message of invalid performative.

        :param ledger_api_msg: the ledger api message
        :param ledger_api_dialogue: the ledger api dialogue
        """
        self.context.logger.warning(
            "cannot handle ledger_api message of performative={} in dialogue={}.".format(
                ledger_api_msg.performative, ledger_api_dialogue,
            )
        )


class OefSearchHandler(Handler):
    """This class implements the oef search handler."""

    SUPPORTED_PROTOCOL = OefSearchMessage.protocol_id  # type: Optional[PublicId]

    def setup(self) -> None:
        """Implement the setup."""

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
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
        elif oef_search_msg.performative == OefSearchMessage.Performative.SUCCESS:
            self._handle_success(oef_search_msg, oef_search_dialogue)
        elif oef_search_msg.performative == OefSearchMessage.Performative.OEF_ERROR:
            self._on_oef_error(oef_search_msg, oef_search_dialogue)
        else:
            self._handle_invalid(oef_search_msg, oef_search_dialogue)

    def teardown(self) -> None:
        """Implement the handler teardown."""

    def _handle_unidentified_dialogue(self, oef_search_msg: OefSearchMessage) -> None:
        """
        Handle an unidentified dialogue.

        :param oef_search_msg: the message
        """
        self.context.logger.warning(
            "received invalid oef_search message={}, unidentified dialogue.".format(
                oef_search_msg
            )
        )

    def _handle_success(
        self,
        oef_search_success_msg: OefSearchMessage,
        oef_search_dialogue: OefSearchDialogue,
    ) -> None:
        """
        Handle an oef search message.

        :param oef_search_success_msg: the oef search message
        :param oef_search_dialogue: the dialogue
        """
        self.context.logger.info(
            "received oef_search success message={} in dialogue={}.".format(
                oef_search_success_msg, oef_search_dialogue
            )
        )
        target_message = cast(
            OefSearchMessage,
            oef_search_dialogue.get_message_by_id(oef_search_success_msg.target),
        )
        if (
            target_message.performative
            == OefSearchMessage.Performative.REGISTER_SERVICE
        ):
            description = target_message.service_description
            data_model_name = description.data_model.name
            registration_behaviour = cast(
                GoodsRegisterAndSearchBehaviour,
                self.context.behaviours.tac_negotiation,
            )
            if "location_agent" in data_model_name:
                registration_behaviour.register_service()
            elif "set_service_key" in data_model_name:
                registration_behaviour.register_genus()
            elif (
                "personality_agent" in data_model_name
                and description.values["piece"] == "genus"
            ):
                registration_behaviour.register_classification()
            elif (
                "personality_agent" in data_model_name
                and description.values["piece"] == "classification"
            ):
                registration_behaviour.is_registered = True
                self.context.logger.info(
                    "the agent, with its genus and classification, and its service are successfully registered on the SOEF."
                )
            else:
                self.context.logger.warning(
                    f"received soef SUCCESS message as a reply to the following unexpected message: {target_message}"
                )

    def _on_oef_error(
        self,
        oef_search_error_msg: OefSearchMessage,
        oef_search_dialogue: OefSearchDialogue,
    ) -> None:
        """
        Handle an OEF error message.

        :param oef_search_error_msg: the oef search msg
        :param oef_search_dialogue: the dialogue
        """
        self.context.logger.warning(
            "received OEF Search error: dialogue_reference={}, oef_error_operation={}".format(
                oef_search_dialogue.dialogue_label.dialogue_reference,
                oef_search_error_msg.oef_error_operation,
            )
        )
        target_message = cast(
            OefSearchMessage,
            oef_search_dialogue.get_message_by_id(oef_search_error_msg.target),
        )
        if (
            target_message.performative
            == OefSearchMessage.Performative.REGISTER_SERVICE
        ):
            registration_behaviour = cast(
                GoodsRegisterAndSearchBehaviour,
                self.context.behaviours.tac_negotiation,
            )
            registration_behaviour.failed_registration_msg = target_message

    def _on_search_result(
        self, oef_search_msg: OefSearchMessage, oef_search_dialogue: OefSearchDialogue
    ) -> None:
        """
        Split the search results from the OEF search node.

        :param oef_search_msg: the search result
        :param oef_search_dialogue: the dialogue
        """
        agents = list(oef_search_msg.agents)
        search_id = oef_search_msg.dialogue_reference[0]
        if self.context.agent_address in agents:
            agents.remove(self.context.agent_address)
        agents_less_self = tuple(agents)
        self._handle_search(
            agents_less_self,
            search_id,
            is_searching_for_sellers=oef_search_dialogue.is_seller_search,
        )

    def _handle_search(
        self, agents: Tuple[str, ...], search_id: str, is_searching_for_sellers: bool
    ) -> None:
        """
        Handle the search response.

        :param agents: the agents returned by the search
        :param search_id: the search id
        :param is_searching_for_sellers: whether the agent is searching for sellers
        """
        searched_for = "sellers" if is_searching_for_sellers else "buyers"
        if len(agents) > 0:
            self.context.logger.info(
                "found potential {} agents={} on search_id={}.".format(
                    searched_for, list(map(lambda x: x[-5:], agents)), search_id,
                )
            )
            strategy = cast(Strategy, self.context.strategy)
            fipa_dialogues = cast(FipaDialogues, self.context.fipa_dialogues)
            query = strategy.get_own_services_query(is_searching_for_sellers)

            for opponent_addr in agents:
                self.context.logger.info(
                    "sending CFP to agent={}".format(opponent_addr[-5:])
                )
                fipa_msg, _ = fipa_dialogues.create(
                    counterparty=opponent_addr,
                    performative=FipaMessage.Performative.CFP,
                    query=query,
                )
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
        """
        self.context.logger.warning(
            "cannot handle oef_search message of performative={} in dialogue={}.".format(
                oef_search_msg.performative, oef_search_dialogue,
            )
        )


class ContractApiHandler(Handler):
    """Implement the contract api handler."""

    SUPPORTED_PROTOCOL = ContractApiMessage.protocol_id  # type: Optional[PublicId]

    def setup(self) -> None:
        """Implement the setup for the handler."""

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        """
        contract_api_msg = cast(ContractApiMessage, message)

        # recover dialogue
        contract_api_dialogues = cast(
            ContractApiDialogues, self.context.contract_api_dialogues
        )
        contract_api_dialogue = cast(
            Optional[ContractApiDialogue],
            contract_api_dialogues.update(contract_api_msg),
        )
        if contract_api_dialogue is None:
            self._handle_unidentified_dialogue(contract_api_msg)
            return

        # handle message
        if contract_api_msg.performative is ContractApiMessage.Performative.RAW_MESSAGE:
            self._handle_raw_message(contract_api_msg, contract_api_dialogue)
        elif (
            contract_api_msg.performative
            is ContractApiMessage.Performative.RAW_TRANSACTION
        ):
            self._handle_raw_transaction(contract_api_msg, contract_api_dialogue)
        elif contract_api_msg.performative == ContractApiMessage.Performative.ERROR:
            self._handle_error(contract_api_msg, contract_api_dialogue)
        else:
            self._handle_invalid(contract_api_msg, contract_api_dialogue)

    def teardown(self) -> None:
        """Implement the handler teardown."""

    def _handle_unidentified_dialogue(
        self, contract_api_msg: ContractApiMessage
    ) -> None:
        """
        Handle an unidentified dialogue.

        :param contract_api_msg: the message
        """
        self.context.logger.info(
            "received invalid contract_api message={}, unidentified dialogue.".format(
                contract_api_msg
            )
        )

    def _handle_raw_message(
        self,
        contract_api_msg: ContractApiMessage,
        contract_api_dialogue: ContractApiDialogue,
    ) -> None:
        """
        Handle a message of raw_message performative.

        :param contract_api_msg: the ledger api message
        :param contract_api_dialogue: the ledger api dialogue
        """
        self.context.logger.info("received raw message={}".format(contract_api_msg))
        signing_dialogues = cast(SigningDialogues, self.context.signing_dialogues)
        signing_msg, signing_dialogue = signing_dialogues.create(
            counterparty=self.context.decision_maker_address,
            performative=SigningMessage.Performative.SIGN_MESSAGE,
            raw_message=RawMessage(
                contract_api_msg.raw_message.ledger_id,
                contract_api_msg.raw_message.body,
                is_deprecated_mode=True,
            ),
            terms=contract_api_dialogue.associated_fipa_dialogue.terms,
        )
        signing_dialogue = cast(SigningDialogue, signing_dialogue)
        signing_dialogue.associated_fipa_dialogue = (
            contract_api_dialogue.associated_fipa_dialogue
        )
        self.context.decision_maker_message_queue.put_nowait(signing_msg)
        self.context.logger.info(
            "proposing the message to the decision maker. Waiting for confirmation ..."
        )

    def _handle_raw_transaction(
        self,
        contract_api_msg: ContractApiMessage,
        contract_api_dialogue: ContractApiDialogue,
    ) -> None:
        """
        Handle a message of raw_transaction performative.

        :param contract_api_msg: the ledger api message
        :param contract_api_dialogue: the ledger api dialogue
        """
        self.context.logger.info("received raw transaction={}".format(contract_api_msg))
        signing_dialogues = cast(SigningDialogues, self.context.signing_dialogues)
        signing_msg, signing_dialogue = signing_dialogues.create(
            counterparty=self.context.decision_maker_address,
            performative=SigningMessage.Performative.SIGN_TRANSACTION,
            raw_transaction=contract_api_msg.raw_transaction,
            terms=contract_api_dialogue.associated_fipa_dialogue.terms,
        )
        signing_dialogue = cast(SigningDialogue, signing_dialogue)
        signing_dialogue.associated_fipa_dialogue = (
            contract_api_dialogue.associated_fipa_dialogue
        )
        self.context.decision_maker_message_queue.put_nowait(signing_msg)
        self.context.logger.info(
            "proposing the transaction to the decision maker. Waiting for confirmation ..."
        )

    def _handle_error(
        self,
        contract_api_msg: ContractApiMessage,
        contract_api_dialogue: ContractApiDialogue,
    ) -> None:
        """
        Handle a message of error performative.

        :param contract_api_msg: the ledger api message
        :param contract_api_dialogue: the ledger api dialogue
        """
        self.context.logger.info(
            "received contract_api error message={} in dialogue={}.".format(
                contract_api_msg, contract_api_dialogue
            )
        )

    def _handle_invalid(
        self,
        contract_api_msg: ContractApiMessage,
        contract_api_dialogue: ContractApiDialogue,
    ) -> None:
        """
        Handle a message of invalid performative.

        :param contract_api_msg: the ledger api message
        :param contract_api_dialogue: the ledger api dialogue
        """
        self.context.logger.warning(
            "cannot handle contract_api message of performative={} in dialogue={}.".format(
                contract_api_msg.performative, contract_api_dialogue,
            )
        )
