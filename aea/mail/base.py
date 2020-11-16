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
"""Mail module abstract base classes."""

import logging
from abc import ABC, abstractmethod
from typing import Optional, Tuple, Union
from urllib.parse import urlparse

from aea.common import Address
from aea.configurations.base import PackageId, PublicId
from aea.configurations.constants import CONNECTION, SKILL
from aea.exceptions import enforce
from aea.mail import base_pb2
from aea.protocols.base import Message


_default_logger = logging.getLogger(__name__)


class AEAConnectionError(Exception):
    """Exception class for connection errors."""


class Empty(Exception):
    """Exception for when the inbox is empty."""


class URI:
    """URI following RFC3986."""

    def __init__(self, uri_raw: str):
        """
        Initialize the URI.

        Must follow: https://tools.ietf.org/html/rfc3986.html

        :param uri_raw: the raw form uri
        :raises ValueError: if uri_raw is not RFC3986 compliant
        """
        self.uri_raw = uri_raw
        parsed = urlparse(uri_raw)
        self._scheme = parsed.scheme
        self._netloc = parsed.netloc
        self._path = parsed.path
        self._params = parsed.params
        self._query = parsed.query
        self._fragment = parsed.fragment
        self._username = parsed.username
        self._password = parsed.password
        self._host = parsed.hostname
        self._port = parsed.port

    @property
    def scheme(self) -> str:
        """Get the scheme."""
        return self._scheme

    @property
    def netloc(self) -> str:
        """Get the netloc."""
        return self._netloc

    @property
    def path(self) -> str:
        """Get the path."""
        return self._path

    @property
    def params(self) -> str:
        """Get the params."""
        return self._params

    @property
    def query(self) -> str:
        """Get the query."""
        return self._query

    @property
    def fragment(self) -> str:
        """Get the fragment."""
        return self._fragment

    @property
    def username(self) -> Optional[str]:
        """Get the username."""
        return self._username

    @property
    def password(self) -> Optional[str]:
        """Get the password."""
        return self._password

    @property
    def host(self) -> Optional[str]:
        """Get the host."""
        return self._host

    @property
    def port(self) -> Optional[int]:
        """Get the port."""
        return self._port

    def __str__(self):
        """Get string representation."""
        return self.uri_raw

    def __eq__(self, other):
        """Compare with another object."""
        return (
            isinstance(other, URI)
            and self.scheme == other.scheme
            and self.netloc == other.netloc
            and self.path == other.path
            and self.params == other.params
            and self.query == other.query
            and self.fragment == other.fragment
            and self.username == other.username
            and self.password == other.password
            and self.host == other.host
            and self.port == other.port
        )


class EnvelopeContext:
    """Extra information for the handling of an envelope."""

    def __init__(
        self,
        connection_id: Optional[PublicId] = None,
        skill_id: Optional[PublicId] = None,
        uri: Optional[URI] = None,
    ):
        """
        Initialize the envelope context.

        :param connection_id: the connection id used for routing the outgoing envelope in the multiplexer.
        :param skill_id: the skill id used for routing the incoming envelope in the AEA.
        :param uri: the URI sent with the envelope.
        """
        skill_id_from_uri, connection_id_from_uri = (
            self._get_public_ids_from_uri(uri) if uri is not None else (None, None)
        )
        if connection_id_from_uri and connection_id:
            raise ValueError("Cannot define connection_id explicitly and in URI.")
        self._connection_id = connection_id or connection_id_from_uri
        if skill_id_from_uri and skill_id:
            raise ValueError("Cannot define skill_id explicitly and in URI.")
        self._skill_id = skill_id or skill_id_from_uri
        self.uri = uri

    @property
    def connection_id(self) -> Optional[PublicId]:
        """Get the connection id."""
        return self._connection_id

    @property
    def skill_id(self) -> Optional[PublicId]:
        """Get the skill id."""
        return self._skill_id

    @property
    def uri_raw(self) -> str:
        """Get uri in string format."""
        return str(self.uri) if self.uri is not None else ""

    @staticmethod
    def _get_public_ids_from_uri(
        uri: URI,
    ) -> Tuple[Optional[PublicId], Optional[PublicId]]:
        """
        Try get skill and connection id from uri.

        :param uri: the uri
        :return: (skill_id if present in uri, connection if present in uri)
        """
        skill_id = None
        connection_id = None
        try:
            package_id = PackageId.from_uri_path(uri.path)
            package_type = str(package_id.package_type)
            if package_type == SKILL:
                skill_id = package_id.public_id
            elif package_type == CONNECTION:
                connection_id = package_id.public_id
            else:
                raise ValueError(
                    f"Invalid package type {package_type} in uri for envelope context."
                )
        except ValueError as e:
            _default_logger.debug(
                f"URI - {uri.path} - not a valid package_id id. Error: {e}"
            )
        return (skill_id, connection_id)

    def __str__(self):
        """Get the string representation."""
        return f"EnvelopeContext(connection_id={self.connection_id}, skill_id={self.skill_id}, uri_raw={self.uri_raw})"

    def __eq__(self, other):
        """Compare with another object."""
        return (
            isinstance(other, EnvelopeContext)
            and self.connection_id == other.connection_id
            and self.skill_id == other.skill_id
            and self.uri == other.uri
        )


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
        envelope_pb.protocol_id = str(envelope.protocol_id)
        envelope_pb.message = envelope.message_bytes
        if envelope.context is not None and envelope.context.uri_raw != "":
            envelope_pb.uri = envelope.context.uri_raw

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
        protocol_id = PublicId.from_str(raw_protocol_id)
        message = envelope_pb.message  # pylint: disable=no-member

        uri_raw = envelope_pb.uri  # pylint: disable=no-member
        if uri_raw != "":  # empty string means this field is not set in proto3
            uri = URI(uri_raw=uri_raw)
            context = EnvelopeContext(uri=uri)
            envelope = Envelope(
                to=to,
                sender=sender,
                protocol_id=protocol_id,
                message=message,
                context=context,
            )
        else:
            envelope = Envelope(
                to=to, sender=sender, protocol_id=protocol_id, message=message,
            )

        return envelope


