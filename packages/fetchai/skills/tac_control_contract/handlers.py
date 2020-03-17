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

from aea.configurations.base import ProtocolId
from aea.crypto.base import LedgerApi
from aea.decision_maker.messages.transaction import TransactionMessage
from aea.protocols.base import Message
from aea.skills.base import Handler

from packages.fetchai.protocols.oef.message import OEFMessage
from packages.fetchai.protocols.tac.message import TACMessage
from packages.fetchai.protocols.tac.serialization import TACSerializer
from packages.fetchai.skills.tac_control_contract.game import Game, Phase
from packages.fetchai.skills.tac_control_contract.parameters import Parameters


class TACHandler(Handler):
    """This class handles oef messages."""

    SUPPORTED_PROTOCOL = TACMessage.protocol_id

    def setup(self) -> None:
        """
        Implement the handler setup.

        :return: None
        """
        pass

    def handle(self, message: Message) -> None:
        """
        Handle a register message.

        If the address is already registered, answer with an error message.

        :param message: the 'get agent state' TACMessage.
        :return: None
        """
        tac_message = cast(TACMessage, message)
        tac_type = tac_message.type

        game = cast(Game, self.context.game)

        self.context.logger.debug(
            "[{}]: Handling TAC message. type={}".format(
                self.context.agent_name, tac_type
            )
        )
        if (
            tac_type == TACMessage.Type.REGISTER
            and game.phase == Phase.GAME_REGISTRATION
        ):
            self._on_register(tac_message)
        elif (
            tac_type == TACMessage.Type.UNREGISTER
            and game.phase == Phase.GAME_REGISTRATION
        ):
            self._on_unregister(tac_message)
        else:
            self.context.logger.warning(
                "[{}]: TAC Message type not recognized or not permitted.".format(
                    self.context.agent_name
                )
            )

    def _on_register(self, message: TACMessage) -> None:
        """
        Handle a register message.

        If the address is not registered, answer with an error message.

        :param message: the 'get agent state' TACMessage.
        :return: None
        """
        parameters = cast(Parameters, self.context.parameters)
        agent_name = message.agent_name
        if len(parameters.whitelist) != 0 and agent_name not in parameters.whitelist:
            self.context.logger.error(
                "[{}]: Agent name not in whitelist: '{}'".format(
                    self.context.agent_name, agent_name
                )
            )
            tac_msg = TACMessage(
                type=TACMessage.Type.TAC_ERROR,
                error_code=TACMessage.ErrorCode.AGENT_NAME_NOT_IN_WHITELIST,
            )
            self.context.outbox.put_message(
                to=message.counterparty,
                sender=self.context.agent_address,
                protocol_id=TACMessage.protocol_id,
                message=TACSerializer().encode(tac_msg),
            )
            return

        game = cast(Game, self.context.game)
        if message.counterparty in game.registration.agent_addr_to_name:
            self.context.logger.error(
                "[{}]: Agent already registered: '{}'".format(
                    self.context.agent_name,
                    game.registration.agent_addr_to_name[message.counterparty],
                )
            )
            tac_msg = TACMessage(
                type=TACMessage.Type.TAC_ERROR,
                error_code=TACMessage.ErrorCode.AGENT_ADDR_ALREADY_REGISTERED,
            )
            self.context.outbox.put_message(
                to=message.counterparty,
                sender=self.context.agent_address,
                protocol_id=TACMessage.protocol_id,
                message=TACSerializer().encode(tac_msg),
            )

        if agent_name in game.registration.agent_addr_to_name.values():
            self.context.logger.error(
                "[{}]: Agent with this name already registered: '{}'".format(
                    self.context.agent_name, agent_name
                )
            )
            tac_msg = TACMessage(
                type=TACMessage.Type.TAC_ERROR,
                error_code=TACMessage.ErrorCode.AGENT_NAME_ALREADY_REGISTERED,
            )
            self.context.outbox.put_message(
                to=message.counterparty,
                sender=self.context.agent_address,
                protocol_id=TACMessage.protocol_id,
                message=TACSerializer().encode(tac_msg),
            )

        game.registration.register_agent(message.counterparty, agent_name)
        self.context.logger.info(
            "[{}]: Agent registered: '{}'".format(self.context.agent_name, agent_name)
        )

    def _on_unregister(self, message: TACMessage) -> None:
        """
        Handle a unregister message.

        If the address is not registered, answer with an error message.

        :param message: the 'get agent state' TACMessage.
        :return: None
        """
        game = cast(Game, self.context.game)
        if message.counterparty not in game.registration.agent_addr_to_name:
            self.context.logger.error(
                "[{}]: Agent not registered: '{}'".format(
                    self.context.agent_name, message.counterparty
                )
            )
            tac_msg = TACMessage(
                type=TACMessage.Type.TAC_ERROR,
                error_code=TACMessage.ErrorCode.AGENT_NOT_REGISTERED,
            )
            self.context.outbox.put_message(
                to=message.counterparty,
                sender=self.context.agent_address,
                protocol_id=TACMessage.protocol_id,
                message=TACSerializer().encode(tac_msg),
            )
        else:
            self.context.logger.debug(
                "[{}]: Agent unregistered: '{}'".format(
                    self.context.agent_name,
                    game.configuration.agent_addr_to_name[message.counterparty],
                )
            )
            game.registration.unregister_agent(message.counterparty)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass


