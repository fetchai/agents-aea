# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------
#
#   Copyright 2018-2019 Fetch.AI Limited
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""Ethereum module wrapping the public and private key cryptography and ledger api."""
import time

import web3
from eth_account.messages import SignableMessage
from web3 import Web3, HTTPProvider
from eth_account import Account
from eth_keys import keys
import logging
from pathlib import Path
from typing import Optional, BinaryIO

from aea.crypto.base import Crypto, LedgerApi, AddressLike

logger = logging.getLogger(__name__)

ETHEREUM = "ethereum"
GAS_PRICE = '50'
GAS_ID = 'gwei'


class EthereumCrypto(Crypto):
    """Class wrapping the Account Generation from Ethereum ledger."""

    identifier = ETHEREUM

    def __init__(self, private_key_path: Optional[str] = None):
        """
        Instantiate an ethereum crypto object.

        :param private_key_path: the private key path of the agent
        """
        self._account = self._generate_private_key() if private_key_path is None else self._load_private_key_from_path(private_key_path)
        bytes_representation = Web3.toBytes(hexstr=self._account.key.hex())
        self._public_key = keys.PrivateKey(bytes_representation).public_key

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
        return str(self._account.address)

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
        except IOError as e:        # pragma: no cover
            logger.exception(str(e))

    def sign_transaction(self, tx_hash: SignableMessage) -> bytes:
        """
        Sign a transaction hash.

        :param tx_hash: the transaction hash
        :return: Signed message in bytes
        """
        signature = self.entity.sign_message(tx_hash)
        return signature['signature']

    # def recover_from_hash(self, tx_hash: bytes, signature: bytes) -> Address:
    #     """
    #     Recover the address from the hash.

    #     :param tx_hash: the transaction hash
    #     :param signature: the transaction signature
    #     :return: the recovered address
    #     """
    #     address = self.entity.recoverHash(tx_hash, signature=signature)
    #     return address

    def _generate_private_key(self) -> Account:
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
        raise NotImplementedError  # pragma: no cover

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

    def __init__(self, address: str):
        """
        Initialize the Ethereum ledger APIs.

        :param address: the endpoint for Web3 APIs.
        """
        self._api = Web3(HTTPProvider(endpoint_uri=address))

    @property
    def api(self) -> Web3:
        """Get the underlying API object."""
        return self._api

    def get_balance(self, address: AddressLike) -> int:
        """Get the balance of a given account."""
        return self._api.eth.getBalance(address)

    def send_transaction(self,
                         crypto: Crypto,
                         destination_address: AddressLike,
                         amount: int,
                         tx_fee: int,
                         chain_id: int = 1,
                         **kwargs) -> Optional[str]:
        """
        Submit a transaction to the ledger.

        :param crypto: the crypto object associated to the payer.
        :param destination_address: the destination address of the payee.
        :param amount: the amount of wealth to be transferred.
        :param tx_fee: the transaction fee.
        :param chain_id: the Chain ID of the Ethereum transaction. Default is 1 (i.e. mainnet).
        :return: the transaction digest, or None if not available.
        """
        nonce = self._api.eth.getTransactionCount(self._api.toChecksumAddress(crypto.address))
        # TODO : handle misconfiguration
        transaction = {
            'nonce': nonce,
            'chainId': chain_id,
            'to': destination_address,
            'value': amount,
            'gas': tx_fee,
            'gasPrice': self._api.toWei(GAS_PRICE, GAS_ID)
        }
        signed = self._api.eth.account.signTransaction(transaction, crypto.entity.key)
        hex_value = self._api.eth.sendRawTransaction(signed.rawTransaction)
        logger.info("TX Hash: {}".format(str(hex_value.hex())))
        while True:
            try:
                self._api.eth.getTransactionReceipt(hex_value)
                logger.info("transaction validated - exiting")
                tx_digest = hex_value.hex()
                break
            except web3.exceptions.TransactionNotFound:  # pragma: no cover
                logger.info("transaction not found - sleeping for 3.0 seconds")
                time.sleep(3.0)
        return tx_digest

    def is_transaction_settled(self, tx_digest: str) -> bool:
        """Check whether a transaction is settled or not."""
        tx_status = self._api.eth.getTransactionReceipt(tx_digest)
        is_successful = False
        if tx_status is not None:
            is_successful = True
        return is_successful