DefaultEnvelopeSerializer = ProtobufEnvelopeSerializer


class Envelope:
    """The top level message class for agent to agent communication."""

    default_serializer = DefaultEnvelopeSerializer()

    def __init__(
        self,
        to: Address,
        sender: Address,
        protocol_id: PublicId,
        message: Union[Message, bytes],
        context: Optional[EnvelopeContext] = None,
    ):
        """
        Initialize a Message object.

        :param to: the address of the receiver.
        :param sender: the address of the sender.
        :param protocol_id: the protocol id.
        :param message: the protocol-specific message.
        :param context: the optional envelope context.
        """
        enforce(isinstance(to, str), f"To must be string. Found '{type(to)}'")
        enforce(
            isinstance(sender, str), f"Sender must be string. Found '{type(sender)}'"
        )
        if isinstance(message, Message):
            message = self._check_consistency(message, to, sender)
        self._to = to
        self._sender = sender
        self._protocol_id = protocol_id
        self._message = message
        self._context = context if context is not None else EnvelopeContext()

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
    def protocol_id(self) -> PublicId:
        """Get protocol id."""
        return self._protocol_id

    @protocol_id.setter
    def protocol_id(self, protocol_id: PublicId) -> None:
        """Set the protocol id."""
        self._protocol_id = protocol_id

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
    def context(self) -> EnvelopeContext:
        """Get the envelope context."""
        return self._context

    @property
    def skill_id(self) -> Optional[PublicId]:
        """
        Get the skill id from an envelope context, if set.

        :return: skill id
        """
        skill_id = None  # Optional[PublicId]
        if self.context is not None:
            skill_id = self.context.skill_id
        return skill_id

    @property
    def connection_id(self) -> Optional[PublicId]:
        """
        Get the connection id from an envelope context, if set.

        :return: connection id
        """
        connection_id = None  # Optional[PublicId]
        if self.context is not None:
            connection_id = self.context.connection_id
        return connection_id

    @property
    def is_sender_public_id(self):
        """Check if sender is a public id."""
        return PublicId.is_valid_str(self.sender)

    @property
    def is_to_public_id(self):
        """Check if to is a public id."""
        return PublicId.is_valid_str(self.to)

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

    def __eq__(self, other):
        """Compare with another object."""
        return (
            isinstance(other, Envelope)
            and self.to == other.to
            and self.sender == other.sender
            and self.protocol_id == other.protocol_id
            and self.message == other.message
            and self.context == other.context
        )

    def encode(self, serializer: Optional[EnvelopeSerializer] = None,) -> bytes:
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

    def __str__(self):
        """Get the string representation of an envelope."""
        return "Envelope(to={to}, sender={sender}, protocol_id={protocol_id}, message={message})".format(
            to=self.to,
            sender=self.sender,
            protocol_id=self.protocol_id,
            message=self.message,
        )
