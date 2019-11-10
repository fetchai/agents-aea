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

import logging
from typing import List, cast, TYPE_CHECKING

from aea.protocols.base import Message
from aea.protocols.oef.message import OEFMessage
from aea.skills.base import Handler

if TYPE_CHECKING:
    from packages.protocols.tac.message import TACMessage
    from packages.protocols.tac.serialization import TACSerializer
    from packages.skills.tac_control.game import Game, Phase, Transaction
    from packages.skills.tac_control.parameters import Parameters
else:
    from tac_protocol.message import TACMessage
    from tac_protocol.serialization import TACSerializer
    from tac_control_skill.game import Game, Phase, Transaction
    from tac_control_skill.parameters import Parameters


Address = str

logger = logging.getLogger("aea.tac_control_skill")


class TACHandler(Handler):
    """This class handles oef messages."""

    SUPPORTED_PROTOCOL = TACMessage.protocol_id

    def setup(self) -> None:
        """
        Implement the handler setup.

        :return: None
        """
        pass

    def handle(self, message: Message, sender: Address) -> None:
        """
        Handle a register message.

        If the public key is already registered, answer with an error message.

        :param message: the 'get agent state' TACMessage.
        :param sender: the public key of the sender
        :return: None
        """
        tac_message = cast(TACMessage, message)
        tac_type = tac_message.get("type")

        game = cast(Game, self.context.game)

        logger.debug("[{}]: Handling TAC message. type={}".format(self.context.agent_name, tac_type))
        if tac_type == TACMessage.Type.REGISTER and game.phase == Phase.GAME_REGISTRATION:
            self._on_register(tac_message, sender)
        elif tac_type == TACMessage.Type.UNREGISTER and game.phase == Phase.GAME_REGISTRATION:
            self._on_unregister(tac_message, sender)
        elif tac_type == TACMessage.Type.TRANSACTION and game.phase == Phase.GAME:
            self._on_transaction(tac_message, sender)
        else:
            logger.warning("[{}]: TAC Message type not recognized or not permitted.".format(self.context.agent_name))

    def _on_register(self, message: TACMessage, sender: Address) -> None:
        """
        Handle a register message.

        If the public key is not registered, answer with an error message.

        :param message: the 'get agent state' TACMessage.
        :param sender: the public key of the sender
        :return: None
        """
        parameters = cast(Parameters, self.context.parameters)
        agent_name = cast(str, message.get("agent_name"))
        if parameters.whitelist is not set() and agent_name not in parameters.whitelist:
            logger.error("[{}]: Agent name not in whitelist: '{}'".format(self.context.agent_name, agent_name))
            tac_msg = TACMessage(tac_type=TACMessage.Type.TAC_ERROR, error_code=TACMessage.ErrorCode.AGENT_NAME_NOT_IN_WHITELIST)
            tac_bytes = TACSerializer().encode(tac_msg)
            self.context.outbox.put_message(to=sender, sender=self.context.agent_public_key, protocol_id=TACMessage.protocol_id, message=tac_bytes)

        game = cast(Game, self.context.game)
        if sender in game.registration.agent_pbk_to_name:
            logger.error("[{}]: Agent already registered: '{}'".format(self.context.agent_name, game.registration.agent_pbk_to_name[sender]))
            tac_msg = TACMessage(tac_type=TACMessage.Type.TAC_ERROR, error_code=TACMessage.ErrorCode.AGENT_PBK_ALREADY_REGISTERED)
            tac_bytes = TACSerializer().encode(tac_msg)
            self.context.outbox.put_message(to=sender, sender=self.context.agent_public_key, protocol_id=TACMessage.protocol_id, message=tac_bytes)

        if agent_name in game.registration.agent_pbk_to_name.values():
            logger.error("[{}]: Agent with this name already registered: '{}'".format(self.context.agent_name, agent_name))
            tac_msg = TACMessage(tac_type=TACMessage.Type.TAC_ERROR, error_code=TACMessage.ErrorCode.AGENT_NAME_ALREADY_REGISTERED)
            tac_bytes = TACSerializer().encode(tac_msg)
            self.context.outbox.put_message(to=sender, sender=self.context.agent_public_key, protocol_id=TACMessage.protocol_id, message=tac_bytes)

        game.registration.register_agent(sender, agent_name)
        logger.debug("[{}]: Agent registered: '{}'".format(self.context.agent_name, agent_name))

    def _on_unregister(self, message: TACMessage, sender: Address) -> None:
        """
        Handle a unregister message.

        If the public key is not registered, answer with an error message.

        :param message: the 'get agent state' TACMessage.
        :param sender: the public key of the sender
        :return: None
        """
        game = cast(Game, self.context.game)
        if sender not in game.registration.agent_pbk_to_name:
            logger.error("[{}]: Agent not registered: '{}'".format(self.context.agent_name, sender))
            tac_msg = TACMessage(tac_type=TACMessage.Type.TAC_ERROR, error_code=TACMessage.ErrorCode.AGENT_NOT_REGISTERED)
            tac_bytes = TACSerializer().encode(tac_msg)
            self.context.outbox.put_message(to=sender, sender=self.context.agent_public_key, protocol_id=TACMessage.protocol_id, message=tac_bytes)
        else:
            logger.debug("[{}]: Agent unregistered: '{}'".format(self.context.agent_name, game.configuration.agent_pbk_to_name[sender]))
            game.registration.unregister_agent(sender)

    def _on_transaction(self, message: TACMessage, sender: Address) -> None:
        """
        Handle a transaction TACMessage message.

        If the transaction is invalid (e.g. because the state of the game are not consistent), reply with an error.

        :param message: the 'get agent state' TACMessage.
        :param sender: the public key of the sender
        :return: None
        """
        transaction = Transaction.from_message(message, sender)
        logger.debug("[{}]: Handling transaction: {}".format(self.context.agent_name, transaction))

        game = cast(Game, self.context.game)
        # if transaction arrives first time then put it into the pending pool
        if transaction.transaction_id not in game.transactions.pending:
            if game.is_transaction_valid(transaction):
                logger.debug("[{}]: Put transaction TACMessage in the pool: {}".format(self.context.agent_name, transaction.transaction_id))
                game.transactions.add_pending(transaction)
            else:
                self._handle_invalid_transaction(message, sender)
        # if transaction arrives second time then process it
        else:
            pending_tx = game.transactions.pop_pending(transaction.transaction_id)
            if transaction.matches(pending_tx):
                if game.is_transaction_valid(transaction):
                    self._handle_valid_transaction(message, sender, transaction)
                else:
                    self._handle_invalid_transaction(message, sender)
            else:
                self._handle_non_matching_transaction(message, sender)

    def _handle_valid_transaction(self, message: TACMessage, sender: Address, transaction: Transaction) -> None:
        """
        Handle a valid transaction.

        That is:
        - update the game state
        - send a transaction confirmation both to the buyer and the seller.

        :param tx: the transaction.
        :return: None
        """
        game = cast(Game, self.context.game)
        logger.debug("[{}]: Handling valid transaction: {}".format(self.context.agent_name, transaction.transaction_id))
        game.transactions.add_confirmed(transaction)
        game.settle_transaction(transaction)

        # send the transaction confirmation.
        tac_msg = TACMessage(tac_type=TACMessage.Type.TRANSACTION_CONFIRMATION, transaction_id=transaction.transaction_id)
        tac_bytes = TACSerializer().encode(tac_msg)
        self.context.outbox.put_message(to=sender, sender=self.context.public_key, protocol_id=TACMessage.protocol_id, message=tac_bytes)
        self.context.outbox.put_message(to=cast(str, message.get("counterparty")), sender=self.context.agent_public_key, protocol_id=TACMessage.protocol_id, message=tac_bytes)

        # log messages
        logger.debug("[{}]: Transaction '{}' settled successfully.".format(self.context.agent_name, transaction.transaction_id))
        logger.debug("[{}]: Current state:\n{}".format(self.context.agent_name, game.holdings_summary))

    def _handle_invalid_transaction(self, message: TACMessage, sender: Address) -> None:
        """Handle an invalid transaction."""
        tac_msg = TACMessage(tac_type=TACMessage.Type.TAC_ERROR, error_code=TACMessage.ErrorCode.TRANSACTION_NOT_VALID, details={"transaction_id": message.get("transaction_id")})
        tac_bytes = TACSerializer().encode(tac_msg)
        self.context.outbox.put_message(to=sender, sender=self.context.agent_public_key, protocol_id=TACMessage.protocol_id, message=tac_bytes)

    def _handle_non_matching_transaction(self, message: TACMessage, sender: Address) -> None:
        """Handle non-matching transaction."""
        tac_msg = TACMessage(tac_type=TACMessage.Type.TAC_ERROR, error_code=TACMessage.ErrorCode.TRANSACTION_NOT_MATCHING)
        tac_bytes = TACSerializer().encode(tac_msg)
        self.context.outbox.put_message(to=sender, sender=self.context.agent_public_key, protocol_id=TACMessage.protocol_id, message=tac_bytes)


