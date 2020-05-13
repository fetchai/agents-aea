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

"""This module contains the tests for the crypto/registry module."""

import logging

import aea.crypto
from aea.crypto.ethereum import EthereumCrypto
from aea.crypto.fetchai import FetchAICrypto
from aea.crypto.registry import EntryPoint

from ..data.custom_crypto import CustomCrypto

logger = logging.getLogger(__name__)


def test_make_fetchai():
    """Test the 'make' method for 'fetchai' crypto."""
    fetchai_crypto = aea.crypto.make("fetchai")

    assert type(fetchai_crypto) == FetchAICrypto

    # calling 'make' again will give a different object.
    fetchai_crypto_1 = aea.crypto.make("fetchai")
    assert type(fetchai_crypto) == type(fetchai_crypto_1)
    assert fetchai_crypto.address != fetchai_crypto_1


def test_make_ethereum():
    """Test the 'make' method for 'ethereum' crypto."""
    ethereum_crypto = aea.crypto.make("ethereum")

    assert type(ethereum_crypto) == EthereumCrypto

    # calling 'make' again will give a different object.
    ethereum_crypto_1 = aea.crypto.make("ethereum")
    assert type(ethereum_crypto) == type(ethereum_crypto_1)
    assert ethereum_crypto.address != ethereum_crypto_1.address


def test_register_custom_crypto():
    """Test the 'register' method with a custom crypto object."""

    aea.crypto.register(
        "my_custom_crypto", entry_point="tests.data.custom_crypto:CustomCrypto"
    )

    assert aea.crypto.registry.registry.specs.get("my_custom_crypto") is not None
    actual_spec = aea.crypto.registry.registry.specs["my_custom_crypto"]

    expected_id = "my_custom_crypto"
    expected_entry_point = EntryPoint("tests.data.custom_crypto:CustomCrypto")
    assert actual_spec.id == expected_id
    assert actual_spec.entry_point == expected_entry_point
    assert actual_spec.entry_point.import_path == expected_entry_point.import_path
    assert actual_spec.entry_point.class_name == expected_entry_point.class_name

    my_crypto = aea.crypto.make("my_custom_crypto")
    assert type(my_crypto) == CustomCrypto

    # calling 'make' again will give a different object.
    my_crypto_1 = aea.crypto.make("my_custom_crypto")
    assert type(my_crypto) == type(my_crypto_1)
    assert my_crypto != my_crypto_1
