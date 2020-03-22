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
from typing import Dict


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
    """This class defines the error codes."""

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

    @property
    @staticmethod
    def to_msg(error_code: int) -> str:
        """Get the error code."""
        return CODE_TO_MSG[error_code]

    @classmethod
    def encode(cls, performative, error_code_from_message: "ErrorCode"):
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


class ErrorInfo(dict):
    """This class represents an instance of ErrorInfo."""

    def __init__(self, *args, **kwargs):
        """Initialise an instance of ErrorInfo."""
        self.update(*args, **kwargs)

    def __setitem__(self, key, value):
        """Set item."""
        assert type(key) == str and type(value) == str
        dict.__setitem__(self, key, value)

    def update(self, *args, **kwargs):
        for key, value in dict(*args, **kwargs).items():
            assert type(key) == str and type(value) == str
            self[key] = value

    @classmethod
    def encode(cls, performative, error_info_from_message: "ErrorInfo"):
        """
        Encode an instance of this class into the protocol buffer object.

        The content in the 'performative' argument must be matched with the message content in the 'error_info_from_message' argument.

        :param performative: the performative protocol buffer object containing a content whose type is this class.
        :param error_info_from_message: the message content to be encoded in the protocol buffer object.
        :return: the 'performative' protocol buffer object encoded with the message content in the 'error_info_from_message' argument.
        """
        raise NotImplementedError

    @classmethod
    def decode(cls, error_info_from_pb2) -> "ErrorInfo":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class must be created that matches the content in the 'error_info_from_pb2' argument.

        :param error_info_from_pb2: the protocol buffer content object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'error_info_from_pb2' argument.
        """
        raise NotImplementedError
