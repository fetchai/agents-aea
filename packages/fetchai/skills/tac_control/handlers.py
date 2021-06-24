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

from aea.protocols.base import Message
from aea.skills.base import Handler

from packages.fetchai.protocols.default.message import DefaultMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.protocols.tac.message import TacMessage
from packages.fetchai.skills.tac_control.behaviours import TacBehaviour
from packages.fetchai.skills.tac_control.dialogues import (
    DefaultDialogues,
    OefSearchDialogue,
    OefSearchDialogues,
    TacDialogue,
    TacDialogues,
)
from packages.fetchai.skills.tac_control.game import Game, Phase, Transaction
from packages.fetchai.skills.tac_control.parameters import Parameters


class TacHandler(Handler):
    """This class handles oef messages."""

    SUPPORTED_PROTOCOL = TacMessage.protocol_id

    def setup(self) -> None:
        """Implement the handler setup."""

    def handle(self, message: Message) -> None:
        """
        Handle a register message.

        If the address is already registered, answer with an error message.

        :param message: the 'get agent state' TacMessage.
        """
        tac_msg = cast(TacMessage, message)

        # recover dialogue
        tac_dialogues = cast(TacDialogues, self.context.tac_dialogues)
        tac_dialogue = cast(TacDialogue, tac_dialogues.update(tac_msg))
        if tac_dialogue is None:
            self._handle_unidentified_dialogue(tac_msg)
            return

        self.context.logger.debug(
            "handling TAC message. performative={}".format(tac_msg.performative)
        )
        if tac_msg.performative == TacMessage.Performative.REGISTER:
            self._on_register(tac_msg, tac_dialogue)
        elif tac_msg.performative == TacMessage.Performative.UNREGISTER:
            self._on_unregister(tac_msg, tac_dialogue)
        elif tac_msg.performative == TacMessage.Performative.TRANSACTION:
            self._on_transaction(tac_msg, tac_dialogue)
        else:
            self._handle_invalid(tac_msg, tac_dialogue)

            self.context.logger.warning(
                "TAC Message performative not recognized or not permitted."
            )

    def teardown(self) -> None:
        """Implement the handler teardown."""

    def _handle_unidentified_dialogue(self, tac_msg: TacMessage) -> None:
        """
        Handle an unidentified dialogue.

        :param tac_msg: the message
        """
        self.context.logger.info(
            "received invalid tac message={}, unidentified dialogue (reference={}).".format(
                tac_msg, tac_msg.dialogue_reference
            )
        )
        default_dialogues = cast(DefaultDialogues, self.context.default_dialogues)
        default_msg, _ = default_dialogues.create(
            counterparty=tac_msg.sender,
            performative=DefaultMessage.Performative.ERROR,
            error_code=DefaultMessage.ErrorCode.INVALID_DIALOGUE,
            error_msg="Invalid dialogue.",
            error_data={"tac_message": tac_msg.encode()},
        )
        self.context.outbox.put_message(message=default_msg)

    def _on_register(self, tac_msg: TacMessage, tac_dialogue: TacDialogue) -> None:
        """
        Handle a register message.

        If the address is not registered, answer with an error message.

        :param tac_msg: the tac message
        :param tac_dialogue: the tac dialogue
        """
        game = cast(Game, self.context.game)
        if not game.phase == Phase.GAME_REGISTRATION:
            self.context.logger.warning(
                "received registration outside of game registration phase: '{}'".format(
                    tac_msg
                )
            )
            return

        parameters = cast(Parameters, self.context.parameters)
        agent_name = tac_msg.agent_name
        if len(parameters.whitelist) != 0 and agent_name not in parameters.whitelist:
            self.context.logger.warning(
                "agent name not in whitelist: '{}'".format(agent_name)
            )
            error_msg = tac_dialogue.reply(
                performative=TacMessage.Performative.TAC_ERROR,
                target_message=tac_msg,
                error_code=TacMessage.ErrorCode.AGENT_NAME_NOT_IN_WHITELIST,
            )
            self.context.outbox.put_message(message=error_msg)
            return

        game = cast(Game, self.context.game)
        if tac_msg.sender in game.registration.agent_addr_to_name:
            self.context.logger.warning(
                "agent already registered: '{}'".format(
                    game.registration.agent_addr_to_name[tac_msg.sender],
                )
            )
            error_msg = tac_dialogue.reply(
                performative=TacMessage.Performative.TAC_ERROR,
                target_message=tac_msg,
                error_code=TacMessage.ErrorCode.AGENT_ADDR_ALREADY_REGISTERED,
            )
            self.context.outbox.put_message(message=error_msg)
            return

        if agent_name in game.registration.agent_addr_to_name.values():
            self.context.logger.warning(
                "agent with this name already registered: '{}'".format(agent_name)
            )
            error_msg = tac_dialogue.reply(
                performative=TacMessage.Performative.TAC_ERROR,
                target_message=tac_msg,
                error_code=TacMessage.ErrorCode.AGENT_NAME_ALREADY_REGISTERED,
            )
            self.context.outbox.put_message(message=error_msg)
            return

        game.registration.register_agent(tac_msg.sender, agent_name)
        self.context.logger.info(
            "agent '{}' registered as '{}'".format(tac_msg.sender, agent_name)
        )

    def _on_unregister(self, tac_msg: TacMessage, tac_dialogue: TacDialogue) -> None:
        """
        Handle a unregister message.

        If the address is not registered, answer with an error message.

        :param tac_msg: the tac message
        :param tac_dialogue: the tac dialogue
        """
        game = cast(Game, self.context.game)
        if not game.phase == Phase.GAME_REGISTRATION:
            self.context.logger.warning(
                "received unregister outside of game registration phase: '{}'".format(
                    tac_msg
                )
            )
            return

        if tac_msg.sender not in game.registration.agent_addr_to_name:
            self.context.logger.warning(
                "agent not registered: '{}'".format(tac_msg.sender)
            )
            error_msg = tac_dialogue.reply(
                performative=TacMessage.Performative.TAC_ERROR,
                target_message=tac_msg,
                error_code=TacMessage.ErrorCode.AGENT_NOT_REGISTERED,
            )
            self.context.outbox.put_message(message=error_msg)
        else:
            self.context.logger.debug(
                "agent unregistered: '{}'".format(
                    game.conf.agent_addr_to_name[tac_msg.sender],
                )
            )
            game.registration.unregister_agent(tac_msg.sender)

    def _on_transaction(self, tac_msg: TacMessage, tac_dialogue: TacDialogue) -> None:
        """
        Handle a transaction TacMessage message.

        If the transaction is invalid (e.g. because the state of the game are not consistent), reply with an error.

        :param tac_msg: the tac message
        :param tac_dialogue: the tac dialogue
        """
        game = cast(Game, self.context.game)
        if not game.phase == Phase.GAME:
            self.context.logger.warning(
                "received transaction outside of game phase: '{}'".format(tac_msg)
            )
            return

        transaction = Transaction.from_message(tac_msg)
        self.context.logger.debug("handling transaction: {}".format(transaction))

        game = cast(Game, self.context.game)
        if game.is_transaction_valid(transaction):
            self._handle_valid_transaction(tac_msg, tac_dialogue, transaction)
        else:
            self._handle_invalid_transaction(tac_msg, tac_dialogue)

    def _handle_valid_transaction(
        self, tac_msg: TacMessage, tac_dialogue: TacDialogue, transaction: Transaction
    ) -> None:
        """
        Handle a valid transaction.

        That is:
        - update the game state
        - send a transaction confirmation both to the buyer and the seller.

        :param tac_msg: the message
        :param tac_dialogue: the fipa dialogue
        :param transaction: the transaction.
        """
        game = cast(Game, self.context.game)
        self.context.logger.info(
            "handling valid transaction: {}".format(transaction.id[-10:])
        )
        game.settle_transaction(transaction)

        # send the transaction confirmation.
        sender_tac_msg = tac_dialogue.reply(
            performative=TacMessage.Performative.TRANSACTION_CONFIRMATION,
            target_message=tac_msg,
            transaction_id=transaction.sender_hash,
            amount_by_currency_id=transaction.amount_by_currency_id,
            quantities_by_good_id=transaction.quantities_by_good_id,
        )
        self.context.outbox.put_message(message=sender_tac_msg)

        tac_dialogues = cast(TacDialogues, self.context.tac_dialogues)
        recovered_tac_dialogues = tac_dialogues.get_dialogues_with_counterparty(
            transaction.counterparty_address
        )
        if len(recovered_tac_dialogues) != 1:
            raise ValueError("Error when retrieving dialogue.")
        recovered_tac_dialogue = recovered_tac_dialogues[0]
        last_msg = recovered_tac_dialogue.last_message
        if last_msg is None:
            raise ValueError("Error when retrieving last message.")
        counterparty_tac_msg = recovered_tac_dialogue.reply(
            performative=TacMessage.Performative.TRANSACTION_CONFIRMATION,
            target_message=last_msg,
            transaction_id=transaction.counterparty_hash,
            amount_by_currency_id=transaction.amount_by_currency_id,
            quantities_by_good_id=transaction.quantities_by_good_id,
        )
        self.context.outbox.put_message(message=counterparty_tac_msg)

        # log messages
        self.context.logger.info(
            "transaction '{}' between '{}' and '{}' settled successfully.".format(
                transaction.id[-10:], sender_tac_msg.sender, counterparty_tac_msg.sender
            )
        )
        self.context.logger.info(
            "total number of transactions settled: {}".format(
                len(game.transactions.confirmed)
            )
        )
        self.context.logger.info("current state:\n{}".format(game.holdings_summary))

    def _handle_invalid_transaction(
        self, tac_msg: TacMessage, tac_dialogue: TacDialogue
    ) -> None:
        """Handle an invalid transaction."""
        self.context.logger.info(
            "handling invalid transaction: {}, tac_msg={}".format(
                tac_msg.transaction_id, tac_msg
            )
        )
        error_msg = tac_dialogue.reply(
            performative=TacMessage.Performative.TAC_ERROR,
            target_message=tac_msg,
            error_code=TacMessage.ErrorCode.TRANSACTION_NOT_VALID,
            info={"transaction_id": tac_msg.transaction_id},
        )
        self.context.outbox.put_message(message=error_msg)

    def _handle_invalid(self, tac_msg: TacMessage, tac_dialogue: TacDialogue) -> None:
        """
        Handle a tac message of invalid performative.

        :param tac_msg: the message
        :param tac_dialogue: the fipa dialogue
        """
        self.context.logger.warning(
            "cannot handle tac message of performative={} in dialogue={}.".format(
                tac_msg.performative, tac_dialogue
            )
        )


class OefSearchHandler(Handler):
    """Handle the message exchange with the OEF search node."""

    SUPPORTED_PROTOCOL = OefSearchMessage.protocol_id

    def setup(self) -> None:
        """Implement the handler setup."""

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
            registration_behaviour = cast(TacBehaviour, self.context.behaviours.tac,)
            if "location_agent" in data_model_name:
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
                game = cast(Game, self.context.game)
                game.is_registered_agent = True
                self.context.logger.info(
                    "the agent, with its genus and classification, is successfully registered on the SOEF."
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
            registration_behaviour = cast(TacBehaviour, self.context.behaviours.tac,)
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
