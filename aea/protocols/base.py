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
import importlib
import inspect
import json
import logging
import re
from abc import ABC, abstractmethod
from copy import copy
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Type, cast

from google.protobuf.struct_pb2 import Struct

from aea.components.base import Component
from aea.configurations.base import (
    ComponentConfiguration,
    ComponentType,
    ProtocolConfig,
    PublicId,
)
from aea.helpers.base import load_aea_package

logger = logging.getLogger(__name__)

Address = str


class Message:
    """This class implements a message."""

    protocol_id = None  # type: PublicId
    serializer = None  # type: Type["Serializer"]

    class Performative(Enum):
        """Performatives for the base message."""

        def __str__(self):
            """Get the string representation."""
            return str(self.value)

    def __init__(self, body: Optional[Dict] = None, **kwargs):
        """
        Initialize a Message object.

        :param body: the dictionary of values to hold.
        :param kwargs: any additional value to add to the body. It will overwrite the body values.
        """
        self._counterparty = None  # type: Optional[Address]
        self._body = copy(body) if body else {}  # type: Dict[str, Any]
        self._body.update(kwargs)
        self._is_incoming = False
        try:
            self._is_consistent()
        except Exception as e:  # pylint: disable=broad-except
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
    def is_incoming(self) -> bool:
        """
        Get the is_incoming value of the message.

        :return whether the message is incoming or is out going
        """
        return self._is_incoming

    @is_incoming.setter
    def is_incoming(self, is_incoming: bool) -> None:
        """Set the is_incoming of the message."""
        self._is_incoming = is_incoming

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

    @property
    def dialogue_reference(self) -> Tuple[str, str]:
        """Get the dialogue_reference of the message."""
        assert self.is_set("dialogue_reference"), "dialogue_reference is not set."
        return cast(Tuple[str, str], self.get("dialogue_reference"))

    @property
    def message_id(self) -> int:
        """Get the message_id of the message."""
        assert self.is_set("message_id"), "message_id is not set."
        return cast(int, self.get("message_id"))

    @property
    def performative(self) -> "Performative":
        """Get the performative of the message."""
        assert self.is_set("performative"), "performative is not set."
        return cast(Message.Performative, self.get("performative"))

    @property
    def target(self) -> int:
        """Get the target of the message."""
        assert self.is_set("target"), "target is not set."
        return cast(int, self.get("target"))

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

    def _is_consistent(self) -> bool:  # pylint: disable=no-self-use
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

    def encode(self) -> bytes:
        """Encode the message."""
        return self.serializer.encode(self)


class Encoder(ABC):
    """Encoder interface."""

    @staticmethod
    @abstractmethod
    def encode(msg: Message) -> bytes:
        """
        Encode a message.

        :param msg: the message to be encoded.
        :return: the encoded message.
        """


class Decoder(ABC):
    """Decoder interface."""

    @staticmethod
    @abstractmethod
    def decode(obj: bytes) -> Message:
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

    @staticmethod
    def encode(msg: Message) -> bytes:
        """Encode a message into bytes using Protobuf."""
        body_json = Struct()
        body_json.update(msg.body)  # pylint: disable=no-member
        body_bytes = body_json.SerializeToString()
        return body_bytes

    @staticmethod
    def decode(obj: bytes) -> Message:
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

    @staticmethod
    def encode(msg: Message) -> bytes:
        """
        Encode a message into bytes using JSON format.

        :param msg: the message to be encoded.
        :return: the serialized message.
        """
        bytes_msg = json.dumps(msg.body).encode("utf-8")
        return bytes_msg

    @staticmethod
    def decode(obj: bytes) -> Message:
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

    def __init__(self, configuration: ProtocolConfig, message_class: Type[Message]):
        """
        Initialize the protocol manager.

        :param configuration: the protocol configurations.
        :param serializer: the serializer.
        """
        super().__init__(configuration)

        self._message_class = message_class

    @property
    def serializer(self) -> Type[Serializer]:
        """Get the serializer."""
        return self._message_class.serializer

    @classmethod
    def from_dir(cls, directory: str) -> "Protocol":
        """
        Load the protocol from a directory.

        :param directory: the directory to the skill package.
        :return: the protocol object.
        """
        configuration = cast(
            ProtocolConfig,
            ComponentConfiguration.load(ComponentType.PROTOCOL, Path(directory)),
        )
        configuration.directory = Path(directory)
        return Protocol.from_config(configuration)

    @classmethod
    def from_config(cls, configuration: ProtocolConfig) -> "Protocol":
        """
        Load the protocol from configuration.

        :param configuration: the protocol configuration.
        :return: the protocol object.
        """
        assert (
            configuration.directory is not None
        ), "Configuration must be associated with a directory."
        load_aea_package(configuration)
        class_module = importlib.import_module(
            configuration.prefix_import_path + ".message"
        )
        classes = inspect.getmembers(class_module, inspect.isclass)
        name_camel_case = "".join(
            word.capitalize() for word in configuration.name.split("_")
        )
        message_classes = list(
            filter(
                lambda x: re.match("{}Message".format(name_camel_case), x[0]), classes
            )
        )
        assert len(message_classes) == 1, "Not exactly one message class detected."
        message_class = message_classes[0][1]
        class_module = importlib.import_module(
            configuration.prefix_import_path + ".serialization"
        )
        classes = inspect.getmembers(class_module, inspect.isclass)
        serializer_classes = list(
            filter(
                lambda x: re.match("{}Serializer".format(name_camel_case), x[0]),
                classes,
            )
        )
        assert (
            len(serializer_classes) == 1
        ), "Not exactly one serializer class detected."
        serialize_class = serializer_classes[0][1]
        message_class.serializer = serialize_class

        return Protocol(configuration, message_class)
