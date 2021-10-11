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
from typing import Any, Dict, Tuple

from google.protobuf.struct_pb2 import ListValue, Struct


class DictProtobufStructSerializer:
    """
    Serialize python dictionaries of type DictType = Dict[str, ValueType] recursively conserving their dynamic type, using google.protobuf.Struct

    ValueType = PrimitiveType | DictType | List[ValueType]]
    PrimitiveType = bool | int | float | str | bytes
    """

    NEED_PATCH = "_need_patch"

    @classmethod
    def encode(cls, dictionary: Dict[str, Any]) -> bytes:
        """
        Serialize compatible dictionary to bytes.

        Copies entire dictionary in the process.

        :param dictionary: the dictionary to serialize
        :return: serialized bytes string
        """
        if not isinstance(dictionary, dict):
            raise TypeError(  # pragma: nocover
                "dictionary must be of dict type, got type {}".format(type(dictionary))
            )
        patched_dict = copy.deepcopy(dictionary)
        cls._patch_dict(patched_dict)
        pstruct = Struct()
        pstruct.update(patched_dict)  # pylint: disable=no-member
        return pstruct.SerializeToString(deterministic=True)

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
            new_value, patch_needed = cls._patch_value(value)
            if patch_needed:
                need_patch[key] = True
            dictionnary[key] = new_value

        if need_patch:
            dict_need_patch = dictionnary.get(cls.NEED_PATCH, {})
            dict_need_patch.update(need_patch)
            dictionnary[cls.NEED_PATCH] = dict_need_patch

    @classmethod
    def _patch_value(cls, value: Any) -> Tuple[Any, bool]:
        if isinstance(value, bytes):
            return cls._bytes_to_str(value), True
        if isinstance(value, int) and not isinstance(value, bool):
            return value, True
        if isinstance(value, list):
            result = []
            patched = False
            types = set()
            for v in value:
                types.add(type(v))
                v, need_patch = cls._patch_value(v)
                if need_patch or isinstance(v, dict):
                    patched = True
                result.append(v)
            if len(types) > 1:
                raise ValueError(f"Mixed data types in list are not allowed!: {value}")
            return result, patched
        if isinstance(value, dict):
            cls._patch_dict(value)
            return value, False
        if isinstance(value, tuple([bool, float, str, Struct])):
            # do nothing for supported types
            return value, False
        if value is None:
            return None, False

        raise NotImplementedError(
            "DictProtobufStructSerializer doesn't support dict value type {}".format(
                type(value)
            )
        )

    @classmethod
    def _restore_value(cls, value: Any) -> Any:
        if isinstance(value, str):
            return cls._str_to_bytes(value)

        if isinstance(value, Struct):
            if value != Struct():
                new_dict = dict(value)
                cls._patch_dict_restore(new_dict)
                return new_dict
            return {}

        if isinstance(value, float):
            return int(value)

        if isinstance(value, (list, ListValue)):
            return [cls._restore_value(v) for v in value]  # type: ignore

        raise NotImplementedError(  # pragma: nocover
            "DictProtobufStructSerializer doesn't support dict value type {}".format(
                type(value)
            )
        )

    @classmethod
    def _patch_dict_restore(cls, dictionary: Dict[str, Any]) -> None:
        # protobuf Struct doesn't recursively convert Struct to dict
        need_patch = dictionary.pop(cls.NEED_PATCH, {})
        for key, value in dictionary.items():

            # protobuf struct doesn't recursively convert Struct to dict
            if isinstance(value, Struct):
                dictionary[key] = cls._restore_value(value)

            if key in need_patch:
                dictionary[key] = cls._restore_value(value)

            elif isinstance(value, (list, ListValue)):
                # fix list of elementes not needed to be restored
                dictionary[key] = list(value)  # type: ignore
