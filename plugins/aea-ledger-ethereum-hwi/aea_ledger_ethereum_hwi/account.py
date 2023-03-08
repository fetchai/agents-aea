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

"""Custom implementation of `eth_account.Account` for hardware wallets."""

from contextlib import contextmanager
from typing import Any, Generator, List, NamedTuple, Optional

import rlp
from aea_ledger_ethereum_hwi.exceptions import HWIError
from apduboy.lib.bip32 import h, m
from apduboy.utils import chunk
from construct import (
    Byte,
    Bytes,
    BytesInteger,
    GreedyBytes,
    Int8ub,
    Int32ub,
    PascalString,
    Prefixed,
    PrefixedArray,
    Struct,
)
from cytoolz import dissoc
from eth_account._utils.legacy_transactions import (
    UnsignedTransaction,
    encode_transaction,
    serializable_unsigned_transaction_from_dict,
)
from eth_account._utils.typed_transactions import TypedTransaction
from eth_account.datastructures import HexBytes, SignedMessage, SignedTransaction
from eth_account.messages import SignableMessage
from eth_keys.main import PublicKey
from eth_rlp import HashableRLP
from eth_typing.evm import ChecksumAddress
from eth_utils.curried import keccak
from ledgerwallet.client import CommException, LedgerClient
from ledgerwallet.transport import enumerate_devices
from ledgerwallet.transport.device import Device

from aea.common import JSONLike


address = rlp.sedes.Binary.fixed_length(20, allow_empty=True)
access_list_sede_type = rlp.sedes.CountableList(
    rlp.sedes.List(
        [
            address,
            rlp.sedes.CountableList(rlp.sedes.BigEndianInt(32)),
        ]
    ),
)


class HWIAccountData(NamedTuple):
    """Hardware wallet account data"""

    public_key: str
    address: str
    chain_code: Optional[bytes]


class HWISignedTransaction(NamedTuple):
    """Hardware wallet signed transaction"""

    v: int
    r: int
    s: int


class UnsignedDynamicTransaction(HashableRLP):
    """Unsigned dynamic transaction."""

    fields = [
        ("chain_id", rlp.sedes.big_endian_int),
        ("nonce", rlp.sedes.big_endian_int),
        ("max_priority_fee_per_gas", rlp.sedes.big_endian_int),
        ("max_fee_per_gas", rlp.sedes.big_endian_int),
        ("gas_limit", rlp.sedes.big_endian_int),
        ("destination", address),
        ("amount", rlp.sedes.big_endian_int),
        ("data", rlp.sedes.binary),
        ("access_list", access_list_sede_type),
    ]


class SignTransactionAPDU:
    """Sign transaction APDU codes"""

    INS = 0x04
    P1_0 = 0x00
    P1 = 0x80
    P2 = 0x00


class GetAccountAPDU:
    """Get account APDU codes"""

    INS = 0x02
    P1 = 0x01
    P2 = 0x01


SignedTransactionStruct = Struct(
    v=BytesInteger(1),
    r=BytesInteger(32),
    s=BytesInteger(32),
)


AccountStruct = Struct(
    public_key=Prefixed(Int8ub, GreedyBytes),
    address=PascalString(Int8ub, "ascii"),
    chain_code=Bytes(32),
)


class HWIErrorCodes:
    """HWI com errors."""

    DEVICE_LOCKED = 21781
    EHTEREUM_APP_NOT_OPEN = 25870


@contextmanager
def reraise_from_hwi_com_error() -> Generator:
    """Reraise ledger communication exception as `HWIError`"""

    try:
        yield
    except CommException as e:
        if e.sw == HWIErrorCodes.DEVICE_LOCKED:
            raise HWIError(message="Device is locked", sw=e.sw)
        elif e.sw == HWIErrorCodes.EHTEREUM_APP_NOT_OPEN:
            raise HWIError(message="Please open ethereum app in your device", sw=e.sw)
        else:
            raise HWIError(message=e.message, sw=e.sw, data=e.data)


