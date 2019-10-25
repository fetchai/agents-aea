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
from typing import Optional

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

    def __init__(self, type: Optional[Type] = None,
                 **kwargs):
        """
        Initialize.

        :param type: the type.
        """
        super().__init__(type=type, **kwargs)
        assert self.check_consistency(), "DefaultMessage initialization inconsistent."

    def check_consistency(self) -> bool:
        """Check that the data is consistent."""
        try:
            ttype = DefaultMessage.Type(self.get("type"))
            if ttype == DefaultMessage.Type.BYTES:
                assert self.is_set("content")
                content = self.get("content")
                assert isinstance(content, bytes)
            elif ttype == DefaultMessage.Type.ERROR:
                assert self.is_set("error_code")
                error_code = DefaultMessage.ErrorCode(self.get("error_code"))
                assert error_code in DefaultMessage.ErrorCode
                assert self.is_set("error_msg")
                assert self.is_set("error_data")
            else:
                raise ValueError("Performative not recognized.")

        except (AssertionError, ValueError, KeyError):
            return False

        return True
