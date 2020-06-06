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
from aea.decision_maker.messages.state_update import StateUpdateMessage
from aea.decision_maker.messages.transaction import TransactionMessage
from aea.mail.base import Address
from aea.protocols.base import Message
from aea.skills.base import Handler

from packages.fetchai.contracts.erc1155.contract import ERC1155Contract
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.protocols.tac.message import TacMessage
from packages.fetchai.skills.tac_participation.game import Game, Phase
from packages.fetchai.skills.tac_participation.search import Search


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
        oef_message = cast(OefSearchMessage, message)

        self.context.logger.debug(
            "[{}]: Handling OEFSearch message. performative={}".format(
                self.context.agent_name, oef_message.performative
            )
        )
        if oef_message.performative == OefSearchMessage.Performative.SEARCH_RESULT:
            self._on_search_result(oef_message)
        elif oef_message.performative == OefSearchMessage.Performative.OEF_ERROR:
            self._on_oef_error(oef_message)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass

    def _on_oef_error(self, oef_error: OefSearchMessage) -> None:
        """
        Handle an OEF error message.

        :param oef_error: the oef error

        :return: None
        """
        self.context.logger.warning(
            "[{}]: Received OEF Search error: dialogue_reference={}, oef_error_operation={}".format(
                self.context.agent_name,
                oef_error.dialogue_reference,
                oef_error.oef_error_operation,
            )
        )

    def _on_search_result(self, search_result: OefSearchMessage) -> None:
        """
        Split the search results from the OEF search node.

        :param search_result: the search result

        :return: None
        """
        search = cast(Search, self.context.search)
        search_id = int(search_result.dialogue_reference[0])
        agents = search_result.agents
        self.context.logger.debug(
            "[{}]: on search result: search_id={} agents={}".format(
                self.context.agent_name, search_id, agents
            )
        )
        if search_id in search.ids_for_tac:
            self._on_controller_search_result(agents)
        else:
            self.context.logger.debug(
                "[{}]: Unknown search id: search_id={}".format(
                    self.context.agent_name, search_id
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


class TACHandler(Handler):
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
        game = cast(Game, self.context.game)
        self.context.logger.debug(
            "[{}]: Handling controller response. performative={}".format(
                self.context.agent_name, tac_msg.performative
            )
        )
        try:
            if message.counterparty != game.expected_controller_addr:
                raise ValueError(
                    "The sender of the message is not the controller agent we registered with."
                )

            if tac_msg.performative == TacMessage.Performative.TAC_ERROR:
                self._on_tac_error(tac_msg)
            elif game.phase.value == Phase.PRE_GAME.value:
                raise ValueError(
                    "We do not expect a controller agent message in the pre game phase."
                )
            elif game.phase.value == Phase.GAME_REGISTRATION.value:
                if tac_msg.performative == TacMessage.Performative.GAME_DATA:
                    self._on_start(tac_msg)
                elif tac_msg.performative == TacMessage.Performative.CANCELLED:
                    self._on_cancelled()
            elif game.phase.value == Phase.GAME.value:
                if (
                    tac_msg.performative
                    == TacMessage.Performative.TRANSACTION_CONFIRMATION
                ):
                    self._on_transaction_confirmed(tac_msg)
                elif tac_msg.performative == TacMessage.Performative.CANCELLED:
                    self._on_cancelled()
            elif game.phase.value == Phase.POST_GAME.value:
                raise ValueError(
                    "We do not expect a controller agent message in the post game phase."
                )
        except ValueError as e:
            self.context.logger.warning(str(e))

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass

    def _on_tac_error(self, tac_message: TacMessage) -> None:
        """
        Handle 'on tac error' event emitted by the controller.

        :param tac_message: The tac message.

        :return: None
        """
        error_code = tac_message.error_code
        self.context.logger.debug(
            "[{}]: Received error from the controller. error_msg={}".format(
                self.context.agent_name, TacMessage.ErrorCode.to_msg(error_code.value)
            )
        )
        if error_code == TacMessage.ErrorCode.TRANSACTION_NOT_VALID:
            info = cast(Dict[str, str], tac_message.info)
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

    def _on_start(self, tac_message: TacMessage) -> None:
        """
        Handle the 'start' event emitted by the controller.

        :param tac_message: the game data

        :return: None
        """
        self.context.logger.info(
            "[{}]: Received start event from the controller. Starting to compete...".format(
                self.context.agent_name
            )
        )
        game = cast(Game, self.context.game)
        game.init(tac_message, tac_message.counterparty)
        game.update_game_phase(Phase.GAME)

        if game.is_using_contract:
            contract = cast(ERC1155Contract, self.context.contracts.erc1155)
            contract_address = (
                None
                if tac_message.info is None
                else tac_message.info.get("contract_address")
            )

            if contract_address is not None:
                ledger_api = self.context.ledger_apis.get_api(game.ledger_id)
                contract.set_deployed_instance(
                    ledger_api, contract_address,
                )
                self.context.logger.info(
                    "[{}]: Received a contract address: {}".format(
                        self.context.agent_name, contract_address
                    )
                )
                # TODO; verify on-chain matches off-chain wealth
                self._update_ownership_and_preferences(tac_message)
            else:
                self.context.logger.warning(
                    "[{}]: Did not receive a contract address!".format(
                        self.context.agent_name
                    )
                )
        else:
            self._update_ownership_and_preferences(tac_message)

    def _update_ownership_and_preferences(self, tac_message: TacMessage) -> None:
        """
        Update ownership and preferences.

        :param tac_message: the game data

        :return: None
        """
        state_update_msg = StateUpdateMessage(
            performative=StateUpdateMessage.Performative.INITIALIZE,
            amount_by_currency_id=tac_message.amount_by_currency_id,
            quantities_by_good_id=tac_message.quantities_by_good_id,
            exchange_params_by_currency_id=tac_message.exchange_params_by_currency_id,
            utility_params_by_good_id=tac_message.utility_params_by_good_id,
            tx_fee=tac_message.tx_fee,
        )
        self.context.decision_maker_message_queue.put_nowait(state_update_msg)

    def _on_cancelled(self) -> None:
        """
        Handle the cancellation of the competition from the TAC controller.

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

    def _on_transaction_confirmed(self, message: TacMessage) -> None:
        """
        Handle 'on transaction confirmed' event emitted by the controller.

        :param message: the TacMessage.

        :return: None
        """
        self.context.logger.info(
            "[{}]: Received transaction confirmation from the controller: transaction_id={}".format(
                self.context.agent_name, message.tx_id[-10:]
            )
        )
        state_update_msg = StateUpdateMessage(
            performative=StateUpdateMessage.Performative.APPLY,
            amount_by_currency_id=message.amount_by_currency_id,
            quantities_by_good_id=message.quantities_by_good_id,
        )
        self.context.decision_maker_message_queue.put_nowait(state_update_msg)
        if "confirmed_tx_ids" not in self.context.shared_state.keys():
            self.context.shared_state["confirmed_tx_ids"] = []
        self.context.shared_state["confirmed_tx_ids"].append(message.tx_id)


class TransactionHandler(Handler):
    """This class implements the transaction handler."""

    SUPPORTED_PROTOCOL = TransactionMessage.protocol_id  # type: Optional[ProtocolId]

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
        tx_message = cast(TransactionMessage, message)
        if (
            tx_message.performative
            == TransactionMessage.Performative.SUCCESSFUL_SIGNING
        ):

            # TODO: Need to modify here and add the contract option in case we are using one.

            self.context.logger.info(
                "[{}]: transaction confirmed by decision maker, sending to controller.".format(
                    self.context.agent_name
                )
            )
            game = cast(Game, self.context.game)
            tx_counterparty_signature = cast(
                str, tx_message.info.get("tx_counterparty_signature")
            )
            tx_counterparty_id = cast(str, tx_message.info.get("tx_counterparty_id"))
            if (tx_counterparty_signature is not None) and (
                tx_counterparty_id is not None
            ):
                tx_id = tx_message.tx_id + "_" + tx_counterparty_id
                msg = TacMessage(
                    performative=TacMessage.Performative.TRANSACTION,
                    tx_id=tx_id,
                    tx_sender_addr=tx_message.tx_sender_addr,
                    tx_counterparty_addr=tx_message.tx_counterparty_addr,
                    amount_by_currency_id=tx_message.tx_amount_by_currency_id,
                    tx_sender_fee=tx_message.tx_sender_fee,
                    tx_counterparty_fee=tx_message.tx_counterparty_fee,
                    quantities_by_good_id=tx_message.tx_quantities_by_good_id,
                    tx_sender_signature=tx_message.signed_payload.get("tx_signature"),
                    tx_counterparty_signature=tx_message.info.get(
                        "tx_counterparty_signature"
                    ),
                    tx_nonce=tx_message.info.get("tx_nonce"),
                )
                msg.counterparty = game.conf.controller_addr
                self.context.outbox.put_message(message=msg)
            else:
                self.context.logger.warning(
                    "[{}]: transaction has no counterparty id or signature!".format(
                        self.context.agent_name
                    )
                )
        else:
            self.context.logger.info(
                "[{}]: transaction was not successful.".format(self.context.agent_name)
            )

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass
