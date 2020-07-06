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

import logging
from enum import Enum
from typing import Dict, Optional, Set, Tuple, cast

from aea.configurations.base import ProtocolId
from aea.protocols.base import Message

from packages.fetchai.protocols.tac.custom_types import ErrorCode as CustomErrorCode

logger = logging.getLogger("aea.packages.fetchai.protocols.tac.message")

DEFAULT_BODY_SIZE = 4


class TacMessage(Message):
    """The tac protocol implements the messages an AEA needs to participate in the TAC."""

    protocol_id = ProtocolId("fetchai", "tac", "0.3.0")

    ErrorCode = CustomErrorCode

    class Performative(Enum):
        """Performatives for the tac protocol."""

        CANCELLED = "cancelled"
        GAME_DATA = "game_data"
        REGISTER = "register"
        TAC_ERROR = "tac_error"
        TRANSACTION = "transaction"
        TRANSACTION_CONFIRMATION = "transaction_confirmation"
        UNREGISTER = "unregister"

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
            "register",
            "tac_error",
            "transaction",
            "transaction_confirmation",
            "unregister",
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
    def currency_id_to_name(self) -> Dict[str, str]:
        """Get the 'currency_id_to_name' content from the message."""
        assert self.is_set(
            "currency_id_to_name"
        ), "'currency_id_to_name' content is not set."
        return cast(Dict[str, str], self.get("currency_id_to_name"))

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
    def info(self) -> Optional[Dict[str, str]]:
        """Get the 'info' content from the message."""
        return cast(Optional[Dict[str, str]], self.get("info"))

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
    def tx_counterparty_signature(self) -> str:
        """Get the 'tx_counterparty_signature' content from the message."""
        assert self.is_set(
            "tx_counterparty_signature"
        ), "'tx_counterparty_signature' content is not set."
        return cast(str, self.get("tx_counterparty_signature"))

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
    def tx_sender_signature(self) -> str:
        """Get the 'tx_sender_signature' content from the message."""
        assert self.is_set(
            "tx_sender_signature"
        ), "'tx_sender_signature' content is not set."
        return cast(str, self.get("tx_sender_signature"))

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
                type(self.performative) == TacMessage.Performative
            ), "Invalid 'performative'. Expected either of '{}'. Found '{}'.".format(
                self.valid_performatives, self.performative
            )

            # Check correct contents
            actual_nb_of_contents = len(self.body) - DEFAULT_BODY_SIZE
            expected_nb_of_contents = 0
            if self.performative == TacMessage.Performative.REGISTER:
                expected_nb_of_contents = 1
                assert (
                    type(self.agent_name) == str
                ), "Invalid type for content 'agent_name'. Expected 'str'. Found '{}'.".format(
                    type(self.agent_name)
                )
            elif self.performative == TacMessage.Performative.UNREGISTER:
                expected_nb_of_contents = 0
            elif self.performative == TacMessage.Performative.TRANSACTION:
                expected_nb_of_contents = 10
                assert (
                    type(self.tx_id) == str
                ), "Invalid type for content 'tx_id'. Expected 'str'. Found '{}'.".format(
                    type(self.tx_id)
                )
                assert (
                    type(self.tx_sender_addr) == str
                ), "Invalid type for content 'tx_sender_addr'. Expected 'str'. Found '{}'.".format(
                    type(self.tx_sender_addr)
                )
                assert (
                    type(self.tx_counterparty_addr) == str
                ), "Invalid type for content 'tx_counterparty_addr'. Expected 'str'. Found '{}'.".format(
                    type(self.tx_counterparty_addr)
                )
                assert (
                    type(self.amount_by_currency_id) == dict
                ), "Invalid type for content 'amount_by_currency_id'. Expected 'dict'. Found '{}'.".format(
                    type(self.amount_by_currency_id)
                )
                for (
                    key_of_amount_by_currency_id,
                    value_of_amount_by_currency_id,
                ) in self.amount_by_currency_id.items():
                    assert (
                        type(key_of_amount_by_currency_id) == str
                    ), "Invalid type for dictionary keys in content 'amount_by_currency_id'. Expected 'str'. Found '{}'.".format(
                        type(key_of_amount_by_currency_id)
                    )
                    assert (
                        type(value_of_amount_by_currency_id) == int
                    ), "Invalid type for dictionary values in content 'amount_by_currency_id'. Expected 'int'. Found '{}'.".format(
                        type(value_of_amount_by_currency_id)
                    )
                assert (
                    type(self.tx_sender_fee) == int
                ), "Invalid type for content 'tx_sender_fee'. Expected 'int'. Found '{}'.".format(
                    type(self.tx_sender_fee)
                )
                assert (
                    type(self.tx_counterparty_fee) == int
                ), "Invalid type for content 'tx_counterparty_fee'. Expected 'int'. Found '{}'.".format(
                    type(self.tx_counterparty_fee)
                )
                assert (
                    type(self.quantities_by_good_id) == dict
                ), "Invalid type for content 'quantities_by_good_id'. Expected 'dict'. Found '{}'.".format(
                    type(self.quantities_by_good_id)
                )
                for (
                    key_of_quantities_by_good_id,
                    value_of_quantities_by_good_id,
                ) in self.quantities_by_good_id.items():
                    assert (
                        type(key_of_quantities_by_good_id) == str
                    ), "Invalid type for dictionary keys in content 'quantities_by_good_id'. Expected 'str'. Found '{}'.".format(
                        type(key_of_quantities_by_good_id)
                    )
                    assert (
                        type(value_of_quantities_by_good_id) == int
                    ), "Invalid type for dictionary values in content 'quantities_by_good_id'. Expected 'int'. Found '{}'.".format(
                        type(value_of_quantities_by_good_id)
                    )
                assert (
                    type(self.tx_nonce) == int
                ), "Invalid type for content 'tx_nonce'. Expected 'int'. Found '{}'.".format(
                    type(self.tx_nonce)
                )
                assert (
                    type(self.tx_sender_signature) == str
                ), "Invalid type for content 'tx_sender_signature'. Expected 'str'. Found '{}'.".format(
                    type(self.tx_sender_signature)
                )
                assert (
                    type(self.tx_counterparty_signature) == str
                ), "Invalid type for content 'tx_counterparty_signature'. Expected 'str'. Found '{}'.".format(
                    type(self.tx_counterparty_signature)
                )
            elif self.performative == TacMessage.Performative.CANCELLED:
                expected_nb_of_contents = 0
            elif self.performative == TacMessage.Performative.GAME_DATA:
                expected_nb_of_contents = 9
                assert (
                    type(self.amount_by_currency_id) == dict
                ), "Invalid type for content 'amount_by_currency_id'. Expected 'dict'. Found '{}'.".format(
                    type(self.amount_by_currency_id)
                )
                for (
                    key_of_amount_by_currency_id,
                    value_of_amount_by_currency_id,
                ) in self.amount_by_currency_id.items():
                    assert (
                        type(key_of_amount_by_currency_id) == str
                    ), "Invalid type for dictionary keys in content 'amount_by_currency_id'. Expected 'str'. Found '{}'.".format(
                        type(key_of_amount_by_currency_id)
                    )
                    assert (
                        type(value_of_amount_by_currency_id) == int
                    ), "Invalid type for dictionary values in content 'amount_by_currency_id'. Expected 'int'. Found '{}'.".format(
                        type(value_of_amount_by_currency_id)
                    )
                assert (
                    type(self.exchange_params_by_currency_id) == dict
                ), "Invalid type for content 'exchange_params_by_currency_id'. Expected 'dict'. Found '{}'.".format(
                    type(self.exchange_params_by_currency_id)
                )
                for (
                    key_of_exchange_params_by_currency_id,
                    value_of_exchange_params_by_currency_id,
                ) in self.exchange_params_by_currency_id.items():
                    assert (
                        type(key_of_exchange_params_by_currency_id) == str
                    ), "Invalid type for dictionary keys in content 'exchange_params_by_currency_id'. Expected 'str'. Found '{}'.".format(
                        type(key_of_exchange_params_by_currency_id)
                    )
                    assert (
                        type(value_of_exchange_params_by_currency_id) == float
                    ), "Invalid type for dictionary values in content 'exchange_params_by_currency_id'. Expected 'float'. Found '{}'.".format(
                        type(value_of_exchange_params_by_currency_id)
                    )
                assert (
                    type(self.quantities_by_good_id) == dict
                ), "Invalid type for content 'quantities_by_good_id'. Expected 'dict'. Found '{}'.".format(
                    type(self.quantities_by_good_id)
                )
                for (
                    key_of_quantities_by_good_id,
                    value_of_quantities_by_good_id,
                ) in self.quantities_by_good_id.items():
                    assert (
                        type(key_of_quantities_by_good_id) == str
                    ), "Invalid type for dictionary keys in content 'quantities_by_good_id'. Expected 'str'. Found '{}'.".format(
                        type(key_of_quantities_by_good_id)
                    )
                    assert (
                        type(value_of_quantities_by_good_id) == int
                    ), "Invalid type for dictionary values in content 'quantities_by_good_id'. Expected 'int'. Found '{}'.".format(
                        type(value_of_quantities_by_good_id)
                    )
                assert (
                    type(self.utility_params_by_good_id) == dict
                ), "Invalid type for content 'utility_params_by_good_id'. Expected 'dict'. Found '{}'.".format(
                    type(self.utility_params_by_good_id)
                )
                for (
                    key_of_utility_params_by_good_id,
                    value_of_utility_params_by_good_id,
                ) in self.utility_params_by_good_id.items():
                    assert (
                        type(key_of_utility_params_by_good_id) == str
                    ), "Invalid type for dictionary keys in content 'utility_params_by_good_id'. Expected 'str'. Found '{}'.".format(
                        type(key_of_utility_params_by_good_id)
                    )
                    assert (
                        type(value_of_utility_params_by_good_id) == float
                    ), "Invalid type for dictionary values in content 'utility_params_by_good_id'. Expected 'float'. Found '{}'.".format(
                        type(value_of_utility_params_by_good_id)
                    )
                assert (
                    type(self.tx_fee) == int
                ), "Invalid type for content 'tx_fee'. Expected 'int'. Found '{}'.".format(
                    type(self.tx_fee)
                )
                assert (
                    type(self.agent_addr_to_name) == dict
                ), "Invalid type for content 'agent_addr_to_name'. Expected 'dict'. Found '{}'.".format(
                    type(self.agent_addr_to_name)
                )
                for (
                    key_of_agent_addr_to_name,
                    value_of_agent_addr_to_name,
                ) in self.agent_addr_to_name.items():
                    assert (
                        type(key_of_agent_addr_to_name) == str
                    ), "Invalid type for dictionary keys in content 'agent_addr_to_name'. Expected 'str'. Found '{}'.".format(
                        type(key_of_agent_addr_to_name)
                    )
                    assert (
                        type(value_of_agent_addr_to_name) == str
                    ), "Invalid type for dictionary values in content 'agent_addr_to_name'. Expected 'str'. Found '{}'.".format(
                        type(value_of_agent_addr_to_name)
                    )
                assert (
                    type(self.currency_id_to_name) == dict
                ), "Invalid type for content 'currency_id_to_name'. Expected 'dict'. Found '{}'.".format(
                    type(self.currency_id_to_name)
                )
                for (
                    key_of_currency_id_to_name,
                    value_of_currency_id_to_name,
                ) in self.currency_id_to_name.items():
                    assert (
                        type(key_of_currency_id_to_name) == str
                    ), "Invalid type for dictionary keys in content 'currency_id_to_name'. Expected 'str'. Found '{}'.".format(
                        type(key_of_currency_id_to_name)
                    )
                    assert (
                        type(value_of_currency_id_to_name) == str
                    ), "Invalid type for dictionary values in content 'currency_id_to_name'. Expected 'str'. Found '{}'.".format(
                        type(value_of_currency_id_to_name)
                    )
                assert (
                    type(self.good_id_to_name) == dict
                ), "Invalid type for content 'good_id_to_name'. Expected 'dict'. Found '{}'.".format(
                    type(self.good_id_to_name)
                )
                for (
                    key_of_good_id_to_name,
                    value_of_good_id_to_name,
                ) in self.good_id_to_name.items():
                    assert (
                        type(key_of_good_id_to_name) == str
                    ), "Invalid type for dictionary keys in content 'good_id_to_name'. Expected 'str'. Found '{}'.".format(
                        type(key_of_good_id_to_name)
                    )
                    assert (
                        type(value_of_good_id_to_name) == str
                    ), "Invalid type for dictionary values in content 'good_id_to_name'. Expected 'str'. Found '{}'.".format(
                        type(value_of_good_id_to_name)
                    )
                assert (
                    type(self.version_id) == str
                ), "Invalid type for content 'version_id'. Expected 'str'. Found '{}'.".format(
                    type(self.version_id)
                )
                if self.is_set("info"):
                    expected_nb_of_contents += 1
                    info = cast(Dict[str, str], self.info)
                    assert (
                        type(info) == dict
                    ), "Invalid type for content 'info'. Expected 'dict'. Found '{}'.".format(
                        type(info)
                    )
                    for key_of_info, value_of_info in info.items():
                        assert (
                            type(key_of_info) == str
                        ), "Invalid type for dictionary keys in content 'info'. Expected 'str'. Found '{}'.".format(
                            type(key_of_info)
                        )
                        assert (
                            type(value_of_info) == str
                        ), "Invalid type for dictionary values in content 'info'. Expected 'str'. Found '{}'.".format(
                            type(value_of_info)
                        )
            elif self.performative == TacMessage.Performative.TRANSACTION_CONFIRMATION:
                expected_nb_of_contents = 3
                assert (
                    type(self.tx_id) == str
                ), "Invalid type for content 'tx_id'. Expected 'str'. Found '{}'.".format(
                    type(self.tx_id)
                )
                assert (
                    type(self.amount_by_currency_id) == dict
                ), "Invalid type for content 'amount_by_currency_id'. Expected 'dict'. Found '{}'.".format(
                    type(self.amount_by_currency_id)
                )
                for (
                    key_of_amount_by_currency_id,
                    value_of_amount_by_currency_id,
                ) in self.amount_by_currency_id.items():
                    assert (
                        type(key_of_amount_by_currency_id) == str
                    ), "Invalid type for dictionary keys in content 'amount_by_currency_id'. Expected 'str'. Found '{}'.".format(
                        type(key_of_amount_by_currency_id)
                    )
                    assert (
                        type(value_of_amount_by_currency_id) == int
                    ), "Invalid type for dictionary values in content 'amount_by_currency_id'. Expected 'int'. Found '{}'.".format(
                        type(value_of_amount_by_currency_id)
                    )
                assert (
                    type(self.quantities_by_good_id) == dict
                ), "Invalid type for content 'quantities_by_good_id'. Expected 'dict'. Found '{}'.".format(
                    type(self.quantities_by_good_id)
                )
                for (
                    key_of_quantities_by_good_id,
                    value_of_quantities_by_good_id,
                ) in self.quantities_by_good_id.items():
                    assert (
                        type(key_of_quantities_by_good_id) == str
                    ), "Invalid type for dictionary keys in content 'quantities_by_good_id'. Expected 'str'. Found '{}'.".format(
                        type(key_of_quantities_by_good_id)
                    )
                    assert (
                        type(value_of_quantities_by_good_id) == int
                    ), "Invalid type for dictionary values in content 'quantities_by_good_id'. Expected 'int'. Found '{}'.".format(
                        type(value_of_quantities_by_good_id)
                    )
            elif self.performative == TacMessage.Performative.TAC_ERROR:
                expected_nb_of_contents = 1
                assert (
                    type(self.error_code) == CustomErrorCode
                ), "Invalid type for content 'error_code'. Expected 'ErrorCode'. Found '{}'.".format(
                    type(self.error_code)
                )
                if self.is_set("info"):
                    expected_nb_of_contents += 1
                    info = cast(Dict[str, str], self.info)
                    assert (
                        type(info) == dict
                    ), "Invalid type for content 'info'. Expected 'dict'. Found '{}'.".format(
                        type(info)
                    )
                    for key_of_info, value_of_info in info.items():
                        assert (
                            type(key_of_info) == str
                        ), "Invalid type for dictionary keys in content 'info'. Expected 'str'. Found '{}'.".format(
                            type(key_of_info)
                        )
                        assert (
                            type(value_of_info) == str
                        ), "Invalid type for dictionary values in content 'info'. Expected 'str'. Found '{}'.".format(
                            type(value_of_info)
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
