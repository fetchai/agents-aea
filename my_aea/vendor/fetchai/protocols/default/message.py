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

"""This module contains default's message definition."""

import logging
from enum import Enum
from typing import Dict, Set, Tuple, cast

from aea.configurations.base import ProtocolId
from aea.protocols.base import Message
from aea.protocols.default.custom_types import ErrorCode as CustomErrorCode

logger = logging.getLogger("aea.protocols.default.message")

DEFAULT_BODY_SIZE = 4


class DefaultMessage(Message):
    """A protocol for exchanging any bytes message."""

    protocol_id = ProtocolId("fetchai", "default", "0.3.0")

    ErrorCode = CustomErrorCode

    class Performative(Enum):
        """Performatives for the default protocol."""

        BYTES = "bytes"
        ERROR = "error"

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
                type(self.performative) == DefaultMessage.Performative
            ), "Invalid 'performative'. Expected either of '{}'. Found '{}'.".format(
                self.valid_performatives, self.performative
            )

            # Check correct contents
            actual_nb_of_contents = len(self.body) - DEFAULT_BODY_SIZE
            expected_nb_of_contents = 0
            if self.performative == DefaultMessage.Performative.BYTES:
                expected_nb_of_contents = 1
                assert (
                    type(self.content) == bytes
                ), "Invalid type for content 'content'. Expected 'bytes'. Found '{}'.".format(
                    type(self.content)
                )
            elif self.performative == DefaultMessage.Performative.ERROR:
                expected_nb_of_contents = 3
                assert (
                    type(self.error_code) == CustomErrorCode
                ), "Invalid type for content 'error_code'. Expected 'ErrorCode'. Found '{}'.".format(
                    type(self.error_code)
                )
                assert (
                    type(self.error_msg) == str
                ), "Invalid type for content 'error_msg'. Expected 'str'. Found '{}'.".format(
                    type(self.error_msg)
                )
                assert (
                    type(self.error_data) == dict
                ), "Invalid type for content 'error_data'. Expected 'dict'. Found '{}'.".format(
                    type(self.error_data)
                )
                for key_of_error_data, value_of_error_data in self.error_data.items():
                    assert (
                        type(key_of_error_data) == str
                    ), "Invalid type for dictionary keys in content 'error_data'. Expected 'str'. Found '{}'.".format(
                        type(key_of_error_data)
                    )
                    assert (
                        type(value_of_error_data) == bytes
                    ), "Invalid type for dictionary values in content 'error_data'. Expected 'bytes'. Found '{}'.".format(
                        type(value_of_error_data)
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
