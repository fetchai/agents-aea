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

from aea.configurations.constants import DEFAULT_LEDGER
from aea.identity.base import Identity

from tests.conftest import FETCHAI


def test_init_identity_positive():
    """Test initialization of the identity object."""
    assert Identity("some_name", address="some_address")
    assert Identity(
        "some_name", address="some_address", default_address_key=DEFAULT_LEDGER
    )
    assert Identity(
        "some_name",
        addresses={DEFAULT_LEDGER: "some_address", FETCHAI: "some_address"},
    )
    assert Identity(
        "some_name",
        addresses={DEFAULT_LEDGER: "some_address", FETCHAI: "some_address"},
        default_address_key=DEFAULT_LEDGER,
    )


def test_init_identity_negative():
    """Test initialization of the identity object."""
    name = "some_name"
    address_1 = "some_address"
    with pytest.raises(KeyError):
        Identity(
            name,
            addresses={DEFAULT_LEDGER: address_1, FETCHAI: address_1},
            default_address_key="wrong_key",
        )
    with pytest.raises(AssertionError):
        Identity(name)


def test_accessors():
    """Test the properties of the identity object."""
    name = "some_name"
    address = "some_address"
    identity = Identity(name, address=address)
    assert identity.name == name
    assert identity.address == address
    assert identity.addresses == {DEFAULT_LEDGER: address}
