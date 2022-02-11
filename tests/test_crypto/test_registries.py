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

"""This module contains tests for aea.crypto.registries"""

from typing import Optional

from aea_ledger_cosmos import CosmosApi, CosmosCrypto

from aea.crypto.base import Crypto
from aea.crypto.registries import make_crypto, make_ledger_api
from aea.crypto.registries.base import ItemId, Registry


COSMOS = CosmosCrypto.identifier


def test_make_crypto_cosmos_positive():
    """Test make_crypto for fetchai."""
    crypto = make_crypto(COSMOS)
    assert isinstance(crypto, CosmosCrypto)


def test_make_ledger_api_cosmos_positive():
    """Test make_crypto for fetchai."""
    ledger_api = make_ledger_api(COSMOS, **{"network": "testnet"})
    assert isinstance(ledger_api, CosmosApi)


class Something:
    """Some class."""

    class_key = None  # type: Optional[str]

    def __init__(self, **kwargs):
        """Initialize something."""
        self.kwargs = kwargs


def test_register_make_with_class_kwargs():
    """Test registry make with class kwargs."""
    reg = Registry()
    id_ = "id"
    kwargs = {"key": "value"}
    class_kwargs = {"class_key": "class_value"}
    reg.register(
        id_=id_,
        entry_point="tests.test_crypto.test_registries:Something",
        class_kwargs=class_kwargs,
        **kwargs
    )
    assert Something.class_key is None
    item = reg.make(id_)
    assert item is not None
    assert type(item) == Something
    assert item.kwargs == kwargs
    assert item.class_key == "class_value"


def test_itemid():
    """Test the idemid object."""
    item_id = ItemId(COSMOS)
    assert item_id.name == COSMOS


def test_registry():
    """Test the registry object."""
    registry = Registry[Crypto]()
    item_id = ItemId(COSMOS)
    assert not registry.has_spec(item_id), "Registry should be empty"
