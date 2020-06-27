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

from aea.helpers.search.models import Description
from aea.skills.behaviours import TickerBehaviour

from packages.fetchai.contracts.erc1155.contract import ERC1155Contract
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.erc1155_deploy.dialogues import (
    LedgerApiDialogues,
    OefSearchDialogues,
)
from packages.fetchai.skills.erc1155_deploy.strategy import Strategy

DEFAULT_SERVICES_INTERVAL = 30.0
LEDGER_API_ADDRESS = "fetchai/ledger_api:0.1.0"


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
        self._request_balance()
        self._request_contract_deploy_transaction()
        self._register_service()

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
            creation_message = contract.get_create_batch_transaction_msg(
                deployer_address=self.context.agent_address,
                token_ids=self.token_ids,
                ledger_api=self.context.ledger_apis.get_api(strategy.ledger_id),
                skill_callback_id=self.context.skill_id,
            )
            self.context.decision_maker_message_queue.put_nowait(creation_message)
        if contract.is_deployed and self.is_items_created and not self.is_items_minted:
            self.context.logger.info("Minting a batch of items")
            mint_message = contract.get_mint_batch_transaction_msg(
                deployer_address=self.context.agent_address,
                recipient_address=self.context.agent_address,
                token_ids=self.token_ids,
                mint_quantities=strategy.mint_stock,
                ledger_api=self.context.ledger_apis.get_api(strategy.ledger_id),
                skill_callback_id=self.context.skill_id,
            )
            self.context.decision_maker_message_queue.put_nowait(mint_message)

        self._unregister_service()
        self._register_service()

    def teardown(self) -> None:
        """
        Implement the task teardown.

        :return: None
        """
        self._unregister_service()

    def _request_balance(self) -> None:
        """
        Request ledger balance.

        :return: None
        """
        strategy = cast(Strategy, self.context.strategy)
        ledger_api_dialogues = cast(
            LedgerApiDialogues, self.context.ledger_api_dialogues
        )
        ledger_api_msg = LedgerApiMessage(
            performative=LedgerApiMessage.Performative.GET_BALANCE,
            dialogue_reference=ledger_api_dialogues.new_self_initiated_dialogue_reference(),
            ledger_id=strategy.ledger_id,
            address=cast(str, self.context.agent_addresses.get(strategy.ledger_id)),
        )
        ledger_api_msg.counterparty = LEDGER_API_ADDRESS
        ledger_api_dialogues.update(ledger_api_msg)
        self.context.outbox.put_message(message=ledger_api_msg)

    def _request_contract_deploy_transaction(self) -> None:
        """
        Request contract deploy transaction

        :return: None
        """
        # contract = cast(ERC1155Contract, self.context.contracts.erc1155)
        # if strategy.contract_address is None:
        #     self.context.logger.info("Preparing contract deployment transaction")
        #     contract.set_instance(self.context.ledger_apis.get_api(strategy.ledger_id))  # type: ignore
        #     dm_message_for_deploy = contract.get_deploy_transaction_msg(
        #         deployer_address=self.context.agent_address,
        #         ledger_api=self.context.ledger_apis.get_api(strategy.ledger_id),
        #         skill_callback_id=self.context.skill_id,
        #     )
        #     self.context.decision_maker_message_queue.put_nowait(dm_message_for_deploy)

    def _register_service(self) -> None:
        """
        Register to the OEF Service Directory.

        :return: None
        """
        strategy = cast(Strategy, self.context.strategy)
        description = strategy.get_service_description()
        self._registered_service_description = description
        oef_search_dialogues = cast(
            OefSearchDialogues, self.context.oef_search_dialogues
        )
        oef_search_msg = OefSearchMessage(
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            dialogue_reference=oef_search_dialogues.new_self_initiated_dialogue_reference(),
            service_description=description,
        )
        oef_search_msg.counterparty = self.context.search_service_address
        oef_search_dialogues.update(oef_search_msg)
        self.context.outbox.put_message(message=oef_search_msg)
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
        if self._registered_service_description is not None:
            oef_search_dialogues = cast(
                OefSearchDialogues, self.context.oef_search_dialogues
            )
            oef_search_msg = OefSearchMessage(
                performative=OefSearchMessage.Performative.UNREGISTER_SERVICE,
                dialogue_reference=oef_search_dialogues.new_self_initiated_dialogue_reference(),
                service_description=self._registered_service_description,
            )
            oef_search_msg.counterparty = self.context.search_service_address
            oef_search_dialogues.update(oef_search_msg)
            self.context.outbox.put_message(message=oef_search_msg)
            self.context.logger.info(
                "[{}]: unregistering erc1155 service from OEF search node.".format(
                    self.context.agent_name
                )
            )
            self._registered_service_description = None
