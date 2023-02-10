# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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
"""Solana module wrapping the public and private key cryptography and ledger api."""
import json
import logging
import hashlib
import base64
import base58
import struct
from struct import pack_into
import array
import subprocess
import tempfile
from typing import NewType
import os

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union, cast
import zlib
from ast import literal_eval
from aea.common import Address, JSONLike
from aea.crypto.base import Crypto, FaucetApi, Helper, LedgerApi
from aea.crypto.helpers import DecryptError, KeyIsIncorrect, hex_to_bytes_for_key
from aea.exceptions import enforce
from aea.helpers import http_requests as requests
from aea.helpers.base import try_decorator
from aea.helpers.io import open_file

from solana.publickey import PublicKey
from solana.rpc.api import Client
from solana.blockhash import Blockhash, BlockhashCache
from solana.keypair import Keypair
from solders.signature import Signature
from solders.transaction import Transaction as sTransaction
from solders.hash import Hash
from solders import system_program as ssp
from pythclient.pythaccounts import PythPriceInfo


from anchorpy import Idl
from cryptography.fernet import Fernet


from pathlib import Path
import json
from solana.transaction import Transaction
from anchorpy import Program, Context
from anchorpy.idl import _decode_idl_account, _idl_address
from anchorpy.coder.accounts import ACCOUNT_DISCRIMINATOR_SIZE
from solana.system_program import TransferParams, transfer
from solana.transaction import Transaction, TransactionInstruction, AccountMeta
from solana.system_program import create_account, SYS_PROGRAM_ID
from solana.system_program import CreateAccountParams, CreateAccountWithSeedParams
from spl.token.core import _TokenCore as TokenCore

_default_logger = logging.getLogger(__name__)

_VERSION = "1.24.17"
_SOLANA = "solana"
TESTNET_NAME = "n/a"
DEFAULT_ADDRESS = "https://api.devnet.solana.com"
DEFAULT_CHAIN_ID = 101
DEFAULT_CURRENCY_DENOM = "lamports"
RENT_EXEMPT_AMOUNT = 1000000

LAMPORTS_PER_SOL = 1000000000
_IDL = "idl"
_BYTECODE = "bytecode"


def _pako_inflate(data):
    # https://stackoverflow.com/questions/46351275/using-pako-deflate-with-python
    decompress = zlib.decompressobj(15)
    decompressed_data = decompress.decompress(data)
    decompressed_data += decompress.flush()
    return decompressed_data


