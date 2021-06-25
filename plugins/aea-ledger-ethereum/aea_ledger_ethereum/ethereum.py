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
import json
import logging
import threading
import time
import warnings
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union, cast

import ipfshttpclient  # noqa: F401 # pylint: disable=unused-import
import web3._utils.request
from eth_account import Account
from eth_account._utils.signing import to_standard_signature_bytes
from eth_account.datastructures import HexBytes, SignedTransaction
from eth_account.messages import _hash_eip191_message, encode_defunct
from eth_keys import keys
from eth_typing import HexStr
from lru import LRU  # type: ignore  # pylint: disable=no-name-in-module
from web3 import HTTPProvider, Web3
from web3.datastructures import AttributeDict
from web3.gas_strategies.rpc import rpc_gas_price_strategy
from web3.types import TxData, TxParams, TxReceipt, Wei

from aea.common import Address, JSONLike
from aea.crypto.base import Crypto, FaucetApi, Helper, LedgerApi
from aea.crypto.helpers import DecryptError, KeyIsIncorrect, hex_to_bytes_for_key
from aea.exceptions import enforce
from aea.helpers import http_requests as requests
from aea.helpers.base import try_decorator
from aea.helpers.io import open_file


_default_logger = logging.getLogger(__name__)

_ETHEREUM = "ethereum"
TESTNET_NAME = "ganache"
DEFAULT_ADDRESS = "http://127.0.0.1:8545"
DEFAULT_CHAIN_ID = 1337
DEFAULT_CURRENCY_DENOM = "wei"
ETH_GASSTATION_URL = "https://ethgasstation.info/api/ethgasAPI.json"
_ABI = "abi"
_BYTECODE = "bytecode"


def get_gas_price_strategy(
    gas_price_strategy: Optional[str] = None, api_key: Optional[str] = None
) -> Callable[[Web3, TxParams], Wei]:
    """Get the gas price strategy."""
    supported_gas_price_modes = ["safeLow", "average", "fast", "fastest"]
    if gas_price_strategy is None:
        _default_logger.debug(
            "Gas price strategy not provided. Falling back to `rpc_gas_price_strategy`."
        )
        return rpc_gas_price_strategy

    if gas_price_strategy not in supported_gas_price_modes:
        _default_logger.debug(
            f"Gas price strategy `{gas_price_strategy}` not in list of supported modes: {supported_gas_price_modes}. Falling back to `rpc_gas_price_strategy`."
        )
        return rpc_gas_price_strategy

    if api_key is None:
        _default_logger.debug(
            "No ethgasstation api key provided. Falling back to `rpc_gas_price_strategy`."
        )
        return rpc_gas_price_strategy

    def gas_station_gas_price_strategy(  # pylint: disable=redefined-outer-name,unused-argument
        web3: Web3, transaction_params: TxParams
    ) -> Wei:
        """
        Get gas price from Eth Gas Station api.

        Visit `https://docs.ethgasstation.info/gas-price` for documentation.

        :param web3: web3 instance
        :param transaction_params: transaction parameters
        :return: wei
        """
        response = requests.get(f"{ETH_GASSTATION_URL}?api-key={api_key}")
        if response.status_code != 200:
            raise ValueError(  # pragma: nocover
                f"Gas station API response: {response.status_code}, {response.text}"
            )
        response_dict = response.json()
        _default_logger.debug("Gas station API response: {}".format(response_dict))
        result = response_dict.get(gas_price_strategy, None)
        if type(result) not in [int, float]:  # pragma: nocover
            raise ValueError(f"Invalid return value for `{gas_price_strategy}`!")
        gwei_result = result / 10  # adjustment (see api documentation)
        wei_result = web3.toWei(gwei_result, "gwei")
        return wei_result

    return gas_station_gas_price_strategy


