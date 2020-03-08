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

from enum import Enum
from typing import Set, Tuple, cast

from aea.configurations.base import ProtocolId
from aea.protocols.base import Message

DEFAULT_BODY_SIZE = 4


class HttpMessage(Message):
    """A protocol for HTTP requests and responses."""

    protocol_id = ProtocolId("fetchai", "http", "0.1.0")

    class Performative(Enum):
        """Performatives for the http protocol."""

        REQUEST = "request"
        RESPONSE = "response"

        def __str__(self):
            """Get the string representation."""
            return self.value

    def __init__(
        self,
        dialogue_reference: Tuple[str, str],
        message_id: int,
        target: int,
        performative: Performative,
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
        assert (
            self._is_consistent()
        ), "This message is invalid according to the 'http' protocol."

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
    def performative(self) -> Performative:  # noqa: F821
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
            ), "dialogue_reference must be 'tuple' but it is not."
            assert (
                type(self.dialogue_reference[0]) == str
            ), "The first element of dialogue_reference must be 'str' but it is not."
            assert (
                type(self.dialogue_reference[1]) == str
            ), "The second element of dialogue_reference must be 'str' but it is not."
            assert type(self.message_id) == int, "message_id is not int"
            assert type(self.target) == int, "target is not int"

            # Light Protocol Rule 2
            # Check correct performative
            assert (
                type(self.performative) == HttpMessage.Performative
            ), "'{}' is not in the list of valid performatives: {}".format(
                self.performative, self.valid_performatives
            )

            # Check correct contents
            actual_nb_of_contents = len(self.body) - DEFAULT_BODY_SIZE
            expected_nb_of_contents = 0
            if self.performative == HttpMessage.Performative.REQUEST:
                expected_nb_of_contents = 5
                assert (
                    type(self.method) == str
                ), "Content 'method' is not of type 'str'."
                assert type(self.url) == str, "Content 'url' is not of type 'str'."
                assert (
                    type(self.version) == str
                ), "Content 'version' is not of type 'str'."
                assert (
                    type(self.headers) == str
                ), "Content 'headers' is not of type 'str'."
                assert (
                    type(self.bodyy) == bytes
                ), "Content 'bodyy' is not of type 'bytes'."
            elif self.performative == HttpMessage.Performative.RESPONSE:
                expected_nb_of_contents = 5
                assert (
                    type(self.version) == str
                ), "Content 'version' is not of type 'str'."
                assert (
                    type(self.status_code) == int
                ), "Content 'status_code' is not of type 'int'."
                assert (
                    type(self.status_text) == str
                ), "Content 'status_text' is not of type 'str'."
                assert (
                    type(self.headers) == str
                ), "Content 'headers' is not of type 'str'."
                assert (
                    type(self.bodyy) == bytes
                ), "Content 'bodyy' is not of type 'bytes'."

            # Check correct content count
            assert (
                expected_nb_of_contents == actual_nb_of_contents
            ), "Incorrect number of contents. Expected {} contents. Found {}".format(
                expected_nb_of_contents, actual_nb_of_contents
            )

            # Light Protocol Rule 3
            if self.message_id == 1:
                assert (
                    self.target == 0
                ), "Expected target to be 0 when message_id is 1. Found {}.".format(
                    self.target
                )
            else:
                assert (
                    0 < self.target < self.message_id
                ), "Expected target to be between 1 to (message_id -1) inclusive. Found {}".format(
                    self.target
                )
        except (AssertionError, ValueError, KeyError) as e:
            print(str(e))
            return False

        return True
