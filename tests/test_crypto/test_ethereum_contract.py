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
"""This module contains the tests of the ethereum module."""

import pytest
from aea_ledger_ethereum import EthereumApi

from tests.conftest import MAX_FLAKY_RERUNS


@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
@pytest.mark.integration
@pytest.mark.ledger
def test_get_contract_instance(erc1155_contract, ethereum_testnet_config):
    """Test the get contract instance method."""
    contract, contract_address = erc1155_contract
    ethereum_api = EthereumApi(**ethereum_testnet_config)
    interface = {"abi": [], "bytecode": b""}
    instance = ethereum_api.get_contract_instance(
        contract_interface=interface, contract_address=contract_address,
    )
    assert str(type(instance)) == "<class 'web3._utils.datatypes.Contract'>"
    instance = ethereum_api.get_contract_instance(contract_interface=interface,)
    assert (
        str(type(instance)) == "<class 'web3._utils.datatypes.PropertyCheckingFactory'>"
    )