class OEFRegistrationHandler(Handler):
    """Handle the message exchange with the OEF."""

    SUPPORTED_PROTOCOL = OEFMessage.protocol_id

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
        oef_message = cast(OEFMessage, message)
        oef_type = oef_message.type

        self.context.logger.debug(
            "[{}]: Handling OEF message. type={}".format(
                self.context.agent_name, oef_type
            )
        )
        if oef_type == OEFMessage.Type.OEF_ERROR:
            self._on_oef_error(oef_message)
        elif oef_type == OEFMessage.Type.DIALOGUE_ERROR:
            self._on_dialogue_error(oef_message)
        else:
            self.context.logger.warning(
                "[{}]: OEF Message type not recognized.".format(self.context.agent_name)
            )

    def _on_oef_error(self, oef_error: OEFMessage) -> None:
        """
        Handle an OEF error message.

        :param oef_error: the oef error

        :return: None
        """
        self.context.logger.error(
            "[{}]: Received OEF error: answer_id={}, operation={}".format(
                self.context.agent_name, oef_error.id, oef_error.operation
            )
        )

    def _on_dialogue_error(self, dialogue_error: OEFMessage) -> None:
        """
        Handle a dialogue error message.

        :param dialogue_error: the dialogue error message

        :return: None
        """
        self.context.logger.error(
            "[{}]: Received Dialogue error: answer_id={}, dialogue_id={}, origin={}".format(
                self.context.agent_name,
                dialogue_error.id,
                dialogue_error.dialogue_id,
                dialogue_error.origin,
            )
        )

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass


class TransactionHandler(Handler):
    """Implement the transaction handler."""

    SUPPORTED_PROTOCOL = TransactionMessage.protocol_id  # type: Optional[ProtocolId]

    def setup(self) -> None:
        """Implement the setup for the handler."""
        pass

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :return: None
        """
        tx_msg_response = cast(TransactionMessage, message)
        contract = self.context.contracts.erc1155
        ledger_api = cast(LedgerApi, self.context.ledger_apis.apis.get("ethereum"))
        if tx_msg_response.tx_id == "contract_deploy":
            self.context.logger.info("Sending deployment transaction to the ledger!")
            tx_signed = tx_msg_response.signed_payload.get("tx_signed")
            tx_digest = ledger_api.send_signed_transaction(
                is_waiting_for_confirmation=True, tx_signed=tx_signed
            )
            transaction = ledger_api.get_transaction_status(  # type: ignore
                tx_digest=tx_digest
            )
            if transaction.status != 1:
                self.context.is_active = False
                self.context.info(
                    "The contract did not deployed successfully aborting."
                )
            else:
                self.context.logger.info(
                    "The contract was successfully deployed. Contract address: {} and transaction hash: {}".format(
                        transaction.contractAddress, transaction.transactionHash.hex()
                    )
                )
                contract.set_address(ledger_api, transaction.contractAddress)
        elif (
            tx_msg_response.tx_id == "contract_create_batch"
            or tx_msg_response.tx_id == "contract_create_single"
        ):
            self.context.logger.info("Sending creation transaction to the ledger!")
            tx_signed = tx_msg_response.signed_payload.get("tx_signed")
            ledger_api = cast(LedgerApi, self.context.ledger_apis.apis.get("ethereum"))
            tx_digest = ledger_api.send_signed_transaction(
                is_waiting_for_confirmation=True, tx_signed=tx_signed
            )
            transaction = ledger_api.get_transaction_status(  # type: ignore
                tx_digest=tx_digest
            )
            if transaction.status != 1:
                self.context.is_active = False
                self.context.info("The creation command wasn't successful. Aborting.")
            else:
                self.context.shared_state["is_items_created"] = True
                self.context.logger.info(tx_msg_response.tx_id)
                self._mint_objects(is_batch=True)
                self.context.logger.info(
                    "Successfully created the items. Transaction hash: {}".format(
                        transaction.transactionHash.hex()
                    )
                )
        elif tx_msg_response.tx_id == "contract_mint_batch":
            self.context.logger.info("Sending minting transaction to the ledger!")
            tx_signed = tx_msg_response.signed_payload.get("tx_signed")
            ledger_api = cast(LedgerApi, self.context.ledger_apis.apis.get("ethereum"))
            tx_digest = ledger_api.send_signed_transaction(
                is_waiting_for_confirmation=True, tx_signed=tx_signed
            )
            transaction = ledger_api.get_transaction_status(  # type: ignore
                tx_digest=tx_digest
            )
            if transaction.status != 1:
                self.context.is_active = False
                self.context.logger.info(
                    "The mint command wasn't successful. Aborting."
                )
                self.context.logger.info(transaction)
            else:

                self.context.logger.info(
                    "Successfully minted the items. Transaction hash: {}".format(
                        transaction.transactionHash.hex()
                    )
                )

                if (
                    self.context.shared_state["agents_total_participants"]
                    == self.context.shared_state["agents_participants_counter"]
                ):
                    self.context.logger.info("Can start the game.!")
                    self.context.shared_state["can_start"] = True

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass

    def _mint_objects(self, is_batch: bool, token_id: int = None):
        self.context.logger.info("Minting the items")
        contract = self.context.contracts.erc1155
        parameters = cast(Parameters, self.context.parameters)
        if is_batch:
            minting = [parameters.base_good_endowment] * parameters.nb_goods
            transaction_message = contract.get_mint_batch_transaction(
                deployer_address=self.context.agent_address,
                recipient_address=self.context.agent_address,
                mint_quantities=minting,
                ledger_api=self.context.ledger_apis.apis.get("ethereum"),
                skill_callback_id=self.context.skill_id,
                token_ids=self.context.shared_state["token_ids"],
            )
            self.context.decision_maker_message_queue.put_nowait(transaction_message)
        else:
            self.context.logger.info("Minting the game currency")
            contract = self.context.contracts.erc1155
            parameters = cast(Parameters, self.context.parameters)
            transaction_message = contract.get_mint_single_tx(
                deployer_address=self.context.agent_address,
                recipient_address=self.context.agent_address,
                mint_quantity=parameters.money_endowment,
                ledger_api=self.context.ledger_apis.apis.get("ethereum"),
                skill_callback_id=self.context.skill_id,
                token_id=self.context.shared_state["token_ids"][0],
            )
            self.context.decision_maker_message_queue.put_nowait(transaction_message)
