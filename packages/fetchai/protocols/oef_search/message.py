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

"""This module contains oef_search's message definition."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,too-many-branches,not-an-iterable,unidiomatic-typecheck,unsubscriptable-object
import logging
from typing import Any, Set, Tuple, cast

from aea.configurations.base import PublicId
from aea.exceptions import AEAEnforceError, enforce
from aea.protocols.base import Message

from packages.fetchai.protocols.oef_search.custom_types import (
    AgentsInfo as CustomAgentsInfo,
)
from packages.fetchai.protocols.oef_search.custom_types import (
    Description as CustomDescription,
)
from packages.fetchai.protocols.oef_search.custom_types import (
    OefErrorOperation as CustomOefErrorOperation,
)
from packages.fetchai.protocols.oef_search.custom_types import Query as CustomQuery


_default_logger = logging.getLogger("aea.packages.fetchai.protocols.oef_search.message")

DEFAULT_BODY_SIZE = 4


class OefSearchMessage(Message):
    """A protocol for interacting with an OEF search service."""

    protocol_id = PublicId.from_str("fetchai/oef_search:1.0.0")
    protocol_specification_id = PublicId.from_str("fetchai/oef_search:1.0.0")

    AgentsInfo = CustomAgentsInfo

    Description = CustomDescription

    OefErrorOperation = CustomOefErrorOperation

    Query = CustomQuery

    class Performative(Message.Performative):
        """Performatives for the oef_search protocol."""

        OEF_ERROR = "oef_error"
        REGISTER_SERVICE = "register_service"
        SEARCH_RESULT = "search_result"
        SEARCH_SERVICES = "search_services"
        SUCCESS = "success"
        UNREGISTER_SERVICE = "unregister_service"

        def __str__(self) -> str:
            """Get the string representation."""
            return str(self.value)

    _performatives = {
        "oef_error",
        "register_service",
        "search_result",
        "search_services",
        "success",
        "unregister_service",
    }
    __slots__: Tuple[str, ...] = tuple()

    class _SlotsCls:
        __slots__ = (
            "agents",
            "agents_info",
            "dialogue_reference",
            "message_id",
            "oef_error_operation",
            "performative",
            "query",
            "service_description",
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
        Initialise an instance of OefSearchMessage.

        :param message_id: the message id.
        :param dialogue_reference: the dialogue reference.
        :param target: the message target.
        :param performative: the message performative.
        """
        super().__init__(
            dialogue_reference=dialogue_reference,
            message_id=message_id,
            target=target,
            performative=OefSearchMessage.Performative(performative),
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
        return cast(OefSearchMessage.Performative, self.get("performative"))

    @property
    def target(self) -> int:
        """Get the target of the message."""
        enforce(self.is_set("target"), "target is not set.")
        return cast(int, self.get("target"))

    @property
    def agents(self) -> Tuple[str, ...]:
        """Get the 'agents' content from the message."""
        enforce(self.is_set("agents"), "'agents' content is not set.")
        return cast(Tuple[str, ...], self.get("agents"))

    @property
    def agents_info(self) -> CustomAgentsInfo:
        """Get the 'agents_info' content from the message."""
        enforce(self.is_set("agents_info"), "'agents_info' content is not set.")
        return cast(CustomAgentsInfo, self.get("agents_info"))

    @property
    def oef_error_operation(self) -> CustomOefErrorOperation:
        """Get the 'oef_error_operation' content from the message."""
        enforce(
            self.is_set("oef_error_operation"),
            "'oef_error_operation' content is not set.",
        )
        return cast(CustomOefErrorOperation, self.get("oef_error_operation"))

    @property
    def query(self) -> CustomQuery:
        """Get the 'query' content from the message."""
        enforce(self.is_set("query"), "'query' content is not set.")
        return cast(CustomQuery, self.get("query"))

    @property
    def service_description(self) -> CustomDescription:
        """Get the 'service_description' content from the message."""
        enforce(
            self.is_set("service_description"),
            "'service_description' content is not set.",
        )
        return cast(CustomDescription, self.get("service_description"))

    def _is_consistent(self) -> bool:
        """Check that the message follows the oef_search protocol."""
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
                isinstance(self.performative, OefSearchMessage.Performative),
                "Invalid 'performative'. Expected either of '{}'. Found '{}'.".format(
                    self.valid_performatives, self.performative
                ),
            )

            # Check correct contents
            actual_nb_of_contents = len(self._body) - DEFAULT_BODY_SIZE
            expected_nb_of_contents = 0
            if self.performative == OefSearchMessage.Performative.REGISTER_SERVICE:
                expected_nb_of_contents = 1
                enforce(
                    isinstance(self.service_description, CustomDescription),
                    "Invalid type for content 'service_description'. Expected 'Description'. Found '{}'.".format(
                        type(self.service_description)
                    ),
                )
            elif self.performative == OefSearchMessage.Performative.UNREGISTER_SERVICE:
                expected_nb_of_contents = 1
                enforce(
                    isinstance(self.service_description, CustomDescription),
                    "Invalid type for content 'service_description'. Expected 'Description'. Found '{}'.".format(
                        type(self.service_description)
                    ),
                )
            elif self.performative == OefSearchMessage.Performative.SEARCH_SERVICES:
                expected_nb_of_contents = 1
                enforce(
                    isinstance(self.query, CustomQuery),
                    "Invalid type for content 'query'. Expected 'Query'. Found '{}'.".format(
                        type(self.query)
                    ),
                )
            elif self.performative == OefSearchMessage.Performative.SEARCH_RESULT:
                expected_nb_of_contents = 2
                enforce(
                    isinstance(self.agents, tuple),
                    "Invalid type for content 'agents'. Expected 'tuple'. Found '{}'.".format(
                        type(self.agents)
                    ),
                )
                enforce(
                    all(isinstance(element, str) for element in self.agents),
                    "Invalid type for tuple elements in content 'agents'. Expected 'str'.",
                )
                enforce(
                    isinstance(self.agents_info, CustomAgentsInfo),
                    "Invalid type for content 'agents_info'. Expected 'AgentsInfo'. Found '{}'.".format(
                        type(self.agents_info)
                    ),
                )
            elif self.performative == OefSearchMessage.Performative.SUCCESS:
                expected_nb_of_contents = 1
                enforce(
                    isinstance(self.agents_info, CustomAgentsInfo),
                    "Invalid type for content 'agents_info'. Expected 'AgentsInfo'. Found '{}'.".format(
                        type(self.agents_info)
                    ),
                )
            elif self.performative == OefSearchMessage.Performative.OEF_ERROR:
                expected_nb_of_contents = 1
                enforce(
                    isinstance(self.oef_error_operation, CustomOefErrorOperation),
                    "Invalid type for content 'oef_error_operation'. Expected 'OefErrorOperation'. Found '{}'.".format(
                        type(self.oef_error_operation)
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
