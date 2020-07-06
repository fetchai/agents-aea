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

from aea.configurations.base import ProtocolId
from aea.mail.base import Address
from aea.protocols.base import Message
from aea.protocols.signing.message import SigningMessage
from aea.protocols.state_update.message import StateUpdateMessage
from aea.skills.base import Handler

from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.protocols.tac.message import TacMessage
from packages.fetchai.skills.tac_participation.dialogues import (
    OefSearchDialogue,
    OefSearchDialogues,
    SigningDialogue,
    SigningDialogues,
    TacDialogue,
    TacDialogues,
)
from packages.fetchai.skills.tac_participation.game import Game, Phase


class OEFSearchHandler(Handler):
    """This class handles oef messages."""

    SUPPORTED_PROTOCOL = OefSearchMessage.protocol_id

    def setup(self) -> None:
        """
        Implement the handler setup.

        :return: None
        """
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
        if oef_search_msg.performative == OefSearchMessage.Performative.SEARCH_RESULT:
            self._on_search_result(oef_search_msg, oef_search_dialogue)
        elif oef_search_msg.performative == OefSearchMessage.Performative.OEF_ERROR:
            self._on_oef_error(oef_search_msg, oef_search_dialogue)
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
        self.context.logger.warning(
            "[{}]: received invalid oef_search message={}, unidentified dialogue.".format(
                self.context.agent_name, oef_search_msg
            )
        )

    def _on_oef_error(
        self, oef_search_msg: OefSearchMessage, oef_search_dialogue: OefSearchDialogue
    ) -> None:
        """
        Handle an OEF error message.

        :param oef_search_msg: the oef search msg
        :param oef_search_dialogue: the dialogue
        :return: None
        """
        self.context.logger.warning(
            "[{}]: Received OEF Search error: dialogue_reference={}, oef_error_operation={}".format(
                self.context.agent_name,
                oef_search_msg.dialogue_reference,
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
        :return: None
        """
        self.context.logger.debug(
            "[{}]: on search result: dialogue_reference={} agents={}".format(
                self.context.agent_name,
                oef_search_msg.dialogue_reference,
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
        :return: None
        """
        self.context.logger.warning(
            "[{}]: cannot handle oef_search message of performative={} in dialogue={}.".format(
                self.context.agent_name,
                oef_search_msg.performative,
                oef_search_dialogue,
            )
        )

    def _on_controller_search_result(
        self, agent_addresses: Tuple[Address, ...]
    ) -> None:
        """
        Process the search result for a controller.

        :param agent_addresses: list of agent addresses

        :return: None
        """
        game = cast(Game, self.context.game)
        if game.phase.value != Phase.PRE_GAME.value:
            self.context.logger.debug(
                "[{}]: Ignoring controller search result, the agent is already competing.".format(
                    self.context.agent_name
                )
            )
            return

        if len(agent_addresses) == 0:
            self.context.logger.info(
                "[{}]: Couldn't find the TAC controller. Retrying...".format(
                    self.context.agent_name
                )
            )
        elif len(agent_addresses) > 1:
            self.context.logger.warning(
                "[{}]: Found more than one TAC controller. Retrying...".format(
                    self.context.agent_name
                )
            )
        else:
            self.context.logger.info(
                "[{}]: Found the TAC controller. Registering...".format(
                    self.context.agent_name
                )
            )
            controller_addr = agent_addresses[0]
            self._register_to_tac(controller_addr)

    def _register_to_tac(self, controller_addr: Address) -> None:
        """
        Register to active TAC Controller.

        :param controller_addr: the address of the controller.

        :return: None
        """
        game = cast(Game, self.context.game)
        game.update_expected_controller_addr(controller_addr)
        game.update_game_phase(Phase.GAME_REGISTRATION)
        tac_msg = TacMessage(
            performative=TacMessage.Performative.REGISTER,
            agent_name=self.context.agent_name,
        )
        tac_msg.counterparty = controller_addr
        self.context.outbox.put_message(message=tac_msg)
        self.context.behaviours.tac.is_active = False


class TacHandler(Handler):
    """This class handles oef messages."""

    SUPPORTED_PROTOCOL = TacMessage.protocol_id

    def setup(self) -> None:
        """
        Implement the handler setup.

        :return: None
        """
        pass

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :return: None
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
            "[{}]: Handling controller response. performative={}".format(
                self.context.agent_name, tac_msg.performative
            )
        )
        if message.counterparty != game.expected_controller_addr:
            raise ValueError(
                "The sender of the message is not the controller agent we registered with."
            )

        if tac_msg.performative == TacMessage.Performative.TAC_ERROR:
            self._on_tac_error(tac_msg, tac_dialogue)
        elif game.phase.value == Phase.PRE_GAME.value:
            raise ValueError(
                "We do not expect a controller agent message in the pre game phase."
            )
        elif game.phase.value == Phase.GAME_REGISTRATION.value:
            if tac_msg.performative == TacMessage.Performative.GAME_DATA:
                self._on_start(tac_msg, tac_dialogue)
            elif tac_msg.performative == TacMessage.Performative.CANCELLED:
                self._on_cancelled(tac_msg, tac_dialogue)
        elif game.phase.value == Phase.GAME.value:
            if tac_msg.performative == TacMessage.Performative.TRANSACTION_CONFIRMATION:
                self._on_transaction_confirmed(tac_msg, tac_dialogue)
            elif tac_msg.performative == TacMessage.Performative.CANCELLED:
                self._on_cancelled(tac_msg, tac_dialogue)
        elif game.phase.value == Phase.POST_GAME.value:
            raise ValueError(
                "We do not expect a controller agent message in the post game phase."
            )
        else:
            self._handle_invalid(tac_msg, tac_dialogue)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass

    def _handle_unidentified_dialogue(self, tac_msg: TacMessage) -> None:
        """
        Handle an unidentified dialogue.

        :param tac_msg: the message
        """
        self.context.logger.warning(
            "[{}]: received invalid tac message={}, unidentified dialogue.".format(
                self.context.agent_name, tac_msg
            )
        )

    def _on_tac_error(self, tac_msg: TacMessage, tac_dialogue: TacDialogue) -> None:
        """
        Handle 'on tac error' event emitted by the controller.

        :param tac_msg: The tac message.
        :param tac_dialogue: the tac dialogue
        :return: None
        """
        error_code = tac_msg.error_code
        self.context.logger.debug(
            "[{}]: Received error from the controller. error_msg={}".format(
                self.context.agent_name, TacMessage.ErrorCode.to_msg(error_code.value)
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
                "[{}]: Received error on transaction id: {}".format(
                    self.context.agent_name, transaction_id[-10:]
                )
            )

    def _on_start(self, tac_msg: TacMessage, tac_dialogue: TacDialogue) -> None:
        """
        Handle the 'start' event emitted by the controller.

        :param tac_msg: the game data
        :param tac_dialogue: the tac dialogue
        :return: None
        """
        self.context.logger.info(
            "[{}]: Received start event from the controller. Starting to compete...".format(
                self.context.agent_name
            )
        )
        game = cast(Game, self.context.game)
        game.init(tac_msg, tac_msg.counterparty)
        game.update_game_phase(Phase.GAME)

        if game.is_using_contract:
            contract_address = (
                None if tac_msg.info is None else tac_msg.info.get("contract_address")
            )

            if contract_address is not None:
                game.contract_address = contract_address
                self.context.shared_state["erc1155_contract_address"] = contract_address
                self.context.logger.info(
                    "[{}]: Received a contract address: {}".format(
                        self.context.agent_name, contract_address
                    )
                )
                # TODO; verify on-chain matches off-chain wealth
                self._update_ownership_and_preferences(tac_msg, tac_dialogue)
            else:
                self.context.logger.warning(
                    "[{}]: Did not receive a contract address!".format(
                        self.context.agent_name
                    )
                )
        else:
            self._update_ownership_and_preferences(tac_msg, tac_dialogue)

    def _update_ownership_and_preferences(
        self, tac_msg: TacMessage, tac_dialogue: TacDialogue
    ) -> None:
        """
        Update ownership and preferences.

        :param tac_msg: the game data
        :param tac_dialogue: the tac dialogue
        :return: None
        """
        state_update_msg = StateUpdateMessage(
            performative=StateUpdateMessage.Performative.INITIALIZE,
            amount_by_currency_id=tac_msg.amount_by_currency_id,
            quantities_by_good_id=tac_msg.quantities_by_good_id,
            exchange_params_by_currency_id=tac_msg.exchange_params_by_currency_id,
            utility_params_by_good_id=tac_msg.utility_params_by_good_id,
            tx_fee=tac_msg.tx_fee,
        )
        self.context.decision_maker_message_queue.put_nowait(state_update_msg)

    def _on_cancelled(self, tac_msg: TacMessage, tac_dialogue: TacDialogue) -> None:
        """
        Handle the cancellation of the competition from the TAC controller.

        :param tac_msg: the TacMessage.
        :param tac_dialogue: the tac dialogue
        :return: None
        """
        self.context.logger.info(
            "[{}]: Received cancellation from the controller.".format(
                self.context.agent_name
            )
        )
        game = cast(Game, self.context.game)
        game.update_game_phase(Phase.POST_GAME)
        self.context.is_active = False
        self.context.shared_state["is_game_finished"] = True

    def _on_transaction_confirmed(
        self, tac_msg: TacMessage, tac_dialogue: TacDialogue
    ) -> None:
        """
        Handle 'on transaction confirmed' event emitted by the controller.

        :param tac_msg: the TacMessage.
        :param tac_dialogue: the tac dialogue
        :return: None
        """
        self.context.logger.info(
            "[{}]: Received transaction confirmation from the controller: transaction_id={}".format(
                self.context.agent_name, tac_msg.tx_id[-10:]
            )
        )
        state_update_msg = StateUpdateMessage(
            performative=StateUpdateMessage.Performative.APPLY,
            amount_by_currency_id=tac_msg.amount_by_currency_id,
            quantities_by_good_id=tac_msg.quantities_by_good_id,
        )
        self.context.decision_maker_message_queue.put_nowait(state_update_msg)
        if "confirmed_tx_ids" not in self.context.shared_state.keys():
            self.context.shared_state["confirmed_tx_ids"] = []
        self.context.shared_state["confirmed_tx_ids"].append(tac_msg.tx_id)

    def _handle_invalid(self, tac_msg: TacMessage, tac_dialogue: TacDialogue) -> None:
        """
        Handle an oef search message.

        :param tac_msg: the tac message
        :param tac_dialogue: the tac dialogue
        :return: None
        """
        game = cast(Game, self.context.game)
        self.context.logger.warning(
            "[{}]: cannot handle tac message of performative={} in dialogue={} during game_phase={}.".format(
                self.context.agent_name, tac_msg.performative, tac_dialogue, game.phase,
            )
        )


class SigningHandler(Handler):
    """This class implements the transaction handler."""

    SUPPORTED_PROTOCOL = SigningMessage.protocol_id  # type: Optional[ProtocolId]

    def setup(self) -> None:
        """
        Implement the setup.

        :return: None
        """
        pass

    def handle(self, message: Message) -> None:
        """
        Dispatch message to relevant handler and respond.

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
        # TODO: Need to modify here and add the contract option in case we are using one.
        self.context.logger.info(
            "[{}]: transaction confirmed by decision maker, sending to controller.".format(
                self.context.agent_name
            )
        )
        game = cast(Game, self.context.game)
        tx_counterparty_signature = cast(
            str, signing_msg.skill_callback_info.get("tx_counterparty_signature")
        )
        tx_counterparty_id = cast(
            str, signing_msg.skill_callback_info.get("tx_counterparty_id")
        )
        tx_id = cast(str, signing_msg.skill_callback_info.get("tx_id"))
        if (tx_counterparty_signature is not None) and (tx_counterparty_id is not None):
            # tx_id = tx_message.tx_id + "_" + tx_counterparty_id
            msg = TacMessage(
                performative=TacMessage.Performative.TRANSACTION,
                tx_id=tx_id,
                tx_sender_addr=signing_msg.terms.sender_address,
                tx_counterparty_addr=signing_msg.terms.counterparty_address,
                amount_by_currency_id=signing_msg.terms.amount_by_currency_id,
                is_sender_payable_tx_fee=signing_msg.terms.is_sender_payable_tx_fee,
                quantities_by_good_id=signing_msg.terms.quantities_by_good_id,
                tx_sender_signature=signing_msg.signed_transaction.body,
                tx_counterparty_signature=tx_counterparty_signature,
                tx_nonce=signing_msg.terms.nonce,
            )
            msg.counterparty = game.conf.controller_addr
            self.context.outbox.put_message(message=msg)
        else:
            self.context.logger.warning(
                "[{}]: transaction has no counterparty id or signature!".format(
                    self.context.agent_name
                )
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