class SolanaCrypto(Crypto[Keypair]):
    """Class wrapping the Account Generation from Solana ledger."""

    identifier = _SOLANA

    def __init__(
        self,
        private_key_path: Optional[str] = None,
        password: Optional[str] = None,
        extra_entropy: Union[str, bytes, int] = "",
    ) -> None:
        """
        Instantiate an solana crypto object.

        :param private_key_path: the private key path of the agent
        :param password: the password to encrypt/decrypt the private key.
        :param extra_entropy: add extra randomness to whatever randomness your OS can provide
        """
        super().__init__(
            private_key_path=private_key_path,
            password=password,
            extra_entropy=extra_entropy,
        )
        bytes_representation = self.entity.secret_key
        self._public_key = self.entity.public_key
        self._address = self.entity.public_key

    @property
    def private_key(self) -> str:
        """
        Return a private key.

        64 random hex characters (i.e. 32 bytes) prefix.

        :return: a private key string in hex format
        """

        return base58.b58encode(self.entity.secret_key).decode()

    @ property
    def public_key(self) -> str:
        """
        Return a public key in hex format.


        :return: a public key string in hex format
        """
        return self._public_key

    @ property
    def address(self) -> str:
        """
        Return the address for the key pair.

        :return: an address string in hex format
        """
        return self._address.to_base58().decode()

    @ classmethod
    def load_private_key_from_path(
        cls, file_name: Path, password: Optional[str] = None
    ) -> Keypair:
        """
        Load a private key in base58 or bytes format from a file.

        :param file_name: the path to the hex file.
        :param password: the password to encrypt/decrypt the private key.
        :return: the Entity.
        """
        key_path = Path(file_name)
        if key_path.name.endswith(".json"):
            private_key = open(key_path, "r").read()
            try:
                # t = bytes(literal_eval(private_key))
                key = Keypair.from_secret_key(bytes(literal_eval(private_key)))
            except Exception as e:

                raise KeyIsIncorrect(
                    f"Error on key `{key_path}` load! : Error: {repr(e)} "
                ) from e
        else:
            private_key = open(key_path, "r").read()
            try:
                key = Keypair.from_secret_key(base58.b58decode(private_key))
            except Exception as e:

                raise KeyIsIncorrect(
                    f"Error on key `{key_path}` load! : Error: {repr(e)} "
                ) from e

        return key

    def sign_message(self, message: bytes, is_deprecated_mode: bool = False) -> str:
        """
        Sign a message in bytes string form.

        :param message: the message to be signed
        :param is_deprecated_mode: if the deprecated signing is used
        :return: signature of the message in string form
        """

        keypair = Keypair.from_secret_key(base58.b58decode(self.private_key))
        signed_msg = keypair.sign(message)

        return signed_msg

    def sign_transaction(self, transaction: JSONLike, signers: Optional[list] = []) -> JSONLike:
        """
        Sign a transaction in bytes string form.

        :param transaction: the transaction to be signed
        :param recent_blockhash: a recent blockhash
        :return: signed transaction
        """

        jsonTx = json.dumps(transaction)
        stxn = sTransaction.from_json(jsonTx)
        txn = Transaction.from_solders(stxn)

        # txn = transaction

        keypair = Keypair.from_secret_key(base58.b58decode(self.private_key))
        signers = [Keypair.from_secret_key(base58.b58decode(
            signer.private_key)) for signer in signers]
        signers.append(keypair)

        try:
            txn.sign(*signers)
        except Exception as e:
            raise Exception(e)

        tx = txn._solders.to_json()
        return json.loads(tx)
        # return txn

    @ classmethod
    def generate_private_key(
        cls, extra_entropy: Union[str, bytes, int] = ""
    ) -> Keypair:
        """
        Generate a key pair for Solana network.

        :param extra_entropy: add extra randomness to whatever randomness your OS can provide
        :return: keypair object
        """
        account = Keypair.generate()  # pylint: disable=no-value-for-parameter
        return account

    def encrypt(self, password: str) -> str:
        """
        Encrypt the private key and return in json.

        :param password: the password to decrypt.
        :return: json string containing encrypted private key.
        """
        try:
            pw = str.encode(password)
            hash_object = hashlib.sha256(pw)
            hex_dig = hash_object.digest()
            base64_bytes = base64.b64encode(hex_dig)
            fernet = Fernet(base64_bytes)
            enc_mac = fernet.encrypt(self.private_key.encode())
        except Exception as e:
            raise Exception("Encryption failed")

        return json.dumps(enc_mac.decode())

    @ classmethod
    def decrypt(cls, keyfile_json: str, password: str) -> str:
        """
        Decrypt the private key and return in raw form.

        :param keyfile_json: json str containing encrypted private key.
        :param password: the password to decrypt.
        :return: the raw private key.
        """
        try:
            keyfile = json.loads(keyfile_json)
            keyfile_bytes = keyfile.encode()
            pw = str.encode(password)
            hash_object = hashlib.sha256(pw)
            hex_dig = hash_object.digest()
            base64_bytes = base64.b64encode(hex_dig)
            fernet = Fernet(base64_bytes)

            dec_mac = fernet.decrypt(keyfile_bytes).decode()
        except ValueError as e:
            raise DecryptError() from e
        return dec_mac


