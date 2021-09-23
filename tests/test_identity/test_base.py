# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2020 Fetch.AI Limited
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
    public_key_1 = "some_public_key"
    with pytest.raises(KeyError):
        Identity(
            name,
            addresses={DEFAULT_LEDGER: address_1, FetchAICrypto.identifier: address_1},
            public_keys={
                DEFAULT_LEDGER: public_key_1,
                FetchAICrypto.identifier: public_key_1,
            },
            default_address_key="wrong_key",
        )
    with pytest.raises(ValueError):
        Identity(name)


def test_accessors():
    """Test the properties of the identity object."""
    name = "some_name"
    address = "some_address"
    public_key = "some_public_key"
    identity = Identity(name, address=address, public_key=public_key)
    assert identity.name == name
    assert identity.address == address
    assert identity.addresses == {DEFAULT_LEDGER: address}
    assert identity.default_address_key == DEFAULT_LEDGER
