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
import unittest.mock
from typing import cast

import pytest

from aea.connections.base import ConnectionStatus
from aea.helpers.transaction.base import RawMessage, RawTransaction, State
from aea.mail.base import Envelope

from packages.fetchai.connections.ledger.contract_dispatcher import (
    ContractApiDialogues,
    ContractApiRequestDispatcher,
)
from packages.fetchai.protocols.contract_api import ContractApiMessage

from tests.common.mocks import MockCallableNTimes
from tests.conftest import ETHEREUM, ETHEREUM_ADDRESS_ONE


@pytest.mark.integration
@pytest.mark.ledger
@pytest.mark.asyncio
async def test_erc1155_get_deploy_transaction(erc1155_contract, ledger_apis_connection):
    """Test get state with contract erc1155."""
    # TODO to fix
    address = ETHEREUM_ADDRESS_ONE
    contract_api_dialogues = ContractApiDialogues()
    request = ContractApiMessage(
        performative=ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION,
        dialogue_reference=contract_api_dialogues.new_self_initiated_dialogue_reference(),
        ledger_id=ETHEREUM,
        contract_id="fetchai/erc1155:0.6.0",
        callable="get_deploy_transaction",
        kwargs=ContractApiMessage.Kwargs({"deployer_address": address}),
    )
    request.counterparty = str(ledger_apis_connection.connection_id)
    contract_api_dialogue = contract_api_dialogues.update(request)
    assert contract_api_dialogue is not None
    envelope = Envelope(
        to=str(ledger_apis_connection.connection_id),
        sender=address,
        protocol_id=request.protocol_id,
        message=request,
    )

    await ledger_apis_connection.send(envelope)
    await asyncio.sleep(0.01)
    response = await ledger_apis_connection.receive()

    assert response is not None
    assert type(response.message) == ContractApiMessage
    response_message = cast(ContractApiMessage, response.message)
    assert (
        response_message.performative == ContractApiMessage.Performative.RAW_TRANSACTION
    ), "Error: {}".format(response_message.message)
    response_dialogue = contract_api_dialogues.update(response_message)
    assert response_dialogue == contract_api_dialogue
    assert type(response_message.raw_transaction) == RawTransaction
    assert response_message.raw_transaction.ledger_id == ETHEREUM
    assert len(response.message.raw_transaction.body) == 6
    assert len(response.message.raw_transaction.body["data"]) > 0


@pytest.mark.integration
@pytest.mark.ledger
@pytest.mark.asyncio
async def test_erc1155_get_deploy_transaction_via_callable(
    erc1155_contract, ledger_apis_connection
):
    """Test get_deploy_transaction with contract erc1155 via callable."""
    address = ETHEREUM_ADDRESS_ONE
    contract_api_dialogues = ContractApiDialogues()
    request = ContractApiMessage(
        performative=ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION,
        dialogue_reference=contract_api_dialogues.new_self_initiated_dialogue_reference(),
        ledger_id=ETHEREUM,
        contract_id="fetchai/erc1155:0.6.0",
        callable="get_deploy_transaction",
        kwargs=ContractApiMessage.Kwargs({"deployer_address": address}),
    )
    request.counterparty = str(ledger_apis_connection.connection_id)
    contract_api_dialogue = contract_api_dialogues.update(request)
    assert contract_api_dialogue is not None
    envelope = Envelope(
        to=str(ledger_apis_connection.connection_id),
        sender=address,
        protocol_id=request.protocol_id,
        message=request,
    )

    original_get = request.get

    class mocked_get:
        def __init__(self):
            self.performative_values = MockCallableNTimes(
                [None, None, NotImplementedError], original_get("performative")
            )

        def __call__(self, key, *args, **kwargs):
            if key == "performative":
                return self.performative_values()
            else:
                return original_get(key)

    with unittest.mock.patch.object(
        request, "get", side_effect=mocked_get(),
    ):
        await ledger_apis_connection.send(envelope)
        await asyncio.sleep(0.01)
        response = await ledger_apis_connection.receive()

        assert response is not None
        assert type(response.message) == ContractApiMessage
        response_message = cast(ContractApiMessage, response.message)
        assert (
            response_message.performative
            == ContractApiMessage.Performative.RAW_TRANSACTION
        ), "Error: {}".format(response_message.message)
        response_dialogue = contract_api_dialogues.update(response_message)
        assert response_dialogue == contract_api_dialogue
        assert type(response_message.raw_transaction) == RawTransaction
        assert response_message.raw_transaction.ledger_id == ETHEREUM
        assert len(response.message.raw_transaction.body) == 6
        assert len(response.message.raw_transaction.body["data"]) > 0


