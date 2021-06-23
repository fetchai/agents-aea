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

"""This module contains the strategy class."""
from typing import Any

from aea_ledger_ethereum import EthereumApi

from aea.configurations.constants import DEFAULT_LEDGER
from aea.exceptions import enforce
from aea.helpers.transaction.base import Terms
from aea.skills.base import Model

from packages.fetchai.protocols.contract_api.custom_types import Kwargs


DEFAULT_LEDGER_ID = DEFAULT_LEDGER
MAX_BLOCK_HEIGHT = 1000000000000000000


class Strategy(Model):
    """This class defines a strategy for the agent."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the strategy of the agent."""
        self._ledger_id = kwargs.pop("ledger_id", DEFAULT_LEDGER_ID)
        self._oracle_contract_address = kwargs.pop("oracle_contract_address", None)
        self._client_contract_address = kwargs.pop("client_contract_address", None)
        self._erc20_address = kwargs.pop("erc20_address", None)
        self._query_function = kwargs.pop("query_function", None)
        self._query_oracle_fee = kwargs.pop("query_oracle_fee", 0)
        self._default_gas_deploy = kwargs.pop("default_gas_deploy", 0)
        self._default_gas_query = kwargs.pop("default_gas_query", 0)
        self._default_gas_approve = kwargs.pop("default_gas_approve", 0)
        self._approve_amount = kwargs.pop("approve_amount", 0)

        super().__init__(**kwargs)

        self.is_behaviour_active = True
        self._is_oracle_contract_set = self._oracle_contract_address is not None
        self._is_client_contract_deployed = self._client_contract_address is not None
        self._is_oracle_transaction_approved = False

    @property
    def ledger_id(self) -> str:
        """Get the ledger id."""
        return self._ledger_id

    @property
    def query_function(self) -> str:
        """Get the name of the oracle value query function."""
        return self._query_function

    @property
    def query_oracle_fee(self) -> str:
        """Get the fee amount for querying the oracle contract."""
        return self._query_oracle_fee

    @property
    def default_gas_deploy(self) -> str:
        """Get the default gas for deploying a contract."""
        return self._default_gas_deploy

    @property
    def default_gas_query(self) -> str:
        """Get the default gas for querying oracle value."""
        return self._default_gas_query

    @property
    def default_gas_approve(self) -> str:
        """Get the default gas for querying oracle value."""
        return self._default_gas_query

    @property
    def approve_amount(self) -> str:
        """Get the amount of tokens to approve for spending by the client contract."""
        return self._approve_amount

    @property
    def oracle_contract_address(self) -> str:
        """Get the oracle contract address."""
        if self._oracle_contract_address is None:  # pragma: nocover
            raise ValueError("Oracle contract address not set!")
        return self._oracle_contract_address

    @oracle_contract_address.setter
    def oracle_contract_address(self, oracle_contract_address: str) -> None:
        """Set the oracle contract address."""
        enforce(
            self._oracle_contract_address is None,
            "Oracle contract address already set!",
        )
        self._oracle_contract_address = oracle_contract_address

    @property
    def client_contract_address(self) -> str:
        """Get the client contract address."""
        if self._client_contract_address is None:  # pragma: nocover
            raise ValueError("Oracle client contract address not set!")
        return self._client_contract_address

    @client_contract_address.setter
    def client_contract_address(self, client_contract_address: str) -> None:
        """Set the oracle client contract address."""
        enforce(
            self._client_contract_address is None,
            "Oracle client contract address already set!",
        )
        self._client_contract_address = client_contract_address

    @property
    def erc20_address(self) -> str:
        """Get the erc20 address for token payment."""
        if self._erc20_address is None:  # pragma: nocover
            raise ValueError("ERC20 address not set!")
        return self._erc20_address

    @erc20_address.setter
    def erc20_address(self, erc20_address: str) -> None:
        """Set the erc20 address for token payment."""
        enforce(self._erc20_address is None, "ERC20 address already set!")
        self._erc20_address = erc20_address

    @property
    def is_oracle_contract_set(self) -> bool:
        """Get oracle contract status."""
        return self._is_oracle_contract_set

    @is_oracle_contract_set.setter
    def is_oracle_contract_set(self, is_oracle_contract_set: bool) -> None:
        """Set oracle contract status."""
        enforce(
            not self._is_oracle_contract_set and is_oracle_contract_set,
            "Only allowed to switch to true.",
        )
        self._is_oracle_contract_set = is_oracle_contract_set

    @property
    def is_oracle_transaction_approved(self) -> bool:
        """Get oracle transaction approval status."""
        return self._is_oracle_transaction_approved

    @is_oracle_transaction_approved.setter
    def is_oracle_transaction_approved(
        self, is_oracle_transaction_approved: bool
    ) -> None:
        """Set oracle transaction approval status."""
        enforce(
            not self._is_oracle_transaction_approved and is_oracle_transaction_approved,
            "Only allowed to switch to true.",
        )
        self._is_oracle_transaction_approved = is_oracle_transaction_approved

    @property
    def is_client_contract_deployed(self) -> bool:
        """Get oracle contract status."""
        return self._is_client_contract_deployed

    @is_client_contract_deployed.setter
    def is_client_contract_deployed(self, is_client_contract_deployed: bool) -> None:
        """Set client contract deploy status."""
        enforce(
            not self._is_client_contract_deployed and is_client_contract_deployed,
            "Only allowed to switch to true.",
        )
        self._is_client_contract_deployed = is_client_contract_deployed

    def get_deploy_terms(self, is_init_transaction: bool = False) -> Terms:
        """
        Get terms of deployment.

        :param is_init_transaction: whether the transaction is init or store.
        :return: terms
        """
        if self.ledger_id == EthereumApi.identifier:
            label = "deploy"
        else:
            if is_init_transaction:
                label = "init"
            else:
                label = "store"

        terms = Terms(
            ledger_id=self.ledger_id,
            sender_address=self.context.agent_address,
            counterparty_address=self.context.agent_address,
            amount_by_currency_id={},
            quantities_by_good_id={},
            nonce="",
            label=label,
        )
        return terms

    def get_query_terms(self) -> Terms:
        """
        Get terms of query transaction.

        :return: terms
        """
        terms = Terms(
            ledger_id=self.ledger_id,
            sender_address=self.context.agent_address,
            counterparty_address=self.context.agent_address,
            amount_by_currency_id={},
            quantities_by_good_id={},
            nonce="",
            label="query",
        )
        return terms

    def get_approve_terms(self) -> Terms:
        """
        Get terms of approve transaction.

        :return: terms
        """
        terms = Terms(
            ledger_id=self.ledger_id,
            sender_address=self.context.agent_address,
            counterparty_address=self.context.agent_address,
            amount_by_currency_id={},
            quantities_by_good_id={},
            nonce="",
            label="approve",
        )
        return terms

    def get_deploy_kwargs(self) -> Kwargs:
        """
        Get kwargs for the contract deployment

        :return: kwargs
        """
        if self.ledger_id == EthereumApi.identifier:
            kwargs = Kwargs(
                {
                    "deployer_address": self.context.agent_address,
                    "fetchOracleContractAddress": self.oracle_contract_address,
                    "gas": self.default_gas_deploy,
                }
            )
        else:
            kwargs = Kwargs(
                {
                    "deployer_address": self.context.agent_address,
                    "gas": self.default_gas_deploy,
                }
            )
        return kwargs
