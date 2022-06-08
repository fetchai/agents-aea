# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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
"""Mail module abstract base classes."""

import logging
from abc import ABC, abstractmethod
from typing import Any, Optional, Union
from urllib.parse import urlparse

from aea.common import Address
from aea.configurations.base import PublicId
from aea.exceptions import enforce
from aea.mail import base_pb2
from aea.protocols.base import Message


_default_logger = logging.getLogger(__name__)


class URI:
    """URI following RFC3986."""

    __slots__ = ("_uri_raw",)

    def __init__(self, uri_raw: str) -> None:
        """
        Initialize the URI.

        Must follow: https://tools.ietf.org/html/rfc3986.html

        :param uri_raw: the raw form uri
        """
        self._uri_raw = uri_raw

    @property
    def scheme(self) -> str:
        """Get the scheme."""
        parsed = urlparse(self._uri_raw)
        return parsed.scheme

    @property
    def netloc(self) -> str:
        """Get the netloc."""
        parsed = urlparse(self._uri_raw)
        return parsed.netloc

    @property
    def path(self) -> str:
        """Get the path."""
        parsed = urlparse(self._uri_raw)
        return parsed.path

    @property
    def params(self) -> str:
        """Get the params."""
        parsed = urlparse(self._uri_raw)
        return parsed.params

    @property
    def query(self) -> str:
        """Get the query."""
        parsed = urlparse(self._uri_raw)
        return parsed.query

    @property
    def fragment(self) -> str:
        """Get the fragment."""
        parsed = urlparse(self._uri_raw)
        return parsed.fragment

    @property
    def username(self) -> Optional[str]:
        """Get the username."""
        parsed = urlparse(self._uri_raw)
        return parsed.username

    @property
    def password(self) -> Optional[str]:
        """Get the password."""
        parsed = urlparse(self._uri_raw)
        return parsed.password

    @property
    def host(self) -> Optional[str]:
        """Get the host."""
        parsed = urlparse(self._uri_raw)
        return parsed.hostname

    @property
    def port(self) -> Optional[int]:
        """Get the port."""
        parsed = urlparse(self._uri_raw)
        return parsed.port

    def __str__(self) -> str:
        """Get string representation."""
        return self._uri_raw

    def __eq__(self, other: Any) -> bool:
        """Compare with another object."""
        return isinstance(other, URI) and str(self) == str(other)


class EnvelopeContext:
    """Contains context information of an envelope."""

    __slots__ = ("_connection_id", "_uri")

    def __init__(
        self,
        connection_id: Optional[PublicId] = None,
        uri: Optional[URI] = None,
    ) -> None:
        """
        Initialize the envelope context.

        :param connection_id: the connection id used for routing the outgoing envelope in the multiplexer.
        :param uri: the URI sent with the envelope.
        """
        self._connection_id = connection_id
        self._uri = uri

    @property
    def uri(self) -> Optional[URI]:
        """Get the URI."""
        return self._uri

    @property
    def connection_id(self) -> Optional[PublicId]:
        """Get the connection id to route the envelope."""
        return self._connection_id

    @connection_id.setter
    def connection_id(self, connection_id: PublicId) -> None:
        """Set the 'via' connection id."""
        if self._connection_id is not None:
            raise ValueError("connection_id already set!")  # pragma: nocover
        self._connection_id = connection_id

    def __str__(self) -> str:
        """Get the string representation."""
        return f"EnvelopeContext(connection_id={self.connection_id}, uri={self.uri})"

    def __eq__(self, other: Any) -> bool:
        """Compare with another object."""
        return (
            isinstance(other, EnvelopeContext)
            and self.connection_id == other.connection_id
            and self.uri == other.uri
        )


class AEAConnectionError(Exception):
    """Exception class for connection errors."""


class Empty(Exception):
    """Exception for when the inbox is empty."""


class EnvelopeSerializer(ABC):
    """Abstract class to specify the serialization layer for the envelope."""

    @abstractmethod
    def encode(self, envelope: "Envelope") -> bytes:
        """
        Encode the envelope.

        :param envelope: the envelope to encode
        :return: the encoded envelope
        """

    @abstractmethod
    def decode(self, envelope_bytes: bytes) -> "Envelope":
        """
        Decode the envelope.

        :param envelope_bytes: the encoded envelope
        :return: the envelope
        """