@pytest.mark.integration
@pytest.mark.ledger
@pytest.mark.asyncio
async def test_erc1155_get_raw_transaction(erc1155_contract, ledger_apis_connection):
    """Test get state with contract erc1155."""
    address = ETHEREUM_ADDRESS_ONE
    contract_address = "0x250A2aeb3eB84782e83365b4c42dbE3CDA9920e4"
    contract_api_dialogues = ContractApiDialogues()
    request = ContractApiMessage(
        performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,
        dialogue_reference=contract_api_dialogues.new_self_initiated_dialogue_reference(),
        ledger_id=ETHEREUM,
        contract_id="fetchai/erc1155:0.6.0",
        contract_address=contract_address,
        callable="get_create_batch_transaction",
        kwargs=ContractApiMessage.Kwargs(
            {"deployer_address": address, "token_ids": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]}
        ),
    )
    request.counterparty = str(ledger_apis_connection.connection_id)
    contract_api_dialogue = contract_api_dialogues.update(request)
    assert contract_api_dialogue is not None
    envelope = Envelope(
        to=str(ledger_apis_connection.connection_id),
        sender=address,
        protocol_id=request.protocol_id,
        message=request,
    )

    await ledger_apis_connection.send(envelope)
    await asyncio.sleep(0.01)
    response = await ledger_apis_connection.receive()

    assert response is not None
    assert type(response.message) == ContractApiMessage
    response_message = cast(ContractApiMessage, response.message)
    assert (
        response_message.performative == ContractApiMessage.Performative.RAW_TRANSACTION
    ), "Error: {}".format(response_message.message)
    response_dialogue = contract_api_dialogues.update(response_message)
    assert response_dialogue == contract_api_dialogue
    assert type(response_message.raw_transaction) == RawTransaction
    assert response_message.raw_transaction.ledger_id == ETHEREUM
    assert len(response.message.raw_transaction.body) == 7
    assert len(response.message.raw_transaction.body["data"]) > 0


@pytest.mark.integration
@pytest.mark.ledger
@pytest.mark.asyncio
async def test_erc1155_get_raw_message(erc1155_contract, ledger_apis_connection):
    """Test get state with contract erc1155."""
    address = ETHEREUM_ADDRESS_ONE
    contract_address = "0x250A2aeb3eB84782e83365b4c42dbE3CDA9920e4"
    contract_api_dialogues = ContractApiDialogues()
    request = ContractApiMessage(
        performative=ContractApiMessage.Performative.GET_RAW_MESSAGE,
        dialogue_reference=contract_api_dialogues.new_self_initiated_dialogue_reference(),
        ledger_id=ETHEREUM,
        contract_id="fetchai/erc1155:0.6.0",
        contract_address=contract_address,
        callable="get_hash_single",
        kwargs=ContractApiMessage.Kwargs(
            {
                "from_address": address,
                "to_address": address,
                "token_id": 1,
                "from_supply": 10,
                "to_supply": 0,
                "value": 0,
                "trade_nonce": 1,
            }
        ),
    )
    request.counterparty = str(ledger_apis_connection.connection_id)
    contract_api_dialogue = contract_api_dialogues.update(request)
    assert contract_api_dialogue is not None
    envelope = Envelope(
        to=str(ledger_apis_connection.connection_id),
        sender=address,
        protocol_id=request.protocol_id,
        message=request,
    )

    await ledger_apis_connection.send(envelope)
    await asyncio.sleep(0.01)
    response = await ledger_apis_connection.receive()

    assert response is not None
    assert type(response.message) == ContractApiMessage
    response_message = cast(ContractApiMessage, response.message)
    assert (
        response_message.performative == ContractApiMessage.Performative.RAW_MESSAGE
    ), "Error: {}".format(response_message.message)
    response_dialogue = contract_api_dialogues.update(response_message)
    assert response_dialogue == contract_api_dialogue
    assert type(response_message.raw_message) == RawMessage
    assert response_message.raw_message.ledger_id == ETHEREUM
    assert type(response.message.raw_message.body) == bytes


