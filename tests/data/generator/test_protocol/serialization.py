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

"""Serialization module for test_protocol protocol."""

from typing import cast

from aea.protocols.base import Message
from aea.protocols.base import Serializer

from tests.data.generator.test_protocol import test_protocol_pb2
from tests.data.generator.test_protocol.custom_types import DataModel
from tests.data.generator.test_protocol.message import TestProtocolMessage


class TestProtocolSerializer(Serializer):
    """Serialization for the 'test_protocol' protocol."""

    def encode(self, msg: Message) -> bytes:
        """
        Encode a 'TestProtocol' message into bytes.

        :param msg: the message object.
        :return: the bytes.
        """
        msg = cast(TestProtocolMessage, msg)
        test_protocol_msg = test_protocol_pb2.TestProtocolMessage()
        test_protocol_msg.message_id = msg.message_id
        dialogue_reference = msg.dialogue_reference
        test_protocol_msg.dialogue_starter_reference = dialogue_reference[0]
        test_protocol_msg.dialogue_responder_reference = dialogue_reference[1]
        test_protocol_msg.target = msg.target

        performative_id = msg.performative
        if performative_id == TestProtocolMessage.Performative.PERFORMATIVE_CT:
            performative = test_protocol_pb2.TestProtocolMessage.Performative_Ct()  # type: ignore
            content_ct = msg.content_ct
            performative = DataModel.encode(performative, content_ct)
            test_protocol_msg.performative_ct.CopyFrom(performative)
        elif performative_id == TestProtocolMessage.Performative.PERFORMATIVE_PT:
            performative = test_protocol_pb2.TestProtocolMessage.Performative_Pt()  # type: ignore
            content_bytes = msg.content_bytes
            performative.content_bytes = content_bytes
            content_int = msg.content_int
            performative.content_int = content_int
            content_float = msg.content_float
            performative.content_float = content_float
            content_bool = msg.content_bool
            performative.content_bool = content_bool
            content_str = msg.content_str
            performative.content_str = content_str
            test_protocol_msg.performative_pt.CopyFrom(performative)
        elif performative_id == TestProtocolMessage.Performative.PERFORMATIVE_PCT:
            performative = test_protocol_pb2.TestProtocolMessage.Performative_Pct()  # type: ignore
            content_set_ct = msg.content_set_ct
            performative.content_set_ct.extend(content_set_ct)
            content_set_bytes = msg.content_set_bytes
            performative.content_set_bytes.extend(content_set_bytes)
            content_set_int = msg.content_set_int
            performative.content_set_int.extend(content_set_int)
            content_set_float = msg.content_set_float
            performative.content_set_float.extend(content_set_float)
            content_set_bool = msg.content_set_bool
            performative.content_set_bool.extend(content_set_bool)
            content_set_str = msg.content_set_str
            performative.content_set_str.extend(content_set_str)
            content_list_ct = msg.content_list_ct
            performative.content_list_ct.extend(content_list_ct)
            content_list_bytes = msg.content_list_bytes
            performative.content_list_bytes.extend(content_list_bytes)
            content_list_int = msg.content_list_int
            performative.content_list_int.extend(content_list_int)
            content_list_float = msg.content_list_float
            performative.content_list_float.extend(content_list_float)
            content_list_bool = msg.content_list_bool
            performative.content_list_bool.extend(content_list_bool)
            content_list_str = msg.content_list_str
            performative.content_list_str.extend(content_list_str)
            test_protocol_msg.performative_pct.CopyFrom(performative)
        elif performative_id == TestProtocolMessage.Performative.PERFORMATIVE_PMT:
            performative = test_protocol_pb2.TestProtocolMessage.Performative_Pmt()  # type: ignore
            content_dict_int_ct = msg.content_dict_int_ct
            performative.content_dict_int_ct.update(content_dict_int_ct)
            content_dict_bool_int = msg.content_dict_bool_int
            performative.content_dict_bool_int.update(content_dict_bool_int)
            content_dict_str_float = msg.content_dict_str_float
            performative.content_dict_str_float.update(content_dict_str_float)
            test_protocol_msg.performative_pmt.CopyFrom(performative)
        elif performative_id == TestProtocolMessage.Performative.PERFORMATIVE_MT:
            performative = test_protocol_pb2.TestProtocolMessage.Performative_Mt()  # type: ignore
            if msg.is_set("content_union_type_DataModel"):
                performative.content_union_type_DataModel_is_set = True
                content_union_type_DataModel = msg.content_union_type_DataModel
                performative = DataModel.encode(
                    performative, content_union_type_DataModel
                )
            if msg.is_set("content_union_type_bytes"):
                performative.content_union_type_bytes_is_set = True
                content_union_type_bytes = msg.content_union_type_bytes
                performative.content_union_type_bytes = content_union_type_bytes
            if msg.is_set("content_union_type_int"):
                performative.content_union_type_int_is_set = True
                content_union_type_int = msg.content_union_type_int
                performative.content_union_type_int = content_union_type_int
            if msg.is_set("content_union_type_float"):
                performative.content_union_type_float_is_set = True
                content_union_type_float = msg.content_union_type_float
                performative.content_union_type_float = content_union_type_float
            if msg.is_set("content_union_type_bool"):
                performative.content_union_type_bool_is_set = True
                content_union_type_bool = msg.content_union_type_bool
                performative.content_union_type_bool = content_union_type_bool
            if msg.is_set("content_union_type_str"):
                performative.content_union_type_str_is_set = True
                content_union_type_str = msg.content_union_type_str
                performative.content_union_type_str = content_union_type_str
            if msg.is_set("content_union_type_set_of_int"):
                performative.content_union_type_set_of_int_is_set = True
                content_union_type_set_of_int = msg.content_union_type_set_of_int
                performative.content_union_type_set_of_int.extend(
                    content_union_type_set_of_int
                )
            if msg.is_set("content_union_type_list_of_DataModel"):
                performative.content_union_type_list_of_DataModel_is_set = True
                content_union_type_list_of_DataModel = (
                    msg.content_union_type_list_of_DataModel
                )
                performative.content_union_type_list_of_DataModel.extend(
                    content_union_type_list_of_DataModel
                )
            if msg.is_set("content_union_type_dict_of_str_DataModel"):
                performative.content_union_type_dict_of_str_DataModel_is_set = True
                content_union_type_dict_of_str_DataModel = (
                    msg.content_union_type_dict_of_str_DataModel
                )
                performative.content_union_type_dict_of_str_DataModel.update(
                    content_union_type_dict_of_str_DataModel
                )
            test_protocol_msg.performative_mt.CopyFrom(performative)
        elif performative_id == TestProtocolMessage.Performative.PERFORMATIVE_O:
            performative = test_protocol_pb2.TestProtocolMessage.Performative_O()  # type: ignore
            if msg.is_set("content_o_ct"):
                performative.content_o_ct_is_set = True
                content_o_ct = msg.content_o_ct
                performative = DataModel.encode(performative, content_o_ct)
            if msg.is_set("content_o_bool"):
                performative.content_o_bool_is_set = True
                content_o_bool = msg.content_o_bool
                performative.content_o_bool = content_o_bool
            if msg.is_set("content_o_set_float"):
                performative.content_o_set_float_is_set = True
                content_o_set_float = msg.content_o_set_float
                performative.content_o_set_float.extend(content_o_set_float)
            if msg.is_set("content_o_list_bytes"):
                performative.content_o_list_bytes_is_set = True
                content_o_list_bytes = msg.content_o_list_bytes
                performative.content_o_list_bytes.extend(content_o_list_bytes)
            if msg.is_set("content_o_dict_str_int"):
                performative.content_o_dict_str_int_is_set = True
                content_o_dict_str_int = msg.content_o_dict_str_int
                performative.content_o_dict_str_int.update(content_o_dict_str_int)
            if msg.is_set("content_o_union_type_str"):
                performative.content_o_union_type_str_is_set = True
                content_o_union_type_str = msg.content_o_union_type_str
                performative.content_o_union_type_str = content_o_union_type_str
            if msg.is_set("content_o_union_type_dict_of_str_int"):
                performative.content_o_union_type_dict_of_str_int_is_set = True
                content_o_union_type_dict_of_str_int = (
                    msg.content_o_union_type_dict_of_str_int
                )
                performative.content_o_union_type_dict_of_str_int.update(
                    content_o_union_type_dict_of_str_int
                )
            if msg.is_set("content_o_union_type_set_of_DataModel"):
                performative.content_o_union_type_set_of_DataModel_is_set = True
                content_o_union_type_set_of_DataModel = (
                    msg.content_o_union_type_set_of_DataModel
                )
                performative.content_o_union_type_set_of_DataModel.extend(
                    content_o_union_type_set_of_DataModel
                )
            if msg.is_set("content_o_union_type_dict_of_str_float"):
                performative.content_o_union_type_dict_of_str_float_is_set = True
                content_o_union_type_dict_of_str_float = (
                    msg.content_o_union_type_dict_of_str_float
                )
                performative.content_o_union_type_dict_of_str_float.update(
                    content_o_union_type_dict_of_str_float
                )
            test_protocol_msg.performative_o.CopyFrom(performative)
        elif (
            performative_id
            == TestProtocolMessage.Performative.PERFORMATIVE_EMPTY_CONTENTS
        ):
            performative = test_protocol_pb2.TestProtocolMessage.Performative_Empty_Contents()  # type: ignore
            test_protocol_msg.performative_empty_contents.CopyFrom(performative)
        else:
            raise ValueError("Performative not valid: {}".format(performative_id))

        test_protocol_bytes = test_protocol_msg.SerializeToString()
        return test_protocol_bytes

    def decode(self, obj: bytes) -> Message:
        """
        Decode bytes into a 'TestProtocol' message.

        :param obj: the bytes object.
        :return: the 'TestProtocol' message.
        """
        test_protocol_pb = test_protocol_pb2.TestProtocolMessage()
        test_protocol_pb.ParseFromString(obj)
        message_id = test_protocol_pb.message_id
        dialogue_reference = (
            test_protocol_pb.dialogue_starter_reference,
            test_protocol_pb.dialogue_responder_reference,
        )
        target = test_protocol_pb.target

        performative = test_protocol_pb.WhichOneof("performative")
        performative_id = TestProtocolMessage.Performative(str(performative))
        performative_content = dict()
        if performative_id == TestProtocolMessage.Performative.PERFORMATIVE_CT:
            pb2_content_ct = test_protocol_pb.performative_ct.content_ct
            content_ct = DataModel.decode(pb2_content_ct)
            performative_content["content_ct"] = content_ct
        elif performative_id == TestProtocolMessage.Performative.PERFORMATIVE_PT:
            content_bytes = test_protocol_pb.performative_pt.content_bytes
            performative_content["content_bytes"] = content_bytes
            content_int = test_protocol_pb.performative_pt.content_int
            performative_content["content_int"] = content_int
            content_float = test_protocol_pb.performative_pt.content_float
            performative_content["content_float"] = content_float
            content_bool = test_protocol_pb.performative_pt.content_bool
            performative_content["content_bool"] = content_bool
            content_str = test_protocol_pb.performative_pt.content_str
            performative_content["content_str"] = content_str
        elif performative_id == TestProtocolMessage.Performative.PERFORMATIVE_PCT:
            content_set_ct = test_protocol_pb.performative_pct.content_set_ct
            content_set_ct_frozenset = frozenset(content_set_ct)
            performative_content["content_set_ct"] = content_set_ct_frozenset
            content_set_bytes = test_protocol_pb.performative_pct.content_set_bytes
            content_set_bytes_frozenset = frozenset(content_set_bytes)
            performative_content["content_set_bytes"] = content_set_bytes_frozenset
            content_set_int = test_protocol_pb.performative_pct.content_set_int
            content_set_int_frozenset = frozenset(content_set_int)
            performative_content["content_set_int"] = content_set_int_frozenset
            content_set_float = test_protocol_pb.performative_pct.content_set_float
            content_set_float_frozenset = frozenset(content_set_float)
            performative_content["content_set_float"] = content_set_float_frozenset
            content_set_bool = test_protocol_pb.performative_pct.content_set_bool
            content_set_bool_frozenset = frozenset(content_set_bool)
            performative_content["content_set_bool"] = content_set_bool_frozenset
            content_set_str = test_protocol_pb.performative_pct.content_set_str
            content_set_str_frozenset = frozenset(content_set_str)
            performative_content["content_set_str"] = content_set_str_frozenset
            content_list_ct = test_protocol_pb.performative_pct.content_list_ct
            content_list_ct_tuple = tuple(content_list_ct)
            performative_content["content_list_ct"] = content_list_ct_tuple
            content_list_bytes = test_protocol_pb.performative_pct.content_list_bytes
            content_list_bytes_tuple = tuple(content_list_bytes)
            performative_content["content_list_bytes"] = content_list_bytes_tuple
            content_list_int = test_protocol_pb.performative_pct.content_list_int
            content_list_int_tuple = tuple(content_list_int)
            performative_content["content_list_int"] = content_list_int_tuple
            content_list_float = test_protocol_pb.performative_pct.content_list_float
            content_list_float_tuple = tuple(content_list_float)
            performative_content["content_list_float"] = content_list_float_tuple
            content_list_bool = test_protocol_pb.performative_pct.content_list_bool
            content_list_bool_tuple = tuple(content_list_bool)
            performative_content["content_list_bool"] = content_list_bool_tuple
            content_list_str = test_protocol_pb.performative_pct.content_list_str
            content_list_str_tuple = tuple(content_list_str)
            performative_content["content_list_str"] = content_list_str_tuple
        elif performative_id == TestProtocolMessage.Performative.PERFORMATIVE_PMT:
            content_dict_int_ct = test_protocol_pb.performative_pmt.content_dict_int_ct
            content_dict_int_ct_dict = dict(content_dict_int_ct)
            performative_content["content_dict_int_ct"] = content_dict_int_ct_dict
            content_dict_bool_int = (
                test_protocol_pb.performative_pmt.content_dict_bool_int
            )
            content_dict_bool_int_dict = dict(content_dict_bool_int)
            performative_content["content_dict_bool_int"] = content_dict_bool_int_dict
            content_dict_str_float = (
                test_protocol_pb.performative_pmt.content_dict_str_float
            )
            content_dict_str_float_dict = dict(content_dict_str_float)
            performative_content["content_dict_str_float"] = content_dict_str_float_dict
        elif performative_id == TestProtocolMessage.Performative.PERFORMATIVE_MT:
            if test_protocol_pb.performative_mt.content_union_type_DataModel_is_set:
                pb2_content_union_type_DataModel = (
                    test_protocol_pb.performative_mt.content_union_type_DataModel
                )
                content_union = DataModel.decode(pb2_content_union_type_DataModel)
                performative_content["content_union"] = content_union
            if test_protocol_pb.performative_mt.content_union_type_bytes_is_set:
                content_union = (
                    test_protocol_pb.performative_mt.content_union_type_bytes
                )
                performative_content["content_union"] = content_union
            if test_protocol_pb.performative_mt.content_union_type_int_is_set:
                content_union = test_protocol_pb.performative_mt.content_union_type_int
                performative_content["content_union"] = content_union
            if test_protocol_pb.performative_mt.content_union_type_float_is_set:
                content_union = (
                    test_protocol_pb.performative_mt.content_union_type_float
                )
                performative_content["content_union"] = content_union
            if test_protocol_pb.performative_mt.content_union_type_bool_is_set:
                content_union = test_protocol_pb.performative_mt.content_union_type_bool
                performative_content["content_union"] = content_union
            if test_protocol_pb.performative_mt.content_union_type_str_is_set:
                content_union = test_protocol_pb.performative_mt.content_union_type_str
                performative_content["content_union"] = content_union
            if test_protocol_pb.performative_mt.content_union_type_set_of_int_is_set:
                content_union = test_protocol_pb.performative_mt.content_union
                content_union_frozenset = frozenset(content_union)
                performative_content["content_union"] = content_union_frozenset
            if (
                test_protocol_pb.performative_mt.content_union_type_list_of_DataModel_is_set
            ):
                content_union = test_protocol_pb.performative_mt.content_union
                content_union_tuple = tuple(content_union)
                performative_content["content_union"] = content_union_tuple
            if (
                test_protocol_pb.performative_mt.content_union_type_dict_of_str_DataModel_is_set
            ):
                content_union = test_protocol_pb.performative_mt.content_union
                content_union_dict = dict(content_union)
                performative_content["content_union"] = content_union_dict
        elif performative_id == TestProtocolMessage.Performative.PERFORMATIVE_O:
            if test_protocol_pb.performative_o.content_o_ct_is_set:
                pb2_content_o_ct = test_protocol_pb.performative_o.content_o_ct
                content_o_ct = DataModel.decode(pb2_content_o_ct)
                performative_content["content_o_ct"] = content_o_ct
            if test_protocol_pb.performative_o.content_o_bool_is_set:
                content_o_bool = test_protocol_pb.performative_o.content_o_bool
                performative_content["content_o_bool"] = content_o_bool
            if test_protocol_pb.performative_o.content_o_set_float_is_set:
                content_o_set_float = (
                    test_protocol_pb.performative_o.content_o_set_float
                )
                content_o_set_float_frozenset = frozenset(content_o_set_float)
                performative_content[
                    "content_o_set_float"
                ] = content_o_set_float_frozenset
            if test_protocol_pb.performative_o.content_o_list_bytes_is_set:
                content_o_list_bytes = (
                    test_protocol_pb.performative_o.content_o_list_bytes
                )
                content_o_list_bytes_tuple = tuple(content_o_list_bytes)
                performative_content[
                    "content_o_list_bytes"
                ] = content_o_list_bytes_tuple
            if test_protocol_pb.performative_o.content_o_dict_str_int_is_set:
                content_o_dict_str_int = (
                    test_protocol_pb.performative_o.content_o_dict_str_int
                )
                content_o_dict_str_int_dict = dict(content_o_dict_str_int)
                performative_content[
                    "content_o_dict_str_int"
                ] = content_o_dict_str_int_dict
            if test_protocol_pb.performative_o.content_o_union_type_str_is_set:
                content_o_union = (
                    test_protocol_pb.performative_o.content_o_union_type_str
                )
                performative_content["content_o_union"] = content_o_union
            if (
                test_protocol_pb.performative_o.content_o_union_type_dict_of_str_int_is_set
            ):
                content_o_union = test_protocol_pb.performative_o.content_o_union
                content_o_union_dict = dict(content_o_union)
                performative_content["content_o_union"] = content_o_union_dict
            if (
                test_protocol_pb.performative_o.content_o_union_type_set_of_DataModel_is_set
            ):
                content_o_union = test_protocol_pb.performative_o.content_o_union
                content_o_union_frozenset = frozenset(content_o_union)
                performative_content["content_o_union"] = content_o_union_frozenset
            if (
                test_protocol_pb.performative_o.content_o_union_type_dict_of_str_float_is_set
            ):
                content_o_union = test_protocol_pb.performative_o.content_o_union
                content_o_union_dict = dict(content_o_union)
                performative_content["content_o_union"] = content_o_union_dict
        elif (
            performative_id
            == TestProtocolMessage.Performative.PERFORMATIVE_EMPTY_CONTENTS
        ):
            pass
        else:
            raise ValueError("Performative not valid: {}.".format(performative_id))

        return TestProtocolMessage(
            message_id=message_id,
            dialogue_reference=dialogue_reference,
            target=target,
            performative=performative,
            **performative_content
        )
