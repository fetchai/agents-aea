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

"""This module contains the tests of the ledger API connection for the contract APIs."""
import asyncio
import json
from pathlib import Path
from typing import cast

import pytest

from aea.components.loader import load_component_from_config
from aea.configurations.base import (
    ComponentConfiguration,
    ComponentType,
    ContractConfig,
)
from aea.connections.base import Connection
from aea.contracts import contract_registry
from aea.crypto.fetchai import FetchAICrypto
from aea.crypto.wallet import CryptoStore
from aea.identity.base import Identity
from aea.mail.base import Envelope

from packages.fetchai.connections.ledger_api.contract_dispatcher import (
    ContractApiDialogues,
)
from packages.fetchai.protocols.contract_api import ContractApiMessage

from ....conftest import ETHEREUM_ADDRESS_ONE, ROOT_DIR


@pytest.fixture()
async def ledger_apis_connection(request):
    identity = Identity("name", FetchAICrypto().address)
    crypto_store = CryptoStore()
    directory = Path(ROOT_DIR, "packages", "fetchai", "connections", "ledger_api")
    connection = Connection.from_dir(
        directory, identity=identity, crypto_store=crypto_store
    )
    connection = cast(Connection, connection)
    await connection.connect()
    yield connection
    await connection.disconnect()


@pytest.fixture()
def load_erc1155_contract():
    directory = Path(ROOT_DIR, "packages", "fetchai", "contracts", "erc1155")
    configuration = ComponentConfiguration.load(ComponentType.CONTRACT, directory)
    configuration._directory = directory
    configuration = cast(ContractConfig, configuration)
    load_component_from_config(configuration)
    path = Path(configuration.directory, configuration.path_to_contract_interface)
    with open(path, "r") as interface_file:
        contract_interface = json.load(interface_file)

    contract_registry.register(
        id=str(configuration.public_id),
        entry_point=f"{configuration.prefix_import_path}.contract:{configuration.class_name}",
        contract_config=configuration,
        contract_interface=contract_interface,
    )
    yield
    contract_registry.specs.pop(str(configuration.public_id))


@pytest.mark.asyncio
async def test_erc1155_get_state(ledger_apis_connection, load_erc1155_contract):
    """Test get state with contract erc1155."""
    address = ETHEREUM_ADDRESS_ONE
    ledger_api_dialogues = ContractApiDialogues()
    request = ContractApiMessage(
        performative=ContractApiMessage.Performative.GET_STATE,
        dialogue_reference=ledger_api_dialogues.new_self_initiated_dialogue_reference(),
        contract_address="",  # TODO
        callable="",
        kwargs=dict(),
        ledger_id="fetchai/erc1155:0.5.0",
    )
    request.counterparty = str(ledger_apis_connection.connection_id)
    ledger_api_dialogue = ledger_api_dialogues.update(request)
    assert ledger_api_dialogue is not None
    envelope = Envelope(
        to=str(ledger_apis_connection.connection_id),
        sender=address,
        protocol_id=request.protocol_id,
        message=request,
    )

    await ledger_apis_connection.send(envelope)
    await asyncio.sleep(0.01)
    response = await ledger_apis_connection.receive()

    assert response.message.performative == ContractApiMessage.Performative.GET_STATE
