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

import pickle  # nosec
from typing import Any


class AnyObject:
    """This class represents an instance of AnyObject."""

    __slots__ = ("any",)

    def __init__(self, _any: Any):
        """Initialise an instance of AnyObject."""
        self.any = _any

    @staticmethod
    def encode(any_object_protobuf_object: Any, any_object_object: "AnyObject") -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the any_object_protobuf_object argument is matched with the instance of this class in the 'any_object_object' argument.

        :param any_object_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param any_object_object: an instance of this class to be encoded in the protocol buffer object.
        :return: None
        """
        any_object_protobuf_object.any = pickle.dumps(any_object_object)  # nosec

    @classmethod
    def decode(cls, any_object_protobuf_object: Any) -> "AnyObject":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class is created that matches the protocol buffer object in the 'any_object_protobuf_object' argument.

        :param any_object_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'any_object_protobuf_object' argument.
        """
        return pickle.loads(any_object_protobuf_object.any)  # nosec

    def __eq__(self, other: Any) -> bool:
        """Check equality."""
        return self.any == other.any
