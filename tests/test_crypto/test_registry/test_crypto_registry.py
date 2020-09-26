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

"""This module contains the tests for the crypto registry."""

import logging
import string
from unittest import mock

import pytest

import aea.crypto
from aea.crypto.cosmos import CosmosCrypto
from aea.crypto.ethereum import EthereumCrypto
from aea.crypto.fetchai import FetchAICrypto
from aea.crypto.registries.base import EntryPoint
from aea.exceptions import AEAException

from tests.conftest import COSMOS, ETHEREUM, FETCHAI
from tests.data.custom_crypto import CustomCrypto


logger = logging.getLogger(__name__)

forbidden_special_characters = "".join(
    filter(lambda c: c not in "_:/.", string.punctuation)
)


def test_make_fetchai():
    """Test the 'make' method for 'fetchai' crypto."""
    fetchai_crypto = aea.crypto.registries.make_crypto(FETCHAI)

    assert type(fetchai_crypto) == FetchAICrypto

    # calling 'make' again will give a different object.
    fetchai_crypto_1 = aea.crypto.registries.make_crypto(FETCHAI)
    assert type(fetchai_crypto) == type(fetchai_crypto_1)
    assert fetchai_crypto.address != fetchai_crypto_1


def test_make_ethereum():
    """Test the 'make' method for 'ethereum' crypto."""
    ethereum_crypto = aea.crypto.registries.make_crypto(ETHEREUM)

    assert type(ethereum_crypto) == EthereumCrypto

    # calling 'make' again will give a different object.
    ethereum_crypto_1 = aea.crypto.registries.make_crypto(ETHEREUM)
    assert type(ethereum_crypto) == type(ethereum_crypto_1)
    assert ethereum_crypto.address != ethereum_crypto_1.address


def test_make_cosmos():
    """Test the 'make' method for 'cosmos' crypto."""
    cosmos_crypto = aea.crypto.registries.make_crypto(COSMOS)

    assert type(cosmos_crypto) == CosmosCrypto

    # calling 'make' again will give a different object.
    cosmos_crypto_1 = aea.crypto.registries.make_crypto(COSMOS)
    assert type(cosmos_crypto) == type(cosmos_crypto_1)
    assert cosmos_crypto.address != cosmos_crypto_1.address


def test_register_custom_crypto():
    """Test the 'register' method with a custom crypto object."""

    aea.crypto.registries.register_crypto(
        "my_custom_crypto", entry_point="tests.data.custom_crypto:CustomCrypto"
    )

    assert (
        aea.crypto.registries.crypto_registry.specs.get("my_custom_crypto") is not None
    )
    actual_spec = aea.crypto.registries.crypto_registry.specs["my_custom_crypto"]

    expected_id = "my_custom_crypto"
    expected_entry_point = EntryPoint("tests.data.custom_crypto:CustomCrypto")
    assert actual_spec.id == expected_id
    assert actual_spec.entry_point == expected_entry_point
    assert actual_spec.entry_point.import_path == expected_entry_point.import_path
    assert actual_spec.entry_point.class_name == expected_entry_point.class_name

    my_crypto = aea.crypto.registries.make_crypto("my_custom_crypto")
    assert type(my_crypto) == CustomCrypto

    # calling 'make' again will give a different object.
    my_crypto_1 = aea.crypto.registries.make_crypto("my_custom_crypto")
    assert type(my_crypto) == type(my_crypto_1)
    assert my_crypto != my_crypto_1

    aea.crypto.registries.crypto_registry.specs.pop("my_custom_crypto")


def test_cannot_register_crypto_twice():
    """Test we cannot register a crytpo twice."""
    aea.crypto.registries.register_crypto(
        "my_custom_crypto", entry_point="tests.data.custom_crypto:CustomCrypto"
    )

    with pytest.raises(AEAException, match="Cannot re-register id: 'my_custom_crypto'"):
        aea.crypto.registries.register_crypto(
            "my_custom_crypto", entry_point="tests.data.custom_crypto:CustomCrypto"
        )

    aea.crypto.registries.crypto_registry.specs.pop("my_custom_crypto")


@mock.patch("importlib.import_module", side_effect=ImportError)
def test_import_error(*mocks):
    """Test import errors."""
    aea.crypto.registries.register_crypto(
        "some_crypto", entry_point="path.to.module:SomeCrypto"
    )
    with pytest.raises(
        AEAException,
        match="A module (.*) was specified for the item but was not found",
    ):
        aea.crypto.registries.make_crypto("some_crypto", module="some.module")
    aea.crypto.registries.crypto_registry.specs.pop("some_crypto")


class TestRegisterWithMalformedId:
    """Test the error message when we try to register a crypto whose identifier is malformed."""

    MESSAGE_REGEX = "Malformed .*: '.*'. It must be of the form '.*'."

    def test_wrong_spaces(self):
        """Spaces not allowed in a Crypto ID."""
        # beginning space
        with pytest.raises(AEAException, match=self.MESSAGE_REGEX):
            aea.crypto.registries.register_crypto(
                " malformed_id", "path.to.module:CryptoClass"
            )

        # trailing space
        with pytest.raises(AEAException, match=self.MESSAGE_REGEX):
            aea.crypto.registries.register_crypto(
                "malformed_id ", "path.to.module:CryptoClass"
            )

        # in between
        with pytest.raises(AEAException, match=self.MESSAGE_REGEX):
            aea.crypto.registries.register_crypto(
                "malformed id", "path.to.module:CryptoClass"
            )

    @pytest.mark.parametrize("special_character", forbidden_special_characters)
    def test_special_characters(self, special_character):
        """Special characters are not allowed (only underscore)."""
        with pytest.raises(AEAException, match=self.MESSAGE_REGEX):
            aea.crypto.registries.register_crypto(
                "malformed_id" + special_character, "path.to.module:CryptoClass"
            )


class TestRegisterWithMalformedEntryPoint:
    """Test the error message when we try to register a crypto with a wrong entry point."""

    MESSAGE_REGEX = "Malformed .*: '.*'. It must be of the form '.*'."

    def test_wrong_spaces(self):
        """Spaces not allowed in a Crypto ID."""
        # beginning space
        with pytest.raises(AEAException, match=self.MESSAGE_REGEX):
            aea.crypto.registries.register_crypto(
                "crypto_id", " path.to.module:CryptoClass"
            )

        # trailing space
        with pytest.raises(AEAException, match=self.MESSAGE_REGEX):
            aea.crypto.registries.register_crypto(
                "crypto_id", "path.to.module :CryptoClass"
            )

        # in between
        with pytest.raises(AEAException, match=self.MESSAGE_REGEX):
            aea.crypto.registries.register_crypto(
                "crypto_id", "path.to .module:CryptoClass"
            )

    @pytest.mark.parametrize("special_character", forbidden_special_characters)
    def test_special_characters(self, special_character):
        """Special characters are not allowed (only underscore)."""
        with pytest.raises(AEAException, match=self.MESSAGE_REGEX):
            aea.crypto.registries.register_crypto(
                "crypto_id", "path" + special_character + ".to.module:CryptoClass"
            )
