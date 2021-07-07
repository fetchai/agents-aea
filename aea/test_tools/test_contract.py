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
"""This module contains test case classes based on pytest for AEA contract testing."""
from pathlib import Path
from typing import Any, Dict, Optional, cast

from aea_ledger_ethereum import EthereumCrypto

from aea.common import JSONLike
from aea.configurations.loader import (
    ComponentType,
    ContractConfig,
    load_component_configuration,
)
from aea.contracts.base import Contract, contract_registry
from aea.crypto.base import Crypto, LedgerApi
from aea.crypto.registries import crypto_registry, ledger_apis_registry


class BaseContractTestCase:
    """A class to test a contract."""

    path_to_contract: Path = Path(".")
    ledger_identifier: str = EthereumCrypto.identifier
    _contract: Contract

    ledger_api: LedgerApi
    deployer_crypto: Crypto
    item_owner_crypto: Crypto

    contract_address: str

    @property
    def contract(self) -> Contract:
        """Get the contract."""
        try:
            value = self._contract
        except AttributeError:
            raise ValueError("Ensure the contract is set during setup.")
        return value

    @classmethod
    def setup(cls, **kwargs: Any) -> None:
        """Set up the contract test case."""
        _ledger_config = cast(Dict[str, str], kwargs.pop("ledger_config", {}))
        _deployer_private_key_path = cast(
            Optional[Dict[str, str]], kwargs.pop("deployer_private_key_path", None)
        )
        _item_owner_private_key_path = cast(
            Optional[Dict[str, str]], kwargs.pop("item_owner_private_key_path", None)
        )

        cls.ledger_api = ledger_apis_registry.make(
            cls.ledger_identifier, **_ledger_config
        )

        cls.deployer_crypto = crypto_registry.make(
            cls.ledger_identifier, private_key_path=_deployer_private_key_path
        )
        cls.item_owner_crypto = crypto_registry.make(
            cls.ledger_identifier, private_key_path=_item_owner_private_key_path
        )

        # register contract
        configuration = load_component_configuration(
            ComponentType.CONTRACT, cls.path_to_contract
        )
        configuration._directory = cls.path_to_contract  # pylint: disable=protected-access
        configuration = cast(ContractConfig, configuration)

        if str(configuration.public_id) not in contract_registry.specs:
            # load contract into sys modules
            Contract.from_config(configuration)

        cls._contract = contract_registry.make(str(configuration.public_id))

        cls.contract_address = cls._deploy_ethereum_contract(
            cls._contract, cls.ledger_api, cls.deployer_crypto, gas=5000000
        )

    @staticmethod
    def _deploy_ethereum_contract(
        contract: Contract, ledger_api: LedgerApi, deployer_crypto: Crypto, gas: int
    ) -> str:
        """Deploy contract on Ethereum."""
        tx = cast(
            JSONLike,
            contract.get_deploy_transaction(
                ledger_api=ledger_api,
                deployer_address=deployer_crypto.address,
                gas=gas,
            ),
        )

        if tx is not None:
            gas = ledger_api.api.eth.estimateGas(transaction=tx)
            tx["gas"] = gas

            tx_signed = deployer_crypto.sign_transaction(tx)
            tx_digest = cast(str, ledger_api.send_signed_transaction(tx_signed))
            receipt = ledger_api.get_transaction_receipt(tx_digest)

        return cast(Dict, receipt)["contractAddress"]
