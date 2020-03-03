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

"""This package contains the behaviour of a generic seller AEA."""
import time
from typing import Optional, cast

from aea.crypto.ethereum import ETHEREUM
from aea.crypto.fetchai import FETCHAI
from aea.helpers.search.models import Description
from aea.skills.behaviours import TickerBehaviour

from packages.fetchai.protocols.oef.message import OEFMessage
from packages.fetchai.protocols.oef.serialization import DEFAULT_OEF, OEFSerializer
from packages.fetchai.skills.erc1155_skill.strategy import Strategy


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

        if strategy.is_deploying_contract:
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
        strategy = cast(Strategy, self.context.strategy)
        if strategy.is_deploying_contract:
            if contract.is_deployed and not contract.is_items_created:
                create_items = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
                contract.create_item_ids(token_type=strategy.ft, token_ids=create_items)

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
                mint_items = [20, 20, 20, 20, 26, 24, 22, 21, 23, 22]
                self.context.logger.info("Minting a batch of items")
                mint_message = contract.get_mint_batch_transaction(
                    deployer_address=self.context.agent_address,
                    recipient_address=self.context.agent_address,
                    mint_quantities=mint_items,
                    ledger_api=self.context.ledger_apis.apis.get("ethereum"),
                )
                self.context.decision_maker_message_queue.put_nowait(mint_message)
                contract.is_items_minted = True
                time.sleep(10)

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
            "[{}]: updating generic seller services on OEF.".format(
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
            "[{}]: unregistering generic seller services from OEF.".format(
                self.context.agent_name
            )
        )
        self._registered_service_description = None
