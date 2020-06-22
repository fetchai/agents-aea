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

"""This module contains tests for aea.crypto.registries"""

from aea.crypto.base import Crypto
from aea.crypto.fetchai import FetchAIApi, FetchAICrypto
from aea.crypto.registries import make_crypto, make_ledger_api
from aea.crypto.registries.base import ItemId, Registry


def test_make_crypto_fetchai_positive():
    """Test make_crypto for fetchai."""
    crypto = make_crypto("fetchai")
    assert isinstance(crypto, FetchAICrypto)


def test_make_ledger_api_fetchai_positive():
    """Test make_crypto for fetchai."""
    ledger_api = make_ledger_api("fetchai")
    assert isinstance(ledger_api, FetchAIApi)


def test_itemid():
    """Test the idemid object."""
    item_id = ItemId("fetchai")
    assert item_id.name == "fetchai"


def test_registry():
    """Test the registry object."""
    registry = Registry[Crypto]()
    item_id = ItemId("fetchai")
    assert not registry.has_spec(item_id), "Registry should be empty"
