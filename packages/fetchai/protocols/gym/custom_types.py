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

    def __init__(self, _any: Any):
        """Initialise an instance of AnyObject."""
        self.any = _any

    @classmethod
    def encode(cls, performative_content, any_from_message: "Any"):
        """
        Encode an instance of this class into the protocol buffer object.

        The content in the 'performative_content' argument must be matched with the message content in the 'any_object_from_message' argument.

        :param performative: the performative protocol buffer object containing a content whose type is this class.
        :param any_object_from_message: the message content to be encoded in the protocol buffer object.
        :return: None
        """
        performative_content.any = pickle.dumps(any_from_message)  # nosec

    @classmethod
    def decode(cls, any_from_pb2) -> "Any":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class must be created that matches the content in the 'any_object_from_pb2' argument.

        :param any_object_from_pb2: the protocol buffer content object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'any_object_from_pb2' argument.
        """
        _any = pickle.loads(any_from_pb2.any)  # nosec
        return _any

    def __eq__(self, other):
        return self.any == other.any
