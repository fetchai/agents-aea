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
from aea.decision_maker.messages.transaction import TransactionMessage
from aea.protocols.base import Message
from aea.skills.base import Handler

from packages.fetchai.contracts.erc1155.contract import ERC1155Contract
from packages.fetchai.protocols.fipa.message import FipaMessage
from packages.fetchai.protocols.fipa.serialization import FipaSerializer
from packages.fetchai.skills.erc1155_deploy.strategy import Strategy


class FIPAHandler(Handler):
    """This class implements a FIPA handler."""

    SUPPORTED_PROTOCOL = FipaMessage.protocol_id  # type: Optional[ProtocolId]

    def setup(self) -> None:
        """Implement the setup for the handler."""
        pass

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :return: None
        """
        fipa_msg = cast(FipaMessage, message)

        if fipa_msg.performative == FipaMessage.Performative.CFP:
            self._handle_cfp(fipa_msg)
        elif fipa_msg.performative == FipaMessage.Performative.INFORM:
            self._handle_inform(fipa_msg)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass

    def _handle_cfp(self, msg: FipaMessage) -> None:
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
        if self.context.behaviours.service_registration.is_items_minted:
            strategy = cast(Strategy, self.context.strategy)
            contract = cast(ERC1155Contract, self.context.contracts.erc1155)
            contract_nonce = contract.generate_trade_nonce(self.context.agent_address)
            self.context.shared_state["contract_nonce"] = contract_nonce
            self.token_id = self.context.behaviours.service_registration.token_ids[0]
            info_msg = FipaMessage(
                message_id=new_message_id,
                dialogue_reference=("", ""),
                target=new_target,
                performative=FipaMessage.Performative.INFORM,
                info={
                    "contract": contract.instance.address,
                    "token_id": self.token_id,
                    "trade_nonce": contract_nonce,
                    "from_supply": strategy.from_supply,
                    "to_supply": strategy.to_supply,
                    "value": strategy.value,
                },
            )
            self.context.logger.info("Sending proposal.")
            self.context.outbox.put_message(
                to=msg.counterparty,
                sender=self.context.agent_address,
                protocol_id=FipaMessage.protocol_id,
                message=FipaSerializer().encode(info_msg),
            )
        else:
            self.context.logger.info("Contract items not minted yet.")

    def _handle_inform(self, msg: FipaMessage) -> None:
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
        signature = msg.info.get("signature", None)
        if signature is not None:
            strategy = cast(Strategy, self.context.strategy)
            contract = cast(ERC1155Contract, self.context.contracts.erc1155)
            contract_nonce = cast(int, self.context.shared_state.get("contract_nonce"))
            tx = contract.get_atomic_swap_single_proposal(
                from_address=self.context.agent_address,
                to_address=msg.counterparty,
                item_id=self.token_id,
                from_supply=strategy.from_supply,
                to_supply=strategy.to_supply,
                value=strategy.value,
                trade_nonce=contract_nonce,
                ledger_api=self.context.ledger_apis.ethereum_api,
                skill_callback_id=self.context.skill_id,
                signature=signature,
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
        contract = cast(ERC1155Contract, self.context.contracts.erc1155)
        if tx_msg_response.tx_id == contract.Performative.CONTRACT_DEPLOY.value:
            tx_signed = tx_msg_response.signed_payload.get("tx_signed")
            tx_digest = self.context.ledger_apis.ethereum_api.send_signed_transaction(
                is_waiting_for_confirmation=True, tx_signed=tx_signed
            )
            transaction = self.context.ledger_apis.ethereum_api.get_transaction_status(  # type: ignore
                tx_digest=tx_digest
            )
            if transaction.status != 1:
                self.context.is_active = False
                self.context.logger.info("Failed to deploy. Aborting...")
            else:
                contract.set_address(
                    self.context.ledger_apis.ethereum_api, transaction.contractAddress
                )
                self.context.logger.info("Successfully deployed the contract.")

        elif tx_msg_response.tx_id == contract.Performative.CONTRACT_CREATE_BATCH.value:
            tx_signed = tx_msg_response.signed_payload.get("tx_signed")
            tx_digest = self.context.ledger_apis.ethereum_api.send_signed_transaction(
                is_waiting_for_confirmation=True, tx_signed=tx_signed
            )
            transaction = self.context.ledger_apis.ethereum_api.get_transaction_status(  # type: ignore
                tx_digest=tx_digest
            )
            if transaction.status != 1:
                self.context.is_active = False
                self.context.logger.info("Failed to create items. Aborting...")
            else:
                self.context.behaviours.service_registration.is_items_created = True
                self.context.logger.info(
                    "Successfully created items. Transaction digest: {}".format(
                        tx_digest
                    )
                )
        elif tx_msg_response.tx_id == contract.Performative.CONTRACT_MINT_BATCH.value:
            tx_signed = tx_msg_response.signed_payload.get("tx_signed")
            tx_digest = self.context.ledger_apis.ethereum_api.send_signed_transaction(
                is_waiting_for_confirmation=True, tx_signed=tx_signed
            )
            transaction = self.context.ledger_apis.ethereum_api.get_transaction_status(  # type: ignore
                tx_digest=tx_digest
            )
            if transaction.status != 1:
                self.context.is_active = False
                self.context.logger.info("Failed to mint items. Aborting...")
            else:
                self.context.behaviours.service_registration.is_items_minted = True
                self.context.logger.info(
                    "Successfully minted items. Transaction digest: {}".format(
                        tx_digest
                    )
                )
                result = contract.get_balance_of_batch(
                    address=self.context.agent_address,
                    token_ids=self.context.behaviours.service_registration.token_ids,
                )
                self.context.logger.info("Current balances: {}".format(result))
        elif (
            tx_msg_response.tx_id
            == contract.Performative.CONTRACT_ATOMIC_SWAP_SINGLE.value
        ):
            tx_signed = tx_msg_response.signed_payload.get("tx_signed")
            tx_digest = self.context.ledger_apis.ethereum_api.send_signed_transaction(
                is_waiting_for_confirmation=True, tx_signed=tx_signed
            )
            transaction = self.context.ledger_apis.ethereum_api.get_transaction_status(  # type: ignore
                tx_digest=tx_digest
            )
            if transaction.status != 1:
                self.context.is_active = False
                self.context.logger.info("Failed to create items. Aborting.")
            else:
                self.context.logger.info(
                    "Transaction digest for atomic_swap: {}".format(tx_digest)
                )
                self.context.logger.info("Ask the contract about my balances:")
                result = contract.get_balance_of_batch(
                    address=self.context.agent_address,
                    token_ids=self.context.behaviours.service_registration.token_ids,
                )
                self.context.logger.info(result)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
        pass
