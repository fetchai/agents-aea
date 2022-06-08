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

from typing import Any

from aea.common import JSONLike
from aea.exceptions import enforce
from aea.helpers.serializers import DictProtobufStructSerializer
from aea.helpers.transaction.base import RawMessage as BaseRawMessage
from aea.helpers.transaction.base import RawTransaction as BaseRawTransaction
from aea.helpers.transaction.base import State as BaseState


RawMessage = BaseRawMessage
RawTransaction = BaseRawTransaction
State = BaseState


class Kwargs:
    """This class represents an instance of Kwargs."""

    __slots__ = ("_body",)

    def __init__(
        self,
        body: JSONLike,
    ):
        """Initialise an instance of RawTransaction."""
        self._body = body
        self._check_consistency()

    def _check_consistency(self) -> None:
        """Check consistency of the object."""
        enforce(
            isinstance(self._body, dict)
            and all([isinstance(key, str) for key in self._body.keys()]),
            "Body must be dict and keys must be str.",
        )

    @property
    def body(self) -> JSONLike:
        """Get the body."""
        return self._body

    @staticmethod
    def encode(kwargs_protobuf_object: Any, kwargs_object: "Kwargs") -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the kwargs_protobuf_object argument is matched with the instance of this class in the 'kwargs_object' argument.

        :param kwargs_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param kwargs_object: an instance of this class to be encoded in the protocol buffer object.
        """
        kwargs_protobuf_object.kwargs = DictProtobufStructSerializer.encode(
            kwargs_object.body
        )

    @classmethod
    def decode(cls, kwargs_protobuf_object: Any) -> "Kwargs":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class is created that matches the protocol buffer object in the 'kwargs_protobuf_object' argument.

        :param kwargs_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'kwargs_protobuf_object' argument.
        """
        kwargs = DictProtobufStructSerializer.decode(kwargs_protobuf_object.kwargs)
        return cls(kwargs)

    def __eq__(self, other: Any) -> bool:
        """Check equality."""
        return isinstance(other, Kwargs) and self.body == other.body

    def __str__(self) -> str:
        """Get string representation."""
        return "Kwargs: body={}".format(self.body)
