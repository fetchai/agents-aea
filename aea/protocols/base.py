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

import inspect
import json
import logging
import re
from abc import ABC, abstractmethod
from copy import copy
from pathlib import Path
from typing import Any, Dict, Optional, cast

from google.protobuf.struct_pb2 import Struct

from aea.configurations.base import (
    ProtocolConfig,
    ProtocolId,
    PublicId,
)
from aea.configurations.components import Component
from aea.helpers.base import load_module
from aea.mail.base import Address

logger = logging.getLogger(__name__)


class Message:
    """This class implements a message."""

    protocol_id = None  # type: PublicId

    def __init__(self, body: Optional[Dict] = None, **kwargs):
        """
        Initialize a Message object.

        :param body: the dictionary of values to hold.
        :param kwargs: any additional value to add to the body. It will overwrite the body values.
        """
        self._counterparty = None  # type: Optional[Address]
        self._body = copy(body) if body else {}  # type: Dict[str, Any]
        self._body.update(kwargs)
        try:
            self._is_consistent()
        except Exception as e:
            logger.error(e)

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

    def _is_consistent(self) -> bool:
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


class Protocol(Component):
    """
    This class implements a specifications for a protocol.

    It includes a serializer to encode/decode a message.
    """

    def __init__(
        self, configuration: ProtocolConfig,
    ):
        """
        Initialize the protocol manager.

        :param configuration: the protocol configurations.
        """
        super().__init__(configuration)

        self._serializer = None  # type: Optional[Serializer]

    @property
    def id(self) -> ProtocolId:
        """Get the name."""
        return self._configuration.public_id

    @property
    def serializer(self) -> Serializer:
        """Get the serializer."""
        assert self._serializer is not None, "Serializer not initialized yet."
        return self._serializer

    @serializer.setter
    def serializer(self, serializer: Serializer) -> None:
        """Set the serializer."""
        assert self._serializer is None, "Serializer already initialized."
        self._serializer = serializer

    @property
    def config(self) -> ProtocolConfig:
        """Get the configuration."""
        return cast(ProtocolConfig, self._configuration)

    def load(self) -> None:
        """
        Set the component up.

        In the case of a protocol, we load the 'serialization.py' module
        to instantiate an instance of the Serializer.

        :return: None
        :raises Exception: if the parsing failed.
        """
        serialization_module = load_module(
            "serialization", Path(self.directory, "serialization.py")
        )
        classes = inspect.getmembers(serialization_module, inspect.isclass)
        serializer_classes = list(
            filter(lambda x: re.match("\\w+Serializer", x[0]), classes)
        )
        assert len(serializer_classes) == 1, "Not exactly one serializer detected."
        serializer_class = serializer_classes[0][1]

        # update attributes.
        self._serializer = serializer_class()
