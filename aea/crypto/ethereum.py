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

"""Ethereum module wrapping the public and private key cryptography and ledger api."""

import json
import logging
import time
from pathlib import Path
from typing import Any, BinaryIO, Dict, Optional, Tuple, Union, cast

from eth_account import Account
from eth_account.datastructures import AttributeDict
from eth_account.messages import encode_defunct

from eth_keys import keys

import requests

from web3 import HTTPProvider, Web3

from aea.crypto.base import Crypto, FaucetApi, Helper, LedgerApi
from aea.helpers.base import try_decorator
from aea.mail.base import Address

logger = logging.getLogger(__name__)

_ETHEREUM = "ethereum"
GAS_ID = "gwei"
ETHEREUM_TESTNET_FAUCET_URL = "https://faucet.ropsten.be/donate/"
DEFAULT_ADDRESS = "https://ropsten.infura.io/v3/f00f7b3ba0e848ddbdc8941c527447fe"
DEFAULT_CHAIN_ID = 3
DEFAULT_GAS_PRICE = "50"


class EthereumCrypto(Crypto[Account]):
    """Class wrapping the Account Generation from Ethereum ledger."""

    identifier = _ETHEREUM

    def __init__(self, private_key_path: Optional[str] = None):
        """
        Instantiate an ethereum crypto object.

        :param private_key_path: the private key path of the agent
        """
        super().__init__(private_key_path=private_key_path)
        bytes_representation = Web3.toBytes(hexstr=self.entity.key.hex())
        self._public_key = str(keys.PrivateKey(bytes_representation).public_key)
        self._address = str(self.entity.address)

    @property
    def private_key(self) -> str:
        """
        Return a private key.

        :return: a private key string
        """
        return self.entity.key.hex()

    @property
    def public_key(self) -> str:
        """
        Return a public key in hex format.

        :return: a public key string in hex format
        """
        return self._public_key

    @property
    def address(self) -> str:
        """
        Return the address for the key pair.

        :return: a display_address str
        """
        return self._address

    @classmethod
    def load_private_key_from_path(cls, file_name) -> Account:
        """
        Load a private key in hex format from a file.

        :param file_name: the path to the hex file.
        :return: the Entity.
        """
        path = Path(file_name)
        with open(path, "r") as key:
            data = key.read()
            account = Account.from_key(  # pylint: disable=no-value-for-parameter
                private_key=data
            )
        return account

    def sign_message(self, message: bytes, is_deprecated_mode: bool = False) -> str:
        """
        Sign a message in bytes string form.

        :param message: the message to be signed
        :param is_deprecated_mode: if the deprecated signing is used
        :return: signature of the message in string form
        """
        if is_deprecated_mode and len(message) == 32:
            signature_dict = self.entity.signHash(message)
            signed_msg = signature_dict["signature"].hex()
        else:
            signable_message = encode_defunct(primitive=message)
            signature = self.entity.sign_message(signable_message=signable_message)
            signed_msg = signature["signature"].hex()
        return signed_msg

    def sign_transaction(self, transaction: Any) -> Any:
        """
        Sign a transaction in bytes string form.

        :param transaction: the transaction to be signed
        :return: signed transaction
        """
        signed_transaction = self.entity.sign_transaction(transaction_dict=transaction)
        #  Note: self.entity.signTransaction(transaction_dict=transaction) == signed_transaction
        return signed_transaction

    @classmethod
    def generate_private_key(cls) -> Account:
        """Generate a key pair for ethereum network."""
        account = Account.create()  # pylint: disable=no-value-for-parameter
        return account

    def dump(self, fp: BinaryIO) -> None:
        """
        Serialize crypto object as binary stream to `fp` (a `.write()`-supporting file-like object).

        :param fp: the output file pointer. Must be set in binary mode (mode='wb')
        :return: None
        """
        fp.write(self.private_key.encode("utf-8"))