class SolanaHelper(Helper):
    """Helper class usable as Mixin for SolanaApi or as standalone class."""

    @ classmethod
    def load_contract_interface(cls,
                                idl_file_path: Optional[Path] = None,
                                program_keypair: Optional[Crypto] = None,
                                program_address: Optional[str] = None,
                                rpc_api: Optional[str] = None,
                                bytecode_path: Optional[Path] = None,
                                ) -> Dict[str, str]:
        """
        Load contract interface.

        :param idl_file_path: the file path to the IDL
        :param program_keypair: the program keypair
        :param rpc_api: the rpc api
        :param bytecode_path: the file path to the bytecode

        :return: the interface
        """
        if bytecode_path is not None:
            in_file = open(bytecode_path, "rb")
            bytecode = in_file.read()
        else:
            bytecode = None

        if (program_keypair is not None or program_address is not None) and rpc_api is not None:
            try:
                pid = program_address if program_address is not None else program_keypair.address
                base = PublicKey.find_program_address(
                    [], PublicKey(pid))[0]
                idl_address = PublicKey.create_with_seed(
                    base, "anchor:idl", PublicKey(pid))
                client = Client(endpoint=rpc_api)
                account_info = client.get_account_info(idl_address)

                account_info_val = account_info.value
                idl_account = _decode_idl_account(
                    bytes(account_info_val.data)[
                        ACCOUNT_DISCRIMINATOR_SIZE:]
                )
                inflated_idl = _pako_inflate(
                    bytes(idl_account["data"])).decode()
                json_idl = json.loads(inflated_idl)
                return {"idl": json_idl, "bytecode": bytecode, "program_address": program_address, "program_keypair": program_keypair}
            except Exception as e:

                raise Exception("Could not locate IDL")

        elif idl_file_path is not None:
            with open_file(idl_file_path, "r") as interface_file_solana:
                json_idl = json.load(interface_file_solana)

            return {"idl": json_idl, "bytecode": bytecode, "program_address": program_address, "program_keypair": program_keypair}
        else:
            raise Exception("Could not locate IDL")

    @ staticmethod
    def is_transaction_valid(
        tx: dict
    ) -> bool:
        """
        Check whether a transaction is valid or not.

        :param tx: the transaction.
        :return: True if the random_message is equals to tx['input']
        """

        return NotImplementedError

    @ staticmethod
    def is_transaction_settled(tx_receipt: JSONLike) -> bool:
        """
        Check whether a transaction is settled or not.

        :param tx_receipt: the receipt associated to the transaction.
        :return: True if the transaction has been settled, False o/w.
        """
        is_successful = False
        if tx_receipt is not None:
            is_successful = tx_receipt['meta']['status'] == {
                'Ok': None}
        return is_successful

    @ staticmethod
    def get_hash(message: bytes) -> str:
        """
        Get the hash of a message.

        :param message: the message to be hashed.
        :return: the hash of the message as a hex string.
        """
        sha = hashlib.sha256()
        sha.update(message)
        return sha.hexdigest()

    @ classmethod
    def recover_message(
        cls, message: bytes, signature: str, is_deprecated_mode: bool = False
    ) -> Tuple[Address, ...]:
        """
        **TOBEIMPLEMENTED**
        Recover the addresses from the hash.

        :param message: the message we expect
        :param signature: the transaction signature
        :param is_deprecated_mode: if the deprecated signing was used
        :return: the recovered addresses
        """

        return NotImplementedError

    @ classmethod
    def recover_public_keys_from_message(
        cls, message: bytes, signature: str, is_deprecated_mode: bool = False
    ) -> Tuple[str, ...]:
        """
        **TOBEIMPLEMENTED**
        Get the public key used to produce the `signature` of the `message`

        :param message: raw bytes used to produce signature
        :param signature: signature of the message
        :param is_deprecated_mode: if the deprecated signing was used
        :return: the recovered public keys
        """

        return NotImplementedError

    @ try_decorator("Unable to get nonce: {}", logger_method="warning")
    def generate_tx_nonce(self) -> str:
        """
        Fetch a latest blockhash to distinguish transactions with the same terms.

        :return: return the blockhash as a nonce.
        """
        try:
            blockhash = self.BlockhashCache.get()
            # return json.loads(((Hash.from_string(blockhash)).to_json()))
            return blockhash
        except Exception as e:
            result = self._api.get_latest_blockhash()
            blockhash_json = result.value.to_json()
            blockhash = json.loads(blockhash_json)
            self.BlockhashCache.set(
                blockhash=blockhash['blockhash'], slot=result.context.slot)
            # return json.loads((Hash.from_string(blockhash['blockhash'])).to_json())
            return blockhash['blockhash']

    def add_nonce(self, tx: dict) -> JSONLike:
        """
        Check whether a transaction is valid or not.

        :param tx: the transaction.
        :return: True if the random_message is equals to tx['input']
        """
        jsonTx = json.dumps(tx)
        stxn = sTransaction.from_json(jsonTx)
        txObj = Transaction.from_solders(stxn)
        # blockash in string format
        nonce = self.generate_tx_nonce()
        txObj.recent_blockhash = nonce
        return json.loads(txObj._solders.to_json())

    def to_transaction_format(self, tx: dict) -> JSONLike:
        """
        Check whether a transaction is valid or not.

        :param tx: the transaction.
        :return: True if the random_message is equals to tx['input']
        """
        jsonTx = json.dumps(tx)
        stxn = sTransaction.from_json(jsonTx)
        return Transaction.from_solders(stxn)

    def to_dict_format(self, tx) -> JSONLike:
        """
        Check whether a transaction is valid or not.

        :param tx: the transaction.
        :return: True if the random_message is equals to tx['input']
        """

        return json.loads(tx._solders.to_json())

    def add_increase_compute_ix(self, tx, compute: int) -> JSONLike:
        """
        Check whether a transaction is valid or not.

        :param tx: the transaction.
        :return: True if the random_message is equals to tx['input']
        """
        program_id = PublicKey("ComputeBudget111111111111111111111111111111")

        name_bytes = bytearray(1 + 4 + 4)
        pack_into("B", name_bytes, 0, 0)
        pack_into("I", name_bytes, 1, compute)
        pack_into("I", name_bytes, 5, 0)
        data = bytes(name_bytes)

        compute_ix = TransactionInstruction([], program_id, data)
        tx = self.to_transaction_format(tx)
        tx.add(compute_ix)

        return self.to_dict_format(tx)

    @ staticmethod
    def get_contract_address(tx_receipt: JSONLike) -> Optional[list[str]]:
        """
        Retrieve the `contract_addresses` from a transaction receipt.
        **Solana can have many contract addresses in one tx**

        :param tx_receipt: the receipt of the transaction.
        :return: the contract address, if present
        """
        contract_addresses = []
        keys = tx_receipt['transaction']['message']['accountKeys']
        for ix in tx_receipt['transaction']['message']['instructions']:
            program_index = ix['programIdIndex']
            contract_addresses.append(keys[program_index])
        return contract_addresses

    @ classmethod
    def get_address_from_public_key(cls, public_key: PublicKey) -> str:
        """
        Get the address from the public key.

        :param public_key: the public key
        :return: str
        """

        return public_key.to_base58().decode()

    @ classmethod
    def is_valid_address(cls, address: str) -> bool:
        """
        Check if the address is valid.

        :param address: the address to validate
        :return: whether the address is valid
        """
        try:
            isValid = PublicKey(address)
            return True
        except Exception as e:
            return False


