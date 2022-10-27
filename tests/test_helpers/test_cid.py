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

"""Test cid implementation."""

from typing import cast

import pytest

from aea.helpers.cid import CID, CIDv0, CIDv1, to_v0, to_v1


HASH_V0 = "QmbWqxBEKC3P8tqsKc98xmWNzrzDtRLMiMPL8wBuTGsMnR"
HASH_V1 = "bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi"


def test_conversion() -> None:
    """Test conversion."""

    assert to_v0(HASH_V1) == HASH_V0
    assert to_v1(HASH_V0) == HASH_V1

    with pytest.raises(
        ValueError,
        match=f"{HASH_V0} is already v0.",
    ):
        to_v0(HASH_V0)

    with pytest.raises(
        ValueError,
        match=f"{HASH_V1} is already v1.",
    ):
        to_v1(HASH_V1)

    with pytest.raises(
        ValueError,
        match="CIDv1 can only be converted for codec dag-pb",
    ):
        cid_v1 = cast(CIDv1, CID.from_string(HASH_V1))
        cid_v1._codec = CIDv0.CODEC[::-1]
        cid_v1.to_v0()


def test_cids() -> None:
    """Test CID object."""

    cid_v0 = CID.from_string(HASH_V0)

    assert isinstance(cid_v0, CIDv0)
    assert cid_v0.version == 0
    assert str(cid_v0) == HASH_V0

    cid_v1 = CID.from_string(HASH_V1)

    assert isinstance(cid_v1, CIDv1)
    assert cid_v1.version == 1
    assert str(cid_v1) == HASH_V1


@pytest.mark.parametrize("multihash", [HASH_V0, HASH_V1])
def test_cid__eq__(multihash):
    """Test CID __eq__"""
    cid = CID.from_string(multihash)
    assert cid is not CID.from_string(multihash)
    assert cid == CID.from_string(multihash)
    assert not cid == multihash
    assert not multihash == cid


def test_make() -> None:
    """Test make method."""

    cid_v0_expected = CID.from_string(HASH_V0)
    cid_v1_expected = CID.from_string(HASH_V1)

    with pytest.raises(ValueError, match="version should be 0 or 1, 2 was provided"):
        CID.make(2, "", b"")

    with pytest.raises(ValueError, match="invalid codec  provided, please check"):
        CID.make(0, "", b"")

    with pytest.raises(
        ValueError, match="invalid type for multihash provided, should be bytes"
    ):
        CID.make(0, CIDv0.CODEC, "")  # type: ignore

    with pytest.raises(
        ValueError, match="codec for version 0 can only be dag-pb, found: protobuf"
    ):
        CID.make(0, "protobuf", b"")

    cid_v0 = CID.make(
        cid_v0_expected.version,
        cid_v0_expected.codec,
        cid_v0_expected.multihash,
    )

    assert cid_v0 == cid_v0_expected

    cid_v1 = CID.make(
        cid_v1_expected.version,
        cid_v1_expected.codec,
        cid_v1_expected.multihash,
    )

    assert cid_v1 == cid_v1_expected


@pytest.mark.parametrize("multihash", [HASH_V0, HASH_V1])
def test_cid__repr__(multihash):
    """Test CID __repr__"""

    keys = ["version", "codec", "multihash"]
    cid = CID.from_string(multihash)
    assert all(k in repr(cid) for k in keys)


@pytest.mark.parametrize("multihash", [HASH_V0, HASH_V1])
def test_is_cid(multihash):
    """Test CID.is_cid"""

    assert CID.is_cid(multihash)
    assert not CID.is_cid(multihash[::-1])


@pytest.mark.parametrize("multihash", [HASH_V0, HASH_V1])
def test_cid_from_bytes(multihash):
    """Test CID.from_bytes"""

    multihash_bytes = multihash.encode("utf-8")
    assert CID.from_bytes(multihash_bytes)


@pytest.mark.parametrize(
    "cid_bytes, error_message",
    [
        (b"b", "argument length can not be zero"),
        (b"bb", "cid length is invalid"),
        (bytes(2), "multihash is too short"),
        (bytes(10), "multihash length field does not match digest field length"),
        (
            HASH_V1[::-1].encode("utf-8"),
            "multihash is not a valid base58 encoded multihash",
        ),
    ],
)
def test_cid_from_incorrect_bytes_raises(cid_bytes, error_message):
    """Test CID.from_bytes raises on incorrect input"""

    with pytest.raises(ValueError, match=error_message):
        assert CID.from_bytes(cid_bytes)
