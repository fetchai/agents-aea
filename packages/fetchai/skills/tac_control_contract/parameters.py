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

"""This package contains a class representing the game parameters."""

from typing import Dict, List, Optional

from aea.exceptions import AEAEnforceError, enforce
from aea.helpers.transaction.base import Terms

from packages.fetchai.skills.tac_control.parameters import Parameters as BaseParameters


class ContractManager:
    """Class managing the contract."""

    def __init__(self, is_contract_deployed: bool = False):
        """Instantiate the contract manager class."""
        self._deploy_tx_digest = None  # type: Optional[str]
        self._create_tokens_tx_digest = None  # type: Optional[str]
        self._mint_tokens_tx_digests = {}  # type: Dict[str, str]
        self._confirmed_mint_tokens_agents = []  # type: List[str]
        self.is_contract_deployed = is_contract_deployed
        self.is_tokens_created = False
        self.is_tokens_minted = False

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


class Parameters(BaseParameters):
    """This class contains the parameters of the game."""

    def __init__(self, **kwargs):
        """Instantiate the parameter class."""
        super().__init__(**kwargs)
        self._contract_manager = ContractManager()

    @property
    def contract_manager(self) -> ContractManager:
        """Get contract manager."""
        return self._contract_manager

    def get_deploy_terms(self) -> Terms:
        """
        Get deploy terms of deployment.

        :return: terms
        """
        terms = Terms(
            ledger_id=self.ledger_id,
            sender_address=self.context.agent_address,
            counterparty_address=self.context.agent_address,
            amount_by_currency_id={},
            quantities_by_good_id={},
            nonce="",
        )
        return terms

    def get_create_token_terms(self) -> Terms:
        """
        Get create token terms of deployment.

        :return: terms
        """
        terms = Terms(
            ledger_id=self.ledger_id,
            sender_address=self.context.agent_address,
            counterparty_address=self.context.agent_address,
            amount_by_currency_id={},
            quantities_by_good_id={},
            nonce="",
        )
        return terms

    def get_mint_token_terms(self) -> Terms:
        """
        Get mint token terms of deployment.

        :return: terms
        """
        terms = Terms(
            ledger_id=self.ledger_id,
            sender_address=self.context.agent_address,
            counterparty_address=self.context.agent_address,
            amount_by_currency_id={},
            quantities_by_good_id={},
            nonce="",
        )
        return terms
