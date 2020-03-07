# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2020 Fetch.AI Limited
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


class ErrorCode(Enum):
    """This class represents an instance of ErrorCode."""

    UNSUPPORTED_PROTOCOL = 0
    DECODING_ERROR = 1
    INVALID_MESSAGE = 2
    UNSUPPORTED_SKILL = 3
    INVALID_DIALOGUE = 4

    @classmethod
    def encode(
        cls, performative, error_code_from_message: "ErrorCode",
    ):
        """
        Encode an instance of this class into the protocol buffer object.

        The content in the 'performative' argument must be matched with the message content in the 'error_code_from_message' argument.

        :param performative: the performative protocol buffer object containing a content whose type is this class.
        :param error_code_from_message: the message content to be encoded in the protocol buffer object.
        :return: the 'performative' protocol buffer object encoded with the message content in the 'error_code_from_message' argument.
        """
        performative.error_code.error_code = error_code_from_message.value
        return performative

    @classmethod
    def decode(cls, error_code_from_pb2) -> "ErrorCode":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class must be created that matches the content in the 'error_code_from_pb2' argument.

        :param error_code_from_pb2: the protocol buffer content object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'error_code_from_pb2' argument.
        """
        enum_value_from_pb2 = error_code_from_pb2.error_code
        return ErrorCode(enum_value_from_pb2)
