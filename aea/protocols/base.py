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

"""This module contains the base message and serialization definition."""

import json
from abc import ABC, abstractmethod
from copy import copy
from typing import Any, Dict, Optional

from google.protobuf.struct_pb2 import Struct

from aea.configurations.base import ProtocolConfig, ProtocolId
from aea.mail.base import Address


class Message:
    """This class implements a message."""

    protocol_id = "base"

    def __init__(self, body: Optional[Dict] = None, **kwargs):
        """
        Initialize a Message object.

        :param body: the dictionary of values to hold.
        :param kwargs: any additional value to add to the body. It will overwrite the body values.
        """
        self._counterparty = None  # type: Optional[Address]
        self._body = copy(body) if body else {}  # type: Dict[str, Any]
        self._body.update(kwargs)
        assert self._check_consistency(), "Message initialization inconsistent."

    @property
    def counterparty(self) -> Address:
        """
        Get the counterparty of the message in Address form.

        :return the address
        """
        assert self._counterparty is not None, "Counterparty must not be None."
        return self._counterparty

    @counterparty.setter
    def counterparty(self, counterparty: Address) -> None:
        """Set the counterparty of the message."""
        self._counterparty = counterparty

    @property
    def body(self) -> Dict:
        """
        Get the body of the message (in dictionary form).

        :return: the body
        """
        return self._body

    @body.setter
    def body(self, body: Dict) -> None:
        """
        Set the body of hte message.

        :param body: the body.
        :return: None
        """
        self._body = body

    def set(self, key: str, value: Any) -> None:
        """
        Set key and value pair.

        :param key: the key.
        :param value: the value.
        :return: None
        """
        self._body[key] = value

    def get(self, key: str) -> Optional[Any]:
        """Get value for key."""
        return self._body.get(key, None)

    def unset(self, key: str) -> None:
        """Unset valye for key."""
        self._body.pop(key, None)

    def is_set(self, key: str) -> bool:
        """Check value is set for key."""
        return key in self._body

    def _check_consistency(self) -> bool:
        """Check that the data is consistent."""
        return True

    def __eq__(self, other):
        """Compare with another object."""
        return (
            isinstance(other, Message)
            and self.body == other.body
            and self._counterparty == other._counterparty
        )

    def __str__(self):
        """Get the string representation of the message."""
        return (
            "Message("
            + " ".join(
                map(
                    lambda key_value: str(key_value[0]) + "=" + str(key_value[1]),
                    self.body.items(),
                )
            )
            + ")"
        )


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
    """
    Default serialization in JSON for the Message object.

    It assumes that the Message contains a JSON-serializable body.
    """

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


class Protocol(ABC):
    """
    This class implements a specifications for a protocol.

    It includes:
    - a serializer, to encode/decode a message.
    - a 'check' abstract method (to be implemented) to check if a message is allowed for the protocol.
    """

    def __init__(self, protocol_id: ProtocolId, serializer: Serializer, config: ProtocolConfig):
        """
        Initialize the protocol manager.

        :param protocol_id: the protocol id.
        :param serializer: the serializer.
        :param config: the protocol configurations.
        """
        self._protocol_id = protocol_id
        self._serializer = serializer
        self._config = config

    @property
    def id(self) -> ProtocolId:
        """Get the name."""
        return self._protocol_id

    @property
    def serializer(self) -> Serializer:
        """Get the serializer."""
        return self._serializer

    @property
    def config(self) -> ProtocolConfig:
        """Get the configuration."""
        return self._config

    def check(self, msg: Message) -> bool:
        """
        Check whether the message belongs to the allowed messages.

        :param msg: the message.
        :return: True if the message is valid wrt the protocol, False otherwise.
        """
        # TODO 'check' should check the message against the protocol rules, if such rules are provided.
        return True