@pytest.mark.integration
@pytest.mark.ledger
@pytest.mark.asyncio
async def test_erc1155_get_state(erc1155_contract, ledger_apis_connection):
    """Test get state with contract erc1155."""
    address = ETHEREUM_ADDRESS_ONE
    contract_address = "0x250A2aeb3eB84782e83365b4c42dbE3CDA9920e4"
    contract_api_dialogues = ContractApiDialogues()
    token_id = 1
    request = ContractApiMessage(
        performative=ContractApiMessage.Performative.GET_STATE,
        dialogue_reference=contract_api_dialogues.new_self_initiated_dialogue_reference(),
        ledger_id=ETHEREUM,
        contract_id="fetchai/erc1155:0.6.0",
        contract_address=contract_address,
        callable="get_balance",
        kwargs=ContractApiMessage.Kwargs(
            {"agent_address": address, "token_id": token_id}
        ),
    )
    request.counterparty = str(ledger_apis_connection.connection_id)
    contract_api_dialogue = contract_api_dialogues.update(request)
    assert contract_api_dialogue is not None
    envelope = Envelope(
        to=str(ledger_apis_connection.connection_id),
        sender=address,
        protocol_id=request.protocol_id,
        message=request,
    )

    await ledger_apis_connection.send(envelope)
    await asyncio.sleep(0.01)
    response = await ledger_apis_connection.receive()

    assert response is not None
    assert type(response.message) == ContractApiMessage
    response_message = cast(ContractApiMessage, response.message)
    assert (
        response_message.performative == ContractApiMessage.Performative.STATE
    ), "Error: {}".format(response_message.message)
    response_dialogue = contract_api_dialogues.update(response_message)
    assert response_dialogue == contract_api_dialogue
    assert type(response_message.state) == State
    assert response_message.state.ledger_id == ETHEREUM
    result = response_message.state.body.get("balance", None)
    expected_result = {token_id: 0}
    assert result is not None and result == expected_result


@pytest.mark.asyncio
async def test_run_async():
    """Test run async error handled."""
    # for pydocstyle
    def _raise():
        raise Exception("Expected")

    contract_api_dialogues = ContractApiDialogues()
    message = ContractApiMessage(
        performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,
        dialogue_reference=contract_api_dialogues.new_self_initiated_dialogue_reference(),
        ledger_id=ETHEREUM,
        contract_id="fetchai/erc1155:0.6.0",
        contract_address="test addr",
        callable="get_create_batch_transaction",
        kwargs=ContractApiMessage.Kwargs(
            {
                "deployer_address": "test_addr",
                "token_ids": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            }
        ),
    )
    message.counterparty = "test"
    dialogue = contract_api_dialogues.update(message)
    api = None
    msg = await ContractApiRequestDispatcher(ConnectionStatus()).run_async(
        _raise, api, message, dialogue
    )
    assert msg.performative == ContractApiMessage.Performative.ERROR


@pytest.mark.asyncio
async def test_get_handler():
    """Test failed to get handler."""
    with pytest.raises(Exception, match="Performative not recognized."):
        ContractApiRequestDispatcher(ConnectionStatus()).get_handler(
            ContractApiMessage.Performative.ERROR
        )


