# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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
"""Fetchai module wrapping the public and private key cryptography and ledger api."""

from typing import Any, Dict, Optional

from aea_ledger_fetchai._cosmos import (
    CosmosCrypto,
    CosmosFaucetApi,
    CosmosHelper,
    _CosmosApi,
)

from aea.common import JSONLike


_FETCHAI = "fetchai"
_FETCH = "fetch"
TESTNET_NAME = "testnet"
FETCHAI_TESTNET_FAUCET_URL = "https://faucet-dorado.fetch.ai"
DEFAULT_ADDRESS = "https://rest-dorado.fetch.ai:443"
DEFAULT_CURRENCY_DENOM = "atestfet"
DEFAULT_CHAIN_ID = "dorado-1"


class FetchAIHelper(CosmosHelper):
    """Helper class usable as Mixin for FetchAIApi or as standalone class."""

    address_prefix = _FETCH


class FetchAICrypto(CosmosCrypto):  # pylint: disable=W0223
    """Class wrapping the Entity Generation from Fetch.AI ledger."""

    identifier = _FETCHAI
    helper = FetchAIHelper


class FetchAIApi(_CosmosApi, FetchAIHelper):
    """Class to interact with the Fetch ledger APIs."""

    identifier = _FETCHAI

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the Fetch.ai ledger APIs."""
        if "address" not in kwargs:
            kwargs["address"] = DEFAULT_ADDRESS  # pragma: nocover
        if "denom" not in kwargs:
            kwargs["denom"] = DEFAULT_CURRENCY_DENOM
        if "chain_id" not in kwargs:
            kwargs["chain_id"] = DEFAULT_CHAIN_ID
        super().__init__(**kwargs)

    def contract_method_call(
        self,
        contract_instance: Any,
        method_name: str,
        **method_args: Any,
    ) -> Optional[JSONLike]:
        """Call a contract's method

        :param contract_instance: the contract to use
        :param method_name: the contract method to call
        :param method_args: the contract call parameters
        """
        raise NotImplementedError

    def build_transaction(
        self,
        contract_instance: Any,
        method_name: str,
        method_args: Optional[Dict],
        tx_args: Optional[Dict],
        raise_on_try: bool = False,
    ) -> Optional[JSONLike]:
        """Prepare a transaction

        :param contract_instance: the contract to use
        :param method_name: the contract method to call
        :param method_args: the contract parameters
        :param tx_args: the transaction parameters
        :param raise_on_try: whether the method will raise or log on error
        """
        raise NotImplementedError

    def get_transaction_transfer_logs(
        self,
        contract_instance: Any,
        tx_hash: str,
        target_address: Optional[str] = None,
    ) -> Optional[JSONLike]:
        """
        Get all transfer events derived from a transaction.

        :param contract_instance: the contract
        :param tx_hash: the transaction hash
        :param target_address: optional address to filter transfer events to just those that affect it
        """
        raise NotImplementedError


class FetchAIFaucetApi(CosmosFaucetApi):
    """Fetchai testnet faucet API."""

    identifier = _FETCHAI
    testnet_name = TESTNET_NAME
    testnet_faucet_url = FETCHAI_TESTNET_FAUCET_URL
