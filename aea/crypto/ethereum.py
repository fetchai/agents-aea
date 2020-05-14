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

import logging
import time
from pathlib import Path
from typing import Any, BinaryIO, Dict, Optional, Tuple, cast

from eth_account import Account
from eth_account.datastructures import AttributeDict
from eth_account.messages import encode_defunct

from eth_keys import keys

import web3
from web3 import HTTPProvider, Web3

from aea.crypto.base import Crypto, LedgerApi
from aea.mail.base import Address

logger = logging.getLogger(__name__)

ETHEREUM = "ethereum"
ETHEREUM_CURRENCY = "ETH"
DEFAULT_GAS_PRICE = "50"
GAS_ID = "gwei"


class EthereumCrypto(Crypto):
    """Class wrapping the Account Generation from Ethereum ledger."""

    identifier = ETHEREUM

    def __init__(self, private_key_path: Optional[str] = None):
        """
        Instantiate an ethereum crypto object.

        :param private_key_path: the private key path of the agent
        """
        self._account = (
            self._generate_private_key()
            if private_key_path is None
            else self._load_private_key_from_path(private_key_path)
        )
        bytes_representation = Web3.toBytes(hexstr=self._account.key.hex())
        self._public_key = str(keys.PrivateKey(bytes_representation).public_key)
        self._address = str(self._account.address)

    @property
    def entity(self) -> Account:
        """Get the entity."""
        return self._account

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

    def _load_private_key_from_path(self, file_name) -> Account:
        """
        Load a private key in hex format from a file.

        :param file_name: the path to the hex file.
        :return: the Entity.
        """
        path = Path(file_name)
        try:
            if path.is_file():
                with open(path, "r") as key:
                    data = key.read()
                    account = Account.from_key(data)
            else:
                account = self._generate_private_key()
            return account
        except IOError as e:  # pragma: no cover
            logger.exception(str(e))

    def sign_message(self, message: bytes, is_deprecated_mode: bool = False) -> str:
        """
        Sign a message in bytes string form.

        :param message: the message to be signed
        :param is_deprecated_mode: if the deprecated signing is used
        :return: signature of the message in string form
        """
        if is_deprecated_mode:
            assert len(message) == 32, "Message must be hashed to exactly 32 bytes."
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

    def recover_message(
        self, message: bytes, signature: str, is_deprecated_mode: bool = False
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
            address = Account.recoverHash(message_hash=message, signature=signature)
        else:
            signable_message = encode_defunct(primitive=message)
            address = Account.recover_message(
                signable_message=signable_message, signature=signature
            )
        return (address,)

    @classmethod
    def _generate_private_key(cls) -> Account:
        """Generate a key pair for ethereum network."""
        account = Account.create()
        return account

    @classmethod
    def get_address_from_public_key(cls, public_key: str) -> str:
        """
        Get the address from the public key.

        :param public_key: the public key
        :return: str
        """
        keccak_hash = Web3.keccak(hexstr=public_key)
        raw_address = keccak_hash[-20:].hex().upper()
        address = Web3.toChecksumAddress(raw_address)
        return address

    @classmethod
    def load(cls, fp: BinaryIO):
        """
        Deserialize binary file `fp` (a `.read()`-supporting file-like object containing a private key).

        :param fp: the input file pointer. Must be set in binary mode (mode='rb')
        :return: None
        """
        raise NotImplementedError  # pragma: no cover

    def dump(self, fp: BinaryIO) -> None:
        """
        Serialize crypto object as binary stream to `fp` (a `.write()`-supporting file-like object).

        :param fp: the output file pointer. Must be set in binary mode (mode='wb')
        :return: None
        """
        fp.write(self._account.key.hex().encode("utf-8"))


class EthereumApi(LedgerApi):
    """Class to interact with the Ethereum Web3 APIs."""

    identifier = ETHEREUM

    def __init__(self, address: str, gas_price: str = DEFAULT_GAS_PRICE):
        """
        Initialize the Ethereum ledger APIs.

        :param address: the endpoint for Web3 APIs.
        """
        self._api = Web3(HTTPProvider(endpoint_uri=address))
        self._gas_price = gas_price

    @property
    def api(self) -> Web3:
        """Get the underlying API object."""
        return self._api

    def get_balance(self, address: Address) -> Optional[int]:
        """Get the balance of a given account."""
        return self._try_get_balance(address)

    def _try_get_balance(self, address: Address) -> Optional[int]:
        """Get the balance of a given account."""
        try:
            balance = self._api.eth.getBalance(address)
        except Exception as e:
            logger.warning("Unable to retrieve balance: {}".format(str(e)))
            balance = None
        return balance

    def transfer(
        self,
        crypto: Crypto,
        destination_address: Address,
        amount: int,
        tx_fee: int,
        tx_nonce: str,
        chain_id: int = 1,
        **kwargs,
    ) -> Optional[str]:
        """
        Submit a transfer transaction to the ledger.

        :param crypto: the crypto object associated to the payer.
        :param destination_address: the destination address of the payee.
        :param amount: the amount of wealth to be transferred.
        :param tx_fee: the transaction fee.
        :param tx_nonce: verifies the authenticity of the tx
        :param chain_id: the Chain ID of the Ethereum transaction. Default is 1 (i.e. mainnet).
        :return: tx digest if present, otherwise None
        """
        tx_digest = None
        nonce = self._try_get_transaction_count(crypto.address)
        if nonce is None:
            return tx_digest

        transaction = {
            "nonce": nonce,
            "chainId": chain_id,
            "to": destination_address,
            "value": amount,
            "gas": tx_fee,
            "gasPrice": self._api.toWei(self._gas_price, GAS_ID),
            "data": tx_nonce,
        }

        gas_estimate = self._try_get_gas_estimate(transaction)
        if gas_estimate is None or tx_fee <= gas_estimate:  # pragma: no cover
            logger.warning(
                "Need to increase tx_fee in the configs to cover the gas consumption of the transaction. Estimated gas consumption is: {}.".format(
                    gas_estimate
                )
            )
            return tx_digest

        signed_transaction = crypto.sign_transaction(transaction)

        tx_digest = self.send_signed_transaction(tx_signed=signed_transaction,)

        return tx_digest

    def _try_get_transaction_count(self, address: Address) -> Optional[int]:
        """Try get the transaction count."""
        try:
            nonce = self._api.eth.getTransactionCount(
                self._api.toChecksumAddress(address)
            )
        except Exception as e:  # pragma: no cover
            logger.warning("Unable to retrieve transaction count: {}".format(str(e)))
            nonce = None
        return nonce

    def _try_get_gas_estimate(self, transaction: Dict[str, str]) -> Optional[int]:
        """Try get the gas estimate."""
        try:
            gas_estimate = self._api.eth.estimateGas(transaction=transaction)
        except Exception as e:  # pragma: no cover
            logger.warning("Unable to retrieve transaction count: {}".format(str(e)))
            gas_estimate = None
        return gas_estimate

    def send_signed_transaction(self, tx_signed: Any) -> Optional[str]:
        """
        Send a signed transaction and wait for confirmation.

        :param tx_signed: the signed transaction
        :return: tx_digest, if present
        """
        tx_digest = self._try_send_signed_transaction(tx_signed)
        return tx_digest

    def _try_send_signed_transaction(self, tx_signed: Any) -> Optional[str]:
        """Try send a signed transaction."""
        try:
            tx_signed = cast(AttributeDict, tx_signed)
            hex_value = self._api.eth.sendRawTransaction(tx_signed.rawTransaction)
            tx_digest = hex_value.hex()
            logger.debug(
                "Successfully sent transaction with digest: {}".format(tx_digest)
            )
        except Exception as e:  # pragma: no cover
            logger.warning("Unable to send transaction: {}".format(str(e)))
            tx_digest = None
        return tx_digest

    def is_transaction_settled(self, tx_digest: str) -> bool:
        """
        Check whether a transaction is settled or not.

        :param tx_digest: the digest associated to the transaction.
        :return: True if the transaction has been settled, False o/w.
        """
        is_successful = False
        tx_receipt = self.get_transaction_receipt(tx_digest)
        if tx_receipt is not None:
            is_successful = tx_receipt.status == 1
        return is_successful

    def get_transaction_receipt(self, tx_digest: str) -> Optional[Any]:
        """
        Get the transaction receipt for a transaction digest (non-blocking).

        :param tx_digest: the digest associated to the transaction.
        :return: the tx receipt, if present
        """
        tx_receipt = self._try_get_transaction_receipt(tx_digest)
        return tx_receipt

    def _try_get_transaction_receipt(self, tx_digest: str) -> Optional[Any]:
        """
        Try get the transaction receipt (non-blocking).

        :param tx_digest: the digest associated to the transaction.
        :return: the tx receipt, if present
        """
        try:
            tx_receipt = self._api.eth.getTransactionReceipt(tx_digest)
        except web3.exceptions.TransactionNotFound as e:
            logger.debug("Error when attempting getting tx receipt: {}".format(str(e)))
            tx_receipt = None
        return tx_receipt

    def generate_tx_nonce(self, seller: Address, client: Address) -> str:
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

    def is_transaction_valid(
        self,
        tx_digest: str,
        seller: Address,
        client: Address,
        tx_nonce: str,
        amount: int,
    ) -> bool:
        """
        Check whether a transaction is valid or not (non-blocking).

        :param tx_digest: the transaction digest.
        :param seller: the address of the seller.
        :param client: the address of the client.
        :param tx_nonce: the transaction nonce.
        :param amount: the amount we expect to get from the transaction.
        :return: True if the random_message is equals to tx['input']
        """
        is_valid = False
        tx = self._try_get_transaction(tx_digest)
        if tx is not None:
            is_valid = (
                tx.get("input") == tx_nonce
                and tx.get("value") == amount
                and tx.get("from") == client
                and tx.get("to") == seller
            )
        return is_valid

    def _try_get_transaction(self, tx_digest: str) -> Optional[Any]:
        """
        Get the transaction (non-blocking).

        :param tx_digest: the transaction digest.
        :return: the tx, if found
        """
        try:
            tx = self._api.eth.getTransaction(tx_digest)
        except Exception as e:  # pragma: no cover
            logger.debug("Error when attempting getting tx: {}".format(str(e)))
            tx = None
        return tx
