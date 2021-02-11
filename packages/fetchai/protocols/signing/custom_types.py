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
from typing import Any

from aea.helpers.transaction.base import RawMessage as BaseRawMessage
from aea.helpers.transaction.base import RawTransaction as BaseRawTransaction
from aea.helpers.transaction.base import SignedMessage as BaseSignedMessage
from aea.helpers.transaction.base import SignedTransaction as BaseSignedTransaction
from aea.helpers.transaction.base import Terms as BaseTerms


class ErrorCode(Enum):
    """This class represents an instance of ErrorCode."""

    UNSUCCESSFUL_MESSAGE_SIGNING = 0
    UNSUCCESSFUL_TRANSACTION_SIGNING = 1

    @staticmethod
    def encode(error_code_protobuf_object: Any, error_code_object: "ErrorCode") -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the error_code_protobuf_object argument is matched with the instance of this class in the 'error_code_object' argument.

        :param error_code_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param error_code_object: an instance of this class to be encoded in the protocol buffer object.
        :return: None
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


RawMessage = BaseRawMessage
RawTransaction = BaseRawTransaction
SignedMessage = BaseSignedMessage
SignedTransaction = BaseSignedTransaction
Terms = BaseTerms
