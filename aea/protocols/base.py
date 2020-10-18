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
import logging
import re
from abc import ABC, abstractmethod
from copy import copy
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional, Tuple, Type, cast

from google.protobuf.struct_pb2 import Struct

from aea.components.base import Component, load_aea_package
from aea.configurations.base import ComponentType, ProtocolConfig, PublicId
from aea.configurations.loader import load_component_configuration
from aea.exceptions import enforce
from aea.mail.base_pb2 import DialogueMessage
from aea.mail.base_pb2 import Message as ProtobufMessage


_default_logger = logging.getLogger(__name__)

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

    def __init__(self, _body: Optional[Dict] = None, **kwargs):
        """
        Initialize a Message object.

        :param body: the dictionary of values to hold.
        :param kwargs: any additional value to add to the body. It will overwrite the body values.
        """
        self._to: Optional[Address] = None
        self._sender: Optional[Address] = None
        self.__body: Dict[str, Any] = copy(_body) if _body else {}
        self.__body.update(kwargs)

        try:
            self._is_consistent()
        except Exception as e:  # pylint: disable=broad-except
            _default_logger.error(e)

    @property
    def has_sender(self) -> bool:
        """Check if it has a sender."""
        return self._sender is not None

    @property
    def sender(self) -> Address:
        """
        Get the sender of the message in Address form.

        :return the address
        """
        if self._sender is None:
            raise ValueError("Message's 'Sender' field must be set.")  # pragma: nocover
        return self._sender

    @sender.setter
    def sender(self, sender: Address) -> None:
        """Set the sender of the message."""
        enforce(self._sender is None, "Sender already set.")
        enforce(
            isinstance(sender, str),
            f"Sender must be string type. Found '{type(sender)}'",
        )
        self._sender = sender

    @property
    def has_to(self) -> bool:
        """Check if it has a sender."""
        return self._to is not None

    @property
    def to(self) -> Address:
        """Get address of receiver."""
        if self._to is None:
            raise ValueError("Message's 'To' field must be set.")
        return self._to

    @to.setter
    def to(self, to: Address) -> None:
        """Set address of receiver."""
        enforce(self._to is None, "To already set.")
        enforce(isinstance(to, str), f"To must be string type. Found '{type(to)}'")
        self._to = to

    @property
    def _body(self) -> Dict:
        """
        Get the body of the message (in dictionary form).

        :return: the body
        """
        return self.__body

    @_body.setter
    def _body(self, body: Dict) -> None:
        """
        Set the body of hte message.

        :param body: the body.
        :return: None
        """
        self.__body = body

    @property
    def dialogue_reference(self) -> Tuple[str, str]:
        """Get the dialogue_reference of the message."""
        if not self.is_set("dialogue_reference"):
            raise ValueError("dialogue_reference is not set.")  # pragma: nocover
        return cast(Tuple[str, str], self.get("dialogue_reference"))

    @property
    def message_id(self) -> int:
        """Get the message_id of the message."""
        if not self.is_set("message_id"):
            raise ValueError("message_id is not set.")  # pragma: nocover
        return cast(int, self.get("message_id"))

    @property
    def performative(self) -> "Performative":
        """Get the performative of the message."""
        if not self.is_set("performative"):
            raise ValueError("performative is not set.")  # pragma: nocover
        return cast(Message.Performative, self.get("performative"))

    @property
    def target(self) -> int:
        """Get the target of the message."""
        if not self.is_set("target"):
            raise ValueError("target is not set.")  # pragma: nocover
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
            and self._sender == other._sender
            and self._to == other._to
            # and self.dialogue_reference == other.dialogue_reference  # noqa: E800
            # and self.message_id == other.message_id  # noqa: E800
            # and self.target == other.target  # noqa: E800
            # and self.performative == other.performative  # noqa: E800
            and self._body == other._body
        )

    def __str__(self):
        """Get the string representation of the message."""
        return (
            "Message(sender={},to={},".format(self._sender, self._to)
            + ",".join(
                map(
                    lambda key_value: str(key_value[0]) + "=" + str(key_value[1]),
                    self._body.items(),
                )
            )
            + ")"
        )

    def encode(self) -> bytes:
        """Encode the message."""
        return self.serializer.encode(self)

    @property
    def has_dialogue_info(self) -> bool:
        """
        Check whether a message has the dialogue fields populated.

        More precisely, it checks whether the fields 'message_id',
        'target' and 'dialogue_reference' are set.

        :return: True if the message has the dialogue fields set, False otherwise.
        """
        return (
            self.is_set("message_id")
            and self.is_set("target")
            and self.is_set("dialogue_reference")
        )


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
        """
        Encode a message into bytes using Protobuf.

        - if one of message_id, target and dialogue_reference are not defined,
          serialize only the message body/
        - otherwise, extract those fields from the body and instantiate
          a Message struct.
        """
        message_pb = ProtobufMessage()
        if msg.has_dialogue_info:
            dialogue_message_pb = DialogueMessage()
            dialogue_message_pb.message_id = msg.message_id
            dialogue_message_pb.dialogue_starter_reference = msg.dialogue_reference[0]
            dialogue_message_pb.dialogue_responder_reference = msg.dialogue_reference[1]
            dialogue_message_pb.target = msg.target

            new_body = copy(msg._body)  # pylint: disable=protected-access
            new_body.pop("message_id")
            new_body.pop("dialogue_reference")
            new_body.pop("target")

            body_json = Struct()
            body_json.update(new_body)  # pylint: disable=no-member

            dialogue_message_pb.content = (  # pylint: disable=no-member
                body_json.SerializeToString()
            )
            message_pb.dialogue_message.CopyFrom(  # pylint: disable=no-member
                dialogue_message_pb
            )
        else:
            body_json = Struct()
            body_json.update(msg._body)  # pylint: disable=no-member,protected-access
            message_pb.body.CopyFrom(body_json)  # pylint: disable=no-member

        return message_pb.SerializeToString()

    @staticmethod
    def decode(obj: bytes) -> Message:
        """
        Decode bytes into a message using Protobuf.

        First, try to parse the input as a Protobuf 'Message';
        if it fails, parse the bytes as struct.
        """
        message_pb = ProtobufMessage()
        message_pb.ParseFromString(obj)
        message_type = message_pb.WhichOneof("message")
        if message_type == "body":
            body = dict(message_pb.body)  # pylint: disable=no-member
            msg = Message(_body=body)
            return msg
        if message_type == "dialogue_message":
            dialogue_message_pb = (
                message_pb.dialogue_message  # pylint: disable=no-member
            )
            message_id = dialogue_message_pb.message_id
            target = dialogue_message_pb.target
            dialogue_starter_reference = dialogue_message_pb.dialogue_starter_reference
            dialogue_responder_reference = (
                dialogue_message_pb.dialogue_responder_reference
            )
            body_json = Struct()
            body_json.ParseFromString(dialogue_message_pb.content)
            body = dict(body_json)
            body["message_id"] = message_id
            body["target"] = target
            body["dialogue_reference"] = (
                dialogue_starter_reference,
                dialogue_responder_reference,
            )
            return Message(_body=body)
        raise ValueError("Message type not recognized.")  # pragma: nocover


