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

"""Fetchai module wrapping the public and private key cryptography and ledger api."""

import logging
from pathlib import Path
from typing import BinaryIO, Optional, cast

from fetchai.ledger.api import LedgerApi as FetchaiLedgerApi
from fetchai.ledger.crypto import Address, Entity, Identity  # type: ignore

from aea.crypto.base import AddressLike, Crypto, LedgerApi

logger = logging.getLogger(__name__)

FETCHAI = "fetchai"
SUCCESSFUL_TERMINAL_STATES = ("Executed", "Submitted")
DEFAULT_FETCHAI_CONFIG = ("alpha.fetch-ai.com", 80)


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
        self._address = str(Address(Identity.from_hex(self.public_key)))

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

    def _generate_private_key(self) -> Entity:
        entity = Entity()
        return entity

    def sign_message(self, message: bytes) -> bytes:
        """
        Sign a message in bytes string form.

        :param message: the message we want to send
        :return: Signed message in bytes
        """
        signature = self.entity.sign(message)
        return signature

    def recover_message(self, message: bytes, signature: bytes) -> bool:
        """
        Recover the address from the hash.

        :param message: the expected message
        :param signature: the transaction signature
        :return: the recovered address
        """
        return self.entity.verify(message=message, signature=signature)

    @classmethod
    def get_address_from_public_key(cls, public_key: str) -> Address:
        """
        Get the address from the public key.

        :param public_key: the public key
        :return: str
        """
        identity = Identity.from_hex(public_key)
        return Address(identity)

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

    def __init__(self, host: str, port: int):
        """
        Initialize the Fetch.AI ledger APIs.

        :param host: URL to the server.
        :param port: the listening port.
        """
        self._api = FetchaiLedgerApi(host, port)

    @property
    def api(self) -> FetchaiLedgerApi:
        """Get the underlying API object."""
        return self._api

    def get_balance(self, address: AddressLike) -> int:
        """Get the balance of a given account."""
        return self._api.tokens.balance(address)

    def send_transaction(
        self,
        crypto: Crypto,
        destination_address: AddressLike,
        amount: int,
        tx_fee: int,
        **kwargs
    ) -> Optional[str]:
        """Submit a transaction to the ledger."""
        tx_digest = self._api.tokens.transfer(
            crypto.entity, destination_address, amount, tx_fee
        )
        self._api.sync(tx_digest)
        return tx_digest

    def is_transaction_settled(self, tx_digest: str) -> bool:
        """Check whether a transaction is settled or not."""
        tx_status = cast(str, self._api.tx.status(tx_digest))
        is_successful = False
        if tx_status in SUCCESSFUL_TERMINAL_STATES:
            # tx_contents = cast(TxContents, api.tx.contents(tx_digest))
            # tx_contents.transfers_to()
            # TODO: check the amount of the transaction is correct
            is_successful = True
        return is_successful