class OEFRegistrationHandler(Handler):
    """Handle the message exchange with the OEF."""

    SUPPORTED_PROTOCOL = OEFMessage.protocol_id

    def setup(self) -> None:
        """
        Implement the handler setup.

        :return: None
        """
        pass

    def handle(self, message: Message, sender: str) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :param sender: the sender
        :return: None
        """
        oef_message = cast(OEFMessage, message)
        oef_type = oef_message.get("type")

        logger.debug("[{}]: Handling OEF message. type={}".format(self.context.agent_name, oef_type))
        if oef_type == OEFMessage.Type.SEARCH_RESULT:
            self._on_search_result(oef_message)
        elif oef_type == OEFMessage.Type.OEF_ERROR:
            self._on_oef_error(oef_message)
        elif oef_type == OEFMessage.Type.DIALOGUE_ERROR:
            self._on_dialogue_error(oef_message)
        else:
            logger.warning("[{}]: OEF Message type not recognized.".format(self.context.agent_name))

    def _on_oef_error(self, oef_error: OEFMessage) -> None:
        """
        Handle an OEF error message.

        :param oef_error: the oef error

        :return: None
        """
        logger.error("[{}]: Received OEF error: answer_id={}, operation={}"
                     .format(self.context.agent_name, oef_error.get("id"), oef_error.get("operation")))

    def _on_dialogue_error(self, dialogue_error: OEFMessage) -> None:
        """
        Handle a dialogue error message.

        :param dialogue_error: the dialogue error message

        :return: None
        """
        logger.error("[{}]: Received Dialogue error: answer_id={}, dialogue_id={}, origin={}"
                     .format(self.context.agent_name, dialogue_error.get("id"), dialogue_error.get("dialogue_id"), dialogue_error.get("origin")))

    def _on_search_result(self, search_result: OEFMessage) -> None:
        """
        Split the search results from the OEF.

        :param search_result: the search result

        :return: None
        """
        # search = cast(Search, self.context.search)
        search_id = search_result.get("id")
        agents = cast(List[str], search_result.get("agents"))
        logger.debug("[{}]: on search result with search_id={} found agents={}".format(self.context.agent_name, search_id, agents))
        # SEARCH SELF
        # if search_id in search.ids_for_tac:
        #     self._on_controller_search_result(agents)
        # else:
        #     logger.debug("[{}]: Unknown search id: search_id={}".format(self.context.agent_name, search_id))

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass
