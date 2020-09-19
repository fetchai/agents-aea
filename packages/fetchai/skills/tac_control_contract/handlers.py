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
from aea.protocols.signing.message import SigningMessage
from aea.skills.base import Handler

from packages.fetchai.skills.tac_control.handlers import (
    OefSearchHandler as BaseOefSearchHandler,
)
from packages.fetchai.skills.tac_control.handlers import TacHandler as BaseTacHandler
from packages.fetchai.skills.tac_control_contract.game import Game, Phase
from packages.fetchai.skills.tac_control_contract.parameters import Parameters


TacHandler = BaseTacHandler


OefSearchHandler = BaseOefSearchHandler


class SigningHandler(Handler):
    """Implement the transaction handler."""

    SUPPORTED_PROTOCOL = SigningMessage.protocol_id

    def setup(self) -> None:
        """Implement the setup for the handler."""
        pass

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :return: None
        """
        signing_msg_response = cast(SigningMessage, message)
        game = cast(Game, self.context.game)
        parameters = cast(Parameters, self.context.parameters)
        ledger_api = self.context.ledger_apis.get_api(parameters.ledger)
        if signing_msg_response.dialogue_reference[0] == "contract_deploy":
            game.phase = Phase.CONTRACT_DEPLOYING
            self.context.logger.info("sending deployment transaction to the ledger...")
            tx_signed = signing_msg_response.signed_transaction
            tx_digest = ledger_api.send_signed_transaction(tx_signed=tx_signed)
            if tx_digest is None:
                self.context.logger.warning("sending transaction failed. Aborting!")
                self.context.is_active = False
            else:
                game.contract_manager.deploy_tx_digest = tx_digest
        elif signing_msg_response.dialogue_reference[0] == "contract_create_batch":
            game.phase = Phase.TOKENS_CREATING
            self.context.logger.info("sending creation transaction to the ledger...")
            tx_signed = signing_msg_response.signed_transaction
            tx_digest = ledger_api.send_signed_transaction(tx_signed=tx_signed)
            if tx_digest is None:
                self.context.logger.warning("sending transaction failed. Aborting!")
                self.context.is_active = False
            else:
                game.contract_manager.create_tokens_tx_digest = tx_digest
        elif signing_msg_response.dialogue_reference[0] == "contract_mint_batch":
            game.phase = Phase.TOKENS_MINTING
            self.context.logger.info("sending minting transaction to the ledger...")
            tx_signed = signing_msg_response.signed_transaction
            agent_addr = signing_msg_response.terms.counterparty_address
            tx_digest = ledger_api.send_signed_transaction(tx_signed=tx_signed)
            if tx_digest is None:
                self.context.logger.warning("sending transaction failed. Aborting!")
                self.context.is_active = False
            else:
                game.contract_manager.set_mint_tokens_tx_digest(agent_addr, tx_digest)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass
