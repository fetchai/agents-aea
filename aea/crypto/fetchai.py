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

"""Fetchai module wrapping the public and private key cryptography and ledger api."""

import logging
import time
from pathlib import Path
from typing import Any, BinaryIO, Optional, Tuple, cast

from fetchai.ledger.api import LedgerApi as FetchaiLedgerApi
from fetchai.ledger.api.tx import TxContents, TxStatus
from fetchai.ledger.crypto import Address as FetchaiAddress
from fetchai.ledger.crypto import Entity, Identity  # type: ignore
from fetchai.ledger.serialisation import sha256_hash

from aea.crypto.base import Crypto, LedgerApi
from aea.mail.base import Address

logger = logging.getLogger(__name__)

FETCHAI = "fetchai"
FETCHAI_CURRENCY = "FET"
SUCCESSFUL_TERMINAL_STATES = ("Executed", "Submitted")
DEFAULT_FETCHAI_CONFIG = {"network": "testnet"}


class FetchAICrypto(Crypto):
    """Class wrapping the Entity Generation from Fetch.AI ledger."""

    identifier = FETCHAI

    def __init__(self, private_key_path: Optional[str] = None):
        """
        Instantiate a fetchai crypto object.

        :param private_key_path: the private key path of the agent
        """
        self._entity = (
            self._generate_private_key()
            if private_key_path is None
            else self._load_private_key_from_path(private_key_path)
        )
        self._address = str(FetchaiAddress(Identity.from_hex(self.public_key)))

    @property
    def entity(self) -> Entity:
        """Get the entity."""
        return self._entity

    @property
    def public_key(self) -> str:
        """
        Return a public key in hex format.

        :return: a public key string in hex format
        """
        return self._entity.public_key_hex

    @property
    def address(self) -> str:
        """
        Return the address for the key pair.

        :return: a display_address str
        """
        return self._address

    def _load_private_key_from_path(self, file_name) -> Entity:
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
                    entity = Entity.from_hex(data)

            else:
                entity = self._generate_private_key()

            return entity
        except IOError as e:  # pragma: no cover
            logger.exception(str(e))

    @classmethod
    def _generate_private_key(cls) -> Entity:
        entity = Entity()
        return entity

    def sign_message(self, message: bytes, is_deprecated_mode: bool = False) -> str:
        """
        Sign a message in bytes string form.

        :param message: the message we want to send
        :param is_deprecated_mode: if the deprecated signing is used
        :return: signature of the message in string form
        """
        signature = self.entity.sign(message)
        return signature

    def sign_transaction(self, transaction: Any) -> Any:
        """
        Sign a transaction in bytes string form.

        :param transaction: the transaction to be signed
        :return: signed transaction
        """
        raise NotImplementedError

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
        raise NotImplementedError  # praggma: no cover

    @classmethod
    def get_address_from_public_key(cls, public_key: str) -> Address:
        """
        Get the address from the public key.

        :param public_key: the public key
        :return: str
        """
        identity = Identity.from_hex(public_key)
        address = str(FetchaiAddress(identity))
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
        fp.write(self.entity.private_key_hex.encode("utf-8"))


class FetchAIApi(LedgerApi):
    """Class to interact with the Fetch ledger APIs."""

    identifier = FETCHAI

    def __init__(self, **kwargs):
        """
        Initialize the Fetch.AI ledger APIs.

        :param kwargs: key word arguments (expects either a pair of 'host' and 'port' or a 'network')
        """
        self._api = FetchaiLedgerApi(**kwargs)

    @property
    def api(self) -> FetchaiLedgerApi:
        """Get the underlying API object."""
        return self._api

    def get_balance(self, address: Address) -> Optional[int]:
        """
        Get the balance of a given account.

        :param address: the address for which to retrieve the balance.
        :return: the balance, if retrivable, otherwise None
        """
        balance = self._try_get_balance(address)
        return balance

    def _try_get_balance(self, address: Address) -> Optional[int]:
        """Try get the balance."""
        try:
            balance = self._api.tokens.balance(FetchaiAddress(address))
        except Exception as e:
            logger.debug("Unable to retrieve balance: {}".format(str(e)))
            balance = None
        return balance

    def transfer(
        self,
        crypto: Crypto,
        destination_address: Address,
        amount: int,
        tx_fee: int,
        tx_nonce: str,
        is_waiting_for_confirmation: bool = True,
        **kwargs,
    ) -> Optional[str]:
        """Submit a transaction to the ledger."""
        tx_digest = self._try_transfer_tokens(
            crypto, destination_address, amount, tx_fee
        )
        return tx_digest

    def _try_transfer_tokens(
        self, crypto: Crypto, destination_address: Address, amount: int, tx_fee: int
    ) -> Optional[str]:
        """Try transfer tokens."""
        try:
            tx_digest = self._api.tokens.transfer(
                crypto.entity, FetchaiAddress(destination_address), amount, tx_fee
            )
            self._api.sync(tx_digest)
        except Exception as e:
            logger.debug("Error when attempting transfering tokens: {}".format(str(e)))
            tx_digest = None
        return tx_digest

    def send_signed_transaction(self, tx_signed: Any) -> Optional[str]:
        """
        Send a signed transaction and wait for confirmation.

        :param tx_signed: the signed transaction
        """
        raise NotImplementedError

    def is_transaction_settled(self, tx_digest: str) -> bool:
        """Check whether a transaction is settled or not."""
        tx_status = cast(TxStatus, self._try_get_transaction_receipt(tx_digest))
        is_successful = False
        if tx_status is not None:
            is_successful = tx_status.status in SUCCESSFUL_TERMINAL_STATES
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
        Get the transaction receipt (non-blocking).

        :param tx_digest: the transaction digest.
        :return: the transaction receipt, if found
        """
        try:
            tx_receipt = self._api.tx.status(tx_digest)
        except Exception as e:
            logger.debug("Error when attempting getting tx receipt: {}".format(str(e)))
            tx_receipt = None
        return tx_receipt

    def generate_tx_nonce(self, seller: Address, client: Address) -> str:
        """
        Generate a random str message.

        :param seller: the address of the seller.
        :param client: the address of the client.
        :return: return the hash in hex.
        """
        time_stamp = int(time.time())
        aggregate_hash = sha256_hash(
            b"".join([seller.encode(), client.encode(), time_stamp.to_bytes(32, "big")])
        )
        return aggregate_hash.hex()

    # TODO: Add the tx_nonce check here when the ledger supports extra data to the tx.
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

        :param seller: the address of the seller.
        :param client: the address of the client.
        :param tx_nonce: the transaction nonce.
        :param amount: the amount we expect to get from the transaction.
        :param tx_digest: the transaction digest.

        :return: True if the random_message is equals to tx['input']
        """
        is_valid = False
        tx_contents = self._try_get_transaction(tx_digest)
        if tx_contents is not None:
            seller_address = FetchaiAddress(seller)
            is_valid = (
                str(tx_contents.from_address) == client
                and amount == tx_contents.transfers[seller_address]
                and self.is_transaction_settled(tx_digest=tx_digest)
            )
        return is_valid

    def _try_get_transaction(self, tx_digest: str) -> Optional[TxContents]:
        """
        Try get the transaction (non-blocking).

        :param tx_digest: the transaction digest.
        :return: the tx, if found
        """
        try:
            tx = cast(TxContents, self._api.tx.contents(tx_digest))
        except Exception as e:
            logger.debug("Error when attempting getting tx: {}".format(str(e)))
            tx = None
        return tx
