# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2020 Fetch.AI Limited
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

"""This package contains the handlers of the erc1155 deploy skill AEA."""

from typing import Optional, cast

from aea.configurations.base import ProtocolId
from aea.crypto.base import LedgerApi
from aea.decision_maker.messages.transaction import TransactionMessage
from aea.protocols.base import Message
from aea.skills.base import Handler

from packages.fetchai.protocols.fipa.message import FIPAMessage
from packages.fetchai.protocols.fipa.serialization import FIPASerializer
from packages.fetchai.skills.erc1155_deploy.strategy import Strategy


class FIPAHandler(Handler):
    """This class implements a FIPA handler."""

    SUPPORTED_PROTOCOL = FIPAMessage.protocol_id  # type: Optional[ProtocolId]

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
        fipa_msg = cast(FIPAMessage, message)

        # handle message
        if fipa_msg.performative == FIPAMessage.Performative.CFP:
            self._handle_cfp(fipa_msg)
        elif fipa_msg.performative == FIPAMessage.Performative.INFORM:
            self._handle_inform(fipa_msg)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass

    def _handle_cfp(self, msg: FIPAMessage) -> None:
        """
        Handle the CFP.

        If the CFP matches the supplied services then send a PROPOSE, otherwise send a DECLINE.

        :param msg: the message
        :return: None
        """
        new_message_id = msg.message_id + 1
        new_target = msg.message_id
        self.context.logger.info(
            "[{}]: received CFP from sender={}".format(
                self.context.agent_name, msg.counterparty[-5:]
            )
        )
        strategy = cast(Strategy, self.context.strategy)
        contract = self.context.contracts.erc1155
        self.context.logger.info(contract.item_ids)
        contract_nonce = contract.generate_trade_nonce(self.context.agent_address)
        self.context.shared_state["contract_nonce"] = contract_nonce
        info_msg = FIPAMessage(
            message_id=new_message_id,
            dialogue_reference=("", ""),
            target=new_target,
            performative=FIPAMessage.Performative.INFORM,
            info={
                "contract": contract.instance.address,
                "item_ids": contract.item_ids,
                "trade_nonce": contract_nonce,
                "from_supply": strategy.from_supply,
                "to_supply": strategy.to_supply,
                "value": strategy.value,
            },
        )

        self.context.outbox.put_message(
            to=msg.counterparty,
            sender=self.context.agent_address,
            protocol_id=FIPAMessage.protocol_id,
            message=FIPASerializer().encode(info_msg),
        )

    def _handle_inform(self, msg: FIPAMessage) -> None:
        """
        Handle the INFORM.

        If the INFORM message contains the transaction_digest then verify that it is settled, otherwise do nothing.
        If the transaction is settled, send the data, otherwise do nothing.

        :param msg: the message
        :return: None
        """
        self.context.logger.info(
            "[{}]: received INFORM from sender={}".format(
                self.context.agent_name, msg.counterparty[-5:]
            )
        )
        self.context.logger.info(self.context.ledger_apis.apis.get("ethereum"))
        strategy = cast(Strategy, self.context.strategy)
        contract = self.context.contracts.erc1155
        contract_nonce = cast(int, self.context.shared_state.get("contract_nonce"))
        tx = contract.get_atomic_swap_single_proposal(
            from_address=self.context.agent_address,
            to_address=msg.counterparty,
            item_id=contract.item_ids[0],
            from_supply=strategy.from_supply,
            to_supply=strategy.to_supply,
            value=strategy.value,
            trade_nonce=contract_nonce,
            ledger_api=self.context.ledger_apis.apis.get("ethereum"),
            skill_callback_id=self.context.skill_id,
            signature=msg.info.get("signature"),
        )

        self.context.decision_maker_message_queue.put(tx)


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
        tx_digest = ""
        if tx_msg_response.tx_id == "contract_deploy":
            tx_signed = tx_msg_response.signed_payload.get("tx_signed")
            tx_digest = ledger_api.send_signed_transaction(
                is_waiting_for_confirmation=True, tx_signed=tx_signed
            )
            transaction = ledger_api.get_transaction_status(  # type: ignore
                tx_digest=tx_digest
            )
            self.context.logger.info(transaction)
            contract.set_address(ledger_api, transaction.contractAddress)
            self.context.logger.info(contract.is_deployed)
        elif tx_msg_response.tx_id == "contract_create_batch":
            tx_signed = tx_msg_response.signed_payload.get("tx_signed")
            ledger_api = cast(LedgerApi, self.context.ledger_apis.apis.get("ethereum"))
            tx_digest = ledger_api.send_signed_transaction(
                is_waiting_for_confirmation=True, tx_signed=tx_signed
            )
            self.context.logger.info(
                "Transaction digest for creating items: {}".format(tx_digest)
            )
        elif tx_msg_response.tx_id == "contract_mint_batch":
            tx_signed = tx_msg_response.signed_payload.get("tx_signed")
            ledger_api = cast(LedgerApi, self.context.ledger_apis.apis.get("ethereum"))
            tx_digest = ledger_api.send_signed_transaction(
                is_waiting_for_confirmation=True, tx_signed=tx_signed
            )
            self.context.logger.info(
                "Transaction digest for minting objects: {}".format(tx_digest)
            )
            self.context.logger.info("Ask the contract about my balances:")
            result = contract.get_balance_of_batch(address=self.context.agent_address)
            self.context.logger.info(result)
        elif tx_msg_response.tx_id == "contract_atomic_swap_single":
            self.context.logger.info("Sending the trade transaction.")
            tx_signed = tx_msg_response.signed_payload.get("tx_signed")
            ledger_api = cast(LedgerApi, self.context.ledger_apis.apis.get("ethereum"))
            tx_digest = ledger_api.send_signed_transaction(
                is_waiting_for_confirmation=True, tx_signed=tx_signed
            )
            self.context.logger.info(
                "Transaction digest for atomic_swap: {}".format(tx_digest)
            )
            self.context.logger.info("Ask the contract about my balances:")
            result = contract.get_balance_of_batch(address=self.context.agent_address)
            self.context.logger.info(result)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass
