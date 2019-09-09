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

"""This module contains the implementation of a protocol manager."""
from abc import ABC

from aea.protocols.base.message import Message
from aea.protocols.base.serialization import Serializer


class Protocol(ABC):
    """
    This class implements a specifications for a protocol.

    It includes:
    - a serializer, to encode/decode a message.
    - a 'check' abstract method (to be implemented) to check if a message is allowed for the protocol.
    """

    def __init__(self, id: str, serializer: Serializer):
        """
        Initialize the protocol manager.

        :param id: the protocol id.
        :param serializer: the serializer.
        """
        self._id = id
        self._serializer = serializer

    @property
    def id(self):
        """Get the name."""
        return self._id

    @property
    def serializer(self) -> Serializer:
        """Get the serializer."""
        return self._serializer

    def check(self, msg: Message) -> bool:
        """
        Check whether the message belongs to the allowed messages.

        :param msg: the message.
        :return: True if the message is valid wrt the protocol, False otherwise.
        """
        # TODO 'check' should be an abstract method, and every protocol should provide a concrete Protocol class that implements it.
        return True