class SignedTransactionTranslator:
    """Translator for SignedTransaction."""

    @staticmethod
    def to_dict(signed_transaction: SignedTransaction) -> Dict[str, Union[str, int]]:
        """Write SignedTransaction to dict."""
        signed_transaction_dict = {
            "raw_transaction": signed_transaction.rawTransaction.hex(),
            "hash": signed_transaction.hash.hex(),
            "r": signed_transaction.r,
            "s": signed_transaction.s,
            "v": signed_transaction.v,
        }
        return signed_transaction_dict

    @staticmethod
    def from_dict(signed_transaction_dict: JSONLike) -> SignedTransaction:
        """Get SignedTransaction from dict."""
        if (
            not isinstance(signed_transaction_dict, dict)
            and len(signed_transaction_dict) == 5
        ):
            raise ValueError(  # pragma: nocover
                f"Invalid for conversion. Found object: {signed_transaction_dict}."
            )
        signed_transaction = SignedTransaction(
            rawTransaction=HexBytes(signed_transaction_dict["raw_transaction"]),
            hash=HexBytes(signed_transaction_dict["hash"]),
            r=signed_transaction_dict["r"],
            s=signed_transaction_dict["s"],
            v=signed_transaction_dict["v"],
        )
        return signed_transaction


class AttributeDictTranslator:
    """Translator for AttributeDict."""

    @classmethod
    def _remove_hexbytes(cls, value: Any) -> Any:
        """Process value to remove hexbytes."""
        if value is None:
            return value
        if isinstance(value, HexBytes):
            return value.hex()
        if isinstance(value, list):
            return cls._process_list(value, cls._remove_hexbytes)
        if type(value) in (bool, int, float, str, bytes):
            return value
        if isinstance(value, AttributeDict):
            return cls.to_dict(value)
        raise NotImplementedError(  # pragma: nocover
            f"Unknown type conversion. Found type: {type(value)}"
        )

    @classmethod
    def _add_hexbytes(cls, value: Any) -> Any:
        """Process value to add hexbytes."""
        if value is None:
            return value
        if isinstance(value, str):
            try:
                int(value, 16)
                return HexBytes(value)
            except Exception:  # pylint: disable=broad-except
                return value
        if isinstance(value, list):
            return cls._process_list(value, cls._add_hexbytes)
        if isinstance(value, dict):
            return cls.from_dict(value)
        if type(value) in (bool, int, float, bytes):
            return value
        raise NotImplementedError(  # pragma: nocover
            f"Unknown type conversion. Found type: {type(value)}"
        )

    @classmethod
    def _process_list(cls, li: list, callable_name: Callable) -> List:
        """Simplify a list with process value."""
        return [callable_name(el) for el in li]

    @classmethod
    def _valid_key(cls, key: Any) -> str:
        """Check validity of key."""
        if isinstance(key, str):
            return key
        raise ValueError("Key must be string.")  # pragma: nocover

    @classmethod
    def to_dict(cls, attr_dict: Union[AttributeDict, TxReceipt, TxData]) -> JSONLike:
        """Simplify to dict."""
        if not isinstance(attr_dict, AttributeDict):
            raise ValueError("No AttributeDict provided.")  # pragma: nocover
        result = {
            cls._valid_key(key): cls._remove_hexbytes(value)
            for key, value in attr_dict.items()
        }
        return result

    @classmethod
    def from_dict(cls, di: JSONLike) -> AttributeDict:
        """Get back attribute dict."""
        if not isinstance(di, dict):
            raise ValueError("No dict provided.")  # pragma: nocover
        processed_dict = {
            cls._valid_key(key): cls._add_hexbytes(value) for key, value in di.items()
        }
        return AttributeDict(processed_dict)


