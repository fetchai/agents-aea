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

"""This module contains ml_trade's message definition."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,too-many-branches,not-an-iterable,unidiomatic-typecheck,unsubscriptable-object
import logging
from typing import Any, Set, Tuple, cast

from aea.configurations.base import PublicId
from aea.exceptions import AEAEnforceError, enforce
from aea.protocols.base import Message

from packages.fetchai.protocols.ml_trade.custom_types import (
    Description as CustomDescription,
)
from packages.fetchai.protocols.ml_trade.custom_types import Query as CustomQuery


_default_logger = logging.getLogger("aea.packages.fetchai.protocols.ml_trade.message")

DEFAULT_BODY_SIZE = 4


class MlTradeMessage(Message):
    """A protocol for trading data for training and prediction purposes."""

    protocol_id = PublicId.from_str("fetchai/ml_trade:1.0.0")
    protocol_specification_id = PublicId.from_str("fetchai/ml_trade:1.0.0")

    Description = CustomDescription

    Query = CustomQuery

    class Performative(Message.Performative):
        """Performatives for the ml_trade protocol."""

        ACCEPT = "accept"
        CFP = "cfp"
        DATA = "data"
        TERMS = "terms"

        def __str__(self) -> str:
            """Get the string representation."""
            return str(self.value)

    _performatives = {"accept", "cfp", "data", "terms"}
    __slots__: Tuple[str, ...] = tuple()

    class _SlotsCls:
        __slots__ = (
            "dialogue_reference",
            "message_id",
            "payload",
            "performative",
            "query",
            "target",
            "terms",
            "tx_digest",
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
        Initialise an instance of MlTradeMessage.

        :param message_id: the message id.
        :param dialogue_reference: the dialogue reference.
        :param target: the message target.
        :param performative: the message performative.
        """
        super().__init__(
            dialogue_reference=dialogue_reference,
            message_id=message_id,
            target=target,
            performative=MlTradeMessage.Performative(performative),
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
        return cast(MlTradeMessage.Performative, self.get("performative"))

    @property
    def target(self) -> int:
        """Get the target of the message."""
        enforce(self.is_set("target"), "target is not set.")
        return cast(int, self.get("target"))

    @property
    def payload(self) -> bytes:
        """Get the 'payload' content from the message."""
        enforce(self.is_set("payload"), "'payload' content is not set.")
        return cast(bytes, self.get("payload"))

    @property
    def query(self) -> CustomQuery:
        """Get the 'query' content from the message."""
        enforce(self.is_set("query"), "'query' content is not set.")
        return cast(CustomQuery, self.get("query"))

    @property
    def terms(self) -> CustomDescription:
        """Get the 'terms' content from the message."""
        enforce(self.is_set("terms"), "'terms' content is not set.")
        return cast(CustomDescription, self.get("terms"))

    @property
    def tx_digest(self) -> str:
        """Get the 'tx_digest' content from the message."""
        enforce(self.is_set("tx_digest"), "'tx_digest' content is not set.")
        return cast(str, self.get("tx_digest"))

    def _is_consistent(self) -> bool:
        """Check that the message follows the ml_trade protocol."""
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
                isinstance(self.performative, MlTradeMessage.Performative),
                "Invalid 'performative'. Expected either of '{}'. Found '{}'.".format(
                    self.valid_performatives, self.performative
                ),
            )

            # Check correct contents
            actual_nb_of_contents = len(self._body) - DEFAULT_BODY_SIZE
            expected_nb_of_contents = 0
            if self.performative == MlTradeMessage.Performative.CFP:
                expected_nb_of_contents = 1
                enforce(
                    isinstance(self.query, CustomQuery),
                    "Invalid type for content 'query'. Expected 'Query'. Found '{}'.".format(
                        type(self.query)
                    ),
                )
            elif self.performative == MlTradeMessage.Performative.TERMS:
                expected_nb_of_contents = 1
                enforce(
                    isinstance(self.terms, CustomDescription),
                    "Invalid type for content 'terms'. Expected 'Description'. Found '{}'.".format(
                        type(self.terms)
                    ),
                )
            elif self.performative == MlTradeMessage.Performative.ACCEPT:
                expected_nb_of_contents = 2
                enforce(
                    isinstance(self.terms, CustomDescription),
                    "Invalid type for content 'terms'. Expected 'Description'. Found '{}'.".format(
                        type(self.terms)
                    ),
                )
                enforce(
                    isinstance(self.tx_digest, str),
                    "Invalid type for content 'tx_digest'. Expected 'str'. Found '{}'.".format(
                        type(self.tx_digest)
                    ),
                )
            elif self.performative == MlTradeMessage.Performative.DATA:
                expected_nb_of_contents = 2
                enforce(
                    isinstance(self.terms, CustomDescription),
                    "Invalid type for content 'terms'. Expected 'Description'. Found '{}'.".format(
                        type(self.terms)
                    ),
                )
                enforce(
                    isinstance(self.payload, bytes),
                    "Invalid type for content 'payload'. Expected 'bytes'. Found '{}'.".format(
                        type(self.payload)
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
