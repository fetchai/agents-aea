# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 valory
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

"""Test messages module for contract_api protocol."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,redefined-builtin
from typing import List

from aea.test_tools.test_protocol import BaseProtocolMessagesTestCase

from packages.valory.protocols.contract_api.custom_types import (
    Kwargs,
    RawMessage,
    RawTransaction,
    State,
)
from packages.valory.protocols.contract_api.message import ContractApiMessage


class TestMessageContractApi(BaseProtocolMessagesTestCase):
    """Test for the 'contract_api' protocol message."""

    MESSAGE_CLASS = ContractApiMessage

    def build_messages(self) -> List[ContractApiMessage]:  # type: ignore[override]
        """Build the messages to be used for testing."""
        return [
            ContractApiMessage(
                performative=ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION,
                ledger_id="some str",
                contract_id="some str",
                callable="some str",
                kwargs=Kwargs({"key_1": 1, "key_2": 2}),
            ),
            ContractApiMessage(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,
                ledger_id="some str",
                contract_id="some str",
                contract_address="some str",
                callable="some str",
                kwargs=Kwargs({"key_1": 1, "key_2": 2}),
            ),
            ContractApiMessage(
                performative=ContractApiMessage.Performative.GET_RAW_MESSAGE,
                ledger_id="some str",
                contract_id="some str",
                contract_address="some str",
                callable="some str",
                kwargs=Kwargs({"key_1": 1, "key_2": 2}),
            ),
            ContractApiMessage(
                performative=ContractApiMessage.Performative.GET_STATE,
                ledger_id="some str",
                contract_id="some str",
                contract_address="some str",
                callable="some str",
                kwargs=Kwargs({"key_1": 1, "key_2": 2}),
            ),
            ContractApiMessage(
                performative=ContractApiMessage.Performative.STATE,
                state=State("some_ledger_id", {"key": "some_body"}),
            ),
            ContractApiMessage(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                raw_transaction=RawTransaction("some_ledger_id", {"body": "some_body"}),
            ),
            ContractApiMessage(
                performative=ContractApiMessage.Performative.RAW_MESSAGE,
                raw_message=RawMessage("some_ledger_id", b"some_body"),
            ),
            ContractApiMessage(
                performative=ContractApiMessage.Performative.ERROR,
                code=12,
                message="some str",
                data=b"some_bytes",
            ),
        ]

    def build_inconsistent(self) -> List[ContractApiMessage]:  # type: ignore[override]
        """Build inconsistent messages to be used for testing."""
        return [
            ContractApiMessage(
                performative=ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION,
                # skip content: ledger_id
                contract_id="some str",
                callable="some str",
                kwargs=Kwargs({"key_1": 1, "key_2": 2}),
            ),
            ContractApiMessage(
                performative=ContractApiMessage.Performative.GET_RAW_TRANSACTION,
                # skip content: ledger_id
                contract_id="some str",
                contract_address="some str",
                callable="some str",
                kwargs=Kwargs({"key_1": 1, "key_2": 2}),
            ),
            ContractApiMessage(
                performative=ContractApiMessage.Performative.GET_RAW_MESSAGE,
                # skip content: ledger_id
                contract_id="some str",
                contract_address="some str",
                callable="some str",
                kwargs=Kwargs({"key_1": 1, "key_2": 2}),
            ),
            ContractApiMessage(
                performative=ContractApiMessage.Performative.GET_STATE,
                # skip content: ledger_id
                contract_id="some str",
                contract_address="some str",
                callable="some str",
                kwargs=Kwargs({"key_1": 1, "key_2": 2}),
            ),
            ContractApiMessage(
                performative=ContractApiMessage.Performative.STATE,
                # skip content: state
            ),
            ContractApiMessage(
                performative=ContractApiMessage.Performative.RAW_TRANSACTION,
                # skip content: raw_transaction
            ),
            ContractApiMessage(
                performative=ContractApiMessage.Performative.RAW_MESSAGE,
                # skip content: raw_message
            ),
            ContractApiMessage(
                performative=ContractApiMessage.Performative.ERROR,
                # skip content: code
                message=["some str"],
                data=b"some_bytes",
            ),
        ]
