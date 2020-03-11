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
import time
from typing import Optional, cast

from aea.crypto.ethereum import ETHEREUM
from aea.crypto.fetchai import FETCHAI
from aea.helpers.search.models import Description
from aea.skills.behaviours import TickerBehaviour

from packages.fetchai.protocols.oef.message import OEFMessage
from packages.fetchai.protocols.oef.serialization import DEFAULT_OEF, OEFSerializer
from packages.fetchai.skills.erc1155_deploy.strategy import Strategy


SERVICE_ID = ""
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
        self.is_trade = False

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
        contract = self.context.contracts.erc1155
        if strategy.contract_address is None:
            self.context.logger.info("Loading details from json")
            contract.set_instance(self.context.ledger_apis.apis.get("ethereum"))

            dm_message_for_deploy = contract.get_deploy_transaction(
                deployer_address=self.context.agent_address,
                ledger_api=self.context.ledger_apis.apis.get("ethereum"),
                skill_callback_id=self.context.skill_id,
            )
            self.context.decision_maker_message_queue.put_nowait(dm_message_for_deploy)
        else:
            self.context.logger.info("Setting the address of the deployed contract")
            contract.set_instance_w_address(
                ledger_api=self.context.ledger_apis.apis.get("ethereum"),
                contract_address=str(strategy.contract_address),
            )
            contract.create_token_ids(
                token_type=strategy.ft, nb_tokens=strategy.nb_tokens
            )

    def act(self) -> None:
        """
        Implement the act.

        :return: None
        """
        contract = self.context.contracts.erc1155
        strategy = cast(Strategy, self.context.strategy)
        if contract.is_deployed and not self.is_items_created:
            contract.create_token_ids(
                token_type=strategy.ft, nb_tokens=strategy.nb_tokens
            )

            self.context.logger.info("Creating a batch of items")
            creation_message = contract.get_create_batch_transaction(
                deployer_address=self.context.agent_address,
                ledger_api=self.context.ledger_apis.apis.get("ethereum"),
                skill_callback_id=self.context.skill_id,
            )
            self.context.decision_maker_message_queue.put_nowait(creation_message)
            self.is_items_created = True
            time.sleep(10)
        if contract.is_deployed and self.is_items_created and not self.is_items_minted:
            self.context.logger.info("Minting a batch of items")
            mint_message = contract.get_mint_batch_transaction(
                deployer_address=self.context.agent_address,
                recipient_address=self.context.agent_address,
                mint_quantities=strategy.mint_stock,
                ledger_api=self.context.ledger_apis.apis.get("ethereum"),
                skill_callback_id=self.context.skill_id,
            )
            self.context.decision_maker_message_queue.put_nowait(mint_message)
            self.is_items_minted = True

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
        msg = OEFMessage(
            type=OEFMessage.Type.REGISTER_SERVICE,
            id=oef_msg_id,
            service_description=desc,
            service_id=SERVICE_ID,
        )
        self.context.outbox.put_message(
            to=DEFAULT_OEF,
            sender=self.context.agent_address,
            protocol_id=OEFMessage.protocol_id,
            message=OEFSerializer().encode(msg),
        )
        self.context.logger.info(
            "[{}]: updating erc1155 service on OEF.".format(self.context.agent_name)
        )

    def _unregister_service(self) -> None:
        """
        Unregister service from OEF Service Directory.

        :return: None
        """
        strategy = cast(Strategy, self.context.strategy)
        oef_msg_id = strategy.get_next_oef_msg_id()
        msg = OEFMessage(
            type=OEFMessage.Type.UNREGISTER_SERVICE,
            id=oef_msg_id,
            service_description=self._registered_service_description,
            service_id=SERVICE_ID,
        )
        self.context.outbox.put_message(
            to=DEFAULT_OEF,
            sender=self.context.agent_address,
            protocol_id=OEFMessage.protocol_id,
            message=OEFSerializer().encode(msg),
        )
        self.context.logger.info(
            "[{}]: unregistering erc1155 service from OEF.".format(
                self.context.agent_name
            )
        )
        self._registered_service_description = None
