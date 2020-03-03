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

"""This package contains a scaffold of a handler."""
from typing import Optional, cast

from aea.configurations.base import ProtocolId
from aea.decision_maker.messages.transaction import TransactionMessage
from aea.protocols.base import Message
from aea.skills.base import Handler


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
        if tx_msg_response.tx_id == "contract_deploy":
            tx_signed = tx_msg_response.signed_payload.get("tx_signed")
            ledger_api = self.context.ledger_apis.apis.get("ethereum")
            result = ledger_api.send_signed_transaction(  # type: ignore
                True, tx_signed
            )
            self.context.logger.info(result)
            contract.set_address(ledger_api, result)
            self.context.logger.info(contract.is_deployed)
        elif tx_msg_response.tx_id == "contract_create_batch":
            ledger_api = self.context.ledger_apis.apis.get("ethereum")
            result = ledger_api.send_raw_transaction(  # type: ignore
                tx_msg_response.signed_payload.get("tx_signed")
            )
            self.context.logger.info(result)
        elif tx_msg_response.tx_id == "contract_mint_batch":
            ledger_api = self.context.ledger_apis.apis.get("ethereum")
            result = ledger_api.send_raw_transaction(  # type: ignore
                tx_msg_response.signed_payload.get("tx_signed")
            )
            self.context.logger.info(result)
            contract.is_items_created = True
            self.context.logger.info("Ask the contract about my balances:")
            result = contract.get_balance_of_batch(address=self.context.agent_address)
            self.context.logger.info(result)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass
