# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 fetchai
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

from typing import Dict, List, Set


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

    @staticmethod
    def encode(data_model_protobuf_object, data_model_object: "DataModel") -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the data_model_protobuf_object argument is matched with the instance of this class in the 'data_model_object' argument.

        :param data_model_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param data_model_object: an instance of this class to be encoded in the protocol buffer object.
        :return: None
        """
        data_model_protobuf_object.bytes_field = data_model_object.bytes_field
        data_model_protobuf_object.int_field = data_model_object.int_field
        data_model_protobuf_object.float_field = data_model_object.float_field
        data_model_protobuf_object.bool_field = data_model_object.bool_field
        data_model_protobuf_object.str_field = data_model_object.str_field

        data_model_protobuf_object.set_field.extend(data_model_object.set_field)
        data_model_protobuf_object.list_field.extend(data_model_object.list_field)
        data_model_protobuf_object.dict_field.update(data_model_object.dict_field)

    @classmethod
    def decode(cls, data_model_protobuf_object) -> "DataModel":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class is created that matches the protocol buffer object in the 'data_model_protobuf_object' argument.

        :param data_model_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'data_model_protobuf_object' argument.
        """
        return DataModel(
            bytes_field=data_model_protobuf_object.bytes_field,
            int_field=data_model_protobuf_object.int_field,
            float_field=data_model_protobuf_object.float_field,
            bool_field=data_model_protobuf_object.bool_field,
            str_field=data_model_protobuf_object.str_field,
            set_field=set(data_model_protobuf_object.set_field),
            list_field=data_model_protobuf_object.list_field,
            dict_field=data_model_protobuf_object.dict_field,
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