class Protocol(Component):
    """
    This class implements a specifications for a protocol.

    It includes a serializer to encode/decode a message.
    """

    def __init__(
        self, configuration: ProtocolConfig, message_class: Type[Message], **kwargs
    ):
        """
        Initialize the protocol manager.

        :param configuration: the protocol configurations.
        :param message_class: the message class.
        """
        super().__init__(configuration, **kwargs)

        self._message_class = message_class

    @property
    def serializer(self) -> Type[Serializer]:
        """Get the serializer."""
        return self._message_class.serializer

    @classmethod
    def from_dir(cls, directory: str, **kwargs) -> "Protocol":
        """
        Load the protocol from a directory.

        :param directory: the directory to the skill package.
        :return: the protocol object.
        """
        configuration = cast(
            ProtocolConfig,
            load_component_configuration(ComponentType.PROTOCOL, Path(directory)),
        )
        configuration.directory = Path(directory)
        return Protocol.from_config(configuration, **kwargs)

    @classmethod
    def from_config(cls, configuration: ProtocolConfig, **kwargs) -> "Protocol":
        """
        Load the protocol from configuration.

        :param configuration: the protocol configuration.
        :return: the protocol object.
        """
        if configuration.directory is None:  # pragma: nocover
            raise ValueError("Configuration must be associated with a directory.")
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
        enforce(len(message_classes) == 1, "Not exactly one message class detected.")
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
        enforce(
            len(serializer_classes) == 1, "Not exactly one serializer class detected."
        )
        serialize_class = serializer_classes[0][1]
        message_class.serializer = serialize_class

        return Protocol(configuration, message_class, **kwargs)
