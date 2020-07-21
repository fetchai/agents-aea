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

"""This package contains handlers for the generic buyer skill."""

import pprint
from typing import Optional, cast

from aea.configurations.base import ProtocolId
from aea.protocols.base import Message
from aea.protocols.default.message import DefaultMessage
from aea.protocols.signing.message import SigningMessage
from aea.skills.base import Handler

from packages.fetchai.protocols.fipa.message import FipaMessage
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.generic_buyer.dialogues import (
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
from packages.fetchai.skills.generic_buyer.strategy import GenericStrategy

LEDGER_API_ADDRESS = "fetchai/ledger:0.2.0"


class GenericFipaHandler(Handler):
    """This class implements a FIPA handler."""

    SUPPORTED_PROTOCOL = FipaMessage.protocol_id  # type: Optional[ProtocolId]

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
        fipa_msg = cast(FipaMessage, message)

        # recover dialogue
        fipa_dialogues = cast(FipaDialogues, self.context.fipa_dialogues)
        fipa_dialogue = cast(FipaDialogue, fipa_dialogues.update(fipa_msg))
        if fipa_dialogue is None:
            self._handle_unidentified_dialogue(fipa_msg)
            return

        # handle message
        if fipa_msg.performative == FipaMessage.Performative.PROPOSE:
            self._handle_propose(fipa_msg, fipa_dialogue)
        elif fipa_msg.performative == FipaMessage.Performative.DECLINE:
            self._handle_decline(fipa_msg, fipa_dialogue, fipa_dialogues)
        elif fipa_msg.performative == FipaMessage.Performative.MATCH_ACCEPT_W_INFORM:
            self._handle_match_accept(fipa_msg, fipa_dialogue)
        elif fipa_msg.performative == FipaMessage.Performative.INFORM:
            self._handle_inform(fipa_msg, fipa_dialogue, fipa_dialogues)
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

        :param fipa_msg: the message
        """
        self.context.logger.info(
            "received invalid fipa message={}, unidentified dialogue.".format(fipa_msg)
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

    def _handle_propose(
        self, fipa_msg: FipaMessage, fipa_dialogue: FipaDialogue
    ) -> None:
        """
        Handle the propose.

        :param fipa_msg: the message
        :param fipa_dialogue: the dialogue object
        :return: None
        """
        self.context.logger.info(
            "received proposal={} from sender={}".format(
                fipa_msg.proposal.values, fipa_msg.counterparty[-5:],
            )
        )
        strategy = cast(GenericStrategy, self.context.strategy)
        acceptable = strategy.is_acceptable_proposal(fipa_msg.proposal)
        affordable = strategy.is_affordable_proposal(fipa_msg.proposal)
        if acceptable and affordable:
            self.context.logger.info(
                "accepting the proposal from sender={}".format(
                    fipa_msg.counterparty[-5:]
                )
            )
            terms = strategy.terms_from_proposal(
                fipa_msg.proposal, fipa_msg.counterparty
            )
            fipa_dialogue.terms = terms
            accept_msg = FipaMessage(
                message_id=fipa_msg.message_id + 1,
                dialogue_reference=fipa_dialogue.dialogue_label.dialogue_reference,
                target=fipa_msg.message_id,
                performative=FipaMessage.Performative.ACCEPT,
            )
            accept_msg.counterparty = fipa_msg.counterparty
            fipa_dialogue.update(accept_msg)
            self.context.outbox.put_message(message=accept_msg)
        else:
            self.context.logger.info(
                "declining the proposal from sender={}".format(
                    fipa_msg.counterparty[-5:]
                )
            )
            decline_msg = FipaMessage(
                message_id=fipa_msg.message_id + 1,
                dialogue_reference=fipa_dialogue.dialogue_label.dialogue_reference,
                target=fipa_msg.message_id,
                performative=FipaMessage.Performative.DECLINE,
            )
            decline_msg.counterparty = fipa_msg.counterparty
            fipa_dialogue.update(decline_msg)
            self.context.outbox.put_message(message=decline_msg)

    def _handle_decline(
        self,
        fipa_msg: FipaMessage,
        fipa_dialogue: FipaDialogue,
        fipa_dialogues: FipaDialogues,
    ) -> None:
        """
        Handle the decline.

        :param fipa_msg: the message
        :param fipa_dialogue: the fipa dialogue
        :param fipa_dialogues: the fipa dialogues
        :return: None
        """
        self.context.logger.info(
            "received DECLINE from sender={}".format(fipa_msg.counterparty[-5:])
        )
        if fipa_msg.target == 1:
            fipa_dialogues.dialogue_stats.add_dialogue_endstate(
                FipaDialogue.EndState.DECLINED_CFP, fipa_dialogue.is_self_initiated
            )
        elif fipa_msg.target == 3:
            fipa_dialogues.dialogue_stats.add_dialogue_endstate(
                FipaDialogue.EndState.DECLINED_ACCEPT, fipa_dialogue.is_self_initiated
            )

    def _handle_match_accept(
        self, fipa_msg: FipaMessage, fipa_dialogue: FipaDialogue
    ) -> None:
        """
        Handle the match accept.

        :param fipa_msg: the message
        :param fipa_dialogue: the dialogue object
        :return: None
        """
        self.context.logger.info(
            "received MATCH_ACCEPT_W_INFORM from sender={} with info={}".format(
                fipa_msg.counterparty[-5:], fipa_msg.info
            )
        )
        strategy = cast(GenericStrategy, self.context.strategy)
        if strategy.is_ledger_tx:
            transfer_address = fipa_msg.info.get("address", None)
            if transfer_address is not None and isinstance(transfer_address, str):
                fipa_dialogue.terms.counterparty_address = transfer_address
            ledger_api_dialogues = cast(
                LedgerApiDialogues, self.context.ledger_api_dialogues
            )
            ledger_api_msg = LedgerApiMessage(
                performative=LedgerApiMessage.Performative.GET_RAW_TRANSACTION,
                dialogue_reference=ledger_api_dialogues.new_self_initiated_dialogue_reference(),
                terms=fipa_dialogue.terms,
            )
            ledger_api_msg.counterparty = LEDGER_API_ADDRESS
            ledger_api_dialogue = cast(
                Optional[LedgerApiDialogue], ledger_api_dialogues.update(ledger_api_msg)
            )
            assert (
                ledger_api_dialogue is not None
            ), "Error when creating ledger api dialogue."
            ledger_api_dialogue.associated_fipa_dialogue = fipa_dialogue
            fipa_dialogue.associated_ledger_api_dialogue = ledger_api_dialogue
            self.context.outbox.put_message(message=ledger_api_msg)
            self.context.logger.info(
                "requesting transfer transaction from ledger api..."
            )
        else:
            inform_msg = FipaMessage(
                message_id=fipa_msg.message_id + 1,
                dialogue_reference=fipa_dialogue.dialogue_label.dialogue_reference,
                target=fipa_msg.message_id,
                performative=FipaMessage.Performative.INFORM,
                info={"Done": "Sending payment via bank transfer"},
            )
            inform_msg.counterparty = fipa_msg.counterparty
            fipa_dialogue.update(inform_msg)
            self.context.outbox.put_message(message=inform_msg)
            self.context.logger.info(
                "informing counterparty={} of payment.".format(
                    fipa_msg.counterparty[-5:]
                )
            )

    def _handle_inform(
        self,
        fipa_msg: FipaMessage,
        fipa_dialogue: FipaDialogue,
        fipa_dialogues: FipaDialogues,
    ) -> None:
        """
        Handle the match inform.

        :param fipa_msg: the message
        :param fipa_dialogue: the fipa dialogue
        :param fipa_dialogues: the fipa dialogues
        :return: None
        """
        self.context.logger.info(
            "received INFORM from sender={}".format(fipa_msg.counterparty[-5:])
        )
        if len(fipa_msg.info.keys()) >= 1:
            data = fipa_msg.info
            self.context.logger.info(
                "received the following data={}".format(pprint.pformat(data))
            )
            fipa_dialogues.dialogue_stats.add_dialogue_endstate(
                FipaDialogue.EndState.SUCCESSFUL, fipa_dialogue.is_self_initiated
            )
        else:
            self.context.logger.info(
                "received no data from sender={}".format(fipa_msg.counterparty[-5:])
            )

    def _handle_invalid(
        self, fipa_msg: FipaMessage, fipa_dialogue: FipaDialogue
    ) -> None:
        """
        Handle a fipa message of invalid performative.

        :param fipa_msg: the message
        :param fipa_dialogue: the fipa dialogue
        :return: None
        """
        self.context.logger.warning(
            "cannot handle fipa message of performative={} in dialogue={}.".format(
                fipa_msg.performative, fipa_dialogue
            )
        )


class GenericOefSearchHandler(Handler):
    """This class implements an OEF search handler."""

    SUPPORTED_PROTOCOL = OefSearchMessage.protocol_id  # type: Optional[ProtocolId]

    def setup(self) -> None:
        """Call to setup the handler."""
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
        if oef_search_msg.performative is OefSearchMessage.Performative.OEF_ERROR:
            self._handle_error(oef_search_msg, oef_search_dialogue)
        elif oef_search_msg.performative is OefSearchMessage.Performative.SEARCH_RESULT:
            self._handle_search(oef_search_msg, oef_search_dialogue)
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
        :return: None
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

        :param agents: the agents returned by the search
        :return: None
        """
        if len(oef_search_msg.agents) == 0:
            self.context.logger.info("found no agents, continue searching.")
            return

        self.context.logger.info(
            "found agents={}, stopping search.".format(
                list(map(lambda x: x[-5:], oef_search_msg.agents)),
            )
        )
        strategy = cast(GenericStrategy, self.context.strategy)
        strategy.is_searching = False  # stopping search
        query = strategy.get_service_query()
        fipa_dialogues = cast(FipaDialogues, self.context.fipa_dialogues)
        for idx, counterparty in enumerate(oef_search_msg.agents):
            if idx >= strategy.max_negotiations:
                continue
            cfp_msg = FipaMessage(
                performative=FipaMessage.Performative.CFP,
                dialogue_reference=fipa_dialogues.new_self_initiated_dialogue_reference(),
                query=query,
            )
            cfp_msg.counterparty = counterparty
            fipa_dialogues.update(cfp_msg)
            self.context.outbox.put_message(message=cfp_msg)
            self.context.logger.info(
                "sending CFP to agent={}".format(counterparty[-5:])
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


class GenericSigningHandler(Handler):
    """Implement the signing handler."""

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
        :return: None
        """
        self.context.logger.info("transaction signing was successful.")
        fipa_dialogue = signing_dialogue.associated_fipa_dialogue
        ledger_api_dialogue = fipa_dialogue.associated_ledger_api_dialogue
        last_ledger_api_msg = ledger_api_dialogue.last_incoming_message
        assert (
            last_ledger_api_msg is not None
        ), "Could not retrieve last message in ledger api dialogue"
        ledger_api_msg = LedgerApiMessage(
            performative=LedgerApiMessage.Performative.SEND_SIGNED_TRANSACTION,
            dialogue_reference=ledger_api_dialogue.dialogue_label.dialogue_reference,
            target=last_ledger_api_msg.message_id,
            message_id=last_ledger_api_msg.message_id + 1,
            signed_transaction=signing_msg.signed_transaction,
        )
        ledger_api_msg.counterparty = LEDGER_API_ADDRESS
        ledger_api_dialogue.update(ledger_api_msg)
        self.context.outbox.put_message(message=ledger_api_msg)
        self.context.logger.info("sending transaction to ledger.")

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


class GenericLedgerApiHandler(Handler):
    """Implement the ledger handler."""

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
            ledger_api_msg.performative is LedgerApiMessage.Performative.RAW_TRANSACTION
        ):
            self._handle_raw_transaction(ledger_api_msg, ledger_api_dialogue)
        elif (
            ledger_api_msg.performative
            == LedgerApiMessage.Performative.TRANSACTION_DIGEST
        ):
            self._handle_transaction_digest(ledger_api_msg, ledger_api_dialogue)
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
            "received invalid ledger_api message={}, unidentified dialogue.".format(
                ledger_api_msg
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
        strategy = cast(GenericStrategy, self.context.strategy)
        if ledger_api_msg.balance > 0:
            self.context.logger.info(
                "starting balance on {} ledger={}.".format(
                    strategy.ledger_id, ledger_api_msg.balance,
                )
            )
            strategy.balance = ledger_api_msg.balance
            strategy.is_searching = True
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

        :param ledger_api_message: the ledger api message
        :param ledger_api_dialogue: the ledger api dialogue
        """
        self.context.logger.info("received raw transaction={}".format(ledger_api_msg))
        signing_dialogues = cast(SigningDialogues, self.context.signing_dialogues)
        signing_msg = SigningMessage(
            performative=SigningMessage.Performative.SIGN_TRANSACTION,
            dialogue_reference=signing_dialogues.new_self_initiated_dialogue_reference(),
            skill_callback_ids=(str(self.context.skill_id),),
            raw_transaction=ledger_api_msg.raw_transaction,
            terms=ledger_api_dialogue.associated_fipa_dialogue.terms,
            skill_callback_info={},
        )
        signing_msg.counterparty = "decision_maker"
        signing_dialogue = cast(
            Optional[SigningDialogue], signing_dialogues.update(signing_msg)
        )
        assert signing_dialogue is not None, "Error when creating signing dialogue"
        signing_dialogue.associated_fipa_dialogue = (
            ledger_api_dialogue.associated_fipa_dialogue
        )
        self.context.decision_maker_message_queue.put_nowait(signing_msg)
        self.context.logger.info(
            "proposing the transaction to the decision maker. Waiting for confirmation ..."
        )

    def _handle_transaction_digest(
        self, ledger_api_msg: LedgerApiMessage, ledger_api_dialogue: LedgerApiDialogue
    ) -> None:
        """
        Handle a message of transaction_digest performative.

        :param ledger_api_message: the ledger api message
        :param ledger_api_dialogue: the ledger api dialogue
        """
        fipa_dialogue = ledger_api_dialogue.associated_fipa_dialogue
        self.context.logger.info(
            "transaction was successfully submitted. Transaction digest={}".format(
                ledger_api_msg.transaction_digest
            )
        )
        fipa_msg = cast(Optional[FipaMessage], fipa_dialogue.last_incoming_message)
        assert fipa_msg is not None, "Could not retrieve fipa message"
        inform_msg = FipaMessage(
            performative=FipaMessage.Performative.INFORM,
            message_id=fipa_msg.message_id + 1,
            dialogue_reference=fipa_dialogue.dialogue_label.dialogue_reference,
            target=fipa_msg.message_id,
            info={"transaction_digest": ledger_api_msg.transaction_digest.body},
        )
        inform_msg.counterparty = fipa_dialogue.dialogue_label.dialogue_opponent_addr
        fipa_dialogue.update(inform_msg)
        self.context.outbox.put_message(message=inform_msg)
        self.context.logger.info(
            "informing counterparty={} of transaction digest.".format(
                fipa_dialogue.dialogue_label.dialogue_opponent_addr[-5:],
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
            "received ledger_api error message={} in dialogue={}.".format(
                ledger_api_msg, ledger_api_dialogue
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
            "cannot handle ledger_api message of performative={} in dialogue={}.".format(
                ledger_api_msg.performative, ledger_api_dialogue,
            )
        )
