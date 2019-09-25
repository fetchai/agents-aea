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

"""This module contains the scaffold message definition."""

from enum import Enum
from typing import Optional

from aea.protocols.base import Message


class MyScaffoldMessage(Message):
    """The scaffold message class."""

    protocol_id = "my_scaffold_protocol"

    class Type(Enum):
        """Scaffold Message types."""

        def __str__(self):
            """Get string representation."""
            return self.value

    def __init__(self, oef_type: Optional[Type] = None,
                 **kwargs):
        """
        Initialize.

        :param oef_type: the type of message.
        """
        super().__init__(type=oef_type, **kwargs)
        assert self.check_consistency(), "MyScaffoldMessage initialization inconsistent."

    def check_consistency(self) -> bool:
        """Check that the data is consistent."""
        try:
            raise NotImplementedError
        except (AssertionError, ValueError):
            return False

        return True
