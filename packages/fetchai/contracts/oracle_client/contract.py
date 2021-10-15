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
from typing import cast

from aea_ledger_ethereum import EthereumApi
from aea_ledger_fetchai import FetchAIApi

from aea.common import Address, JSONLike
from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea.crypto.base import LedgerApi


PUBLIC_ID = PublicId.from_str("fetchai/oracle_client:0.10.0")

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
        amount: int = 0,
        gas: int = 0,
        tx_fee: int = 0,
    ) -> JSONLike:
        """
        Get transaction to query oracle value in contract

        :param ledger_api: the ledger apis.
        :param contract_address: the contract address.
        :param from_address: the address of the transaction sender.
        :param query_function: the query oracle value function.
        :param amount: the amount to transfer as part of the transaction.
        :param gas: the gas limit for the transaction.
        :param tx_fee: the transaction fee.
        :return: the query transaction
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
                    "from": from_address,
                    "nonce": nonce,
                }
            )
            tx = ledger_api.update_with_gas_estimate(tx)
            return tx
        if ledger_api.identifier == FetchAIApi.identifier:
            msg = {"query_oracle_value": {}}  # type: JSONLike
            fetchai_api = cast(FetchAIApi, ledger_api)
            tx = fetchai_api.get_handle_transaction(
                from_address,
                contract_address,
                msg,
                amount=amount,
                tx_fee=tx_fee,
                gas=gas,
            )
            return tx
        raise NotImplementedError
