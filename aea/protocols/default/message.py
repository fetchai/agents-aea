# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2020 Fetch.AI Limited
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

"""This module contains default's message definition."""

from enum import Enum
from typing import Dict, Set, Tuple, cast

from aea.configurations.base import ProtocolId
from aea.protocols.base import Message
from aea.protocols.default.custom_types import ErrorCode as CustomErrorCode

DEFAULT_BODY_SIZE = 4


class DefaultMessage(Message):
    """A protocol for exchanging any bytes message."""

    protocol_id = ProtocolId("fetchai", "default", "0.1.0")

    ErrorCode = CustomErrorCode

    class Performative(Enum):
        """Performatives for the default protocol."""

        BYTES = "bytes"
        ERROR = "error"

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
        Initialise an instance of DefaultMessage.

        :param message_id: the message id.
        :param dialogue_reference: the dialogue reference.
        :param target: the message target.
        :param performative: the message performative.
        """
        super().__init__(
            dialogue_reference=dialogue_reference,
            message_id=message_id,
            target=target,
            performative=DefaultMessage.Performative(performative),
            **kwargs,
        )
        self._performatives = {"bytes", "error"}
        assert (
            self._is_consistent()
        ), "This message is invalid according to the 'default' protocol."

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
        return cast(DefaultMessage.Performative, self.get("performative"))

    @property
    def target(self) -> int:
        """Get the target of the message."""
        assert self.is_set("target"), "target is not set."
        return cast(int, self.get("target"))

    @property
    def content(self) -> bytes:
        """Get the 'content' content from the message."""
        assert self.is_set("content"), "'content' content is not set."
        return cast(bytes, self.get("content"))

    @property
    def error_code(self) -> CustomErrorCode:
        """Get the 'error_code' content from the message."""
        assert self.is_set("error_code"), "'error_code' content is not set."
        return cast(CustomErrorCode, self.get("error_code"))

    @property
    def error_data(self) -> Dict[str, bytes]:
        """Get the 'error_data' content from the message."""
        assert self.is_set("error_data"), "'error_data' content is not set."
        return cast(Dict[str, bytes], self.get("error_data"))

    @property
    def error_msg(self) -> str:
        """Get the 'error_msg' content from the message."""
        assert self.is_set("error_msg"), "'error_msg' content is not set."
        return cast(str, self.get("error_msg"))

    def _is_consistent(self) -> bool:
        """Check that the message follows the default protocol."""
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
                type(self.performative) == DefaultMessage.Performative
            ), "'{}' is not in the list of valid performatives: {}".format(
                self.performative, self.valid_performatives
            )

            # Check correct contents
            actual_nb_of_contents = len(self.body) - DEFAULT_BODY_SIZE
            expected_nb_of_contents = 0
            if self.performative == DefaultMessage.Performative.BYTES:
                expected_nb_of_contents = 1
                assert (
                    type(self.content) == bytes
                ), "Content 'content' is not of type 'bytes'."
            elif self.performative == DefaultMessage.Performative.ERROR:
                expected_nb_of_contents = 3
                assert (
                    type(self.error_code) == CustomErrorCode
                ), "Content 'error_code' is not of type 'ErrorCode'."
                assert (
                    type(self.error_msg) == str
                ), "Content 'error_msg' is not of type 'str'."
                assert (
                    type(self.error_data) == dict
                ), "Content 'error_data' is not of type 'dict'."
                for key, value in self.error_data.items():
                    assert (
                        type(key) == str
                    ), "Keys of 'error_data' dictionary are not of type 'str'."
                    assert (
                        type(value) == bytes
                    ), "Values of 'error_data' dictionary are not of type 'bytes'."

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
