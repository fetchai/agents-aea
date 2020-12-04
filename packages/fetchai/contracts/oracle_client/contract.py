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

"""This module contains the class to connect to an oracle client contract."""

import logging

from aea.common import Address
from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea.crypto.base import LedgerApi
from aea.crypto.ethereum import EthereumApi


PUBLIC_ID = PublicId.from_str("fetchai/oracle_client:0.1.0")

_default_logger = logging.getLogger(
    "aea.packages.fetchai.contracts.oracle_client.contract"
)


class FetchOracleClientContract(Contract):
    """The Fetch oracle client contract."""

    @classmethod
    def get_query_transaction(
        cls,
        ledger_api: LedgerApi,
        contract_address: Address,
        from_address: Address,
        query_function: str,
        gas: int = 0,
    ) -> None:
        """
        Get transaction to query oracle value in contract

        :param ledger_api: the ledger apis.
        :param contract_address: the contract address.
        :param from_address: the address of the transaction sender.
        :param query_function: the query oracle value function.
        :param gas: the gas limit for the transaction.
        :return: None
        """
        if ledger_api.identifier == EthereumApi.identifier:
            nonce = ledger_api.api.eth.getTransactionCount(from_address)
            instance = cls.get_instance(ledger_api, contract_address)
            function = getattr(instance.functions, query_function)
            query_args = ()
            intermediate = function(*query_args)
            tx = intermediate.buildTransaction(
                {
                    "gas": gas,
                    "gasPrice": ledger_api.api.toWei("50", "gwei"),
                    "nonce": nonce,
                }
            )
            tx = ledger_api.update_with_gas_estimate(tx)
            return tx
        raise NotImplementedError
