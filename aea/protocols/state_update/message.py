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

"""This module contains state_update's message definition."""

import logging
from enum import Enum
from typing import Dict, Set, Tuple, cast

from aea.configurations.base import ProtocolId
from aea.protocols.base import Message

logger = logging.getLogger("aea.packages.fetchai.protocols.state_update.message")

DEFAULT_BODY_SIZE = 4


class StateUpdateMessage(Message):
    """A protocol for state updates to the decision maker state."""

    protocol_id = ProtocolId("fetchai", "state_update", "0.1.0")

    class Performative(Enum):
        """Performatives for the state_update protocol."""

        APPLY = "apply"
        INITIALIZE = "initialize"

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
        Initialise an instance of StateUpdateMessage.

        :param message_id: the message id.
        :param dialogue_reference: the dialogue reference.
        :param target: the message target.
        :param performative: the message performative.
        """
        super().__init__(
            dialogue_reference=dialogue_reference,
            message_id=message_id,
            target=target,
            performative=StateUpdateMessage.Performative(performative),
            **kwargs,
        )
        self._performatives = {"apply", "initialize"}

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
        return cast(StateUpdateMessage.Performative, self.get("performative"))

    @property
    def target(self) -> int:
        """Get the target of the message."""
        assert self.is_set("target"), "target is not set."
        return cast(int, self.get("target"))

    @property
    def amount_by_currency_id(self) -> Dict[str, int]:
        """Get the 'amount_by_currency_id' content from the message."""
        assert self.is_set(
            "amount_by_currency_id"
        ), "'amount_by_currency_id' content is not set."
        return cast(Dict[str, int], self.get("amount_by_currency_id"))

    @property
    def exchange_params_by_currency_id(self) -> Dict[str, float]:
        """Get the 'exchange_params_by_currency_id' content from the message."""
        assert self.is_set(
            "exchange_params_by_currency_id"
        ), "'exchange_params_by_currency_id' content is not set."
        return cast(Dict[str, float], self.get("exchange_params_by_currency_id"))

    @property
    def quantities_by_good_id(self) -> Dict[str, int]:
        """Get the 'quantities_by_good_id' content from the message."""
        assert self.is_set(
            "quantities_by_good_id"
        ), "'quantities_by_good_id' content is not set."
        return cast(Dict[str, int], self.get("quantities_by_good_id"))

    @property
    def utility_params_by_good_id(self) -> Dict[str, float]:
        """Get the 'utility_params_by_good_id' content from the message."""
        assert self.is_set(
            "utility_params_by_good_id"
        ), "'utility_params_by_good_id' content is not set."
        return cast(Dict[str, float], self.get("utility_params_by_good_id"))

    def _is_consistent(self) -> bool:
        """Check that the message follows the state_update protocol."""
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
                type(self.performative) == StateUpdateMessage.Performative
            ), "Invalid 'performative'. Expected either of '{}'. Found '{}'.".format(
                self.valid_performatives, self.performative
            )

            # Check correct contents
            actual_nb_of_contents = len(self.body) - DEFAULT_BODY_SIZE
            expected_nb_of_contents = 0
            if self.performative == StateUpdateMessage.Performative.INITIALIZE:
                expected_nb_of_contents = 4
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
            elif self.performative == StateUpdateMessage.Performative.APPLY:
                expected_nb_of_contents = 2
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
