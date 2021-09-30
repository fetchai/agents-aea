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

from typing import Dict, Optional, Tuple, cast

from aea.common import Address
from aea.protocols.base import Message
from aea.skills.base import Handler

from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.protocols.state_update.message import StateUpdateMessage
from packages.fetchai.protocols.tac.message import TacMessage
from packages.fetchai.skills.tac_participation.dialogues import (
    OefSearchDialogue,
    OefSearchDialogues,
    StateUpdateDialogue,
    StateUpdateDialogues,
    TacDialogue,
    TacDialogues,
)
from packages.fetchai.skills.tac_participation.game import Game, Phase


class OefSearchHandler(Handler):
    """This class handles oef messages."""

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
        if oef_search_msg.performative == OefSearchMessage.Performative.SEARCH_RESULT:
            self._on_search_result(oef_search_msg, oef_search_dialogue)
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

    def _on_oef_error(
        self, oef_search_msg: OefSearchMessage, oef_search_dialogue: OefSearchDialogue
    ) -> None:
        """
        Handle an OEF error message.

        :param oef_search_msg: the oef search msg
        :param oef_search_dialogue: the dialogue
        """
        self.context.logger.warning(
            "received OEF Search error: dialogue_reference={}, oef_error_operation={}".format(
                oef_search_dialogue.dialogue_label.dialogue_reference,
                oef_search_msg.oef_error_operation,
            )
        )

    def _on_search_result(
        self, oef_search_msg: OefSearchMessage, oef_search_dialogue: OefSearchDialogue
    ) -> None:
        """
        Split the search results from the OEF search node.

        :param oef_search_msg: the search result
        :param oef_search_dialogue: the dialogue
        """
        self.context.logger.debug(
            "on search result: dialogue_reference={} agents={}".format(
                oef_search_dialogue.dialogue_label.dialogue_reference,
                oef_search_msg.agents,
            )
        )
        self._on_controller_search_result(oef_search_msg.agents)

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

    def _on_controller_search_result(
        self, agent_addresses: Tuple[Address, ...]
    ) -> None:
        """
        Process the search result for a controller.

        :param agent_addresses: list of agent addresses
        """
        game = cast(Game, self.context.game)
        if game.phase.value != Phase.PRE_GAME.value:
            self.context.logger.debug(
                "ignoring controller search result, the agent is already competing."
            )
            return

        if len(agent_addresses) == 0:
            self.context.logger.info("couldn't find the TAC controller. Retrying...")
        elif len(agent_addresses) > 1:
            self.context.logger.warning(
                "found more than one TAC controller. Retrying..."
            )
        else:
            self.context.logger.info("found the TAC controller. Registering...")
            controller_addr = agent_addresses[0]
            self._register_to_tac(controller_addr)

    def _register_to_tac(self, controller_addr: Address) -> None:
        """
        Register to active TAC Controller.

        :param controller_addr: the address of the controller.
        """
        game = cast(Game, self.context.game)
        game.update_expected_controller_addr(controller_addr)
        game.update_game_phase(Phase.GAME_REGISTRATION)
        tac_dialogues = cast(TacDialogues, self.context.tac_dialogues)
        tac_msg, tac_dialogue = tac_dialogues.create(
            counterparty=controller_addr,
            performative=TacMessage.Performative.REGISTER,
            agent_name=self.context.agent_name,
        )
        tac_dialogue = cast(TacDialogue, tac_dialogue)
        game.tac_dialogue = tac_dialogue
        self.context.outbox.put_message(message=tac_msg)
        self.context.behaviours.tac_search.is_active = False
        self.context.shared_state["tac_version_id"] = game.expected_version_id


