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

"""Serializer for base."""
import json
from abc import abstractmethod, ABC

from google.protobuf.struct_pb2 import Struct

from aea.protocols.base.message import Message


class Encoder(ABC):
    """Encoder interface."""

    @abstractmethod
    def encode(self, msg: Message) -> bytes:
        """
        Encode a message.

        :param msg: the message to be encoded.
        :return: the encoded message.
        """


class Decoder(ABC):
    """Decoder interface."""

    @abstractmethod
    def decode(self, obj: bytes) -> Message:
        """
        Decode a message.

        :param obj: the sequence of bytes to be decoded.
        :return: the decoded message.
        """


class Serializer(Encoder, Decoder, ABC):
    """The implementations of this class defines a serialization layer for a protocol."""


class ProtobufSerializer(Serializer):
    """
    Default Protobuf serializer.

    It assumes that the Message contains a JSON-serializable body.
    """

    def encode(self, msg: Message) -> bytes:
        """Encode a message into bytes using Protobuf."""
        body_json = Struct()
        body_json.update(msg.body)
        body_bytes = body_json.SerializeToString()
        return body_bytes

    def decode(self, obj: bytes) -> Message:
        """Decode bytes into a message using Protobuf."""
        body_json = Struct()
        body_json.ParseFromString(obj)

        body = dict(body_json)
        msg = Message(body=body)
        return msg


class JSONSerializer(Serializer):
    """Default serialization in JSON for the Message object."""

    def encode(self, msg: Message) -> bytes:
        """
        Encode a message into bytes using JSON format.

        :param msg: the message to be encoded.
        :return: the serialized message.
        """
        bytes_msg = json.dumps(msg.body).encode("utf-8")
        return bytes_msg

    def decode(self, obj: bytes) -> Message:
        """
        Decode bytes into a message using JSON.

        :param obj: the serialized message.
        :return: the decoded message.
        """
        json_msg = json.loads(obj.decode("utf-8"))
        return Message(json_msg)
