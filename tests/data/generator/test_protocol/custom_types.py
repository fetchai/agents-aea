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

from typing import Set, List, Dict


class DataModel:
    """This class represents an instance of DataModel."""

    def __init__(
        self,
        bytes_field: bytes,
        int_field: int,
        float_field: float,
        bool_field: bool,
        str_field: str,
        set_field: Set[int],
        list_field: List[str],
        dict_field: Dict[int, bool],
    ):
        """Initialise an instance of DataModel."""
        self.bytes_field = bytes_field
        self.int_field = int_field
        self.float_field = float_field
        self.bool_field = bool_field
        self.str_field = str_field
        self.set_field = set_field
        self.list_field = list_field
        self.dict_field = dict_field

    @classmethod
    def encode(cls, performative, data_model_from_message: "DataModel"):
        """
        Encode an instance of this class into the protocol buffer object.

        The content in the 'performative' argument is matched with the message content in the 'data_model_from_message' argument.

        :param performative: the performative protocol buffer object containing a content whose type is this class.
        :param data_model_from_message: the message content to be encoded in the protocol buffer object.
        :return: the 'performative' protocol buffer object encoded with the message content in the 'data_model_from_message' argument.
        """
        performative.content_ct.bytes_field = data_model_from_message.bytes_field
        performative.content_ct.int_field = data_model_from_message.int_field
        performative.content_ct.float_field = data_model_from_message.float_field
        performative.content_ct.bool_field = data_model_from_message.bool_field
        performative.content_ct.str_field = data_model_from_message.str_field

        performative.content_ct.set_field.extend(data_model_from_message.set_field)
        performative.content_ct.list_field.extend(data_model_from_message.list_field)
        performative.content_ct.dict_field.update(data_model_from_message.dict_field)
        return performative

    @classmethod
    def decode(cls, data_model_from_pb2) -> "DataModel":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class is created that matches the content in the 'data_model_from_pb2' argument.

        :param data_model_from_pb2: the protocol buffer content object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'data_model_from_pb2' argument.
        """
        set_field = set(data_model_from_pb2.set_field)

        return DataModel(
            bytes_field=data_model_from_pb2.bytes_field,
            int_field=data_model_from_pb2.int_field,
            float_field=data_model_from_pb2.float_field,
            bool_field=data_model_from_pb2.bool_field,
            str_field=data_model_from_pb2.str_field,
            set_field=set(data_model_from_pb2.set_field),
            list_field=data_model_from_pb2.list_field,
            dict_field=data_model_from_pb2.dict_field,
        )

    def __eq__(self, other):
        """Overrides the default implementation"""
        if not isinstance(other, DataModel):
            return False
        return (
            self.bytes_field == other.bytes_field
            and self.int_field == other.int_field
            # floats seem to lose some precision when serialised then deserialised using protobuf
            # and self.float_field == other.float_field
            and self.bool_field == other.bool_field
            and self.str_field == other.str_field
            and self.set_field == other.set_field
            and self.list_field == other.list_field
            and self.dict_field == other.dict_field
        )
