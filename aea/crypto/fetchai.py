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

import base64
import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Any, BinaryIO, Optional, Tuple, cast

from ecdsa import SECP256k1, VerifyingKey
from ecdsa.util import sigencode_string_canonize

from fetchai.ledger.api import LedgerApi as FetchaiLedgerApi
from fetchai.ledger.api.token import TokenTxFactory
from fetchai.ledger.api.tx import TxContents
from fetchai.ledger.crypto import Address as FetchaiAddress
from fetchai.ledger.crypto import Entity, Identity
from fetchai.ledger.serialisation import sha256_hash, transaction

import requests

from aea.crypto.base import Crypto, FaucetApi, Helper, LedgerApi
from aea.helpers.base import try_decorator
from aea.mail.base import Address

logger = logging.getLogger(__name__)

_FETCHAI = "fetchai"
DEFAULT_NETWORK = "testnet"
SUCCESSFUL_TERMINAL_STATES = ("Executed", "Submitted")
FETCHAI_TESTNET_FAUCET_URL = "https://explore-testnet.fetch.ai/api/v1/send_tokens/"


class FetchAICrypto(Crypto[Entity]):
    """Class wrapping the Entity Generation from Fetch.AI ledger."""

    identifier = _FETCHAI

    def __init__(self, private_key_path: Optional[str] = None):
        """
        Instantiate a fetchai crypto object.

        :param private_key_path: the private key path of the agent
        """
        super().__init__(private_key_path=private_key_path)
        self._address = str(FetchaiAddress(Identity.from_hex(self.public_key)))

    @property
    def private_key(self) -> str:
        """
        Return a private key.

        :return: a private key string
        """
        return self.entity.private_key_hex

    @property
    def public_key(self) -> str:
        """
        Return a public key in hex format.

        :return: a public key string in hex format
        """
        return self.entity.public_key_hex

    @property
    def address(self) -> str:
        """
        Return the address for the key pair.

        :return: a display_address str
        """
        return self._address

    @classmethod
    def load_private_key_from_path(cls, file_name: str) -> Entity:
        """
        Load a private key in hex format from a file.

        :param file_name: the path to the hex file.

        :return: the Entity.
        """
        path = Path(file_name)
        with path.open() as key:
            data = key.read()
            entity = Entity.from_hex(data)
        return entity

    @classmethod
    def generate_private_key(cls) -> Entity:
        """Generate a key pair for fetchai network."""
        entity = Entity()
        return entity

    def sign_message(self, message: bytes, is_deprecated_mode: bool = False) -> str:
        """
        Sign a message in bytes string form.

        :param message: the message we want to send
        :param is_deprecated_mode: if the deprecated signing is used
        :return: signature of the message in string form
        """
        signature_compact = self.entity.signing_key.sign_deterministic(
            message, hashfunc=hashlib.sha256, sigencode=sigencode_string_canonize,
        )
        signature_base64_str = base64.b64encode(signature_compact).decode("utf-8")
        return signature_base64_str

    def sign_transaction(self, transaction: Any) -> Any:
        """
        Sign a transaction in bytes string form.

        :param transaction: the transaction to be signed
        :return: signed transaction
        """
        identity = Identity.from_hex(self.public_key)
        transaction.add_signer(identity)
        transaction.sign(self.entity)
        return transaction

    def dump(self, fp: BinaryIO) -> None:
        """
        Serialize crypto object as binary stream to `fp` (a `.write()`-supporting file-like object).

        :param fp: the output file pointer. Must be set in binary mode (mode='wb')
        :return: None
        """
        fp.write(self.private_key.encode("utf-8"))


