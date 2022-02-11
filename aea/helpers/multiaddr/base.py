# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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

"""This module contains multiaddress class."""

from binascii import unhexlify
from typing import Optional

import base58
import multihash  # type: ignore
from ecdsa import VerifyingKey, curves, keys

from aea.helpers.multiaddr.crypto_pb2 import KeyType, PublicKey


# NOTE:
# - Reference: https://github.com/libp2p/specs/blob/master/peer-ids/peer-ids.md#keys
# - Implementation inspired from https://github.com/libp2p/py-libp2p
# - On inlining see: https://github.com/libp2p/specs/issues/138
# - Enabling inlining to be interoperable w/ the Go implementation

ENABLE_INLINING = True
MAX_INLINE_KEY_LENGTH = 42
IDENTITY_MULTIHASH_CODE = 0x00

KEY_SIZE = 32
ZERO = b"\x00"

if ENABLE_INLINING:

    class IdentityHash:
        """Neutral hashing implementation for inline multihashing."""

        _digest: bytes

        def __init__(self) -> None:
            """Initialize IdentityHash object."""
            self._digest = bytearray()

        def update(self, input_data: bytes) -> None:
            """
            Update data to hash.

            :param input_data: the data
            """
            self._digest += input_data

        def digest(self) -> bytes:
            """
            Get hash of input data.

            :return: the hash
            """
            return self._digest

    multihash.FuncReg.register(
        IDENTITY_MULTIHASH_CODE, "identity", hash_new=IdentityHash
    )


def _pad_scalar(scalar: bytes) -> bytes:
    """Pad scalar."""
    return (ZERO * (KEY_SIZE - len(scalar))) + scalar


def _pad_hex(hexed: str) -> str:
    """Pad odd-length hex strings."""
    return hexed if not len(hexed) & 1 else "0" + hexed


def _hex_to_bytes(hexed: str) -> bytes:
    """Hex to bytes."""
    return _pad_scalar(unhexlify(_pad_hex(hexed)))


class MultiAddr:
    """Protocol Labs' Multiaddress representation of a network address."""

    def __init__(
        self,
        host: str,
        port: int,
        public_key: Optional[str] = None,
        multihash_id: Optional[str] = None,
    ) -> None:
        """
        Initialize a multiaddress.

        :param host: ip host of the address
        :param port: port number of the address
        :param public_key: hex encoded public key. Must conform to Bitcoin EC encoding standard for Secp256k1
        :param multihash_id: a multihash of the public key
        """

        self._host = host
        self._port = port

        if public_key is not None:
            try:
                VerifyingKey._from_compressed(
                    _hex_to_bytes(public_key), curves.SECP256k1
                )
            except keys.MalformedPointError as e:  # pragma: no cover
                raise ValueError(
                    "Malformed public key '{}': {}".format(public_key, str(e))
                )

            self._public_key = public_key
            self._peerid = self.compute_peerid(self._public_key)
        elif multihash_id is not None:
            try:
                multihash.decode(base58.b58decode(multihash_id))
            except Exception as e:  # pylint: disable=broad-except
                raise ValueError(
                    "Malformed multihash '{}': {}".format(multihash_id, str(e))
                )

            self._public_key = ""
            self._peerid = multihash_id
        else:
            raise ValueError(  # pragma: no cover
                "MultiAddr requires either public_key or multihash_id to be provided."
            )

    @staticmethod
    def compute_peerid(public_key: str) -> str:
        """
        Compute the peer id from a public key.

        In particular, compute the base58 representation of
        libp2p PeerID from Bitcoin EC encoded Secp256k1 public key.

        :param public_key: the public key.
        :return: the peer id.
        """
        key_protobuf = PublicKey(
            key_type=KeyType.Secp256k1, data=_hex_to_bytes(public_key)  # type: ignore
        )
        key_serialized = key_protobuf.SerializeToString()
        algo = multihash.Func.sha2_256
        if ENABLE_INLINING and len(key_serialized) <= MAX_INLINE_KEY_LENGTH:
            algo = IDENTITY_MULTIHASH_CODE
        key_mh = multihash.digest(key_serialized, algo)
        return base58.b58encode(key_mh.encode()).decode()

    @classmethod
    def from_string(cls, maddr: str) -> "MultiAddr":
        """
        Construct a MultiAddr object from its string format

        :param maddr: multiaddress string
        :return: multiaddress object
        """
        parts = maddr.split("/")
        if len(parts) != 7 or not parts[4].isdigit():
            raise ValueError("Malformed multiaddress '{}'".format(maddr))

        return cls(host=parts[2], port=int(parts[4]), multihash_id=parts[6])

    @property
    def public_key(self) -> str:
        """Get the public key."""
        return self._public_key

    @property
    def peer_id(self) -> str:
        """Get the peer id."""
        return self._peerid

    @property
    def host(self) -> str:
        """Get the peer host."""
        return self._host

    @property
    def port(self) -> int:
        """Get the peer port."""
        return self._port

    def format(self) -> str:
        """Canonical representation of a multiaddress."""
        return f"/dns4/{self._host}/tcp/{self._port}/p2p/{self._peerid}"

    def __str__(self) -> str:
        """Default string representation of a multiaddress."""
        return self.format()
