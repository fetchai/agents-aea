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

"""This module contains the tests for the identity module."""

import pytest
from aea_ledger_fetchai import FetchAICrypto

from aea.configurations.constants import DEFAULT_LEDGER
from aea.exceptions import AEAEnforceError
from aea.identity.base import Identity


def test_init_identity_positive():
    """Test initialization of the identity object."""
    assert Identity("some_name", address="some_address", public_key="some_public_key")
    assert Identity(
        "some_name",
        address="some_address",
        public_key="some_public_key",
        default_address_key=DEFAULT_LEDGER,
    )
    assert Identity(
        "some_name",
        addresses={
            DEFAULT_LEDGER: "some_address",
            FetchAICrypto.identifier: "some_address",
        },
        public_keys={
            DEFAULT_LEDGER: "some_public_key",
            FetchAICrypto.identifier: "some_public_key",
        },
    )
    assert Identity(
        "some_name",
        addresses={
            DEFAULT_LEDGER: "some_address",
            FetchAICrypto.identifier: "some_address",
        },
        public_keys={
            DEFAULT_LEDGER: "some_public_key",
            FetchAICrypto.identifier: "some_public_key",
        },
        default_address_key=DEFAULT_LEDGER,
    )


def test_init_identity_negative():
    """Test initialization of the identity object."""
    name = "some_name"
    address_1 = "some_address"
    addresses_1 = {"some_ledger_id": "some_address"}
    addresses_2 = {}
    public_key_1 = "some_public_key"
    public_keys_1 = {"some_ledger_id": "some_public_key"}
    public_keys_2 = {}
    with pytest.raises(ValueError, match="Provide a key for the default address."):
        Identity(name, default_address_key=None)
    with pytest.raises(
        ValueError,
        match="Either provide a single address or a dictionary of addresses, and not both.",
    ):
        Identity(name)
    with pytest.raises(
        ValueError,
        match="Either provide a single address or a dictionary of addresses, and not both.",
    ):
        Identity(name, address=address_1, addresses=addresses_1)
    with pytest.raises(ValueError, match="Provide at least one pair of addresses."):
        Identity(name, addresses=addresses_2)
    with pytest.raises(
        ValueError,
        match="If you provide a dictionary of addresses, you must provide its corresponding dictionary of public keys.",
    ):
        Identity(name, addresses=addresses_1)
    with pytest.raises(
        ValueError,
        match="If you provide a dictionary of addresses, you must not provide a single public key.",
    ):
        Identity(name, addresses=addresses_1, public_key=public_key_1)
    with pytest.raises(
        AEAEnforceError,
        match="Keys in public keys and addresses dictionaries do not match. They must be identical.",
    ):
        Identity(name, addresses=addresses_1, public_keys=public_keys_2)
    with pytest.raises(
        AEAEnforceError,
        match="The default address key must exist in both addresses and public keys dictionaries.",
    ):
        Identity(
            name,
            addresses=addresses_1,
            public_keys=public_keys_1,
            default_address_key="some_other_ledger",
        )
    with pytest.raises(
        ValueError,
        match="If you provide a single address, you must not provide a dictionary of public keys.",
    ):
        Identity(name, address=address_1, public_keys=public_keys_1)
    with pytest.raises(
        ValueError,
        match="If you provide a single address, you must provide its corresponding public key.",
    ):
        Identity(name, address=address_1)


def test_accessors():
    """Test the properties of the identity object."""
    name = "some_name"
    address = "some_address"
    public_key = "some_public_key"
    identity = Identity(name, address=address, public_key=public_key)
    assert identity.name == name
    assert identity.address == address
    assert identity.addresses == {DEFAULT_LEDGER: address}
    assert identity.public_key == public_key
    assert identity.public_keys == {DEFAULT_LEDGER: public_key}
    assert identity.default_address_key == DEFAULT_LEDGER