class FetchAIHelper(Helper):
    """Helper class usable as Mixin for FetchAIApi or as standalone class."""

    @staticmethod
    def is_transaction_settled(tx_receipt: Any) -> bool:
        """
        Check whether a transaction is settled or not.

        :param tx_digest: the digest associated to the transaction.
        :return: True if the transaction has been settled, False o/w.
        """
        is_successful = False
        if tx_receipt is not None:
            is_successful = tx_receipt.status in SUCCESSFUL_TERMINAL_STATES
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
            seller_address = FetchaiAddress(seller)
            is_valid = (
                str(tx.from_address) == client
                and amount == tx.transfers[seller_address]
                # and self.is_transaction_settled(tx_digest=tx_digest)
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
        aggregate_hash = sha256_hash(
            b"".join([seller.encode(), client.encode(), time_stamp.to_bytes(32, "big")])
        )
        return aggregate_hash.hex()

    @staticmethod
    def get_address_from_public_key(public_key: str) -> Address:
        """
        Get the address from the public key.

        :param public_key: the public key
        :return: str
        """
        identity = Identity.from_hex(public_key)
        address = str(FetchaiAddress(identity))
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
        signature_b64 = base64.b64decode(signature)
        verifying_keys = VerifyingKey.from_public_key_recovery(
            signature_b64, message, SECP256k1, hashfunc=hashlib.sha256,
        )
        public_keys = [
            verifying_key.to_string("compressed").hex()
            for verifying_key in verifying_keys
        ]
        addresses = [
            FetchAIHelper.get_address_from_public_key(public_key)
            for public_key in public_keys
        ]
        return tuple(addresses)


class FetchAIApi(LedgerApi, FetchAIHelper):
    """Class to interact with the Fetch ledger APIs."""

    identifier = _FETCHAI

    def __init__(self, **kwargs):
        """
        Initialize the Fetch.AI ledger APIs.

        :param kwargs: key word arguments (expects either a pair of 'host' and 'port' or a 'network')
        """
        if not ("host" in kwargs and "port" in kwargs):
            network = kwargs.pop("network", DEFAULT_NETWORK)
            kwargs["network"] = network
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

    @try_decorator("Unable to retrieve balance: {}", logger_method="debug")
    def _try_get_balance(self, address: Address) -> Optional[int]:
        """Try get the balance."""
        return self._api.tokens.balance(FetchaiAddress(address))

    def get_transfer_transaction(  # pylint: disable=arguments-differ
        self,
        sender_address: Address,
        destination_address: Address,
        amount: int,
        tx_fee: int,
        tx_nonce: str,
        **kwargs,
    ) -> Optional[Any]:
        """
        Submit a transfer transaction to the ledger.

        :param sender_address: the sender address of the payer.
        :param destination_address: the destination address of the payee.
        :param amount: the amount of wealth to be transferred.
        :param tx_fee: the transaction fee.
        :param tx_nonce: verifies the authenticity of the tx
        :return: the transfer transaction
        """
        tx = TokenTxFactory.transfer(
            FetchaiAddress(sender_address),
            FetchaiAddress(destination_address),
            amount,
            tx_fee,
            [],  # we don't add signer here as we would need the public key for this
        )
        self._api.set_validity_period(tx)
        return tx

    def send_signed_transaction(self, tx_signed: Any) -> Optional[str]:
        """
        Send a signed transaction and wait for confirmation.

        :param tx_signed: the signed transaction
        """
        encoded_tx = transaction.encode_transaction(tx_signed)
        endpoint = "transfer" if tx_signed.transfers is not None else "create"
        return self.api.tokens._post_tx_json(  # pylint: disable=protected-access
            encoded_tx, endpoint
        )

    def get_transaction_receipt(self, tx_digest: str) -> Optional[Any]:
        """
        Get the transaction receipt for a transaction digest (non-blocking).

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
        Get the transaction receipt (non-blocking).

        :param tx_digest: the transaction digest.
        :return: the transaction receipt, if found
        """
        return self._api.tx.status(tx_digest)

    def get_transaction(self, tx_digest: str) -> Optional[Any]:
        """
        Get the transaction for a transaction digest.

        :param tx_digest: the digest associated to the transaction.
        :return: the tx, if present
        """
        tx = self._try_get_transaction(tx_digest)
        return tx

    @try_decorator("Error when attempting getting tx: {}", logger_method="debug")
    def _try_get_transaction(self, tx_digest: str) -> Optional[TxContents]:
        """
        Try get the transaction (non-blocking).

        :param tx_digest: the transaction digest.
        :return: the tx, if found
        """
        return cast(TxContents, self._api.tx.contents(tx_digest))


class FetchAIFaucetApi(FaucetApi):
    """Fetchai testnet faucet API."""

    identifier = _FETCHAI

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
        payload = json.dumps({"address": address})
        response = requests.post(FETCHAI_TESTNET_FAUCET_URL, data=payload)
        if response.status_code // 100 == 5:
            logger.error("Response: {}".format(response.status_code))
        else:
            response_dict = json.loads(response.text)
            if response_dict.get("error_message") is not None:
                logger.warning(
                    "Response: {}\nMessage: {}".format(
                        response.status_code, response_dict.get("error_message")
                    )
                )
            else:
                logger.info(
                    "Response: {}\nMessage: {}\nDigest: {}".format(
                        response.status_code,
                        response_dict.get("message"),
                        response_dict.get("digest"),
                    )
                )  # pragma: no cover
