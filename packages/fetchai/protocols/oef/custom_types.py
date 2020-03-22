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

import base64
import pickle  # nosec
from enum import Enum

from aea.helpers.search.models import Description as BaseDescription
from aea.helpers.search.models import Query as BaseQuery


class Description(BaseDescription):
    """This class represents an instance of Description."""

    @classmethod
    def encode(cls, performative, description_from_message: "Description"):
        """
        Encode an instance of this class into the protocol buffer object.

        The content in the 'performative' argument must be matched with the message content in the 'description_from_message' argument.

        :param performative: the performative protocol buffer object containing a content whose type is this class.
        :param description_from_message: the message content to be encoded in the protocol buffer object.
        :return: the 'performative' protocol buffer object encoded with the message content in the 'description_from_message' argument.
        """
        description_from_message_bytes = base64.b64encode(
            pickle.dumps(description_from_message)  # nosec
        ).decode("utf-8")
        performative.service_description.description = description_from_message_bytes
        return performative

    @classmethod
    def decode(cls, description_from_pb2) -> "Description":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class must be created that matches the content in the 'description_from_pb2' argument.

        :param description_from_pb2: the protocol buffer content object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'description_from_pb2' argument.
        """
        service_description_bytes = base64.b64decode(description_from_pb2)
        service_description = pickle.loads(service_description_bytes)  # nosec
        return service_description


class OEFErrorOperation(Enum):
    """This class represents an instance of OEFErrorOperation."""

    REGISTER_SERVICE = 0
    UNREGISTER_SERVICE = 1
    SEARCH_SERVICES = 2
    SEARCH_SERVICES_WIDE = 3
    SEND_MESSAGE = 4

    OTHER = 10000

    def __str__(self):
        """Get string representation."""
        return str(self.value)

    @classmethod
    def encode(
        cls, performative, o_e_f_error_operation_from_message: "OEFErrorOperation"
    ):
        """
        Encode an instance of this class into the protocol buffer object.

        The content in the 'performative' argument must be matched with the message content in the 'o_e_f_error_operation_from_message' argument.

        :param performative: the performative protocol buffer object containing a content whose type is this class.
        :param o_e_f_error_operation_from_message: the message content to be encoded in the protocol buffer object.
        :return: the 'performative' protocol buffer object encoded with the message content in the 'o_e_f_error_operation_from_message' argument.
        """
        performative.operation.oef_error = error_code_from_message.value
        return performative

    @classmethod
    def decode(cls, o_e_f_error_operation_from_pb2) -> "OEFErrorOperation":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class must be created that matches the content in the 'o_e_f_error_operation_from_pb2' argument.

        :param o_e_f_error_operation_from_pb2: the protocol buffer content object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'o_e_f_error_operation_from_pb2' argument.
        """
        enum_value_from_pb2 = oef_error_operation_from_pb2.oef_error
        return OEFErrorOperation(enum_value_from_pb2)


class Query(BaseQuery):
    """This class represents an instance of Query."""

    @classmethod
    def encode(cls, performative, query_from_message: "Query"):
        """
        Encode an instance of this class into the protocol buffer object.

        The content in the 'performative' argument must be matched with the message content in the 'query_from_message' argument.

        :param performative: the performative protocol buffer object containing a content whose type is this class.
        :param query_from_message: the message content to be encoded in the protocol buffer object.
        :return: the 'performative' protocol buffer object encoded with the message content in the 'query_from_message' argument.
        """
        query_bytes = base64.b64encode(pickle.dumps(query_from_message)).decode(
            "utf-8"
        )  # nosec
        performative.query.query_bytes = query_bytes
        return performative

    @classmethod
    def decode(cls, query_from_pb2) -> "Query":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class must be created that matches the content in the 'query_from_pb2' argument.

        :param query_from_pb2: the protocol buffer content object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'query_from_pb2' argument.
        """
        query_bytes = base64.b64decode(query_from_pb2)
        query = pickle.loads(query)  # nosec type: BaseQuery
        return query
