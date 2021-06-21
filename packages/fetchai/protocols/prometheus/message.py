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

"""This module contains prometheus's message definition."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,too-many-branches,not-an-iterable,unidiomatic-typecheck,unsubscriptable-object
import logging
from typing import Any, Dict, Optional, Set, Tuple, cast

from aea.configurations.base import PublicId
from aea.exceptions import AEAEnforceError, enforce
from aea.protocols.base import Message


_default_logger = logging.getLogger("aea.packages.fetchai.protocols.prometheus.message")

DEFAULT_BODY_SIZE = 4


class PrometheusMessage(Message):
    """A protocol for adding and updating metrics to a prometheus server."""

    protocol_id = PublicId.from_str("fetchai/prometheus:1.0.0")
    protocol_specification_id = PublicId.from_str("fetchai/prometheus:1.0.0")

    class Performative(Message.Performative):
        """Performatives for the prometheus protocol."""

        ADD_METRIC = "add_metric"
        RESPONSE = "response"
        UPDATE_METRIC = "update_metric"

        def __str__(self) -> str:
            """Get the string representation."""
            return str(self.value)

    _performatives = {"add_metric", "response", "update_metric"}
    __slots__: Tuple[str, ...] = tuple()

    class _SlotsCls:
        __slots__ = (
            "callable",
            "code",
            "description",
            "dialogue_reference",
            "labels",
            "message",
            "message_id",
            "performative",
            "target",
            "title",
            "type",
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
        Initialise an instance of PrometheusMessage.

        :param message_id: the message id.
        :param dialogue_reference: the dialogue reference.
        :param target: the message target.
        :param performative: the message performative.
        """
        super().__init__(
            dialogue_reference=dialogue_reference,
            message_id=message_id,
            target=target,
            performative=PrometheusMessage.Performative(performative),
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
        return cast(PrometheusMessage.Performative, self.get("performative"))

    @property
    def target(self) -> int:
        """Get the target of the message."""
        enforce(self.is_set("target"), "target is not set.")
        return cast(int, self.get("target"))

    @property
    def callable(self) -> str:
        """Get the 'callable' content from the message."""
        enforce(self.is_set("callable"), "'callable' content is not set.")
        return cast(str, self.get("callable"))

    @property
    def code(self) -> int:
        """Get the 'code' content from the message."""
        enforce(self.is_set("code"), "'code' content is not set.")
        return cast(int, self.get("code"))

    @property
    def description(self) -> str:
        """Get the 'description' content from the message."""
        enforce(self.is_set("description"), "'description' content is not set.")
        return cast(str, self.get("description"))

    @property
    def labels(self) -> Dict[str, str]:
        """Get the 'labels' content from the message."""
        enforce(self.is_set("labels"), "'labels' content is not set.")
        return cast(Dict[str, str], self.get("labels"))

    @property
    def message(self) -> Optional[str]:
        """Get the 'message' content from the message."""
        return cast(Optional[str], self.get("message"))

    @property
    def title(self) -> str:
        """Get the 'title' content from the message."""
        enforce(self.is_set("title"), "'title' content is not set.")
        return cast(str, self.get("title"))

    @property
    def type(self) -> str:
        """Get the 'type' content from the message."""
        enforce(self.is_set("type"), "'type' content is not set.")
        return cast(str, self.get("type"))

    @property
    def value(self) -> float:
        """Get the 'value' content from the message."""
        enforce(self.is_set("value"), "'value' content is not set.")
        return cast(float, self.get("value"))

    def _is_consistent(self) -> bool:
        """Check that the message follows the prometheus protocol."""
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
                isinstance(self.performative, PrometheusMessage.Performative),
                "Invalid 'performative'. Expected either of '{}'. Found '{}'.".format(
                    self.valid_performatives, self.performative
                ),
            )

            # Check correct contents
            actual_nb_of_contents = len(self._body) - DEFAULT_BODY_SIZE
            expected_nb_of_contents = 0
            if self.performative == PrometheusMessage.Performative.ADD_METRIC:
                expected_nb_of_contents = 4
                enforce(
                    isinstance(self.type, str),
                    "Invalid type for content 'type'. Expected 'str'. Found '{}'.".format(
                        type(self.type)
                    ),
                )
                enforce(
                    isinstance(self.title, str),
                    "Invalid type for content 'title'. Expected 'str'. Found '{}'.".format(
                        type(self.title)
                    ),
                )
                enforce(
                    isinstance(self.description, str),
                    "Invalid type for content 'description'. Expected 'str'. Found '{}'.".format(
                        type(self.description)
                    ),
                )
                enforce(
                    isinstance(self.labels, dict),
                    "Invalid type for content 'labels'. Expected 'dict'. Found '{}'.".format(
                        type(self.labels)
                    ),
                )
                for key_of_labels, value_of_labels in self.labels.items():
                    enforce(
                        isinstance(key_of_labels, str),
                        "Invalid type for dictionary keys in content 'labels'. Expected 'str'. Found '{}'.".format(
                            type(key_of_labels)
                        ),
                    )
                    enforce(
                        isinstance(value_of_labels, str),
                        "Invalid type for dictionary values in content 'labels'. Expected 'str'. Found '{}'.".format(
                            type(value_of_labels)
                        ),
                    )
            elif self.performative == PrometheusMessage.Performative.UPDATE_METRIC:
                expected_nb_of_contents = 4
                enforce(
                    isinstance(self.title, str),
                    "Invalid type for content 'title'. Expected 'str'. Found '{}'.".format(
                        type(self.title)
                    ),
                )
                enforce(
                    isinstance(self.callable, str),
                    "Invalid type for content 'callable'. Expected 'str'. Found '{}'.".format(
                        type(self.callable)
                    ),
                )
                enforce(
                    isinstance(self.value, float),
                    "Invalid type for content 'value'. Expected 'float'. Found '{}'.".format(
                        type(self.value)
                    ),
                )
                enforce(
                    isinstance(self.labels, dict),
                    "Invalid type for content 'labels'. Expected 'dict'. Found '{}'.".format(
                        type(self.labels)
                    ),
                )
                for key_of_labels, value_of_labels in self.labels.items():
                    enforce(
                        isinstance(key_of_labels, str),
                        "Invalid type for dictionary keys in content 'labels'. Expected 'str'. Found '{}'.".format(
                            type(key_of_labels)
                        ),
                    )
                    enforce(
                        isinstance(value_of_labels, str),
                        "Invalid type for dictionary values in content 'labels'. Expected 'str'. Found '{}'.".format(
                            type(value_of_labels)
                        ),
                    )
            elif self.performative == PrometheusMessage.Performative.RESPONSE:
                expected_nb_of_contents = 1
                enforce(
                    type(self.code) is int,
                    "Invalid type for content 'code'. Expected 'int'. Found '{}'.".format(
                        type(self.code)
                    ),
                )
                if self.is_set("message"):
                    expected_nb_of_contents += 1
                    message = cast(str, self.message)
                    enforce(
                        isinstance(message, str),
                        "Invalid type for content 'message'. Expected 'str'. Found '{}'.".format(
                            type(message)
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
