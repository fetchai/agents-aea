# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2020 Fetch.AI Limited
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

"""This package contains the handlers of the erc1155 deploy skill AEA."""

from typing import Optional, cast

from aea.configurations.base import ProtocolId
from aea.crypto.ethereum import EthereumHelper
from aea.protocols.base import Message
from aea.protocols.default.message import DefaultMessage
from aea.protocols.signing.message import SigningMessage
from aea.skills.base import Handler

from packages.fetchai.protocols.contract_api.message import ContractApiMessage
from packages.fetchai.protocols.fipa.message import FipaMessage
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.skills.erc1155_deploy.dialogues import (
    ContractApiDialogue,
    ContractApiDialogues,
    DefaultDialogues,
    FipaDialogue,
    FipaDialogues,
    LedgerApiDialogue,
    LedgerApiDialogues,
    SigningDialogue,
    SigningDialogues,
)
from packages.fetchai.skills.erc1155_deploy.strategy import Strategy


LEDGER_API_ADDRESS = "fetchai/ledger:0.2.0"


class FipaHandler(Handler):
    """This class implements a FIPA handler."""

    SUPPORTED_PROTOCOL = FipaMessage.protocol_id  # type: Optional[ProtocolId]

    def setup(self) -> None:
        """Implement the setup for the handler."""
        pass

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :return: None
        """
        fipa_msg = cast(FipaMessage, message)

        # recover dialogue
        fipa_dialogues = cast(FipaDialogues, self.context.fipa_dialogues)
        fipa_dialogue = cast(FipaDialogue, fipa_dialogues.update(fipa_msg))
        if fipa_dialogue is None:
            self._handle_unidentified_dialogue(fipa_msg)
            return

        if fipa_msg.performative == FipaMessage.Performative.CFP:
            self._handle_cfp(fipa_msg, fipa_dialogue)
        elif fipa_msg.performative == FipaMessage.Performative.ACCEPT_W_INFORM:
            self._handle_accept_w_inform(fipa_msg, fipa_dialogue)
        else:
            self._handle_invalid(fipa_msg, fipa_dialogue)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass

    def _handle_unidentified_dialogue(self, fipa_msg: FipaMessage) -> None:
        """
        Handle an unidentified dialogue.

        Respond to the sender with a default message containing the appropriate error information.

        :param fipa_msg: the message
        :return: None
        """
        self.context.logger.info(
            "[{}]: unidentified dialogue.".format(self.context.agent_name)
        )
        default_dialogues = cast(DefaultDialogues, self.context.default_dialogues)
        default_msg = DefaultMessage(
            performative=DefaultMessage.Performative.ERROR,
            dialogue_reference=default_dialogues.new_self_initiated_dialogue_reference(),
            error_code=DefaultMessage.ErrorCode.INVALID_DIALOGUE,
            error_msg="Invalid dialogue.",
            error_data={"fipa_message": fipa_msg.encode()},
        )
        default_msg.counterparty = fipa_msg.counterparty
        default_dialogues.update(default_msg)
        self.context.outbox.put_message(message=default_msg)

    def _handle_cfp(self, fipa_msg: FipaMessage, fipa_dialogue: FipaDialogue) -> None:
        """
        Handle the CFP.

        If the CFP matches the supplied services then send a PROPOSE, otherwise send a DECLINE.

        :param fipa_msg: the message
        :param fipa_dialogue: the dialogue object
        :return: None
        """
        strategy = cast(Strategy, self.context.strategy)
        self.context.logger.info(
            "[{}]: received CFP from sender={}".format(
                self.context.agent_name, fipa_msg.counterparty[-5:]
            )
        )
        if not strategy.is_tokens_minted:
            self.context.logger.info("Contract items not minted yet. Try again later.")
            return

        # simply send the same proposal, independent of the query
        fipa_dialogue.proposal = strategy.get_proposal()
        proposal_msg = FipaMessage(
            message_id=fipa_msg.message_id + 1,
            dialogue_reference=fipa_dialogue.dialogue_label.dialogue_reference,
            target=fipa_msg.message_id,
            performative=FipaMessage.Performative.PROPOSE,
            proposal=fipa_dialogue.proposal,
        )
        proposal_msg.counterparty = fipa_msg.counterparty
        fipa_dialogue.update(proposal_msg)
        self.context.logger.info(
            "[{}]: Sending PROPOSE to agent={}: proposal={}".format(
                self.context.agent_name,
                fipa_msg.counterparty[-5:],
                fipa_dialogue.proposal.values,
            )
        )
        self.context.outbox.put_message(message=proposal_msg)

    def _handle_accept_w_inform(
        self, fipa_msg: FipaMessage, fipa_dialogue: FipaDialogue
    ) -> None:
        """
        Handle the ACCEPT_W_INFORM.

        If the ACCEPT_W_INFORM message contains the signed transaction, sign it too, otherwise do nothing.

        :param fipa_msg: the message
        :param fipa_dialogue: the dialogue object
        :return: None
        """
        tx_signature = fipa_msg.info.get("tx_signature", None)
        if tx_signature is not None:
            self.context.logger.info(
                "[{}]: received ACCEPT_W_INFORM from sender={}: tx_signature={}".format(
                    self.context.agent_name, fipa_msg.counterparty[-5:], tx_signature
                )
            )
            strategy = cast(Strategy, self.context.strategy)
            contract_api_dialogues = cast(
                ContractApiDialogues, self.context.contract_api_dialogues
            )
            contract_api_msg = ContractApiMessage(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,
                dialogue_reference=contract_api_dialogues.new_self_initiated_dialogue_reference(),
                ledger_id=strategy.ledger_id,
                contract_id="fetchai/erc1155:0.6.0",
                contract_address=strategy.contract_address,
                callable="get_atomic_swap_single_transaction",
                kwargs=ContractApiMessage.Kwargs(
                    {
                        "from_address": self.context.agent_address,
                        "to_address": fipa_msg.counterparty,
                        "token_id": int(fipa_dialogue.proposal.values["token_id"]),
                        "from_supply": int(
                            fipa_dialogue.proposal.values["from_supply"]
                        ),
                        "to_supply": int(fipa_dialogue.proposal.values["to_supply"]),
                        "value": int(fipa_dialogue.proposal.values["value"]),
                        "trade_nonce": int(
                            fipa_dialogue.proposal.values["trade_nonce"]
                        ),
                        "signature": tx_signature,
                    }
                ),
            )
            contract_api_msg.counterparty = LEDGER_API_ADDRESS
            contract_api_dialogue = cast(
                Optional[ContractApiDialogue],
                contract_api_dialogues.update(contract_api_msg),
            )
            assert (
                contract_api_dialogue is not None
            ), "Contract api dialogue not created."
            contract_api_dialogue.terms = strategy.get_single_swap_terms(
                fipa_dialogue.proposal, fipa_msg.counterparty
            )
            self.context.outbox.put_message(message=contract_api_msg)
            self.context.logger.info(
                "[{}]: Requesting single atomic swap transaction...".format(
                    self.context.agent_name
                )
            )
        else:
            self.context.logger.info(
                "[{}]: received ACCEPT_W_INFORM from sender={} with no signature.".format(
                    self.context.agent_name, fipa_msg.counterparty[-5:]
                )
            )

    def _handle_invalid(
        self, fipa_msg: FipaMessage, fipa_dialogue: FipaDialogue
    ) -> None:
        """
        Handle a fipa message of invalid performative.

        :param fipa_msg: the message
        :param fipa_dialogue: the dialogue object
        :return: None
        """
        self.context.logger.warning(
            "[{}]: cannot handle fipa message of performative={} in dialogue={}.".format(
                self.context.agent_name, fipa_msg.performative, fipa_dialogue
            )
        )


class LedgerApiHandler(Handler):
    """Implement the ledger api handler."""

    SUPPORTED_PROTOCOL = LedgerApiMessage.protocol_id  # type: Optional[ProtocolId]

    def setup(self) -> None:
        """Implement the setup for the handler."""
        pass

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :return: None
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
            self._handle_balance(ledger_api_msg, ledger_api_dialogue)
        elif (
            ledger_api_msg.performative
            is LedgerApiMessage.Performative.TRANSACTION_DIGEST
        ):
            self._handle_transaction_digest(ledger_api_msg, ledger_api_dialogue)
        elif (
            ledger_api_msg.performative
            is LedgerApiMessage.Performative.TRANSACTION_RECEIPT
        ):
            self._handle_transaction_receipt(ledger_api_msg, ledger_api_dialogue)
        elif ledger_api_msg.performative == LedgerApiMessage.Performative.ERROR:
            self._handle_error(ledger_api_msg, ledger_api_dialogue)
        else:
            self._handle_invalid(ledger_api_msg, ledger_api_dialogue)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass

    def _handle_unidentified_dialogue(self, ledger_api_msg: LedgerApiMessage) -> None:
        """
        Handle an unidentified dialogue.

        :param msg: the message
        """
        self.context.logger.info(
            "[{}]: received invalid ledger_api message={}, unidentified dialogue.".format(
                self.context.agent_name, ledger_api_msg
            )
        )

    def _handle_balance(
        self, ledger_api_msg: LedgerApiMessage, ledger_api_dialogue: LedgerApiDialogue
    ) -> None:
        """
        Handle a message of balance performative.

        :param ledger_api_message: the ledger api message
        :param ledger_api_dialogue: the ledger api dialogue
        """
        self.context.logger.info(
            "[{}]: starting balance on {} ledger={}.".format(
                self.context.agent_name,
                ledger_api_msg.ledger_id,
                ledger_api_msg.balance,
            )
        )

    def _handle_transaction_digest(
        self, ledger_api_msg: LedgerApiMessage, ledger_api_dialogue: LedgerApiDialogue
    ) -> None:
        """
        Handle a message of transaction_digest performative.

        :param ledger_api_message: the ledger api message
        :param ledger_api_dialogue: the ledger api dialogue
        """
        self.context.logger.info(
            "[{}]: transaction was successfully submitted. Transaction digest={}".format(
                self.context.agent_name, ledger_api_msg.transaction_digest
            )
        )
        msg = LedgerApiMessage(
            performative=LedgerApiMessage.Performative.GET_TRANSACTION_RECEIPT,
            message_id=ledger_api_msg.message_id + 1,
            dialogue_reference=ledger_api_dialogue.dialogue_label.dialogue_reference,
            target=ledger_api_msg.message_id,
            transaction_digest=ledger_api_msg.transaction_digest,
        )
        msg.counterparty = ledger_api_msg.counterparty
        ledger_api_dialogue.update(msg)
        self.context.outbox.put_message(message=msg)
        self.context.logger.info(
            "[{}]: requesting transaction receipt.".format(self.context.agent_name)
        )

    def _handle_transaction_receipt(
        self, ledger_api_msg: LedgerApiMessage, ledger_api_dialogue: LedgerApiDialogue
    ) -> None:
        """
        Handle a message of transaction_receipt performative.

        :param ledger_api_message: the ledger api message
        :param ledger_api_dialogue: the ledger api dialogue
        """
        is_transaction_successful = EthereumHelper.is_transaction_settled(
            ledger_api_msg.transaction_receipt.receipt
        )
        if is_transaction_successful:
            self.context.logger.info(
                "[{}]: transaction was successfully settled. Transaction receipt={}".format(
                    self.context.agent_name, ledger_api_msg.transaction_receipt
                )
            )
            strategy = cast(Strategy, self.context.strategy)
            if not strategy.is_contract_deployed:
                contract_address = ledger_api_msg.transaction_receipt.receipt.get(
                    "contractAddress", None
                )
                strategy.contract_address = contract_address
                strategy.is_contract_deployed = is_transaction_successful
                strategy.is_behaviour_active = is_transaction_successful
            elif not strategy.is_tokens_created:
                strategy.is_tokens_created = is_transaction_successful
                strategy.is_behaviour_active = is_transaction_successful
            elif not strategy.is_tokens_minted:
                strategy.is_tokens_minted = is_transaction_successful
                strategy.is_behaviour_active = is_transaction_successful
            elif strategy.is_tokens_minted:
                self.context.is_active = False
                self.context.logger.info(
                    "[{}]: Demo finished!".format(self.context.agent_name)
                )
            else:
                self.context.logger.error(
                    "[{}]: Unexpected transaction receipt!".format(
                        self.context.agent_name
                    )
                )
        else:
            self.context.logger.error(
                "[{}]: transaction failed. Transaction receipt={}".format(
                    self.context.agent_name, ledger_api_msg.transaction_receipt
                )
            )

    def _handle_error(
        self, ledger_api_msg: LedgerApiMessage, ledger_api_dialogue: LedgerApiDialogue
    ) -> None:
        """
        Handle a message of error performative.

        :param ledger_api_message: the ledger api message
        :param ledger_api_dialogue: the ledger api dialogue
        """
        self.context.logger.info(
            "[{}]: received ledger_api error message={} in dialogue={}.".format(
                self.context.agent_name, ledger_api_msg, ledger_api_dialogue
            )
        )

    def _handle_invalid(
        self, ledger_api_msg: LedgerApiMessage, ledger_api_dialogue: LedgerApiDialogue
    ) -> None:
        """
        Handle a message of invalid performative.

        :param ledger_api_message: the ledger api message
        :param ledger_api_dialogue: the ledger api dialogue
        """
        self.context.logger.warning(
            "[{}]: cannot handle ledger_api message of performative={} in dialogue={}.".format(
                self.context.agent_name,
                ledger_api_msg.performative,
                ledger_api_dialogue,
            )
        )


class ContractApiHandler(Handler):
    """Implement the contract api handler."""

    SUPPORTED_PROTOCOL = ContractApiMessage.protocol_id  # type: Optional[ProtocolId]

    def setup(self) -> None:
        """Implement the setup for the handler."""
        pass

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :return: None
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
        if (
            contract_api_msg.performative
            is ContractApiMessage.Performative.RAW_TRANSACTION
        ):
            self._handle_raw_transaction(contract_api_msg, contract_api_dialogue)
        elif contract_api_msg.performative == ContractApiMessage.Performative.ERROR:
            self._handle_error(contract_api_msg, contract_api_dialogue)
        else:
            self._handle_invalid(contract_api_msg, contract_api_dialogue)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass

    def _handle_unidentified_dialogue(
        self, contract_api_msg: ContractApiMessage
    ) -> None:
        """
        Handle an unidentified dialogue.

        :param msg: the message
        """
        self.context.logger.info(
            "[{}]: received invalid contract_api message={}, unidentified dialogue.".format(
                self.context.agent_name, contract_api_msg
            )
        )

    def _handle_raw_transaction(
        self,
        contract_api_msg: ContractApiMessage,
        contract_api_dialogue: ContractApiDialogue,
    ) -> None:
        """
        Handle a message of raw_transaction performative.

        :param contract_api_message: the ledger api message
        :param contract_api_dialogue: the ledger api dialogue
        """
        self.context.logger.info(
            "[{}]: received raw transaction={}".format(
                self.context.agent_name, contract_api_msg
            )
        )
        signing_dialogues = cast(SigningDialogues, self.context.signing_dialogues)
        signing_msg = SigningMessage(
            performative=SigningMessage.Performative.SIGN_TRANSACTION,
            dialogue_reference=signing_dialogues.new_self_initiated_dialogue_reference(),
            skill_callback_ids=(str(self.context.skill_id),),
            raw_transaction=contract_api_msg.raw_transaction,
            terms=contract_api_dialogue.terms,
            skill_callback_info={},
        )
        signing_msg.counterparty = "decision_maker"
        signing_dialogue = cast(
            Optional[SigningDialogue], signing_dialogues.update(signing_msg)
        )
        assert signing_dialogue is not None, "Error when creating signing dialogue."
        signing_dialogue.associated_contract_api_dialogue = contract_api_dialogue
        self.context.decision_maker_message_queue.put_nowait(signing_msg)
        self.context.logger.info(
            "[{}]: proposing the transaction to the decision maker. Waiting for confirmation ...".format(
                self.context.agent_name
            )
        )

    def _handle_error(
        self,
        contract_api_msg: ContractApiMessage,
        contract_api_dialogue: ContractApiDialogue,
    ) -> None:
        """
        Handle a message of error performative.

        :param contract_api_message: the ledger api message
        :param contract_api_dialogue: the ledger api dialogue
        """
        self.context.logger.info(
            "[{}]: received ledger_api error message={} in dialogue={}.".format(
                self.context.agent_name, contract_api_msg, contract_api_dialogue
            )
        )

    def _handle_invalid(
        self,
        contract_api_msg: ContractApiMessage,
        contract_api_dialogue: ContractApiDialogue,
    ) -> None:
        """
        Handle a message of invalid performative.

        :param contract_api_message: the ledger api message
        :param contract_api_dialogue: the ledger api dialogue
        """
        self.context.logger.warning(
            "[{}]: cannot handle contract_api message of performative={} in dialogue={}.".format(
                self.context.agent_name,
                contract_api_msg.performative,
                contract_api_dialogue,
            )
        )


class SigningHandler(Handler):
    """Implement the transaction handler."""

    SUPPORTED_PROTOCOL = SigningMessage.protocol_id  # type: Optional[ProtocolId]

    def setup(self) -> None:
        """Implement the setup for the handler."""
        pass

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

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
            self._handle_signed_transaction(signing_msg, signing_dialogue)
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
            "[{}]: received invalid signing message={}, unidentified dialogue.".format(
                self.context.agent_name, signing_msg
            )
        )

    def _handle_signed_transaction(
        self, signing_msg: SigningMessage, signing_dialogue: SigningDialogue
    ) -> None:
        """
        Handle an oef search message.

        :param signing_msg: the signing message
        :param signing_dialogue: the dialogue
        :return: None
        """
        self.context.logger.info(
            "[{}]: transaction signing was successful.".format(self.context.agent_name)
        )
        ledger_api_dialogues = cast(
            LedgerApiDialogues, self.context.ledger_api_dialogues
        )
        ledger_api_msg = LedgerApiMessage(
            performative=LedgerApiMessage.Performative.SEND_SIGNED_TRANSACTION,
            dialogue_reference=ledger_api_dialogues.new_self_initiated_dialogue_reference(),
            signed_transaction=signing_msg.signed_transaction,
        )
        ledger_api_msg.counterparty = LEDGER_API_ADDRESS
        ledger_api_dialogue = cast(
            Optional[LedgerApiDialogue], ledger_api_dialogues.update(ledger_api_msg)
        )
        assert ledger_api_dialogue is not None, "Error when creating signing dialogue."
        ledger_api_dialogue.associated_signing_dialogue = signing_dialogue
        self.context.outbox.put_message(message=ledger_api_msg)
        self.context.logger.info(
            "[{}]: sending transaction to ledger.".format(self.context.agent_name)
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
            "[{}]: transaction signing was not successful. Error_code={} in dialogue={}".format(
                self.context.agent_name, signing_msg.error_code, signing_dialogue
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
            "[{}]: cannot handle signing message of performative={} in dialogue={}.".format(
                self.context.agent_name, signing_msg.performative, signing_dialogue
            )
        )