class TacHandler(Handler):
    """This class handles oef messages."""

    SUPPORTED_PROTOCOL = TacMessage.protocol_id

    def setup(self) -> None:
        """Implement the handler setup."""

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        """
        tac_msg = cast(TacMessage, message)

        # recover dialogue
        tac_dialogues = cast(TacDialogues, self.context.tac_dialogues)
        tac_dialogue = cast(Optional[TacDialogue], tac_dialogues.update(tac_msg))
        if tac_dialogue is None:
            self._handle_unidentified_dialogue(tac_msg)
            return

        # handle message
        game = cast(Game, self.context.game)
        self.context.logger.debug(
            "handling controller response. performative={}".format(tac_msg.performative)
        )
        if tac_msg.sender != game.expected_controller_addr:
            raise ValueError(
                "The sender of the message is not the controller agent we registered with."
            )

        if tac_msg.performative == TacMessage.Performative.TAC_ERROR:
            self._on_tac_error(tac_msg, tac_dialogue)
        elif tac_msg.performative == TacMessage.Performative.GAME_DATA:
            self._on_start(tac_msg)
        elif tac_msg.performative == TacMessage.Performative.CANCELLED:
            self._on_cancelled(tac_msg)
        elif tac_msg.performative == TacMessage.Performative.TRANSACTION_CONFIRMATION:
            self._on_transaction_confirmed(tac_msg)
        else:
            self._handle_invalid(tac_msg, tac_dialogue)

    def teardown(self) -> None:
        """Implement the handler teardown."""

    def _handle_unidentified_dialogue(self, tac_msg: TacMessage) -> None:
        """
        Handle an unidentified dialogue.

        :param tac_msg: the message
        """
        self.context.logger.warning(
            "received invalid tac message={}, unidentified dialogue.".format(tac_msg)
        )

    def _on_tac_error(self, tac_msg: TacMessage, tac_dialogue: TacDialogue) -> None:
        """
        Handle 'on tac error' event emitted by the controller.

        :param tac_msg: The tac message.
        :param tac_dialogue: the tac dialogue
        """
        error_code = tac_msg.error_code
        self.context.logger.debug(
            "received error from the controller in dialogue={}. error_msg={}".format(
                tac_dialogue, TacMessage.ErrorCode.to_msg(error_code.value)
            )
        )
        if error_code == TacMessage.ErrorCode.TRANSACTION_NOT_VALID:
            info = cast(Dict[str, str], tac_msg.info)
            transaction_id = (
                cast(str, info.get("transaction_id"))
                if (info is not None and info.get("transaction_id") is not None)
                else "NO_TX_ID"
            )
            self.context.logger.warning(
                "received error on transaction id: {}".format(transaction_id[-10:])
            )

    def _on_start(self, tac_msg: TacMessage) -> None:
        """
        Handle the 'start' event emitted by the controller.

        :param tac_msg: the game data
        """
        game = cast(Game, self.context.game)
        if game.phase.value != Phase.GAME_REGISTRATION.value:
            self.context.logger.warning(
                "we do not expect a start message in game phase={}".format(
                    game.phase.value
                )
            )
            return

        self.context.logger.info(
            "received start event from the controller. Starting to compete..."
        )
        game = cast(Game, self.context.game)
        game.init(tac_msg, tac_msg.sender)
        game.update_game_phase(Phase.GAME)

        if game.is_using_contract:
            contract_address = (
                None if tac_msg.info is None else tac_msg.info.get("contract_address")
            )

            if contract_address is not None:
                game.contract_address = contract_address
                self.context.shared_state["erc1155_contract_address"] = contract_address
                self.context.logger.info(
                    "received a contract address: {}".format(contract_address)
                )
                self._update_ownership_and_preferences(tac_msg)
            else:
                self.context.logger.warning("did not receive a contract address!")
        else:
            self._update_ownership_and_preferences(tac_msg)

    def _update_ownership_and_preferences(self, tac_msg: TacMessage) -> None:
        """
        Update ownership and preferences.

        :param tac_msg: the game data
        """
        self.context.logger.info("processing game data, message={}".format(tac_msg))
        state_update_dialogues = cast(
            StateUpdateDialogues, self.context.state_update_dialogues
        )
        state_update_msg, state_update_dialogue = state_update_dialogues.create(
            counterparty=self.context.decision_maker_address,
            performative=StateUpdateMessage.Performative.INITIALIZE,
            amount_by_currency_id=tac_msg.amount_by_currency_id,
            quantities_by_good_id=tac_msg.quantities_by_good_id,
            exchange_params_by_currency_id=tac_msg.exchange_params_by_currency_id,
            utility_params_by_good_id=tac_msg.utility_params_by_good_id,
        )
        self.context.shared_state["fee_by_currency_id"] = tac_msg.fee_by_currency_id
        state_update_dialogue = cast(StateUpdateDialogue, state_update_dialogue)
        game = cast(Game, self.context.game)
        game.state_update_dialogue = state_update_dialogue
        self.context.decision_maker_message_queue.put_nowait(state_update_msg)

    def _on_cancelled(self, tac_msg: TacMessage) -> None:
        """
        Handle the cancellation of the competition from the TAC controller.

        :param tac_msg: the TacMessage.
        """
        game = cast(Game, self.context.game)
        if game.phase.value not in [Phase.GAME_REGISTRATION.value, Phase.GAME.value]:
            self.context.logger.warning(
                "we do not expect a message in game phase={}, received msg={}".format(
                    game.phase.value, tac_msg
                )
            )
            return

        self.context.logger.info("received cancellation from the controller.")
        game = cast(Game, self.context.game)
        game.update_game_phase(Phase.POST_GAME)
        self.context.is_active = False
        self.context.shared_state["is_game_finished"] = True

    def _on_transaction_confirmed(self, tac_msg: TacMessage) -> None:
        """
        Handle 'on transaction confirmed' event emitted by the controller.

        :param tac_msg: the TacMessage.
        """
        game = cast(Game, self.context.game)
        if game.phase.value != Phase.GAME.value:
            self.context.logger.warning(
                "we do not expect a transaction in game phase={}, received msg={}".format(
                    game.phase.value, tac_msg
                )
            )
            return

        self.context.logger.info(
            "received transaction confirmation from the controller: transaction_id={}".format(
                tac_msg.transaction_id
            )
        )
        state_update_dialogue = game.state_update_dialogue
        last_msg = state_update_dialogue.last_message
        if last_msg is None:
            raise ValueError("Could not retrieve last message.")
        state_update_msg = state_update_dialogue.reply(
            performative=StateUpdateMessage.Performative.APPLY,
            target_message=last_msg,
            amount_by_currency_id=tac_msg.amount_by_currency_id,
            quantities_by_good_id=tac_msg.quantities_by_good_id,
        )
        self.context.decision_maker_message_queue.put_nowait(state_update_msg)
        if "confirmed_tx_ids" not in self.context.shared_state.keys():
            self.context.shared_state["confirmed_tx_ids"] = []
        self.context.shared_state["confirmed_tx_ids"].append(tac_msg.transaction_id)

    def _handle_invalid(self, tac_msg: TacMessage, tac_dialogue: TacDialogue) -> None:
        """
        Handle an oef search message.

        :param tac_msg: the tac message
        :param tac_dialogue: the tac dialogue
        """
        self.context.logger.warning(
            "cannot handle tac message of performative={} in dialogue={}.".format(
                tac_msg.performative, tac_dialogue
            )
        )
