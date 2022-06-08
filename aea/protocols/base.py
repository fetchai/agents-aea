# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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
from base64 import b64decode, b64encode
from copy import copy
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional, Set, Tuple, Type, cast

from aea.components.base import Component, load_aea_package
from aea.configurations.base import ComponentType, ProtocolConfig, PublicId
from aea.configurations.loader import load_component_configuration
from aea.exceptions import AEAComponentLoadException, enforce


_default_logger = logging.getLogger(__name__)

MAX_PRINT_INNER = 600
MAX_PRINT_OUTER = 2000
Address = str


class Message:
    """This class implements a message."""

    protocol_id = None  # type: PublicId
    protocol_specification_id = None  # type: PublicId
    serializer = None  # type: Type["Serializer"]

    __slots__ = ("_slots", "_to", "_sender")

    class Performative(Enum):
        """Performatives for the base message."""

        def __str__(self) -> str:
            """Get the string representation."""
            return str(self.value)

    class _SlotsCls:  # pylint: disable=too-few-public-methods
        __slots__: Tuple[str, ...] = (
            "performative",
            "dialogue_reference",
            "message_id",
            "target",
        )

    _performatives: Set[str] = set()

    def __init__(self, _body: Optional[Dict] = None, **kwargs: Any) -> None:
        """
        Initialize a Message object.

        :param _body: the dictionary of values to hold.
        :param kwargs: any additional value to add to the body. It will overwrite the body values.
        """
        self._slots = self._SlotsCls()

        self._to: Optional[Address] = None
        self._sender: Optional[Address] = None

        self._update_slots_from_dict(copy(_body) if _body else {})
        self._update_slots_from_dict(kwargs)

        try:
            self._is_consistent()
        except Exception as e:  # pylint: disable=broad-except
            _default_logger.error(e)

    def json(self) -> dict:
        """Get json friendly str representation of the message."""
        return {
            "to": self._to,
            "sender": self._sender,
            "body": b64encode(self.encode()).decode("utf-8"),
        }

    @classmethod
    def from_json(cls, data: dict) -> "Message":
        """Construct message instance from json data."""
        try:
            instance = cls.decode(b64decode(data["body"]))
            sender = data["sender"]
            if sender:
                instance.sender = sender
            to = data["to"]
            if to:
                instance.to = to
            return instance
        except KeyError:  # pragma: nocover
            raise ValueError(f"Message representation is invalid: {data}")

    @property
    def valid_performatives(self) -> Set[str]:
        """Get valid performatives."""
        return self._performatives

    @property
    def has_sender(self) -> bool:
        """Check if it has a sender."""
        return self._sender is not None

    @property
    def sender(self) -> Address:
        """Get the sender of the message in Address form."""
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
        return {
            key: self.get(key) for key in self._SlotsCls.__slots__ if self.is_set(key)
        }

    @_body.setter
    def _body(self, body: Dict) -> None:
        """
        Set the body of the message.

        :param body: the body.
        """
        self._slots = self._SlotsCls()  # new instance to clean up all data
        self._update_slots_from_dict(body)

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
        """
        if value is None and not hasattr(self._slots, key):
            return
        if value is None and hasattr(self._slots, key):
            delattr(self._slots, key)
            return
        try:
            setattr(self._slots, key, value)
        except AttributeError as e:  # pragma: nocover
            raise ValueError(f"Field `{key}` is not supported {e}")

    def get(self, key: str) -> Optional[Any]:
        """Get value for key."""
        return getattr(self._slots, key, None)

    def is_set(self, key: str) -> bool:
        """Check value is set for key."""
        return hasattr(self._slots, key)

    def _update_slots_from_dict(self, data: dict) -> None:
        """Update slots value with data from dict."""
        for key, value in data.items():
            self.set(key, value)

    def _is_consistent(self) -> bool:  # pylint: disable=no-self-use
        """Check that the data is consistent."""
        return True

    def __eq__(self, other: Any) -> bool:
        """Compare with another object."""
        return (
            isinstance(other, Message)
            and self._sender == other._sender
            and self._to == other._to
            and self._body == other._body
        )

    def __repr__(self) -> str:
        """Get the representation of the message."""
        body = ",".join(
            map(
                lambda key_value: f"{str(key_value[0])}={str(key_value[1])}",
                self._body.items(),
            )
        )
        return f"Message(sender={self._sender},to={self._to},{body})"

    def __str__(self) -> str:
        """Get the string representation of the message. Abbreviated to prevent spamming of logs."""
        body = ",".join(
            map(
                lambda key_value: f"{str(key_value[0])[:MAX_PRINT_INNER]}={str(key_value[1])[:MAX_PRINT_INNER]}",
                self._body.items(),
            )
        )
        return f"Message(sender={self._sender},to={self._to},{body})"[:MAX_PRINT_OUTER]

    def encode(self) -> bytes:
        """Encode the message."""
        return self.serializer.encode(self)

    @classmethod
    def decode(cls, data: bytes) -> "Message":
        """Decode the message."""
        return cls.serializer.decode(data)

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


class Protocol(Component):
    """
    This class implements a specifications for a protocol.

    It includes a serializer to encode/decode a message.
    """

    __slots__ = ("_message_class",)

    def __init__(
        self, configuration: ProtocolConfig, message_class: Type[Message], **kwargs: Any
    ) -> None:
        """
        Initialize the protocol manager.

        :param configuration: the protocol configurations.
        :param message_class: the message class.
        :param kwargs: the keyword arguments.
        """
        super().__init__(configuration, **kwargs)
        self._message_class = message_class

    @property
    def serializer(self) -> Type[Serializer]:
        """Get the serializer."""
        return self._message_class.serializer

    @classmethod
    def from_dir(cls, directory: str, **kwargs: Any) -> "Protocol":
        """
        Load the protocol from a directory.

        :param directory: the directory to the skill package.
        :param kwargs: the keyword arguments.
        :return: the protocol object.
        """
        configuration = cast(
            ProtocolConfig,
            load_component_configuration(ComponentType.PROTOCOL, Path(directory)),
        )
        configuration.directory = Path(directory)
        return Protocol.from_config(configuration, **kwargs)

    @classmethod
    def from_config(cls, configuration: ProtocolConfig, **kwargs: Any) -> "Protocol":
        """
        Load the protocol from configuration.

        :param configuration: the protocol configuration.
        :param kwargs: the keyword arguments.
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
            filter(lambda x: re.match(f"{name_camel_case}Message", x[0]), classes)
        )
        if len(message_classes) != 1:  # pragma: nocover
            raise AEAComponentLoadException("Not exactly one message class detected.")
        message_class = message_classes[0][1]
        class_module = importlib.import_module(
            configuration.prefix_import_path + ".serialization"
        )
        classes = inspect.getmembers(class_module, inspect.isclass)
        serializer_classes = list(
            filter(
                lambda x: re.match(f"{name_camel_case}Serializer", x[0]),
                classes,
            )
        )
        if len(serializer_classes) != 1:  # pragma: nocover
            raise AEAComponentLoadException(
                "Not exactly one serializer class detected."
            )
        serialize_class = serializer_classes[0][1]
        message_class.serializer = serialize_class

        return Protocol(configuration, message_class, **kwargs)

    @property
    def protocol_id(self) -> PublicId:
        """Get protocol id."""
        return cast(ProtocolConfig, self._configuration).public_id

    @property
    def protocol_specification_id(self) -> PublicId:
        """Get protocol specification id."""
        return cast(ProtocolConfig, self._configuration).protocol_specification_id

    def __repr__(self) -> str:
        """Get str representation of the protocol."""
        return f"Protocol({self.protocol_id})"
