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

import base64
import hashlib
import json
import logging
from pathlib import Path
from typing import Any, BinaryIO, Optional, Tuple

from bech32 import bech32_encode, convertbits

from ecdsa import SECP256k1, SigningKey, VerifyingKey
from ecdsa.util import sigencode_string_canonize

import requests

from aea.crypto.base import Crypto, LedgerApi
from aea.mail.base import Address

logger = logging.getLogger(__name__)

COSMOS = "cosmos"
COSMOS_CURRENCY = "ATOM"


class CosmosCrypto(Crypto):
    """Class wrapping the Account Generation from Ethereum ledger."""

    identifier = COSMOS

    def __init__(self, private_key_path: Optional[str] = None):
        """
        Instantiate an ethereum crypto object.

        :param private_key_path: the private key path of the agent
        """
        self._signing_key = (
            self._generate_private_key()
            if private_key_path is None
            else self._load_private_key_from_path(private_key_path)
        )
        self._public_key = (
            self._signing_key.get_verifying_key().to_string("compressed").hex()
        )
        self._address = self.get_address_from_public_key(self.public_key)

    @property
    def entity(self) -> SigningKey:
        """Get the entity."""
        return self._signing_key

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

    def _load_private_key_from_path(self, file_name) -> SigningKey:
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
                    signing_key = SigningKey.from_string(
                        bytes.fromhex(data), curve=SECP256k1
                    )
            else:
                signing_key = self._generate_private_key()
            return signing_key
        except IOError as e:  # pragma: no cover
            logger.exception(str(e))

    def sign_message(self, message: bytes, is_deprecated_mode: bool = False) -> str:
        """
        Sign a message in bytes string form.

        :param message: the message to be signed
        :param is_deprecated_mode: if the deprecated signing is used
        :return: signature of the message in string form
        """
        signature_compact = self.entity.sign_deterministic(
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
        transaction_str = json.dumps(transaction, separators=(",", ":"), sort_keys=True)
        transaction_bytes = transaction_str.encode("utf-8")
        signed_transaction = self.sign_message(transaction_bytes)
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
        signature_b64 = base64.b64decode(signature)
        verifying_keys = VerifyingKey.from_public_key_recovery(
            signature_b64, message, SECP256k1, hashfunc=hashlib.sha256,
        )
        public_keys = [
            verifying_key.to_string("compressed").hex()
            for verifying_key in verifying_keys
        ]
        addresses = [
            self.get_address_from_public_key(public_key) for public_key in public_keys
        ]
        return tuple(addresses)

    @classmethod
    def _generate_private_key(cls) -> SigningKey:
        """Generate a key pair for cosmos network."""
        signing_key = SigningKey.generate(curve=SECP256k1)
        return signing_key

    @classmethod
    def get_address_from_public_key(cls, public_key: str) -> str:
        """
        Get the address from the public key.

        :param public_key: the public key
        :return: str
        """
        public_key_bytes = bytes.fromhex(public_key)
        s = hashlib.new("sha256", public_key_bytes).digest()
        r = hashlib.new("ripemd160", s).digest()
        five_bit_r = convertbits(r, 8, 5)
        assert five_bit_r is not None, "Unsuccessful bech32.convertbits call"
        address = bech32_encode("cosmos", five_bit_r)
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
        fp.write(self._signing_key.to_string().hex().encode("utf-8"))


class CosmosApi(LedgerApi):
    """Class to interact with the Cosmos SDK via a HTTP APIs."""

    identifier = COSMOS

    def __init__(self, **kwargs):
        """
        Initialize the Ethereum ledger APIs.

        :param address: the endpoint for Web3 APIs.
        """
        self._api = None
        assert "address" in kwargs, "Address kwarg missing!"
        self.network_address = kwargs.pop("address")

    @property
    def api(self) -> None:
        """Get the underlying API object."""
        return self._api

    def get_balance(self, address: Address) -> Optional[int]:
        """Get the balance of a given account."""
        balance = self._try_get_balance(address)
        return balance

    def _try_get_balance(self, address: Address) -> Optional[int]:
        """Try get the balance of a given account."""
        balance = None  # type: Optional[int]
        try:
            url = self.network_address + f"/bank/balances/{address}"
            response = requests.get(url=url)
            if response.status_code == 200:
                logger.debug("Response: {}".format(response.json()))
                balance = int(response.json()["result"][0]["amount"])
            else:
                raise
        except Exception as e:
            logger.warning(
                "Encountered exception when trying get balance: {}".format(e)
            )
        return balance

    def transfer(
        self,
        crypto: Crypto,
        destination_address: Address,
        amount: int,
        tx_fee: int,
        tx_nonce: str = "",
        denom: str = "testfet",
        account_number: int = 0,
        sequence: int = 0,
        gas: int = 80000,
        memo: str = "",
        sync_mode: str = "sync",
        chain_id: str = "aea-testnet",
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
        result = self._try_get_account_number_and_sequence(crypto.address)
        if result is not None:
            account_number, sequence = result
        transfer = {
            "type": "cosmos-sdk/MsgSend",
            "value": {
                "from_address": crypto.address,
                "to_address": destination_address,
                "amount": [{"denom": denom, "amount": str(amount)}],
            },
        }
        tx = {
            "account_number": str(account_number),
            "sequence": str(sequence),
            "chain_id": chain_id,
            "fee": {
                "gas": str(gas),
                "amount": [{"denom": denom, "amount": str(tx_fee)}],
            },
            "memo": memo,
            "msgs": [transfer],
        }
        signature = crypto.sign_transaction(tx)
        base64_pbk = base64.b64encode(bytes.fromhex(crypto.public_key)).decode("utf-8")
        pushable_tx = {
            "tx": {
                "msg": [transfer],
                "fee": {
                    "gas": str(gas),
                    "amount": [{"denom": denom, "amount": str(tx_fee)}],
                },
                "memo": memo,
                "signatures": [
                    {
                        "signature": signature,
                        "pub_key": {
                            "type": "tendermint/PubKeySecp256k1",
                            "value": base64_pbk,
                        },
                        "account_number": str(account_number),
                        "sequence": str(sequence),
                    }
                ],
            },
            "mode": sync_mode,
        }
        # TODO retrieve, gas dynamically

        tx_digest = self.send_signed_transaction(tx_signed=pushable_tx)

        return tx_digest

    def send_signed_transaction(self, tx_signed: Any) -> Optional[str]:
        """
        Send a signed transaction and wait for confirmation.

        :param tx_signed: the signed transaction
        :return: tx_digest, if present
        """
        tx_digest = self._try_send_signed_transaction(tx_signed)
        return tx_digest

    def _try_send_signed_transaction(self, tx_signed: Any) -> Optional[str]:
        """Try send the signed transaction."""
        tx_digest = None  # type: Optional[str]
        try:
            url = self.network_address + "/txs"
            response = requests.post(url=url, json=tx_signed)
            if response.status_code == 200:
                tx_digest = response.json()["txhash"]
        except Exception as e:
            logger.warning("Encountered exception when trying to send tx: {}".format(e))
        return tx_digest

    def _try_get_account_number_and_sequence(
        self, address: Address
    ) -> Optional[Tuple[int, int]]:
        """Try send the signed transaction."""
        result = None  # type: Optional[Tuple[int, int]]
        try:
            url = self.network_address + f"/auth/accounts/{address}"
            response = requests.get(url=url)
            if response.status_code == 200:
                result = (
                    int(response.json()["result"]["value"]["account_number"]),
                    int(response.json()["result"]["value"]["sequence"]),
                )
        except Exception as e:
            logger.warning(
                "Encountered exception when trying to get account number and sequence: {}".format(
                    e
                )
            )
        return result

    def is_transaction_settled(self, tx_digest: str) -> bool:
        """
        Check whether a transaction is settled or not.

        :param tx_digest: the digest associated to the transaction.
        :return: True if the transaction has been settled, False o/w.
        """
        is_successful = False
        tx_receipt = self._try_get_transaction_receipt(tx_digest)
        if tx_receipt is not None:
            # TODO: quick fix only, not sure this is reliable
            is_successful = "code" not in tx_receipt
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
        Try get the transaction receipt for a transaction digest (non-blocking).

        :param tx_digest: the digest associated to the transaction.
        :return: the tx receipt, if present
        """
        result = None  # type: Optional[Any]
        try:
            url = self.network_address + f"/txs/{tx_digest}"
            response = requests.get(url=url)
            if response.status_code == 200:
                result = response.json()
        except Exception as e:
            logger.warning(
                "Encountered exception when trying to get transaction receipt: {}".format(
                    e
                )
            )
        return result

    def generate_tx_nonce(self, seller: Address, client: Address) -> str:
        """
        Generate a unique hash to distinguish txs with the same terms.

        :param seller: the address of the seller.
        :param client: the address of the client.
        :return: return the hash in hex.
        """
        raise NotImplementedError

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
        tx_receipt = self._try_get_transaction_receipt(tx_digest)
        try:
            assert tx_receipt is not None
            tx = tx_receipt.get("tx").get("value").get("msg")[0]
            recovered_amount = int(tx.get("value").get("amount")[0].get("amount"))
            sender = tx.get("value").get("from_address")
            recipient = tx.get("value").get("to_address")
            is_valid = (
                recovered_amount == amount and sender == client and recipient == seller
            )
        except Exception:
            is_valid = False
        return is_valid
