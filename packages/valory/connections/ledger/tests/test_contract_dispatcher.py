# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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

"""This module contains the tests of the ledger connection module."""

from unittest import mock
from unittest.mock import ANY, MagicMock, Mock, patch

import pytest
from aea_ledger_ethereum import EthereumCrypto

from aea.common import Address
from aea.crypto.ledger_apis import ETHEREUM_DEFAULT_ADDRESS
from aea.crypto.registries import ledger_apis_registry
from aea.exceptions import AEAException
from aea.helpers.async_utils import AsyncState
from aea.multiplexer import MultiplexerStatus
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue

from packages.valory.connections.ledger.contract_dispatcher import (
    ContractApiRequestDispatcher,
)

# pylint: skip-file
from packages.valory.protocols.contract_api import ContractApiMessage
from packages.valory.protocols.contract_api.dialogues import ContractApiDialogue
from packages.valory.protocols.contract_api.dialogues import (
    ContractApiDialogues as BaseContractApiDialogues,
)


SOME_SKILL_ID = "some/skill:0.1.0"
NON_BLOCKING_TIME = 1
BLOCKING_TIME = 100
TOLERANCE = 1
WAIT_TIME_AMONG_TASKS = 0.1


class ContractApiDialogues(BaseContractApiDialogues):
    """This class keeps track of all contract_api dialogues."""

    def __init__(self, self_address: str) -> None:
        """
        Initialize dialogues.

        :param self_address: the address of the entity for whom dialogues are maintained
        """

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> Dialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            return ContractApiDialogue.Role.AGENT

        BaseContractApiDialogues.__init__(
            self,
            self_address=self_address,
            role_from_first_message=role_from_first_message,
        )


def test_validate_and_call_callable() -> None:
    """Tests a default method call through ContractApiRequestDispatcher."""

    dummy_address = "0x0000000000000000000000000000000000000000"
    contract_dispatcher = ContractApiRequestDispatcher(
        connection_id=Mock(), connection_state=AsyncState()
    )
    contract = Mock()

    def getAddress(ledger_api=None, contract_address=None, _addr=None):  # type: ignore
        return 0

    contract.getAddress = getAddress
    contract.dummy_method = None
    contract_instance = Mock()
    contract.get_instance.return_value = contract_instance

    ledger_api = ledger_apis_registry.make(
        EthereumCrypto.identifier,
        address=ETHEREUM_DEFAULT_ADDRESS,
    )

    message = MagicMock()
    message.performative = ContractApiMessage.Performative.GET_STATE
    message.kwargs.body = {"_addr": dummy_address}

    message.contract_address = dummy_address

    message.callable = "some"
    contract.some = None
    contract.default_method_call = lambda x, y, z, _addr: 12
    contract.get_state = Mock(side_effect=AttributeError())
    with patch.object(
        contract_dispatcher.contract_registry, "make", return_value=contract
    ):
        assert (
            contract_dispatcher.dispatch_request(
                dialogue=Mock(),
                ledger_api=ledger_api,
                message=message,
                response_builder=lambda x, y: 12,  # type: ignore
            )
            == 12
        )

    contract.some = Mock(side_effect=AEAException("expected"))
    dialogue = Mock()
    dialogue.reply = Mock(return_value=1234)
    with patch.object(
        contract_dispatcher.contract_registry, "make", return_value=contract
    ):
        assert (
            contract_dispatcher.dispatch_request(
                dialogue=dialogue,
                ledger_api=ledger_api,
                message=message,
                response_builder=lambda x, y: 12,  # type: ignore
            )
            == 1234
        )
        dialogue.reply.assert_called_once_with(
            performative=ContractApiMessage.Performative.ERROR,
            target_message=ANY,
            code=500,
            message=ANY,
            data=ANY,
        )

    message.callable = "getAddress"
    # Call a method present in the ABI but not in the contract package
    with mock.patch("web3.contract.ContractFunction.call", return_value=0):
        result = ContractApiRequestDispatcher._validate_and_call_callable(
            ledger_api, message, contract
        )
        assert result == 0

    # Call an non-existent method
    message.callable = "dummy_method"
    contract_instance.get_function_by_name = Mock(side_effect=ValueError())
    with pytest.raises(
        AEAException,
        match=f"Contract method dummy_method not found in ABI of contract {type(contract)}",
    ):
        ContractApiRequestDispatcher._validate_and_call_callable(
            ledger_api, message, contract
        )

    message.performative = None
    message.callable = "getAddress"
    with pytest.raises(AEAException, match="Unexpected performative:"):
        ContractApiRequestDispatcher._validate_and_call_callable(
            ledger_api, message, contract
        )

    message.callable = "some_fn"
    message.performative = ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION
    contract.some_fn = lambda x: None
    with pytest.raises(AEAException, match="Missing required argument `ledger_api`"):
        ContractApiRequestDispatcher._validate_and_call_callable(
            ledger_api, message, contract
        )

    contract.some_fn = lambda: None
    with pytest.raises(
        AEAException, match="Expected one or more positional arguments, got 0"
    ):
        ContractApiRequestDispatcher._validate_and_call_callable(
            ledger_api, message, contract
        )

    contract.some_fn = lambda ledger_api, _addr: None
    ContractApiRequestDispatcher._validate_and_call_callable(
        ledger_api, message, contract
    )

    with pytest.raises(
        AttributeError,
    ):
        ContractApiRequestDispatcher._validate_and_call_callable(
            ledger_api, message, None  # type: ignore
        )


