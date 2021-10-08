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

"""This package contains the handlers."""

from typing import Optional, cast

from aea_ledger_fetchai import FetchAIApi

from aea.common import JSONLike
from aea.configurations.base import PublicId
from aea.crypto.ledger_apis import LedgerApis
from aea.protocols.base import Message
from aea.skills.base import Handler

from packages.fetchai.connections.ledger.base import (
    CONNECTION_ID as LEDGER_CONNECTION_PUBLIC_ID,
)
from packages.fetchai.protocols.signing.message import SigningMessage
from packages.fetchai.skills.tac_control.handlers import (
    OefSearchHandler as BaseOefSearchHandler,
)
from packages.fetchai.skills.tac_control.handlers import TacHandler as BaseTacHandler
from packages.fetchai.skills.tac_control_contract.dialogues import (
    ContractApiDialogue,
    ContractApiDialogues,
    ContractApiMessage,
    LedgerApiDialogue,
    LedgerApiDialogues,
    LedgerApiMessage,
    SigningDialogue,
    SigningDialogues,
)
from packages.fetchai.skills.tac_control_contract.game import Game, Phase
from packages.fetchai.skills.tac_control_contract.parameters import Parameters


LEDGER_API_ADDRESS = str(LEDGER_CONNECTION_PUBLIC_ID)


TacHandler = BaseTacHandler


OefSearchHandler = BaseOefSearchHandler


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
            terms=contract_api_dialogue.terms,
        )
        signing_dialogue = cast(SigningDialogue, signing_dialogue)
        signing_dialogue.associated_contract_api_dialogue = contract_api_dialogue
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


class SigningHandler(Handler):
    """Implement the transaction handler."""

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
            "received invalid signing message={}, unidentified dialogue.".format(
                signing_msg
            )
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

    def _request_init_transaction(
        self, ledger_id: str, deployment_tx_receipt: JSONLike
    ) -> None:
        """
        Send a message to request the initialisation transaction to finalise contract deployment on fetch ledger

        :param ledger_id: the ledger id
        :param deployment_tx_receipt: the transaction receipt
        """
        parameters = cast(Parameters, self.context.parameters)
        contract_api_dialogues = cast(
            ContractApiDialogues, self.context.contract_api_dialogues
        )
        fetchai_api = cast(FetchAIApi, LedgerApis.get_api(ledger_id))
        code_id = fetchai_api.get_code_id(deployment_tx_receipt)  # type: Optional[int]
        if code_id:
            contract_api_msg, dialogue = contract_api_dialogues.create(
                counterparty=LEDGER_API_ADDRESS,
                performative=ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION,
                ledger_id=parameters.ledger_id,
                contract_id=parameters.contract_id,
                callable=ContractApiDialogue.Callable.GET_DEPLOY_TRANSACTION.value,
                kwargs=ContractApiMessage.Kwargs(
                    {
                        "label": "TACERC1155",
                        "init_msg": {},
                        "gas": parameters.gas,
                        "amount": 0,
                        "code_id": code_id,
                        "deployer_address": self.context.agent_address,
                        "tx_fee": 0,
                    }
                ),
            )
            contract_api_dialogue = cast(ContractApiDialogue, dialogue)
            contract_api_dialogue.terms = parameters.get_deploy_terms(
                is_init_transaction=True
            )
            contract_api_dialogue.callable = (
                ContractApiDialogue.Callable.GET_DEPLOY_TRANSACTION
            )
            self.context.outbox.put_message(message=contract_api_msg)
            self.context.logger.info(
                "requesting contract initialisation transaction..."
            )
        else:  # pragma: nocover
            self.context.logger.info("Failed to initialise contract: code_id not found")

    def _handle_transaction_receipt(
        self, ledger_api_msg: LedgerApiMessage, ledger_api_dialogue: LedgerApiDialogue
    ) -> None:
        """
        Handle a message of transaction_receipt performative.

        :param ledger_api_msg: the ledger api message
        :param ledger_api_dialogue: the ledger api dialogue
        """
        ledger_id = ledger_api_msg.transaction_receipt.ledger_id
        tx_receipt = ledger_api_msg.transaction_receipt.receipt

        is_transaction_successful = LedgerApis.is_transaction_settled(
            ledger_id, tx_receipt
        )

        signing_dialogue = ledger_api_dialogue.associated_signing_dialogue
        contract_api_dialogue = signing_dialogue.associated_contract_api_dialogue
        if is_transaction_successful:
            self.context.logger.info(
                "transaction was successfully settled. Transaction receipt={}".format(
                    ledger_api_msg.transaction_receipt
                )
            )
            parameters = cast(Parameters, self.context.parameters)
            game = cast(Game, self.context.game)
            if (
                contract_api_dialogue.callable
                == ContractApiDialogue.Callable.GET_DEPLOY_TRANSACTION
            ):
                transaction_label = contract_api_dialogue.terms.kwargs.get(
                    "label", None
                )
                if game.phase != Phase.CONTRACT_DEPLOYED:
                    if (
                        transaction_label == "store"
                    ):  # deploying contract on fetch ledger
                        self._request_init_transaction(ledger_id, tx_receipt)
                    elif transaction_label in {"deploy", "init"}:
                        contract_address = LedgerApis.get_contract_address(
                            ledger_id, tx_receipt
                        )
                        if contract_address is None:
                            raise ValueError(
                                "No contract address found."
                            )  # pragma: nocover
                        parameters.contract_address = contract_address
                        game.phase = Phase.CONTRACT_DEPLOYED
                        self.context.logger.info("contract deployed.")
                    else:
                        self.context.logger.error(
                            f"Invalid transaction label: {transaction_label}"
                        )  # pragma: nocover
            elif (
                contract_api_dialogue.callable
                == ContractApiDialogue.Callable.GET_CREATE_BATCH_TRANSACTION
            ):
                game.phase = Phase.TOKENS_CREATED
                self.context.logger.info("tokens created.")
            elif (
                contract_api_dialogue.callable
                == ContractApiDialogue.Callable.GET_MINT_BATCH_TRANSACTION
            ):
                self.context.logger.info("tokens minted.")
                parameters.nb_completed_minting += 1
                game.is_allowed_to_mint = True
                if game.registration.nb_agents == parameters.nb_completed_minting:
                    game.phase = Phase.TOKENS_MINTED
                    self.context.logger.info("all tokens minted.")
            else:
                self.context.logger.error("unexpected transaction receipt!")
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
