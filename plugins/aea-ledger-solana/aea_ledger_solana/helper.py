# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 Valory AG
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
"""This module contains the helpers for the solana ledger."""
import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, cast

from aea_ledger_solana.transaction import SolanaTransaction
from aea_ledger_solana.utils import pako_inflate
from anchorpy.coder.accounts import ACCOUNT_DISCRIMINATOR_SIZE
from anchorpy.idl import _decode_idl_account
from solana.blockhash import BlockhashCache  # type: ignore
from solana.rpc.api import Client  # type: ignore
from solders.pubkey import Pubkey as PublicKey

from aea.common import Address, JSONLike
from aea.crypto.base import Crypto, Helper
from aea.helpers.base import try_decorator


class SolanaHelper(Helper):
    """Helper class usable as Mixin for SolanaApi or as standalone class."""

    BlockhashCache: BlockhashCache  # defined in SolanaAPi.__init__
    _api: Client  # defined in SolanaAPi.__init__

    @classmethod
    def load_contract_interface(
        cls,
        idl_file_path: Optional[Path] = None,
        program_keypair: Optional[Crypto] = None,
        program_address: Optional[str] = None,
        rpc_api: Optional[str] = None,
        bytecode_path: Optional[Path] = None,
    ) -> Dict[str, Any]:  # type: ignore
        """
        Load contract interface.

        :param idl_file_path: the file path to the IDL
        :param program_keypair: the program keypair
        :param program_address: the program address
        :param rpc_api: the rpc api
        :param bytecode_path: the file path to the bytecode

        :return: the interface
        """
        if bytecode_path is not None:
            in_file = open(bytecode_path, "rb")
            bytecode = in_file.read()
        else:
            bytecode = None

        if (
            program_keypair is not None or program_address is not None
        ) and rpc_api is not None:
            try:
                pid = program_address or program_keypair.address  # type: ignore # mypy doesnt recognize `if` condition above

                base = PublicKey.find_program_address([], PublicKey(pid))[0]
                idl_address = PublicKey.create_with_seed(
                    base, "anchor:idl", PublicKey(pid)
                )
                client = Client(endpoint=rpc_api)
                account_info = client.get_account_info(idl_address)

                account_info_val = account_info.value
                idl_account = _decode_idl_account(
                    bytes(account_info_val.data)[ACCOUNT_DISCRIMINATOR_SIZE:]
                )
                inflated_idl = pako_inflate(bytes(idl_account["data"])).decode()
                json_idl = json.loads(inflated_idl)
                return {
                    "idl": json_idl,
                    "bytecode": bytecode,
                    "program_address": program_address,
                    "program_keypair": program_keypair,
                }
            except Exception as e:
                raise Exception("Could not locate IDL") from e

        elif idl_file_path is not None:
            with open(idl_file_path, "r") as interface_file_solana:
                json_idl = json.load(interface_file_solana)

            return {
                "idl": json_idl,
                "bytecode": bytecode,
                "program_address": program_address,
                "program_keypair": program_keypair,
            }
        else:
            raise Exception("Could not locate IDL")

    @staticmethod
    def is_transaction_valid(
        tx: JSONLike,
        seller: Address,
        client: Address,
        tx_nonce: str,
        amount: int,
    ) -> bool:
        """
        Check whether a transaction is valid or not.

        :param tx: the transaction.
        :param seller: the address of the seller.
        :param client: the address of the client.
        :param tx_nonce: the transaction nonce.
        :param amount: the amount we expect to get from the transaction.

        # noqa: DAR202

        :return: True if the random_message is equals to tx['input']
        """
        raise NotImplementedError

    @staticmethod
    def is_transaction_settled(tx_receipt: JSONLike) -> bool:
        """
        Check whether a transaction is settled or not.

        :param tx_receipt: the receipt associated to the transaction.
        :return: True if the transaction has been settled, False o/w.
        """
        is_successful = False
        if tx_receipt is not None:
            is_successful = tx_receipt["meta"]["status"] == {"Ok": None}  # type: ignore
        return is_successful

    @staticmethod
    def get_hash(message: bytes) -> str:
        """
        Get the hash of a message.

        :param message: the message to be hashed.
        :return: the hash of the message as a hex string.
        """
        sha = hashlib.sha256()
        sha.update(message)
        return sha.hexdigest()

    @classmethod
    def recover_message(
        cls, message: bytes, signature: str, is_deprecated_mode: bool = False
    ) -> Tuple[Address, ...]:
        """
        Recover the addresses from the hash.

        **TOBEIMPLEMENTED**

        :param message: the message we expect
        :param signature: the transaction signature
        :param is_deprecated_mode: if the deprecated signing was used

        # noqa: DAR202

        :return: the recovered addresses
        """
        raise NotImplementedError

    @classmethod
    def recover_public_keys_from_message(
        cls, message: bytes, signature: str, is_deprecated_mode: bool = False
    ) -> Tuple[str, ...]:
        """
        Get the public key used to produce the `signature` of the `message`

        **TOBEIMPLEMENTED**

        :param message: raw bytes used to produce signature
        :param signature: signature of the message
        :param is_deprecated_mode: if the deprecated signing was used

        # noqa: DAR202

        :return: the recovered public keys
        """

        raise NotImplementedError

    @try_decorator("Unable to get nonce: {}", logger_method="warning")
    def _generate_tx_nonce(self) -> str:
        """
        Fetch a latest blockhash to distinguish transactions with the same terms.

        :return: return the blockhash as a nonce.
        """

        try:
            blockhash = self._api.BlockhashCache.get()
            return blockhash
        except Exception:  # pylint: disable=broad-except
            result = self._api.get_latest_blockhash()
            blockhash_json = result.value.to_json()
            blockhash = json.loads(blockhash_json)
            self.BlockhashCache.set(
                blockhash=blockhash["blockhash"], slot=result.context.slot
            )
            return blockhash["blockhash"]

    @staticmethod
    def generate_tx_nonce(seller: Address, client: Address) -> str:
        """
        Generate a unique hash to distinguish transactions with the same terms.

        :param seller: the address of the seller.
        :param client: the address of the client.
        :return: return the hash in hex.
        """
        time_stamp = int(time.time())
        aggregate_hash = hashlib.sha256(
            b"".join([seller.encode(), client.encode(), time_stamp.to_bytes(32, "big")])
        )
        return aggregate_hash.hexdigest()

    def add_nonce(self, tx: dict) -> JSONLike:
        """
        Check whether a transaction is valid or not.

        :param tx: the transaction.
        :return: True if the random_message is equals to tx['input']
        """
        stxn = SolanaTransaction.from_json(tx)
        nonce = self._generate_tx_nonce()
        txn = stxn.to_json()
        txn["recentBlockhash"] = nonce
        return txn

    @staticmethod
    def to_transaction_format(tx: dict) -> Any:
        """Check whether a transaction is valid or not."""
        jsonTx = json.dumps(tx)
        stxn = SolanaTransaction.from_json(jsonTx)  # mypy: ignore
        return SolanaTransaction.from_solders(stxn)

    @staticmethod
    def to_dict_format(tx) -> JSONLike:
        """
        Check whether a transaction is valid or not.

        :param tx: the transaction.
        :return: True if the random_message is equals to tx['input']
        """

        return json.loads(tx._solders.to_json())  # pylint: disable=protected-access

    @staticmethod
    def get_contract_address(tx_receipt: JSONLike) -> Optional[str]:
        """
        Retrieve the `contract_addresses` from a transaction receipt.

        **Solana can have many contract addresses in one tx**

        :param tx_receipt: the receipt of the transaction.
        :return: the contract address, if present
        """
        contract_addresses = []
        keys = tx_receipt["transaction"]["message"]["accountKeys"]  # type: ignore
        for ix in tx_receipt["transaction"]["message"]["instructions"]:  # type: ignore
            program_index = ix["programIdIndex"]  # type: ignore
            contract_addresses.append(cast(str, keys[program_index]))  # type: ignore
        return contract_addresses[0] if contract_addresses else None

    @classmethod
    def get_address_from_public_key(cls, public_key: str) -> str:
        """
        Get the address from the public key.

        :param public_key: the public key
        :return: str
        """
        return str(PublicKey(bytes.fromhex(public_key)))

    @classmethod
    def is_valid_address(cls, address: str) -> bool:
        """
        Check if the address is valid.

        :param address: the address to validate
        :return: whether the address is valid
        """
        try:
            PublicKey.from_string(address)
            return True
        except Exception:  # pylint: disable=broad-except
            return False
