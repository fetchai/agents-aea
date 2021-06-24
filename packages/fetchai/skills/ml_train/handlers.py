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

"""This module contains the handler for the 'ml_train' skill."""

from typing import Optional, cast

from aea.configurations.base import PublicId
from aea.crypto.ledger_apis import LedgerApis
from aea.protocols.base import Message
from aea.skills.base import Handler

from packages.fetchai.connections.ledger.base import (
    CONNECTION_ID as LEDGER_CONNECTION_PUBLIC_ID,
)
from packages.fetchai.protocols.default.message import DefaultMessage
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.ml_trade.message import MlTradeMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.protocols.signing.message import SigningMessage
from packages.fetchai.skills.ml_train.behaviours import TransactionBehaviour
from packages.fetchai.skills.ml_train.dialogues import (
    DefaultDialogues,
    LedgerApiDialogue,
    LedgerApiDialogues,
    MlTradeDialogue,
    MlTradeDialogues,
    OefSearchDialogue,
    OefSearchDialogues,
    SigningDialogue,
    SigningDialogues,
)
from packages.fetchai.skills.ml_train.strategy import Strategy


DUMMY_DIGEST = "dummy_digest"
LEDGER_API_ADDRESS = str(LEDGER_CONNECTION_PUBLIC_ID)


class MlTradeHandler(Handler):
    """ML trade handler."""

    SUPPORTED_PROTOCOL = MlTradeMessage.protocol_id

    def setup(self) -> None:
        """Set up the handler."""

    def handle(self, message: Message) -> None:
        """
        Handle messages.

        :param message: the message
        """
        ml_trade_msg = cast(MlTradeMessage, message)

        # recover dialogue
        ml_trade_dialogues = cast(MlTradeDialogues, self.context.ml_trade_dialogues)
        ml_trade_dialogue = cast(
            MlTradeDialogue, ml_trade_dialogues.update(ml_trade_msg)
        )
        if ml_trade_dialogue is None:
            self._handle_unidentified_dialogue(ml_trade_msg)
            return

        # handle message
        if ml_trade_msg.performative == MlTradeMessage.Performative.TERMS:
            self._handle_terms(ml_trade_msg, ml_trade_dialogue)
        elif ml_trade_msg.performative == MlTradeMessage.Performative.DATA:
            self._handle_data(ml_trade_msg)
        else:
            self._handle_invalid(ml_trade_msg, ml_trade_dialogue)

    def teardown(self) -> None:
        """Teardown the handler."""

    def _handle_unidentified_dialogue(self, ml_trade_msg: MlTradeMessage) -> None:
        """
        Handle an unidentified dialogue.

        :param ml_trade_msg: the message
        """
        self.context.logger.info(
            "received invalid ml_trade message={}, unidentified dialogue.".format(
                ml_trade_msg
            )
        )
        default_dialogues = cast(DefaultDialogues, self.context.default_dialogues)
        default_msg, _ = default_dialogues.create(
            counterparty=ml_trade_msg.sender,
            performative=DefaultMessage.Performative.ERROR,
            error_code=DefaultMessage.ErrorCode.INVALID_DIALOGUE,
            error_msg="Invalid dialogue.",
            error_data={"ml_trade_message": ml_trade_msg.encode()},
        )
        self.context.outbox.put_message(message=default_msg)

    def _handle_terms(
        self, ml_trade_msg: MlTradeMessage, ml_trade_dialogue: MlTradeDialogue
    ) -> None:
        """
        Handle the terms of the request.

        :param ml_trade_msg: the ml trade message
        :param ml_trade_dialogue: the dialogue object
        """
        proposal_terms = ml_trade_msg.terms
        self.context.logger.info(
            "received terms message from {}: terms={}".format(
                ml_trade_msg.sender[-5:], proposal_terms.values
            )
        )

        strategy = cast(Strategy, self.context.strategy)
        acceptable = strategy.is_acceptable_terms(proposal_terms)
        affordable = strategy.is_affordable_terms(proposal_terms)
        if not (acceptable and affordable):
            self.context.logger.info(
                "rejecting, terms are not acceptable and/or affordable"
            )
            return

        if strategy.is_ledger_tx:
            terms = strategy.terms_from_proposal(proposal_terms)
            ml_trade_dialogue.terms = terms
            tx_behaviour = cast(
                TransactionBehaviour, self.context.behaviours.transaction
            )
            tx_behaviour.waiting.append(ml_trade_dialogue)
        else:
            # accept directly with a dummy transaction digest, no settlement
            ml_accept = ml_trade_dialogue.reply(
                performative=MlTradeMessage.Performative.ACCEPT,
                target_message=ml_trade_msg,
                tx_digest=DUMMY_DIGEST,
                terms=proposal_terms,
            )
            self.context.outbox.put_message(message=ml_accept)
            self.context.logger.info("sending dummy transaction digest ...")

    def _handle_data(self, ml_trade_msg: MlTradeMessage) -> None:
        """
        Handle the data.

        :param ml_trade_msg: the ml trade message
        """
        strategy = cast(Strategy, self.context.strategy)
        terms = ml_trade_msg.terms
        payload = ml_trade_msg.payload
        data = strategy.decode_sample_data(payload)
        if data is None:
            self.context.logger.info(
                "received data message with no data from {}".format(
                    ml_trade_msg.sender[-5:]
                )
            )
        else:
            self.context.logger.info(
                "received data message from {}: data shape={}, terms={}".format(
                    ml_trade_msg.sender[-5:], data[0].shape, terms.values
                )
            )
            strategy.data.append(data)
            strategy.is_searching = True

    def _handle_invalid(
        self, ml_trade_msg: MlTradeMessage, ml_trade_dialogue: MlTradeDialogue
    ) -> None:
        """
        Handle a fipa message of invalid performative.

        :param ml_trade_msg: the message
        :param ml_trade_dialogue: the dialogue object
        """
        self.context.logger.warning(
            "cannot handle ml_trade message of performative={} in dialogue={}.".format(
                ml_trade_msg.performative, ml_trade_dialogue
            )
        )