class ProtobufEnvelopeSerializer(EnvelopeSerializer):
    """Envelope serializer using Protobuf."""

    def encode(self, envelope: "Envelope") -> bytes:
        """
        Encode the envelope.

        :param envelope: the envelope to encode
        :return: the encoded envelope
        """
        envelope_pb = base_pb2.Envelope()
        envelope_pb.to = envelope.to
        envelope_pb.sender = envelope.sender
        envelope_pb.protocol_id = str(envelope.protocol_specification_id)
        envelope_pb.message = envelope.message_bytes
        if envelope.context is not None and envelope.context.uri is not None:
            envelope_pb.uri = str(envelope.context.uri)

        envelope_bytes = envelope_pb.SerializeToString()
        return envelope_bytes

    def decode(self, envelope_bytes: bytes) -> "Envelope":
        """
        Decode the envelope.

        The default serializer doesn't decode the message field.

        :param envelope_bytes: the encoded envelope
        :return: the envelope
        """
        envelope_pb = base_pb2.Envelope()
        envelope_pb.ParseFromString(envelope_bytes)

        to = envelope_pb.to  # pylint: disable=no-member
        sender = envelope_pb.sender  # pylint: disable=no-member
        raw_protocol_id = envelope_pb.protocol_id  # pylint: disable=no-member
        protocol_specification_id = PublicId.from_str(raw_protocol_id)
        message = envelope_pb.message  # pylint: disable=no-member

        uri_raw = envelope_pb.uri  # pylint: disable=no-member
        if uri_raw != "":  # empty string means this field is not set in proto3
            uri = URI(uri_raw=uri_raw)
            context = EnvelopeContext(uri=uri)
            envelope = Envelope(
                to=to,
                sender=sender,
                protocol_specification_id=protocol_specification_id,
                message=message,
                context=context,
            )
        else:
            envelope = Envelope(
                to=to,
                sender=sender,
                protocol_specification_id=protocol_specification_id,
                message=message,
            )

        return envelope


DefaultEnvelopeSerializer = ProtobufEnvelopeSerializer


