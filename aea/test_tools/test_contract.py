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
    ledger_identifier: str = ""
    _deployment_gas: int = 5000000
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
        if cls.ledger_identifier == "":
            raise ValueError("ledger_identifier not set!")

        _ledger_config: Dict[str, str] = kwargs.pop("ledger_config", {})
        _deployer_private_key_path: Optional[str] = kwargs.pop(
            "deployer_private_key_path", None
        )
        _item_owner_private_key_path: Optional[str] = kwargs.pop(
            "item_owner_private_key_path", None
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
        configuration = cast(
            ContractConfig,
            load_component_configuration(ComponentType.CONTRACT, cls.path_to_contract),
        )
        configuration._directory = (  # pylint: disable=protected-access
            cls.path_to_contract
        )

        if str(configuration.public_id) not in contract_registry.specs:
            # load contract into sys modules
            Contract.from_config(configuration)

        cls._contract = contract_registry.make(str(configuration.public_id))

        cls.contract_address = cls._deploy_contract(
            cls._contract, cls.ledger_api, cls.deployer_crypto, gas=cls._deployment_gas
        )

    def _deploy_fetchai_contract(self) -> None:
        """Deploy contract on the Fetch.ai ledger."""
        tx = self.contract.get_deploy_transaction(
            ledger_api=self.ledger_api,
            deployer_address=self.deployer_crypto.address,
            gas=2000000,
        )
        assert len(tx) == 6
        signed_tx = self.deployer_crypto.sign_transaction(tx)
        tx_hash = self.ledger_api.send_signed_transaction(signed_tx)
        tx_receipt = self.ledger_api.get_transaction_receipt(tx_hash)
        assert len(tx_receipt) == 9
        assert self.ledger_api.is_transaction_settled(tx_receipt), tx_receipt["raw_log"]

        code_id = self.ledger_api.get_code_id(tx_receipt)

        assert code_id is not None
        assert code_id == self.ledger_api.get_last_code_id()
        self.code_id = code_id

        # Init contract
        tx = self.contract.get_deploy_transaction(
            ledger_api=self.ledger_api,
            deployer_address=self.deployer_crypto.address,
            code_id=self.code_id,
            init_msg={},
            tx_fee=0,
            amount=0,
            label="ERC1155",
            gas=1000000,
        )
        assert len(tx) == 6
        signed_tx = self.deployer_crypto.sign_transaction(tx)
        tx_hash = self.ledger_api.send_signed_transaction(signed_tx)
        tx_receipt = self.ledger_api.get_transaction_receipt(tx_hash)
        assert len(tx_receipt) == 9
        assert self.ledger_api.is_transaction_settled(tx_receipt), tx_receipt["raw_log"]

        contract_address = self.ledger_api.get_contract_address(tx_receipt)

        assert contract_address is not None
        assert contract_address == self.ledger_api.get_last_contract_address(
            self.code_id
        )
        self.contract_address = contract_address

    @staticmethod
    def _deploy_contract(
        contract: Contract, ledger_api: LedgerApi, deployer_crypto: Crypto, gas: int
    ) -> str:
        """Deploy contract on network."""
        tx = contract.get_deploy_transaction(
            ledger_api=ledger_api, deployer_address=deployer_crypto.address, gas=gas,
        )

        if tx is None:
            raise ValueError("Deploy transaction not found!")

        tx_signed = deployer_crypto.sign_transaction(tx)
        tx_digest = ledger_api.send_signed_transaction(tx_signed)

        if tx_digest is None:
            raise ValueError("Transaction digest not found!")

        tx_receipt = ledger_api.get_transaction_receipt(tx_digest)

        if tx_receipt is None:
            raise ValueError("Transaction receipt not found!")

        address = ledger_api.get_contract_address(tx_receipt)

        if address is None:
            raise ValueError("Contract address not found!")

        return address