class OEFSearchHandler(Handler):
    """The OEF search handler."""

    SUPPORTED_PROTOCOL = OefSearchMessage.protocol_id  # type: Optional[PublicId]

    def setup(self) -> None:
        """Call to setup the handler."""

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
        if oef_search_msg.performative is OefSearchMessage.Performative.OEF_ERROR:
            self._handle_error(oef_search_msg, oef_search_dialogue)
        elif oef_search_msg.performative is OefSearchMessage.Performative.SEARCH_RESULT:
            self._handle_search(oef_search_msg, oef_search_dialogue)
        else:
            self._handle_invalid(oef_search_msg, oef_search_dialogue)

    def teardown(self) -> None:
        """Implement the handler teardown."""

    def _handle_unidentified_dialogue(self, oef_search_msg: OefSearchMessage) -> None:
        """
        Handle an unidentified dialogue.

        :param oef_search_msg: the message
        """
        self.context.logger.info(
            "received invalid oef_search message={}, unidentified dialogue.".format(
                oef_search_msg
            )
        )

    def _handle_error(
        self, oef_search_msg: OefSearchMessage, oef_search_dialogue: OefSearchDialogue
    ) -> None:
        """
        Handle an oef search message.

        :param oef_search_msg: the oef search message
        :param oef_search_dialogue: the dialogue
        """
        self.context.logger.info(
            "received oef_search error message={} in dialogue={}.".format(
                oef_search_msg, oef_search_dialogue
            )
        )

    def _handle_search(
        self, oef_search_msg: OefSearchMessage, oef_search_dialogue: OefSearchDialogue
    ) -> None:
        """
        Handle the search response.

        :param oef_search_msg: the oef search message
        :param oef_search_dialogue: the dialogue
        """
        if len(oef_search_msg.agents) == 0:
            self.context.logger.info(
                "found no agents in dialogue={}, continue searching.".format(
                    oef_search_dialogue
                )
            )
            return

        self.context.logger.info(
            "found agents={}, stopping search.".format(
                list(map(lambda x: x[-5:], oef_search_msg.agents)),
            )
        )
        strategy = cast(Strategy, self.context.strategy)
        strategy.is_searching = False
        query = strategy.get_service_query()
        ml_trade_dialogues = cast(MlTradeDialogues, self.context.ml_trade_dialogues)
        for idx, opponent_address in enumerate(oef_search_msg.agents):
            if idx >= strategy.max_negotiations:
                continue
            self.context.logger.info(
                "sending CFT to agent={}".format(opponent_address[-5:])
            )
            cft_msg, _ = ml_trade_dialogues.create(
                counterparty=opponent_address,
                performative=MlTradeMessage.Performative.CFP,
                query=query,
            )
            self.context.outbox.put_message(message=cft_msg)

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


