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

from aea.configurations.constants import DEFAULT_LEDGER
from aea.exceptions import enforce
from aea.helpers.transaction.base import Terms
from aea.skills.base import Model


DEFAULT_LEDGER_ID = DEFAULT_LEDGER
MAX_BLOCK_HEIGHT = 1000000000000000000


class Strategy(Model):
    """This class defines a strategy for the agent."""

    def __init__(self, **kwargs) -> None:
        """Initialize the strategy of the agent."""
        self._ledger_id = kwargs.pop("ledger_id", DEFAULT_LEDGER_ID)
        self._contract_address = kwargs.pop("contract_address", None)
        self._erc20_address = kwargs.pop("erc20_address", None)
        self._update_function = kwargs.pop("update_function", None)
        self._is_oracle_role_granted = kwargs.pop("is_oracle_role_granted", False)
        self._initial_fee_deploy = kwargs.pop("initial_fee_deploy", 0)
        self._default_gas_deploy = kwargs.pop("default_gas_deploy", 0)
        self._default_gas_grant_role = kwargs.pop("default_gas_grant_role", 0)
        self._default_gas_update = kwargs.pop("default_gas_update", 0)

        super().__init__(**kwargs)

        self.is_behaviour_active = True
        self._is_contract_deployed = self._contract_address is not None

    @property
    def ledger_id(self) -> str:
        """Get the ledger id."""
        return self._ledger_id

    @property
    def update_function(self) -> str:
        """Get the name of the oracle value update function."""
        return self._update_function

    @property
    def initial_fee_deploy(self) -> str:
        """Get the initial for contract deployment."""
        return self._initial_fee_deploy

    @property
    def default_gas_deploy(self) -> str:
        """Get the default gas for deploying a contract."""
        return self._default_gas_deploy

    @property
    def default_gas_grant_role(self) -> str:
        """Get the default gas for role granting."""
        return self._default_gas_grant_role

    @property
    def default_gas_update(self) -> str:
        """Get the default gas for updating value."""
        return self._default_gas_update

    @property
    def contract_address(self) -> str:
        """Get the contract address."""
        if self._contract_address is None:
            raise ValueError("Contract address not set!")
        return self._contract_address

    @contract_address.setter
    def contract_address(self, contract_address: str) -> None:
        """Set the contract address."""
        enforce(self._contract_address is None, "Contract address already set!")
        self._contract_address = contract_address

    @property
    def erc20_address(self) -> str:
        """Get the erc20 address for token payment."""
        if self._erc20_address is None:
            raise ValueError("ERC20 address not set!")
        return self._erc20_address

    @erc20_address.setter
    def erc20_address(self, erc20_address: str) -> None:
        """Set the erc20 address for token payment."""
        enforce(self._erc20_address is None, "ERC20 address already set!")
        self._erc20_address = erc20_address

    @property
    def is_contract_deployed(self) -> bool:
        """Get contract deploy status."""
        return self._is_contract_deployed

    @is_contract_deployed.setter
    def is_contract_deployed(self, is_contract_deployed: bool) -> None:
        """Set contract deploy status."""
        enforce(
            not self._is_contract_deployed and is_contract_deployed,
            "Only allowed to switch to true.",
        )
        self._is_contract_deployed = is_contract_deployed

    @property
    def is_oracle_role_granted(self) -> bool:
        """Get oracle role status."""
        return self._is_oracle_role_granted

    @is_oracle_role_granted.setter
    def is_oracle_role_granted(self, is_oracle_role_granted: bool) -> None:
        """Set oracle role status."""
        enforce(
            not self._is_oracle_role_granted and is_oracle_role_granted,
            "Only allowed to switch to true.",
        )
        self._is_oracle_role_granted = is_oracle_role_granted

    def get_deploy_terms(self) -> Terms:
        """
        Get terms of deployment.

        :return: terms
        """
        terms = Terms(
            ledger_id=self.ledger_id,
            sender_address=self.context.agent_address,
            counterparty_address=self.context.agent_address,
            amount_by_currency_id={},
            quantities_by_good_id={},
            nonce="",
            label="deploy",
        )
        return terms

    def get_grant_role_terms(self) -> Terms:
        """
        Get terms of oracle role granting.

        :return: terms
        """
        terms = Terms(
            ledger_id=self.ledger_id,
            sender_address=self.context.agent_address,
            counterparty_address=self.context.agent_address,
            amount_by_currency_id={},
            quantities_by_good_id={},
            nonce="",
            label="grant_role",
        )
        return terms

    def get_update_terms(self) -> Terms:
        """
        Get terms of update transaction.

        :return: terms
        """
        terms = Terms(
            ledger_id=self.ledger_id,
            sender_address=self.context.agent_address,
            counterparty_address=self.context.agent_address,
            amount_by_currency_id={},
            quantities_by_good_id={},
            nonce="",
            label="update",
        )
        return terms
