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

"""Cosmos module wrapping the public and private key cryptography and ledger api."""

import base64
import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Any, BinaryIO, Optional, Tuple

from bech32 import bech32_encode, convertbits

from ecdsa import SECP256k1, SigningKey, VerifyingKey
from ecdsa.util import sigencode_string_canonize

import requests

from aea.crypto.base import Crypto, FaucetApi, Helper, LedgerApi
from aea.helpers.base import try_decorator
from aea.mail.base import Address

logger = logging.getLogger(__name__)

_COSMOS = "cosmos"
COSMOS_TESTNET_FAUCET_URL = "https://faucet-agent-land.prod.fetch-ai.com:443/claim"
DEFAULT_ADDRESS = "https://rest-agent-land.prod.fetch-ai.com:443"
DEFAULT_CURRENCY_DENOM = "atestfet"
DEFAULT_CHAIN_ID = "agent-land"


class CosmosCrypto(Crypto[SigningKey]):
    """Class wrapping the Account Generation from Ethereum ledger."""

    identifier = _COSMOS

    def __init__(self, private_key_path: Optional[str] = None):
        """
        Instantiate an ethereum crypto object.

        :param private_key_path: the private key path of the agent
        """
        super().__init__(private_key_path=private_key_path)
        self._public_key = self.entity.get_verifying_key().to_string("compressed").hex()
        self._address = CosmosHelper.get_address_from_public_key(self.public_key)

    @property
    def private_key(self) -> str:
        """
        Return a private key.

        :return: a private key string
        """
        return self.entity.to_string().hex()

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
    def load_private_key_from_path(cls, file_name) -> SigningKey:
        """
        Load a private key in hex format from a file.

        :param file_name: the path to the hex file.
        :return: the Entity.
        """
        path = Path(file_name)
        with open(path, "r") as key:
            data = key.read()
            signing_key = SigningKey.from_string(bytes.fromhex(data), curve=SECP256k1)
        return signing_key

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
        base64_pbk = base64.b64encode(bytes.fromhex(self.public_key)).decode("utf-8")
        pushable_tx = {
            "tx": {
                "msg": transaction["msgs"],
                "fee": transaction["fee"],
                "memo": transaction["memo"],
                "signatures": [
                    {
                        "signature": signed_transaction,
                        "pub_key": {
                            "type": "tendermint/PubKeySecp256k1",
                            "value": base64_pbk,
                        },
                        "account_number": transaction["account_number"],
                        "sequence": transaction["sequence"],
                    }
                ],
            },
            "mode": "async",
        }
        return pushable_tx

    @classmethod
    def generate_private_key(cls) -> SigningKey:
        """Generate a key pair for cosmos network."""
        signing_key = SigningKey.generate(curve=SECP256k1)
        return signing_key

    def dump(self, fp: BinaryIO) -> None:
        """
        Serialize crypto object as binary stream to `fp` (a `.write()`-supporting file-like object).

        :param fp: the output file pointer. Must be set in binary mode (mode='wb')
        :return: None
        """
        fp.write(self.private_key.encode("utf-8"))


class CosmosHelper(Helper):
    """Helper class usable as Mixin for CosmosApi or as standalone class."""

    @staticmethod
    def is_transaction_settled(tx_receipt: Any) -> bool:
        """
        Check whether a transaction is settled or not.

        :param tx_digest: the digest associated to the transaction.
        :return: True if the transaction has been settled, False o/w.
        """
        is_successful = False
        if tx_receipt is not None:
            # TODO: quick fix only, not sure this is reliable
            is_successful = True
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
        if tx is None:
            return False  # pragma: no cover

        try:
            _tx = tx.get("tx").get("value").get("msg")[0]
            recovered_amount = int(_tx.get("value").get("amount")[0].get("amount"))
            sender = _tx.get("value").get("from_address")
            recipient = _tx.get("value").get("to_address")
            is_valid = (
                recovered_amount == amount and sender == client and recipient == seller
            )
        except (KeyError, IndexError):  # pragma: no cover
            is_valid = False
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
        aggregate_hash = hashlib.sha256(
            b"".join([seller.encode(), client.encode(), time_stamp.to_bytes(32, "big")])
        )
        return aggregate_hash.hexdigest()

    @staticmethod
    def get_address_from_public_key(public_key: str) -> str:
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
        address = bech32_encode(_COSMOS, five_bit_r)
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
            CosmosHelper.get_address_from_public_key(public_key)
            for public_key in public_keys
        ]
        return tuple(addresses)


