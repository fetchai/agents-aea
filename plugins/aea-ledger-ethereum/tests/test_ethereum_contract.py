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

from pathlib import Path
from typing import Dict, cast

import pytest
from aea_ledger_ethereum import EthereumApi, EthereumCrypto

from tests.conftest import ETHEREUM_PRIVATE_KEY_PATH, MAX_FLAKY_RERUNS, ROOT_DIR


@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
@pytest.mark.integration
@pytest.mark.ledger
def test_get_contract_instance(ethereum_testnet_config, ganache):
    """Test the get contract instance method."""
    ec = EthereumCrypto(private_key_path=ETHEREUM_PRIVATE_KEY_PATH)
    ethereum_api = EthereumApi(**ethereum_testnet_config)
    full_path = Path(ROOT_DIR, "tests", "data", "dummy_contract", "build", "some.json")
    contract_interface = ethereum_api.load_contract_interface(full_path)
    tx = ethereum_api.get_deploy_transaction(
        contract_interface, ec.address, gas=5000000
    )
    gas = ethereum_api.api.eth.estimateGas(transaction=tx)
    tx["gas"] = gas
    tx_signed = ec.sign_transaction(tx)
    tx_receipt = ethereum_api.send_signed_transaction(tx_signed)
    receipt = ethereum_api.get_transaction_receipt(tx_receipt)
    erc1155_contract_address = cast(Dict, receipt)["contractAddress"]
    interface = {"abi": [], "bytecode": b""}
    instance = ethereum_api.get_contract_instance(
        contract_interface=interface, contract_address=erc1155_contract_address,
    )
    assert str(type(instance)) == "<class 'web3._utils.datatypes.Contract'>"
    instance = ethereum_api.get_contract_instance(contract_interface=interface,)
    assert (
        str(type(instance)) == "<class 'web3._utils.datatypes.PropertyCheckingFactory'>"
    )
