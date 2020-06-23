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

from aea.identity.base import Identity


def test_init_identity_positive():
    """Test initialization of the identity object."""
    assert Identity("some_name", address="some_address")
    assert Identity("some_name", address="some_address", default_address_key="cosmos")
    assert Identity(
        "some_name", addresses={"cosmos": "some_address", "fetchai": "some_address"}
    )
    assert Identity(
        "some_name",
        addresses={"cosmos": "some_address", "fetchai": "some_address"},
        default_address_key="cosmos",
    )


def test_init_identity_negative():
    """Test initialization of the identity object."""
    with pytest.raises(KeyError):
        Identity(
            "some_name",
            addresses={"cosmos": "some_address", "fetchai": "some_address"},
            default_address_key="ethereum",
        )
    with pytest.raises(AssertionError):
        Identity("some_name")


def test_accessors():
    """Test the properties of the identity object."""
    identity = Identity("some_name", address="some_address")
    assert identity.name == "some_name"
    assert identity.address == "some_address"
    assert identity.addresses == {"fetchai": "some_address"}