class CosmosApi(LedgerApi, CosmosHelper):
    """Class to interact with the Cosmos SDK via a HTTP APIs."""

    identifier = _COSMOS

    def __init__(self, **kwargs):
        """
        Initialize the Ethereum ledger APIs.
        """
        self._api = None
        self.network_address = kwargs.pop("address", DEFAULT_ADDRESS)
        self.denom = kwargs.pop("denom", DEFAULT_CURRENCY_DENOM)
        self.chain_id = kwargs.pop("chain_id", DEFAULT_CHAIN_ID)

    @property
    def api(self) -> None:
        """Get the underlying API object."""
        return self._api

    def get_balance(self, address: Address) -> Optional[int]:
        """Get the balance of a given account."""
        balance = self._try_get_balance(address)
        return balance

    @try_decorator(
        "Encountered exception when trying get balance: {}",
        logger_method=logger.warning,
    )
    def _try_get_balance(self, address: Address) -> Optional[int]:
        """Try get the balance of a given account."""
        balance = None  # type: Optional[int]
        url = self.network_address + f"/bank/balances/{address}"
        response = requests.get(url=url)
        if response.status_code == 200:
            result = response.json()["result"]
            if len(result) == 0:
                balance = 0
            else:
                balance = int(result[0]["amount"])
        return balance

    def get_transfer_transaction(  # pylint: disable=arguments-differ
        self,
        sender_address: Address,
        destination_address: Address,
        amount: int,
        tx_fee: int,
        tx_nonce: str,
        denom: Optional[str] = None,
        account_number: int = 0,
        sequence: int = 0,
        gas: int = 80000,
        memo: str = "",
        chain_id: Optional[str] = None,
        **kwargs,
    ) -> Optional[Any]:
        """
        Submit a transfer transaction to the ledger.

        :param sender_address: the sender address of the payer.
        :param destination_address: the destination address of the payee.
        :param amount: the amount of wealth to be transferred.
        :param tx_fee: the transaction fee.
        :param tx_nonce: verifies the authenticity of the tx
        :param chain_id: the Chain ID of the Ethereum transaction. Default is 1 (i.e. mainnet).
        :return: the transfer transaction
        """
        denom = denom if denom is not None else self.denom
        chain_id = chain_id if chain_id is not None else self.chain_id
        account_number, sequence = self._try_get_account_number_and_sequence(
            sender_address
        )
        transfer = {
            "type": "cosmos-sdk/MsgSend",
            "value": {
                "from_address": sender_address,
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
        return tx

    @try_decorator(
        "Encountered exception when trying to get account number and sequence: {}",
        logger_method=logger.warning,
    )
    def _try_get_account_number_and_sequence(
        self, address: Address
    ) -> Optional[Tuple[int, int]]:
        """
        Try get account number and sequence for an address.

        :param address: the address
        :return: a tuple of account number and sequence
        """
        result = None  # type: Optional[Tuple[int, int]]
        url = self.network_address + f"/auth/accounts/{address}"
        response = requests.get(url=url)
        if response.status_code == 200:
            result = (
                int(response.json()["result"]["value"]["account_number"]),
                int(response.json()["result"]["value"]["sequence"]),
            )
        return result

    def send_signed_transaction(self, tx_signed: Any) -> Optional[str]:
        """
        Send a signed transaction and wait for confirmation.

        :param tx_signed: the signed transaction
        :return: tx_digest, if present
        """
        tx_digest = self._try_send_signed_transaction(tx_signed)
        return tx_digest

    @try_decorator(
        "Encountered exception when trying to send tx: {}", logger_method=logger.warning
    )
    def _try_send_signed_transaction(self, tx_signed: Any) -> Optional[str]:
        """
        Try send the signed transaction.

        :param tx_signed: the signed transaction
        :return: tx_digest, if present
        """
        tx_digest = None  # type: Optional[str]
        url = self.network_address + "/txs"
        response = requests.post(url=url, json=tx_signed)
        if response.status_code == 200:
            tx_digest = response.json()["txhash"]
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
        "Encountered exception when trying to get transaction receipt: {}",
        logger_method=logger.warning,
    )
    def _try_get_transaction_receipt(self, tx_digest: str) -> Optional[Any]:
        """
        Try get the transaction receipt for a transaction digest.

        :param tx_digest: the digest associated to the transaction.
        :return: the tx receipt, if present
        """
        result = None  # type: Optional[Any]
        url = self.network_address + f"/txs/{tx_digest}"
        response = requests.get(url=url)
        if response.status_code == 200:
            result = response.json()
        return result

    def get_transaction(self, tx_digest: str) -> Optional[Any]:
        """
        Get the transaction for a transaction digest.

        :param tx_digest: the digest associated to the transaction.
        :return: the tx, if present
        """
        # Cosmos does not distinguis between transaction receipt and transaction
        tx_receipt = self._try_get_transaction_receipt(tx_digest)
        return tx_receipt


class CosmosFaucetApi(FaucetApi):
    """Cosmos testnet faucet API."""

    identifier = _COSMOS

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
        logger_method=logger.error,
    )
    def _try_get_wealth(address: Address) -> None:
        """
        Get wealth from the faucet for the provided address.

        :param address: the address.
        :return: None
        """
        response = requests.post(
            url=COSMOS_TESTNET_FAUCET_URL, data={"Address": address}
        )
        if response.status_code == 200:
            tx_hash = response.text
            logger.info("Wealth generated, tx_hash: {}".format(tx_hash))
        else:  # pragma: no cover
            logger.warning(
                "Response: {}, Text: {}".format(response.status_code, response.text)
            )