class EthereumCrypto(Crypto[Account]):
    """Class wrapping the Account Generation from Ethereum ledger."""

    identifier = _ETHEREUM

    def __init__(
        self, private_key_path: Optional[str] = None, password: Optional[str] = None
    ) -> None:
        """
        Instantiate an ethereum crypto object.

        :param private_key_path: the private key path of the agent
        :param password: the password to encrypt/decrypt the private key.
        """
        super().__init__(private_key_path=private_key_path, password=password)
        bytes_representation = Web3.toBytes(hexstr=self.entity.key.hex())
        self._public_key = str(keys.PrivateKey(bytes_representation).public_key)
        self._address = str(self.entity.address)

    @property
    def private_key(self) -> str:
        """
        Return a private key.

        :return: a private key string
        """
        return self.entity.key.hex()

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
    def load_private_key_from_path(
        cls, file_name: str, password: Optional[str] = None
    ) -> Account:
        """
        Load a private key in hex format from a file.

        :param file_name: the path to the hex file.
        :param password: the password to encrypt/decrypt the private key.
        :return: the Entity.
        """
        private_key = cls.load(file_name, password)
        try:
            if not private_key.startswith("0x"):
                hex_to_bytes_for_key(private_key)
        except KeyIsIncorrect as e:
            if not password:
                raise KeyIsIncorrect(
                    f"Error on key `{file_name}` load! Try to specify `password`: Error: {repr(e)} "
                ) from e
            raise KeyIsIncorrect(
                f"Error on key `{file_name}` load! Wrong password?: Error: {repr(e)} "
            ) from e

        account = Account.from_key(  # pylint: disable=no-value-for-parameter
            private_key=private_key
        )
        return account

    def sign_message(self, message: bytes, is_deprecated_mode: bool = False) -> str:
        """
        Sign a message in bytes string form.

        :param message: the message to be signed
        :param is_deprecated_mode: if the deprecated signing is used
        :return: signature of the message in string form
        """
        if is_deprecated_mode and len(message) == 32:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                signature_dict = self.entity.signHash(message)
            signed_msg = signature_dict["signature"].hex()
        else:
            signable_message = encode_defunct(primitive=message)
            signature = self.entity.sign_message(signable_message=signable_message)
            signed_msg = signature["signature"].hex()
        return signed_msg

    def sign_transaction(self, transaction: JSONLike) -> JSONLike:
        """
        Sign a transaction in bytes string form.

        :param transaction: the transaction to be signed
        :return: signed transaction
        """
        signed_transaction = self.entity.sign_transaction(transaction_dict=transaction)
        #  Note: self.entity.signTransaction(transaction_dict=transaction) == signed_transaction # noqa: E800
        signed_transaction_dict = SignedTransactionTranslator.to_dict(
            signed_transaction
        )
        return cast(JSONLike, signed_transaction_dict)

    @classmethod
    def generate_private_key(cls) -> Account:
        """Generate a key pair for ethereum network."""
        account = Account.create()  # pylint: disable=no-value-for-parameter
        return account

    def encrypt(self, password: str) -> str:
        """
        Encrypt the private key and return in json.

        :param password: the password to decrypt.
        :return: json string containing encrypted private key.
        """
        encrypted = Account.encrypt(self.private_key, password)
        return json.dumps(encrypted)

    @classmethod
    def decrypt(cls, keyfile_json: str, password: str) -> str:
        """
        Decrypt the private key and return in raw form.

        :param keyfile_json: json str containing encrypted private key.
        :param password: the password to decrypt.
        :return: the raw private key.
        """
        try:
            private_key = Account.decrypt(keyfile_json, password)
        except ValueError as e:
            if e.args[0] == "MAC mismatch":
                raise DecryptError() from e
            raise
        return private_key.hex()[2:]


