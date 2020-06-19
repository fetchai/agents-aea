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

"""This module contains ml_trade's message definition."""

import logging
from enum import Enum
from typing import Set, Tuple, cast

from aea.configurations.base import ProtocolId
from aea.protocols.base import Message

from packages.fetchai.protocols.ml_trade.custom_types import (
    Description as CustomDescription,
)
from packages.fetchai.protocols.ml_trade.custom_types import Query as CustomQuery

logger = logging.getLogger("aea.packages.fetchai.protocols.ml_trade.message")

DEFAULT_BODY_SIZE = 4


class MlTradeMessage(Message):
    """A protocol for trading data for training and prediction purposes."""

    protocol_id = ProtocolId("fetchai", "ml_trade", "0.3.0")

    Description = CustomDescription

    Query = CustomQuery

    class Performative(Enum):
        """Performatives for the ml_trade protocol."""

        ACCEPT = "accept"
        CFP = "cfp"
        DATA = "data"
        TERMS = "terms"

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
        self._performatives = {"accept", "cfp", "data", "terms"}

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
        return cast(MlTradeMessage.Performative, self.get("performative"))

    @property
    def target(self) -> int:
        """Get the target of the message."""
        assert self.is_set("target"), "target is not set."
        return cast(int, self.get("target"))

    @property
    def payload(self) -> bytes:
        """Get the 'payload' content from the message."""
        assert self.is_set("payload"), "'payload' content is not set."
        return cast(bytes, self.get("payload"))

    @property
    def query(self) -> CustomQuery:
        """Get the 'query' content from the message."""
        assert self.is_set("query"), "'query' content is not set."
        return cast(CustomQuery, self.get("query"))

    @property
    def terms(self) -> CustomDescription:
        """Get the 'terms' content from the message."""
        assert self.is_set("terms"), "'terms' content is not set."
        return cast(CustomDescription, self.get("terms"))

    @property
    def tx_digest(self) -> str:
        """Get the 'tx_digest' content from the message."""
        assert self.is_set("tx_digest"), "'tx_digest' content is not set."
        return cast(str, self.get("tx_digest"))

    def _is_consistent(self) -> bool:
        """Check that the message follows the ml_trade protocol."""
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
                type(self.performative) == MlTradeMessage.Performative
            ), "Invalid 'performative'. Expected either of '{}'. Found '{}'.".format(
                self.valid_performatives, self.performative
            )

            # Check correct contents
            actual_nb_of_contents = len(self.body) - DEFAULT_BODY_SIZE
            expected_nb_of_contents = 0
            if self.performative == MlTradeMessage.Performative.CFP:
                expected_nb_of_contents = 1
                assert (
                    type(self.query) == CustomQuery
                ), "Invalid type for content 'query'. Expected 'Query'. Found '{}'.".format(
                    type(self.query)
                )
            elif self.performative == MlTradeMessage.Performative.TERMS:
                expected_nb_of_contents = 1
                assert (
                    type(self.terms) == CustomDescription
                ), "Invalid type for content 'terms'. Expected 'Description'. Found '{}'.".format(
                    type(self.terms)
                )
            elif self.performative == MlTradeMessage.Performative.ACCEPT:
                expected_nb_of_contents = 2
                assert (
                    type(self.terms) == CustomDescription
                ), "Invalid type for content 'terms'. Expected 'Description'. Found '{}'.".format(
                    type(self.terms)
                )
                assert (
                    type(self.tx_digest) == str
                ), "Invalid type for content 'tx_digest'. Expected 'str'. Found '{}'.".format(
                    type(self.tx_digest)
                )
            elif self.performative == MlTradeMessage.Performative.DATA:
                expected_nb_of_contents = 2
                assert (
                    type(self.terms) == CustomDescription
                ), "Invalid type for content 'terms'. Expected 'Description'. Found '{}'.".format(
                    type(self.terms)
                )
                assert (
                    type(self.payload) == bytes
                ), "Invalid type for content 'payload'. Expected 'bytes'. Found '{}'.".format(
                    type(self.payload)
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
