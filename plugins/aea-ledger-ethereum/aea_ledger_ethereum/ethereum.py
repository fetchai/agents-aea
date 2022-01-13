# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021 Valory AG
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
import decimal
import json
import logging
import math
import threading
import warnings
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union, cast
from uuid import uuid4

import ipfshttpclient  # noqa: F401 # pylint: disable=unused-import
import web3._utils.request
from eth_account import Account
from eth_account._utils.signing import to_standard_signature_bytes
from eth_account.datastructures import HexBytes, SignedTransaction
from eth_account.messages import _hash_eip191_message, encode_defunct
from eth_account.signers.local import LocalAccount
from eth_keys import keys
from eth_typing import HexStr
from eth_utils.currency import from_wei, to_wei  # pylint: disable=import-error
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
EIP1559 = "eip1559"
GAS_STATION = "gas_station"
AVAILABLE_STRATEGIES = (EIP1559, GAS_STATION)

MAX_GAS_FAST = 1500

# How many blocks to consider for priority fee estimation
FEE_HISTORY_BLOCKS = 10

# Which percentile of effective priority fees to include
FEE_HISTORY_PERCENTILE = 5

# Which base fee to trigger priority fee estimation at (GWEI)
PRIORITY_FEE_ESTIMATION_TRIGGER = 100

# Returned if above trigger is not met (GWEI)
DEFAULT_PRIORITY_FEE = 3

# In case something goes wrong fall back to this estimate
FALLBACK_ESTIMATE = {
    "maxFeePerGas": to_wei(20, "gwei"),
    "maxPriorityFeePerGas": to_wei(DEFAULT_PRIORITY_FEE, "gwei"),
    "baseFee": None,
}

PRIORITY_FEE_INCREASE_BOUNDARY = 200  # percentage


DEFAULT_EIP1559_STRATEGY = {
    "max_gas_fast": MAX_GAS_FAST,
    "fee_history_blocks": FEE_HISTORY_BLOCKS,
    "fee_history_percentile": FEE_HISTORY_PERCENTILE,
    "priority_fee_estimation_trigger": PRIORITY_FEE_ESTIMATION_TRIGGER,
    "default_priority_fee": DEFAULT_PRIORITY_FEE,
    "fallback_estimate": FALLBACK_ESTIMATE,
    "priority_fee_increase_boundary": PRIORITY_FEE_INCREASE_BOUNDARY,
}


DEFAULT_GAS_STATION_STRATEGY = {"gas_price_api_key": "", "gas_price_strategy": "fast"}

DEFAULT_GAS_PRICE_STRATEGIES = {
    EIP1559: DEFAULT_EIP1559_STRATEGY,
    GAS_STATION: DEFAULT_GAS_STATION_STRATEGY,
}

# The tip increase is the minimum required of 10%.
TIP_INCREASE = 1.1


def wei_to_gwei(number: Type[int]) -> Union[int, decimal.Decimal]:
    """Covert WEI to GWEI"""
    return from_wei(cast(int, number), unit="gwei")


def round_to_whole_gwei(number: Type[int]) -> Wei:
    """Round WEI to equivalent GWEI"""
    gwei = wei_to_gwei(number)
    rounded = math.ceil(gwei)
    return cast(Wei, to_wei(rounded, "gwei"))


def get_base_fee_multiplier(base_fee_gwei: int) -> float:
    """Returns multiplier value."""

    if base_fee_gwei <= 40:  # pylint: disable=no-else-return
        return 2.0
    elif base_fee_gwei <= 100:  # pylint: disable=no-else-return
        return 1.6
    elif base_fee_gwei <= 200:  # pylint: disable=no-else-return
        return 1.4
    else:  # pylint: disable=no-else-return
        return 1.2


