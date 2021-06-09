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

"""Serialization for the scaffold protocol."""


from aea.protocols.base import Message, Serializer


class MyScaffoldSerializer(Serializer):  # pragma: no cover
    """Serialization for the scaffold protocol."""

    @staticmethod
    def encode(msg: Message) -> bytes:
        """
        Decode the message.

        :param msg: the message object
        :return: the bytes  # noqa: DAR202
        """
        raise NotImplementedError  # pragma: no cover

    @staticmethod
    def decode(obj: bytes) -> Message:
        """
        Decode the message.

        :param obj: the bytes object
        :return: the message  # noqa: DAR202
        """
        raise NotImplementedError  # pragma: no cover