def test_build_response_fails_on_bad_data_type() -> None:
    """Test internal build_response functions for data type check."""
    dispatcher = ContractApiRequestDispatcher(MagicMock(), connection_id="test_id")
    with patch.object(
        dispatcher,
        "dispatch_request",
        lambda x, x1, x2, fn: fn(data=b"some_data", dialogue=MagicMock()),
    ), pytest.raises(
        ValueError, match=r"Invalid state type, got=<class '.+'>, expected=typing.Dict"
    ):
        dispatcher.get_state(MagicMock(), MagicMock(), MagicMock())

    with patch.object(
        dispatcher,
        "dispatch_request",
        lambda x, x1, x2, fn: fn(raw_message=12, dialogue=MagicMock()),
    ), pytest.raises(ValueError, match=r"Invalid message type"):
        dispatcher.get_raw_message(MagicMock(), MagicMock(), MagicMock())

    with patch.object(
        dispatcher,
        "dispatch_request",
        lambda x, x1, x2, fn: fn(transaction=b"some_data", dialogue=MagicMock()),
    ):
        with pytest.raises(
            ValueError,
            match=r"Invalid transaction type, got=<class '.+'>, expected=typing.Dict",
        ):
            dispatcher.get_deploy_transaction(MagicMock(), MagicMock(), MagicMock())
        with pytest.raises(
            ValueError,
            match=r"Invalid transaction type, got=<class '.+'>, expected=typing.Dict",
        ):
            dispatcher.get_raw_transaction(MagicMock(), MagicMock(), MagicMock())


@pytest.mark.asyncio
async def test_run_async() -> None:
    """Test run async error handled."""
    # for pydocstyle
    def _raise():  # type: ignore
        raise Exception("Expected")

    contract_api_dialogues = ContractApiDialogues(SOME_SKILL_ID)
    request, dialogue = contract_api_dialogues.create(
        counterparty="str(ledger_apis_connection.connection_id)",
        performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,
        ledger_id=EthereumCrypto.identifier,
        contract_id=str(SOME_SKILL_ID),
        contract_address="test addr",
        callable="get_create_batch_transaction",
        kwargs=ContractApiMessage.Kwargs(
            {
                "deployer_address": "test_addr",
                "token_ids": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            }
        ),
    )
    api = None
    msg = await ContractApiRequestDispatcher(
        MultiplexerStatus(), connection_id="test_id"
    ).run_async(
        _raise, api, request, dialogue  # type: ignore
    )
    assert msg.performative == ContractApiMessage.Performative.ERROR  # type: ignore


@pytest.mark.asyncio
async def test_get_handler() -> None:
    """Test failed to get handler."""
    with pytest.raises(Exception, match="Performative not recognized."):
        ContractApiRequestDispatcher(
            MultiplexerStatus(), connection_id="test_id"
        ).get_handler(ContractApiMessage.Performative.ERROR)
