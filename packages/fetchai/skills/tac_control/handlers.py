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

from typing import cast

from aea.protocols.base import Message
from aea.skills.base import Handler

from packages.fetchai.protocols.oef.message import OEFMessage
from packages.fetchai.protocols.tac.message import TacMessage
from packages.fetchai.protocols.tac.serialization import TacSerializer
from packages.fetchai.skills.tac_control.game import Game, Phase, Transaction
from packages.fetchai.skills.tac_control.parameters import Parameters


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
        Handle a register message.

        If the address is already registered, answer with an error message.

        :param message: the 'get agent state' TacMessage.
        :return: None
        """
        tac_message = cast(TacMessage, message)

        game = cast(Game, self.context.game)

        self.context.logger.debug(
            "[{}]: Handling TAC message. performative={}".format(
                self.context.agent_name, tac_message.performative
            )
        )
        if (
            tac_message.performative == TacMessage.Performative.REGISTER
            and game.phase == Phase.GAME_REGISTRATION
        ):
            self._on_register(tac_message)
        elif (
            tac_message.performative == TacMessage.Performative.UNREGISTER
            and game.phase == Phase.GAME_REGISTRATION
        ):
            self._on_unregister(tac_message)
        elif (
            tac_message.performative == TacMessage.Performative.TRANSACTION
            and game.phase == Phase.GAME
        ):
            self._on_transaction(tac_message)
        else:
            self.context.logger.warning(
                "[{}]: TAC Message performative not recognized or not permitted.".format(
                    self.context.agent_name
                )
            )

    def _on_register(self, message: TacMessage) -> None:
        """
        Handle a register message.

        If the address is not registered, answer with an error message.

        :param message: the 'get agent state' TacMessage.
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
            tac_msg = TacMessage(
                performative=TacMessage.Performative.TAC_ERROR,
                error_code=TacMessage.ErrorCode.AGENT_NAME_NOT_IN_WHITELIST,
            )
            self.context.outbox.put_message(
                to=message.counterparty,
                sender=self.context.agent_address,
                protocol_id=TacMessage.protocol_id,
                message=TacSerializer().encode(tac_msg),
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
            tac_msg = TacMessage(
                performative=TacMessage.Performative.TAC_ERROR,
                error_code=TacMessage.ErrorCode.AGENT_ADDR_ALREADY_REGISTERED,
            )
            self.context.outbox.put_message(
                to=message.counterparty,
                sender=self.context.agent_address,
                protocol_id=TacMessage.protocol_id,
                message=TacSerializer().encode(tac_msg),
            )

        if agent_name in game.registration.agent_addr_to_name.values():
            self.context.logger.error(
                "[{}]: Agent with this name already registered: '{}'".format(
                    self.context.agent_name, agent_name
                )
            )
            tac_msg = TacMessage(
                performative=TacMessage.Performative.TAC_ERROR,
                error_code=TacMessage.ErrorCode.AGENT_NAME_ALREADY_REGISTERED,
            )
            self.context.outbox.put_message(
                to=message.counterparty,
                sender=self.context.agent_address,
                protocol_id=TacMessage.protocol_id,
                message=TacSerializer().encode(tac_msg),
            )

        game.registration.register_agent(message.counterparty, agent_name)
        self.context.logger.info(
            "[{}]: Agent registered: '{}'".format(self.context.agent_name, agent_name)
        )

    def _on_unregister(self, message: TacMessage) -> None:
        """
        Handle a unregister message.

        If the address is not registered, answer with an error message.

        :param message: the 'get agent state' TacMessage.
        :return: None
        """
        game = cast(Game, self.context.game)
        if message.counterparty not in game.registration.agent_addr_to_name:
            self.context.logger.error(
                "[{}]: Agent not registered: '{}'".format(
                    self.context.agent_name, message.counterparty
                )
            )
            tac_msg = TacMessage(
                performative=TacMessage.Performative.TAC_ERROR,
                error_code=TacMessage.ErrorCode.AGENT_NOT_REGISTERED,
            )
            self.context.outbox.put_message(
                to=message.counterparty,
                sender=self.context.agent_address,
                protocol_id=TacMessage.protocol_id,
                message=TacSerializer().encode(tac_msg),
            )
        else:
            self.context.logger.debug(
                "[{}]: Agent unregistered: '{}'".format(
                    self.context.agent_name,
                    game.configuration.agent_addr_to_name[message.counterparty],
                )
            )
            game.registration.unregister_agent(message.counterparty)

    def _on_transaction(self, message: TacMessage) -> None:
        """
        Handle a transaction TacMessage message.

        If the transaction is invalid (e.g. because the state of the game are not consistent), reply with an error.

        :param message: the 'get agent state' TacMessage.
        :return: None
        """
        transaction = Transaction.from_message(message)
        self.context.logger.debug(
            "[{}]: Handling transaction: {}".format(
                self.context.agent_name, transaction
            )
        )

        game = cast(Game, self.context.game)
        if game.is_transaction_valid(transaction):
            self._handle_valid_transaction(message, transaction)
        else:
            self._handle_invalid_transaction(message)

    def _handle_valid_transaction(
        self, message: TacMessage, transaction: Transaction
    ) -> None:
        """
        Handle a valid transaction.

        That is:
        - update the game state
        - send a transaction confirmation both to the buyer and the seller.

        :param transaction: the transaction.
        :return: None
        """
        game = cast(Game, self.context.game)
        self.context.logger.info(
            "[{}]: Handling valid transaction: {}".format(
                self.context.agent_name, transaction.id[-10:]
            )
        )
        game.settle_transaction(transaction)

        tx_sender_id, tx_counterparty_id = transaction.id.split("_")
        # send the transaction confirmation.
        sender_tac_msg = TacMessage(
            performative=TacMessage.Performative.TRANSACTION_CONFIRMATION,
            tx_id=tx_sender_id,
            amount_by_currency_id=transaction.amount_by_currency_id,
            quantities_by_good_id=transaction.quantities_by_good_id,
        )
        counterparty_tac_msg = TacMessage(
            performative=TacMessage.Performative.TRANSACTION_CONFIRMATION,
            tx_id=tx_counterparty_id,
            amount_by_currency_id=transaction.amount_by_currency_id,
            quantities_by_good_id=transaction.quantities_by_good_id,
        )
        self.context.outbox.put_message(
            to=transaction.sender_addr,
            sender=self.context.agent_address,
            protocol_id=TacMessage.protocol_id,
            message=TacSerializer().encode(sender_tac_msg),
        )
        self.context.outbox.put_message(
            to=transaction.counterparty_addr,
            sender=self.context.agent_address,
            protocol_id=TacMessage.protocol_id,
            message=TacSerializer().encode(counterparty_tac_msg),
        )

        # log messages
        self.context.logger.info(
            "[{}]: Transaction '{}' settled successfully.".format(
                self.context.agent_name, transaction.id[-10:]
            )
        )
        self.context.logger.info(
            "[{}]: Current state:\n{}".format(
                self.context.agent_name, game.holdings_summary
            )
        )

    def _handle_invalid_transaction(self, message: TacMessage) -> None:
        """Handle an invalid transaction."""
        tx_id = message.tx_id[-10:]
        self.context.logger.info(
            "[{}]: Handling invalid transaction: {}".format(
                self.context.agent_name, tx_id
            )
        )
        tac_msg = TacMessage(
            performative=TacMessage.Performative.TAC_ERROR,
            error_code=TacMessage.ErrorCode.TRANSACTION_NOT_VALID,
            info={"transaction_id": message.tx_id},
        )
        self.context.outbox.put_message(
            to=message.counterparty,
            sender=self.context.agent_address,
            protocol_id=TacMessage.protocol_id,
            message=TacSerializer().encode(tac_msg),
        )

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
