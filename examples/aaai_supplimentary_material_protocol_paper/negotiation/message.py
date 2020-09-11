# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2020 AAAI_paper_authors
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

"""This module contains negotiation's message definition."""

import logging
from typing import Set, Tuple, cast

from aea.configurations.base import ProtocolId
from aea.exceptions import AEAEnforceError, enforce
from aea.protocols.base import Message

from packages.AAAI_paper_authors.protocols.negotiation.custom_types import (
    Resources as CustomResources,
)

logger = logging.getLogger(
    "aea.packages.AAAI_paper_authors.protocols.negotiation.message"
)

DEFAULT_BODY_SIZE = 4


class NegotiationMessage(Message):
    """A bilateral negotiation protocol, for AAAI-21 submission."""

    protocol_id = ProtocolId.from_str("AAAI_paper_authors/negotiation:0.1.0")

    Resources = CustomResources

    class Performative(Message.Performative):
        """Performatives for the negotiation protocol."""

        ACCEPT = "accept"
        CFP = "cfp"
        DECLINE = "decline"
        PROPOSE = "propose"

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
        Initialise an instance of NegotiationMessage.

        :param message_id: the message id.
        :param dialogue_reference: the dialogue reference.
        :param target: the message target.
        :param performative: the message performative.
        """
        self._performatives = {"accept", "cfp", "decline", "propose"}
        super().__init__(
            dialogue_reference=dialogue_reference,
            message_id=message_id,
            target=target,
            performative=NegotiationMessage.Performative(performative),
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
        return cast(NegotiationMessage.Performative, self.get("performative"))

    @property
    def target(self) -> int:
        """Get the target of the message."""
        enforce(self.is_set("target"), "target is not set.")
        return cast(int, self.get("target"))

    @property
    def e(self) -> CustomResources:
        """Get the 'e' content from the message."""
        enforce(self.is_set("e"), "'e' content is not set.")
        return cast(CustomResources, self.get("e"))

    @property
    def p(self) -> int:
        """Get the 'p' content from the message."""
        enforce(self.is_set("p"), "'p' content is not set.")
        return cast(int, self.get("p"))

    def _is_consistent(self) -> bool:
        """Check that the message follows the negotiation protocol."""
        try:
            enforce(
                type(self.dialogue_reference) == tuple,
                "Invalid type for 'dialogue_reference'. Expected 'tuple'. Found '{}'.".format(
                    type(self.dialogue_reference)
                ),
            )
            enforce(
                type(self.dialogue_reference[0]) == str,
                "Invalid type for 'dialogue_reference[0]'. Expected 'str'. Found '{}'.".format(
                    type(self.dialogue_reference[0])
                ),
            )
            enforce(
                type(self.dialogue_reference[1]) == str,
                "Invalid type for 'dialogue_reference[1]'. Expected 'str'. Found '{}'.".format(
                    type(self.dialogue_reference[1])
                ),
            )
            enforce(
                type(self.message_id) == int,
                "Invalid type for 'message_id'. Expected 'int'. Found '{}'.".format(
                    type(self.message_id)
                ),
            )
            enforce(
                type(self.target) == int,
                "Invalid type for 'target'. Expected 'int'. Found '{}'.".format(
                    type(self.target)
                ),
            )

            # Light Protocol Rule 2
            # Check correct performative
            enforce(
                type(self.performative) == NegotiationMessage.Performative,
                "Invalid 'performative'. Expected either of '{}'. Found '{}'.".format(
                    self.valid_performatives, self.performative
                ),
            )

            # Check correct contents
            actual_nb_of_contents = len(self.body) - DEFAULT_BODY_SIZE
            expected_nb_of_contents = 0
            if self.performative == NegotiationMessage.Performative.CFP:
                expected_nb_of_contents = 1
                enforce(
                    type(self.e) == CustomResources,
                    "Invalid type for content 'e'. Expected 'Resources'. Found '{}'.".format(
                        type(self.e)
                    ),
                )
            elif self.performative == NegotiationMessage.Performative.PROPOSE:
                expected_nb_of_contents = 2
                enforce(
                    type(self.e) == CustomResources,
                    "Invalid type for content 'e'. Expected 'Resources'. Found '{}'.".format(
                        type(self.e)
                    ),
                )
                enforce(
                    type(self.p) == int,
                    "Invalid type for content 'p'. Expected 'int'. Found '{}'.".format(
                        type(self.p)
                    ),
                )
            elif self.performative == NegotiationMessage.Performative.ACCEPT:
                expected_nb_of_contents = 0
            elif self.performative == NegotiationMessage.Performative.DECLINE:
                expected_nb_of_contents = 0

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
            else:
                enforce(
                    0 < self.target < self.message_id,
                    "Invalid 'target'. Expected an integer between 1 and {} inclusive. Found {}.".format(
                        self.message_id - 1, self.target,
                    ),
                )
        except (AEAEnforceError, ValueError, KeyError) as e:
            logger.error(str(e))
            return False

        return True
