# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021 fetchai
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

"""This module contains aggregation's message definition."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,too-many-branches,not-an-iterable,unidiomatic-typecheck,unsubscriptable-object
import logging
from typing import Any, Set, Tuple, cast

from aea.configurations.base import PublicId
from aea.exceptions import AEAEnforceError, enforce
from aea.protocols.base import Message


_default_logger = logging.getLogger(
    "aea.packages.fetchai.protocols.aggregation.message"
)

DEFAULT_BODY_SIZE = 4


class AggregationMessage(Message):
    """A protocol for agents to aggregate individual observations"""

    protocol_id = PublicId.from_str("fetchai/aggregation:0.1.0")
    protocol_specification_id = PublicId.from_str("fetchai/aggregation:0.1.0")

    class Performative(Message.Performative):
        """Performatives for the aggregation protocol."""

        AGGREGATION = "aggregation"
        OBSERVATION = "observation"

        def __str__(self) -> str:
            """Get the string representation."""
            return str(self.value)

    _performatives = {"aggregation", "observation"}
    __slots__: Tuple[str, ...] = tuple()

    class _SlotsCls:
        __slots__ = (
            "contributors",
            "dialogue_reference",
            "message_id",
            "performative",
            "signature",
            "source",
            "target",
            "time",
            "value",
        )

    def __init__(
        self,
        performative: Performative,
        dialogue_reference: Tuple[str, str] = ("", ""),
        message_id: int = 1,
        target: int = 0,
        **kwargs: Any,
    ):
        """
        Initialise an instance of AggregationMessage.

        :param message_id: the message id.
        :param dialogue_reference: the dialogue reference.
        :param target: the message target.
        :param performative: the message performative.
        """
        super().__init__(
            dialogue_reference=dialogue_reference,
            message_id=message_id,
            target=target,
            performative=AggregationMessage.Performative(performative),
            **kwargs,
        )

    @property
    def valid_performatives(self) -> Set[str]:
        """Get valid performatives."""
        return self._performatives

    @property
    def dialogue_reference(self) -> Tuple[str, str]:
        """Get the dialogue_reference of the message."""
        enforce(self.is_set("dialogue_reference"), "dialogue_reference is not set.")
        return cast(Tuple[str, str], self.get("dialogue_reference"))

    @property
    def message_id(self) -> int:
        """Get the message_id of the message."""
        enforce(self.is_set("message_id"), "message_id is not set.")
        return cast(int, self.get("message_id"))

    @property
    def performative(self) -> Performative:  # type: ignore # noqa: F821
        """Get the performative of the message."""
        enforce(self.is_set("performative"), "performative is not set.")
        return cast(AggregationMessage.Performative, self.get("performative"))

    @property
    def target(self) -> int:
        """Get the target of the message."""
        enforce(self.is_set("target"), "target is not set.")
        return cast(int, self.get("target"))

    @property
    def contributors(self) -> Tuple[str, ...]:
        """Get the 'contributors' content from the message."""
        enforce(self.is_set("contributors"), "'contributors' content is not set.")
        return cast(Tuple[str, ...], self.get("contributors"))

    @property
    def signature(self) -> str:
        """Get the 'signature' content from the message."""
        enforce(self.is_set("signature"), "'signature' content is not set.")
        return cast(str, self.get("signature"))

    @property
    def source(self) -> str:
        """Get the 'source' content from the message."""
        enforce(self.is_set("source"), "'source' content is not set.")
        return cast(str, self.get("source"))

    @property
    def time(self) -> str:
        """Get the 'time' content from the message."""
        enforce(self.is_set("time"), "'time' content is not set.")
        return cast(str, self.get("time"))

    @property
    def value(self) -> int:
        """Get the 'value' content from the message."""
        enforce(self.is_set("value"), "'value' content is not set.")
        return cast(int, self.get("value"))

    def _is_consistent(self) -> bool:
        """Check that the message follows the aggregation protocol."""
        try:
            enforce(
                isinstance(self.dialogue_reference, tuple),
                "Invalid type for 'dialogue_reference'. Expected 'tuple'. Found '{}'.".format(
                    type(self.dialogue_reference)
                ),
            )
            enforce(
                isinstance(self.dialogue_reference[0], str),
                "Invalid type for 'dialogue_reference[0]'. Expected 'str'. Found '{}'.".format(
                    type(self.dialogue_reference[0])
                ),
            )
            enforce(
                isinstance(self.dialogue_reference[1], str),
                "Invalid type for 'dialogue_reference[1]'. Expected 'str'. Found '{}'.".format(
                    type(self.dialogue_reference[1])
                ),
            )
            enforce(
                type(self.message_id) is int,
                "Invalid type for 'message_id'. Expected 'int'. Found '{}'.".format(
                    type(self.message_id)
                ),
            )
            enforce(
                type(self.target) is int,
                "Invalid type for 'target'. Expected 'int'. Found '{}'.".format(
                    type(self.target)
                ),
            )

            # Light Protocol Rule 2
            # Check correct performative
            enforce(
                isinstance(self.performative, AggregationMessage.Performative),
                "Invalid 'performative'. Expected either of '{}'. Found '{}'.".format(
                    self.valid_performatives, self.performative
                ),
            )

            # Check correct contents
            actual_nb_of_contents = len(self._body) - DEFAULT_BODY_SIZE
            expected_nb_of_contents = 0
            if self.performative == AggregationMessage.Performative.OBSERVATION:
                expected_nb_of_contents = 4
                enforce(
                    type(self.value) is int,
                    "Invalid type for content 'value'. Expected 'int'. Found '{}'.".format(
                        type(self.value)
                    ),
                )
                enforce(
                    isinstance(self.time, str),
                    "Invalid type for content 'time'. Expected 'str'. Found '{}'.".format(
                        type(self.time)
                    ),
                )
                enforce(
                    isinstance(self.source, str),
                    "Invalid type for content 'source'. Expected 'str'. Found '{}'.".format(
                        type(self.source)
                    ),
                )
                enforce(
                    isinstance(self.signature, str),
                    "Invalid type for content 'signature'. Expected 'str'. Found '{}'.".format(
                        type(self.signature)
                    ),
                )
            elif self.performative == AggregationMessage.Performative.AGGREGATION:
                expected_nb_of_contents = 4
                enforce(
                    type(self.value) is int,
                    "Invalid type for content 'value'. Expected 'int'. Found '{}'.".format(
                        type(self.value)
                    ),
                )
                enforce(
                    isinstance(self.time, str),
                    "Invalid type for content 'time'. Expected 'str'. Found '{}'.".format(
                        type(self.time)
                    ),
                )
                enforce(
                    isinstance(self.contributors, tuple),
                    "Invalid type for content 'contributors'. Expected 'tuple'. Found '{}'.".format(
                        type(self.contributors)
                    ),
                )
                enforce(
                    all(isinstance(element, str) for element in self.contributors),
                    "Invalid type for tuple elements in content 'contributors'. Expected 'str'.",
                )
                enforce(
                    isinstance(self.signature, str),
                    "Invalid type for content 'signature'. Expected 'str'. Found '{}'.".format(
                        type(self.signature)
                    ),
                )

            # Check correct content count
            enforce(
                expected_nb_of_contents == actual_nb_of_contents,
                "Incorrect number of contents. Expected {}. Found {}".format(
                    expected_nb_of_contents, actual_nb_of_contents
                ),
            )

            # Light Protocol Rule 3
            if self.message_id == 1:
                enforce(
                    self.target == 0,
                    "Invalid 'target'. Expected 0 (because 'message_id' is 1). Found {}.".format(
                        self.target
                    ),
                )
        except (AEAEnforceError, ValueError, KeyError) as e:
            _default_logger.error(str(e))
            return False

        return True
