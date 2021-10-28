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

"""This module contains the FET ERC20 contract definition."""

import logging

from aea_ledger_ethereum import EthereumApi

from aea.common import Address, JSONLike
from aea.configurations.base import PublicId
from aea.contracts.base import Contract
from aea.crypto.base import LedgerApi


_default_logger = logging.getLogger("aea.packages.fetchai.contracts.fet_erc20.contract")

PUBLIC_ID = PublicId.from_str("fetchai/fet_erc20:0.9.0")


class FetERC20(Contract):
    """The FetERC20 contract class which acts as a bridge between AEA framework and ERC20 ABI."""

    contract_id = PUBLIC_ID

    @classmethod
    def get_approve_transaction(
        cls,
        ledger_api: LedgerApi,
        contract_address: Address,
        from_address: Address,
        spender: Address,
        amount: int,
        gas: int = 0,
    ) -> JSONLike:
        """
        Get transaction to approve oracle client contract transactions on behalf of sender.

        :param ledger_api: the ledger apis.
        :param contract_address: the contract address.
        :param from_address: the address of the approver.
        :param spender: the address approved to spend on behalf of sender.
        :param amount: the amount approved to be spent.
        :param gas: the gas limit for the transaction.
        :return: the approve transaction
        """
        if ledger_api.identifier == EthereumApi.identifier:
            nonce = ledger_api.api.eth.getTransactionCount(from_address)
            instance = cls.get_instance(ledger_api, contract_address)
            function = instance.functions.approve
            intermediate = function(spender, amount)
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

    @classmethod
    def get_transfer_transaction(
        cls,
        ledger_api: LedgerApi,
        contract_address: Address,
        from_address: Address,
        receiver: Address,
        amount: int,
        gas: int = 0,
    ) -> JSONLike:
        """
        Get transaction to transfer tokens to an account

        :param ledger_api: the ledger apis.
        :param contract_address: the contract address.
        :param from_address: the address of the sender.
        :param receiver: the address to which to transfer tokens.
        :param amount: the amount of tokens to transfer.
        :param gas: the gas limit for the transaction.
        :return: the transfer transaction
        """
        if ledger_api.identifier == EthereumApi.identifier:
            nonce = ledger_api.api.eth.getTransactionCount(from_address)
            instance = cls.get_instance(ledger_api, contract_address)
            function = instance.functions.transfer
            intermediate = function(receiver, amount)
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
