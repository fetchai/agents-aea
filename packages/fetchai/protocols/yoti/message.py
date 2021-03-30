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

"""This module contains yoti's message definition."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,too-many-branches,not-an-iterable,unidiomatic-typecheck,unsubscriptable-object
import logging
from typing import Any, Dict, Set, Tuple, cast

from aea.configurations.base import PublicId
from aea.exceptions import AEAEnforceError, enforce
from aea.protocols.base import Message


_default_logger = logging.getLogger("aea.packages.fetchai.protocols.yoti.message")

DEFAULT_BODY_SIZE = 4


class YotiMessage(Message):
    """A protocol for communication between yoti skills and yoti connection."""

    protocol_id = PublicId.from_str("fetchai/yoti:1.0.0")
    protocol_specification_id = PublicId.from_str("fetchai/yoti:1.0.0")

    class Performative(Message.Performative):
        """Performatives for the yoti protocol."""

        ERROR = "error"
        GET_PROFILE = "get_profile"
        PROFILE = "profile"

        def __str__(self) -> str:
            """Get the string representation."""
            return str(self.value)

    _performatives = {"error", "get_profile", "profile"}
    __slots__: Tuple[str, ...] = tuple()

    class _SlotsCls:
        __slots__ = (
            "args",
            "dialogue_reference",
            "dotted_path",
            "error_code",
            "error_msg",
            "info",
            "message_id",
            "performative",
            "target",
            "token",
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
        Initialise an instance of YotiMessage.

        :param message_id: the message id.
        :param dialogue_reference: the dialogue reference.
        :param target: the message target.
        :param performative: the message performative.
        """
        super().__init__(
            dialogue_reference=dialogue_reference,
            message_id=message_id,
            target=target,
            performative=YotiMessage.Performative(performative),
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
        return cast(YotiMessage.Performative, self.get("performative"))

    @property
    def target(self) -> int:
        """Get the target of the message."""
        enforce(self.is_set("target"), "target is not set.")
        return cast(int, self.get("target"))

    @property
    def args(self) -> Tuple[str, ...]:
        """Get the 'args' content from the message."""
        enforce(self.is_set("args"), "'args' content is not set.")
        return cast(Tuple[str, ...], self.get("args"))

    @property
    def dotted_path(self) -> str:
        """Get the 'dotted_path' content from the message."""
        enforce(self.is_set("dotted_path"), "'dotted_path' content is not set.")
        return cast(str, self.get("dotted_path"))

    @property
    def error_code(self) -> int:
        """Get the 'error_code' content from the message."""
        enforce(self.is_set("error_code"), "'error_code' content is not set.")
        return cast(int, self.get("error_code"))

    @property
    def error_msg(self) -> str:
        """Get the 'error_msg' content from the message."""
        enforce(self.is_set("error_msg"), "'error_msg' content is not set.")
        return cast(str, self.get("error_msg"))

    @property
    def info(self) -> Dict[str, str]:
        """Get the 'info' content from the message."""
        enforce(self.is_set("info"), "'info' content is not set.")
        return cast(Dict[str, str], self.get("info"))

    @property
    def token(self) -> str:
        """Get the 'token' content from the message."""
        enforce(self.is_set("token"), "'token' content is not set.")
        return cast(str, self.get("token"))

    def _is_consistent(self) -> bool:
        """Check that the message follows the yoti protocol."""
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
                isinstance(self.performative, YotiMessage.Performative),
                "Invalid 'performative'. Expected either of '{}'. Found '{}'.".format(
                    self.valid_performatives, self.performative
                ),
            )

            # Check correct contents
            actual_nb_of_contents = len(self._body) - DEFAULT_BODY_SIZE
            expected_nb_of_contents = 0
            if self.performative == YotiMessage.Performative.GET_PROFILE:
                expected_nb_of_contents = 3
                enforce(
                    isinstance(self.token, str),
                    "Invalid type for content 'token'. Expected 'str'. Found '{}'.".format(
                        type(self.token)
                    ),
                )
                enforce(
                    isinstance(self.dotted_path, str),
                    "Invalid type for content 'dotted_path'. Expected 'str'. Found '{}'.".format(
                        type(self.dotted_path)
                    ),
                )
                enforce(
                    isinstance(self.args, tuple),
                    "Invalid type for content 'args'. Expected 'tuple'. Found '{}'.".format(
                        type(self.args)
                    ),
                )
                enforce(
                    all(isinstance(element, str) for element in self.args),
                    "Invalid type for tuple elements in content 'args'. Expected 'str'.",
                )
            elif self.performative == YotiMessage.Performative.PROFILE:
                expected_nb_of_contents = 1
                enforce(
                    isinstance(self.info, dict),
                    "Invalid type for content 'info'. Expected 'dict'. Found '{}'.".format(
                        type(self.info)
                    ),
                )
                for key_of_info, value_of_info in self.info.items():
                    enforce(
                        isinstance(key_of_info, str),
                        "Invalid type for dictionary keys in content 'info'. Expected 'str'. Found '{}'.".format(
                            type(key_of_info)
                        ),
                    )
                    enforce(
                        isinstance(value_of_info, str),
                        "Invalid type for dictionary values in content 'info'. Expected 'str'. Found '{}'.".format(
                            type(value_of_info)
                        ),
                    )
            elif self.performative == YotiMessage.Performative.ERROR:
                expected_nb_of_contents = 2
                enforce(
                    type(self.error_code) is int,
                    "Invalid type for content 'error_code'. Expected 'int'. Found '{}'.".format(
                        type(self.error_code)
                    ),
                )
                enforce(
                    isinstance(self.error_msg, str),
                    "Invalid type for content 'error_msg'. Expected 'str'. Found '{}'.".format(
                        type(self.error_msg)
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
