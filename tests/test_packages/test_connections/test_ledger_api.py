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

"""This module contains the tests of the ledger API connection module."""
import asyncio
import logging
from pathlib import Path
from typing import cast

import pytest

import aea
from aea.components.loader import load_component_from_config
from aea.configurations.base import ComponentConfiguration, ComponentType
from aea.connections.base import Connection
from aea.crypto.fetchai import FetchAICrypto
from aea.crypto.wallet import CryptoStore
from aea.identity.base import Identity
from aea.mail.base import Envelope

from packages.fetchai.protocols.ledger_api import LedgerApiMessage

from ...conftest import (
    COSMOS_ADDRESS_ONE,
    ETHEREUM_ADDRESS_ONE,
    FETCHAI_ADDRESS_ONE,
    ROOT_DIR,
)

logger = logging.getLogger(__name__)


ledger_ids = pytest.mark.parametrize(
    "ledger_id,address",
    [
        ("fetchai", FETCHAI_ADDRESS_ONE),
        ("ethereum", ETHEREUM_ADDRESS_ONE),
        ("cosmos", COSMOS_ADDRESS_ONE),
    ],
)


@pytest.fixture()
async def ledger_apis_connection(request):
    identity = Identity("name", FetchAICrypto().address)
    crypto_store = CryptoStore()
    configuration = ComponentConfiguration.load(
        ComponentType.CONNECTION,
        Path(ROOT_DIR, "packages", "fetchai", "connections", "ledger_api"),
    )
    connection = load_component_from_config(
        configuration, identity=identity, crypto_store=crypto_store
    )
    connection = cast(Connection, connection)
    await connection.connect()
    yield connection
    await connection.disconnect()


@pytest.mark.asyncio
@ledger_ids
async def test_get_balance(ledger_id, address, ledger_apis_connection: Connection):
    """Test get balance."""
    request = LedgerApiMessage("get_balance", ledger_id=ledger_id, address=address)
    envelope = Envelope("", "", request.protocol_id, message=request)
    await ledger_apis_connection.send(envelope)
    await asyncio.sleep(0.01)
    response = await ledger_apis_connection.receive()

    assert response.message.performative == LedgerApiMessage.Performative.BALANCE
    actual_balance_amount = response.message.amount
    expected_balance_amount = aea.crypto.registries.make_ledger_api(
        ledger_id
    ).get_balance(address)
    assert actual_balance_amount == expected_balance_amount
