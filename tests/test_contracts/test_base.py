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

"""This module contains tests for aea.contracts.base."""

import logging
import os
from pathlib import Path
from typing import cast
from unittest.mock import patch

import pytest
import web3
from aea_ledger_ethereum import EthereumCrypto
from aea_ledger_fetchai import FetchAICrypto

from aea.configurations.base import ComponentType, ContractConfig
from aea.configurations.loader import load_component_configuration
from aea.contracts import contract_registry
from aea.contracts.base import Contract
from aea.contracts.scaffold.contract import MyScaffoldContract
from aea.crypto.ledger_apis import ETHEREUM_DEFAULT_ADDRESS, FETCHAI_DEFAULT_ADDRESS
from aea.crypto.registries import crypto_registry, ledger_apis_registry
from aea.exceptions import AEAComponentLoadException

from tests.conftest import ROOT_DIR, make_uri


logger = logging.getLogger(__name__)


def test_from_dir():
    """Tests the from dir and from config methods."""
    contract = Contract.from_dir(
        os.path.join(ROOT_DIR, "tests", "data", "dummy_contract")
    )
    assert contract is not None
    assert contract.contract_interface is not None
    assert isinstance(contract.contract_interface, dict)


def test_from_config_and_registration():
    """Tests the from config method and contract registry registration."""

    directory = Path(ROOT_DIR, "tests", "data", "dummy_contract")
    configuration = load_component_configuration(ComponentType.CONTRACT, directory)
    configuration._directory = directory
    configuration = cast(ContractConfig, configuration)

    if str(configuration.public_id) in contract_registry.specs:
        contract_registry.specs.pop(str(configuration.public_id))

    contract = Contract.from_config(configuration)
    assert contract is not None
    assert contract.contract_interface is not None
    assert isinstance(contract.contract_interface, dict)
    assert contract.configuration == configuration
    assert contract.id == configuration.public_id

    # the contract is registered as side-effect
    assert str(contract.public_id) in contract_registry.specs

    try:
        contract_registry.specs.pop(str(configuration.public_id))
    except Exception as e:
        logger.exception(e)


def test_from_config_negative():
    """Tests the from config method raises."""

    directory = Path(ROOT_DIR, "tests", "data", "dummy_contract")
    configuration = load_component_configuration(ComponentType.CONTRACT, directory)
    configuration._directory = directory
    configuration = cast(ContractConfig, configuration)

    if str(configuration.public_id) in contract_registry.specs:
        contract_registry.specs.pop(str(configuration.public_id))

    configuration.class_name = "WrongName"
    with pytest.raises(AEAComponentLoadException):
        _ = Contract.from_config(configuration)

    try:
        contract_registry.specs.pop(str(configuration.public_id))
    except Exception as e:
        logger.exception(e)


def test_non_implemented_class_methods():
    """Tests the non implemented class methods."""
    with pytest.raises(NotImplementedError):
        Contract.get_raw_transaction("ledger_api", "contract_address")

    with pytest.raises(NotImplementedError):
        Contract.get_raw_message("ledger_api", "contract_address")

    with pytest.raises(NotImplementedError):
        Contract.get_state("ledger_api", "contract_address")


@pytest.fixture()
def dummy_contract(request):
    """Dummy contract fixture."""
    directory = Path(ROOT_DIR, "tests", "data", "dummy_contract")
    configuration = load_component_configuration(ComponentType.CONTRACT, directory)
    configuration._directory = directory
    configuration = cast(ContractConfig, configuration)

    if str(configuration.public_id) in contract_registry.specs:
        contract_registry.specs.pop(str(configuration.public_id))

    # load into sys modules and register into contract registry
    contract = Contract.from_config(configuration)
    yield contract
    contract_registry.specs.pop(str(configuration.public_id))


def test_get_instance_no_address_ethereum(dummy_contract):
    """Tests get instance method with no address for ethereum."""
    ledger_api = ledger_apis_registry.make(
        EthereumCrypto.identifier, address=ETHEREUM_DEFAULT_ADDRESS,
    )
    instance = dummy_contract.get_instance(ledger_api)
    assert type(instance) == web3._utils.datatypes.PropertyCheckingFactory


@pytest.mark.integration
@pytest.mark.ledger
def test_get_deploy_transaction_ethereum(
    dummy_contract, ganache_addr, ganache_port, ganache
):
    """Tests the deploy transaction classmethod for ethereum."""
    aea_ledger_ethereum = crypto_registry.make(EthereumCrypto.identifier)
    ledger_api = ledger_apis_registry.make(
        EthereumCrypto.identifier, address=make_uri(ganache_addr, ganache_port)
    )
    with patch(
        "web3.contract.ContractConstructor.buildTransaction",
        return_value={"data": "0xstub"},
    ):
        deploy_tx = dummy_contract.get_deploy_transaction(
            ledger_api, aea_ledger_ethereum.address
        )
    assert deploy_tx is not None and len(deploy_tx) == 6
    assert all(
        key in ["from", "value", "gas", "gasPrice", "nonce", "data"]
        for key in deploy_tx.keys()
    )


def test_get_instance_no_address_cosmwasm(dummy_contract):
    """Tests get instance method with no address for fetchai."""
    ledger_api = ledger_apis_registry.make(
        FetchAICrypto.identifier, address=FETCHAI_DEFAULT_ADDRESS,
    )
    instance = dummy_contract.get_instance(ledger_api)
    assert instance is None


def test_get_deploy_transaction_cosmwasm(dummy_contract):
    """Tests the deploy transaction classmethod for fetchai."""
    aea_ledger_fetchai = crypto_registry.make(FetchAICrypto.identifier)
    ledger_api = ledger_apis_registry.make(
        FetchAICrypto.identifier, address=FETCHAI_DEFAULT_ADDRESS,
    )
    deploy_tx = dummy_contract.get_deploy_transaction(
        ledger_api, aea_ledger_fetchai.address, account_number=1, sequence=0
    )
    assert deploy_tx is not None and len(deploy_tx) == 2
    assert all(key in ["tx", "sign_data"] for key in deploy_tx.keys())


def test_scaffold():
    """Test the scaffold contract can be loaded/instantiated."""
    scaffold = MyScaffoldContract("config")
    kwargs = {"key": "value"}
    with pytest.raises(NotImplementedError):
        scaffold.get_raw_transaction("ledger_api", "contract_address", **kwargs)
    with pytest.raises(NotImplementedError):
        scaffold.get_raw_message("ledger_api", "contract_address", **kwargs)
    with pytest.raises(NotImplementedError):
        scaffold.get_state("ledger_api", "contract_address", **kwargs)
