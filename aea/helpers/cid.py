# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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

"""
Utils to support multiple CID versions.

Original implementation: https://github.com/ipld/py-cid/
"""

from typing import Union, cast

import base58
import multibase
import multicodec
import multihash as mh
from morphys import ensure_bytes, ensure_unicode


DEFAULT_ENCODING = "base32"
BTC_ENCODING = "base58btc"


class BaseCID:
    """Base CID object."""

    _version: int
    _codec: str
    _multihash: bytes

    def __init__(self, version: int, codec: str, multihash: bytes):
        """Creates a new CID object."""

        self._version = version
        self._codec = codec
        self._multihash = ensure_bytes(multihash)

    @property
    def version(self) -> int:
        """CID version"""
        return self._version

    @property
    def codec(self) -> str:
        """CID codec"""
        return self._codec

    @property
    def multihash(self) -> bytes:
        """CID multihash"""
        return self._multihash

    @property
    def buffer(self) -> bytes:
        """Multihash buffer."""
        raise NotImplementedError

    def encode(self, encoding: str = DEFAULT_ENCODING) -> bytes:
        """Encode multihash."""
        raise NotImplementedError

    def __repr__(self) -> str:
        """Object representation."""

        def truncate(s: bytes, length: int) -> bytes:
            return s[:length] + b".." if len(s) > length else s

        truncate_length = 20
        multihash = (truncate(self._multihash, truncate_length),)

        return f"<version={self._version}, codec={self._codec}, multihash={multihash}>"

    def __str__(self) -> str:
        """String representation."""

        return ensure_unicode(self.encode())

    def __eq__(self, other: object) -> bool:
        """Dunder to check object equivalence."""

        if not isinstance(other, BaseCID):
            return NotImplemented

        return self.__dict__ == other.__dict__


class CIDv0(BaseCID):
    """CID version 0 object"""

    CODEC: str = "dag-pb"

    def __init__(self, multihash: bytes) -> None:
        """Initialize object."""

        super().__init__(0, self.CODEC, multihash)

    @property
    def buffer(self) -> bytes:
        """The raw representation that will be encoded."""

        return self.multihash

    def encode(self, encoding: str = DEFAULT_ENCODING) -> bytes:
        """base58-encoded buffer"""

        return ensure_bytes(base58.b58encode(self.buffer))

    def to_v1(self) -> "CIDv1":
        """Get an equivalent `CIDv1` object."""

        return CIDv1(self.CODEC, self.multihash)


class CIDv1(BaseCID):
    """CID version 1 object"""

    def __init__(self, codec: str, multihash: bytes) -> None:
        """Initialize object."""

        super().__init__(1, codec, multihash)

    @property
    def buffer(self) -> bytes:
        """The raw representation of the CID"""

        return b"".join(
            [bytes([self.version]), multicodec.add_prefix(self.codec, self.multihash)]
        )

    def encode(self, encoding: str = DEFAULT_ENCODING) -> bytes:
        """Encoded version of the raw representation"""

        return multibase.encode(encoding, self.buffer)

    def to_v0(self) -> CIDv0:
        """Get an equivalent `CIDv0` object."""

        if self.codec != CIDv0.CODEC:
            raise ValueError(
                "CIDv1 can only be converted for codec {}".format(CIDv0.CODEC)
            )

        return CIDv0(self.multihash)


CIDObject = Union[CIDv0, CIDv1]


class CID:
    """CID class."""

    @classmethod
    def make(
        cls,
        version: int,
        codec: str,
        multihash: bytes,
    ) -> CIDObject:
        """Make CID from given arguments."""

        if version not in (0, 1):
            raise ValueError(
                "version should be 0 or 1, {} was provided".format(version)
            )

        if not multicodec.is_codec(codec):
            raise ValueError("invalid codec {} provided, please check".format(codec))

        if not isinstance(multihash, bytes):
            raise ValueError("invalid type for multihash provided, should be bytes")

        if version == 1:
            return CIDv1(codec, multihash)

        if codec != CIDv0.CODEC:
            raise ValueError(
                "codec for version 0 can only be {}, found: {}".format(
                    CIDv0.CODEC, codec
                )
            )
        return CIDv0(multihash)

    @classmethod
    def is_cid(cls, cid: str) -> bool:
        """Checks if a given input string is valid encoded CID or not."""

        try:
            return bool(cls.from_string(cid))
        except ValueError:
            return False

    @classmethod
    def from_string(cls, cid: str) -> CIDObject:
        """Creates a CID object from a encoded form"""

        cid_bytes = ensure_bytes(cid, "utf-8")
        return cls.from_bytes(cid_bytes)

    @classmethod
    def from_bytes(cls, cid: bytes) -> CIDObject:
        """Creates a CID object from a encoded form"""

        if len(cid) < 2:
            raise ValueError("argument length can not be zero")

        # first byte for identity multibase and CIDv0 is 0x00
        # putting in assumption that multibase for CIDv0 can not be identity
        # refer: https://github.com/ipld/cid/issues/13#issuecomment-326490275

        if cid[0] != 0 and multibase.is_encoded(cid):
            # if the bytestream is multibase encoded
            cid = multibase.decode(cid)
            if len(cid) < 2:
                raise ValueError("cid length is invalid")

            data = cid[1:]
            version = int(cid[0])
            codec = multicodec.get_codec(data)
            multihash = multicodec.remove_prefix(data)

        elif cid[0] in (0, 1):
            # if the bytestream is a CID
            version = cid[0]
            data = cid[1:]
            codec = multicodec.get_codec(data)
            multihash = multicodec.remove_prefix(data)

        else:
            # otherwise its just base58-encoded multihash
            try:
                version = 0
                codec = CIDv0.CODEC
                multihash = base58.b58decode(cid)
            except ValueError:
                raise ValueError("multihash is not a valid base58 encoded multihash")

        mh.decode(multihash)
        return cls.make(version, codec, multihash)


def to_v0(hash_string: str) -> str:
    """Convert CID v1 hash to CID v0"""

    cid = CID.from_string(hash_string)
    if cid.version == 0:
        raise ValueError(f"{hash_string} is already v0.")

    return cast(CIDv1, cid).to_v0().encode().decode()


def to_v1(hash_string: str, encoding: str = DEFAULT_ENCODING) -> str:
    """Convert CID v0 hash to CID v1"""

    cid = CID.from_string(hash_string)
    if cid.version == 1:
        raise ValueError(f"{hash_string} is already v1.")

    return cast(CIDv0, cid).to_v1().encode(encoding=encoding).decode()