class EthereumHelper(Helper):
    """Helper class usable as Mixin for EthereumApi or as standalone class."""

    @staticmethod
    def is_transaction_settled(tx_receipt: JSONLike) -> bool:
        """
        Check whether a transaction is settled or not.

        :param tx_receipt: the receipt associated to the transaction.
        :return: True if the transaction has been settled, False o/w.
        """
        is_successful = False
        if tx_receipt is not None:
            is_successful = tx_receipt.get("status", 0) == 1
        return is_successful

    @staticmethod
    def get_contract_address(tx_receipt: JSONLike) -> Optional[str]:
        """
        Retrieve the `contract_address` from a transaction receipt.

        :param tx_receipt: the receipt of the transaction.
        :return: the contract address, if present
        """
        contract_address = cast(Optional[str], tx_receipt.get("contractAddress", None))
        return contract_address

    @staticmethod
    def is_transaction_valid(
        tx: dict, seller: Address, client: Address, tx_nonce: str, amount: int,
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
            is_valid = (
                tx.get("input") == tx_nonce
                and tx.get("value") == amount
                and tx.get("from") == client
                and tx.get("to") == seller
            )
        return is_valid

    @staticmethod
    def generate_tx_nonce(seller: Address, client: Address) -> str:
        """
        Generate a unique hash to distinguish transactions with the same terms.

        :param seller: the address of the seller.
        :param client: the address of the client.
        :return: return the hash in hex.
        """
        time_stamp = int(time.time())
        aggregate_hash = Web3.keccak(
            b"".join([seller.encode(), client.encode(), time_stamp.to_bytes(32, "big")])
        )
        return aggregate_hash.hex()

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
        if is_deprecated_mode:
            enforce(len(message) == 32, "Message must be hashed to exactly 32 bytes.")
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                address = Account.recoverHash(  # pylint: disable=no-value-for-parameter
                    message_hash=message, signature=signature
                )
        else:
            signable_message = encode_defunct(primitive=message)
            address = Account.recover_message(  # pylint: disable=no-value-for-parameter
                signable_message=signable_message, signature=signature
            )
        return (address,)

    @classmethod
    def recover_public_keys_from_message(
        cls, message: bytes, signature: str, is_deprecated_mode: bool = False
    ) -> Tuple[str, ...]:
        """
        Get the public key used to produce the `signature` of the `message`

        :param message: raw bytes used to produce signature
        :param signature: signature of the message
        :param is_deprecated_mode: if the deprecated signing was used
        :return: the recovered public keys
        """
        if not is_deprecated_mode:
            signable_message = encode_defunct(primitive=message)
            message = _hash_eip191_message(signable_message)
        hash_bytes = HexBytes(message)
        # code taken from https://github.com/ethereum/eth-account/blob/master/eth_account/account.py#L428
        if len(hash_bytes) != 32:  # pragma: nocover
            raise ValueError("The message hash must be exactly 32-bytes")
        signature_bytes = HexBytes(signature)
        signature_bytes_standard = to_standard_signature_bytes(signature_bytes)
        signature_obj = keys.Signature(signature_bytes=signature_bytes_standard)
        pubkey = signature_obj.recover_public_key_from_msg_hash(hash_bytes)
        return (str(pubkey),)

    @staticmethod
    def get_hash(message: bytes) -> str:
        """
        Get the hash of a message.

        :param message: the message to be hashed.
        :return: the hash of the message.
        """
        digest = Web3.keccak(message).hex()
        return digest

    @classmethod
    def load_contract_interface(cls, file_path: Path) -> Dict[str, str]:
        """
        Load contract interface.

        :param file_path: the file path to the interface
        :return: the interface
        """
        with open_file(file_path, "r") as interface_file_ethereum:
            contract_interface = json.load(interface_file_ethereum)
        for key in [_ABI, _BYTECODE]:
            if key not in contract_interface:  # pragma: nocover
                raise ValueError(f"Contract {file_path} missing key {key}.")
        return contract_interface


class EthereumApi(LedgerApi, EthereumHelper):
    """Class to interact with the Ethereum Web3 APIs."""

    identifier = _ETHEREUM

    def __init__(self, **kwargs: Any):
        """
        Initialize the Ethereum ledger APIs.

        :param kwargs: keyword arguments
        """
        self._api = Web3(
            HTTPProvider(endpoint_uri=kwargs.pop("address", DEFAULT_ADDRESS))
        )
        self._chain_id = kwargs.pop("chain_id", DEFAULT_CHAIN_ID)
        self._gas_price_api_key = kwargs.pop("gas_price_api_key", None)

    @property
    def api(self) -> Web3:
        """Get the underlying API object."""
        return self._api

    def get_balance(self, address: Address) -> Optional[int]:
        """Get the balance of a given account."""
        return self._try_get_balance(address)

    @try_decorator("Unable to retrieve balance: {}", logger_method="warning")
    def _try_get_balance(self, address: Address) -> Optional[int]:
        """Get the balance of a given account."""
        check_address = self._api.toChecksumAddress(address)
        return self._api.eth.getBalance(check_address)  # pylint: disable=no-member

    def get_state(
        self, callable_name: str, *args: Any, **kwargs: Any
    ) -> Optional[JSONLike]:
        """Call a specified function on the ledger API."""
        response = self._try_get_state(callable_name, *args, **kwargs)
        return response

    @try_decorator("Unable to get state: {}", logger_method="warning")
    def _try_get_state(  # pylint: disable=unused-argument
        self, callable_name: str, *args: Any, **kwargs: Any
    ) -> Optional[JSONLike]:
        """Try to call a function on the ledger API."""

        function = getattr(self._api.eth, callable_name)
        response = function(*args, **kwargs)

        if isinstance(response, AttributeDict):
            result = AttributeDictTranslator.to_dict(response)
            return result

        if type(response) in (int, float, bytes, str, list, dict):  # pragma: nocover
            # missing full checks for nested objects
            return {f"{callable_name}_result": response}
        raise NotImplementedError(  # pragma: nocover
            f"Response must be of types=int, float, bytes, str, list, dict. Found={type(response)}."
        )

    def get_transfer_transaction(  # pylint: disable=arguments-differ
        self,
        sender_address: Address,
        destination_address: Address,
        amount: int,
        tx_fee: int,
        tx_nonce: str,
        chain_id: Optional[int] = None,
        gas_price: Optional[str] = None,
        gas_price_strategy: Optional[str] = None,
        **kwargs: Any,
    ) -> Optional[JSONLike]:
        """
        Submit a transfer transaction to the ledger.

        :param sender_address: the sender address of the payer.
        :param destination_address: the destination address of the payee.
        :param amount: the amount of wealth to be transferred (in Wei).
        :param tx_fee: the transaction fee (gas) to be used (in Wei).
        :param tx_nonce: verifies the authenticity of the tx.
        :param chain_id: the Chain ID of the Ethereum transaction.
        :param gas_price: the gas price (in Wei)
        :param gas_price_strategy: the gas price strategy to be used.
        :param kwargs: keyword arguments
        :return: the transfer transaction
        """
        transaction: Optional[JSONLike] = None
        chain_id = chain_id if chain_id is not None else self._chain_id
        gas_price = (
            self._try_get_gas_price(gas_price_strategy)
            if gas_price is None
            else gas_price
        )
        if gas_price is None:
            return transaction  # pragma: nocover
        nonce = self._try_get_transaction_count(sender_address)
        if nonce is None:
            return transaction
        transaction = {
            "nonce": nonce,
            "chainId": chain_id,
            "to": destination_address,
            "value": amount,
            "gas": tx_fee,
            "gasPrice": gas_price,
            "data": tx_nonce,
        }
        transaction = self.update_with_gas_estimate(transaction)
        return transaction

    @try_decorator("Unable to retrieve gas price: {}", logger_method="warning")
    def _try_get_gas_price(
        self, gas_price_strategy: Optional[str] = None
    ) -> Optional[int]:
        """Try get the gas price based on the provided strategy."""
        gas_price_strategy_callable = get_gas_price_strategy(
            gas_price_strategy, self._gas_price_api_key
        )
        prior_strategy = self._api.eth.gasPriceStrategy
        try:
            self._api.eth.setGasPriceStrategy(gas_price_strategy_callable)
            gas_price = self._api.eth.generateGasPrice()
        finally:
            if prior_strategy is not None:
                self._api.eth.setGasPriceStrategy(prior_strategy)  # pragma: nocover
        return gas_price

    @try_decorator("Unable to retrieve transaction count: {}", logger_method="warning")
    def _try_get_transaction_count(self, address: Address) -> Optional[int]:
        """Try get the transaction count."""
        nonce = self._api.eth.getTransactionCount(  # pylint: disable=no-member
            self._api.toChecksumAddress(address)
        )
        return nonce

    def update_with_gas_estimate(self, transaction: JSONLike) -> JSONLike:
        """
        Attempts to update the transaction with a gas estimate

        :param transaction: the transaction
        :return: the updated transaction
        """
        gas_estimate = self._try_get_gas_estimate(transaction)
        if gas_estimate is not None:
            specified_gas = transaction["gas"]
            if specified_gas < gas_estimate:
                # eventually; there should be some specifiable strategy
                _default_logger.warning(  # pragma: nocover
                    f"Needed to increase gas to cover the gas consumption of the transaction. Estimated gas consumption is: {gas_estimate}. Specified gas was: {specified_gas}."
                )
            transaction["gas"] = gas_estimate
        return transaction

    @try_decorator("Unable to retrieve gas estimate: {}", logger_method="warning")
    def _try_get_gas_estimate(self, transaction: JSONLike) -> Optional[int]:
        """Try get the gas estimate."""
        gas_estimate = self._api.eth.estimateGas(  # pylint: disable=no-member
            transaction=cast(TxParams, AttributeDictTranslator.from_dict(transaction))
        )
        return gas_estimate

    def send_signed_transaction(self, tx_signed: JSONLike) -> Optional[str]:
        """
        Send a signed transaction and wait for confirmation.

        :param tx_signed: the signed transaction
        :return: tx_digest, if present
        """
        tx_digest = self._try_send_signed_transaction(tx_signed)
        return tx_digest

    @try_decorator("Unable to send transaction: {}", logger_method="warning")
    def _try_send_signed_transaction(self, tx_signed: JSONLike) -> Optional[str]:
        """
        Try send a signed transaction.

        :param tx_signed: the signed transaction
        :return: tx_digest, if present
        """
        signed_transaction = SignedTransactionTranslator.from_dict(tx_signed)
        hex_value = self._api.eth.sendRawTransaction(  # pylint: disable=no-member
            signed_transaction.rawTransaction
        )
        tx_digest = hex_value.hex()
        _default_logger.debug(
            "Successfully sent transaction with digest: {}".format(tx_digest)
        )
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
        "Error when attempting getting tx receipt: {}", logger_method="debug"
    )
    def _try_get_transaction_receipt(self, tx_digest: str) -> Optional[JSONLike]:
        """
        Try get the transaction receipt.

        :param tx_digest: the digest associated to the transaction.
        :return: the tx receipt, if present
        """
        tx_receipt = self._api.eth.getTransactionReceipt(  # pylint: disable=no-member
            cast(HexStr, tx_digest)
        )
        return AttributeDictTranslator.to_dict(tx_receipt)

    def get_transaction(self, tx_digest: str) -> Optional[JSONLike]:
        """
        Get the transaction for a transaction digest.

        :param tx_digest: the digest associated to the transaction.
        :return: the tx, if present
        """
        tx = self._try_get_transaction(tx_digest)
        return tx

    @try_decorator("Error when attempting getting tx: {}", logger_method="debug")
    def _try_get_transaction(self, tx_digest: str) -> Optional[JSONLike]:
        """
        Get the transaction.

        :param tx_digest: the transaction digest.
        :return: the tx, if found
        """
        tx = self._api.eth.getTransaction(
            cast(HexStr, tx_digest)
        )  # pylint: disable=no-member
        return AttributeDictTranslator.to_dict(tx)

    def get_contract_instance(
        self, contract_interface: Dict[str, str], contract_address: Optional[str] = None
    ) -> Any:
        """
        Get the instance of a contract.

        :param contract_interface: the contract interface.
        :param contract_address: the contract address.
        :return: the contract instance
        """
        if contract_address is None:
            instance = self.api.eth.contract(
                abi=contract_interface[_ABI], bytecode=contract_interface[_BYTECODE],
            )
        else:
            _contract_address = self.api.toChecksumAddress(contract_address)
            instance = self.api.eth.contract(
                address=_contract_address,
                abi=contract_interface[_ABI],
                bytecode=contract_interface[_BYTECODE],
            )
        return instance

    def get_deploy_transaction(  # pylint: disable=arguments-differ
        self,
        contract_interface: Dict[str, str],
        deployer_address: Address,
        value: int = 0,
        gas: int = 0,
        gas_price: Optional[str] = None,
        gas_price_strategy: Optional[str] = None,
        **kwargs: Any,
    ) -> Optional[JSONLike]:
        """
        Get the transaction to deploy the smart contract.

        :param contract_interface: the contract interface.
        :param deployer_address: The address that will deploy the contract.
        :param value: value to send to contract (in Wei)
        :param gas: the gas to be used (in Wei)
        :param gas_price: the gas price (in Wei)
        :param gas_price_strategy: the gas price strategy to be used.
        :param kwargs: keyword arguments
        :return: the transaction dictionary.
        """
        transaction: Optional[JSONLike] = None
        _deployer_address = self.api.toChecksumAddress(deployer_address)
        nonce = self.api.eth.getTransactionCount(_deployer_address)
        if nonce is None:
            return transaction
        gas_price = (
            self._try_get_gas_price(gas_price_strategy)
            if gas_price is None
            else gas_price
        )
        if gas_price is None:
            return transaction  # pragma: nocover
        instance = self.get_contract_instance(contract_interface)
        data = instance.constructor(**kwargs).buildTransaction().get("data", "0x")
        transaction = {
            "from": _deployer_address,  # only 'from' address, don't insert 'to' address!
            "value": value,
            "gas": gas,
            "gasPrice": gas_price,
            "nonce": nonce,
            "data": data,
        }
        transaction = self.update_with_gas_estimate(transaction)
        return transaction

    @classmethod
    def is_valid_address(cls, address: Address) -> bool:
        """
        Check if the address is valid.

        :param address: the address to validate
        :return: whether the address is valid
        """
        return Web3.isAddress(address)


