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

"""This module contains the handler for the 'ml_data_provider' skill."""

from typing import Optional, cast

from aea.configurations.base import PublicId
from aea.protocols.base import Message
from aea.skills.base import Handler

from packages.fetchai.protocols.default.message import DefaultMessage
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.ml_trade.message import MlTradeMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.ml_data_provider.behaviours import (
    ServiceRegistrationBehaviour,
)
from packages.fetchai.skills.ml_data_provider.dialogues import (
    DefaultDialogues,
    LedgerApiDialogue,
    LedgerApiDialogues,
    MlTradeDialogue,
    MlTradeDialogues,
    OefSearchDialogue,
    OefSearchDialogues,
)
from packages.fetchai.skills.ml_data_provider.strategy import Strategy


class MlTradeHandler(Handler):
    """ML trade handler."""

    SUPPORTED_PROTOCOL = MlTradeMessage.protocol_id

    def setup(self) -> None:
        """Set up the handler."""

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

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
        if ml_trade_msg.performative == MlTradeMessage.Performative.CFP:
            self._handle_cft(ml_trade_msg, ml_trade_dialogue)
        elif ml_trade_msg.performative == MlTradeMessage.Performative.ACCEPT:
            self._handle_accept(ml_trade_msg, ml_trade_dialogue)
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

    def _handle_cft(
        self, ml_trade_msg: MlTradeMessage, ml_trade_dialogue: MlTradeDialogue
    ) -> None:
        """
        Handle call for terms.

        :param ml_trade_msg: the ml trade message
        :param ml_trade_dialogue: the dialogue object
        """
        query = ml_trade_msg.query
        self.context.logger.info(
            "got a Call for Terms from {}.".format(ml_trade_msg.sender[-5:])
        )
        strategy = cast(Strategy, self.context.strategy)
        if not strategy.is_matching_supply(query):
            self.context.logger.info("query does not match supply.")
            return
        terms = strategy.generate_terms()
        self.context.logger.info(
            "sending to the address={} a Terms message: {}".format(
                ml_trade_msg.sender[-5:], terms.values
            )
        )
        terms_msg = ml_trade_dialogue.reply(
            performative=MlTradeMessage.Performative.TERMS,
            target_message=ml_trade_msg,
            terms=terms,
        )
        self.context.outbox.put_message(message=terms_msg)

    def _handle_accept(
        self, ml_trade_msg: MlTradeMessage, ml_trade_dialogue: MlTradeDialogue
    ) -> None:
        """
        Handle accept.

        :param ml_trade_msg: the ml trade message
        :param ml_trade_dialogue: the dialogue object
        """
        terms = ml_trade_msg.terms
        self.context.logger.info(
            "got an Accept from {}: {}".format(ml_trade_msg.sender[-5:], terms.values)
        )
        strategy = cast(Strategy, self.context.strategy)
        if not strategy.is_valid_terms(terms):
            self.context.logger.info("terms are not valid.")
            return
        data = strategy.sample_data(terms.values["batch_size"])
        self.context.logger.info(
            "sending to address={} a Data message: shape={}".format(
                ml_trade_msg.sender[-5:], data[0].shape
            )
        )
        payload = strategy.encode_sample_data(data)
        data_msg = ml_trade_dialogue.reply(
            performative=MlTradeMessage.Performative.DATA,
            target_message=ml_trade_msg,
            terms=terms,
            payload=payload,
        )
        self.context.outbox.put_message(message=data_msg)

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
                ServiceRegistrationBehaviour,
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
                ServiceRegistrationBehaviour,
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