@pytest.mark.integration
@pytest.mark.ledger
@pytest.mark.asyncio
async def test_callable_wrong_number_of_arguments_api_and_contract_address(
    erc1155_contract, ledger_apis_connection
):
    """
    Test a contract callable with wrong number of arguments.

    Test the case of either GET_STATE, GET_RAW_MESSAGE or GET_RAW_TRANSACTION.
    """
    address = ETHEREUM_ADDRESS_ONE
    contract_api_dialogues = ContractApiDialogues()
    token_id = 1
    contract_address = "0x250A2aeb3eB84782e83365b4c42dbE3CDA9920e4"
    request = ContractApiMessage(
        performative=ContractApiMessage.Performative.GET_STATE,
        dialogue_reference=contract_api_dialogues.new_self_initiated_dialogue_reference(),
        ledger_id=ETHEREUM,
        contract_id="fetchai/erc1155:0.6.0",
        contract_address=contract_address,
        callable="get_balance",
        kwargs=ContractApiMessage.Kwargs(
            {"agent_address": address, "token_id": token_id}
        ),
    )
    request.counterparty = str(ledger_apis_connection.connection_id)
    contract_api_dialogue = contract_api_dialogues.update(request)
    assert contract_api_dialogue is not None
    envelope = Envelope(
        to=str(ledger_apis_connection.connection_id),
        sender=address,
        protocol_id=request.protocol_id,
        message=request,
    )

    with unittest.mock.patch(
        "inspect.getfullargspec", return_value=unittest.mock.MagicMock(args=[None])
    ):
        with unittest.mock.patch.object(
            ledger_apis_connection._logger, "error"
        ) as mock_logger:
            await ledger_apis_connection.send(envelope)
            await asyncio.sleep(0.01)
            response = await ledger_apis_connection.receive()
            mock_logger.assert_any_call(
                "Expected two or more positional arguments, got 1"
            )
            assert (
                response.message.performative == ContractApiMessage.Performative.ERROR
            )
            assert (
                response.message.message
                == "Expected two or more positional arguments, got 1"
            )


@pytest.mark.integration
@pytest.mark.ledger
@pytest.mark.asyncio
async def test_callable_wrong_number_of_arguments_apis(
    erc1155_contract, ledger_apis_connection
):
    """
    Test a contract callable with wrong number of arguments.

    Test the case of GET_DEPLOY_TRANSACTION.
    """
    address = ETHEREUM_ADDRESS_ONE
    contract_api_dialogues = ContractApiDialogues()
    request = ContractApiMessage(
        performative=ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION,
        dialogue_reference=contract_api_dialogues.new_self_initiated_dialogue_reference(),
        ledger_id=ETHEREUM,
        contract_id="fetchai/erc1155:0.6.0",
        callable="get_create_batch_transaction",
        kwargs=ContractApiMessage.Kwargs({"deployer_address": address}),
    )
    request.counterparty = str(ledger_apis_connection.connection_id)
    contract_api_dialogue = contract_api_dialogues.update(request)
    assert contract_api_dialogue is not None
    envelope = Envelope(
        to=str(ledger_apis_connection.connection_id),
        sender=address,
        protocol_id=request.protocol_id,
        message=request,
    )

    original_get = request.get

    class mocked_get:
        def __init__(self):
            self.performative_values = MockCallableNTimes(
                [None, None, NotImplementedError], original_get("performative")
            )

        def __call__(self, key, *args, **kwargs):
            if key == "performative":
                return self.performative_values()
            else:
                return original_get(key)

    with unittest.mock.patch(
        "inspect.getfullargspec", return_value=unittest.mock.MagicMock(args=[])
    ), unittest.mock.patch.object(
        request, "get", side_effect=mocked_get(),
    ), unittest.mock.patch.object(
        ledger_apis_connection._logger, "error"
    ) as mock_logger:
        await ledger_apis_connection.send(envelope)
        await asyncio.sleep(0.01)
        response = await ledger_apis_connection.receive()
        mock_logger.assert_any_call("Expected one or more positional arguments, got 0")
        assert response.message.performative == ContractApiMessage.Performative.ERROR
        assert (
            response.message.message
            == "Expected one or more positional arguments, got 0"
        )


