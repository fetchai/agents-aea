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

"""This package contains the behaviour of a erc1155 deploy skill AEA."""

from typing import Optional, cast

from aea.crypto.ethereum import ETHEREUM
from aea.crypto.fetchai import FETCHAI
from aea.helpers.search.models import Description
from aea.skills.behaviours import TickerBehaviour

from packages.fetchai.contracts.erc1155.contract import ERC1155Contract
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.protocols.oef_search.serialization import OefSearchSerializer
from packages.fetchai.skills.erc1155_deploy.strategy import Strategy


DEFAULT_SERVICES_INTERVAL = 30.0


class ServiceRegistrationBehaviour(TickerBehaviour):
    """This class implements a behaviour."""

    def __init__(self, **kwargs):
        """Initialise the behaviour."""
        services_interval = kwargs.pop(
            "services_interval", DEFAULT_SERVICES_INTERVAL
        )  # type: int
        super().__init__(tick_interval=services_interval, **kwargs)
        self._registered_service_description = None  # type: Optional[Description]
        self.is_items_created = False
        self.is_items_minted = False
        self.token_ids = []  # List[int]

    def setup(self) -> None:
        """
        Implement the setup.

        :return: None
        """

        strategy = cast(Strategy, self.context.strategy)

        if self.context.ledger_apis.has_fetchai:
            fet_balance = self.context.ledger_apis.token_balance(
                FETCHAI, cast(str, self.context.agent_addresses.get(FETCHAI))
            )
            if fet_balance > 0:
                self.context.logger.info(
                    "[{}]: starting balance on fetchai ledger={}.".format(
                        self.context.agent_name, fet_balance
                    )
                )
            else:
                self.context.logger.warning(
                    "[{}]: you have no starting balance on fetchai ledger!".format(
                        self.context.agent_name
                    )
                )

        if self.context.ledger_apis.has_ethereum:
            eth_balance = self.context.ledger_apis.token_balance(
                ETHEREUM, cast(str, self.context.agent_addresses.get(ETHEREUM))
            )
            if eth_balance > 0:
                self.context.logger.info(
                    "[{}]: starting balance on ethereum ledger={}.".format(
                        self.context.agent_name, eth_balance
                    )
                )
            else:
                self.context.logger.warning(
                    "[{}]: you have no starting balance on ethereum ledger!".format(
                        self.context.agent_name
                    )
                )

        self._register_service()
        contract = cast(ERC1155Contract, self.context.contracts.erc1155)
        if strategy.contract_address is None:
            self.context.logger.info("Preparing contract deployment transaction")
            contract.set_instance(self.context.ledger_apis.ethereum_api)
            dm_message_for_deploy = contract.get_deploy_transaction(
                deployer_address=self.context.agent_address,
                ledger_api=self.context.ledger_apis.ethereum_api,
                skill_callback_id=self.context.skill_id,
            )
            self.context.decision_maker_message_queue.put_nowait(dm_message_for_deploy)
        else:
            self.context.logger.info("Setting the address of the deployed contract")
            contract.set_address(
                ledger_api=self.context.ledger_apis.ethereum_api,
                contract_address=str(strategy.contract_address),
            )

    def act(self) -> None:
        """
        Implement the act.

        :return: None
        """
        contract = cast(ERC1155Contract, self.context.contracts.erc1155)
        strategy = cast(Strategy, self.context.strategy)
        if contract.is_deployed and not self.is_items_created:
            self.token_ids = contract.create_token_ids(
                token_type=strategy.ft, nb_tokens=strategy.nb_tokens
            )
            self.context.logger.info("Creating a batch of items")
            creation_message = contract.get_create_batch_transaction(
                deployer_address=self.context.agent_address,
                ledger_api=self.context.ledger_apis.ethereum_api,
                skill_callback_id=self.context.skill_id,
                token_ids=self.token_ids,
            )
            self.context.decision_maker_message_queue.put_nowait(creation_message)
        if contract.is_deployed and self.is_items_created and not self.is_items_minted:
            self.context.logger.info("Minting a batch of items")
            mint_message = contract.get_mint_batch_transaction(
                deployer_address=self.context.agent_address,
                recipient_address=self.context.agent_address,
                mint_quantities=strategy.mint_stock,
                ledger_api=self.context.ledger_apis.ethereum_api,
                skill_callback_id=self.context.skill_id,
                token_ids=self.token_ids,
            )
            self.context.decision_maker_message_queue.put_nowait(mint_message)

        self._unregister_service()
        self._register_service()

    def teardown(self) -> None:
        """
        Implement the task teardown.

        :return: None
        """
        if self.context.ledger_apis.has_fetchai:
            balance = self.context.ledger_apis.token_balance(
                FETCHAI, cast(str, self.context.agent_addresses.get(FETCHAI))
            )
            self.context.logger.info(
                "[{}]: ending balance on fetchai ledger={}.".format(
                    self.context.agent_name, balance
                )
            )

        if self.context.ledger_apis.has_ethereum:
            balance = self.context.ledger_apis.token_balance(
                ETHEREUM, cast(str, self.context.agent_addresses.get(ETHEREUM))
            )
            self.context.logger.info(
                "[{}]: ending balance on ethereum ledger={}.".format(
                    self.context.agent_name, balance
                )
            )

        self._unregister_service()

    def _register_service(self) -> None:
        """
        Register to the OEF Service Directory.

        :return: None
        """
        strategy = cast(Strategy, self.context.strategy)
        desc = strategy.get_service_description()
        self._registered_service_description = desc
        oef_msg_id = strategy.get_next_oef_msg_id()
        msg = OefSearchMessage(
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            dialogue_reference=(str(oef_msg_id), ""),
            service_description=desc,
        )
        self.context.outbox.put_message(
            to=self.context.search_service_address,
            sender=self.context.agent_address,
            protocol_id=OefSearchMessage.protocol_id,
            message=OefSearchSerializer().encode(msg),
        )
        self.context.logger.info(
            "[{}]: updating erc1155 service on OEF search node.".format(
                self.context.agent_name
            )
        )

    def _unregister_service(self) -> None:
        """
        Unregister service from OEF Service Directory.

        :return: None
        """
        strategy = cast(Strategy, self.context.strategy)
        oef_msg_id = strategy.get_next_oef_msg_id()
        msg = OefSearchMessage(
            performative=OefSearchMessage.Performative.UNREGISTER_SERVICE,
            dialogue_reference=(str(oef_msg_id), ""),
            service_description=self._registered_service_description,
        )
        self.context.outbox.put_message(
            to=self.context.search_service_address,
            sender=self.context.agent_address,
            protocol_id=OefSearchMessage.protocol_id,
            message=OefSearchSerializer().encode(msg),
        )
        self.context.logger.info(
            "[{}]: unregistering erc1155 service from OEF search node.".format(
                self.context.agent_name
            )
        )
        self._registered_service_description = None
