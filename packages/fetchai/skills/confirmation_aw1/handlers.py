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

from typing import Optional, cast

from aea.configurations.base import PublicId
from aea.crypto.ledger_apis import LedgerApis
from aea.protocols.base import Message
from aea.skills.base import Handler

from packages.fetchai.connections.ledger.base import (
    CONNECTION_ID as LEDGER_CONNECTION_PUBLIC_ID,
)
from packages.fetchai.protocols.contract_api.message import ContractApiMessage
from packages.fetchai.protocols.default.message import DefaultMessage
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.register.message import RegisterMessage
from packages.fetchai.protocols.signing.message import SigningMessage
from packages.fetchai.skills.confirmation_aw1.behaviours import TransactionBehaviour
from packages.fetchai.skills.confirmation_aw1.dialogues import (
    ContractApiDialogue,
    ContractApiDialogues,
    DefaultDialogues,
    LedgerApiDialogue,
    LedgerApiDialogues,
    RegisterDialogue,
    RegisterDialogues,
    SigningDialogue,
    SigningDialogues,
)
from packages.fetchai.skills.confirmation_aw1.strategy import Strategy


LEDGER_API_ADDRESS = str(LEDGER_CONNECTION_PUBLIC_ID)


class AW1RegistrationHandler(Handler):
    """This class handles register messages."""

    SUPPORTED_PROTOCOL = RegisterMessage.protocol_id

    def setup(self) -> None:
        """Implement the setup."""

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to an envelope.

        :param message: the message
        """
        register_msg = cast(RegisterMessage, message)

        # recover dialogue
        register_dialogues = cast(RegisterDialogues, self.context.register_dialogues)
        register_dialogue = cast(
            Optional[RegisterDialogue], register_dialogues.update(register_msg)
        )
        if register_dialogue is None:
            self._handle_unidentified_dialogue(register_msg)
            return

        # handle message
        if register_msg.performative is RegisterMessage.Performative.REGISTER:
            self._handle_register(register_msg, register_dialogue)
        else:
            self._handle_invalid(register_msg, register_dialogue)

    def teardown(self) -> None:
        """Implement the handler teardown."""

    def _handle_unidentified_dialogue(self, register_msg: RegisterMessage) -> None:
        """
        Handle an unidentified dialogue.

        :param register_msg: the register message
        """
        self.context.logger.info(
            f"received invalid register_msg message={register_msg}, unidentified dialogue."
        )

    def _handle_register(
        self, register_msg: RegisterMessage, register_dialogue: RegisterDialogue
    ) -> None:
        """
        Handle an register message.

        :param register_msg: the register message
        :param register_dialogue: the dialogue
        """
        self.context.logger.info(
            f"received register_msg register message={register_msg} in dialogue={register_dialogue}."
        )
        strategy = cast(Strategy, self.context.strategy)
        is_valid, error_code, error_msg = strategy.valid_registration(
            register_msg.info, register_msg.sender
        )
        if is_valid:
            strategy.lock_registration_temporarily(
                register_msg.sender, register_msg.info
            )
            self.context.logger.info(
                f"valid registration={register_msg.info}. Verifying if tokens staked."
            )
            terms = strategy.get_terms(register_msg.sender)
            if not strategy.developer_handle_only:
                contract_api_dialogues = cast(
                    ContractApiDialogues, self.context.contract_api_dialogues
                )
                kwargs = strategy.get_kwargs(register_msg.info)
                contract_api_msg, contract_api_dialogue = contract_api_dialogues.create(
                    counterparty=LEDGER_API_ADDRESS,
                    performative=ContractApiMessage.Performative.GET_STATE,
                    ledger_id=strategy.contract_ledger_id,
                    contract_id=strategy.contract_id,
                    contract_address=strategy.contract_address,
                    callable=strategy.contract_callable,
                    kwargs=ContractApiMessage.Kwargs(kwargs),
                )
                contract_api_dialogue = cast(ContractApiDialogue, contract_api_dialogue)
                contract_api_dialogue.terms = terms
                contract_api_dialogue.associated_register_dialogue = register_dialogue
                self.context.outbox.put_message(contract_api_msg)
            else:
                strategy.finalize_registration(register_msg.sender)
                register_dialogue.terms = terms
                tx_behaviour = cast(
                    TransactionBehaviour, self.context.behaviours.transaction
                )
                tx_behaviour.waiting.append(register_dialogue)
        else:
            self.context.logger.info(
                f"invalid registration={register_msg.info}. Rejecting."
            )
            reply = register_dialogue.reply(
                performative=RegisterMessage.Performative.ERROR,
                error_code=error_code,
                error_msg=error_msg,
                info={},
            )
            self.context.outbox.put_message(reply)

    def _handle_invalid(
        self, register_msg: RegisterMessage, register_dialogue: RegisterDialogue
    ) -> None:
        """
        Handle an register message.

        :param register_msg: the register message
        :param register_dialogue: the dialogue
        """
        self.context.logger.warning(
            f"cannot handle register_msg message of performative={register_msg.performative} in dialogue={register_dialogue}."
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
        if contract_api_msg.performative is ContractApiMessage.Performative.STATE:
            self._handle_state(contract_api_msg, contract_api_dialogue)
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

        :param contract_api_msg: the contract api message
        """
        self.context.logger.info(
            f"received invalid contract_api message={contract_api_msg}, unidentified dialogue."
        )

    def _handle_state(
        self,
        contract_api_msg: ContractApiMessage,
        contract_api_dialogue: ContractApiDialogue,
    ) -> None:
        """
        Handle a message of raw_message performative.

        :param contract_api_msg: the ledger api message
        :param contract_api_dialogue: the ledger api dialogue
        """
        self.context.logger.info(f"received state message={contract_api_msg}")
        register_dialogue = contract_api_dialogue.associated_register_dialogue
        register_msg = cast(
            Optional[RegisterMessage], register_dialogue.last_incoming_message
        )
        if register_msg is None:
            raise ValueError("Could not retrieve fipa message")
        strategy = cast(Strategy, self.context.strategy)
        if strategy.has_staked(contract_api_msg.state.body):
            self.context.logger.info("Has staked! Requesting funds release.")
            strategy.finalize_registration(register_msg.sender)
            register_dialogue.terms = contract_api_dialogue.terms
            tx_behaviour = cast(
                TransactionBehaviour, self.context.behaviours.transaction
            )
            tx_behaviour.waiting.append(register_dialogue)
        else:
            strategy.unlock_registration(register_msg.sender)
            self.context.logger.info(
                f"invalid registration={register_msg.info}. Rejecting."
            )
            reply = register_dialogue.reply(
                performative=RegisterMessage.Performative.ERROR,
                error_code=1,
                error_msg="No funds staked!",
                info={},
            )
            self.context.outbox.put_message(reply)

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
            f"received ledger_api error message={contract_api_msg} in dialogue={contract_api_dialogue}."
        )
        register_dialogue = contract_api_dialogue.associated_register_dialogue
        register_msg = cast(
            Optional[RegisterMessage], register_dialogue.last_incoming_message
        )
        if register_msg is None:
            raise ValueError("Could not retrieve fipa message")
        strategy = cast(Strategy, self.context.strategy)
        strategy.unlock_registration(register_msg.sender)

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
            f"cannot handle contract_api message of performative={contract_api_msg.performative} in dialogue={contract_api_dialogue}."
        )


class LedgerApiHandler(Handler):
    """Implement the ledger handler."""

    SUPPORTED_PROTOCOL = LedgerApiMessage.protocol_id  # type: Optional[PublicId]

    def setup(self) -> None:
        """Implement the setup for the handler."""
        strategy = cast(Strategy, self.context.strategy)
        for registered_aea in strategy.all_registered_aeas:
            self._send_confirmation_details_to_awx_aeas(registered_aea)

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
        if ledger_api_msg.performative is LedgerApiMessage.Performative.RAW_TRANSACTION:
            self._handle_raw_transaction(ledger_api_msg, ledger_api_dialogue)
        elif (
            ledger_api_msg.performative
            == LedgerApiMessage.Performative.TRANSACTION_DIGEST
        ):
            self._handle_transaction_digest(ledger_api_msg, ledger_api_dialogue)
        elif (
            ledger_api_msg.performative
            == LedgerApiMessage.Performative.TRANSACTION_RECEIPT
        ):
            self._handle_transaction_receipt(ledger_api_msg, ledger_api_dialogue)
        elif ledger_api_msg.performative == LedgerApiMessage.Performative.ERROR:
            self._handle_error(ledger_api_msg, ledger_api_dialogue)
        else:
            self._handle_invalid(ledger_api_msg, ledger_api_dialogue)

    def teardown(self) -> None:
        """Implement the handler teardown."""

    def _handle_unidentified_dialogue(self, ledger_api_msg: LedgerApiMessage) -> None:
        """
        Handle an unidentified dialogue.

        :param ledger_api_msg: the ledger api message
        """
        self.context.logger.info(
            f"received invalid ledger_api message={ledger_api_msg}, unidentified dialogue."
        )

    def _handle_raw_transaction(
        self, ledger_api_msg: LedgerApiMessage, ledger_api_dialogue: LedgerApiDialogue
    ) -> None:
        """
        Handle a message of raw_transaction performative.

        :param ledger_api_msg: the ledger api message
        :param ledger_api_dialogue: the ledger api dialogue
        """
        self.context.logger.info(f"received raw transaction={ledger_api_msg}")
        signing_dialogues = cast(SigningDialogues, self.context.signing_dialogues)
        signing_msg, signing_dialogue = signing_dialogues.create(
            counterparty=self.context.decision_maker_address,
            performative=SigningMessage.Performative.SIGN_TRANSACTION,
            raw_transaction=ledger_api_msg.raw_transaction,
            terms=ledger_api_dialogue.associated_register_dialogue.terms,
        )
        signing_dialogue = cast(SigningDialogue, signing_dialogue)
        signing_dialogue.associated_ledger_api_dialogue = ledger_api_dialogue
        self.context.decision_maker_message_queue.put_nowait(signing_msg)
        self.context.logger.info(
            "proposing the transaction to the decision maker. Waiting for confirmation ..."
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
        ledger_api_msg_ = ledger_api_dialogue.reply(
            performative=LedgerApiMessage.Performative.GET_TRANSACTION_RECEIPT,
            target_message=ledger_api_msg,
            transaction_digest=ledger_api_msg.transaction_digest,
        )
        self.context.logger.info("checking transaction is settled.")
        self.context.outbox.put_message(message=ledger_api_msg_)

    def _handle_transaction_receipt(
        self, ledger_api_msg: LedgerApiMessage, ledger_api_dialogue: LedgerApiDialogue
    ) -> None:
        """
        Handle a message of balance performative.

        :param ledger_api_msg: the ledger api message
        :param ledger_api_dialogue: the ledger api dialogue
        """
        register_dialogue = ledger_api_dialogue.associated_register_dialogue
        is_settled = LedgerApis.is_transaction_settled(
            register_dialogue.terms.ledger_id,
            ledger_api_msg.transaction_receipt.receipt,
        )
        tx_behaviour = cast(TransactionBehaviour, self.context.behaviours.transaction)
        if is_settled:
            tx_behaviour.finish_processing(ledger_api_dialogue)
            ledger_api_msg_ = cast(
                Optional[LedgerApiMessage], ledger_api_dialogue.last_outgoing_message
            )
            if ledger_api_msg_ is None:
                raise ValueError(  # pragma: nocover
                    "Could not retrieve last ledger_api message"
                )
            register_msg = cast(
                Optional[RegisterMessage], register_dialogue.last_incoming_message
            )
            if register_msg is None:
                raise ValueError("Could not retrieve last register message")
            response = register_dialogue.reply(
                performative=RegisterMessage.Performative.SUCCESS,
                target_message=register_msg,
                info={"transaction_digest": ledger_api_msg_.transaction_digest.body},
            )
            self.context.outbox.put_message(message=response)
            self.context.logger.info(
                f"informing counterparty={response.to} of registration success."
            )
            self._send_confirmation_details_to_awx_aeas(response.to)
        else:
            tx_behaviour.failed_processing(ledger_api_dialogue)
            self.context.logger.info(
                "transaction_receipt={} not settled or not valid, aborting".format(
                    ledger_api_msg.transaction_receipt
                )
            )

    def _send_confirmation_details_to_awx_aeas(self, confirmed_aea: str) -> None:
        """
        Send a confirmation of registration to aw2 AEAs.

        :param confirmed_aea: the confirmed aea's address
        """
        strategy = cast(Strategy, self.context.strategy)
        if strategy.awx_aeas != []:
            developer_handle = strategy.get_developer_handle(confirmed_aea)
            self.context.logger.info(
                f"informing awx_aeas={strategy.awx_aeas} of registration success of confirmed aea={confirmed_aea} of developer={developer_handle}."
            )
            default_dialogues = cast(DefaultDialogues, self.context.default_dialogues)
            for awx_aea in strategy.awx_aeas:
                msg, _ = default_dialogues.create(
                    counterparty=awx_aea,
                    performative=DefaultMessage.Performative.BYTES,
                    content=f"{confirmed_aea}_{developer_handle}".encode("utf-8"),
                )
                self.context.outbox.put_message(message=msg)

    def _handle_error(
        self, ledger_api_msg: LedgerApiMessage, ledger_api_dialogue: LedgerApiDialogue
    ) -> None:
        """
        Handle a message of error performative.

        :param ledger_api_msg: the ledger api message
        :param ledger_api_dialogue: the ledger api dialogue
        """
        self.context.logger.info(
            f"received ledger_api error message={ledger_api_msg} in dialogue={ledger_api_dialogue}."
        )
        ledger_api_msg_ = cast(
            Optional[LedgerApiMessage], ledger_api_dialogue.last_outgoing_message
        )
        if (
            ledger_api_msg_ is not None
            and ledger_api_msg_.performative
            != LedgerApiMessage.Performative.GET_BALANCE
        ):
            tx_behaviour = cast(
                TransactionBehaviour, self.context.behaviours.transaction
            )
            tx_behaviour.failed_processing(ledger_api_dialogue)

    def _handle_invalid(
        self, ledger_api_msg: LedgerApiMessage, ledger_api_dialogue: LedgerApiDialogue
    ) -> None:
        """
        Handle a message of invalid performative.

        :param ledger_api_msg: the ledger api message
        :param ledger_api_dialogue: the ledger api dialogue
        """
        self.context.logger.warning(
            f"cannot handle ledger_api message of performative={ledger_api_msg.performative} in dialogue={ledger_api_dialogue}."
        )


class SigningHandler(Handler):
    """Implement the signing handler."""

    SUPPORTED_PROTOCOL = SigningMessage.protocol_id  # type: Optional[PublicId]

    def setup(self) -> None:
        """Implement the setup for the handler."""

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

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

        # handle message
        if signing_msg.performative is SigningMessage.Performative.SIGNED_TRANSACTION:
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
            f"received invalid signing message={signing_msg}, unidentified dialogue."
        )

    def _handle_signed_transaction(
        self, signing_msg: SigningMessage, signing_dialogue: SigningDialogue
    ) -> None:
        """
        Handle an oef search message.

        :param signing_msg: the signing message
        :param signing_dialogue: the dialogue
        """
        self.context.logger.info("transaction signing was successful.")
        ledger_api_dialogue = signing_dialogue.associated_ledger_api_dialogue
        last_ledger_api_msg = ledger_api_dialogue.last_incoming_message
        if last_ledger_api_msg is None:
            raise ValueError("Could not retrieve last message in ledger api dialogue")
        ledger_api_msg = ledger_api_dialogue.reply(
            performative=LedgerApiMessage.Performative.SEND_SIGNED_TRANSACTION,
            target_message=last_ledger_api_msg,
            signed_transaction=signing_msg.signed_transaction,
        )
        self.context.outbox.put_message(message=ledger_api_msg)
        self.context.logger.info("sending transaction to ledger.")

    def _handle_error(
        self, signing_msg: SigningMessage, signing_dialogue: SigningDialogue
    ) -> None:
        """
        Handle an oef search message.

        :param signing_msg: the signing message
        :param signing_dialogue: the dialogue
        """
        self.context.logger.info(
            f"transaction signing was not successful. Error_code={signing_msg.error_code} in dialogue={signing_dialogue}"
        )
        signing_msg_ = cast(
            Optional[SigningMessage], signing_dialogue.last_outgoing_message
        )
        if (
            signing_msg_ is not None
            and signing_msg_.performative
            == SigningMessage.Performative.SIGN_TRANSACTION
        ):
            tx_behaviour = cast(
                TransactionBehaviour, self.context.behaviours.transaction
            )
            ledger_api_dialogue = signing_dialogue.associated_ledger_api_dialogue
            tx_behaviour.failed_processing(ledger_api_dialogue)

    def _handle_invalid(
        self, signing_msg: SigningMessage, signing_dialogue: SigningDialogue
    ) -> None:
        """
        Handle an oef search message.

        :param signing_msg: the signing message
        :param signing_dialogue: the dialogue
        """
        self.context.logger.warning(
            f"cannot handle signing message of performative={signing_msg.performative} in dialogue={signing_dialogue}."
        )
