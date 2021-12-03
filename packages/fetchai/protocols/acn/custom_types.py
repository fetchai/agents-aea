# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021 aea
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

"""This module contains class representations corresponding to every custom type in the protocol specification."""

from enum import Enum
from typing import Any, List

from aea.helpers.base import SimpleId, SimpleIdOrStr


class AgentRecord:
    """
    This class represents an instance of AgentRecord.

    Eventually needs to be unified with `aea.helpers.acn.agent_record`.
    """

    __slots__ = (
        "_address",
        "_public_key",
        "_peer_public_key",
        "_signature",
        "_service_id",
        "_ledger_id",
        "_message_format",
        "_message",
    )

    def __init__(
        self,
        address: str,
        public_key: str,
        peer_public_key: str,
        signature: str,
        service_id: SimpleIdOrStr,
        ledger_id: SimpleIdOrStr,
    ) -> None:
        """Initialise an instance of AgentRecord."""
        self._address = address
        self._public_key = public_key
        self._peer_public_key = peer_public_key
        self._signature = signature
        self._service_id = str(SimpleId(service_id))
        self._ledger_id = str(SimpleId(ledger_id))

    @property
    def address(self) -> str:
        """Get agent address"""
        return self._address

    @property
    def public_key(self) -> str:
        """Get agent public key"""
        return self._public_key

    @property
    def peer_public_key(self) -> str:
        """Get agent representative's public key"""
        return self._peer_public_key

    @property
    def signature(self) -> str:
        """Get record signature"""
        return self._signature

    @property
    def service_id(self) -> SimpleIdOrStr:
        """Get the identifier."""
        return self._service_id

    @property
    def ledger_id(self) -> SimpleIdOrStr:
        """Get ledger id."""
        return self._ledger_id

    @staticmethod
    def encode(
        agent_record_protobuf_object: Any, agent_record_object: "AgentRecord"
    ) -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the agent_record_protobuf_object argument is matched with the instance of this class in the 'agent_record_object' argument.

        :param agent_record_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param agent_record_object: an instance of this class to be encoded in the protocol buffer object.
        """
        agent_record_protobuf_object.address = agent_record_object.address
        agent_record_protobuf_object.public_key = agent_record_object.public_key
        agent_record_protobuf_object.peer_public_key = (
            agent_record_object.peer_public_key
        )
        agent_record_protobuf_object.signature = agent_record_object.signature
        agent_record_protobuf_object.service_id = agent_record_object.service_id
        agent_record_protobuf_object.ledger_id = agent_record_object.ledger_id

    @classmethod
    def decode(cls, agent_record_protobuf_object: Any) -> "AgentRecord":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class is created that matches the protocol buffer object in the 'agent_record_protobuf_object' argument.

        :param agent_record_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'agent_record_protobuf_object' argument.
        """
        record = cls(
            address=agent_record_protobuf_object.address,
            public_key=agent_record_protobuf_object.public_key,
            peer_public_key=agent_record_protobuf_object.peer_public_key,
            signature=agent_record_protobuf_object.signature,
            service_id=agent_record_protobuf_object.service_id,
            ledger_id=agent_record_protobuf_object.ledger_id,
        )
        return record

    def __eq__(self, other: Any) -> bool:
        """Compare to objects of this class."""
        return (
            isinstance(other, AgentRecord)
            and self.address == other.address
            and self.public_key == other.public_key
        )


class StatusBody:
    """This class represents an instance of StatusBody."""

    __slots__ = (
        "_status_code",
        "_msgs",
    )

    class StatusCode(Enum):
        """Status code enum."""

        SUCCESS = 0
        ERROR_UNSUPPORTED_VERSION = 1
        ERROR_UNEXPECTED_PAYLOAD = 2
        ERROR_GENERIC = 3
        ERROR_DECODE = 4

        ERROR_WRONG_AGENT_ADDRESS = 10
        ERROR_WRONG_PUBLIC_KEY = 11
        ERROR_INVALID_PROOF = 12
        ERROR_UNSUPPORTED_LEDGER = 13

        ERROR_UNKNOWN_AGENT_ADDRESS = 20
        ERROR_AGENT_NOT_READY = 21

        def __int__(self) -> int:
            """Get string representation."""
            return self.value

    def __init__(self, status_code: StatusCode, msgs: List[str]) -> None:
        """Initialise an instance of StatusBody."""
        self._status_code = status_code
        self._msgs = msgs

    @property
    def status_code(self) -> "StatusCode":
        """Get the status code."""
        return self._status_code

    @property
    def msgs(self) -> List[str]:
        """Get the list of messages."""
        return self._msgs

    @staticmethod
    def encode(
        status_body_protobuf_object: Any, status_body_object: "StatusBody"
    ) -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the status_body_protobuf_object argument is matched with the instance of this class in the 'status_body_object' argument.

        :param status_body_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param status_body_object: an instance of this class to be encoded in the protocol buffer object.
        """
        status_body_protobuf_object.code = int(status_body_object.status_code)
        status_body_protobuf_object.msgs.extend(status_body_object.msgs)

    @classmethod
    def decode(cls, status_body_protobuf_object: Any) -> "StatusBody":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class is created that matches the protocol buffer object in the 'status_body_protobuf_object' argument.

        :param status_body_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'status_body_protobuf_object' argument.
        """
        status_body = cls(
            status_code=cls.StatusCode(status_body_protobuf_object.code),
            msgs=status_body_protobuf_object.msgs,
        )
        return status_body

    def __eq__(self, other: Any) -> bool:
        """Compare to objects of this class."""
        return (
            isinstance(other, StatusBody)
            and self.status_code == other.status_code
            and self.msgs == other.msgs
        )
