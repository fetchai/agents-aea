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

"""This package contains the handlers of a generic seller AEA."""
import json
from typing import Optional, cast

from aea.configurations.base import ProtocolId
from aea.decision_maker.messages.transaction import TransactionMessage
from aea.protocols.base import Message
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer
from aea.skills.base import Handler


class DefaultHandler(Handler):
    """This class implements a FIPA handler."""

    SUPPORTED_PROTOCOL = DefaultMessage.protocol_id  # type: Optional[ProtocolId]

    def setup(self) -> None:
        """Implement the setup for the handler."""
        pass

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :return: None
        """
        # convenience representations
        msg = cast(DefaultMessage, message)
        content = json.loads(msg.content)
        contract = self.context.contracts.erc1155
        self.context.logger.info(content)
        if "command" in content:
            if "contractAddress" in content.keys():
                json_data = {"command": "contract_address",
                             "address": contract.address}
                msg = DefaultMessage(type=DefaultMessage.Type.BYTES,
                                     content=json_data)
                json_bytes = json.dumps(msg).encode('utf8')
                msg = DefaultMessage(type=DefaultMessage.Type.BYTES, content=json_bytes)
                self.context.logger.info("Sending response to {}".format(message.counterparty))
                self.context.outbox.put_message(
                    to=message.counterparty,
                    sender=self.context.agent_address,
                    protocol_id=DefaultMessage.protocol_id,
                    message=DefaultSerializer().encode(msg),
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
        if tx_msg_response.tx_id == "contract_deploy":
            tx_signed = tx_msg_response.signed_payload.get("tx_signed")
            ledger_api = self.context.ledger_apis.apis.get("ethereum")
            tx_digest = ledger_api.send_signed_transaction(is_waiting_for_confirmation= True,
                                                           tx_signed=tx_signed)
            transaction = ledger_api.get_transaction_status(  # type: ignore
                tx_digest=tx_digest
            )
            self.context.logger.info(transaction)
            contract.set_address(ledger_api, transaction.contractAddress)
            self.context.logger.info(contract.is_deployed)
        elif tx_msg_response.tx_id == "contract_create_batch":
            tx_signed = tx_msg_response.signed_payload.get("tx_signed")
            ledger_api = self.context.ledger_apis.apis.get("ethereum")
            ledger_api.send_signed_transaction(is_waiting_for_confirmation=True,
                                               tx_signed=tx_signed)
            self.context.logger.info("Created the items.")
        elif tx_msg_response.tx_id == "contract_mint_batch":
            tx_signed = tx_msg_response.signed_payload.get("tx_signed")
            ledger_api = self.context.ledger_apis.apis.get("ethereum")
            ledger_api.send_signed_transaction(is_waiting_for_confirmation=True,
                                               tx_signed=tx_signed)
            self.context.logger.info("Ask the contract about my balances:")
            result = contract.get_balance_of_batch(address=self.context.agent_address)
            self.context.logger.info(result)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass
