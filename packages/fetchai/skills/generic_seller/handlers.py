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

"""This package contains the handlers of a generic seller AEA."""

from typing import Optional, cast

from aea.configurations.base import PublicId
from aea.crypto.ledger_apis import LedgerApis
from aea.helpers.transaction.base import TransactionDigest
from aea.protocols.base import Message
from aea.skills.base import Handler

from packages.fetchai.connections.ledger.base import (
    CONNECTION_ID as LEDGER_CONNECTION_PUBLIC_ID,
)
from packages.fetchai.protocols.default.message import DefaultMessage
from packages.fetchai.protocols.fipa.message import FipaMessage
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.generic_seller.behaviours import (
    GenericServiceRegistrationBehaviour,
)
from packages.fetchai.skills.generic_seller.dialogues import (
    DefaultDialogues,
    FipaDialogue,
    FipaDialogues,
    LedgerApiDialogue,
    LedgerApiDialogues,
    OefSearchDialogue,
    OefSearchDialogues,
)
from packages.fetchai.skills.generic_seller.strategy import GenericStrategy


LEDGER_API_ADDRESS = str(LEDGER_CONNECTION_PUBLIC_ID)


class GenericFipaHandler(Handler):
    """This class implements a FIPA handler."""

    SUPPORTED_PROTOCOL = FipaMessage.protocol_id  # type: Optional[PublicId]

    def setup(self) -> None:
        """Implement the setup for the handler."""

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        """
        fipa_msg = cast(FipaMessage, message)

        # recover dialogue
        fipa_dialogues = cast(FipaDialogues, self.context.fipa_dialogues)
        fipa_dialogue = cast(FipaDialogue, fipa_dialogues.update(fipa_msg))
        if fipa_dialogue is None:
            self._handle_unidentified_dialogue(fipa_msg)
            return

        # handle message
        if fipa_msg.performative == FipaMessage.Performative.CFP:
            self._handle_cfp(fipa_msg, fipa_dialogue)
        elif fipa_msg.performative == FipaMessage.Performative.DECLINE:
            self._handle_decline(fipa_msg, fipa_dialogue, fipa_dialogues)
        elif fipa_msg.performative == FipaMessage.Performative.ACCEPT:
            self._handle_accept(fipa_msg, fipa_dialogue)
        elif fipa_msg.performative == FipaMessage.Performative.INFORM:
            self._handle_inform(fipa_msg, fipa_dialogue)
        else:
            self._handle_invalid(fipa_msg, fipa_dialogue)

    def teardown(self) -> None:
        """Implement the handler teardown."""

    def _handle_unidentified_dialogue(self, fipa_msg: FipaMessage) -> None:
        """
        Handle an unidentified dialogue.

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

    def _handle_cfp(self, fipa_msg: FipaMessage, fipa_dialogue: FipaDialogue) -> None:
        """
        Handle the CFP.

        If the CFP matches the supplied services then send a PROPOSE, otherwise send a DECLINE.

        :param fipa_msg: the message
        :param fipa_dialogue: the dialogue object
        """
        self.context.logger.info(
            "received CFP from sender={}".format(fipa_msg.sender[-5:])
        )
        strategy = cast(GenericStrategy, self.context.strategy)
        if strategy.is_matching_supply(fipa_msg.query):
            proposal, terms, data_for_sale = strategy.generate_proposal_terms_and_data(
                fipa_msg.query, fipa_msg.sender
            )
            fipa_dialogue.data_for_sale = data_for_sale
            fipa_dialogue.terms = terms
            self.context.logger.info(
                "sending a PROPOSE with proposal={} to sender={}".format(
                    proposal.values, fipa_msg.sender[-5:]
                )
            )
            proposal_msg = fipa_dialogue.reply(
                performative=FipaMessage.Performative.PROPOSE,
                target_message=fipa_msg,
                proposal=proposal,
            )
            self.context.outbox.put_message(message=proposal_msg)
        else:
            self.context.logger.info(
                "declined the CFP from sender={}".format(fipa_msg.sender[-5:])
            )
            decline_msg = fipa_dialogue.reply(
                performative=FipaMessage.Performative.DECLINE, target_message=fipa_msg,
            )
            self.context.outbox.put_message(message=decline_msg)

    def _handle_decline(
        self,
        fipa_msg: FipaMessage,
        fipa_dialogue: FipaDialogue,
        fipa_dialogues: FipaDialogues,
    ) -> None:
        """
        Handle the DECLINE.

        Close the dialogue.

        :param fipa_msg: the message
        :param fipa_dialogue: the dialogue object
        :param fipa_dialogues: the dialogues object
        """
        self.context.logger.info(
            "received DECLINE from sender={}".format(fipa_msg.sender[-5:])
        )
        fipa_dialogues.dialogue_stats.add_dialogue_endstate(
            FipaDialogue.EndState.DECLINED_PROPOSE, fipa_dialogue.is_self_initiated
        )

    def _handle_accept(
        self, fipa_msg: FipaMessage, fipa_dialogue: FipaDialogue
    ) -> None:
        """
        Handle the ACCEPT.

        Respond with a MATCH_ACCEPT_W_INFORM which contains the address to send the funds to.

        :param fipa_msg: the message
        :param fipa_dialogue: the dialogue object
        """
        self.context.logger.info(
            "received ACCEPT from sender={}".format(fipa_msg.sender[-5:])
        )
        info = {"address": fipa_dialogue.terms.sender_address}
        match_accept_msg = fipa_dialogue.reply(
            performative=FipaMessage.Performative.MATCH_ACCEPT_W_INFORM,
            target_message=fipa_msg,
            info=info,
        )
        self.context.logger.info(
            "sending MATCH_ACCEPT_W_INFORM to sender={} with info={}".format(
                fipa_msg.sender[-5:], info,
            )
        )
        self.context.outbox.put_message(message=match_accept_msg)

    def _handle_inform(
        self, fipa_msg: FipaMessage, fipa_dialogue: FipaDialogue
    ) -> None:
        """
        Handle the INFORM.

        If the INFORM message contains the transaction_digest then verify that it is settled, otherwise do nothing.
        If the transaction is settled, send the data, otherwise do nothing.

        :param fipa_msg: the message
        :param fipa_dialogue: the dialogue object
        """
        self.context.logger.info(
            "received INFORM from sender={}".format(fipa_msg.sender[-5:])
        )

        strategy = cast(GenericStrategy, self.context.strategy)
        if strategy.is_ledger_tx and "transaction_digest" in fipa_msg.info.keys():
            self.context.logger.info(
                "checking whether transaction={} has been received ...".format(
                    fipa_msg.info["transaction_digest"]
                )
            )
            ledger_api_dialogues = cast(
                LedgerApiDialogues, self.context.ledger_api_dialogues
            )
            ledger_api_msg, ledger_api_dialogue = ledger_api_dialogues.create(
                counterparty=LEDGER_API_ADDRESS,
                performative=LedgerApiMessage.Performative.GET_TRANSACTION_RECEIPT,
                transaction_digest=TransactionDigest(
                    fipa_dialogue.terms.ledger_id, fipa_msg.info["transaction_digest"]
                ),
            )
            ledger_api_dialogue = cast(LedgerApiDialogue, ledger_api_dialogue)
            ledger_api_dialogue.associated_fipa_dialogue = fipa_dialogue
            self.context.outbox.put_message(message=ledger_api_msg)
        elif strategy.is_ledger_tx:
            self.context.logger.warning(
                "did not receive transaction digest from sender={}.".format(
                    fipa_msg.sender[-5:]
                )
            )
        elif not strategy.is_ledger_tx and "Done" in fipa_msg.info.keys():
            inform_msg = fipa_dialogue.reply(
                performative=FipaMessage.Performative.INFORM,
                target_message=fipa_msg,
                info=fipa_dialogue.data_for_sale,
            )
            self.context.outbox.put_message(message=inform_msg)
            fipa_dialogues = cast(FipaDialogues, self.context.fipa_dialogues)
            fipa_dialogues.dialogue_stats.add_dialogue_endstate(
                FipaDialogue.EndState.SUCCESSFUL, fipa_dialogue.is_self_initiated
            )
            self.context.logger.info(
                "transaction confirmed, sending data={} to buyer={}.".format(
                    fipa_dialogue.data_for_sale, fipa_msg.sender[-5:],
                )
            )
        else:
            self.context.logger.warning(
                "did not receive transaction confirmation from sender={}.".format(
                    fipa_msg.sender[-5:]
                )
            )

    def _handle_invalid(
        self, fipa_msg: FipaMessage, fipa_dialogue: FipaDialogue
    ) -> None:
        """
        Handle a fipa message of invalid performative.

        :param fipa_msg: the message
        :param fipa_dialogue: the dialogue object
        """
        self.context.logger.warning(
            "cannot handle fipa message of performative={} in dialogue={}.".format(
                fipa_msg.performative, fipa_dialogue
            )
        )


class GenericLedgerApiHandler(Handler):
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

    def _handle_transaction_receipt(
        self, ledger_api_msg: LedgerApiMessage, ledger_api_dialogue: LedgerApiDialogue
    ) -> None:
        """
        Handle a message of balance performative.

        :param ledger_api_msg: the ledger api message
        :param ledger_api_dialogue: the ledger api dialogue
        """
        fipa_dialogue = ledger_api_dialogue.associated_fipa_dialogue
        is_settled = LedgerApis.is_transaction_settled(
            fipa_dialogue.terms.ledger_id, ledger_api_msg.transaction_receipt.receipt
        )
        is_valid = LedgerApis.is_transaction_valid(
            fipa_dialogue.terms.ledger_id,
            ledger_api_msg.transaction_receipt.transaction,
            fipa_dialogue.terms.sender_address,
            fipa_dialogue.terms.counterparty_address,
            fipa_dialogue.terms.nonce,
            fipa_dialogue.terms.counterparty_payable_amount,
        )
        if is_settled and is_valid:
            last_message = cast(
                Optional[FipaMessage], fipa_dialogue.last_incoming_message
            )
            if last_message is None:
                raise ValueError("Cannot retrieve last fipa message.")
            inform_msg = fipa_dialogue.reply(
                performative=FipaMessage.Performative.INFORM,
                target_message=last_message,
                info=fipa_dialogue.data_for_sale,
            )
            self.context.outbox.put_message(message=inform_msg)
            fipa_dialogues = cast(FipaDialogues, self.context.fipa_dialogues)
            fipa_dialogues.dialogue_stats.add_dialogue_endstate(
                FipaDialogue.EndState.SUCCESSFUL, fipa_dialogue.is_self_initiated
            )
            self.context.logger.info(
                "transaction confirmed, sending data={} to buyer={}.".format(
                    fipa_dialogue.data_for_sale, last_message.sender[-5:],
                )
            )
        else:
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


class GenericOefSearchHandler(Handler):
    """This class implements an OEF search handler."""

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
        if oef_search_msg.performative == OefSearchMessage.Performative.SUCCESS:
            self._handle_success(oef_search_msg, oef_search_dialogue)
        elif oef_search_msg.performative == OefSearchMessage.Performative.OEF_ERROR:
            self._handle_error(oef_search_msg, oef_search_dialogue)
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
                GenericServiceRegistrationBehaviour,
                self.context.behaviours.service_registration,
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
                self.context.logger.info(
                    "the agent, with its genus and classification, and its service are successfully registered on the SOEF."
                )
            else:
                self.context.logger.warning(
                    f"received soef SUCCESS message as a reply to the following unexpected message: {target_message}"
                )

    def _handle_error(
        self,
        oef_search_error_msg: OefSearchMessage,
        oef_search_dialogue: OefSearchDialogue,
    ) -> None:
        """
        Handle an oef search message.

        :param oef_search_error_msg: the oef search message
        :param oef_search_dialogue: the dialogue
        """
        self.context.logger.info(
            "received oef_search error message={} in dialogue={}.".format(
                oef_search_error_msg, oef_search_dialogue
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
                GenericServiceRegistrationBehaviour,
                self.context.behaviours.service_registration,
            )
            registration_behaviour.failed_registration_msg = target_message

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
