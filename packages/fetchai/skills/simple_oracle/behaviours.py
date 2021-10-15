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

"""This package contains a simple Fetch oracle contract deployment behaviour."""

from typing import Any, Dict, cast

from aea.skills.behaviours import TickerBehaviour

from packages.fetchai.connections.ledger.base import CONNECTION_ID as LEDGER_API_ADDRESS
from packages.fetchai.connections.prometheus.connection import (
    PUBLIC_ID as PROM_CONNECTION_ID,
)
from packages.fetchai.contracts.oracle.contract import PUBLIC_ID as CONTRACT_PUBLIC_ID
from packages.fetchai.protocols.contract_api.message import ContractApiMessage
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.prometheus.message import PrometheusMessage
from packages.fetchai.skills.simple_oracle.dialogues import (
    ContractApiDialogue,
    ContractApiDialogues,
    LedgerApiDialogues,
    PrometheusDialogues,
)
from packages.fetchai.skills.simple_oracle.strategy import Strategy


DEFAULT_UPDATE_INTERVAL = 5
DEFAULT_DECIMALS = 5
EXPIRATION_BLOCK = 1000000000000000


class SimpleOracleBehaviour(TickerBehaviour):
    """This class implements a behaviour that deploys a Fetch oracle contract."""

    def __init__(self, **kwargs: Any):
        """Initialise the behaviour."""
        update_interval = kwargs.pop(
            "update_interval", DEFAULT_UPDATE_INTERVAL
        )  # type: int
        super().__init__(tick_interval=update_interval, **kwargs)

    def setup(self) -> None:
        """Implement the setup."""
        self.context.logger.info("Setting up Fetch oracle contract...")
        strategy = cast(Strategy, self.context.strategy)

        if not strategy.is_contract_deployed:
            self._request_contract_deploy_transaction()
        else:
            self.context.logger.info("Fetch oracle contract address already added")

        if strategy.is_oracle_role_granted:
            self.context.logger.info("Oracle role already granted")

        prom_dialogues = cast(PrometheusDialogues, self.context.prometheus_dialogues)

        if prom_dialogues.enabled:
            for metric in prom_dialogues.metrics:
                metric_name = metric["name"]
                self.context.logger.info("Adding Prometheus metric: " + metric_name)
                self.add_prometheus_metric(
                    metric_name,
                    metric["type"],
                    metric["description"],
                    dict(metric["labels"]),
                )

    def act(self) -> None:
        """Implement the act."""
        strategy = cast(Strategy, self.context.strategy)

        # Request account balance
        self._get_balance()

        if not strategy.is_contract_deployed:
            self.context.logger.info("Oracle contract not yet deployed")
            return

        if not strategy.is_oracle_role_granted:
            self.context.logger.info("Oracle not yet created")
            self._request_grant_role_transaction()
            return

        # Check for oracle from data collecting skill
        oracle_data = self.context.shared_state.get(strategy.oracle_value_name, None)

        if oracle_data is None:
            self.context.logger.info("No oracle value to publish")
        else:
            self.context.logger.info("Publishing oracle value")

            # add expiration block
            oracle_data["expiration_block"] = EXPIRATION_BLOCK
            self.context.logger.info(f"Update kwargs: {oracle_data}")
            self._request_update_transaction(oracle_data)

    def _request_contract_deploy_transaction(self) -> None:
        """Request contract deployment transaction."""
        strategy = cast(Strategy, self.context.strategy)
        strategy.is_behaviour_active = False
        contract_api_dialogues = cast(
            ContractApiDialogues, self.context.contract_api_dialogues
        )
        contract_api_msg, contract_api_dialogue = contract_api_dialogues.create(
            counterparty=str(LEDGER_API_ADDRESS),
            performative=ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION,
            ledger_id=strategy.ledger_id,
            contract_id=str(CONTRACT_PUBLIC_ID),
            callable="get_deploy_transaction",
            kwargs=strategy.get_deploy_kwargs(),
        )
        contract_api_dialogue = cast(ContractApiDialogue, contract_api_dialogue,)
        contract_api_dialogue.terms = strategy.get_deploy_terms()
        self.context.outbox.put_message(message=contract_api_msg)
        self.context.logger.info("requesting contract deployment transaction...")

    def _request_grant_role_transaction(self) -> None:
        """Request transaction that grants oracle role in a Fetch oracle contract."""
        strategy = cast(Strategy, self.context.strategy)
        strategy.is_behaviour_active = False
        contract_api_dialogues = cast(
            ContractApiDialogues, self.context.contract_api_dialogues
        )
        contract_api_msg, contract_api_dialogue = contract_api_dialogues.create(
            counterparty=str(LEDGER_API_ADDRESS),
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,
            ledger_id=strategy.ledger_id,
            contract_id=str(CONTRACT_PUBLIC_ID),
            contract_address=strategy.contract_address,
            callable="get_grant_role_transaction",
            kwargs=ContractApiMessage.Kwargs(
                {
                    "oracle_address": self.context.agent_address,
                    "gas": strategy.default_gas_grant_role,
                }
            ),
        )
        contract_api_dialogue = cast(ContractApiDialogue, contract_api_dialogue)
        contract_api_dialogue.terms = strategy.get_grant_role_terms()
        self.context.outbox.put_message(message=contract_api_msg)
        self.context.logger.info("requesting grant role transaction...")

    def _request_update_transaction(self, update_kwargs: Dict[str, Any]) -> None:
        """Request transaction that updates value in Fetch oracle contract."""
        strategy = cast(Strategy, self.context.strategy)
        strategy.is_behaviour_active = False
        contract_api_dialogues = cast(
            ContractApiDialogues, self.context.contract_api_dialogues
        )
        contract_api_msg, contract_api_dialogue = contract_api_dialogues.create(
            counterparty=str(LEDGER_API_ADDRESS),
            performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,
            ledger_id=strategy.ledger_id,
            contract_id=str(CONTRACT_PUBLIC_ID),
            contract_address=strategy.contract_address,
            callable="get_update_transaction",
            kwargs=ContractApiMessage.Kwargs(
                {
                    "oracle_address": self.context.agent_address,
                    "update_function": strategy.update_function,
                    "update_kwargs": update_kwargs,
                    "gas": strategy.default_gas_update,
                }
            ),
        )
        contract_api_dialogue = cast(ContractApiDialogue, contract_api_dialogue)
        contract_api_dialogue.terms = strategy.get_update_terms()
        self.context.outbox.put_message(message=contract_api_msg)
        self.context.logger.info("requesting update transaction...")

    def _get_balance(self) -> None:
        """Request balance of agent account by sending a message to the ledger API."""
        strategy = cast(Strategy, self.context.strategy)
        ledger_api_dialogues = cast(
            LedgerApiDialogues, self.context.ledger_api_dialogues
        )
        ledger_api_msg, _ = ledger_api_dialogues.create(
            counterparty=str(LEDGER_API_ADDRESS),
            performative=LedgerApiMessage.Performative.GET_BALANCE,
            ledger_id=strategy.ledger_id,
            address=cast(str, self.context.agent_addresses.get(strategy.ledger_id)),
        )
        self.context.outbox.put_message(message=ledger_api_msg)

    def add_prometheus_metric(
        self,
        metric_name: str,
        metric_type: str,
        description: str,
        labels: Dict[str, str],
    ) -> None:
        """
        Add a prometheus metric.

        :param metric_name: the name of the metric to add.
        :param metric_type: the type of the metric.
        :param description: a description of the metric.
        :param labels: the metric labels.
        """
        # context
        prom_dialogues = cast(PrometheusDialogues, self.context.prometheus_dialogues)

        # prometheus update message
        message, _ = prom_dialogues.create(
            counterparty=str(PROM_CONNECTION_ID),
            performative=PrometheusMessage.Performative.ADD_METRIC,
            type=metric_type,
            title=metric_name,
            description=description,
            labels=labels,
        )

        # send message
        self.context.outbox.put_message(message=message)

    def update_prometheus_metric(
        self, metric_name: str, update_func: str, value: float, labels: Dict[str, str],
    ) -> None:
        """
        Update a prometheus metric.

        :param metric_name: the name of the metric.
        :param update_func: the name of the update function (e.g. inc, dec, set, ...).
        :param value: the value to provide to the update function.
        :param labels: the metric labels.
        """
        # context
        prom_dialogues = cast(PrometheusDialogues, self.context.prometheus_dialogues)

        # prometheus update message
        message, _ = prom_dialogues.create(
            counterparty=str(PROM_CONNECTION_ID),
            performative=PrometheusMessage.Performative.UPDATE_METRIC,
            title=metric_name,
            callable=update_func,
            value=value,
            labels=labels,
        )

        # send message
        self.context.outbox.put_message(message=message)

    def teardown(self) -> None:
        """Implement the task teardown."""