class SolanaApi(LedgerApi, SolanaHelper):
    """Class to interact with the Solana Web3 APIs."""

    identifier = _SOLANA

    def __init__(self, **kwargs: Any):
        """
        Initialize the Solana ledger APIs.

        :param kwargs: keyword arguments
        """

        Commitment = NewType("Commitment", str)
        """Type for commitment."""

        Finalized = Commitment("finalized")
        Confirmed = Commitment("confirmed")

        self._api = Client(
            endpoint=kwargs.pop("address", DEFAULT_ADDRESS), commitment=Confirmed
        )

        self.BlockhashCache = BlockhashCache(ttl=10)
        result = self._api.get_latest_blockhash()
        blockhash_json = result.value.to_json()
        blockhash = json.loads(blockhash_json)
        hash = blockhash['blockhash']
        self.BlockhashCache.set(blockhash=hash, slot=result.context.slot)

        self._chain_id = kwargs.pop("chain_id", DEFAULT_CHAIN_ID)
        self._version = _VERSION

    @ property
    def api(self) -> Client:
        """Get the underlying API object."""
        return self._api

    def update_with_gas_estimate(self, transaction: JSONLike) -> JSONLike:
        """
        **NOT APPLICABLE**
        Attempts to update the transaction with a gas estimate

        :param transaction: the transaction
        :return: the updated transaction
        """

        return transaction

    def get_balance(
        self, address: Address, raise_on_try: bool = False
    ) -> Optional[int]:
        """Get the balance of a given account."""
        return self._try_get_balance(address, raise_on_try=raise_on_try)

    @ try_decorator("Unable to retrieve balance: {}", logger_method="warning")
    def _try_get_balance(self, address: Address, **_kwargs: Any) -> Optional[int]:
        """Get the balance of a given account."""
        response = self._api.get_balance(
            PublicKey(address), commitment="processed")  # pylint: disable=no-member
        return response.value

    def get_state(
        self, address: str, *args: Any, raise_on_try: bool = False, **kwargs: Any
    ) -> Optional[JSONLike]:
        """Call a specified function on the ledger API."""
        response = self._try_get_state(
            address, *args, raise_on_try=raise_on_try, **kwargs
        )
        return response

    @ try_decorator("Unable to get state: {}", logger_method="warning")
    def _try_get_state(  # pylint: disable=unused-argument
        self, address: str, *args: Any, **kwargs: Any
    ) -> Optional[JSONLike]:
        """Try to call a function on the ledger API."""

        if "raise_on_try" in kwargs:
            logging.info(
                f"popping `raise_on_try` from {self.__class__.__name__}.get_state kwargs"
            )
            kwargs.pop("raise_on_try")

        account_object = self._api.get_account_info_json_parsed(
            PublicKey(address))
        account_info_val = account_object.value
        return account_info_val

    def get_transfer_transaction(  # pylint: disable=arguments-differ
        self,
        sender_address: Address,
        destination_address: Address,
        amount: int,
        chain_id: Optional[int] = None,
        raise_on_try: bool = False,
        **kwargs: Any,
    ) -> Optional[JSONLike]:
        """
        Submit a transfer transaction to the ledger.

        :param sender_address: the sender address of the payer.
        :param destination_address: the destination address of the payee.
        :param amount: the amount of wealth to be transferred (in Lamports).
        :param chain_id: the Chain ID of the Ethereum transaction.
        :param raise_on_try: whether the method will raise or log on error
        :param kwargs: keyword arguments
        :return: the transfer transaction
        """
        chain_id = chain_id if chain_id is not None else self._chain_id

        state = self.get_state(destination_address)
        if state is None:
            seed = "seed"
            acc = PublicKey.create_with_seed(
                PublicKey(sender_address), seed, PublicKey("11111111111111111111111111111111"))
            params = CreateAccountWithSeedParams(
                PublicKey(sender_address),
                acc,
                PublicKey(sender_address),
                seed,
                amount,
                0,
                PublicKey("11111111111111111111111111111111")
            )
            ix_create_pda = TransactionInstruction.from_solders(
                ssp.create_account_with_seed(params.to_solders()))

            params = ssp.TransferWithSeedParams(
                from_pubkey=acc.to_solders(),
                from_base=PublicKey(sender_address).to_solders(),
                from_seed=seed,
                from_owner=PublicKey(
                    "11111111111111111111111111111111").to_solders(),
                to_pubkey=PublicKey(destination_address).to_solders(),
                lamports=amount,
            )
            ix_transfer = TransactionInstruction.from_solders(
                ssp.transfer_with_seed(params))

            txn = Transaction(fee_payer=PublicKey(
                sender_address)).add(ix_create_pda).add(ix_transfer)
        else:
            txn = Transaction(fee_payer=sender_address).add(transfer(TransferParams(
                from_pubkey=PublicKey(sender_address), to_pubkey=PublicKey(destination_address), lamports=amount)))

        tx = txn._solders.to_json()

        return json.loads(tx)

    def send_signed_transaction(
        self, tx_signed: JSONLike, raise_on_try: bool = False
    ) -> Optional[str]:
        """
        Send a signed transaction and wait for confirmation.

        :param tx_signed: the signed transaction
        :param raise_on_try: whether the method will raise or log on error
        :return: tx_digest, if present
        """
        tx_digest = self._try_send_signed_transaction(
            tx_signed, raise_on_try=True
        )
        try:
            tx = json.loads(tx_digest)
        except Exception as e:
            print(e)
        return tx['result']

    @ try_decorator("Unable to send transaction: {}", logger_method="warning")
    def _try_send_signed_transaction(
        self, tx_signed: JSONLike, **_kwargs: Any
    ) -> Optional[str]:
        """
        Try send a signed transaction.

        :param tx_signed: the signed transaction
        :param _kwargs: the keyword arguments. Possible kwargs are:
            `raise_on_try`: bool flag specifying whether the method will raise or log on error (used by `try_decorator`)
        :return: tx_digest, if present
        """

        # txOpts = types.TxOpts(skip_preflight=True)

        jsonTx = json.dumps(tx_signed)
        stxn = sTransaction.from_json(jsonTx)
        txn = Transaction.from_solders(stxn)

        # txn = tx_signed

        txn_resp = self._api.send_raw_transaction(
            txn.serialize())

        return txn_resp.to_json()

    def get_transaction_receipt(
        self, tx_digest: str, raise_on_try: bool = False
    ) -> Optional[JSONLike]:
        """
        Get the transaction receipt for a transaction digest.

        :param tx_digest: the digest associated to the transaction.
        :param raise_on_try: whether the method will raise or log on error
        :return: the tx receipt, if present
        """
        tx_receipt = self._try_get_transaction_receipt(
            tx_digest,
            raise_on_try=raise_on_try,
        )

        return tx_receipt

    @ try_decorator(
        "Error when attempting getting tx receipt: {}", logger_method="debug"
    )
    def _try_get_transaction_receipt(
        self, tx_digest: str, **_kwargs: Any
    ) -> Optional[JSONLike]:
        """
        Try get the transaction receipt.

        :param tx_digest: the digest associated to the transaction.
        :param _kwargs: the keyword arguments. Possible kwargs are:
            `raise_on_try`: bool flag specifying whether the method will raise or log on error (used by `try_decorator`)
        :return: the tx receipt, if present
        """

        tx_receipt = self._api.get_transaction(
            Signature.from_string(tx_digest))  # pylint: disable=no-member

        tx = json.loads(tx_receipt.to_json())
        return tx["result"]

    def get_transaction(
        self,
        tx_digest: str,
        raise_on_try: bool = False,
    ) -> Optional[JSONLike]:
        """
        Get the transaction for a transaction digest.

        :param tx_digest: the digest associated to the transaction.
        :param raise_on_try: whether the method will raise or log on error
        :return: the tx, if present
        """
        tx = self._try_get_transaction(tx_digest, raise_on_try=raise_on_try)
        return tx

    @ try_decorator("Error when attempting getting tx: {}", logger_method="debug")
    def _try_get_transaction(
        self, tx_digest: str, **_kwargs: Any
    ) -> Optional[JSONLike]:
        """
        Get the transaction.

        :param tx_digest: the transaction digest.
        :param _kwargs: the keyword arguments. Possible kwargs are:
            `raise_on_try`: bool flag specifying whether the method will raise or log on error (used by `try_decorator`)
        :return: the tx, if found
        """
        tx = self._api.get_transaction(Signature.from_string(tx_digest))

        # pylint: disable=no-member
        return json.loads(tx.value.to_json())

    def create_default_account(self, from_address: str, new_account_address: str, lamports: int, space: int, program_id: Optional[str] = SYS_PROGRAM_ID):
        """
        Build a create account transaction.

        :param from_pubkey: the sender public key
        :param new_account_pubkey: the new account public key
        :param lamports: the amount of lamports to send
        :param space: the space to allocate
        :param program_id: the program id
        :return: the tx, if present
        """
        params = CreateAccountParams(
            PublicKey(from_address),
            PublicKey(new_account_address),
            lamports,
            space,
            PublicKey(program_id)
        )
        createAccountInstruction = create_account(params)
        txn = Transaction(fee_payer=from_address).add(
            createAccountInstruction)
        tx = txn._solders.to_json()
        return json.loads(tx)

    def create_pda(self,
                   from_address: str,
                   new_account_address: str,
                   base_address: str,
                   seed: str,
                   lamports: int,
                   space: int,
                   program_id: str):
        """
        Build a create pda transaction.

        :param from_pubkey: the sender public key
        :param new_account_pubkey: the new account public key
        :param lamports: the amount of lamports to send
        :param space: the space to allocate
        :param program_id: the program id
        :return: the tx, if present
        """
        params = CreateAccountWithSeedParams(
            PublicKey(from_address),
            PublicKey(new_account_address),
            PublicKey(base_address),
            seed,
            lamports,
            space,
            PublicKey(program_id)
        )
        createPDAInstruction = TransactionInstruction.from_solders(
            ssp.create_account_with_seed(params.to_solders()))
        txn = Transaction().add(
            createPDAInstruction)
        tx = txn._solders.to_json()
        return json.loads(tx)

    def get_contract_instance(
        self, contract_interface: Dict[str, str], contract_address: str, bytecode_path: Optional[Path] = None
    ) -> Any:
        """
        Get the instance of a contract.

        :param contract_interface: the contract interface.
        :param contract_address: the contract address.
        :param bytecode: the contract bytecode.
        :return: the contract instance
        """

        program_id = PublicKey(contract_address)
        idl = Idl.from_json(json.dumps(contract_interface["idl"]))
        pg = Program(idl, program_id)

        pg.provider.connection = self.api

        if bytecode_path is not None:
            # opening for [r]eading as [b]inary
            in_file = open(bytecode_path, "rb")
            bytecode = in_file.read()
        else:
            bytecode = None
        return {"program": pg, "bytecode": bytecode}

    def get_deploy_transaction(  # pylint: disable=arguments-differ
        self,
        contract_interface: Dict[Any, Any],
        payer_keypair: Address,
        raise_on_try: bool = False,
        **kwargs: Any,
    ) -> Optional[JSONLike]:
        """

        Deploy the smart contract.

        :param contract_interface: the contract instance.
        :param payer_keypair: The keypair that will deploy the contract.
        :param raise_on_try: whether the method will raise or log on error
        :param kwargs: keyword arguments
        :return: the transaction dictionary.
        """
        return NotImplementedError
        # if contract_interface["bytecode"] is None or contract_interface["program_keypair"] is None:
        #     raise ValueError("Bytecode or program_keypair is required")

        # # check if solana cli is installed
        # result = subprocess.run(
        #     ["solana --version"], capture_output=True, text=True, shell=True)
        # if result.stderr != "":
        #     raise ValueError(result.stderr)

        # # save keys in uint8 array temp
        # value = struct.unpack('64B', payer_keypair.entity.secret_key)
        # uint8_array = array.array('B', value)
        # payer_uint8 = uint8_array.tolist()
        # temp_dir_payer = Path(tempfile.mkdtemp())
        # temp_file_payer = temp_dir_payer / "payer.json"
        # temp_file_payer.write_text(str(payer_uint8))

        # value = struct.unpack(
        #     '64B', contract_interface["program_keypair"].entity.secret_key)
        # uint8_array = array.array('B', value)
        # program_uint8 = uint8_array.tolist()
        # temp_dir_program = Path(tempfile.mkdtemp())
        # temp_file_program = temp_dir_program / "program.json"
        # temp_file_program.write_text(str(program_uint8))

        # t = SolanaCrypto(temp_file_payer)
        # temp_dir_bytecode = Path(tempfile.mkdtemp())
        # temp_file_bytecode = temp_dir_bytecode / "bytecode.so"
        # temp_file_bytecode.write_bytes(contract_interface["bytecode"])

        # cmd = f'''solana program deploy --url {DEFAULT_ADDRESS} -v --keypair {str(temp_file_payer)} --program-id {str(temp_file_program)} {str(temp_file_bytecode)}'''

        # result = subprocess.run(
        #     [cmd], capture_output=True, text=True, shell=True)

        # if result.stderr != "":
        #     raise ValueError(result.stderr)

        # return result.stdout

    @ classmethod
    def contract_method_call(
        cls,
        contract_instance: Any,
        method_name: str,
        **method_args: Any,
    ) -> Optional[JSONLike]:
        """Call a contract's method
        **TOBEIMPLEMENTED**

        :param contract_instance: the contract to use
        :param method_name: the contract method to call
        :param method_args: the contract call parameters
        :return: the call result
        """

        return NotImplementedError

    def build_transaction(  # pylint: disable=too-many-arguments
        self,
        contract_instance: Any,
        method_name: str,
        method_args: Optional[Dict[Any, Any]],
        tx_args: Optional[Dict[Any, Any]],
        raise_on_try: bool = False,
    ) -> Optional[JSONLike]:
        """Prepare a transaction

        :param contract_instance: the contract to use
        :param method_name: the contract method to call
        :param method_args: the contract parameters
        :param tx_args: the transaction parameters
        :param raise_on_try: whether the method will raise or log on error
        :return: the transaction
        """
        if method_args['data'] is None:
            raise ValueError("Data is required")
        if method_args['accounts'] is None:
            raise ValueError("Accounts are required")
        if "remaining_accounts" not in method_args:
            method_args['remaining_accounts'] = None

        data = method_args['data']
        accounts = method_args['accounts']
        remaining_accounts = method_args['remaining_accounts']

        txn = contract_instance.transaction[method_name](*data, ctx=Context(
            accounts=accounts,
            remaining_accounts=remaining_accounts))
        tx = txn._solders.to_json()
        return json.loads(tx)

    def get_transaction_transfer_logs(  # pylint: disable=too-many-arguments,too-many-locals
        self,
        tx_hash: str,
        target_address: Optional[str] = None,
    ) -> Optional[JSONLike]:
        """
        Get all transfer events derived from a transaction.

        :param tx_hash: the transaction hash
        :param target_address: optional address to filter tranfer events to just those that affect it
        :return: the transfer logs
        """
        try:
            tx_receipt = self.get_transaction_receipt(tx_hash)
            if tx_receipt is None:
                raise ValueError  # pragma: nocover

        except (Exception, ValueError):  # pragma: nocover
            return dict()

        keys = tx_receipt['transaction']['message']['accountKeys']
        if target_address:
            transfers = {
                "preBalances": [
                    {"address": keys[idx], "balance":balance} for idx, balance in enumerate(tx_receipt['meta']['preBalances'])
                    if keys[idx] == target_address

                ],
                "postBalances": [
                    {"address": keys[idx], "balance":balance} for idx, balance in enumerate(tx_receipt['meta']['postBalances'])
                    if keys[idx] == target_address

                ]
            }
        else:
            transfers = {
                "preBalances": [
                    {"address": keys[idx], "balance":balance} for idx, balance in enumerate(tx_receipt['meta']['preBalances'])
                ],
                "postBalances": [
                    {"address": keys[idx], "balance":balance} for idx, balance in enumerate(tx_receipt['meta']['postBalances'])
                ]
            }

        return transfers