@pytest.mark.integration
@pytest.mark.ledger
@pytest.mark.asyncio
async def test_nonexisting_callable(erc1155_contract, ledger_apis_connection):
    """Test the case where the specified callable does not exist."""
    address = ETHEREUM_ADDRESS_ONE
    contract_address = "0x250A2aeb3eB84782e83365b4c42dbE3CDA9920e4"
    contract_api_dialogues = ContractApiDialogues()
    request = ContractApiMessage(
        performative=ContractApiMessage.Performative.GET_STATE,
        dialogue_reference=contract_api_dialogues.new_self_initiated_dialogue_reference(),
        ledger_id=ETHEREUM,
        contract_address=contract_address,
        contract_id="fetchai/erc1155:0.6.0",
        callable="not_existing_callable",
        kwargs=ContractApiMessage.Kwargs({"deployer_address": address}),
    )
    request.counterparty = str(ledger_apis_connection.connection_id)
    contract_api_dialogue = contract_api_dialogues.update(request)
    assert contract_api_dialogue is not None
    envelope = Envelope(
        to=str(ledger_apis_connection.connection_id),
        sender=address,
        protocol_id=request.protocol_id,
        message=request,
    )

    with unittest.mock.patch.object(
        ledger_apis_connection._logger, "error"
    ) as mock_logger:
        await ledger_apis_connection.send(envelope)
        await asyncio.sleep(0.01)
        response = await ledger_apis_connection.receive()
        mock_logger.assert_any_call(
            f"Cannot find '{request.callable}' in contract '{type(erc1155_contract).__name__}'"
        )
        assert response.message.performative == ContractApiMessage.Performative.ERROR
        assert (
            response.message.message
            == f"Cannot find '{request.callable}' in contract '{type(erc1155_contract).__name__}'"
        )


@pytest.mark.integration
@pytest.mark.ledger
@pytest.mark.asyncio
async def test_callable_generic_error(erc1155_contract, ledger_apis_connection):
    """Test error messages when an exception is raised while processing the request."""
    address = ETHEREUM_ADDRESS_ONE
    contract_api_dialogues = ContractApiDialogues()
    token_id = 1
    contract_address = "0x250A2aeb3eB84782e83365b4c42dbE3CDA9920e4"
    request = ContractApiMessage(
        performative=ContractApiMessage.Performative.GET_STATE,
        dialogue_reference=contract_api_dialogues.new_self_initiated_dialogue_reference(),
        ledger_id=ETHEREUM,
        contract_id="fetchai/erc1155:0.6.0",
        contract_address=contract_address,
        callable="get_balance",
        kwargs=ContractApiMessage.Kwargs(
            {"agent_address": address, "token_id": token_id}
        ),
    )
    request.counterparty = str(ledger_apis_connection.connection_id)
    contract_api_dialogue = contract_api_dialogues.update(request)
    assert contract_api_dialogue is not None
    envelope = Envelope(
        to=str(ledger_apis_connection.connection_id),
        sender=address,
        protocol_id=request.protocol_id,
        message=request,
    )

    with unittest.mock.patch(
        "inspect.getfullargspec", side_effect=Exception("Generic error")
    ):
        with unittest.mock.patch.object(
            ledger_apis_connection._logger, "error"
        ) as mock_logger:
            await ledger_apis_connection.send(envelope)
            await asyncio.sleep(0.01)
            response = await ledger_apis_connection.receive()
            mock_logger.assert_any_call(
                "An error occurred while processing the contract api request: 'Generic error'."
            )
            assert (
                response.message.performative == ContractApiMessage.Performative.ERROR
            )
            assert response.message.message == "Generic error"
