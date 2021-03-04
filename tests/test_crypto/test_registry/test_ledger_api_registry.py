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

"""This module contains the tests for the ledger api registry."""

import logging

import pytest
from aea_ledger_ethereum import EthereumCrypto
from aea_ledger_fetchai import FetchAICrypto

import aea.crypto

from tests.conftest import (
    ETHEREUM_ADDRESS_ONE,
    ETHEREUM_TESTNET_CONFIG,
    FETCHAI_ADDRESS_ONE,
    FETCHAI_TESTNET_CONFIG,
)


logger = logging.getLogger(__name__)


@pytest.mark.parametrize(
    "identifier,address,config",
    [
        (FetchAICrypto.identifier, FETCHAI_ADDRESS_ONE, FETCHAI_TESTNET_CONFIG),
        (EthereumCrypto.identifier, ETHEREUM_ADDRESS_ONE, ETHEREUM_TESTNET_CONFIG),
    ],
)
def test_make_ledger_apis(identifier, address, config):
    """Test the 'make' method for ledger api."""
    api = aea.crypto.registries.make_ledger_api(identifier, **config)

    # minimal functional test - comprehensive tests on ledger APIs are located in another module
    balance_1 = api.get_balance(address)
    balance_2 = api.get_balance(address)
    assert balance_1 == balance_2
