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

"""This module contains Serializers that can be used for custom types."""

import copy
from typing import Any, Dict

from google.protobuf.struct_pb2 import Struct


class DictProtobufStructSerializer:
    """
    Serialize python dictionaries of type DictType = Dict[str, ValueType] recursively conserving their dynamic type, using google.protobuf.Struct

    ValueType = PrimitiveType | DictType | List[ValueType]]
    PrimitiveType = bool | int | float | str | bytes
    """

    NEED_PATCH = "_need_patch"

    @classmethod
    def encode(cls, dictionary: Dict[str, Any]) -> bytes:
        """Serialize compatible dictionary to bytes"""
        if not isinstance(dictionary, dict):
            raise TypeError(  # pragma: nocover
                "dictionary must be of dict type, got type {}".format(type(dictionary))
            )
        # TOFIX(LR) problematic as it'll copy every message
        patched_dict = copy.deepcopy(dictionary)
        cls._patch_dict(patched_dict)
        pstruct = Struct()
        pstruct.update(patched_dict)  # pylint: disable=no-member
        return pstruct.SerializeToString()

    @classmethod
    def decode(cls, buffer: bytes) -> Dict[str, Any]:
        """Deserialize a compatible dictionary"""
        pstruct = Struct()
        pstruct.ParseFromString(buffer)
        dictionary = dict(pstruct)
        cls._patch_dict_restore(dictionary)
        return dictionary

    @classmethod
    def _bytes_to_str(cls, value: bytes) -> str:
        return value.decode("utf-8")

    @classmethod
    def _str_to_bytes(cls, value: str) -> bytes:
        return value.encode("utf-8")

    @classmethod
    def _patch_dict(cls, dictionnary: Dict[str, Any]) -> None:
        need_patch: Dict[str, bool] = dict()
        for key, value in dictionnary.items():
            if isinstance(value, bytes):
                # convert bytes values to string, as protobuf.Struct does support byte fields
                dictionnary[key] = cls._bytes_to_str(value)
                if cls.NEED_PATCH in dictionnary:
                    dictionnary[cls.NEED_PATCH][key] = True
                else:
                    need_patch[key] = True
            elif isinstance(value, int) and not isinstance(value, bool):
                # protobuf Struct store int as float under numeric_value type
                if cls.NEED_PATCH in dictionnary:
                    dictionnary[cls.NEED_PATCH][key] = True
                else:
                    need_patch[key] = True
            elif isinstance(value, dict):
                cls._patch_dict(value)  # pylint: disable=protected-access
            elif (
                not isinstance(value, bool)
                and not isinstance(value, float)
                and not isinstance(value, str)
                and not isinstance(value, Struct)
            ):  # pragma: nocover
                raise NotImplementedError(
                    "DictProtobufStructSerializer doesn't support dict value type {}".format(
                        type(value)
                    )
                )
        if len(need_patch) > 0:
            dictionnary[cls.NEED_PATCH] = need_patch

    @classmethod
    def _patch_dict_restore(cls, dictionary: Dict[str, Any]) -> None:
        # protobuf Struct doesn't recursively convert Struct to dict
        need_patch = dictionary.get(cls.NEED_PATCH, {})
        if len(need_patch) > 0:
            dictionary[cls.NEED_PATCH] = dict(need_patch)

        for key, value in dictionary.items():
            if key == cls.NEED_PATCH:
                continue

            # protobuf struct doesn't recursively convert Struct to dict
            if isinstance(value, Struct):
                if value != Struct():
                    value = dict(value)
                dictionary[key] = value

            if isinstance(value, dict):
                cls._patch_dict_restore(value)
            elif isinstance(value, str) and dictionary.get(cls.NEED_PATCH, dict()).get(
                key, False
            ):
                dictionary[key] = cls._str_to_bytes(value)
            elif isinstance(value, float) and dictionary.get(
                cls.NEED_PATCH, dict()
            ).get(key, False):
                dictionary[key] = int(value)

        dictionary.pop(cls.NEED_PATCH, None)
