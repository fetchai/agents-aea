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

"""This package contains a simple Fetch oracle client behaviour."""

from typing import Any, cast

from aea_ledger_ethereum import EthereumApi

from aea.skills.behaviours import TickerBehaviour

from packages.fetchai.connections.ledger.base import CONNECTION_ID as LEDGER_API_ADDRESS
from packages.fetchai.contracts.fet_erc20.contract import (
    PUBLIC_ID as FET_ERC20_PUBLIC_ID,
)
from packages.fetchai.contracts.oracle_client.contract import (
    PUBLIC_ID as CLIENT_CONTRACT_PUBLIC_ID,
)
from packages.fetchai.protocols.contract_api.message import ContractApiMessage
from packages.fetchai.skills.simple_oracle_client.dialogues import (
    ContractApiDialogue,
    ContractApiDialogues,
)
from packages.fetchai.skills.simple_oracle_client.strategy import Strategy


DEFAULT_QUERY_INTERVAL = 5


class SimpleOracleClientBehaviour(TickerBehaviour):
    """This class implements a behaviour that deploys a Fetch oracle client contract."""

    def __init__(self, **kwargs: Any):
        """Initialise the behaviour."""
        query_interval = kwargs.pop(
            "query_interval", DEFAULT_QUERY_INTERVAL
        )  # type: int
        super().__init__(tick_interval=query_interval, **kwargs)

    def setup(self) -> None:
        """Implement the setup."""
        self.context.logger.info("Setting up Fetch oracle client contract...")
        strategy = cast(Strategy, self.context.strategy)

        if not strategy.is_client_contract_deployed:
            self._request_contract_deploy_transaction()
        else:
            self.context.logger.info(
                "Fetch oracle client contract address already added"
            )

    def act(self) -> None:
        """Implement the act."""
        strategy = cast(Strategy, self.context.strategy)

        if not strategy.is_client_contract_deployed:
            self.context.logger.info("Oracle client contract not yet deployed")
            return
        if (
            strategy.ledger_id == EthereumApi.identifier
            and not strategy.is_oracle_transaction_approved
        ):
            self.context.logger.info(
                "Oracle client contract not yet approved to spend tokens"
            )
            self._request_approve_transaction()
            return

        # Call contract function that queries oracle value
        self.context.logger.info("Calling contract to request oracle value...")
        self._request_query_transaction()

    def _request_contract_deploy_transaction(self) -> None:
        """Request contract deployment transaction"""
        strategy = cast(Strategy, self.context.strategy)
        strategy.is_behaviour_active = False
        contract_api_dialogues = cast(
            ContractApiDialogues, self.context.contract_api_dialogues
        )
        contract_api_msg, contract_api_dialogue = contract_api_dialogues.create(
            counterparty=str(LEDGER_API_ADDRESS),
            performative=ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION,
            ledger_id=strategy.ledger_id,
            contract_id=str(CLIENT_CONTRACT_PUBLIC_ID),
            callable="get_deploy_transaction",
            kwargs=strategy.get_deploy_kwargs(),
        )
        contract_api_dialogue = cast(ContractApiDialogue, contract_api_dialogue,)
        contract_api_dialogue.terms = strategy.get_deploy_terms()
        self.context.outbox.put_message(message=contract_api_msg)
        self.context.logger.info("requesting contract deployment transaction...")

    def _request_approve_transaction(self) -> None:
        """Request transaction that approves client contract to spend tokens on behalf of sender."""
        strategy = cast(Strategy, self.context.strategy)
        strategy.is_behaviour_active = False
        contract_api_dialogues = cast(
            ContractApiDialogues, self.context.contract_api_dialogues
        )
        contract_api_msg, contract_api_dialogue = contract_api_dialogues.create(
            counterparty=str(LEDGER_API_ADDRESS),
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,
            ledger_id=strategy.ledger_id,
            contract_id=str(FET_ERC20_PUBLIC_ID),
            contract_address=strategy.erc20_address,
            callable="get_approve_transaction",
            kwargs=ContractApiMessage.Kwargs(
                {
                    "from_address": self.context.agent_address,
                    "spender": strategy.client_contract_address,
                    "amount": strategy.approve_amount,
                    "gas": strategy.default_gas_approve,
                }
            ),
        )
        contract_api_dialogue = cast(ContractApiDialogue, contract_api_dialogue)
        contract_api_dialogue.terms = strategy.get_approve_terms()
        self.context.outbox.put_message(message=contract_api_msg)
        self.context.logger.info("requesting query transaction...")

    def _request_query_transaction(self) -> None:
        """Request transaction that requests value from Fetch oracle contract."""
        strategy = cast(Strategy, self.context.strategy)
        strategy.is_behaviour_active = False
        contract_api_dialogues = cast(
            ContractApiDialogues, self.context.contract_api_dialogues
        )
        contract_api_msg, contract_api_dialogue = contract_api_dialogues.create(
            counterparty=str(LEDGER_API_ADDRESS),
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,
            ledger_id=strategy.ledger_id,
            contract_id=str(CLIENT_CONTRACT_PUBLIC_ID),
            contract_address=strategy.client_contract_address,
            callable="get_query_transaction",
            kwargs=ContractApiMessage.Kwargs(
                {
                    "from_address": self.context.agent_address,
                    "query_function": strategy.query_function,
                    "amount": strategy.query_oracle_fee,
                    "gas": strategy.default_gas_query,
                }
            ),
        )
        contract_api_dialogue = cast(ContractApiDialogue, contract_api_dialogue)
        contract_api_dialogue.terms = strategy.get_query_terms()
        self.context.outbox.put_message(message=contract_api_msg)
        self.context.logger.info("requesting query transaction...")

    def teardown(self) -> None:
        """Implement the task teardown."""
