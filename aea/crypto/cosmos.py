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
import gzip
import hashlib
import json
import logging
import os
import subprocess  # nosec
import tempfile
import time
from collections import namedtuple
from pathlib import Path
from typing import Any, BinaryIO, Collection, Dict, List, Optional, Tuple, cast

import requests
from bech32 import bech32_decode, bech32_encode, convertbits
from ecdsa import SECP256k1, SigningKey, VerifyingKey
from ecdsa.util import sigencode_string_canonize

from aea.common import Address, JSONLike
from aea.crypto.base import Crypto, FaucetApi, Helper, LedgerApi
from aea.exceptions import AEAEnforceError
from aea.helpers.base import try_decorator


_default_logger = logging.getLogger(__name__)

_COSMOS = "cosmos"
TESTNET_NAME = "testnet"
DEFAULT_FAUCET_URL = "INVALID_URL"
DEFAULT_ADDRESS = "INVALID_URL"
DEFAULT_CURRENCY_DENOM = "INVALID_CURRENCY_DENOM"
DEFAULT_CHAIN_ID = "INVALID_CHAIN_ID"
_BYTECODE = "wasm_byte_code"


class CosmosHelper(Helper):
    """Helper class usable as Mixin for CosmosApi or as standalone class."""

    address_prefix = _COSMOS

    @staticmethod
    def is_transaction_settled(tx_receipt: JSONLike) -> bool:
        """
        Check whether a transaction is settled or not.

        :param tx_digest: the digest associated to the transaction.
        :return: True if the transaction has been settled, False o/w.
        """
        is_successful = False
        if tx_receipt is not None:
            code = tx_receipt.get("code", None)
            is_successful = code is None
            if not is_successful:
                _default_logger.warning(
                    f"Transaction not settled. Raw log: {tx_receipt.get('raw_log')}"
                )
        return is_successful

    @staticmethod
    def is_transaction_valid(
        tx: JSONLike, seller: Address, client: Address, tx_nonce: str, amount: int,
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
            _tx = cast(dict, tx.get("tx", {})).get("value", {}).get("msg", [])[0]
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
        if five_bit_r is None:  # pragma: nocover
            raise AEAEnforceError("Unsuccessful bech32.convertbits call")
        address = bech32_encode(cls.address_prefix, five_bit_r)
        return address

    @classmethod
    def recover_message(
        cls, message: bytes, signature: str, is_deprecated_mode: bool = False
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
            cls.get_address_from_public_key(public_key) for public_key in public_keys
        ]
        return tuple(addresses)

    @staticmethod
    def get_hash(message: bytes) -> str:
        """
        Get the hash of a message.

        :param message: the message to be hashed.
        :return: the hash of the message.
        """
        digest = hashlib.sha256(message).hexdigest()
        return digest

    @classmethod
    def is_valid_address(cls, address: Address) -> bool:
        """
        Check if the address is valid.

        :param address: the address to validate
        """
        result = bech32_decode(address)
        return result != (None, None) and result[0] == cls.address_prefix

    @classmethod
    def load_contract_interface(cls, file_path: Path) -> Dict[str, str]:
        """
        Load contract interface.

        :param file_path: the file path to the interface
        :return: the interface
        """
        with open(file_path, "rb") as interface_file_cosmos:
            contract_interface = {
                _BYTECODE: str(
                    base64.b64encode(
                        gzip.compress(interface_file_cosmos.read(), 6)
                    ).decode()
                )
            }
        return contract_interface


class CosmosCrypto(Crypto[SigningKey]):
    """Class wrapping the Account Generation from Ethereum ledger."""

    identifier = _COSMOS
    helper = CosmosHelper

    def __init__(self, private_key_path: Optional[str] = None):
        """
        Instantiate an ethereum crypto object.

        :param private_key_path: the private key path of the agent
        """
        super().__init__(private_key_path=private_key_path)
        self._public_key = self.entity.get_verifying_key().to_string("compressed").hex()
        self._address = self.helper.get_address_from_public_key(self.public_key)

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

    def sign_message(  # pylint: disable=unused-argument
        self, message: bytes, is_deprecated_mode: bool = False
    ) -> str:
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

    @staticmethod
    def format_default_transaction(
        transaction: JSONLike, signature: str, base64_pbk: str
    ) -> JSONLike:
        """
        Format default CosmosSDK transaction and add signature.

        :param transaction: the transaction to be formatted
        :param signature: the transaction signature
        :param base64_pbk: the base64 formatted public key

        :return: formatted transaction with signature
        """
        pushable_tx: JSONLike = {
            "tx": {
                "msg": transaction["msgs"],
                "fee": transaction["fee"],
                "memo": transaction["memo"],
                "signatures": [
                    {
                        "signature": signature,
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

    @staticmethod
    def format_wasm_transaction(
        transaction: JSONLike, signature: str, base64_pbk: str
    ) -> JSONLike:
        """
        Format CosmWasm transaction and add signature.

        :param transaction: the transaction to be formatted
        :param signature: the transaction signature
        :param base64_pbk: the base64 formatted public key

        :return: formatted transaction with signature
        """
        pushable_tx: JSONLike = {
            "type": "cosmos-sdk/StdTx",
            "value": {
                "msg": transaction["msgs"],
                "fee": transaction["fee"],
                "signatures": [
                    {
                        "pub_key": {
                            "type": "tendermint/PubKeySecp256k1",
                            "value": base64_pbk,
                        },
                        "signature": signature,
                    }
                ],
                "memo": transaction["memo"],
            },
        }
        return pushable_tx

    def sign_transaction(self, transaction: JSONLike) -> JSONLike:
        """
        Sign a transaction in bytes string form.

        :param transaction: the transaction to be signed
        :return: signed transaction
        """
        transaction_str = json.dumps(transaction, separators=(",", ":"), sort_keys=True)
        transaction_bytes = transaction_str.encode("utf-8")
        signed_transaction = self.sign_message(transaction_bytes)
        base64_pbk = base64.b64encode(bytes.fromhex(self.public_key)).decode("utf-8")

        msgs = cast(list, transaction.get("msgs", []))
        if len(msgs) == 1 and "type" in msgs[0] and "wasm" in msgs[0]["type"]:
            return self.format_wasm_transaction(
                transaction, signed_transaction, base64_pbk
            )
        return self.format_default_transaction(
            transaction, signed_transaction, base64_pbk
        )

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


class _CosmosApi(LedgerApi):
    """Class to interact with the Cosmos SDK via a HTTP APIs."""

    identifier = _COSMOS

    def __init__(self, **kwargs):
        """Initialize the Cosmos ledger APIs."""
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
        logger_method=_default_logger.warning,
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

    def get_state(self, callable_name: str, *args, **kwargs) -> Optional[JSONLike]:
        """
        Call a specified function on the ledger API.

        Based on the cosmos REST
        API specification, which takes a path (strings separated by '/'). The
        convention here is to define the root of the path (txs, blocks, etc.)
        as the callable_name and the rest of the path as args.
        """
        response = self._try_get_state(callable_name, *args, **kwargs)
        return response

    @try_decorator(
        "Encountered exception when trying get state: {}",
        logger_method=_default_logger.warning,
    )
    def _try_get_state(  # pylint: disable=unused-argument
        self, callable_name: str, *args, **kwargs
    ) -> Optional[JSONLike]:
        """Try to call a function on the ledger API."""
        result: Optional[JSONLike] = None
        query = "/".join(args)
        url = self.network_address + f"/{callable_name}/{query}"
        response = requests.get(url=url)
        if response.status_code == 200:
            result = response.json()
        return result

    def get_deploy_transaction(  # pylint: disable=arguments-differ
        self,
        contract_interface: Dict[str, str],
        deployer_address: Address,
        tx_fee: int = 0,
        gas: int = 80000,
        denom: Optional[str] = None,
        memo: str = "",
        chain_id: Optional[str] = None,
        **kwargs,
    ) -> Optional[JSONLike]:
        """
        Create a CosmWasm bytecode deployment transaction.

        :param sender_address: the sender address of the message initiator.
        :param filename: the path to wasm bytecode file.
        :param gas: Maximum amount of gas to be used on executing command.
        :param memo: any string comment.
        :param chain_id: the Chain ID of the CosmWasm transaction. Default is 1 (i.e. mainnet).
        :return: the unsigned CosmWasm contract deploy message
        """
        denom = denom if denom is not None else self.denom
        chain_id = chain_id if chain_id is not None else self.chain_id
        account_number, sequence = self._try_get_account_number_and_sequence(
            deployer_address
        )
        if account_number is None or sequence is None:
            return None
        deploy_msg = {
            "type": "wasm/store-code",
            "value": {
                "sender": deployer_address,
                "wasm_byte_code": contract_interface[_BYTECODE],
                "source": "",
                "builder": "",
            },
        }
        tx = self._get_transaction(
            account_number,
            chain_id,
            tx_fee,
            denom,
            gas,
            memo,
            sequence,
            msg=deploy_msg,
        )
        return tx

    def get_init_transaction(
        self,
        deployer_address: Address,
        code_id: int,
        init_msg: Any,
        amount: int,
        tx_fee: int,
        gas: int = 80000,
        denom: Optional[str] = None,
        label: str = "",
        memo: str = "",
        chain_id: Optional[str] = None,
    ) -> Optional[JSONLike]:
        """
        Create a CosmWasm InitMsg transaction.

        :param deployer_address: the deployer address of the message initiator.
        :param amount: Contract's initial funds amount
        :param code_id: the ID of contract bytecode.
        :param init_msg: the InitMsg containing parameters for contract constructor.
        :param gas: Maximum amount of gas to be used on executing command.
        :param denom: the name of the denomination of the contract funds
        :param label: the label name of the contract
        :param memo: any string comment.
        :param chain_id: the Chain ID of the CosmWasm transaction. Default is 1 (i.e. mainnet).
        :return: the unsigned CosmWasm InitMsg
        """
        denom = denom if denom is not None else self.denom
        chain_id = chain_id if chain_id is not None else self.chain_id
        account_number, sequence = self._try_get_account_number_and_sequence(
            deployer_address
        )
        if account_number is None or sequence is None:
            return None
        instantiate_msg = {
            "type": "wasm/instantiate",
            "value": {
                "sender": deployer_address,
                "code_id": str(code_id),
                "label": label,
                "init_msg": init_msg,
                "init_funds": [{"denom": denom, "amount": str(amount)}],
            },
        }
        tx = self._get_transaction(
            account_number,
            chain_id,
            tx_fee,
            denom,
            gas,
            memo,
            sequence,
            msg=instantiate_msg,
        )
        return tx

    def get_handle_transaction(
        self,
        sender_address: Address,
        contract_address: Address,
        handle_msg: Any,
        amount: int,
        tx_fee: int,
        denom: Optional[str] = None,
        gas: int = 80000,
        memo: str = "",
        chain_id: Optional[str] = None,
    ) -> Optional[JSONLike]:
        """
        Create a CosmWasm HandleMsg transaction.

        :param sender_address: the sender address of the message initiator.
        :param contract_address: the address of the smart contract.
        :param handle_msg: HandleMsg in JSON format.
        :param gas: Maximum amount of gas to be used on executing command.
        :param memo: any string comment.
        :param chain_id: the Chain ID of the CosmWasm transaction. Default is 1 (i.e. mainnet).
        :return: the unsigned CosmWasm HandleMsg
        """
        denom = denom if denom is not None else self.denom
        chain_id = chain_id if chain_id is not None else self.chain_id
        account_number, sequence = self._try_get_account_number_and_sequence(
            sender_address
        )
        if account_number is None or sequence is None:
            return None
        execute_msg = {
            "type": "wasm/execute",
            "value": {
                "sender": sender_address,
                "contract": contract_address,
                "msg": handle_msg,
                "sent_funds": [{"amount": str(amount), "denom": denom}],
            },
        }
        tx = self._get_transaction(
            account_number,
            chain_id,
            tx_fee,
            denom,
            gas,
            memo,
            sequence,
            msg=execute_msg,
        )
        return tx

    @staticmethod
    @try_decorator(
        "Encountered exception when trying to execute wasm transaction: {}",
        logger_method=_default_logger.warning,
    )
    def try_execute_wasm_transaction(
        tx_signed: JSONLike, signed_tx_filename: str = "tx.signed"
    ) -> Optional[str]:
        """
        Execute a CosmWasm Transaction. QueryMsg doesn't require signing.

        :param tx_signed: the signed transaction.
        :return: the transaction digest
        """
        with tempfile.TemporaryDirectory() as tmpdirname:
            with open(os.path.join(tmpdirname, signed_tx_filename), "w") as f:
                f.write(json.dumps(tx_signed))

            command = [
                "wasmcli",
                "tx",
                "broadcast",
                os.path.join(tmpdirname, signed_tx_filename),
            ]

            stdout, _ = subprocess.Popen(  # nosec
                command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
            ).communicate()

        return stdout.decode("ascii")

    @staticmethod
    @try_decorator(
        "Encountered exception when trying to execute wasm query: {}",
        logger_method=_default_logger.warning,
    )
    def try_execute_wasm_query(
        contract_address: Address, query_msg: JSONLike
    ) -> Optional[str]:
        """
        Execute a CosmWasm QueryMsg. QueryMsg doesn't require signing.

        :param contract_address: the address of the smart contract.
        :param query_msg: QueryMsg in JSON format.
        :return: the message receipt
        """
        command = [
            "wasmcli",
            "query",
            "wasm",
            "contract-state",
            "smart",
            str(contract_address),
            json.dumps(query_msg),
        ]

        stdout, _ = subprocess.Popen(  # nosec
            command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        ).communicate()

        return stdout.decode("ascii")

    def get_transfer_transaction(  # pylint: disable=arguments-differ
        self,
        sender_address: Address,
        destination_address: Address,
        amount: int,
        tx_fee: int,
        tx_nonce: str,
        denom: Optional[str] = None,
        gas: int = 80000,
        memo: str = "",
        chain_id: Optional[str] = None,
        **kwargs,
    ) -> Optional[JSONLike]:
        """
        Submit a transfer transaction to the ledger.

        :param sender_address: the sender address of the payer.
        :param destination_address: the destination address of the payee.
        :param amount: the amount of wealth to be transferred.
        :param tx_fee: the transaction fee.
        :param tx_nonce: verifies the authenticity of the tx
        :param denom: the denomination of tx fee and amount
        :param gas: the gas used.
        :param memo: memo to include in tx.
        :param chain_id: the chain ID of the transaction.
        :return: the transfer transaction
        """
        denom = denom if denom is not None else self.denom
        chain_id = chain_id if chain_id is not None else self.chain_id
        account_number, sequence = self._try_get_account_number_and_sequence(
            sender_address
        )
        if account_number is None or sequence is None:
            return None
        transfer_msg = {
            "type": "cosmos-sdk/MsgSend",
            "value": {
                "amount": [{"amount": str(amount), "denom": denom}],
                "from_address": sender_address,
                "to_address": destination_address,
            },
        }
        tx = self._get_transaction(
            account_number,
            chain_id,
            tx_fee,
            denom,
            gas,
            memo,
            sequence,
            msg=transfer_msg,
        )
        return tx

    @staticmethod
    def _get_transaction(
        account_number: int,
        chain_id: str,
        tx_fee: int,
        denom: str,
        gas: int,
        memo: str,
        sequence: int,
        msg: Dict[str, Collection[str]],
    ) -> JSONLike:
        """
        Get a transaction.

        :param account_number: the account number.
        :param chain_id: the chain ID of the transaction.
        :param tx_fee: the transaction fee.
        :param denom: the denomination of tx fee and amount
        :param gas: the gas used.
        :param memo: memo to include in tx.
        :param msg: the transaction msg.
        :param sequence: the sequence.
        :return: the transaction
        """
        tx: JSONLike = {
            "account_number": str(account_number),
            "chain_id": chain_id,
            "fee": {
                "amount": [{"amount": str(tx_fee), "denom": denom}],
                "gas": str(gas),
            },
            "memo": memo,
            "msgs": [msg],
            "sequence": str(sequence),
        }
        return tx

    @try_decorator(
        "Encountered exception when trying to get account number and sequence: {}",
        logger_method=_default_logger.warning,
    )
    def _try_get_account_number_and_sequence(
        self, address: Address
    ) -> Tuple[Optional[int], Optional[int]]:
        """
        Try get account number and sequence for an address.

        :param address: the address
        :return: a tuple of account number and sequence
        """
        result: Tuple[Optional[int], Optional[int]] = (None, None)
        url = self.network_address + f"/auth/accounts/{address}"
        response = requests.get(url=url)
        if response.status_code == 200:
            result = (
                int(response.json()["result"]["value"]["account_number"]),
                int(response.json()["result"]["value"]["sequence"]),
            )
        return result

    def send_signed_transaction(self, tx_signed: JSONLike) -> Optional[str]:
        """
        Send a signed transaction and wait for confirmation.

        :param tx_signed: the signed transaction
        :return: tx_digest, if present
        """
        if self.is_cosmwasm_transaction(tx_signed):
            tx_digest = self.try_execute_wasm_transaction(tx_signed)
        elif self.is_transfer_transaction(tx_signed):
            tx_digest = self._try_send_signed_transaction(tx_signed)
        else:  # pragma: nocover
            _default_logger.warning(
                "Cannot send transaction. Unknown transaction type: {}".format(
                    tx_signed
                )
            )
            tx_digest = None
        return tx_digest

    @staticmethod
    def is_cosmwasm_transaction(tx_signed: JSONLike) -> bool:
        """Check whether it is a cosmwasm tx."""
        try:
            _type = cast(dict, tx_signed.get("value", {})).get("msg", [])[0]["type"]
            result = _type in ["wasm/store-code", "wasm/instantiate", "wasm/execute"]
        except (KeyError, IndexError):  # pragma: nocover
            result = False
        return result

    @staticmethod
    def is_transfer_transaction(tx_signed: JSONLike) -> bool:
        """Check whether it is a transfer tx."""
        try:
            _type = cast(dict, tx_signed.get("tx", {})).get("msg", [])[0]["type"]
            result = _type in ["cosmos-sdk/MsgSend"]
        except (KeyError, IndexError):  # pragma: nocover
            result = False
        return result

    @try_decorator(
        "Encountered exception when trying to send tx: {}",
        logger_method=_default_logger.warning,
    )
    def _try_send_signed_transaction(self, tx_signed: JSONLike) -> Optional[str]:
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
        else:  # pragma: nocover
            _default_logger.error("Cannot send transaction: {}".format(response.json()))
        return tx_digest

    def get_transaction_receipt(self, tx_digest: str) -> Optional[JSONLike]:
        """
        Get the transaction receipt for a transaction digest.

        :param tx_digest: the digest associated to the transaction.
        :return: the tx receipt, if present
        """
        tx_receipt = self._try_get_transaction_receipt(tx_digest)
        return tx_receipt

    @try_decorator(
        "Encountered exception when trying to get transaction receipt: {}",
        logger_method=_default_logger.warning,
    )
    def _try_get_transaction_receipt(self, tx_digest: str) -> Optional[JSONLike]:
        """
        Try get the transaction receipt for a transaction digest.

        :param tx_digest: the digest associated to the transaction.
        :return: the tx receipt, if present
        """
        result: Optional[JSONLike] = None
        url = self.network_address + f"/txs/{tx_digest}"
        response = requests.get(url=url)
        if response.status_code == 200:
            result = response.json()
        return result

    def get_transaction(self, tx_digest: str) -> Optional[JSONLike]:
        """
        Get the transaction for a transaction digest.

        :param tx_digest: the digest associated to the transaction.
        :return: the tx, if present
        """
        # Cosmos does not distinguis between transaction receipt and transaction
        tx_receipt = self._try_get_transaction_receipt(tx_digest)
        return tx_receipt

    def get_contract_instance(
        self, contract_interface: Dict[str, str], contract_address: Optional[str] = None
    ) -> Any:
        """
        Get the instance of a contract.

        :param contract_interface: the contract interface.
        :param contract_address: the contract address.
        :return: the contract instance
        """
        # Instance object not available for cosmwasm
        return None

    @staticmethod
    def _execute_shell_command(command: List[str]) -> List[Dict[str, str]]:
        """
        Execute command using subprocess and get result as JSON dict.

        :param command: the shell command to be executed
        :return: the stdout result converted to JSON dict
        """
        stdout, _ = subprocess.Popen(  # nosec
            command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT
        ).communicate()

        return json.loads(stdout.decode("ascii"))

    def get_last_code_id(self) -> int:
        """
        Get ID of latest deployed .wasm bytecode.

        :return: code id of last deployed .wasm bytecode
        """

        command = ["wasmcli", "query", "wasm", "list-code"]
        res = self._execute_shell_command(command)

        return int(res[-1]["id"])

    def get_contract_address(self, code_id: int) -> str:
        """
        Get contract address of latest initialised contract by its ID.

        :param code_id: id of deployed CosmWasm bytecode
        :return: contract address of last initialised contract
        """

        command = ["wasmcli", "query", "wasm", "list-contract-by-code", str(code_id)]
        res = self._execute_shell_command(command)

        return res[-1]["address"]

    def update_with_gas_estimate(self, transaction: JSONLike) -> JSONLike:
        """
        Attempts to update the transaction with a gas estimate

        :param transaction: the transaction
        :return: the updated transaction
        """
        raise NotImplementedError(  # pragma: nocover
            "No gas estimation has been implemented."
        )


class CosmosApi(_CosmosApi, CosmosHelper):
    """Class to interact with the Cosmos SDK via a HTTP APIs."""


""" Equivalent to:

@dataclass
class CosmosFaucetStatus:
    tx_digest: Optional[str]
    status: str
    status_code: int
"""
CosmosFaucetStatus = namedtuple(
    "CosmosFaucetStatus", ["tx_digest", "status", "status_code"]
)


class CosmosFaucetApi(FaucetApi):
    """Cosmos testnet faucet API."""

    FAUCET_STATUS_PENDING = 1  # noqa: F841
    FAUCET_STATUS_PROCESSING = 2  # noqa: F841
    FAUCET_STATUS_COMPLETED = 20  # noqa: F841
    FAUCET_STATUS_FAILED = 21  # noqa: F841
    FAUCET_STATUS_TIMED_OUT = 22  # noqa: F841
    FAUCET_STATUS_RATE_LIMITED = 23  # noqa: F841
    FAUCET_STATUS_RATE_UNAVAILABLE = 99  # noqa: F841

    identifier = _COSMOS
    testnet_faucet_url = DEFAULT_FAUCET_URL
    testnet_name = TESTNET_NAME

    def __init__(self, poll_interval=None):
        """Initialize CosmosFaucetApi."""
        self._poll_interval = float(poll_interval or 1)

    def get_wealth(self, address: Address, url: Optional[str] = None) -> None:
        """
        Get wealth from the faucet for the provided address.

        :param address: the address.
        :param url: the url
        :return: None
        :raises: RuntimeError of explicit faucet failures
        """
        uid = self._try_create_faucet_claim(address, url)
        if uid is None:  # pragma: nocover
            raise RuntimeError("Unable to create faucet claim")

        while True:

            # lookup status form the claim uid
            status = self._try_check_faucet_claim(uid, url)
            if status is None:  # pragma: nocover
                raise RuntimeError("Failed to check faucet claim status")

            # if the status is complete
            if status.status_code == self.FAUCET_STATUS_COMPLETED:
                break

            # if the status is failure
            if status.status_code > self.FAUCET_STATUS_COMPLETED:  # pragma: nocover
                raise RuntimeError(f"Failed to get wealth for {address}")

            # if the status is incomplete
            time.sleep(self._poll_interval)

    @classmethod
    @try_decorator(
        "An error occured while attempting to request a faucet request:\n{}",
        logger_method=_default_logger.error,
    )
    def _try_create_faucet_claim(
        cls, address: Address, url: Optional[str] = None
    ) -> Optional[str]:
        """
        Create a token faucet claim request

        :param address: the address to request funds
        :param url: the url
        :return: None on failure, otherwise the request uid
        """
        uri = cls._faucet_request_uri(url)
        response = requests.post(url=uri, data={"Address": address})

        uid = None
        if response.status_code == 200:
            data = response.json()
            uid = data["uid"]

            _default_logger.info("Wealth claim generated, uid: {}".format(uid))
        else:  # pragma: no cover
            _default_logger.warning(
                "Response: {}, Text: {}".format(response.status_code, response.text)
            )

        return uid

    @classmethod
    @try_decorator(
        "An error occured while attempting to request a faucet request:\n{}",
        logger_method=_default_logger.error,
    )
    def _try_check_faucet_claim(
        cls, uid: str, url: Optional[str] = None
    ) -> Optional[CosmosFaucetStatus]:
        """
        Check the status of a faucet request

        :param uid: The request uid to be checked
        :param url: the url
        :return: None on failure otherwise a CosmosFaucetStatus for the specified uid
        """
        response = requests.get(cls._faucet_status_uri(uid, url))
        if response.status_code != 200:  # pragma: nocover
            _default_logger.warning(
                "Response: {}, Text: {}".format(response.status_code, response.text)
            )
            return None

        # parse the response
        data = response.json()
        return CosmosFaucetStatus(
            tx_digest=data.get("txDigest"),
            status=data["status"],
            status_code=data["statusCode"],
        )

    @classmethod
    def _faucet_request_uri(cls, url: Optional[str] = None) -> str:
        """
        Generates the request URI derived from `cls.faucet_base_url` or provided url.

        :param url: the url
        """
        if cls.testnet_faucet_url is None:  # pragma: nocover
            raise ValueError("Testnet faucet url not set.")
        url = cls.testnet_faucet_url if url is None else url
        return f"{url}/claim/requests"

    @classmethod
    def _faucet_status_uri(cls, uid: str, url: Optional[str] = None) -> str:
        """Generates the status URI derived from `cls.faucet_base_url`."""
        return f"{cls._faucet_request_uri(url)}/{uid}"
