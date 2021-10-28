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

"""This module contains the erc1155 contract definition."""

import logging

from aea_ledger_ethereum import EthereumApi

from aea.common import Address, JSONLike
from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea.crypto.base import LedgerApi


_default_logger = logging.getLogger(
    "aea.packages.fetchai.contracts.staking_erc20.contract"
)

PUBLIC_ID = PublicId.from_str("fetchai/staking_erc20:0.10.0")


class StakingERC20(Contract):
    """The ERC1155 contract class which acts as a bridge between AEA framework and ERC1155 ABI."""

    contract_id = PUBLIC_ID

    @classmethod
    def get_stake(
        cls, ledger_api: LedgerApi, contract_address: Address, address: Address,
    ) -> JSONLike:
        """
        Get the balance for a specific token id.

        :param ledger_api: the ledger API
        :param contract_address: the address of the contract
        :param address: the address
        :return: the balance in a dictionary - {"balance": {token_id: int, balance: int}}
        """
        if ledger_api.identifier == EthereumApi.identifier:
            instance = cls.get_instance(ledger_api, contract_address)
            result = instance.functions.getStakeForUser(address).call()
            return {"stake": result[0]}
        raise NotImplementedError
