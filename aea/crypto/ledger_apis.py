# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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
from typing import Any, Dict, Optional, Tuple, Union

from aea.common import Address
from aea.configurations.constants import (
    DEFAULT_LEDGER,
    _COSMOS_IDENTIFIER,
    _ETHEREUM_IDENTIFIER,
    _FETCHAI_IDENTIFIER,
)
from aea.crypto.base import LedgerApi
from aea.crypto.registries import (
    ledger_apis_registry,
    make_ledger_api,
    make_ledger_api_cls,
)
from aea.exceptions import enforce


COSMOS_DEFAULT_ADDRESS = "INVALID_URL"
COSMOS_DEFAULT_CURRENCY_DENOM = "INVALID_CURRENCY_DENOM"
COSMOS_DEFAULT_CHAIN_ID = "INVALID_CHAIN_ID"
ETHEREUM_DEFAULT_ADDRESS = "http://127.0.0.1:8545"
ETHEREUM_DEFAULT_CHAIN_ID = 1337
ETHEREUM_DEFAULT_CURRENCY_DENOM = "wei"
FETCHAI_DEFAULT_ADDRESS = "https://rest-dorado.fetch.ai:443"
FETCHAI_DEFAULT_CURRENCY_DENOM = "atestfet"
FETCHAI_DEFAULT_CHAIN_ID = "dorado-1"


DEFAULT_LEDGER_CONFIGS: Dict[str, Dict[str, Union[str, int]]] = {
    _COSMOS_IDENTIFIER: {
        "address": COSMOS_DEFAULT_ADDRESS,
        "chain_id": COSMOS_DEFAULT_CHAIN_ID,
        "denom": COSMOS_DEFAULT_CURRENCY_DENOM,
    },
    _ETHEREUM_IDENTIFIER: {
        "address": ETHEREUM_DEFAULT_ADDRESS,
        "chain_id": ETHEREUM_DEFAULT_CHAIN_ID,
        "denom": ETHEREUM_DEFAULT_CURRENCY_DENOM,
    },
    _FETCHAI_IDENTIFIER: {
        "address": FETCHAI_DEFAULT_ADDRESS,
        "chain_id": FETCHAI_DEFAULT_CHAIN_ID,
        "denom": FETCHAI_DEFAULT_CURRENCY_DENOM,
    },
}
DEFAULT_CURRENCY_DENOMINATIONS = {
    _COSMOS_IDENTIFIER: COSMOS_DEFAULT_CURRENCY_DENOM,
    _ETHEREUM_IDENTIFIER: ETHEREUM_DEFAULT_CURRENCY_DENOM,
    _FETCHAI_IDENTIFIER: FETCHAI_DEFAULT_CURRENCY_DENOM,
}


