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
        """Encode an instance of this class into its protobuf object."""
        performative.error_code.error_code = error_code_from_message.value
        return performative

    @classmethod
    def decode(cls, error_code_from_pb2) -> "ErrorCode":
        """Decode an instance of this class that has been serialised."""
        enum_value_from_pb2 = error_code_from_pb2.error_code
        return ErrorCode(enum_value_from_pb2)
