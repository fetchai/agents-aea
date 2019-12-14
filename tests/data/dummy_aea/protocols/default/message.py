# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------
#
#   Copyright 2018-2019 Fetch.AI Limited
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

"""This module contains the default message definition."""
from enum import Enum
from typing import cast, Dict, Any

from aea.protocols.base import Message


class DefaultMessage(Message):
    """The Default message class."""

    protocol_id = "default"

    class Type(Enum):
        """Default message types."""

        BYTES = "bytes"
        ERROR = "error"

        def __str__(self):
            """Get the string representation."""
            return self.value

    class ErrorCode(Enum):
        """The error codes."""

        UNSUPPORTED_PROTOCOL = -10001
        DECODING_ERROR = -10002
        INVALID_MESSAGE = -10003
        UNSUPPORTED_SKILL = -10004
        INVALID_DIALOGUE = -10005

    def __init__(self, type: Type,
                 **kwargs):
        """
        Initialize.

        :param type: the type.
        """
        super().__init__(type=type, **kwargs)
        assert self.check_consistency(), "DefaultMessage initialization inconsistent."

    @property
    def type(self) -> Type:  # noqa: F821
        """Get the type of the message."""
        assert self.is_set("type"), "type is not set"
        return DefaultMessage.Type(self.get("type"))

    @property
    def content(self) -> bytes:
        """Get the content of the message."""
        assert self.is_set("content"), "content is not set!"
        return cast(bytes, self.get("content"))

    @property
    def error_code(self) -> ErrorCode:  # noqa: F821
        """Get the error_code of the message."""
        assert self.is_set("error_code"), "error_code is not set"
        return DefaultMessage.ErrorCode(self.get("error_code"))

    @property
    def error_msg(self) -> str:
        """Get the error message."""
        assert self.is_set("error_msg"), "error_msg is not set"
        return cast(str, self.get("error_msg"))

    @property
    def error_data(self) -> Dict[str, Any]:
        """Get the data of the error message."""
        assert self.is_set("error_data"), "error_data is not set."
        return cast(Dict[str, Any], self.get("error_data"))

    def check_consistency(self) -> bool:
        """Check that the data is consistent."""
        try:
            assert isinstance(self.type, DefaultMessage.Type)
            if self.type == DefaultMessage.Type.BYTES:
                assert isinstance(self.content, bytes), "Expect the content to be bytes"
                assert len(self.body) == 2
            elif self.type == DefaultMessage.Type.ERROR:
                assert self.error_code in DefaultMessage.ErrorCode, "ErrorCode is not valid"
                assert isinstance(self.error_code, DefaultMessage.ErrorCode), "error_code has wrong type."
                assert isinstance(self.error_msg, str), "error_msg should be str"
                assert isinstance(self.error_data, dict), "error_data should be dict"
                assert len(self.body) == 4
            else:
                raise ValueError("Type not recognized.")

        except (AssertionError, ValueError, KeyError):
            return False

        return True