class Envelope:
    """The top level message class for agent to agent communication."""

    default_serializer = DefaultEnvelopeSerializer()

    __slots__ = ("_to", "_sender", "_protocol_specification_id", "_message", "_context")

    def __init__(
        self,
        to: Address,
        sender: Address,
        message: Union[Message, bytes],
        context: Optional[EnvelopeContext] = None,
        protocol_specification_id: Optional[PublicId] = None,
    ) -> None:
        """
        Initialize a Message object.

        :param to: the address of the receiver.
        :param sender: the address of the sender.
        :param message: the protocol-specific message.
        :param context: the optional envelope context.
        :param protocol_specification_id: the protocol specification id (wire id).
        """
        enforce(isinstance(to, str), f"To must be string. Found '{type(to)}'")
        enforce(
            isinstance(sender, str), f"Sender must be string. Found '{type(sender)}'"
        )
        enforce(
            isinstance(message, (Message, bytes)),
            "message should be a type of Message or bytes!",
        )

        if isinstance(message, Message):
            message = self._check_consistency(message, to, sender)

        self._to = to
        self._sender = sender

        enforce(
            self.is_to_public_id == self.is_sender_public_id,
            "To and sender must either both be agent addresses or both be public ids of AEA components.",
        )

        if isinstance(message, bytes):
            if protocol_specification_id is None:
                raise ValueError(
                    "Message is bytes object, protocol_specification_id must be provided!"
                )
        elif isinstance(message, Message):
            if message.protocol_id is None:
                raise ValueError(  # pragma: nocover
                    f"message class {type(message)} has no protocol_id specified!"
                )
            protocol_specification_id = message.protocol_specification_id
            if protocol_specification_id is None:
                raise ValueError(
                    "Message is Message object, protocol_specification_id could not be resolved! Ensure protocol is valid!"
                )
        else:
            raise ValueError(
                f"Message type: {type(message)} is not supported!"
            )  # pragma: nocover

        self._protocol_specification_id: PublicId = protocol_specification_id
        self._message = message
        if self.is_component_to_component_message:
            enforce(
                context is None,
                "EnvelopeContext must be None for component to component messages.",
            )
        self._context = context

    @property
    def to(self) -> Address:
        """Get address of receiver."""
        return self._to

    @to.setter
    def to(self, to: Address) -> None:
        """Set address of receiver."""
        enforce(isinstance(to, str), f"To must be string. Found '{type(to)}'")
        self._to = to

    @property
    def sender(self) -> Address:
        """Get address of sender."""
        return self._sender

    @sender.setter
    def sender(self, sender: Address) -> None:
        """Set address of sender."""
        enforce(
            isinstance(sender, str), f"Sender must be string. Found '{type(sender)}'"
        )
        self._sender = sender

    @property
    def protocol_specification_id(self) -> PublicId:
        """Get protocol_specification_id."""
        return self._protocol_specification_id

    @property
    def message(self) -> Union[Message, bytes]:
        """Get the protocol-specific message."""
        return self._message

    @message.setter
    def message(self, message: Union[Message, bytes]) -> None:
        """Set the protocol-specific message."""
        self._message = message

    @property
    def message_bytes(self) -> bytes:
        """Get the protocol-specific message."""
        if isinstance(self._message, Message):
            return self._message.encode()
        return self._message

    @property
    def context(self) -> Optional[EnvelopeContext]:
        """Get the envelope context."""
        return self._context

    @property
    def to_as_public_id(self) -> Optional[PublicId]:
        """Get to as public id."""
        return PublicId.try_from_str(self.to)

    @property
    def is_sender_public_id(self) -> bool:
        """Check if sender is a public id."""
        return PublicId.is_valid_str(self.sender)

    @property
    def is_to_public_id(self) -> bool:
        """Check if to is a public id."""
        return PublicId.is_valid_str(self.to)

    @property
    def is_component_to_component_message(self) -> bool:
        """Whether or not the message contained is component to component."""
        return self.is_to_public_id and self.is_sender_public_id

    @staticmethod
    def _check_consistency(message: Message, to: str, sender: str) -> Message:
        """Check consistency of sender and to."""
        if message.has_to:
            enforce(
                message.to == to, "To specified on message does not match envelope."
            )
        else:
            message.to = to
        if message.has_sender:
            enforce(
                message.sender == sender,
                "Sender specified on message does not match envelope.",
            )
        else:
            message.sender = sender
        return message

    def __eq__(self, other: Any) -> bool:
        """Compare with another object."""
        return (
            isinstance(other, Envelope)
            and self.to == other.to
            and self.sender == other.sender
            and self.protocol_specification_id == other.protocol_specification_id
            and self.message == other.message
            and self.context == other.context
        )

    def encode(
        self,
        serializer: Optional[EnvelopeSerializer] = None,
    ) -> bytes:
        """
        Encode the envelope.

        :param serializer: the serializer that implements the encoding procedure.
        :return: the encoded envelope.
        """
        if serializer is None:
            serializer = self.default_serializer
        envelope_bytes = serializer.encode(self)
        return envelope_bytes

    @classmethod
    def decode(
        cls, envelope_bytes: bytes, serializer: Optional[EnvelopeSerializer] = None
    ) -> "Envelope":
        """
        Decode the envelope.

        :param envelope_bytes: the bytes to be decoded.
        :param serializer: the serializer that implements the decoding procedure.
        :return: the decoded envelope.
        """
        if serializer is None:
            serializer = cls.default_serializer
        envelope = serializer.decode(envelope_bytes)
        return envelope

    def __str__(self) -> str:
        """Get the string representation of an envelope."""
        return "Envelope(to={to}, sender={sender}, protocol_specification_id={protocol_specification_id}, message={message})".format(
            to=self.to,
            sender=self.sender,
            protocol_specification_id=self.protocol_specification_id,
            message="{!r}".format(self.message)
            if isinstance(self.message, bytes)
            else self.message,
        )
