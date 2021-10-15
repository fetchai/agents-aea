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

"""This module contains the class to connect to an Oracle contract."""

import logging
from typing import Any, Dict, cast

from aea_ledger_ethereum import EthereumApi
from aea_ledger_fetchai import FetchAIApi

from aea.common import Address, JSONLike
from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea.crypto.base import LedgerApi


PUBLIC_ID = PublicId.from_str("fetchai/oracle:0.11.0")


def keccak256(input_: bytes) -> bytes:
    """Compute hash."""
    return bytes(bytearray.fromhex(EthereumApi.get_hash(input_)[2:]))


ORACLE_ROLE = "ORACLE_ROLE"

_default_logger = logging.getLogger("aea.packages.fetchai.contracts.oracle.contract")


class FetchOracleContract(Contract):
    """The Fetch oracle contract."""

    @classmethod
    def get_grant_role_transaction(
        cls,
        ledger_api: LedgerApi,
        contract_address: Address,
        oracle_address: Address,
        gas: int = 0,
        tx_fee: int = 0,
    ) -> JSONLike:
        """
        Get transaction to grant oracle role to recipient_address

        :param ledger_api: the ledger API
        :param contract_address: the contract address
        :param oracle_address: the address of the oracle
        :param gas: the gas limit
        :param tx_fee: the transaction fee
        :return: the transaction object
        """
        if ledger_api.identifier == EthereumApi.identifier:
            nonce = ledger_api.api.eth.getTransactionCount(oracle_address)
            instance = cls.get_instance(ledger_api, contract_address)
            oracle_role = keccak256(ORACLE_ROLE.encode("utf-8"))
            tx = instance.functions.grantRole(
                oracle_role, oracle_address
            ).buildTransaction(
                {
                    "gas": gas,
                    "gasPrice": ledger_api.api.toWei("50", "gwei"),
                    "nonce": nonce,
                }
            )
            tx = ledger_api.update_with_gas_estimate(tx)
            return tx
        if ledger_api.identifier == FetchAIApi.identifier:
            msg = {"grant_role": {"role": ORACLE_ROLE, "address": oracle_address}}
            fetchai_api = cast(FetchAIApi, ledger_api)
            tx = fetchai_api.get_handle_transaction(
                oracle_address, contract_address, msg, amount=0, tx_fee=tx_fee, gas=gas
            )
            return tx
        raise NotImplementedError

    @classmethod
    def get_update_transaction(
        cls,
        ledger_api: LedgerApi,
        contract_address: Address,
        oracle_address: Address,
        update_function: str,
        update_kwargs: Dict[str, Any],
        gas: int = 0,
        tx_fee: int = 0,
    ) -> JSONLike:
        """
        Update oracle value in contract

        :param ledger_api: the ledger apis.
        :param contract_address: the contract address.
        :param oracle_address: the oracle address.
        :param update_function: the oracle value update function.
        :param update_kwargs: the arguments to the contract's update function.
        :param gas: the gas limit
        :param tx_fee: the transaction fee
        :return: transaction json
        """
        if ledger_api.identifier == EthereumApi.identifier:
            nonce = ledger_api.api.eth.getTransactionCount(oracle_address)
            instance = cls.get_instance(ledger_api, contract_address)
            function = getattr(instance.functions, update_function)
            update_args = list(update_kwargs.values())
            intermediate = function(*update_args)
            tx = intermediate.buildTransaction(
                {
                    "gas": gas,
                    "gasPrice": ledger_api.api.toWei("50", "gwei"),
                    "nonce": nonce,
                }
            )
            tx = ledger_api.update_with_gas_estimate(tx)
            return tx
        if ledger_api.identifier in FetchAIApi.identifier:

            # Convert all values to strings for CosmWasm message
            update_kwargs_str = {
                key: str(value) for (key, value) in update_kwargs.items()
            }

            msg = {update_function: update_kwargs_str}
            fetchai_api = cast(FetchAIApi, ledger_api)
            tx = fetchai_api.get_handle_transaction(
                oracle_address, contract_address, msg, amount=0, tx_fee=tx_fee, gas=gas
            )
            return tx
        raise NotImplementedError