class EthereumHelper(Helper):
    """Helper class usable as Mixin for EthereumApi or as standalone class."""

    @staticmethod
    def is_transaction_settled(tx_receipt: Any) -> bool:
        """
        Check whether a transaction is settled or not.

        :param tx_digest: the digest associated to the transaction.
        :return: True if the transaction has been settled, False o/w.
        """
        is_successful = False
        if tx_receipt is not None:
            is_successful = tx_receipt.status == 1
        return is_successful

    @staticmethod
    def is_transaction_valid(
        tx: Any, seller: Address, client: Address, tx_nonce: str, amount: int,
    ) -> bool:
        """
        Check whether a transaction is valid or not.

        :param tx: the transaction.
        :param seller: the address of the seller.
        :param client: the address of the client.
        :param tx_nonce: the transaction nonce.
        :param amount: the amount we expect to get from the transaction.
        :return: True if the random_message is equals to tx['input']
        """
        is_valid = False
        if tx is not None:
            is_valid = (
                tx.get("input") == tx_nonce
                and tx.get("value") == amount
                and tx.get("from") == client
                and tx.get("to") == seller
            )
        return is_valid

    @staticmethod
    def generate_tx_nonce(seller: Address, client: Address) -> str:
        """
        Generate a unique hash to distinguish txs with the same terms.

        :param seller: the address of the seller.
        :param client: the address of the client.
        :return: return the hash in hex.
        """
        time_stamp = int(time.time())
        aggregate_hash = Web3.keccak(
            b"".join([seller.encode(), client.encode(), time_stamp.to_bytes(32, "big")])
        )
        return aggregate_hash.hex()

    @staticmethod
    def get_address_from_public_key(public_key: str) -> str:
        """
        Get the address from the public key.

        :param public_key: the public key
        :return: str
        """
        keccak_hash = Web3.keccak(hexstr=public_key)
        raw_address = keccak_hash[-20:].hex().upper()
        address = Web3.toChecksumAddress(raw_address)
        return address

    @staticmethod
    def recover_message(
        message: bytes, signature: str, is_deprecated_mode: bool = False
    ) -> Tuple[Address, ...]:
        """
        Recover the addresses from the hash.

        :param message: the message we expect
        :param signature: the transaction signature
        :param is_deprecated_mode: if the deprecated signing was used
        :return: the recovered addresses
        """
        if is_deprecated_mode:
            assert len(message) == 32, "Message must be hashed to exactly 32 bytes."
            address = Account.recoverHash(  # pylint: disable=no-value-for-parameter
                message_hash=message, signature=signature
            )
        else:
            signable_message = encode_defunct(primitive=message)
            address = Account.recover_message(  # pylint: disable=no-value-for-parameter
                signable_message=signable_message, signature=signature
            )
        return (address,)