class LedgerApis:
    """Store all the ledger apis we initialise."""

    ledger_api_configs: Dict[str, Dict[str, Union[str, int]]] = DEFAULT_LEDGER_CONFIGS

    @staticmethod
    def has_ledger(identifier: str) -> bool:
        """Check if it has the api."""
        return identifier in ledger_apis_registry.supported_ids

    @classmethod
    def get_api(cls, identifier: str) -> LedgerApi:
        """Get the ledger API."""
        enforce(
            identifier in ledger_apis_registry.supported_ids,
            "Not a registered ledger api identifier.",
        )
        api = make_ledger_api(identifier, **cls.ledger_api_configs[identifier])
        return api

    @classmethod
    def get_balance(cls, identifier: str, address: str) -> Optional[int]:
        """
        Get the token balance.

        :param identifier: the identifier of the ledger
        :param address: the address to check for
        :return: the token balance
        """
        enforce(
            identifier in ledger_apis_registry.supported_ids,
            "Not a registered ledger api identifier.",
        )
        api = make_ledger_api(identifier, **cls.ledger_api_configs[identifier])
        balance = api.get_balance(address)
        return balance

    @classmethod
    def get_transfer_transaction(
        cls,
        identifier: str,
        sender_address: str,
        destination_address: str,
        amount: int,
        tx_fee: int,
        tx_nonce: str,
        **kwargs: Any,
    ) -> Optional[Any]:
        """
        Get a transaction to transfer from self to destination.

        :param identifier: the identifier of the ledger
        :param sender_address: the address of the sender
        :param destination_address: the address of the receiver
        :param amount: the amount
        :param tx_nonce: verifies the authenticity of the tx
        :param tx_fee: the tx fee
        :param kwargs: the keyword arguments.

        :return: tx
        """
        enforce(
            identifier in ledger_apis_registry.supported_ids,
            "Not a registered ledger api identifier.",
        )
        api = make_ledger_api(identifier, **cls.ledger_api_configs[identifier])
        tx = api.get_transfer_transaction(
            sender_address,
            destination_address,
            amount,
            tx_fee,
            tx_nonce,
            **kwargs,
        )
        return tx

    @classmethod
    def send_signed_transaction(cls, identifier: str, tx_signed: Any) -> Optional[str]:
        """
        Send a signed transaction and wait for confirmation.

        :param identifier: the identifier of the ledger
        :param tx_signed: the signed transaction
        :return: the tx_digest, if present
        """
        enforce(
            identifier in ledger_apis_registry.supported_ids,
            "Not a registered ledger api identifier.",
        )
        api = make_ledger_api(identifier, **cls.ledger_api_configs[identifier])
        tx_digest = api.send_signed_transaction(tx_signed)
        return tx_digest

    @classmethod
    def get_transaction_receipt(cls, identifier: str, tx_digest: str) -> Optional[Any]:
        """
        Get the transaction receipt for a transaction digest.

        :param identifier: the identifier of the ledger
        :param tx_digest: the digest associated to the transaction.
        :return: the tx receipt, if present
        """
        enforce(
            identifier in ledger_apis_registry.supported_ids,
            "Not a registered ledger api identifier.",
        )
        api = make_ledger_api(identifier, **cls.ledger_api_configs[identifier])
        tx_receipt = api.get_transaction_receipt(tx_digest)
        return tx_receipt

    @classmethod
    def get_transaction(cls, identifier: str, tx_digest: str) -> Optional[Any]:
        """
        Get the transaction for a transaction digest.

        :param identifier: the identifier of the ledger
        :param tx_digest: the digest associated to the transaction.
        :return: the tx, if present
        """
        enforce(
            identifier in ledger_apis_registry.supported_ids,
            "Not a registered ledger api identifier.",
        )
        api = make_ledger_api(identifier, **cls.ledger_api_configs[identifier])
        tx = api.get_transaction(tx_digest)
        return tx

    @staticmethod
    def get_contract_address(identifier: str, tx_receipt: Any) -> Optional[Address]:
        """
        Get the contract address from a transaction receipt.

        :param identifier: the identifier of the ledger
        :param tx_receipt: the transaction receipt
        :return: the contract address if successful
        """
        enforce(
            identifier in ledger_apis_registry.supported_ids,
            "Not a registered ledger api identifier.",
        )
        api_class = make_ledger_api_cls(identifier)
        address = api_class.get_contract_address(tx_receipt)
        return address

    @staticmethod
    def is_transaction_settled(identifier: str, tx_receipt: Any) -> bool:
        """
        Check whether the transaction is settled and correct.

        :param identifier: the identifier of the ledger
        :param tx_receipt: the transaction digest
        :return: True if correctly settled, False otherwise
        """
        enforce(
            identifier in ledger_apis_registry.supported_ids,
            "Not a registered ledger api identifier.",
        )
        api_class = make_ledger_api_cls(identifier)
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
        enforce(
            identifier in ledger_apis_registry.supported_ids,
            "Not a registered ledger api identifier.",
        )
        api_class = make_ledger_api_cls(identifier)
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
        enforce(
            identifier in ledger_apis_registry.supported_ids,
            "Not a registered ledger api identifier.",
        )
        api_class = make_ledger_api_cls(identifier)
        tx_nonce = api_class.generate_tx_nonce(seller=seller, client=client)
        return tx_nonce

    @staticmethod
    def recover_message(
        identifier: str,
        message: bytes,
        signature: str,
        is_deprecated_mode: bool = False,
    ) -> Tuple[Address, ...]:
        """
        Recover the addresses from the hash.

        :param identifier: ledger identifier.
        :param message: the message we expect
        :param signature: the transaction signature
        :param is_deprecated_mode: if the deprecated signing was used
        :return: the recovered addresses
        """
        enforce(
            identifier in ledger_apis_registry.supported_ids,
            "Not a registered ledger api identifier.",
        )
        api_class = make_ledger_api_cls(identifier)
        addresses = api_class.recover_message(
            message=message, signature=signature, is_deprecated_mode=is_deprecated_mode
        )
        return addresses

    @staticmethod
    def get_hash(identifier: str, message: bytes) -> str:
        """
        Get the hash of a message.

        :param identifier: ledger identifier.
        :param message: the message to be hashed.
        :return: the hash of the message.
        """
        identifier = (
            identifier
            if identifier in ledger_apis_registry.supported_ids
            else DEFAULT_LEDGER
        )
        api_class = make_ledger_api_cls(identifier)
        digest = api_class.get_hash(message=message)
        return digest

    @staticmethod
    def is_valid_address(identifier: str, address: Address) -> bool:
        """
        Check if the address is valid.

        :param identifier: ledger identifier.
        :param address: the address to validate.
        :return: whether it is a valid address or not.
        """
        identifier = (
            identifier
            if identifier in ledger_apis_registry.supported_ids
            else DEFAULT_LEDGER
        )
        api_class = make_ledger_api_cls(identifier)
        result = api_class.is_valid_address(address=address)
        return result
