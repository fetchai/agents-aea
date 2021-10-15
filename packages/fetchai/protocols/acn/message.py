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

"""This module contains acn's message definition."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,too-many-branches,not-an-iterable,unidiomatic-typecheck,unsubscriptable-object
import logging
from typing import Any, Set, Tuple, cast

from aea.configurations.base import PublicId
from aea.exceptions import AEAEnforceError, enforce
from aea.protocols.base import Message

from packages.fetchai.protocols.acn.custom_types import AgentRecord as CustomAgentRecord
from packages.fetchai.protocols.acn.custom_types import StatusBody as CustomStatusBody


_default_logger = logging.getLogger("aea.packages.fetchai.protocols.acn.message")

DEFAULT_BODY_SIZE = 4


class AcnMessage(Message):
    """The protocol used for envelope delivery on the ACN."""

    protocol_id = PublicId.from_str("fetchai/acn:1.0.0")
    protocol_specification_id = PublicId.from_str("aea/acn:1.0.0")

    AgentRecord = CustomAgentRecord

    StatusBody = CustomStatusBody

    class Performative(Message.Performative):
        """Performatives for the acn protocol."""

        AEA_ENVELOPE = "aea_envelope"
        LOOKUP_REQUEST = "lookup_request"
        LOOKUP_RESPONSE = "lookup_response"
        REGISTER = "register"
        STATUS = "status"

        def __str__(self) -> str:
            """Get the string representation."""
            return str(self.value)

    _performatives = {
        "aea_envelope",
        "lookup_request",
        "lookup_response",
        "register",
        "status",
    }
    __slots__: Tuple[str, ...] = tuple()

    class _SlotsCls:
        __slots__ = (
            "agent_address",
            "body",
            "dialogue_reference",
            "envelope",
            "message_id",
            "performative",
            "record",
            "target",
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
        Initialise an instance of AcnMessage.

        :param message_id: the message id.
        :param dialogue_reference: the dialogue reference.
        :param target: the message target.
        :param performative: the message performative.
        """
        super().__init__(
            dialogue_reference=dialogue_reference,
            message_id=message_id,
            target=target,
            performative=AcnMessage.Performative(performative),
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
        return cast(AcnMessage.Performative, self.get("performative"))

    @property
    def target(self) -> int:
        """Get the target of the message."""
        enforce(self.is_set("target"), "target is not set.")
        return cast(int, self.get("target"))

    @property
    def agent_address(self) -> str:
        """Get the 'agent_address' content from the message."""
        enforce(self.is_set("agent_address"), "'agent_address' content is not set.")
        return cast(str, self.get("agent_address"))

    @property
    def body(self) -> CustomStatusBody:
        """Get the 'body' content from the message."""
        enforce(self.is_set("body"), "'body' content is not set.")
        return cast(CustomStatusBody, self.get("body"))

    @property
    def envelope(self) -> bytes:
        """Get the 'envelope' content from the message."""
        enforce(self.is_set("envelope"), "'envelope' content is not set.")
        return cast(bytes, self.get("envelope"))

    @property
    def record(self) -> CustomAgentRecord:
        """Get the 'record' content from the message."""
        enforce(self.is_set("record"), "'record' content is not set.")
        return cast(CustomAgentRecord, self.get("record"))

    def _is_consistent(self) -> bool:
        """Check that the message follows the acn protocol."""
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
                isinstance(self.performative, AcnMessage.Performative),
                "Invalid 'performative'. Expected either of '{}'. Found '{}'.".format(
                    self.valid_performatives, self.performative
                ),
            )

            # Check correct contents
            actual_nb_of_contents = len(self._body) - DEFAULT_BODY_SIZE
            expected_nb_of_contents = 0
            if self.performative == AcnMessage.Performative.REGISTER:
                expected_nb_of_contents = 1
                enforce(
                    isinstance(self.record, CustomAgentRecord),
                    "Invalid type for content 'record'. Expected 'AgentRecord'. Found '{}'.".format(
                        type(self.record)
                    ),
                )
            elif self.performative == AcnMessage.Performative.LOOKUP_REQUEST:
                expected_nb_of_contents = 1
                enforce(
                    isinstance(self.agent_address, str),
                    "Invalid type for content 'agent_address'. Expected 'str'. Found '{}'.".format(
                        type(self.agent_address)
                    ),
                )
            elif self.performative == AcnMessage.Performative.LOOKUP_RESPONSE:
                expected_nb_of_contents = 1
                enforce(
                    isinstance(self.record, CustomAgentRecord),
                    "Invalid type for content 'record'. Expected 'AgentRecord'. Found '{}'.".format(
                        type(self.record)
                    ),
                )
            elif self.performative == AcnMessage.Performative.AEA_ENVELOPE:
                expected_nb_of_contents = 2
                enforce(
                    isinstance(self.envelope, bytes),
                    "Invalid type for content 'envelope'. Expected 'bytes'. Found '{}'.".format(
                        type(self.envelope)
                    ),
                )
                enforce(
                    isinstance(self.record, CustomAgentRecord),
                    "Invalid type for content 'record'. Expected 'AgentRecord'. Found '{}'.".format(
                        type(self.record)
                    ),
                )
            elif self.performative == AcnMessage.Performative.STATUS:
                expected_nb_of_contents = 1
                enforce(
                    isinstance(self.body, CustomStatusBody),
                    "Invalid type for content 'body'. Expected 'StatusBody'. Found '{}'.".format(
                        type(self.body)
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
