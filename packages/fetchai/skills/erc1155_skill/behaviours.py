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

"""This package contains a scaffold of a behaviour."""
import time

from aea.skills.base import Behaviour


class ERC1155Behaviour(Behaviour):
    """This class scaffolds a behaviour."""

    def setup(self) -> None:
        """
        Implement the setup.

        :return: None
        """

        contract = self.context.contracts.erc1155
        self.context.logger.info("Loading details from json")
        contract.set_instance(self.context.ledger_apis.apis.get("ethereum"))
        dm_message_for_deploy = contract.get_deploy_transaction(
            deployer_address=self.context.agent_address,
            ledger_api=self.context.ledger_apis.apis.get("ethereum"),
        )
        self.context.decision_maker_message_queue.put_nowait(dm_message_for_deploy)

    def act(self) -> None:
        """
        Implement the act.

        :return: None
        """
        contract = self.context.contracts.erc1155
        if contract.is_deployed and not contract.is_items_created:
            create_items = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
            contract.create_item_ids(token_type=2, token_ids=create_items)

            self.context.logger.info("Creating a batch of items")
            creation_message = contract.get_create_batch_transaction(
                deployer_address=self.context.agent_address,
                ledger_api=self.context.ledger_apis.apis.get("ethereum"),
            )
            self.context.decision_maker_message_queue.put_nowait(creation_message)
            contract.is_items_created = True
            time.sleep(20)

        if (
            contract.is_deployed
            and contract.is_items_created
            and not contract.is_items_minted
        ):
            mint_items = [2, 0, 0, 0, 6, 4, 2, 1, 3, 2]
            self.context.logger.info("Minting a batch of items")
            mint_message = contract.get_mint_batch_transaction(
                deployer_address=self.context.agent_address,
                recipient_address=self.context.agent_address,
                mint_quantities=mint_items,
                ledger_api=self.context.ledger_apis.apis.get("ethereum"),
            )
            self.context.decision_maker_message_queue.put_nowait(mint_message)
            contract.is_items_created = True
            time.sleep(10)

        if (
            contract.is_deployed
            and contract.is_items_created
            and contract.is_items_minted
            and not contract.is_trade
        ):
            receiver_address = "0x307CB021482575A61Db80F5365A47A07F3Ffed65"
            nonce = contract.generate_trade_nonce(
                contract=contract, address=self.context.agent_address
            )
            self.context.logger.info("Making a trade with an other address")
            trade_message = contract.get_atomic_swap_single_proposal(
                from_address=self.context.agent_address,
                to_address=receiver_address,
                item_id=contract.item_ids[0],
                from_supply=2,
                to_supply=0,
                value=0,
                trade_nonce=nonce,
                signature=contract.get_single_hash(
                    _from=self.context.agent_address,
                    _to=receiver_address,
                    _id=contract.item_ids[0],
                    _from_value=2,
                    _to_value=0,
                    _value_eth=0,
                    _nonce=nonce,
                ),
            )
            self.context.decision_maker_message_queue.put_nowait(trade_message)

    def teardown(self) -> None:
        """
        Implement the task teardown.

        :return: None
        """
        pass
