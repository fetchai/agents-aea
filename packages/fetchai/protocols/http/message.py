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

"""This module contains http's message definition."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,too-many-branches,not-an-iterable,unidiomatic-typecheck,unsubscriptable-object
import logging
from typing import Any, Set, Tuple, cast

from aea.configurations.base import PublicId
from aea.exceptions import AEAEnforceError, enforce
from aea.protocols.base import Message


_default_logger = logging.getLogger("aea.packages.fetchai.protocols.http.message")

DEFAULT_BODY_SIZE = 4


class HttpMessage(Message):
    """A protocol for HTTP requests and responses."""

    protocol_id = PublicId.from_str("fetchai/http:1.0.0")
    protocol_specification_id = PublicId.from_str("fetchai/http:1.0.0")

    class Performative(Message.Performative):
        """Performatives for the http protocol."""

        REQUEST = "request"
        RESPONSE = "response"

        def __str__(self) -> str:
            """Get the string representation."""
            return str(self.value)

    _performatives = {"request", "response"}
    __slots__: Tuple[str, ...] = tuple()

    class _SlotsCls:
        __slots__ = (
            "body",
            "dialogue_reference",
            "headers",
            "message_id",
            "method",
            "performative",
            "status_code",
            "status_text",
            "target",
            "url",
            "version",
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
        Initialise an instance of HttpMessage.

        :param message_id: the message id.
        :param dialogue_reference: the dialogue reference.
        :param target: the message target.
        :param performative: the message performative.
        """
        super().__init__(
            dialogue_reference=dialogue_reference,
            message_id=message_id,
            target=target,
            performative=HttpMessage.Performative(performative),
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
        return cast(HttpMessage.Performative, self.get("performative"))

    @property
    def target(self) -> int:
        """Get the target of the message."""
        enforce(self.is_set("target"), "target is not set.")
        return cast(int, self.get("target"))

    @property
    def body(self) -> bytes:
        """Get the 'body' content from the message."""
        enforce(self.is_set("body"), "'body' content is not set.")
        return cast(bytes, self.get("body"))

    @property
    def headers(self) -> str:
        """Get the 'headers' content from the message."""
        enforce(self.is_set("headers"), "'headers' content is not set.")
        return cast(str, self.get("headers"))

    @property
    def method(self) -> str:
        """Get the 'method' content from the message."""
        enforce(self.is_set("method"), "'method' content is not set.")
        return cast(str, self.get("method"))

    @property
    def status_code(self) -> int:
        """Get the 'status_code' content from the message."""
        enforce(self.is_set("status_code"), "'status_code' content is not set.")
        return cast(int, self.get("status_code"))

    @property
    def status_text(self) -> str:
        """Get the 'status_text' content from the message."""
        enforce(self.is_set("status_text"), "'status_text' content is not set.")
        return cast(str, self.get("status_text"))

    @property
    def url(self) -> str:
        """Get the 'url' content from the message."""
        enforce(self.is_set("url"), "'url' content is not set.")
        return cast(str, self.get("url"))

    @property
    def version(self) -> str:
        """Get the 'version' content from the message."""
        enforce(self.is_set("version"), "'version' content is not set.")
        return cast(str, self.get("version"))

    def _is_consistent(self) -> bool:
        """Check that the message follows the http protocol."""
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
                isinstance(self.performative, HttpMessage.Performative),
                "Invalid 'performative'. Expected either of '{}'. Found '{}'.".format(
                    self.valid_performatives, self.performative
                ),
            )

            # Check correct contents
            actual_nb_of_contents = len(self._body) - DEFAULT_BODY_SIZE
            expected_nb_of_contents = 0
            if self.performative == HttpMessage.Performative.REQUEST:
                expected_nb_of_contents = 5
                enforce(
                    isinstance(self.method, str),
                    "Invalid type for content 'method'. Expected 'str'. Found '{}'.".format(
                        type(self.method)
                    ),
                )
                enforce(
                    isinstance(self.url, str),
                    "Invalid type for content 'url'. Expected 'str'. Found '{}'.".format(
                        type(self.url)
                    ),
                )
                enforce(
                    isinstance(self.version, str),
                    "Invalid type for content 'version'. Expected 'str'. Found '{}'.".format(
                        type(self.version)
                    ),
                )
                enforce(
                    isinstance(self.headers, str),
                    "Invalid type for content 'headers'. Expected 'str'. Found '{}'.".format(
                        type(self.headers)
                    ),
                )
                enforce(
                    isinstance(self.body, bytes),
                    "Invalid type for content 'body'. Expected 'bytes'. Found '{}'.".format(
                        type(self.body)
                    ),
                )
            elif self.performative == HttpMessage.Performative.RESPONSE:
                expected_nb_of_contents = 5
                enforce(
                    isinstance(self.version, str),
                    "Invalid type for content 'version'. Expected 'str'. Found '{}'.".format(
                        type(self.version)
                    ),
                )
                enforce(
                    type(self.status_code) is int,
                    "Invalid type for content 'status_code'. Expected 'int'. Found '{}'.".format(
                        type(self.status_code)
                    ),
                )
                enforce(
                    isinstance(self.status_text, str),
                    "Invalid type for content 'status_text'. Expected 'str'. Found '{}'.".format(
                        type(self.status_text)
                    ),
                )
                enforce(
                    isinstance(self.headers, str),
                    "Invalid type for content 'headers'. Expected 'str'. Found '{}'.".format(
                        type(self.headers)
                    ),
                )
                enforce(
                    isinstance(self.body, bytes),
                    "Invalid type for content 'body'. Expected 'bytes'. Found '{}'.".format(
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
