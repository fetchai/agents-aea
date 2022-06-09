# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
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

"""This module contains misc tests for the registry (crypto/ledger_api/contract)."""

import logging

import pytest

from aea.crypto.registries.base import Registry
from aea.exceptions import AEAException


logger = logging.getLogger(__name__)


@pytest.mark.parametrize(
    "current_id,is_valid",
    [
        ("a", True),
        ("_", True),
        ("0", False),
        ("_0", True),
        ("-", False),
        ("ABCDE", True),
        ("author/package:0.1.0", True),
        ("author/package:0.1.", False),
        ("0author/package:0.1.0", False),
    ],
)
def test_validation_item_id(current_id, is_valid):
    """Test validation of item id id."""
    registry = Registry()
    entrypoint = "some_entrypoint:SomeEntrypoint"
    if is_valid:
        registry.register(current_id, entry_point=entrypoint)
    else:
        with pytest.raises(
            AEAException,
            match=rf"Malformed ItemId: '{current_id}'\. It must be of the form .*\.",
        ):
            registry.register(current_id, entry_point=entrypoint)
