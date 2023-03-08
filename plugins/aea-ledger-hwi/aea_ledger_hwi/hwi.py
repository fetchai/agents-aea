# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2023 Valory AG
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

import logging
import warnings
from typing import Any, Callable, Dict, List, Optional, Union, cast

from aea_ledger_ethereum.ethereum import (
    EthereumApi,
    EthereumFaucetApi,
    EthereumHelper,
    TESTNET_NAME,
    set_wrapper_for_web3py_session_cache,
)
from aea_ledger_hwi.account import HWIAccount
from eth_account.datastructures import HexBytes, SignedTransaction
from eth_account.messages import encode_defunct
from eth_account.signers.local import LocalAccount
from web3.datastructures import AttributeDict
from web3.types import TxData, TxReceipt

from aea.common import JSONLike
from aea.crypto.base import Crypto


_default_logger = logging.getLogger(__name__)

_ETHEREUM_HWI = "ethereum_hwi"
DEFAULT_DEVICE_INDEX = 0
DEFAULT_KEYPAIR_INDEX = 0


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


class EthereumHWICrypto(Crypto[HWIAccount]):
    """Class wrapping the Account Generation from Ethereum ledger."""

    identifier = _ETHEREUM_HWI

    def __init__(
        self,
        private_key_path: Optional[str] = None,
        password: Optional[str] = None,
        extra_entropy: Union[str, bytes, int] = "",
        **kwargs: Any,
    ) -> None:
        """
        Instantiate an ethereum crypto object.

        :param private_key_path: the private key path of the agent
        :param password: the password to encrypt/decrypt the private key.
        :param extra_entropy: add extra randomness to whatever randomness your OS can provide
        :param kwargs: extra keyword arguments
        """
        self._device_index = kwargs.pop(
            "default_device_index",
            DEFAULT_DEVICE_INDEX,
        )
        self._keypair_index = kwargs.pop(
            "default_keypair_index",
            DEFAULT_KEYPAIR_INDEX,
        )
        account = HWIAccount(
            default_device=self._device_index,
            default_key_index=self._keypair_index,
        )
        super().__init__(
            private_key_path=private_key_path,
            password=password,
            extra_entropy=extra_entropy,
            entity=account,
        )

    @property
    def private_key(self) -> str:
        """
        Return a private key.

        64 random hex characters (i.e. 32 bytes) + "0x" prefix.
        """

        raise NotImplementedError()

    @property
    def public_key(self) -> str:
        """
        Return a public key in hex format.

        128 hex characters (i.e. 64 bytes) + "0x" prefix.

        :return: a public key string in hex format
        """
        return self.entity.public_key

    @property
    def address(self) -> str:
        """
        Return the address for the key pair.

        40 hex characters (i.e. 20 bytes) + "0x" prefix.

        :return: an address string in hex format
        """
        return self.entity.address

    @classmethod
    def load_private_key_from_path(
        cls, file_name: str, password: Optional[str] = None
    ) -> LocalAccount:
        """
        Load a private key in hex format from a file.

        :param file_name: the path to the hex file.
        :param password: the password to encrypt/decrypt the private key.
        """

        raise NotImplementedError()

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
                signature_dict = cast(HWIAccount, self.entity).signHash(message)
            signed_msg = signature_dict["signature"].hex()
        else:
            signable_message = encode_defunct(primitive=message)
            signature = cast(HWIAccount, self.entity).sign_message(
                signable_message=signable_message
            )
            signed_msg = signature["signature"].hex()
        return signed_msg

    def sign_transaction(self, transaction: JSONLike, **kwargs: Any) -> JSONLike:
        """
        Sign a transaction in bytes string form.

        :param transaction: the transaction to be signed
        :param kwargs: extra keyword arguments
        :return: signed transaction
        """
        signed_transaction = cast(HWIAccount, self.entity).sign_transaction(
            transaction_dict=transaction, **kwargs
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
        """

        raise NotImplementedError()

    def encrypt(self, password: str) -> str:
        """
        Encrypt the private key and return in json.

        :param password: the password to decrypt.
        """

        raise NotImplementedError()

    @classmethod
    def decrypt(cls, keyfile_json: str, password: str) -> str:
        """
        Decrypt the private key and return in raw form.

        :param keyfile_json: json str containing encrypted private key.
        :param password: the password to decrypt.
        """

        raise NotImplementedError()


class EthereumHWIHelper(EthereumHelper):
    """Helper class usable as Mixin for EthereumApi or as standalone class."""


class EthereumHWIApi(EthereumApi, EthereumHWIHelper):
    """Class to interact with the Ethereum Web3 APIs."""

    identifier = _ETHEREUM_HWI

    def __init__(self, **kwargs: Any):
        """Initialize object."""
        super().__init__(**kwargs)


class EthereumHWIFaucetApi(EthereumFaucetApi):
    """Ethereum testnet faucet API."""

    identifier = _ETHEREUM_HWI
    testnet_name = TESTNET_NAME


set_wrapper_for_web3py_session_cache()
