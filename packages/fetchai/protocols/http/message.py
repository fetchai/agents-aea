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

"""This module contains http's message definition."""

import logging
from enum import Enum
from typing import Set, Tuple, cast

from aea.configurations.base import ProtocolId
from aea.protocols.base import Message

logger = logging.getLogger("aea.packages.fetchai.protocols.http.message")

DEFAULT_BODY_SIZE = 4


class HttpMessage(Message):
    """A protocol for HTTP requests and responses."""

    protocol_id = ProtocolId("fetchai", "http", "0.3.0")

    class Performative(Enum):
        """Performatives for the http protocol."""

        REQUEST = "request"
        RESPONSE = "response"

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
        self._performatives = {"request", "response"}

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
        return cast(HttpMessage.Performative, self.get("performative"))

    @property
    def target(self) -> int:
        """Get the target of the message."""
        assert self.is_set("target"), "target is not set."
        return cast(int, self.get("target"))

    @property
    def bodyy(self) -> bytes:
        """Get the 'bodyy' content from the message."""
        assert self.is_set("bodyy"), "'bodyy' content is not set."
        return cast(bytes, self.get("bodyy"))

    @property
    def headers(self) -> str:
        """Get the 'headers' content from the message."""
        assert self.is_set("headers"), "'headers' content is not set."
        return cast(str, self.get("headers"))

    @property
    def method(self) -> str:
        """Get the 'method' content from the message."""
        assert self.is_set("method"), "'method' content is not set."
        return cast(str, self.get("method"))

    @property
    def status_code(self) -> int:
        """Get the 'status_code' content from the message."""
        assert self.is_set("status_code"), "'status_code' content is not set."
        return cast(int, self.get("status_code"))

    @property
    def status_text(self) -> str:
        """Get the 'status_text' content from the message."""
        assert self.is_set("status_text"), "'status_text' content is not set."
        return cast(str, self.get("status_text"))

    @property
    def url(self) -> str:
        """Get the 'url' content from the message."""
        assert self.is_set("url"), "'url' content is not set."
        return cast(str, self.get("url"))

    @property
    def version(self) -> str:
        """Get the 'version' content from the message."""
        assert self.is_set("version"), "'version' content is not set."
        return cast(str, self.get("version"))

    def _is_consistent(self) -> bool:
        """Check that the message follows the http protocol."""
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
                type(self.performative) == HttpMessage.Performative
            ), "Invalid 'performative'. Expected either of '{}'. Found '{}'.".format(
                self.valid_performatives, self.performative
            )

            # Check correct contents
            actual_nb_of_contents = len(self.body) - DEFAULT_BODY_SIZE
            expected_nb_of_contents = 0
            if self.performative == HttpMessage.Performative.REQUEST:
                expected_nb_of_contents = 5
                assert (
                    type(self.method) == str
                ), "Invalid type for content 'method'. Expected 'str'. Found '{}'.".format(
                    type(self.method)
                )
                assert (
                    type(self.url) == str
                ), "Invalid type for content 'url'. Expected 'str'. Found '{}'.".format(
                    type(self.url)
                )
                assert (
                    type(self.version) == str
                ), "Invalid type for content 'version'. Expected 'str'. Found '{}'.".format(
                    type(self.version)
                )
                assert (
                    type(self.headers) == str
                ), "Invalid type for content 'headers'. Expected 'str'. Found '{}'.".format(
                    type(self.headers)
                )
                assert (
                    type(self.bodyy) == bytes
                ), "Invalid type for content 'bodyy'. Expected 'bytes'. Found '{}'.".format(
                    type(self.bodyy)
                )
            elif self.performative == HttpMessage.Performative.RESPONSE:
                expected_nb_of_contents = 5
                assert (
                    type(self.version) == str
                ), "Invalid type for content 'version'. Expected 'str'. Found '{}'.".format(
                    type(self.version)
                )
                assert (
                    type(self.status_code) == int
                ), "Invalid type for content 'status_code'. Expected 'int'. Found '{}'.".format(
                    type(self.status_code)
                )
                assert (
                    type(self.status_text) == str
                ), "Invalid type for content 'status_text'. Expected 'str'. Found '{}'.".format(
                    type(self.status_text)
                )
                assert (
                    type(self.headers) == str
                ), "Invalid type for content 'headers'. Expected 'str'. Found '{}'.".format(
                    type(self.headers)
                )
                assert (
                    type(self.bodyy) == bytes
                ), "Invalid type for content 'bodyy'. Expected 'bytes'. Found '{}'.".format(
                    type(self.bodyy)
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