class LedgerApiHandler(Handler):
    """Implement the ledger handler."""

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
            ledger_api_msg.performative is LedgerApiMessage.Performative.RAW_TRANSACTION
        ):
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
        strategy = cast(Strategy, self.context.strategy)
        if ledger_api_msg.balance > 0:
            self.context.logger.info(
                "starting balance on {} ledger={}.".format(
                    strategy.ledger_id, ledger_api_msg.balance,
                )
            )
            strategy.is_searching = True
            strategy.balance = ledger_api_msg.balance
        else:
            self.context.logger.warning(
                "you have no starting balance on {} ledger!".format(strategy.ledger_id)
            )
            self.context.is_active = False

    def _handle_raw_transaction(
        self, ledger_api_msg: LedgerApiMessage, ledger_api_dialogue: LedgerApiDialogue
    ) -> None:
        """
        Handle a message of raw_transaction performative.

        :param ledger_api_msg: the ledger api message
        :param ledger_api_dialogue: the ledger api dialogue
        """
        self.context.logger.info("received raw transaction={}".format(ledger_api_msg))
        signing_dialogues = cast(SigningDialogues, self.context.signing_dialogues)
        last_msg = cast(LedgerApiMessage, ledger_api_dialogue.last_outgoing_message)
        if last_msg is None:
            raise ValueError(  # pragma: nocover
                "Could not retrive last outgoing ledger_api_msg."
            )
        signing_msg, signing_dialogue = signing_dialogues.create(
            counterparty=self.context.decision_maker_address,
            performative=SigningMessage.Performative.SIGN_TRANSACTION,
            raw_transaction=ledger_api_msg.raw_transaction,
            terms=last_msg.terms,
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
        ml_trade_dialogue = ledger_api_dialogue.associated_ml_trade_dialogue
        is_settled = LedgerApis.is_transaction_settled(
            ml_trade_dialogue.terms.ledger_id,
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
            ml_trade_msg = cast(
                Optional[MlTradeMessage], ml_trade_dialogue.last_incoming_message
            )
            if ml_trade_msg is None:
                raise ValueError("Could not retrieve last ml_trade message")
            ml_accept = ml_trade_dialogue.reply(
                performative=MlTradeMessage.Performative.ACCEPT,
                target_message=ml_trade_msg,
                tx_digest=ledger_api_msg_.transaction_digest.body,
                terms=ml_trade_msg.terms,
            )
            self.context.outbox.put_message(message=ml_accept)
            self.context.logger.info(
                "informing counterparty={} of transaction digest={}.".format(
                    ml_trade_msg.sender[-5:], ledger_api_msg_.transaction_digest,
                )
            )
        else:
            tx_behaviour.failed_processing(ledger_api_dialogue)
            self.context.logger.info(
                "transaction_receipt={} not settled or not valid, aborting".format(
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
            "cannot handle ledger_api message of performative={} in dialogue={}.".format(
                ledger_api_msg.performative, ledger_api_dialogue,
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
        ledger_api_dialogue = signing_dialogue.associated_ledger_api_dialogue
        last_ledger_api_msg = cast(
            Optional[LedgerApiMessage], ledger_api_dialogue.last_incoming_message
        )
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
            "transaction signing was not successful. Error_code={} in dialogue={}".format(
                signing_msg.error_code, signing_dialogue
            )
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
            "cannot handle signing message of performative={} in dialogue={}.".format(
                signing_msg.performative, signing_dialogue
            )
        )
