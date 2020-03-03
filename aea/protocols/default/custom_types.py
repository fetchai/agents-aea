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

from aea.protocols.default.default_pb2 import DefaultMessage


class ErrorCode:
    """This class represents an instance of ErrorCode."""

    class Type(Enum):
        UNSUPPORTED_PROTOCOL = 0
        DECODING_ERROR = 1
        INVALID_MESSAGE = 2
        UNSUPPORTED_SKILL = 3
        INVALID_DIALOGUE = 4

    def __init__(self, error_code_enum: Type):
        """Initialise an instance of ErrorCode."""
        self.error_code_enum = error_code_enum

    @classmethod
    def encode(
        cls, performative, error_code_from_message: "ErrorCode",
    ):
        """Encode an instance of this class into its protobuf object."""
        performative.error_code.error_code = (
            error_code_from_message.error_code_enum.value
        )
        return performative

    @classmethod
    def decode(cls, error_code_from_pb2) -> "ErrorCode":
        """Decode an instance of this class that has been serialised."""
        enum_value_from_pb2 = error_code_from_pb2.error_code
        error_code_enum = ErrorCode.Type(enum_value_from_pb2)
        error_code = ErrorCode(error_code_enum)
        return error_code

    def __eq__(self, other):
        if isinstance(other, ErrorCode):
            return self.error_code_enum == other.error_code_enum
        return NotImplemented
