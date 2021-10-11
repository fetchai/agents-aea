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

import time
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

from aea.common import JSONLike
from aea.configurations.loader import (
    ComponentType,
    ContractConfig,
    load_component_configuration,
)
from aea.contracts.base import Contract, contract_registry
from aea.crypto.base import Crypto, FaucetApi, LedgerApi
from aea.crypto.registries import (
    crypto_registry,
    faucet_apis_registry,
    ledger_apis_registry,
)


class BaseContractTestCase(ABC):
    """A class to test a contract."""

    path_to_contract: Path = Path(".")
    ledger_identifier: str = ""
    fund_from_faucet: bool = False
    _deployment_gas: int = 5000000
    _contract: Contract

    ledger_api: LedgerApi
    deployer_crypto: Crypto
    item_owner_crypto: Crypto
    faucet_api: FaucetApi

    deployment_tx_receipt: JSONLike
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
            raise ValueError("ledger_identifier not set!")  # pragma: nocover

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
        cls.faucet_api = faucet_apis_registry.make(cls.ledger_identifier)

        # Fund from faucet
        if cls.fund_from_faucet:
            # Refill deployer account from faucet
            cls.refill_from_faucet(
                cls.ledger_api, cls.faucet_api, cls.deployer_crypto.address
            )

            # Refill item owner account from faucet
            cls.refill_from_faucet(
                cls.ledger_api, cls.faucet_api, cls.item_owner_crypto.address
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
            Contract.from_config(configuration)  # pragma: nocover
        cls._contract = contract_registry.make(str(configuration.public_id))

        # deploy contract
        cls.deployment_tx_receipt = cls._deploy_contract(
            cls._contract, cls.ledger_api, cls.deployer_crypto, gas=cls._deployment_gas
        )
        cls.contract_address = cls.finish_contract_deployment()

    @classmethod
    @abstractmethod
    def finish_contract_deployment(cls) -> str:
        """
        Finish deploying contract.

        :return: contract address
        """

    @staticmethod
    def refill_from_faucet(
        ledger_api: LedgerApi, faucet_api: FaucetApi, address: str
    ) -> None:
        """Refill from faucet."""
        start_balance = ledger_api.get_balance(address)

        faucet_api.get_wealth(address)

        balance = ledger_api.get_balance(address)
        if balance == start_balance:
            raise ValueError("Balance not increased!")  # pragma: nocover

    @staticmethod
    def sign_send_confirm_receipt_multisig_transaction(
        tx: JSONLike,
        ledger_api: LedgerApi,
        cryptos: List[Crypto],
        sleep_time: float = 2.0,
    ) -> JSONLike:
        """
        Sign, send and confirm settlement of a transaction with multiple signatures.

        :param tx: the transaction
        :param ledger_api: the ledger api
        :param cryptos: Cryptos to sign transaction with
        :param sleep_time: the time to sleep between transaction submission and receipt request
        :return: The transaction receipt
        """
        for crypto in cryptos:
            tx = crypto.sign_transaction(tx)
        tx_digest = ledger_api.send_signed_transaction(tx)

        if tx_digest is None:
            raise ValueError("Transaction digest not found!")  # pragma: nocover

        tx_receipt = ledger_api.get_transaction_receipt(tx_digest)

        not_settled = True
        elapsed_time = 0
        while not_settled and elapsed_time < 20:
            elapsed_time += 1
            time.sleep(sleep_time)
            tx_receipt = ledger_api.get_transaction_receipt(tx_digest)
            if tx_receipt is None:
                continue
            not_settled = not ledger_api.is_transaction_settled(tx_receipt)

        if tx_receipt is None:
            raise ValueError("Transaction receipt not found!")  # pragma: nocover

        if not_settled:
            raise ValueError(  # pragma: nocover
                f"Transaction receipt not valid!\n{tx_receipt['raw_log']}"
            )

        return tx_receipt

    @classmethod  # noqa
    def sign_send_confirm_receipt_transaction(
        cls,
        tx: JSONLike,
        ledger_api: LedgerApi,
        crypto: Crypto,
        sleep_time: float = 2.0,
    ) -> JSONLike:
        """
        Sign, send and confirm settlement of a transaction with multiple signatures.

        :param tx: the transaction
        :param ledger_api: the ledger api
        :param crypto: Crypto to sign transaction with
        :param sleep_time: the time to sleep between transaction submission and receipt request
        :return: The transaction receipt
        """

        # BACKWARDS COMPATIBILITY: This method supports only 1 signer and is kept for backwards compatibility.
        # new method sign_send_confirm_receipt_multisig_transaction should be used always instead of this one.
        return cls.sign_send_confirm_receipt_multisig_transaction(
            tx, ledger_api, [crypto], sleep_time
        )

    @classmethod
    def _deploy_contract(
        cls,
        contract: Contract,
        ledger_api: LedgerApi,
        deployer_crypto: Crypto,
        gas: int,
    ) -> JSONLike:
        """
        Deploy contract on network.

        :param contract: the contract
        :param ledger_api: the ledger api
        :param deployer_crypto: the contract deployer crypto
        :param gas: the gas amount

        :return: the transaction receipt for initial transaction deployment
        """
        tx = contract.get_deploy_transaction(
            ledger_api=ledger_api, deployer_address=deployer_crypto.address, gas=gas,
        )

        if tx is None:
            raise ValueError("Deploy transaction not found!")  # pragma: nocover

        tx_receipt = cls.sign_send_confirm_receipt_multisig_transaction(
            tx, ledger_api, [deployer_crypto]
        )

        return tx_receipt
