# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 fetchai
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

"""Test messages module for t_protocol protocol."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,redefined-builtin
from typing import List

import pytest

from aea.test_tools.test_protocol import BaseProtocolMessagesTestCase

from tests.data.packages.fetchai.protocols.t_protocol.custom_types import DataModel
from tests.data.packages.fetchai.protocols.t_protocol.message import TProtocolMessage


data_model = DataModel(
    int_field=12,
    bool_field=True,
    bytes_field=b"",
    dict_field={},
    float_field=1.0,
    set_field=set(),
    str_field="str",
    list_field=["str"],
)


class TestMessageTProtocol(BaseProtocolMessagesTestCase):
    """Test for the 't_protocol' protocol message."""

    MESSAGE_CLASS = TProtocolMessage

    def test_messages_ok(self) -> None:
        """Run messages are ok for encode and decode."""
        raise pytest.skip("https://github.com/valory-xyz/open-aea/issues/565")

    def build_messages(self) -> List[TProtocolMessage]:  # type: ignore[override]
        """Build the messages to be used for testing."""
        return [
            TProtocolMessage(
                performative=TProtocolMessage.Performative.PERFORMATIVE_CT,
                content_ct=data_model,
            ),
            TProtocolMessage(
                performative=TProtocolMessage.Performative.PERFORMATIVE_PT,
                content_bytes=b"some_bytes",
                content_int=12,
                content_float=1.0,
                content_bool=True,
                content_str="some str",
            ),
            TProtocolMessage(
                performative=TProtocolMessage.Performative.PERFORMATIVE_PCT,
                content_set_bytes=frozenset([b"some_bytes"]),
                content_set_int=frozenset([12]),
                content_set_float=frozenset([1.0]),
                content_set_bool=frozenset([True]),
                content_set_str=frozenset(["some str"]),
                content_list_bytes=(b"some_bytes",),
                content_list_int=(12,),
                content_list_float=(1.0,),
                content_list_bool=(True,),
                content_list_str=("some str",),
            ),
            TProtocolMessage(
                performative=TProtocolMessage.Performative.PERFORMATIVE_PMT,
                content_dict_int_bytes={12: b"some_bytes"},
                content_dict_int_int={12: 12},
                content_dict_int_float={12: 1.0},
                content_dict_int_bool={12: True},
                content_dict_int_str={12: "some str"},
                content_dict_bool_bytes={True: b"some_bytes"},
                content_dict_bool_int={True: 12},
                content_dict_bool_float={True: 1.0},
                content_dict_bool_bool={True: True},
                content_dict_bool_str={True: "some str"},
                content_dict_str_bytes={"some str": b"some_bytes"},
                content_dict_str_int={"some str": 12},
                content_dict_str_float={"some str": 1.0},
                content_dict_str_bool={"some str": True},
                content_dict_str_str={"some str": "some str"},
            ),
            TProtocolMessage(
                performative=TProtocolMessage.Performative.PERFORMATIVE_MT,
                content_union_1=12,
                content_union_2=frozenset([b"some_bytes"]),
            ),
            TProtocolMessage(
                performative=TProtocolMessage.Performative.PERFORMATIVE_O,
                content_o_ct=data_model,
                content_o_bool=True,
                content_o_set_int=frozenset([12]),
                content_o_list_bytes=(b"some_bytes",),
                content_o_dict_str_int={"some str": 12},
            ),
            TProtocolMessage(
                performative=TProtocolMessage.Performative.PERFORMATIVE_EMPTY_CONTENTS,
            ),
        ]

    def build_inconsistent(self) -> List[TProtocolMessage]:  # type: ignore[override]
        """Build inconsistent messages to be used for testing."""
        return [
            TProtocolMessage(
                performative=TProtocolMessage.Performative.PERFORMATIVE_CT,
                # skip content: content_ct
            ),
            TProtocolMessage(
                performative=TProtocolMessage.Performative.PERFORMATIVE_PT,
                # skip content: content_bytes
                content_int=12,
                content_float=1.0,
                content_bool=True,
                content_str="some str",
            ),
            TProtocolMessage(
                performative=TProtocolMessage.Performative.PERFORMATIVE_PCT,
                # skip content: content_set_bytes
                content_set_int=frozenset([12]),
                content_set_float=frozenset([1.0]),
                content_set_bool=frozenset([True]),
                content_set_str=frozenset(["some str"]),
                content_list_bytes=(b"some_bytes",),
                content_list_int=(12,),
                content_list_float=(1.0,),
                content_list_bool=(True,),
                content_list_str=("some str",),
            ),
            TProtocolMessage(
                performative=TProtocolMessage.Performative.PERFORMATIVE_PMT,
                # skip content: content_dict_int_bytes
                content_dict_int_int={12: 12},
                content_dict_int_float={12: 1.0},
                content_dict_int_bool={12: True},
                content_dict_int_str={12: "some str"},
                content_dict_bool_bytes={True: b"some_bytes"},
                content_dict_bool_int={True: 12},
                content_dict_bool_float={True: 1.0},
                content_dict_bool_bool={True: True},
                content_dict_bool_str={True: "some str"},
                content_dict_str_bytes={"some str": b"some_bytes"},
                content_dict_str_int={"some str": 12},
                content_dict_str_float={"some str": 1.0},
                content_dict_str_bool={"some str": True},
                content_dict_str_str={"some str": "some str"},
            ),
            TProtocolMessage(
                performative=TProtocolMessage.Performative.PERFORMATIVE_MT,
                content_union_2=frozenset([b"some_bytes"]),
            ),
            TProtocolMessage(
                performative=TProtocolMessage.Performative.PERFORMATIVE_O,
                # skip content: content_o_ct
                content_o_bool="str",
                content_o_set_int=frozenset([12]),
                content_o_list_bytes=(b"some_bytes",),
                content_o_dict_str_int={"some str": 12},
            ),
        ]
