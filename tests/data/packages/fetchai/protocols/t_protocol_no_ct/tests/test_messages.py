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

"""Test messages module for t_protocol_no_ct protocol."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,redefined-builtin
from typing import List

from aea.test_tools.test_protocol import BaseProtocolMessagesTestCase

from tests.data.packages.fetchai.protocols.t_protocol_no_ct.message import (
    TProtocolNoCtMessage,
)


class TestMessageTProtocolNoCt(BaseProtocolMessagesTestCase):
    """Test for the 't_protocol_no_ct' protocol message."""

    __test__ = True
    MESSAGE_CLASS = TProtocolNoCtMessage

    def build_messages(self) -> List[TProtocolNoCtMessage]:
        """Build the messages to be used for testing."""
        return [
            TProtocolNoCtMessage(
                performative=TProtocolNoCtMessage.Performative.PERFORMATIVE_PT,
                content_bytes=b"some_bytes",
                content_int=12,
                content_float=1.4,
                content_bool=True,
                content_str="some str",
            ),
            TProtocolNoCtMessage(
                performative=TProtocolNoCtMessage.Performative.PERFORMATIVE_PCT,
                content_set_bytes=FrozenSet[bytes](),
                content_set_int=FrozenSet[int](),
                content_set_float=FrozenSet[float](),
                content_set_bool=FrozenSet[bool](),
                content_set_str=FrozenSet[str](),
                content_list_bytes=Tuple[bytes, ...](),
                content_list_int=Tuple[int, ...](),
                content_list_float=Tuple[float, ...](),
                content_list_bool=Tuple[bool, ...](),
                content_list_str=Tuple[str, ...](),
            ),
            TProtocolNoCtMessage(
                performative=TProtocolNoCtMessage.Performative.PERFORMATIVE_PMT,
                content_dict_int_bytes={12: b"some_bytes"},
                content_dict_int_int={12: 12},
                content_dict_int_float={12: 1.4},
                content_dict_int_bool={12: True},
                content_dict_int_str={12: "some str"},
                content_dict_bool_bytes={True: b"some_bytes"},
                content_dict_bool_int={True: 12},
                content_dict_bool_float={True: 1.4},
                content_dict_bool_bool={True: True},
                content_dict_bool_str={True: "some str"},
                content_dict_str_bytes={"some str": b"some_bytes"},
                content_dict_str_int={"some str": 12},
                content_dict_str_float={"some str": 1.4},
                content_dict_str_bool={"some str": True},
                content_dict_str_str={"some str": "some str"},
            ),
            TProtocolNoCtMessage(
                performative=TProtocolNoCtMessage.Performative.PERFORMATIVE_MT,
                content_union_1=Union[
                    bytes,
                    int,
                    float,
                    bool,
                    str,
                    FrozenSet[int],
                    Tuple[bool, ...],
                    Dict[str, int],
                ](),
                content_union_2=Union[
                    FrozenSet[bytes],
                    FrozenSet[int],
                    FrozenSet[str],
                    Tuple[float, ...],
                    Tuple[bool, ...],
                    Tuple[bytes, ...],
                    Dict[str, int],
                    Dict[int, float],
                    Dict[bool, bytes],
                ](),
            ),
            TProtocolNoCtMessage(
                performative=TProtocolNoCtMessage.Performative.PERFORMATIVE_O,
                content_o_bool=[True],
                content_o_set_int=[FrozenSet[int]()],
                content_o_list_bytes=[Tuple[bytes, ...]()],
                content_o_dict_str_int=[{"some str": 12}],
            ),
            TProtocolNoCtMessage(
                performative=TProtocolNoCtMessage.Performative.PERFORMATIVE_EMPTY_CONTENTS,
            ),
        ]

    def build_inconsistent(self) -> List[TProtocolNoCtMessage]:
        """Build inconsistent messages to be used for testing."""
        return [
            TProtocolNoCtMessage(
                performative=TProtocolNoCtMessage.Performative.PERFORMATIVE_PT,
                # skip content: content_bytes
                content_int=12,
                content_float=1.4,
                content_bool=True,
                content_str="some str",
            ),
            TProtocolNoCtMessage(
                performative=TProtocolNoCtMessage.Performative.PERFORMATIVE_PCT,
                # skip content: content_set_bytes
                content_set_int=FrozenSet[int](),
                content_set_float=FrozenSet[float](),
                content_set_bool=FrozenSet[bool](),
                content_set_str=FrozenSet[str](),
                content_list_bytes=Tuple[bytes, ...](),
                content_list_int=Tuple[int, ...](),
                content_list_float=Tuple[float, ...](),
                content_list_bool=Tuple[bool, ...](),
                content_list_str=Tuple[str, ...](),
            ),
            TProtocolNoCtMessage(
                performative=TProtocolNoCtMessage.Performative.PERFORMATIVE_PMT,
                # skip content: content_dict_int_bytes
                content_dict_int_int={12: 12},
                content_dict_int_float={12: 1.4},
                content_dict_int_bool={12: True},
                content_dict_int_str={12: "some str"},
                content_dict_bool_bytes={True: b"some_bytes"},
                content_dict_bool_int={True: 12},
                content_dict_bool_float={True: 1.4},
                content_dict_bool_bool={True: True},
                content_dict_bool_str={True: "some str"},
                content_dict_str_bytes={"some str": b"some_bytes"},
                content_dict_str_int={"some str": 12},
                content_dict_str_float={"some str": 1.4},
                content_dict_str_bool={"some str": True},
                content_dict_str_str={"some str": "some str"},
            ),
            TProtocolNoCtMessage(
                performative=TProtocolNoCtMessage.Performative.PERFORMATIVE_MT,
                # skip content: content_union_1
                content_union_2=Union[
                    FrozenSet[bytes],
                    FrozenSet[int],
                    FrozenSet[str],
                    Tuple[float, ...],
                    Tuple[bool, ...],
                    Tuple[bytes, ...],
                    Dict[str, int],
                    Dict[int, float],
                    Dict[bool, bytes],
                ](),
            ),
            TProtocolNoCtMessage(
                performative=TProtocolNoCtMessage.Performative.PERFORMATIVE_O,
                # skip content: content_o_bool
                content_o_set_int=[FrozenSet[int]()],
                content_o_list_bytes=[Tuple[bytes, ...]()],
                content_o_dict_str_int=[{"some str": 12}],
            ),
        ]
