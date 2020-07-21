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

"""Module wrapping all the public and private keys cryptography."""
import logging
from typing import Any, Dict, Optional, Type, Union

from aea.crypto.base import LedgerApi
from aea.crypto.cosmos import CosmosApi
from aea.crypto.cosmos import DEFAULT_ADDRESS as COSMOS_DEFAULT_ADDRESS
from aea.crypto.ethereum import DEFAULT_ADDRESS as ETHEREUM_DEFAULT_ADDRESS
from aea.crypto.ethereum import DEFAULT_CHAIN_ID, EthereumApi
from aea.crypto.fetchai import DEFAULT_NETWORK, FetchAIApi
from aea.crypto.registries import make_ledger_api
from aea.mail.base import Address

SUPPORTED_LEDGER_APIS = {
    CosmosApi.identifier: CosmosApi,
    EthereumApi.identifier: EthereumApi,
    FetchAIApi.identifier: FetchAIApi,
}  # type: Dict[str, Type[LedgerApi]]
DEFAULT_LEDGER_CONFIGS = {
    CosmosApi.identifier: {"address": COSMOS_DEFAULT_ADDRESS},
    EthereumApi.identifier: {
        "address": ETHEREUM_DEFAULT_ADDRESS,
        "chain_id": DEFAULT_CHAIN_ID,
    },
    FetchAIApi.identifier: {"network": DEFAULT_NETWORK},
}  # type: Dict[str, Dict[str, Union[str, int]]]

logger = logging.getLogger(__name__)


class LedgerApis:
    """Store all the ledger apis we initialise."""

    def __init__(
        self,
        ledger_api_configs: Dict[str, Dict[str, Union[str, int]]],
        default_ledger_id: str,
    ):
        """
        Instantiate a wallet object.

        :param ledger_api_configs: the ledger api configs.
        :param default_ledger_id: the default ledger id.
        """
        apis = {}  # type: Dict[str, LedgerApi]
        for identifier, config in ledger_api_configs.items():
            api = make_ledger_api(identifier, **config)
            apis[identifier] = api
        self._apis = apis
        self._configs = ledger_api_configs
        self._default_ledger_id = default_ledger_id

    @property
    def configs(self) -> Dict[str, Dict[str, Union[str, int]]]:
        """Get the configs."""
        return self._configs

    @property
    def apis(self) -> Dict[str, LedgerApi]:
        """Get the apis."""
        return self._apis

    def has_ledger(self, identifier: str) -> bool:
        """Check if it has a ."""
        return identifier in self.apis

    def get_api(self, identifier: str) -> LedgerApi:
        """Get the ledger API."""
        assert self.has_ledger(identifier), "Ledger API not instantiated!"
        return self.apis[identifier]

    @property
    def has_default_ledger(self) -> bool:
        """Check if it has the default ledger API."""
        return self.default_ledger_id in self.apis.keys()

    @property
    def default_ledger_id(self) -> str:
        """Get the default ledger id."""
        return self._default_ledger_id

    def get_balance(self, identifier: str, address: str) -> Optional[int]:
        """
        Get the token balance.

        :param identifier: the identifier of the ledger
        :param address: the address to check for
        :return: the token balance
        """
        assert identifier in self.apis.keys(), "Not a registered ledger api identifier."
        api = self.apis[identifier]
        balance = api.get_balance(address)
        return balance

    def get_transfer_transaction(
        self,
        identifier: str,
        sender_address: str,
        destination_address: str,
        amount: int,
        tx_fee: int,
        tx_nonce: str,
        **kwargs,
    ) -> Optional[Any]:
        """
        Get a transaction to transfer from self to destination.

        :param identifier: the identifier of the ledger
        :param sender_address: the address of the sender
        :param destination_address: the address of the receiver
        :param amount: the amount
        :param tx_nonce: verifies the authenticity of the tx
        :param tx_fee: the tx fee

        :return: tx
        """
        assert identifier in self.apis.keys(), "Not a registered ledger api identifier."
        api = self.apis[identifier]
        tx = api.get_transfer_transaction(
            sender_address, destination_address, amount, tx_fee, tx_nonce, **kwargs,
        )
        return tx

    def send_signed_transaction(self, identifier: str, tx_signed: Any) -> Optional[str]:
        """
        Send a signed transaction and wait for confirmation.

        :param identifier: the identifier of the ledger
        :param tx_signed: the signed transaction
        :return: the tx_digest, if present
        """
        assert identifier in self.apis.keys(), "Not a registered ledger api identifier."
        api = self.apis[identifier]
        tx_digest = api.send_signed_transaction(tx_signed)
        return tx_digest

    def get_transaction_receipt(self, identifier: str, tx_digest: str) -> Optional[Any]:
        """
        Get the transaction receipt for a transaction digest.

        :param identifier: the identifier of the ledger
        :param tx_digest: the digest associated to the transaction.
        :return: the tx receipt, if present
        """
        assert identifier in self.apis.keys(), "Not a registered ledger api identifier."
        api = self.apis[identifier]
        tx_receipt = api.get_transaction_receipt(tx_digest)
        return tx_receipt

    def get_transaction(self, identifier: str, tx_digest: str) -> Optional[Any]:
        """
        Get the transaction for a transaction digest.

        :param identifier: the identifier of the ledger
        :param tx_digest: the digest associated to the transaction.
        :return: the tx, if present
        """
        assert identifier in self.apis.keys(), "Not a registered ledger api identifier."
        api = self.apis[identifier]
        tx = api.get_transaction(tx_digest)
        return tx

    @staticmethod
    def is_transaction_settled(identifier: str, tx_receipt: Any) -> bool:
        """
        Check whether the transaction is settled and correct.

        :param identifier: the identifier of the ledger
        :param tx_receipt: the transaction digest
        :return: True if correctly settled, False otherwise
        """
        assert (
            identifier in SUPPORTED_LEDGER_APIS.keys()
        ), "Not a registered ledger api identifier."
        api_class = SUPPORTED_LEDGER_APIS[identifier]
        is_settled = api_class.is_transaction_settled(tx_receipt)
        return is_settled

    @staticmethod
    def is_transaction_valid(
        identifier: str,
        tx: Any,
        seller: Address,
        client: Address,
        tx_nonce: str,
        amount: int,
    ) -> bool:
        """
        Check whether the transaction is valid.

        :param identifier: Ledger identifier
        :param tx:  the transaction
        :param seller: the address of the seller.
        :param client: the address of the client.
        :param tx_nonce: the transaction nonce.
        :param amount: the amount we expect to get from the transaction.
        :return: True if is valid , False otherwise
        """
        assert (
            identifier in SUPPORTED_LEDGER_APIS.keys()
        ), "Not a registered ledger api identifier."
        api_class = SUPPORTED_LEDGER_APIS[identifier]
        is_valid = api_class.is_transaction_valid(tx, seller, client, tx_nonce, amount)
        return is_valid

    @staticmethod
    def generate_tx_nonce(identifier: str, seller: Address, client: Address) -> str:
        """
        Generate a random str message.

        :param identifier: ledger identifier.
        :param seller: the address of the seller.
        :param client: the address of the client.
        :return: return the hash in hex.
        """
        assert (
            identifier in SUPPORTED_LEDGER_APIS.keys()
        ), "Not a registered ledger api identifier."
        api_class = SUPPORTED_LEDGER_APIS[identifier]
        tx_nonce = api_class.generate_tx_nonce(seller=seller, client=client)
        return tx_nonce
