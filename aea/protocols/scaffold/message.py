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

from aea.configurations.base import PublicId
from aea.protocols.base import Message
from aea.protocols.scaffold.serialization import MyScaffoldSerializer


class MyScaffoldMessage(Message):
    """The scaffold message class."""

    protocol_id = PublicId("fetchai", "scaffold", "0.1.0")
    serializer = MyScaffoldSerializer

    class Performative(Enum):
        """Scaffold Message types."""

        def __str__(self):
            """Get string representation."""
            return str(self.value)  # pragma: no cover

    def __init__(self, performative: Performative, **kwargs):
        """
        Initialize.

        :param performative: the type of message.
        """
        super().__init__(performative=performative, **kwargs)
        assert (
            self._is_consistent()
        ), "MyScaffoldMessage initialization inconsistent."  # pragma: no cover

    def _is_consistent(self) -> bool:
        """Check that the data is consistent."""
        try:
            raise NotImplementedError
        except (AssertionError, ValueError):
            return False  # pragma: no cover

        return True  # pragma: no cover
