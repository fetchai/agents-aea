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

"""This module contains tac's message definition."""

from enum import Enum
from typing import Dict, Set, Tuple, cast

from aea.configurations.base import ProtocolId
from aea.protocols.base import Message

from packages.fetchai.protocols.tac.custom_types import ErrorCode as CustomErrorCode
from packages.fetchai.protocols.tac.custom_types import ErrorInfo as CustomErrorInfo

DEFAULT_BODY_SIZE = 4


class TacMessage(Message):
    """A protocol for participating in a TAC."""

    protocol_id = ProtocolId("fetchai", "tac", "0.1.0")

    ErrorCode = CustomErrorCode

    ErrorInfo = CustomErrorInfo

    class Performative(Enum):
        """Performatives for the tac protocol."""

        CANCELLED = "cancelled"
        GAME_DATA = "game_data"
        GET_STATE_UPDATE = "get_state_update"
        REGISTER = "register"
        TAC_ERROR = "tac_error"
        TRANSACTION = "transaction"
        TRANSACTION_CONFIRMATION = "transaction_confirmation"
        UNREGISTER = "unregister"

        def __str__(self):
            """Get the string representation."""
            return self.value

    def __init__(
        self,
        dialogue_reference: Tuple[str, str],
        message_id: int,
        target: int,
        performative: Performative,
        **kwargs,
    ):
        """
        Initialise an instance of TacMessage.

        :param message_id: the message id.
        :param dialogue_reference: the dialogue reference.
        :param target: the message target.
        :param performative: the message performative.
        """
        super().__init__(
            dialogue_reference=dialogue_reference,
            message_id=message_id,
            target=target,
            performative=TacMessage.Performative(performative),
            **kwargs,
        )
        self._performatives = {
            "cancelled",
            "game_data",
            "get_state_update",
            "register",
            "tac_error",
            "transaction",
            "transaction_confirmation",
            "unregister",
        }
        assert (
            self._is_consistent()
        ), "This message is invalid according to the 'tac' protocol."

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
    def performative(self) -> Performative:  # noqa: F821
        """Get the performative of the message."""
        assert self.is_set("performative"), "performative is not set."
        return cast(TacMessage.Performative, self.get("performative"))

    @property
    def target(self) -> int:
        """Get the target of the message."""
        assert self.is_set("target"), "target is not set."
        return cast(int, self.get("target"))

    @property
    def agent_addr_to_name(self) -> Dict[str, str]:
        """Get the 'agent_addr_to_name' content from the message."""
        assert self.is_set(
            "agent_addr_to_name"
        ), "'agent_addr_to_name' content is not set."
        return cast(Dict[str, str], self.get("agent_addr_to_name"))

    @property
    def agent_name(self) -> str:
        """Get the 'agent_name' content from the message."""
        assert self.is_set("agent_name"), "'agent_name' content is not set."
        return cast(str, self.get("agent_name"))

    @property
    def amount_by_currency_id(self) -> Dict[str, int]:
        """Get the 'amount_by_currency_id' content from the message."""
        assert self.is_set(
            "amount_by_currency_id"
        ), "'amount_by_currency_id' content is not set."
        return cast(Dict[str, int], self.get("amount_by_currency_id"))

    @property
    def error_code(self) -> CustomErrorCode:
        """Get the 'error_code' content from the message."""
        assert self.is_set("error_code"), "'error_code' content is not set."
        return cast(CustomErrorCode, self.get("error_code"))

    @property
    def exchange_params_by_currency_id(self) -> Dict[str, float]:
        """Get the 'exchange_params_by_currency_id' content from the message."""
        assert self.is_set(
            "exchange_params_by_currency_id"
        ), "'exchange_params_by_currency_id' content is not set."
        return cast(Dict[str, float], self.get("exchange_params_by_currency_id"))

    @property
    def good_id_to_name(self) -> Dict[str, str]:
        """Get the 'good_id_to_name' content from the message."""
        assert self.is_set("good_id_to_name"), "'good_id_to_name' content is not set."
        return cast(Dict[str, str], self.get("good_id_to_name"))

    @property
    def info(self) -> Dict[str, CustomErrorInfo]:
        """Get the 'info' content from the message."""
        assert self.is_set("info"), "'info' content is not set."
        return cast(Dict[str, CustomErrorInfo], self.get("info"))

    @property
    def quantities_by_good_id(self) -> Dict[str, int]:
        """Get the 'quantities_by_good_id' content from the message."""
        assert self.is_set(
            "quantities_by_good_id"
        ), "'quantities_by_good_id' content is not set."
        return cast(Dict[str, int], self.get("quantities_by_good_id"))

    @property
    def tx_counterparty_addr(self) -> str:
        """Get the 'tx_counterparty_addr' content from the message."""
        assert self.is_set(
            "tx_counterparty_addr"
        ), "'tx_counterparty_addr' content is not set."
        return cast(str, self.get("tx_counterparty_addr"))

    @property
    def tx_counterparty_fee(self) -> int:
        """Get the 'tx_counterparty_fee' content from the message."""
        assert self.is_set(
            "tx_counterparty_fee"
        ), "'tx_counterparty_fee' content is not set."
        return cast(int, self.get("tx_counterparty_fee"))

    @property
    def tx_counterparty_signature(self) -> bytes:
        """Get the 'tx_counterparty_signature' content from the message."""
        assert self.is_set(
            "tx_counterparty_signature"
        ), "'tx_counterparty_signature' content is not set."
        return cast(bytes, self.get("tx_counterparty_signature"))

    @property
    def tx_fee(self) -> int:
        """Get the 'tx_fee' content from the message."""
        assert self.is_set("tx_fee"), "'tx_fee' content is not set."
        return cast(int, self.get("tx_fee"))

    @property
    def tx_id(self) -> str:
        """Get the 'tx_id' content from the message."""
        assert self.is_set("tx_id"), "'tx_id' content is not set."
        return cast(str, self.get("tx_id"))

    @property
    def tx_nonce(self) -> int:
        """Get the 'tx_nonce' content from the message."""
        assert self.is_set("tx_nonce"), "'tx_nonce' content is not set."
        return cast(int, self.get("tx_nonce"))

    @property
    def tx_sender_addr(self) -> str:
        """Get the 'tx_sender_addr' content from the message."""
        assert self.is_set("tx_sender_addr"), "'tx_sender_addr' content is not set."
        return cast(str, self.get("tx_sender_addr"))

    @property
    def tx_sender_fee(self) -> int:
        """Get the 'tx_sender_fee' content from the message."""
        assert self.is_set("tx_sender_fee"), "'tx_sender_fee' content is not set."
        return cast(int, self.get("tx_sender_fee"))

    @property
    def tx_sender_signature(self) -> bytes:
        """Get the 'tx_sender_signature' content from the message."""
        assert self.is_set(
            "tx_sender_signature"
        ), "'tx_sender_signature' content is not set."
        return cast(bytes, self.get("tx_sender_signature"))

    @property
    def utility_params_by_good_id(self) -> Dict[str, float]:
        """Get the 'utility_params_by_good_id' content from the message."""
        assert self.is_set(
            "utility_params_by_good_id"
        ), "'utility_params_by_good_id' content is not set."
        return cast(Dict[str, float], self.get("utility_params_by_good_id"))

    @property
    def version_id(self) -> str:
        """Get the 'version_id' content from the message."""
        assert self.is_set("version_id"), "'version_id' content is not set."
        return cast(str, self.get("version_id"))

    def _is_consistent(self) -> bool:
        """Check that the message follows the tac protocol."""
        try:
            assert (
                type(self.dialogue_reference) == tuple
            ), "dialogue_reference must be 'tuple' but it is not."
            assert (
                type(self.dialogue_reference[0]) == str
            ), "The first element of dialogue_reference must be 'str' but it is not."
            assert (
                type(self.dialogue_reference[1]) == str
            ), "The second element of dialogue_reference must be 'str' but it is not."
            assert type(self.message_id) == int, "message_id is not int"
            assert type(self.target) == int, "target is not int"

            # Light Protocol Rule 2
            # Check correct performative
            assert (
                type(self.performative) == TacMessage.Performative
            ), "'{}' is not in the list of valid performatives: {}".format(
                self.performative, self.valid_performatives
            )

            # Check correct contents
            actual_nb_of_contents = len(self.body) - DEFAULT_BODY_SIZE
            expected_nb_of_contents = 0
            if self.performative == TacMessage.Performative.REGISTER:
                expected_nb_of_contents = 1
                assert (
                    type(self.agent_name) == str
                ), "Content 'agent_name' is not of type 'str'."
            elif self.performative == TacMessage.Performative.UNREGISTER:
                expected_nb_of_contents = 0
            elif self.performative == TacMessage.Performative.TRANSACTION:
                expected_nb_of_contents = 10
                assert type(self.tx_id) == str, "Content 'tx_id' is not of type 'str'."
                assert (
                    type(self.tx_sender_addr) == str
                ), "Content 'tx_sender_addr' is not of type 'str'."
                assert (
                    type(self.tx_counterparty_addr) == str
                ), "Content 'tx_counterparty_addr' is not of type 'str'."
                assert (
                    type(self.amount_by_currency_id) == dict
                ), "Content 'amount_by_currency_id' is not of type 'dict'."
                for key, value in self.amount_by_currency_id.items():
                    assert (
                        type(key) == str
                    ), "Keys of 'amount_by_currency_id' dictionary are not of type 'str'."
                    assert (
                        type(value) == int
                    ), "Values of 'amount_by_currency_id' dictionary are not of type 'int'."
                assert (
                    type(self.tx_sender_fee) == int
                ), "Content 'tx_sender_fee' is not of type 'int'."
                assert (
                    type(self.tx_counterparty_fee) == int
                ), "Content 'tx_counterparty_fee' is not of type 'int'."
                assert (
                    type(self.quantities_by_good_id) == dict
                ), "Content 'quantities_by_good_id' is not of type 'dict'."
                for key, value in self.quantities_by_good_id.items():
                    assert (
                        type(key) == str
                    ), "Keys of 'quantities_by_good_id' dictionary are not of type 'str'."
                    assert (
                        type(value) == int
                    ), "Values of 'quantities_by_good_id' dictionary are not of type 'int'."
                assert (
                    type(self.tx_nonce) == int
                ), "Content 'tx_nonce' is not of type 'int'."
                assert (
                    type(self.tx_sender_signature) == bytes
                ), "Content 'tx_sender_signature' is not of type 'bytes'."
                assert (
                    type(self.tx_counterparty_signature) == bytes
                ), "Content 'tx_counterparty_signature' is not of type 'bytes'."
            elif self.performative == TacMessage.Performative.GET_STATE_UPDATE:
                expected_nb_of_contents = 0
            elif self.performative == TacMessage.Performative.CANCELLED:
                expected_nb_of_contents = 0
            elif self.performative == TacMessage.Performative.GAME_DATA:
                expected_nb_of_contents = 8
                assert (
                    type(self.amount_by_currency_id) == dict
                ), "Content 'amount_by_currency_id' is not of type 'dict'."
                for key, value in self.amount_by_currency_id.items():
                    assert (
                        type(key) == str
                    ), "Keys of 'amount_by_currency_id' dictionary are not of type 'str'."
                    assert (
                        type(value) == int
                    ), "Values of 'amount_by_currency_id' dictionary are not of type 'int'."
                assert (
                    type(self.exchange_params_by_currency_id) == dict
                ), "Content 'exchange_params_by_currency_id' is not of type 'dict'."
                for key, value in self.exchange_params_by_currency_id.items():
                    assert (
                        type(key) == str
                    ), "Keys of 'exchange_params_by_currency_id' dictionary are not of type 'str'."
                    assert (
                        type(value) == float
                    ), "Values of 'exchange_params_by_currency_id' dictionary are not of type 'float'."
                assert (
                    type(self.quantities_by_good_id) == dict
                ), "Content 'quantities_by_good_id' is not of type 'dict'."
                for key, value in self.quantities_by_good_id.items():
                    assert (
                        type(key) == str
                    ), "Keys of 'quantities_by_good_id' dictionary are not of type 'str'."
                    assert (
                        type(value) == int
                    ), "Values of 'quantities_by_good_id' dictionary are not of type 'int'."
                assert (
                    type(self.utility_params_by_good_id) == dict
                ), "Content 'utility_params_by_good_id' is not of type 'dict'."
                for key, value in self.utility_params_by_good_id.items():
                    assert (
                        type(key) == str
                    ), "Keys of 'utility_params_by_good_id' dictionary are not of type 'str'."
                    assert (
                        type(value) == float
                    ), "Values of 'utility_params_by_good_id' dictionary are not of type 'float'."
                assert (
                    type(self.tx_fee) == int
                ), "Content 'tx_fee' is not of type 'int'."
                assert (
                    type(self.agent_addr_to_name) == dict
                ), "Content 'agent_addr_to_name' is not of type 'dict'."
                for key, value in self.agent_addr_to_name.items():
                    assert (
                        type(key) == str
                    ), "Keys of 'agent_addr_to_name' dictionary are not of type 'str'."
                    assert (
                        type(value) == str
                    ), "Values of 'agent_addr_to_name' dictionary are not of type 'str'."
                assert (
                    type(self.good_id_to_name) == dict
                ), "Content 'good_id_to_name' is not of type 'dict'."
                for key, value in self.good_id_to_name.items():
                    assert (
                        type(key) == str
                    ), "Keys of 'good_id_to_name' dictionary are not of type 'str'."
                    assert (
                        type(value) == str
                    ), "Values of 'good_id_to_name' dictionary are not of type 'str'."
                assert (
                    type(self.version_id) == str
                ), "Content 'version_id' is not of type 'str'."
            elif self.performative == TacMessage.Performative.TRANSACTION_CONFIRMATION:
                expected_nb_of_contents = 3
                assert type(self.tx_id) == str, "Content 'tx_id' is not of type 'str'."
                assert (
                    type(self.amount_by_currency_id) == dict
                ), "Content 'amount_by_currency_id' is not of type 'dict'."
                for key, value in self.amount_by_currency_id.items():
                    assert (
                        type(key) == str
                    ), "Keys of 'amount_by_currency_id' dictionary are not of type 'str'."
                    assert (
                        type(value) == int
                    ), "Values of 'amount_by_currency_id' dictionary are not of type 'int'."
                assert (
                    type(self.quantities_by_good_id) == dict
                ), "Content 'quantities_by_good_id' is not of type 'dict'."
                for key, value in self.quantities_by_good_id.items():
                    assert (
                        type(key) == str
                    ), "Keys of 'quantities_by_good_id' dictionary are not of type 'str'."
                    assert (
                        type(value) == int
                    ), "Values of 'quantities_by_good_id' dictionary are not of type 'int'."
            elif self.performative == TacMessage.Performative.TAC_ERROR:
                expected_nb_of_contents = 2
                assert (
                    type(self.error_code) == CustomErrorCode
                ), "Content 'error_code' is not of type 'ErrorCode'."
                assert type(self.info) == dict, "Content 'info' is not of type 'dict'."
                for key, value in self.info.items():
                    assert (
                        type(key) == str
                    ), "Keys of 'info' dictionary are not of type 'str'."
                    assert (
                        type(value) == CustomErrorInfo
                    ), "Values of 'info' dictionary are not of type 'ErrorInfo'."

            # Check correct content count
            assert (
                expected_nb_of_contents == actual_nb_of_contents
            ), "Incorrect number of contents. Expected {} contents. Found {}".format(
                expected_nb_of_contents, actual_nb_of_contents
            )

            # Light Protocol Rule 3
            if self.message_id == 1:
                assert (
                    self.target == 0
                ), "Expected target to be 0 when message_id is 1. Found {}.".format(
                    self.target
                )
            else:
                assert (
                    0 < self.target < self.message_id
                ), "Expected target to be between 1 to (message_id -1) inclusive. Found {}".format(
                    self.target
                )
        except (AssertionError, ValueError, KeyError) as e:
            print(str(e))
            return False

        return True
