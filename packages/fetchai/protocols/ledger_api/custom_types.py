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
from typing import Any, Tuple

from aea.exceptions import enforce
from aea.helpers.transaction.base import RawTransaction as BaseRawTransaction
from aea.helpers.transaction.base import SignedTransaction as BaseSignedTransaction
from aea.helpers.transaction.base import State as BaseState
from aea.helpers.transaction.base import Terms as BaseTerms
from aea.helpers.transaction.base import TransactionDigest as BaseTransactionDigest
from aea.helpers.transaction.base import TransactionReceipt as BaseTransactionReceipt


RawTransaction = BaseRawTransaction
SignedTransaction = BaseSignedTransaction
Terms = BaseTerms
TransactionDigest = BaseTransactionDigest
TransactionReceipt = BaseTransactionReceipt
State = BaseState


class Args:
    """This class represents an instance of Args."""

    def __init__(
        self, body: Tuple[Any],
    ):
        """Initialise an instance of Args."""
        self._body = body
        self._check_consistency()

    def _check_consistency(self) -> None:
        """Check consistency of the object."""
        if self._body is None:
            raise ValueError("body must not be None")
        enforce(
            isinstance(self._body, tuple), "Body must be tupleZ.",
        )

    @property
    def body(self) -> Tuple[Any]:
        """Get the body."""
        return self._body

    @staticmethod
    def encode(args_protobuf_object, args_object: "Args") -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the args_protobuf_object argument is matched with the instance of this class in the 'args_object' argument.

        :param args_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param args_object: an instance of this class to be encoded in the protocol buffer object.
        :return: None
        """
        args_bytes = pickle.dumps(args_object)  # nosec
        args_protobuf_object.args = args_bytes

    @classmethod
    def decode(cls, args_protobuf_object) -> "Args":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class is created that matches the protocol buffer object in the 'args_protobuf_object' argument.

        :param args_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'args_protobuf_object' argument.
        """
        args = pickle.loads(args_protobuf_object.args)  # nosec
        return args

    def __eq__(self, other):
        """Check equality."""
        return isinstance(other, Args) and self.body == other.body

    def __str__(self):
        """Get string representation."""
        return "Args: body={}".format(self.body)