class SolanaFaucetApi(FaucetApi):
    """Solana testnet faucet API."""

    identifier = _SOLANA
    testnet_name = TESTNET_NAME

    def get_wealth(self, address: Address, amount: Optional[int] = None, url: Optional[str] = None) -> None:
        """
        Get wealth from the faucet for the provided address.

        :param address: the address.
        :param amount: the amount of sol to airdrop.
        :param url: the url
        """

        return self._try_get_wealth(address, amount, url)

    @ staticmethod
    @ try_decorator(
        "An error occured while attempting to generate wealth:\n{}",
        logger_method="error",
    )
    def _try_get_wealth(address: Address, amount: Optional[int] = None, url: Optional[str] = None) -> str or None:
        """
        Get wealth from the faucet for the provided address.

        :param address: the address.
        :param url: the url
        """
        if url is None:
            url = DEFAULT_ADDRESS

        if amount is None:
            amount = LAMPORTS_PER_SOL*0.5
        else:
            amount = LAMPORTS_PER_SOL*amount

        solana_client = Client(url, commitment='confirmed')
        resp = solana_client.request_airdrop(
            PublicKey(address), amount)

        response = (json.loads(resp.to_json()))
        if 'message' in response:
            _default_logger.error(
                "Response: {}".format(response.message))
            raise Exception(response.get('message'))
        if response['result'] == None:
            _default_logger.error("Response: {}".format("airdrop failed"))
        elif "error" in response:  # pragma: no cover
            _default_logger.error("Response: {}".format("airdrop failed"))
        elif "result" in response:  # pragma: nocover

            _default_logger.warning(
                "Response: {}\nMessage: {}".format(
                    "success", response['result']
                )
            )
            return response['result']
