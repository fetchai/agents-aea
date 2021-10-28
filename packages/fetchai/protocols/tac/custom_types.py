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


CODE_TO_MSG = {
    0: "Unexpected error.",
    1: "Request not recognized",
    2: "Agent addr already registered.",
    3: "Agent name already registered.",
    4: "Agent not registered.",
    5: "Error in checking transaction",
    6: "The transaction request does not match with a previous transaction request with the same id.",
    7: "Agent name not in whitelist.",
    8: "The competition is not running yet.",
    9: "The message is inconsistent with the dialogue.",
}  # type: Dict[int, str]


class ErrorCode(Enum):
    """This class represents an instance of ErrorCode."""

    GENERIC_ERROR = 0
    REQUEST_NOT_VALID = 1
    AGENT_ADDR_ALREADY_REGISTERED = 2
    AGENT_NAME_ALREADY_REGISTERED = 3
    AGENT_NOT_REGISTERED = 4
    TRANSACTION_NOT_VALID = 5
    TRANSACTION_NOT_MATCHING = 6
    AGENT_NAME_NOT_IN_WHITELIST = 7
    COMPETITION_NOT_RUNNING = 8
    DIALOGUE_INCONSISTENT = 9

    @staticmethod
    def to_msg(error_code: int) -> str:
        """Get the error code."""
        return CODE_TO_MSG[error_code]

    @staticmethod
    def encode(error_code_protobuf_object: Any, error_code_object: "ErrorCode") -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the error_code_protobuf_object argument is matched with the instance of this class in the 'error_code_object' argument.

        :param error_code_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param error_code_object: an instance of this class to be encoded in the protocol buffer object.
        """
        error_code_protobuf_object.error_code = error_code_object.value

    @classmethod
    def decode(cls, error_code_protobuf_object: Any) -> "ErrorCode":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class is created that matches the protocol buffer object in the 'error_code_protobuf_object' argument.

        :param error_code_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'error_code_protobuf_object' argument.
        """
        enum_value_from_pb2 = error_code_protobuf_object.error_code
        return ErrorCode(enum_value_from_pb2)
