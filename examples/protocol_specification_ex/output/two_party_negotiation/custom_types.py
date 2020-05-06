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


class Description:
    """This class represents an instance of Description."""

    def __init__(self):
        """Initialise an instance of Description."""
        raise NotImplementedError

    @staticmethod
    def encode(description_protobuf_object, description_object: "Description") -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the description_protobuf_object argument must be matched with the instance of this class in the 'description_object' argument.

        :param description_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param description_object: an instance of this class to be encoded in the protocol buffer object.
        :return: None
        """
        raise NotImplementedError

    @classmethod
    def decode(cls, description_protobuf_object) -> "Description":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class must be created that matches the protocol buffer object in the 'description_protobuf_object' argument.

        :param description_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'description_protobuf_object' argument.
        """
        raise NotImplementedError

    def __eq__(self, other):
        raise NotImplementedError


class Query:
    """This class represents an instance of Query."""

    def __init__(self):
        """Initialise an instance of Query."""
        raise NotImplementedError

    @staticmethod
    def encode(query_protobuf_object, query_object: "Query") -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the query_protobuf_object argument must be matched with the instance of this class in the 'query_object' argument.

        :param query_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param query_object: an instance of this class to be encoded in the protocol buffer object.
        :return: None
        """
        raise NotImplementedError

    @classmethod
    def decode(cls, query_protobuf_object) -> "Query":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class must be created that matches the protocol buffer object in the 'query_protobuf_object' argument.

        :param query_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'query_protobuf_object' argument.
        """
        raise NotImplementedError

    def __eq__(self, other):
        raise NotImplementedError
