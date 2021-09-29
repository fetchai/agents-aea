# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2020 fetchai
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
from typing import Any, Dict

from aea.exceptions import enforce
from aea.helpers.search.models import Description as BaseDescription
from aea.helpers.search.models import Query as BaseQuery
from aea.helpers.serializers import DictProtobufStructSerializer


Description = BaseDescription


class AgentsInfo:
    """This class represents an instance of AgentsInfo."""

    __slots__ = ("_body",)

    def __init__(self, body: Dict[str, Dict[str, Any]]):
        """Initialise an instance of AgentsInfo."""
        self._body = body
        self._check_consistency()

    def _check_consistency(self) -> None:
        """Check consistency of the object."""
        if self._body is None:
            raise ValueError("body must not be None")
        enforce(
            isinstance(self._body, dict)
            and all([isinstance(key, str) for key in self._body.keys()])
            and all([isinstance(value, dict) for value in self._body.values()]),
            "Body must be dict and keys must be str and values must be dict.",
        )

    @property
    def body(self) -> Dict[str, Dict[str, Any]]:
        """Get the body."""
        return self._body

    def get_info_for_agent(self, agent_address: str) -> Dict[str, Any]:
        """Get the info for the agent address."""
        return self._body.get(agent_address, {})

    @staticmethod
    def encode(
        agents_info_protobuf_object: Any, agents_info_object: "AgentsInfo"
    ) -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the agents_info_protobuf_object argument is matched with the instance of this class in the 'agents_info_object' argument.

        :param agents_info_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param agents_info_object: an instance of this class to be encoded in the protocol buffer object.
        :return: None
        """
        agents_info_protobuf_object.agents_info = DictProtobufStructSerializer.encode(
            agents_info_object.body
        )

    @classmethod
    def decode(cls, agents_info_protobuf_object: Any) -> "AgentsInfo":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class is created that matches the protocol buffer object in the 'agents_info_protobuf_object' argument.

        :param agents_info_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'agents_info_protobuf_object' argument.
        """
        body = DictProtobufStructSerializer.decode(
            agents_info_protobuf_object.agents_info
        )
        return cls(body)

    def __eq__(self, other: Any) -> bool:
        """Compare with another object."""
        if not isinstance(other, AgentsInfo):
            return False  # pragma: nocover
        return self.body == other.body


class OefErrorOperation(Enum):
    """This class represents an instance of OefErrorOperation."""

    REGISTER_SERVICE = 0
    UNREGISTER_SERVICE = 1
    SEARCH_SERVICES = 2
    SEND_MESSAGE = 3

    OTHER = 10000

    def __str__(self) -> str:
        """Get string representation."""
        return str(self.value)

    @staticmethod
    def encode(
        oef_error_operation_protobuf_object: Any,
        oef_error_operation_object: "OefErrorOperation",
    ) -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the oef_error_operation_protobuf_object argument is matched with the instance of this class in the 'oef_error_operation_object'
        argument.

        :param oef_error_operation_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param oef_error_operation_object: an instance of this class to be encoded in the protocol buffer object.
        :return: None
        """
        oef_error_operation_protobuf_object.oef_error = oef_error_operation_object.value

    @classmethod
    def decode(cls, oef_error_operation_protobuf_object: Any) -> "OefErrorOperation":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class is created that matches the protocol buffer object in the 'oef_error_operation_protobuf_object' argument.

        :param oef_error_operation_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'oef_error_operation_protobuf_object' argument.
        """
        enum_value_from_pb2 = oef_error_operation_protobuf_object.oef_error
        return OefErrorOperation(enum_value_from_pb2)


Query = BaseQuery
