# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2019 Fetch.AI Limited
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
"""This module contains the tests for the helpers/serializers module."""
from google.protobuf.struct_pb2 import Struct

from aea.helpers.serializers import DictProtobufStructSerializer


def test_encode_decode_i():
    """Test encode decode logic."""
    case = {
        "key1": True,
        "key2": 0.12,
        "key3": 100,
        "key4": "some string",
        "key5": b"some bytes string",
        "key6": Struct(),
        "_need_patch": {},
    }
    encoded = DictProtobufStructSerializer.encode(case)
    case.pop("_need_patch")
    assert isinstance(encoded, bytes)
    decoded = DictProtobufStructSerializer.decode(encoded)
    assert case == decoded


def test_encode_decode_ii():
    """Test encode decode logic."""
    case = {
        "key1": True,
        "key2": 0.12,
        "key3": 100,
        "key4": "some string",
        "key5": b"some bytes string",
        "key6": {"key1": True, "key2": 0.12},
    }
    encoded = DictProtobufStructSerializer.encode(case)
    assert isinstance(encoded, bytes)
    decoded = DictProtobufStructSerializer.decode(encoded)
    assert case == decoded