class EthereumFaucetApi(FaucetApi):
    """Ethereum testnet faucet API."""

    identifier = _ETHEREUM
    testnet_name = TESTNET_NAME

    def get_wealth(self, address: Address, url: Optional[str] = None) -> None:
        """
        Get wealth from the faucet for the provided address.

        :param address: the address.
        :param url: the url
        """
        self._try_get_wealth(address, url)

    @staticmethod
    @try_decorator(
        "An error occured while attempting to generate wealth:\n{}",
        logger_method="error",
    )
    def _try_get_wealth(address: Address, url: Optional[str] = None) -> None:
        """
        Get wealth from the faucet for the provided address.

        :param address: the address.
        :param url: the url
        """
        if url is None:
            raise ValueError(  # pragma: nocover
                "Url is none, no default url provided. Please provide a faucet url."
            )
        response = requests.get(url + address)
        if response.status_code // 100 == 5:  # pragma: no cover
            _default_logger.error("Response: {}".format(response.status_code))
        elif response.status_code // 100 in [3, 4]:  # pragma: nocover
            response_dict = json.loads(response.text)
            _default_logger.warning(
                "Response: {}\nMessage: {}".format(
                    response.status_code, response_dict.get("message")
                )
            )
        elif response.status_code // 100 == 2:  # pragma: no cover
            response_dict = json.loads(response.text)
            _default_logger.info(
                "Response: {}\nMessage: {}".format(
                    response.status_code, response_dict.get("message")
                )
            )


class LruLockWrapper:
    """Wrapper for LRU with threading.Lock."""

    def __init__(self, lru: LRU) -> None:
        """Init wrapper."""
        self.lru = lru
        self.lock = threading.Lock()

    def __getitem__(self, *args: Any, **kwargs: Any) -> Any:
        """Get item"""
        with self.lock:
            return self.lru.__getitem__(*args, **kwargs)

    def __setitem__(self, *args: Any, **kwargs: Any) -> Any:
        """Set item."""
        with self.lock:
            return self.lru.__setitem__(*args, **kwargs)

    def __contains__(self, *args: Any, **kwargs: Any) -> Any:
        """Contain item."""
        with self.lock:
            return self.lru.__contains__(*args, **kwargs)

    def __delitem__(self, *args: Any, **kwargs: Any) -> Any:
        """Del item."""
        with self.lock:
            return self.lru.__delitem__(*args, **kwargs)


def set_wrapper_for_web3py_session_cache() -> None:
    """Wrap web3py session cache with threading.Lock."""

    # pylint: disable=protected-access
    web3._utils.request._session_cache = LruLockWrapper(
        web3._utils.request._session_cache
    )


set_wrapper_for_web3py_session_cache()
