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
from typing import Any, Dict

from aea.helpers.transaction.base import RawMessage as BaseRawMessage
from aea.helpers.transaction.base import RawTransaction as BaseRawTransaction
from aea.helpers.transaction.base import State as BaseState

RawMessage = BaseRawMessage
RawTransaction = BaseRawTransaction
State = BaseState


class Kwargs:
    """This class represents an instance of Kwargs."""

    def __init__(
        self, body: Dict[str, Any],
    ):
        """Initialise an instance of RawTransaction."""
        self._body = body
        self._check_consistency()

    def _check_consistency(self) -> None:
        """Check consistency of the object."""
        assert self._body is not None, "body must not be None"
        assert isinstance(self._body, dict) and [
            isinstance(key, str) for key in self._body.keys()
        ]

    @property
    def body(self) -> Dict[str, Any]:
        """Get the body."""
        return self._body

    @staticmethod
    def encode(kwargs_protobuf_object, kwargs_object: "Kwargs") -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the kwargs_protobuf_object argument must be matched with the instance of this class in the 'kwargs_object' argument.

        :param kwargs_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param kwargs_object: an instance of this class to be encoded in the protocol buffer object.
        :return: None
        """
        kwargs_bytes = pickle.dumps(kwargs_object)  # nosec
        kwargs_protobuf_object.kwargs_bytes = kwargs_bytes

    @classmethod
    def decode(cls, kwargs_protobuf_object) -> "Kwargs":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class must be created that matches the protocol buffer object in the 'raw_transaction_protobuf_object' argument.

        :param raw_transaction_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'raw_transaction_protobuf_object' argument.
        """
        kwargs = pickle.loads(kwargs_protobuf_object.kwargs_bytes)  # nosec
        return kwargs

    def __eq__(self, other):
        return isinstance(other, Kwargs) and self.body == other.body

    def __str__(self):
        return "Kwargs: body={}".format(self.body)
