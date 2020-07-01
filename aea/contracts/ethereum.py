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

"""The base ethereum contract."""

from typing import Any, Optional, cast

from web3.contract import Contract as EthereumContract

from aea.contracts.base import Contract as BaseContract
from aea.crypto.base import LedgerApi
from aea.crypto.ethereum import EthereumApi


class Contract(BaseContract):
    """Definition of an ethereum contract."""

    @classmethod
    def get_instance(
        cls, ledger_api: LedgerApi, contract_address: Optional[str] = None
    ) -> Any:
        """
        Get the instance.

        :param ledger_api: the ledger api we are using.
        :param contract_address: the contract address.
        :return: the contract instance
        """
        ledger_api = cast(EthereumApi, ledger_api)
        if contract_address is None:
            instance = ledger_api.api.eth.contract(
                abi=cls.contract_interface["abi"],
                bytecode=cls.contract_interface["bytecode"],
            )
        else:
            instance = ledger_api.api.eth.contract(
                address=contract_address,
                abi=cls.contract_interface["abi"],
                bytecode=cls.contract_interface["bytecode"],
            )
        instance = cast(EthereumContract, instance)
        return instance