def estimate_priority_fee(
    web3_object: Web3,
    base_fee_gwei: int,
    block_number: int,
    priority_fee_estimation_trigger: int,
    default_priority_fee: int,
    fee_history_blocks: int,
    fee_history_percentile: int,
    priority_fee_increase_boundary: int,
) -> int:
    """Estimate priority fee from base fee."""

    if base_fee_gwei < priority_fee_estimation_trigger:
        return default_priority_fee

    fee_history = web3_object.eth.fee_history(
        fee_history_blocks, block_number, [fee_history_percentile]
    )

    rewards = sorted([reward for reward in fee_history["reward"] if reward > 0])
    if len(rewards) == 0:
        return None

    # Calculate percentage increases from between ordered list of fees
    percentage_increases = [
        ((j - i) / i) * 100 for i, j in zip(rewards[:-1], rewards[1:])
    ]
    highest_increase = max(*percentage_increases)
    highest_increase_index = percentage_increases.index(highest_increase)

    values = rewards.copy()
    # If we have big increase in value, we could be considering "outliers" in our estimate
    # Skip the low elements and take a new median
    if (
        highest_increase > priority_fee_increase_boundary
        and highest_increase_index >= len(values) // 2
    ):
        values = values[highest_increase_index:]

    return values[len(values) // 2]


def get_gas_price_strategy_eip1559(
    max_gas_fast: int,
    fee_history_blocks: int,
    fee_history_percentile: int,
    priority_fee_estimation_trigger: int,
    default_priority_fee: int,
    fallback_estimate: Dict[str, Optional[int]],
    priority_fee_increase_boundary: int,
) -> Callable[[Web3, TxParams], Dict[str, Wei]]:
    """Get the gas price strategy."""

    def eip1559_price_strategy(
        web3: Web3,  # pylint: disable=redefined-outer-name
        transaction_params: TxParams,  # pylint: disable=unused-argument
    ) -> Dict[str, Wei]:
        """
        Get gas price using EIP1559.

        Visit `https://github.com/ethereum/EIPs/blob/master/EIPS/eip-1559.md`
        for more information.

        :param web3: web3 instance
        :param transaction_params: transaction parameters
        :return: dictionary containing gas price strategy
        """

        latest_block = web3.eth.get_block("latest")
        base_fee = latest_block.get("baseFeePerGas")
        block_number = latest_block.get("number")
        base_fee_gwei = wei_to_gwei(base_fee)

        estimated_priority_fee = estimate_priority_fee(
            web3,
            base_fee_gwei,
            block_number,
            priority_fee_estimation_trigger=priority_fee_estimation_trigger,
            default_priority_fee=default_priority_fee,
            fee_history_blocks=fee_history_blocks,
            fee_history_percentile=fee_history_percentile,
            priority_fee_increase_boundary=priority_fee_increase_boundary,
        )

        if estimated_priority_fee is None:
            _default_logger.warning(
                "An error occurred while estimating priority fee, falling back"
            )
            return fallback_estimate

        max_priority_fee_per_gas = max(
            estimated_priority_fee, to_wei(default_priority_fee, "gwei")
        )
        multiplier = get_base_fee_multiplier(base_fee_gwei)

        potential_max_fee = base_fee * multiplier
        max_fee_per_gas = (
            (potential_max_fee + max_priority_fee_per_gas)
            if max_priority_fee_per_gas > potential_max_fee
            else potential_max_fee
        )

        if (
            wei_to_gwei(max_fee_per_gas) >= max_gas_fast
            or wei_to_gwei(max_priority_fee_per_gas) >= max_gas_fast
        ):
            return fallback_estimate

        return {
            "maxFeePerGas": round_to_whole_gwei(max_fee_per_gas),
            "maxPriorityFeePerGas": round_to_whole_gwei(max_priority_fee_per_gas),
        }

    return eip1559_price_strategy


def rpc_gas_price_strategy_wrapper(
    web3: Web3, transaction_params: TxParams  # pylint: disable=redefined-outer-name
) -> Dict[str, Wei]:
    """RPC gas price strategy wrapper."""
    return {"gasPrice": rpc_gas_price_strategy(web3, transaction_params)}


def get_gas_price_strategy(
    gas_price_strategy: Optional[str] = None, gas_price_api_key: Optional[str] = None
) -> Callable[[Web3, TxParams], Dict[str, Wei]]:
    """Get the gas price strategy."""
    supported_gas_price_modes = ["safeLow", "average", "fast", "fastest"]

    if gas_price_strategy is None:
        _default_logger.debug(
            "Gas price strategy not provided. Falling back to `rpc_gas_price_strategy`."
        )
        return rpc_gas_price_strategy_wrapper

    if gas_price_strategy not in supported_gas_price_modes:
        _default_logger.debug(
            f"Gas price strategy `{gas_price_strategy}` not in list of supported modes: {supported_gas_price_modes}. Falling back to `rpc_gas_price_strategy`."
        )
        return rpc_gas_price_strategy_wrapper

    if gas_price_api_key is None:
        _default_logger.debug(
            "No ethgasstation api key provided. Falling back to `rpc_gas_price_strategy`."
        )
        return rpc_gas_price_strategy_wrapper

    def gas_station_gas_price_strategy(
        web3: Web3,  # pylint: disable=redefined-outer-name
        transaction_params: TxParams,  # pylint: disable=unused-argument
    ) -> Dict[str, Wei]:
        """
        Get gas price from Eth Gas Station api.

        Visit `https://docs.ethgasstation.info/gas-price` for documentation.
        :param web3: web3 instance
        :param transaction_params: transaction parameters
        :return: wei
        """
        response = requests.get(f"{ETH_GASSTATION_URL}?api-key={gas_price_api_key}")
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
        return {"gasPrice": wei_result}

    return gas_station_gas_price_strategy


class SignedTransactionTranslator:
    """Translator for SignedTransaction."""

    @staticmethod
    def to_dict(signed_transaction: SignedTransaction) -> Dict[str, Union[str, int]]:
        """Write SignedTransaction to dict."""
        signed_transaction_dict: Dict[str, Union[str, int]] = {
            "raw_transaction": cast(str, signed_transaction.rawTransaction.hex()),
            "hash": cast(str, signed_transaction.hash.hex()),
            "r": cast(int, signed_transaction.r),
            "s": cast(int, signed_transaction.s),
            "v": cast(int, signed_transaction.v),
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
            rawTransaction=HexBytes(
                cast(str, signed_transaction_dict["raw_transaction"])
            ),
            hash=HexBytes(cast(str, signed_transaction_dict["hash"])),
            r=cast(int, signed_transaction_dict["r"]),
            s=cast(int, signed_transaction_dict["s"]),
            v=cast(int, signed_transaction_dict["v"]),
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


class EthereumCrypto(Crypto[LocalAccount]):
    """Class wrapping the Account Generation from Ethereum ledger."""

    identifier = _ETHEREUM

    def __init__(
        self,
        private_key_path: Optional[str] = None,
        password: Optional[str] = None,
        extra_entropy: Union[str, bytes, int] = "",
    ) -> None:
        """
        Instantiate an ethereum crypto object.

        :param private_key_path: the private key path of the agent
        :param password: the password to encrypt/decrypt the private key.
        :param extra_entropy: add extra randomness to whatever randomness your OS can provide
        """
        super().__init__(
            private_key_path=private_key_path,
            password=password,
            extra_entropy=extra_entropy,
        )

        bytes_representation = Web3.toBytes(hexstr=self.entity.key.hex())
        self._public_key = str(keys.PrivateKey(bytes_representation).public_key)
        self._address = self.entity.address

    @property
    def private_key(self) -> str:
        """
        Return a private key.

        64 random hex characters (i.e. 32 bytes) + "0x" prefix.

        :return: a private key string in hex format
        """
        return self.entity.key.hex()

    @property
    def public_key(self) -> str:
        """
        Return a public key in hex format.

        128 hex characters (i.e. 64 bytes) + "0x" prefix.

        :return: a public key string in hex format
        """
        return self._public_key

    @property
    def address(self) -> str:
        """
        Return the address for the key pair.

        40 hex characters (i.e. 20 bytes) + "0x" prefix.

        :return: an address string in hex format
        """
        return self._address

    @classmethod
    def load_private_key_from_path(
        cls, file_name: str, password: Optional[str] = None
    ) -> LocalAccount:
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
        signed_transaction = cast(Account, self.entity).sign_transaction(
            transaction_dict=transaction
        )
        signed_transaction_dict = SignedTransactionTranslator.to_dict(
            signed_transaction
        )
        return cast(JSONLike, signed_transaction_dict)

    @classmethod
    def generate_private_key(
        cls, extra_entropy: Union[str, bytes, int] = ""
    ) -> LocalAccount:
        """
        Generate a key pair for ethereum network.

        :param extra_entropy: add extra randomness to whatever randomness your OS can provide
        :return: account object
        """
        account = Account.create(
            extra_entropy
        )  # pylint: disable=no-value-for-parameter
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
        :return: the raw private key (without leading "0x").
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
        aggregate_hash = Web3.keccak(
            b"".join([seller.encode(), client.encode(), uuid4().bytes])
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
        raw_address = keccak_hash[-20:].hex()
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
        :return: the hash of the message as a hex string.
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

    _gas_price_strategy_callables: Dict[str, Callable] = {
        GAS_STATION: get_gas_price_strategy,
        EIP1559: get_gas_price_strategy_eip1559,
    }

    def __init__(self, **kwargs: Any):
        """
        Initialize the Ethereum ledger APIs.

        :param kwargs: keyword arguments
        """
        self._api = Web3(
            HTTPProvider(endpoint_uri=kwargs.pop("address", DEFAULT_ADDRESS))
        )
        self._chain_id = kwargs.pop("chain_id", DEFAULT_CHAIN_ID)
        self._is_gas_estimation_enabled = kwargs.pop("is_gas_estimation_enabled", False)

        self._default_gas_price_strategy: str = kwargs.pop(
            "default_gas_price_strategy", EIP1559
        )
        if self._default_gas_price_strategy not in AVAILABLE_STRATEGIES:
            raise ValueError(
                f"Gas price strategy must be one of {AVAILABLE_STRATEGIES}, provided: {self._default_gas_price_strategy}"
            )  # pragma: nocover

        self._gas_price_strategies: Dict[str, Dict] = kwargs.pop(
            "gas_price_strategies", DEFAULT_GAS_PRICE_STRATEGIES
        )

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
        return self._api.eth.get_balance(check_address)  # pylint: disable=no-member

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
        max_fee_per_gas: Optional[int] = None,
        max_priority_fee_per_gas: Optional[str] = None,
        gas_price: Optional[str] = None,
        gas_price_strategy: Optional[str] = None,
        gas_price_strategy_extra_config: Optional[Dict] = None,
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
        :param max_fee_per_gas: maximum amount you’re willing to pay, inclusive of `baseFeePerGas` and `maxPriorityFeePerGas`. The difference between `maxFeePerGas` and `baseFeePerGas + maxPriorityFeePerGas` is refunded  (in Wei).
        :param max_priority_fee_per_gas: the part of the fee that goes to the miner (in Wei).
        :param gas_price: the gas price (in Wei)
        :param gas_price_strategy: the gas price strategy to be used.
        :param gas_price_strategy_extra_config: extra config for gas price strategy.
        :param kwargs: keyword arguments
        :return: the transfer transaction
        """
        transaction: Optional[JSONLike] = None
        chain_id = chain_id if chain_id is not None else self._chain_id
        destination_address = self._api.toChecksumAddress(destination_address)
        sender_address = self._api.toChecksumAddress(sender_address)
        nonce = self._try_get_transaction_count(sender_address)
        if nonce is None:
            return transaction
        transaction = {
            "nonce": nonce,
            "chainId": chain_id,
            "to": destination_address,
            "value": amount,
            "gas": tx_fee,
            "data": tx_nonce,
        }
        if self._is_gas_estimation_enabled:
            transaction = self.update_with_gas_estimate(transaction)

        if max_fee_per_gas is not None:
            max_priority_fee_per_gas = (
                self._try_get_max_priority_fee()
                if max_priority_fee_per_gas is None
                else max_priority_fee_per_gas
            )
            transaction.update(
                {
                    "maxFeePerGas": max_fee_per_gas,
                    "maxPriorityFeePerGas": max_priority_fee_per_gas,
                }
            )

        if gas_price is not None:
            transaction.update({"gasPrice": gas_price})

        if gas_price is None and max_fee_per_gas is None:
            gas_pricing = self.try_get_gas_pricing(
                gas_price_strategy, gas_price_strategy_extra_config
            )
            if gas_pricing is None:
                return transaction  # pragma: nocover
            transaction.update(gas_pricing)

        return transaction

    def _get_gas_price_strategy_callable(
        self,
        gas_price_strategy: Optional[str] = None,
        extra_config: Optional[Dict] = None,
    ) -> Callable:
        """
        Returns parameters for gas price callable.

        Note: The priority of gas price callable will be
        `extra_config(Runtime params) > self._gas_price_strategies (Set using config file.) > DEFAULT_GAS_PRICE_STRATEGIES (Default values.)`

        :param gas_price_strategy: name of the gas price strategy.
        :param extra_config: gas price strategy getter parameters.
        :return: gas price callable.
        """
        gas_price_strategy = (
            gas_price_strategy
            if gas_price_strategy is not None
            else self._default_gas_price_strategy
        )
        if gas_price_strategy not in AVAILABLE_STRATEGIES:  # pragma: nocover
            _default_logger.debug(
                f"Gas price strategy must be one of {AVAILABLE_STRATEGIES}, provided: {self._default_gas_price_strategy}"
            )
            return None

        _default_logger.debug(f"Using strategy: {gas_price_strategy}")
        gas_price_strategy_getter = self._gas_price_strategy_callables.get(
            gas_price_strategy, None
        )

        parameters = DEFAULT_GAS_PRICE_STRATEGIES.get(gas_price_strategy)
        parameters.update(self._gas_price_strategies.get(gas_price_strategy, {}))
        parameters.update(extra_config or {})
        return gas_price_strategy_getter(**parameters)

    @try_decorator("Unable to retrieve gas price: {}", logger_method="warning")
    def try_get_gas_pricing(
        self,
        gas_price_strategy: Optional[str] = None,
        extra_config: Optional[Dict] = None,
        old_tip: Optional[int] = None,
    ) -> Optional[Dict[str, int]]:
        """
        Try get the gas price based on the provided strategy.

        :param gas_price_strategy: the gas price strategy to use, e.g., the EIP-1559 strategy.
            Can be either `eip1559` or `gas_station`.
        :param extra_config: gas price strategy getter parameters.
        :param old_tip: the old `maxPriorityFeePerGas` in case that we are trying to resubmit a transaction.
        :return: a dictionary with the gas data.
        """

        gas_price_strategy_callable = self._get_gas_price_strategy_callable(
            gas_price_strategy, extra_config,
        )
        if gas_price_strategy_callable is None:  # pragma: nocover
            return None

        prior_strategy = self._api.eth.gasPriceStrategy
        try:
            self._api.eth.set_gas_price_strategy(gas_price_strategy_callable)
            gas_price = self._api.eth.generate_gas_price()
        finally:
            self._api.eth.set_gas_price_strategy(prior_strategy)  # pragma: nocover

        if old_tip is not None and gas_price_strategy is EIP1559:
            base_fee_per_gas = (
                gas_price["maxFeePerGas"] - gas_price["maxPriorityFeePerGas"]
            )
            updated_max_priority_fee_per_gas = old_tip * TIP_INCREASE
            updated_max_fee_per_gas = (
                updated_max_priority_fee_per_gas + base_fee_per_gas
            )

            if gas_price["maxPriorityFeePerGas"] < updated_max_priority_fee_per_gas:
                gas_price["maxPriorityFeePerGas"] = updated_max_priority_fee_per_gas
                gas_price["maxFeePerGas"] = updated_max_fee_per_gas

        elif old_tip is not None and gas_price_strategy is GAS_STATION:
            updated_gas_price = old_tip * TIP_INCREASE
            gas_price["gasPrice"] = max(gas_price["gasPrice"], updated_gas_price)

        return gas_price

    @try_decorator("Unable to retrieve transaction count: {}", logger_method="warning")
    def _try_get_transaction_count(self, address: Address) -> Optional[int]:
        """Try get the transaction count."""
        nonce = self._api.eth.get_transaction_count(  # pylint: disable=no-member
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
            transaction["gas"] = gas_estimate
        return transaction

    @try_decorator("Unable to retrieve gas estimate: {}", logger_method="warning")
    def _try_get_gas_estimate(self, transaction: JSONLike) -> Optional[int]:
        """Try get the gas estimate."""
        gas_estimate = self._api.eth.estimate_gas(  # pylint: disable=no-member
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
        hex_value = self._api.eth.send_raw_transaction(  # pylint: disable=no-member
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
        tx_receipt = self._api.eth.get_transaction_receipt(  # pylint: disable=no-member
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
        tx = self._api.eth.get_transaction(
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
        gas: Optional[int] = None,
        max_fee_per_gas: Optional[int] = None,
        max_priority_fee_per_gas: Optional[str] = None,
        gas_price: Optional[str] = None,
        gas_price_strategy: Optional[str] = None,
        gas_price_strategy_extra_config: Optional[Dict] = None,
        **kwargs: Any,
    ) -> Optional[JSONLike]:
        """
        Get the transaction to deploy the smart contract.

        :param contract_interface: the contract interface.
        :param deployer_address: The address that will deploy the contract.
        :param value: value to send to contract (in Wei)
        :param gas: the gas to be used (in Wei)
        :param max_fee_per_gas: maximum amount you’re willing to pay, inclusive of `baseFeePerGas` and `maxPriorityFeePerGas`. The difference between `maxFeePerGas` and `baseFeePerGas + maxPriorityFeePerGas` is refunded  (in Wei).
        :param max_priority_fee_per_gas: the part of the fee that goes to the miner (in Wei).
        :param gas_price: the gas price (in Wei)
        :param gas_price_strategy: the gas price strategy to be used.
        :param gas_price_strategy_extra_config: extra config for gas price strategy..
        :param kwargs: keyword arguments
        :return: the transaction dictionary.
        """
        transaction: Optional[JSONLike] = None
        _deployer_address = self.api.toChecksumAddress(deployer_address)
        nonce = self._try_get_transaction_count(_deployer_address)
        if nonce is None:
            return transaction
        instance = self.get_contract_instance(contract_interface)
        transaction = {
            "value": value,
            "nonce": nonce,
        }
        if max_fee_per_gas is not None:
            max_priority_fee_per_gas = (
                self._try_get_max_priority_fee()
                if max_priority_fee_per_gas is None
                else max_priority_fee_per_gas
            )
            if max_priority_fee_per_gas is None:
                return None  # pragma: nocover
            transaction.update(
                {
                    "maxFeePerGas": max_fee_per_gas,
                    "maxPriorityFeePerGas": max_priority_fee_per_gas,
                }
            )

        if gas_price is not None:
            transaction.update({"gasPrice": gas_price})

        if gas_price is None and max_fee_per_gas is None:
            gas_pricing = self.try_get_gas_pricing(
                gas_price_strategy, gas_price_strategy_extra_config
            )

            if gas_pricing is None:
                return None  # pragma: nocover

            transaction.update(gas_pricing)

        transaction = instance.constructor(**kwargs).buildTransaction(transaction)

        if transaction is None:
            return None  # pragma: nocover
        transaction.pop("to", None)  # only 'from' address, don't insert 'to' address!
        transaction.update({"from": _deployer_address})
        if gas is not None:
            transaction.update({"gas": gas})
        if self._is_gas_estimation_enabled:
            transaction = self.update_with_gas_estimate(transaction)
        return transaction

    @try_decorator("Unable to retrieve max_priority_fee: {}", logger_method="warning")
    def _try_get_max_priority_fee(self) -> str:
        """Try get the gas estimate."""
        return cast(str, self.api.eth.max_priority_fee)

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
