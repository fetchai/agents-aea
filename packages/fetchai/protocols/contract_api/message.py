# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2020 fetchai
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

"""This module contains contract_api's message definition."""

import logging
from enum import Enum
from typing import Optional, Set, Tuple, cast

from aea.configurations.base import ProtocolId
from aea.protocols.base import Message

from packages.fetchai.protocols.contract_api.custom_types import Kwargs as CustomKwargs
from packages.fetchai.protocols.contract_api.custom_types import (
    RawMessage as CustomRawMessage,
)
from packages.fetchai.protocols.contract_api.custom_types import (
    RawTransaction as CustomRawTransaction,
)
from packages.fetchai.protocols.contract_api.custom_types import State as CustomState

logger = logging.getLogger("aea.packages.fetchai.protocols.contract_api.message")

DEFAULT_BODY_SIZE = 4


class ContractApiMessage(Message):
    """A protocol for contract APIs requests and responses."""

    protocol_id = ProtocolId("fetchai", "contract_api", "0.1.0")

    Kwargs = CustomKwargs

    RawMessage = CustomRawMessage

    RawTransaction = CustomRawTransaction

    State = CustomState

    class Performative(Enum):
        """Performatives for the contract_api protocol."""

        ERROR = "error"
        GET_DEPLOY_TRANSACTION = "get_deploy_transaction"
        GET_RAW_MESSAGE = "get_raw_message"
        GET_RAW_TRANSACTION = "get_raw_transaction"
        GET_STATE = "get_state"
        RAW_MESSAGE = "raw_message"
        RAW_TRANSACTION = "raw_transaction"
        STATE = "state"

        def __str__(self):
            """Get the string representation."""
            return str(self.value)

    def __init__(
        self,
        performative: Performative,
        dialogue_reference: Tuple[str, str] = ("", ""),
        message_id: int = 1,
        target: int = 0,
        **kwargs,
    ):
        """
        Initialise an instance of ContractApiMessage.

        :param message_id: the message id.
        :param dialogue_reference: the dialogue reference.
        :param target: the message target.
        :param performative: the message performative.
        """
        super().__init__(
            dialogue_reference=dialogue_reference,
            message_id=message_id,
            target=target,
            performative=ContractApiMessage.Performative(performative),
            **kwargs,
        )
        self._performatives = {
            "error",
            "get_deploy_transaction",
            "get_raw_message",
            "get_raw_transaction",
            "get_state",
            "raw_message",
            "raw_transaction",
            "state",
        }

    @property
    def valid_performatives(self) -> Set[str]:
        """Get valid performatives."""
        return self._performatives

    @property
    def dialogue_reference(self) -> Tuple[str, str]:
        """Get the dialogue_reference of the message."""
        assert self.is_set("dialogue_reference"), "dialogue_reference is not set."
        return cast(Tuple[str, str], self.get("dialogue_reference"))

    @property
    def message_id(self) -> int:
        """Get the message_id of the message."""
        assert self.is_set("message_id"), "message_id is not set."
        return cast(int, self.get("message_id"))

    @property
    def performative(self) -> Performative:  # type: ignore # noqa: F821
        """Get the performative of the message."""
        assert self.is_set("performative"), "performative is not set."
        return cast(ContractApiMessage.Performative, self.get("performative"))

    @property
    def target(self) -> int:
        """Get the target of the message."""
        assert self.is_set("target"), "target is not set."
        return cast(int, self.get("target"))

    @property
    def callable(self) -> str:
        """Get the 'callable' content from the message."""
        assert self.is_set("callable"), "'callable' content is not set."
        return cast(str, self.get("callable"))

    @property
    def code(self) -> Optional[int]:
        """Get the 'code' content from the message."""
        return cast(Optional[int], self.get("code"))

    @property
    def contract_address(self) -> str:
        """Get the 'contract_address' content from the message."""
        assert self.is_set("contract_address"), "'contract_address' content is not set."
        return cast(str, self.get("contract_address"))

    @property
    def contract_id(self) -> str:
        """Get the 'contract_id' content from the message."""
        assert self.is_set("contract_id"), "'contract_id' content is not set."
        return cast(str, self.get("contract_id"))

    @property
    def data(self) -> bytes:
        """Get the 'data' content from the message."""
        assert self.is_set("data"), "'data' content is not set."
        return cast(bytes, self.get("data"))

    @property
    def kwargs(self) -> CustomKwargs:
        """Get the 'kwargs' content from the message."""
        assert self.is_set("kwargs"), "'kwargs' content is not set."
        return cast(CustomKwargs, self.get("kwargs"))

    @property
    def ledger_id(self) -> str:
        """Get the 'ledger_id' content from the message."""
        assert self.is_set("ledger_id"), "'ledger_id' content is not set."
        return cast(str, self.get("ledger_id"))

    @property
    def message(self) -> Optional[str]:
        """Get the 'message' content from the message."""
        return cast(Optional[str], self.get("message"))

    @property
    def raw_message(self) -> CustomRawMessage:
        """Get the 'raw_message' content from the message."""
        assert self.is_set("raw_message"), "'raw_message' content is not set."
        return cast(CustomRawMessage, self.get("raw_message"))

    @property
    def raw_transaction(self) -> CustomRawTransaction:
        """Get the 'raw_transaction' content from the message."""
        assert self.is_set("raw_transaction"), "'raw_transaction' content is not set."
        return cast(CustomRawTransaction, self.get("raw_transaction"))

    @property
    def state(self) -> CustomState:
        """Get the 'state' content from the message."""
        assert self.is_set("state"), "'state' content is not set."
        return cast(CustomState, self.get("state"))

    def _is_consistent(self) -> bool:
        """Check that the message follows the contract_api protocol."""
        try:
            assert (
                type(self.dialogue_reference) == tuple
            ), "Invalid type for 'dialogue_reference'. Expected 'tuple'. Found '{}'.".format(
                type(self.dialogue_reference)
            )
            assert (
                type(self.dialogue_reference[0]) == str
            ), "Invalid type for 'dialogue_reference[0]'. Expected 'str'. Found '{}'.".format(
                type(self.dialogue_reference[0])
            )
            assert (
                type(self.dialogue_reference[1]) == str
            ), "Invalid type for 'dialogue_reference[1]'. Expected 'str'. Found '{}'.".format(
                type(self.dialogue_reference[1])
            )
            assert (
                type(self.message_id) == int
            ), "Invalid type for 'message_id'. Expected 'int'. Found '{}'.".format(
                type(self.message_id)
            )
            assert (
                type(self.target) == int
            ), "Invalid type for 'target'. Expected 'int'. Found '{}'.".format(
                type(self.target)
            )

            # Light Protocol Rule 2
            # Check correct performative
            assert (
                type(self.performative) == ContractApiMessage.Performative
            ), "Invalid 'performative'. Expected either of '{}'. Found '{}'.".format(
                self.valid_performatives, self.performative
            )

            # Check correct contents
            actual_nb_of_contents = len(self.body) - DEFAULT_BODY_SIZE
            expected_nb_of_contents = 0
            if (
                self.performative
                == ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION
            ):
                expected_nb_of_contents = 4
                assert (
                    type(self.ledger_id) == str
                ), "Invalid type for content 'ledger_id'. Expected 'str'. Found '{}'.".format(
                    type(self.ledger_id)
                )
                assert (
                    type(self.contract_id) == str
                ), "Invalid type for content 'contract_id'. Expected 'str'. Found '{}'.".format(
                    type(self.contract_id)
                )
                assert (
                    type(self.callable) == str
                ), "Invalid type for content 'callable'. Expected 'str'. Found '{}'.".format(
                    type(self.callable)
                )
                assert (
                    type(self.kwargs) == CustomKwargs
                ), "Invalid type for content 'kwargs'. Expected 'Kwargs'. Found '{}'.".format(
                    type(self.kwargs)
                )
            elif (
                self.performative == ContractApiMessage.Performative.GET_RAW_TRANSACTION
            ):
                expected_nb_of_contents = 5
                assert (
                    type(self.ledger_id) == str
                ), "Invalid type for content 'ledger_id'. Expected 'str'. Found '{}'.".format(
                    type(self.ledger_id)
                )
                assert (
                    type(self.contract_id) == str
                ), "Invalid type for content 'contract_id'. Expected 'str'. Found '{}'.".format(
                    type(self.contract_id)
                )
                assert (
                    type(self.contract_address) == str
                ), "Invalid type for content 'contract_address'. Expected 'str'. Found '{}'.".format(
                    type(self.contract_address)
                )
                assert (
                    type(self.callable) == str
                ), "Invalid type for content 'callable'. Expected 'str'. Found '{}'.".format(
                    type(self.callable)
                )
                assert (
                    type(self.kwargs) == CustomKwargs
                ), "Invalid type for content 'kwargs'. Expected 'Kwargs'. Found '{}'.".format(
                    type(self.kwargs)
                )
            elif self.performative == ContractApiMessage.Performative.GET_RAW_MESSAGE:
                expected_nb_of_contents = 5
                assert (
                    type(self.ledger_id) == str
                ), "Invalid type for content 'ledger_id'. Expected 'str'. Found '{}'.".format(
                    type(self.ledger_id)
                )
                assert (
                    type(self.contract_id) == str
                ), "Invalid type for content 'contract_id'. Expected 'str'. Found '{}'.".format(
                    type(self.contract_id)
                )
                assert (
                    type(self.contract_address) == str
                ), "Invalid type for content 'contract_address'. Expected 'str'. Found '{}'.".format(
                    type(self.contract_address)
                )
                assert (
                    type(self.callable) == str
                ), "Invalid type for content 'callable'. Expected 'str'. Found '{}'.".format(
                    type(self.callable)
                )
                assert (
                    type(self.kwargs) == CustomKwargs
                ), "Invalid type for content 'kwargs'. Expected 'Kwargs'. Found '{}'.".format(
                    type(self.kwargs)
                )
            elif self.performative == ContractApiMessage.Performative.GET_STATE:
                expected_nb_of_contents = 5
                assert (
                    type(self.ledger_id) == str
                ), "Invalid type for content 'ledger_id'. Expected 'str'. Found '{}'.".format(
                    type(self.ledger_id)
                )
                assert (
                    type(self.contract_id) == str
                ), "Invalid type for content 'contract_id'. Expected 'str'. Found '{}'.".format(
                    type(self.contract_id)
                )
                assert (
                    type(self.contract_address) == str
                ), "Invalid type for content 'contract_address'. Expected 'str'. Found '{}'.".format(
                    type(self.contract_address)
                )
                assert (
                    type(self.callable) == str
                ), "Invalid type for content 'callable'. Expected 'str'. Found '{}'.".format(
                    type(self.callable)
                )
                assert (
                    type(self.kwargs) == CustomKwargs
                ), "Invalid type for content 'kwargs'. Expected 'Kwargs'. Found '{}'.".format(
                    type(self.kwargs)
                )
            elif self.performative == ContractApiMessage.Performative.STATE:
                expected_nb_of_contents = 1
                assert (
                    type(self.state) == CustomState
                ), "Invalid type for content 'state'. Expected 'State'. Found '{}'.".format(
                    type(self.state)
                )
            elif self.performative == ContractApiMessage.Performative.RAW_TRANSACTION:
                expected_nb_of_contents = 1
                assert (
                    type(self.raw_transaction) == CustomRawTransaction
                ), "Invalid type for content 'raw_transaction'. Expected 'RawTransaction'. Found '{}'.".format(
                    type(self.raw_transaction)
                )
            elif self.performative == ContractApiMessage.Performative.RAW_MESSAGE:
                expected_nb_of_contents = 1
                assert (
                    type(self.raw_message) == CustomRawMessage
                ), "Invalid type for content 'raw_message'. Expected 'RawMessage'. Found '{}'.".format(
                    type(self.raw_message)
                )
            elif self.performative == ContractApiMessage.Performative.ERROR:
                expected_nb_of_contents = 1
                if self.is_set("code"):
                    expected_nb_of_contents += 1
                    code = cast(int, self.code)
                    assert (
                        type(code) == int
                    ), "Invalid type for content 'code'. Expected 'int'. Found '{}'.".format(
                        type(code)
                    )
                if self.is_set("message"):
                    expected_nb_of_contents += 1
                    message = cast(str, self.message)
                    assert (
                        type(message) == str
                    ), "Invalid type for content 'message'. Expected 'str'. Found '{}'.".format(
                        type(message)
                    )
                assert (
                    type(self.data) == bytes
                ), "Invalid type for content 'data'. Expected 'bytes'. Found '{}'.".format(
                    type(self.data)
                )

            # Check correct content count
            assert (
                expected_nb_of_contents == actual_nb_of_contents
            ), "Incorrect number of contents. Expected {}. Found {}".format(
                expected_nb_of_contents, actual_nb_of_contents
            )

            # Light Protocol Rule 3
            if self.message_id == 1:
                assert (
                    self.target == 0
                ), "Invalid 'target'. Expected 0 (because 'message_id' is 1). Found {}.".format(
                    self.target
                )
            else:
                assert (
                    0 < self.target < self.message_id
                ), "Invalid 'target'. Expected an integer between 1 and {} inclusive. Found {}.".format(
                    self.message_id - 1, self.target,
                )
        except (AssertionError, ValueError, KeyError) as e:
            logger.error(str(e))
            return False

        return True