class HWIAccount:
    """Hardware wallet interface as ethereum account similar to `eth_account.Account` to represent `Crypto.entity`"""

    default_account: Optional[HWIAccountData]

    def __init__(
        self,
        default_device: int = 0,
        default_key_index: int = 0,
    ) -> None:
        """Initialize object."""

        self.default_device = default_device
        self.default_key_index = default_key_index
        self.default_account = None

    @property
    def devices(self) -> List[Device]:
        """Returns the list of available devices."""
        devices = enumerate_devices()
        if len(devices) == 0:
            raise HWIError(message="Cannot find any ledger device", sw=0)
        return devices

    def get_client(
        self,
        device_index: Optional[int] = None,
    ) -> LedgerClient:
        """Get ledger client."""
        device_index = device_index or self.default_device
        return LedgerClient(device=self.devices[device_index])

    def get_account(
        self,
        key_index: Optional[int] = None,
        device_index: Optional[int] = None,
    ) -> HWIAccountData:
        """Get hardware wallet account."""

        key_index = key_index or self.default_key_index
        path = m / h(44) / h(60) / h(key_index) / 0 / 0

        path_construct = PrefixedArray(Byte, Int32ub)
        path_apdu = path_construct.build(path.to_list())
        client = self.get_client(device_index=device_index)

        with reraise_from_hwi_com_error():
            response = client.apdu_exchange(
                ins=GetAccountAPDU.INS,
                data=path_apdu,
                p1=GetAccountAPDU.P1,
                p2=GetAccountAPDU.P2,
            )

        parsed_response = AccountStruct.parse(response)
        pbk = PublicKey(parsed_response.public_key[1:])

        return HWIAccountData(
            public_key=str(pbk),
            address=pbk.to_address(),
            chain_code=parsed_response.chain_code,
        )

    @property
    def address(self) -> ChecksumAddress:
        """Address"""
        if self.default_account is None:
            self.default_account = self.get_account()
        return self.default_account.address

    @property
    def public_key(self) -> ChecksumAddress:
        """Public key"""
        if self.default_account is None:
            self.default_account = self.get_account()
        return self.default_account.public_key

    def sign_message(
        self, signable_message: SignableMessage, **kwargs: Any
    ) -> SignedMessage:
        """Sign a EIP191 message"""

        raise NotImplementedError()

    @staticmethod
    def encode_transaction(
        transaction: TypedTransaction,
        is_eip1559_tx: bool = False,
        key_index: Optional[int] = None,
    ) -> bytes:
        """Build and encode transaction"""

        # BIP32 Path m/44'/cointype'/account'/change/address
        path = m / h(44) / h(60) / h(key_index or 0) / 0 / 0
        path_construct = PrefixedArray(Byte, Int32ub)
        path_apdu = path_construct.build(path.to_list())

        if is_eip1559_tx:
            as_dict = transaction.as_dict()
            tx = UnsignedDynamicTransaction.from_dict(
                field_dict=dict(
                    chain_id=as_dict["chainId"],
                    nonce=as_dict["nonce"],
                    max_priority_fee_per_gas=as_dict["maxPriorityFeePerGas"],
                    max_fee_per_gas=as_dict["maxFeePerGas"],
                    gas_limit=as_dict.get("gas", 21000),
                    destination=as_dict["to"],
                    amount=as_dict["value"],
                    data=as_dict["data"],
                    access_list=as_dict.get("accessList", []),
                )
            )
            return (
                path_apdu
                + transaction.transaction_type.to_bytes(1, "big")
                + rlp.encode(tx)
            )

        as_dict = transaction.as_dict()
        tx = UnsignedTransaction.from_dict(
            field_dict=dict(
                nonce=as_dict["nonce"],
                gasPrice=as_dict["gasPrice"],
                gas=as_dict["gas"],
                to=as_dict["to"],
                value=as_dict["value"],
                data=as_dict["data"],
            )
        )
        return path_apdu + rlp.encode(tx)

    def _sign_transaction_on_hwi(
        self,
        unsigned_transaction: TypedTransaction,
        key_index: Optional[int] = None,
        device_index: Optional[int] = None,
        chain_id: int = 1,
    ) -> HWISignedTransaction:
        """Hardware wallet signed transaction"""

        client = self.get_client(
            device_index=device_index,
        )

        is_eip1559_tx = (
            hasattr(unsigned_transaction, "transaction_type")
            and unsigned_transaction.transaction_type == 2
        )

        request_data = self.encode_transaction(
            transaction=unsigned_transaction,
            is_eip1559_tx=is_eip1559_tx,
            key_index=key_index,
        )

        with reraise_from_hwi_com_error():
            raw_response = bytes()
            for idx, each in enumerate(chunk(request_data, 255)):
                raw_response = client.apdu_exchange(
                    ins=SignTransactionAPDU.INS,
                    data=each,
                    p1=(
                        SignTransactionAPDU.P1_0 if idx == 0 else SignTransactionAPDU.P1
                    ),
                    p2=SignTransactionAPDU.P2,
                )

        parsed_response = SignedTransactionStruct.parse(raw_response)

        if is_eip1559_tx:
            return HWISignedTransaction(
                v=parsed_response.v,
                r=parsed_response.r,
                s=parsed_response.s,
            )

        return HWISignedTransaction(
            v=(35 + (2 * chain_id)),
            r=parsed_response.r,
            s=parsed_response.s,
        )

    def sign_transaction(
        self,
        transaction_dict: JSONLike,
        **kwargs: Any,
    ) -> SignedTransaction:
        """Sign transaction."""

        key_index: Optional[int] = kwargs.get("key_index")
        device_index: Optional[int] = kwargs.get("device_index")
        account = self.get_account(key_index=key_index, device_index=device_index)
        chain_id = transaction_dict.get(
            "chainId",
            transaction_dict.get(
                "chain_id",
                1,
            ),
        )

        if "from" in transaction_dict:
            if transaction_dict["from"].lower() == account.address.lower():
                sanitized_transaction = dissoc(transaction_dict, "from")
            else:
                raise TypeError(
                    "from field must match key's %s, but it was %s"
                    % (
                        account.address,
                        transaction_dict["from"],
                    )
                )
        else:
            sanitized_transaction = transaction_dict

        to_address = sanitized_transaction["to"]
        if isinstance(to_address, str):
            sanitized_transaction["to"] = bytes.fromhex(to_address[2:])

        if isinstance(to_address, bytes) and to_address.startswith(b"0x"):
            sanitized_transaction["to"] = to_address[2:]

        # encode transaction
        unsigned_transaction = serializable_unsigned_transaction_from_dict(
            sanitized_transaction
        )
        transaction_hash = unsigned_transaction.hash()

        response = self._sign_transaction_on_hwi(
            unsigned_transaction=unsigned_transaction,
            device_index=device_index,
            key_index=key_index,
            chain_id=chain_id,
        )

        # serialize transaction with rlp
        encoded_transaction = encode_transaction(
            unsigned_transaction,
            vrs=(
                response.v,
                response.r,
                response.s,
            ),
        )
        transaction_hash = keccak(encoded_transaction)

        return SignedTransaction(
            rawTransaction=HexBytes(encoded_transaction),
            hash=HexBytes(transaction_hash),
            r=response.r,
            s=response.s,
            v=response.v,
        )