class EthereumApi(LedgerApi, EthereumHelper):
    """Class to interact with the Ethereum Web3 APIs."""

    identifier = _ETHEREUM

    def __init__(self, **kwargs):
        """
        Initialize the Ethereum ledger APIs.

        :param address: the endpoint for Web3 APIs.
        """
        self._api = Web3(
            HTTPProvider(endpoint_uri=kwargs.pop("address", DEFAULT_ADDRESS))
        )
        self._gas_price = kwargs.pop("gas_price", DEFAULT_GAS_PRICE)
        self._chain_id = kwargs.pop("chain_id", DEFAULT_CHAIN_ID)

    @property
    def api(self) -> Web3:
        """Get the underlying API object."""
        return self._api

    def get_balance(self, address: Address) -> Optional[int]:
        """Get the balance of a given account."""
        return self._try_get_balance(address)

    @try_decorator("Unable to retrieve balance: {}", logger_method="warning")
    def _try_get_balance(self, address: Address) -> Optional[int]:
        """Get the balance of a given account."""
        return self._api.eth.getBalance(address)  # pylint: disable=no-member

    def get_transfer_transaction(  # pylint: disable=arguments-differ
        self,
        sender_address: Address,
        destination_address: Address,
        amount: int,
        tx_fee: int,
        tx_nonce: str,
        chain_id: Optional[int] = None,
        gas_price: Optional[str] = None,
        **kwargs,
    ) -> Optional[Any]:
        """
        Submit a transfer transaction to the ledger.

        :param sender_address: the sender address of the payer.
        :param destination_address: the destination address of the payee.
        :param amount: the amount of wealth to be transferred.
        :param tx_fee: the transaction fee.
        :param tx_nonce: verifies the authenticity of the tx
        :param chain_id: the Chain ID of the Ethereum transaction. Default is 3 (i.e. ropsten; mainnet has 1).
        :param gas_price: the gas price
        :return: the transfer transaction
        """
        chain_id = chain_id if chain_id is not None else self._chain_id
        gas_price = gas_price if gas_price is not None else self._gas_price
        nonce = self._try_get_transaction_count(sender_address)

        transaction = {
            "nonce": nonce,
            "chainId": chain_id,
            "to": destination_address,
            "value": amount,
            "gas": tx_fee,
            "gasPrice": self._api.toWei(gas_price, GAS_ID),
            "data": tx_nonce,
        }

        gas_estimate = self._try_get_gas_estimate(transaction)
        if gas_estimate is not None and tx_fee <= gas_estimate:  # pragma: no cover
            logger.warning(
                "Needed to increase tx_fee to cover the gas consumption of the transaction. Estimated gas consumption is: {}.".format(
                    gas_estimate
                )
            )
            transaction["gas"] = gas_estimate

        return transaction

    @try_decorator("Unable to retrieve transaction count: {}", logger_method="warning")
    def _try_get_transaction_count(self, address: Address) -> Optional[int]:
        """Try get the transaction count."""
        nonce = self._api.eth.getTransactionCount(  # pylint: disable=no-member
            self._api.toChecksumAddress(address)
        )
        return nonce

    @try_decorator("Unable to retrieve gas estimate: {}", logger_method="warning")
    def _try_get_gas_estimate(
        self, transaction: Dict[str, Union[str, int, None]]
    ) -> Optional[int]:
        """Try get the gas estimate."""
        gas_estimate = self._api.eth.estimateGas(  # pylint: disable=no-member
            transaction=transaction
        )
        return gas_estimate

    def send_signed_transaction(self, tx_signed: Any) -> Optional[str]:
        """
        Send a signed transaction and wait for confirmation.

        :param tx_signed: the signed transaction
        :return: tx_digest, if present
        """
        tx_digest = self._try_send_signed_transaction(tx_signed)
        return tx_digest

    @try_decorator("Unable to send transaction: {}", logger_method="warning")
    def _try_send_signed_transaction(self, tx_signed: Any) -> Optional[str]:
        """
        Try send a signed transaction.

        :param tx_signed: the signed transaction
        :return: tx_digest, if present
        """
        tx_signed = cast(AttributeDict, tx_signed)
        hex_value = self._api.eth.sendRawTransaction(  # pylint: disable=no-member
            tx_signed.rawTransaction
        )
        tx_digest = hex_value.hex()
        logger.debug("Successfully sent transaction with digest: {}".format(tx_digest))
        return tx_digest

    def get_transaction_receipt(self, tx_digest: str) -> Optional[Any]:
        """
        Get the transaction receipt for a transaction digest.

        :param tx_digest: the digest associated to the transaction.
        :return: the tx receipt, if present
        """
        tx_receipt = self._try_get_transaction_receipt(tx_digest)
        return tx_receipt

    @try_decorator(
        "Error when attempting getting tx receipt: {}", logger_method="debug"
    )
    def _try_get_transaction_receipt(self, tx_digest: str) -> Optional[Any]:
        """
        Try get the transaction receipt.

        :param tx_digest: the digest associated to the transaction.
        :return: the tx receipt, if present
        """
        tx_receipt = self._api.eth.getTransactionReceipt(  # pylint: disable=no-member
            tx_digest
        )
        return tx_receipt

    def get_transaction(self, tx_digest: str) -> Optional[Any]:
        """
        Get the transaction for a transaction digest.

        :param tx_digest: the digest associated to the transaction.
        :return: the tx, if present
        """
        tx = self._try_get_transaction(tx_digest)
        return tx

    @try_decorator("Error when attempting getting tx: {}", logger_method="debug")
    def _try_get_transaction(self, tx_digest: str) -> Optional[Any]:
        """
        Get the transaction.

        :param tx_digest: the transaction digest.
        :return: the tx, if found
        """
        tx = self._api.eth.getTransaction(tx_digest)  # pylint: disable=no-member
        return tx


class EthereumFaucetApi(FaucetApi):
    """Ethereum testnet faucet API."""

    identifier = _ETHEREUM

    def get_wealth(self, address: Address) -> None:
        """
        Get wealth from the faucet for the provided address.

        :param address: the address.
        :return: None
        """
        self._try_get_wealth(address)

    @staticmethod
    @try_decorator(
        "An error occured while attempting to generate wealth:\n{}",
        logger_method="error",
    )
    def _try_get_wealth(address: Address) -> None:
        """
        Get wealth from the faucet for the provided address.

        :param address: the address.
        :return: None
        """
        response = requests.get(ETHEREUM_TESTNET_FAUCET_URL + address)
        if response.status_code // 100 == 5:
            logger.error("Response: {}".format(response.status_code))
        elif response.status_code // 100 in [3, 4]:
            response_dict = json.loads(response.text)
            logger.warning(
                "Response: {}\nMessage: {}".format(
                    response.status_code, response_dict.get("message")
                )
            )
        elif response.status_code // 100 == 2:
            response_dict = json.loads(response.text)
            logger.info(
                "Response: {}\nMessage: {}".format(
                    response.status_code, response_dict.get("message")
                )
            )  # pragma: no cover
