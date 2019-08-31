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

from aea.protocols.base.message import Message


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
        UNSUPPORTED_PROTOCOL = -10001

    def __init__(self, type: Optional[Type] = None,
                 **kwargs):
        """
        Initialize.

        :param type: the type.
        """
        super().__init__(type=type, **kwargs)
