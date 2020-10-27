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

"""Implementation of the base58 encoding."""

from functools import lru_cache
from hashlib import sha256
from typing import Mapping, Union


# 58 character alphabet used
BITCOIN_ALPHABET = b"123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
RIPPLE_ALPHABET = b"rpshnaf39wBUDNEGHJKLM4PQRST7VWXYZ2bcdeCg65jkm8oFqi1tuvAxyz"
XRP_ALPHABET = RIPPLE_ALPHABET

alphabet = BITCOIN_ALPHABET


def scrub_input(v: Union[str, bytes]) -> bytes:
    """Scrub the input."""
    if isinstance(v, str):
        v = v.encode("ascii")

    return v


def b58encode_int(
    i: int, default_one: bool = True, alphabet_: bytes = BITCOIN_ALPHABET
) -> bytes:
    """Encode an integer using Base58."""
    if not i and default_one:
        return alphabet_[0:1]
    string = b""
    while i:
        i, idx = divmod(i, 58)
        string = alphabet_[idx : idx + 1] + string
    return string


def b58encode(v: Union[str, bytes], alphabet_: bytes = BITCOIN_ALPHABET) -> bytes:
    """Encode a string using Base58."""
    v = scrub_input(v)

    origlen = len(v)
    v = v.lstrip(b"\0")
    newlen = len(v)

    acc = int.from_bytes(v, byteorder="big")  # first byte is most significant

    result = b58encode_int(acc, default_one=False, alphabet_=alphabet_)
    return alphabet_[0:1] * (origlen - newlen) + result


@lru_cache()
def _get_base58_decode_map(alphabet_: bytes, autofix: bool) -> Mapping[int, int]:
    invmap = {char: index for index, char in enumerate(alphabet_)}

    if autofix:
        groups = [b"0Oo", b"Il1"]
        for group in groups:
            pivots = [c for c in group if c in invmap]
            if len(pivots) == 1:
                for alternative in group:
                    invmap[alternative] = invmap[pivots[0]]

    return invmap


def b58decode_int(
    v: Union[str, bytes], alphabet_: bytes = BITCOIN_ALPHABET, *, autofix: bool = False
) -> int:
    """Decode a Base58 encoded string as an integer."""
    v = v.rstrip()
    v = scrub_input(v)

    map_ = _get_base58_decode_map(alphabet_, autofix=autofix)

    decimal = 0

    try:
        for char in v:
            decimal = decimal * 58 + map_[char]
    except KeyError as e:
        raise ValueError(
            "Invalid character <{char}>".format(char=chr(e.args[0]))
        ) from None
    return decimal


def b58decode(
    v: Union[str, bytes], alphabet_: bytes = BITCOIN_ALPHABET, *, autofix: bool = False
) -> bytes:
    """Decode a Base58 encoded string."""
    v = v.rstrip()
    v = scrub_input(v)

    origlen = len(v)
    v = v.lstrip(alphabet_[0:1])
    newlen = len(v)

    acc = b58decode_int(v, alphabet_=alphabet_, autofix=autofix)

    result = []
    while acc > 0:
        acc, mod = divmod(acc, 256)
        result.append(mod)

    return b"\0" * (origlen - newlen) + bytes(reversed(result))


def b58encode_check(v: Union[str, bytes], alphabet_: bytes = BITCOIN_ALPHABET) -> bytes:
    """Encode a string using Base58 with a 4 character checksum."""
    v = scrub_input(v)

    digest = sha256(sha256(v).digest()).digest()
    return b58encode(v + digest[:4], alphabet_=alphabet_)


def b58decode_check(
    v: Union[str, bytes], alphabet_: bytes = BITCOIN_ALPHABET, *, autofix: bool = False
) -> bytes:
    """Decode and verify the checksum of a Base58 encoded string."""

    result = b58decode(v, alphabet_=alphabet_, autofix=autofix)
    result, check = result[:-4], result[-4:]
    digest = sha256(sha256(result).digest()).digest()

    if check != digest[:4]:
        raise ValueError("Invalid checksum")

    return result
