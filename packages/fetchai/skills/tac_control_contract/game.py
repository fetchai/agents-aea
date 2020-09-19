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

"""This package contains a class representing the game."""

from typing import Dict, List, Optional

from aea.common import Address
from aea.exceptions import AEAEnforceError, enforce

from packages.fetchai.skills.tac_control.game import AgentState as BaseAgentState
from packages.fetchai.skills.tac_control.game import Configuration as BaseConfiguration
from packages.fetchai.skills.tac_control.game import Game as BaseGame
from packages.fetchai.skills.tac_control.game import (
    Initialization as BaseInitialization,
)
from packages.fetchai.skills.tac_control.game import Phase as BasePhase
from packages.fetchai.skills.tac_control.game import Registration as BaseRegistration
from packages.fetchai.skills.tac_control.game import Transaction as BaseTransaction
from packages.fetchai.skills.tac_control.game import Transactions as BaseTransactions


Phase = BasePhase


class Configuration(BaseConfiguration):
    """Class containing the configuration of the game."""

    def __init__(
        self,
        version_id: str,
        tx_fee: int,
        agent_addr_to_name: Dict[Address, str],
        currency_id_to_name: Dict[str, str],
        good_id_to_name: Dict[str, str],
    ):
        """
        Instantiate a game configuration.

        :param version_id: the version of the game.
        :param tx_fee: the fee for a transaction.
        :param agent_addr_to_name: a dictionary mapping agent addresses to agent names (as strings).
        :param nb_goods: the number of goods.
        """
        super().__init__(version_id, tx_fee, agent_addr_to_name, currency_id_to_name, good_id_to_name)
        self._contract_address = None  # type: Optional[str]

    @property
    def contract_address(self) -> str:
        """Get the contract address for the game."""
        if self._contract_address is None:
            raise AEAEnforceError("Contract_address not set yet!")
        return self._contract_address

    @contract_address.setter
    def contract_address(self, contract_address: str) -> None:
        """Set the contract address for the game."""
        enforce(self._contract_address is None, "Contract_address already set!")
        self._contract_address = contract_address


Initialization = BaseInitialization


Transaction = BaseTransaction


AgentState = BaseAgentState


Transactions = BaseTransactions


Registration = BaseRegistration


class ContractManager:
    """Class managing the contract."""

    def __init__(self):
        """Instantiate the contract manager class."""
        self._deploy_tx_digest = None  # type: Optional[str]
        self._create_tokens_tx_digest = None  # type: Optional[str]
        self._mint_tokens_tx_digests = {}  # type: Dict[str, str]
        self._confirmed_mint_tokens_agents = []  # type: List[str, str]

    @property
    def deploy_tx_digest(self) -> str:
        """Get the contract deployment tx digest."""
        if self._deploy_tx_digest is None:
            raise AEAEnforceError("Deploy_tx_digest is not set yet!")
        return self._deploy_tx_digest

    @deploy_tx_digest.setter
    def deploy_tx_digest(self, deploy_tx_digest: str) -> None:
        """Set the contract deployment tx digest."""
        enforce(self._deploy_tx_digest is None, "Deploy_tx_digest already set!")
        self._deploy_tx_digest = deploy_tx_digest

    @property
    def create_tokens_tx_digest(self) -> str:
        """Get the contract deployment tx digest."""
        if self._create_tokens_tx_digest is None:
            raise AEAEnforceError("Create_tokens_tx_digest is not set yet!")
        return self._create_tokens_tx_digest

    @create_tokens_tx_digest.setter
    def create_tokens_tx_digest(self, create_tokens_tx_digest: str) -> None:
        """Set the contract deployment tx digest."""
        enforce(
            self._create_tokens_tx_digest is None,
            "Create_tokens_tx_digest already set!",
        )
        self._create_tokens_tx_digest = create_tokens_tx_digest

    @property
    def mint_tokens_tx_digests(self) -> Dict[str, str]:
        """Get the mint tokens tx digests."""
        return self._mint_tokens_tx_digests

    def set_mint_tokens_tx_digest(self, agent_addr: str, tx_digest: str) -> None:
        """
        Set a mint token tx digest for an agent.

        :param agent_addr: the agent addresss
        :param tx_digest: the transaction digest
        """
        enforce(
            agent_addr not in self._mint_tokens_tx_digests, "Tx digest already set."
        )
        self._mint_tokens_tx_digests[agent_addr] = tx_digest

    @property
    def confirmed_mint_tokens_agents(self) -> List[str]:
        """Get the agents which are confirmed to have minted tokens on chain."""
        return self._confirmed_mint_tokens_agents

    def add_confirmed_mint_tokens_agents(self, agent_addr: str) -> None:
        """
        Set agent addresses whose tokens have been minted.

        :param agent_addr: the agent address
        """
        enforce(
            agent_addr not in self.confirmed_mint_tokens_agents,
            "Agent already in list.",
        )
        self._confirmed_mint_tokens_agents.append(agent_addr)


class Game(BaseGame):
    """A class to manage a TAC instance."""

    def __init__(self, **kwargs):
        """Instantiate the search class."""
        super().__init__(**kwargs)
        self._contract_manager = ContractManager()

    @property
    def contract_manager(self) -> ContractManager:
        """Get the contract manager."""
        return self._contract_manager
