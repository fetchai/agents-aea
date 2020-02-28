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
        contract.load_from_json(ledger_api=self.context.ledger_apis.apis.get("ethereum"))
        dm_message_for_deploy = contract.get_deploy_transaction(deployer_address=self.context.agent_address,
                                                                ledger_api=self.context.ledger_apis.apis.get("ethereum"))
        self.context.decision_maker_message_queue.put_nowait(dm_message_for_deploy)

    def act(self) -> None:
        """
        Implement the act.

        :return: None
        """
        contract = self.context.contracts.erc1155
        if contract.is_deployed and not contract.is_items_created:
            create_items = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
            contract.create_item_ids(token_ids=create_items)

            self.context.logger.info("Creating a batch of items")
            creation_message = contract.get_create_batch_transaction(deployer_address=self.context.agent_address,
                                                                     ledger_api=self.context.ledger_apis.apis.get(
                                                                         "ethereum"))
            self.context.decision_maker_message_queue.put_nowait(creation_message)
            contract.is_items_created = True
            time.sleep(20)


    def teardown(self) -> None:
        """
        Implement the task teardown.

        :return: None
        """
        pass
