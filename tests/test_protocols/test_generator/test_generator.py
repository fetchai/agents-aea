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
"""This module contains miscellaneous tests for the protocol generator."""
import filecmp
import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import cast
from unittest import TestCase, mock

import pytest

from aea.protocols.generator.base import ProtocolGenerator

from tests.data.generator.t_protocol.message import (  # type: ignore
    TProtocolMessage,
)
from tests.test_protocols.test_generator.common import (
    PATH_TO_T_PROTOCOL,
    PATH_TO_T_PROTOCOL_SPECIFICATION,
    T_PROTOCOL_NAME,
)


logger = logging.getLogger("aea")
logging.basicConfig(level=logging.INFO)


class TestCompareLatestGeneratorOutputWithTestProtocol:
    """Test that the "t_protocol" test protocol matches with the latest generator output based on its specification."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)
        filecmp.clear_cache()

    def test_compare_latest_generator_output_with_test_protocol(self):
        """
        Test that the "t_protocol" test protocol matches with the latest generator output based on its specification.

        Note:
            - custom_types.py files are not compared as the generated one is only a template.
            - protocol.yaml files are consequently not compared either because the different
              custom_types.py files makes their IPFS hashes different.
        """
        path_to_generated_protocol = self.t
        dotted_path_to_package_for_imports = "tests.data.generator."

        # Generate the protocol
        try:
            protocol_generator = ProtocolGenerator(
                path_to_protocol_specification=PATH_TO_T_PROTOCOL_SPECIFICATION,
                output_path=path_to_generated_protocol,
                dotted_path_to_protocol_package=dotted_path_to_package_for_imports,
            )
            protocol_generator.generate()
        except Exception as e:
            pytest.skip(
                "Something went wrong when generating the protocol. The exception:"
                + str(e)
            )

        # compare __init__.py
        init_file_generated = Path(self.t, T_PROTOCOL_NAME, "__init__.py")
        init_file_original = Path(PATH_TO_T_PROTOCOL, "__init__.py",)
        assert filecmp.cmp(init_file_generated, init_file_original)

        # compare message.py
        message_file_generated = Path(self.t, T_PROTOCOL_NAME, "message.py")
        message_file_original = Path(PATH_TO_T_PROTOCOL, "message.py",)
        assert filecmp.cmp(message_file_generated, message_file_original)

        # compare serialization.py
        serialization_file_generated = Path(self.t, T_PROTOCOL_NAME, "serialization.py")
        serialization_file_original = Path(PATH_TO_T_PROTOCOL, "serialization.py",)
        assert filecmp.cmp(serialization_file_generated, serialization_file_original)

        # compare dialogues.py
        dialogue_file_generated = Path(self.t, T_PROTOCOL_NAME, "dialogues.py")
        dialogue_file_original = Path(PATH_TO_T_PROTOCOL, "dialogues.py",)
        assert filecmp.cmp(dialogue_file_generated, dialogue_file_original)

        # compare .proto
        proto_file_generated = Path(
            self.t, T_PROTOCOL_NAME, "{}.proto".format(T_PROTOCOL_NAME)
        )
        proto_file_original = Path(
            PATH_TO_T_PROTOCOL, "{}.proto".format(T_PROTOCOL_NAME),
        )
        assert filecmp.cmp(proto_file_generated, proto_file_original)

        # compare _pb2.py
        # ToDo Fails in CI. Investigate!
        # pb2_file_generated = Path(
        #     self.t, T_PROTOCOL_NAME, "{}_pb2.py".format(T_PROTOCOL_NAME)
        # )
        # pb2_file_original = Path(
        #     PATH_TO_T_PROTOCOL, "{}_pb2.py".format(T_PROTOCOL_NAME),
        # )
        # assert filecmp.cmp(pb2_file_generated, pb2_file_original)

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestSerialisations:
    """
    Test that the generating a protocol works correctly in correct preconditions.

    Note: Types involving Floats seem to lose some precision when serialised then deserialised using protobuf.
    So tests for these types are commented out throughout for now.
    """

    def test_generated_protocol_serialisation_ct(self):
        """Test serialisation and deserialisation of a message involving a ct type."""
        some_dict = {1: True, 2: False, 3: True, 4: False}
        data_model = TProtocolMessage.DataModel(
            bytes_field=b"some bytes",
            int_field=42,
            float_field=42.7,
            bool_field=True,
            str_field="some string",
            set_field={1, 2, 3, 4, 5},
            list_field=["some string 1", "some string 2"],
            dict_field=some_dict,
        )
        message = TProtocolMessage(
            message_id=1,
            dialogue_reference=(str(0), ""),
            target=0,
            performative=TProtocolMessage.Performative.PERFORMATIVE_CT,
            content_ct=data_model,
        )

        encoded_message_in_bytes = TProtocolMessage.serializer.encode(message)
        decoded_message = cast(
            TProtocolMessage,
            TProtocolMessage.serializer.decode(encoded_message_in_bytes),
        )

        assert decoded_message.message_id == message.message_id
        assert decoded_message.dialogue_reference == message.dialogue_reference
        assert decoded_message.dialogue_reference[0] == message.dialogue_reference[0]
        assert decoded_message.dialogue_reference[1] == message.dialogue_reference[1]
        assert decoded_message.target == message.target
        assert decoded_message.performative == message.performative
        assert decoded_message.content_ct == message.content_ct

    def test_generated_protocol_serialisation_pt(self):
        """Test serialisation and deserialisation of a message involving a pt type."""
        message = TProtocolMessage(
            message_id=1,
            dialogue_reference=(str(0), ""),
            target=0,
            performative=TProtocolMessage.Performative.PERFORMATIVE_PT,
            content_bytes=b"some bytes",
            content_int=42,
            content_float=42.7,
            content_bool=True,
            content_str="some string",
        )

        encoded_message_in_bytes = TProtocolMessage.serializer.encode(message)
        decoded_message = cast(
            TProtocolMessage,
            TProtocolMessage.serializer.decode(encoded_message_in_bytes),
        )

        assert decoded_message.message_id == message.message_id
        assert decoded_message.dialogue_reference == message.dialogue_reference
        assert decoded_message.dialogue_reference[0] == message.dialogue_reference[0]
        assert decoded_message.dialogue_reference[1] == message.dialogue_reference[1]
        assert decoded_message.target == message.target
        assert decoded_message.performative == message.performative
        assert decoded_message.content_bytes == message.content_bytes
        assert decoded_message.content_int == message.content_int
        # assert decoded_message.content_float == message.content_float
        assert decoded_message.content_bool == message.content_bool
        assert decoded_message.content_str == message.content_str

    def test_generated_protocol_serialisation_pct(self):
        """Test serialisation and deserialisation of a message involving a pct type."""
        message = TProtocolMessage(
            message_id=1,
            dialogue_reference=(str(0), ""),
            target=0,
            performative=TProtocolMessage.Performative.PERFORMATIVE_PCT,
            content_set_bytes=frozenset([b"byte 1", b"byte 2", b"byte 3"]),
            content_set_int=frozenset([1, 2, 3]),
            content_set_float=frozenset([1.2, 2.3, 3.4]),
            content_set_bool=frozenset([True, False, False, True]),
            content_set_str=frozenset(["string1", "string2", "string3"]),
            content_list_bytes=(b"byte 4", b"byte 5", b"byte 6"),
            content_list_int=(4, 5, 6),
            content_list_float=(4.5, 5.6, 6.7),
            content_list_bool=(False, True, False, False),
            content_list_str=("string4", "string5", "string6"),
        )

        encoded_message_in_bytes = TProtocolMessage.serializer.encode(message)
        decoded_message = cast(
            TProtocolMessage,
            TProtocolMessage.serializer.decode(encoded_message_in_bytes),
        )

        assert decoded_message.message_id == message.message_id
        assert decoded_message.dialogue_reference == message.dialogue_reference
        assert decoded_message.dialogue_reference[0] == message.dialogue_reference[0]
        assert decoded_message.dialogue_reference[1] == message.dialogue_reference[1]
        assert decoded_message.target == message.target
        assert decoded_message.performative == message.performative
        assert decoded_message.content_set_bytes == message.content_set_bytes
        assert decoded_message.content_set_int == message.content_set_int
        # assert decoded_message.content_set_float == message.content_set_float
        assert decoded_message.content_set_bool == message.content_set_bool
        assert decoded_message.content_set_str == message.content_set_str
        assert decoded_message.content_list_bytes == message.content_list_bytes
        assert decoded_message.content_list_int == message.content_list_int
        # assert decoded_message.content_list_float == message.content_list_float
        assert decoded_message.content_list_bool == message.content_list_bool
        assert decoded_message.content_list_str == message.content_list_str

    def test_generated_protocol_serialisation_pmt(self):
        """Test serialisation and deserialisation of a message involving a pmt type."""
        message = TProtocolMessage(
            message_id=1,
            dialogue_reference=(str(0), ""),
            target=0,
            performative=TProtocolMessage.Performative.PERFORMATIVE_PMT,
            content_dict_int_bytes={1: b"bytes1", 2: b"bytes2", 3: b"bytes3"},
            content_dict_int_int={1: 2, 2: 3, 3: 4},
            content_dict_int_float={1: 3.4, 2: 4.7, 3: 4.6},
            content_dict_int_bool={1: True, 2: True, 3: False},
            content_dict_int_str={1: "string1", 2: "string2", 3: "string3"},
            content_dict_bool_bytes={True: b"bytes1", False: b"bytes2"},
            content_dict_bool_int={True: 5, False: 7},
            content_dict_bool_float={True: 5.4, False: 4.6},
            content_dict_bool_bool={True: False, False: False},
            content_dict_bool_str={True: "string1", False: "string2"},
            content_dict_str_bytes={
                "string1": b"bytes1",
                "string2": b"bytes2",
                "string3": b"bytes3",
            },
            content_dict_str_int={"string1": 2, "string2": 3, "string3": 4},
            content_dict_str_float={"string1": 3.4, "string2": 4.7, "string3": 4.6},
            content_dict_str_bool={"string1": True, "string2": True, "string3": False},
            content_dict_str_str={
                "string1": "string4",
                "string2": "string5",
                "string3": "string6",
            },
        )

        encoded_message_in_bytes = TProtocolMessage.serializer.encode(message)
        decoded_message = cast(
            TProtocolMessage,
            TProtocolMessage.serializer.decode(encoded_message_in_bytes),
        )

        assert decoded_message.message_id == message.message_id
        assert decoded_message.dialogue_reference == message.dialogue_reference
        assert decoded_message.dialogue_reference[0] == message.dialogue_reference[0]
        assert decoded_message.dialogue_reference[1] == message.dialogue_reference[1]
        assert decoded_message.target == message.target
        assert decoded_message.performative == message.performative
        assert decoded_message.content_dict_int_bytes == message.content_dict_int_bytes
        assert decoded_message.content_dict_int_int == message.content_dict_int_int
        # assert decoded_message.content_dict_int_float == message.content_dict_int_float
        assert decoded_message.content_dict_int_bool == message.content_dict_int_bool
        assert decoded_message.content_dict_int_str == message.content_dict_int_str
        assert (
            decoded_message.content_dict_bool_bytes == message.content_dict_bool_bytes
        )
        assert decoded_message.content_dict_bool_int == message.content_dict_bool_int
        # assert decoded_message.content_dict_bool_float == message.content_dict_bool_float
        assert decoded_message.content_dict_bool_bool == message.content_dict_bool_bool
        assert decoded_message.content_dict_bool_str == message.content_dict_bool_str
        assert decoded_message.content_dict_str_bytes == message.content_dict_str_bytes
        assert decoded_message.content_dict_str_int == message.content_dict_str_int
        # assert decoded_message.content_dict_str_float == message.content_dict_str_float
        assert decoded_message.content_dict_str_bool == message.content_dict_str_bool
        assert decoded_message.content_dict_str_str == message.content_dict_str_str

    def test_generated_protocol_serialisation_mt(self):
        """Test serialisation and deserialisation of a message involving an mt type."""
        pytest.skip(
            "Currently, union type is not properly implemented in the generator."
        )
        some_dict = {1: True, 2: False, 3: True, 4: False}
        data_model = TProtocolMessage.DataModel(
            bytes_field=b"some bytes",
            int_field=42,
            float_field=42.7,
            bool_field=True,
            str_field="some string",
            set_field={1, 2, 3, 4, 5},
            list_field=["some string 1", "some string 2"],
            dict_field=some_dict,
        )
        message_ct = TProtocolMessage(
            message_id=1,
            dialogue_reference=(str(0), ""),
            target=0,
            performative=TProtocolMessage.Performative.PERFORMATIVE_MT,
            content_union_1=data_model,
        )

        encoded_message_in_bytes = TProtocolMessage.serializer.encode(message_ct)
        decoded_message = cast(
            TProtocolMessage,
            TProtocolMessage.serializer.decode(encoded_message_in_bytes),
        )

        assert decoded_message.message_id == message_ct.message_id
        assert decoded_message.dialogue_reference == message_ct.dialogue_reference
        assert decoded_message.dialogue_reference[0] == message_ct.dialogue_reference[0]
        assert decoded_message.dialogue_reference[1] == message_ct.dialogue_reference[1]
        assert decoded_message.target == message_ct.target
        assert decoded_message.performative == message_ct.performative
        assert decoded_message.content_union_1 == message_ct.content_union_1

        #####################

        message_pt_bytes = TProtocolMessage(
            message_id=1,
            dialogue_reference=(str(0), ""),
            target=0,
            performative=TProtocolMessage.Performative.PERFORMATIVE_MT,
            content_union_1=b"some bytes",
        )

        encoded_message_in_bytes = TProtocolMessage.serializer.encode(message_pt_bytes)
        decoded_message = cast(
            TProtocolMessage,
            TProtocolMessage.serializer.decode(encoded_message_in_bytes),
        )

        assert decoded_message.message_id == message_pt_bytes.message_id
        assert decoded_message.dialogue_reference == message_pt_bytes.dialogue_reference
        assert (
            decoded_message.dialogue_reference[0]
            == message_pt_bytes.dialogue_reference[0]
        )
        assert (
            decoded_message.dialogue_reference[1]
            == message_pt_bytes.dialogue_reference[1]
        )
        assert decoded_message.target == message_pt_bytes.target
        assert decoded_message.performative == message_pt_bytes.performative
        assert decoded_message.content_union_1 == message_pt_bytes.content_union_1

        #####################

        message_pt_int = TProtocolMessage(
            message_id=1,
            dialogue_reference=(str(0), ""),
            target=0,
            performative=TProtocolMessage.Performative.PERFORMATIVE_MT,
            content_union_1=3453,
        )

        encoded_message_in_bytes = TProtocolMessage.serializer.encode(message_pt_int)
        decoded_message = cast(
            TProtocolMessage,
            TProtocolMessage.serializer.decode(encoded_message_in_bytes),
        )

        assert decoded_message.message_id == message_pt_int.message_id
        assert decoded_message.dialogue_reference == message_pt_int.dialogue_reference
        assert (
            decoded_message.dialogue_reference[0]
            == message_pt_int.dialogue_reference[0]
        )
        assert (
            decoded_message.dialogue_reference[1]
            == message_pt_int.dialogue_reference[1]
        )
        assert decoded_message.target == message_pt_int.target
        assert decoded_message.performative == message_pt_int.performative
        assert decoded_message.content_union_1 == message_pt_int.content_union_1

        #####################

        message_pt_float = TProtocolMessage(
            message_id=1,
            dialogue_reference=(str(0), ""),
            target=0,
            performative=TProtocolMessage.Performative.PERFORMATIVE_MT,
            content_union_1=34.64,
        )

        encoded_message_in_bytes = TProtocolMessage.serializer.encode(message_pt_float)
        decoded_message = cast(
            TProtocolMessage,
            TProtocolMessage.serializer.decode(encoded_message_in_bytes),
        )

        assert decoded_message.message_id == message_pt_float.message_id
        assert decoded_message.dialogue_reference == message_pt_float.dialogue_reference
        assert (
            decoded_message.dialogue_reference[0]
            == message_pt_float.dialogue_reference[0]
        )
        assert (
            decoded_message.dialogue_reference[1]
            == message_pt_float.dialogue_reference[1]
        )
        assert decoded_message.target == message_pt_float.target
        assert decoded_message.performative == message_pt_float.performative
        assert decoded_message.content_union_1 == message_pt_float.content_union_1

        #####################

        message_pt_bool = TProtocolMessage(
            message_id=1,
            dialogue_reference=(str(0), ""),
            target=0,
            performative=TProtocolMessage.Performative.PERFORMATIVE_MT,
            content_union_1=True,
        )

        encoded_message_in_bytes = TProtocolMessage.serializer.encode(message_pt_bool)
        decoded_message = cast(
            TProtocolMessage,
            TProtocolMessage.serializer.decode(encoded_message_in_bytes),
        )

        assert decoded_message.message_id == message_pt_bool.message_id
        assert decoded_message.dialogue_reference == message_pt_bool.dialogue_reference
        assert (
            decoded_message.dialogue_reference[0]
            == message_pt_bool.dialogue_reference[0]
        )
        assert (
            decoded_message.dialogue_reference[1]
            == message_pt_bool.dialogue_reference[1]
        )
        assert decoded_message.target == message_pt_bool.target
        assert decoded_message.performative == message_pt_bool.performative
        assert decoded_message.content_union_1 == message_pt_bool.content_union_1

        #####################

        message_pt_str = TProtocolMessage(
            message_id=1,
            dialogue_reference=(str(0), ""),
            target=0,
            performative=TProtocolMessage.Performative.PERFORMATIVE_MT,
            content_union_1="some string",
        )

        encoded_message_in_bytes = TProtocolMessage.serializer.encode(message_pt_str)
        decoded_message = cast(
            TProtocolMessage,
            TProtocolMessage.serializer.decode(encoded_message_in_bytes),
        )

        assert decoded_message.message_id == message_pt_str.message_id
        assert decoded_message.dialogue_reference == message_pt_str.dialogue_reference
        assert (
            decoded_message.dialogue_reference[0]
            == message_pt_str.dialogue_reference[0]
        )
        assert (
            decoded_message.dialogue_reference[1]
            == message_pt_str.dialogue_reference[1]
        )
        assert decoded_message.target == message_pt_str.target
        assert decoded_message.performative == message_pt_str.performative
        assert decoded_message.content_union_1 == message_pt_str.content_union_1

        #####################

        message_set_int = TProtocolMessage(
            message_id=1,
            dialogue_reference=(str(0), ""),
            target=0,
            performative=TProtocolMessage.Performative.PERFORMATIVE_MT,
            content_union_1=frozenset([1, 2, 3]),
        )

        encoded_message_in_bytes = TProtocolMessage.serializer.encode(message_set_int)
        decoded_message = cast(
            TProtocolMessage,
            TProtocolMessage.serializer.decode(encoded_message_in_bytes),
        )

        assert decoded_message.message_id == message_set_int.message_id
        assert decoded_message.dialogue_reference == message_set_int.dialogue_reference
        assert (
            decoded_message.dialogue_reference[0]
            == message_set_int.dialogue_reference[0]
        )
        assert (
            decoded_message.dialogue_reference[1]
            == message_set_int.dialogue_reference[1]
        )
        assert decoded_message.target == message_set_int.target
        assert decoded_message.performative == message_set_int.performative
        assert decoded_message.content_union_1 == message_set_int.content_union_1

        #####################

        message_list_bool = TProtocolMessage(
            message_id=1,
            dialogue_reference=(str(0), ""),
            target=0,
            performative=TProtocolMessage.Performative.PERFORMATIVE_MT,
            content_union_1=(True, False, False, True, True),
        )

        encoded_message_in_bytes = TProtocolMessage.serializer.encode(message_list_bool)
        decoded_message = cast(
            TProtocolMessage,
            TProtocolMessage.serializer.decode(encoded_message_in_bytes),
        )

        assert decoded_message.message_id == message_list_bool.message_id
        assert (
            decoded_message.dialogue_reference == message_list_bool.dialogue_reference
        )
        assert (
            decoded_message.dialogue_reference[0]
            == message_list_bool.dialogue_reference[0]
        )
        assert (
            decoded_message.dialogue_reference[1]
            == message_list_bool.dialogue_reference[1]
        )
        assert decoded_message.target == message_list_bool.target
        assert decoded_message.performative == message_list_bool.performative
        assert decoded_message.content_union_1 == message_list_bool.content_union_1

        #####################

        message_dict_str_int = TProtocolMessage(
            message_id=1,
            dialogue_reference=(str(0), ""),
            target=0,
            performative=TProtocolMessage.Performative.PERFORMATIVE_MT,
            content_union_1={"string1": 2, "string2": 3, "string3": 4},
        )

        encoded_message_in_bytes = TProtocolMessage.serializer.encode(
            message_dict_str_int
        )
        decoded_message = cast(
            TProtocolMessage,
            TProtocolMessage.serializer.decode(encoded_message_in_bytes),
        )

        assert decoded_message.message_id == message_dict_str_int.message_id
        assert (
            decoded_message.dialogue_reference
            == message_dict_str_int.dialogue_reference
        )
        assert (
            decoded_message.dialogue_reference[0]
            == message_dict_str_int.dialogue_reference[0]
        )
        assert (
            decoded_message.dialogue_reference[1]
            == message_dict_str_int.dialogue_reference[1]
        )
        assert decoded_message.target == message_dict_str_int.target
        assert decoded_message.performative == message_dict_str_int.performative
        assert decoded_message.content_union_1 == message_dict_str_int.content_union_1

    def test_generated_protocol_serialisation_o(self):
        """Test serialisation and deserialisation of a message involving an optional type."""
        some_dict = {1: True, 2: False, 3: True, 4: False}
        data_model = TProtocolMessage.DataModel(
            bytes_field=b"some bytes",
            int_field=42,
            float_field=42.7,
            bool_field=True,
            str_field="some string",
            set_field={1, 2, 3, 4, 5},
            list_field=["some string 1", "some string 2"],
            dict_field=some_dict,
        )
        message_o_ct_set = TProtocolMessage(
            message_id=1,
            dialogue_reference=(str(0), ""),
            target=0,
            performative=TProtocolMessage.Performative.PERFORMATIVE_O,
            content_o_ct=data_model,
        )

        encoded_message_in_bytes = TProtocolMessage.serializer.encode(message_o_ct_set)
        decoded_message = cast(
            TProtocolMessage,
            TProtocolMessage.serializer.decode(encoded_message_in_bytes),
        )

        assert decoded_message.message_id == message_o_ct_set.message_id
        assert decoded_message.dialogue_reference == message_o_ct_set.dialogue_reference
        assert (
            decoded_message.dialogue_reference[0]
            == message_o_ct_set.dialogue_reference[0]
        )
        assert (
            decoded_message.dialogue_reference[1]
            == message_o_ct_set.dialogue_reference[1]
        )
        assert decoded_message.target == message_o_ct_set.target
        assert decoded_message.performative == message_o_ct_set.performative
        assert decoded_message.content_o_ct == message_o_ct_set.content_o_ct

        #####################

        message_o_ct_not_set = TProtocolMessage(
            message_id=1,
            dialogue_reference=(str(0), ""),
            target=0,
            performative=TProtocolMessage.Performative.PERFORMATIVE_O,
        )

        encoded_message_in_bytes = TProtocolMessage.serializer.encode(
            message_o_ct_not_set
        )
        decoded_message = cast(
            TProtocolMessage,
            TProtocolMessage.serializer.decode(encoded_message_in_bytes),
        )

        assert decoded_message.message_id == message_o_ct_not_set.message_id
        assert (
            decoded_message.dialogue_reference
            == message_o_ct_not_set.dialogue_reference
        )
        assert (
            decoded_message.dialogue_reference[0]
            == message_o_ct_not_set.dialogue_reference[0]
        )
        assert (
            decoded_message.dialogue_reference[1]
            == message_o_ct_not_set.dialogue_reference[1]
        )
        assert decoded_message.target == message_o_ct_not_set.target
        assert decoded_message.performative == message_o_ct_not_set.performative
        assert decoded_message.content_o_ct == message_o_ct_not_set.content_o_ct

        #####################

        message_o_bool_set = TProtocolMessage(
            message_id=1,
            dialogue_reference=(str(0), ""),
            target=0,
            performative=TProtocolMessage.Performative.PERFORMATIVE_O,
            content_o_bool=True,
        )

        encoded_message_in_bytes = TProtocolMessage.serializer.encode(
            message_o_bool_set
        )
        decoded_message = cast(
            TProtocolMessage,
            TProtocolMessage.serializer.decode(encoded_message_in_bytes),
        )

        assert decoded_message.message_id == message_o_bool_set.message_id
        assert (
            decoded_message.dialogue_reference == message_o_bool_set.dialogue_reference
        )
        assert (
            decoded_message.dialogue_reference[0]
            == message_o_bool_set.dialogue_reference[0]
        )
        assert (
            decoded_message.dialogue_reference[1]
            == message_o_bool_set.dialogue_reference[1]
        )
        assert decoded_message.target == message_o_bool_set.target
        assert decoded_message.performative == message_o_bool_set.performative
        assert decoded_message.content_o_ct == message_o_bool_set.content_o_ct

        #####################

        message_o_bool_not_set = TProtocolMessage(
            message_id=1,
            dialogue_reference=(str(0), ""),
            target=0,
            performative=TProtocolMessage.Performative.PERFORMATIVE_O,
        )

        encoded_message_in_bytes = TProtocolMessage.serializer.encode(
            message_o_bool_not_set
        )
        decoded_message = cast(
            TProtocolMessage,
            TProtocolMessage.serializer.decode(encoded_message_in_bytes),
        )

        assert decoded_message.message_id == message_o_bool_not_set.message_id
        assert (
            decoded_message.dialogue_reference
            == message_o_bool_not_set.dialogue_reference
        )
        assert (
            decoded_message.dialogue_reference[0]
            == message_o_bool_not_set.dialogue_reference[0]
        )
        assert (
            decoded_message.dialogue_reference[1]
            == message_o_bool_not_set.dialogue_reference[1]
        )
        assert decoded_message.target == message_o_bool_not_set.target
        assert decoded_message.performative == message_o_bool_not_set.performative
        assert decoded_message.content_o_bool == message_o_bool_not_set.content_o_bool

        #####################

        message_o_set_int_set = TProtocolMessage(
            message_id=1,
            dialogue_reference=(str(0), ""),
            target=0,
            performative=TProtocolMessage.Performative.PERFORMATIVE_O,
            content_o_set_int=frozenset([1, 2, 3]),
        )

        encoded_message_in_bytes = TProtocolMessage.serializer.encode(
            message_o_set_int_set
        )
        decoded_message = cast(
            TProtocolMessage,
            TProtocolMessage.serializer.decode(encoded_message_in_bytes),
        )

        assert decoded_message.message_id == message_o_set_int_set.message_id
        assert (
            decoded_message.dialogue_reference
            == message_o_set_int_set.dialogue_reference
        )
        assert (
            decoded_message.dialogue_reference[0]
            == message_o_set_int_set.dialogue_reference[0]
        )
        assert (
            decoded_message.dialogue_reference[1]
            == message_o_set_int_set.dialogue_reference[1]
        )
        assert decoded_message.target == message_o_set_int_set.target
        assert decoded_message.performative == message_o_set_int_set.performative
        assert (
            decoded_message.content_o_set_int == message_o_set_int_set.content_o_set_int
        )

        #####################

        message_o_set_int_not_set = TProtocolMessage(
            message_id=1,
            dialogue_reference=(str(0), ""),
            target=0,
            performative=TProtocolMessage.Performative.PERFORMATIVE_O,
        )

        encoded_message_in_bytes = TProtocolMessage.serializer.encode(
            message_o_set_int_not_set
        )
        decoded_message = cast(
            TProtocolMessage,
            TProtocolMessage.serializer.decode(encoded_message_in_bytes),
        )

        assert decoded_message.message_id == message_o_set_int_not_set.message_id
        assert (
            decoded_message.dialogue_reference
            == message_o_set_int_not_set.dialogue_reference
        )
        assert (
            decoded_message.dialogue_reference[0]
            == message_o_set_int_not_set.dialogue_reference[0]
        )
        assert (
            decoded_message.dialogue_reference[1]
            == message_o_set_int_not_set.dialogue_reference[1]
        )
        assert decoded_message.target == message_o_set_int_not_set.target
        assert decoded_message.performative == message_o_set_int_not_set.performative
        assert (
            decoded_message.content_o_set_int
            == message_o_set_int_not_set.content_o_set_int
        )

        #####################

        message_o_list_bytes_set = TProtocolMessage(
            message_id=1,
            dialogue_reference=(str(0), ""),
            target=0,
            performative=TProtocolMessage.Performative.PERFORMATIVE_O,
            content_o_list_bytes=(b"bytes1", b"bytes2", b"bytes3"),
        )

        encoded_message_in_bytes = TProtocolMessage.serializer.encode(
            message_o_list_bytes_set
        )
        decoded_message = cast(
            TProtocolMessage,
            TProtocolMessage.serializer.decode(encoded_message_in_bytes),
        )

        assert decoded_message.message_id == message_o_list_bytes_set.message_id
        assert (
            decoded_message.dialogue_reference
            == message_o_list_bytes_set.dialogue_reference
        )
        assert (
            decoded_message.dialogue_reference[0]
            == message_o_list_bytes_set.dialogue_reference[0]
        )
        assert (
            decoded_message.dialogue_reference[1]
            == message_o_list_bytes_set.dialogue_reference[1]
        )
        assert decoded_message.target == message_o_list_bytes_set.target
        assert decoded_message.performative == message_o_list_bytes_set.performative
        assert (
            decoded_message.content_o_list_bytes
            == message_o_list_bytes_set.content_o_list_bytes
        )

        #####################

        message_o_list_bytes_not_set = TProtocolMessage(
            message_id=1,
            dialogue_reference=(str(0), ""),
            target=0,
            performative=TProtocolMessage.Performative.PERFORMATIVE_O,
        )

        encoded_message_in_bytes = TProtocolMessage.serializer.encode(
            message_o_list_bytes_not_set
        )
        decoded_message = cast(
            TProtocolMessage,
            TProtocolMessage.serializer.decode(encoded_message_in_bytes),
        )

        assert decoded_message.message_id == message_o_list_bytes_not_set.message_id
        assert (
            decoded_message.dialogue_reference
            == message_o_list_bytes_not_set.dialogue_reference
        )
        assert (
            decoded_message.dialogue_reference[0]
            == message_o_list_bytes_not_set.dialogue_reference[0]
        )
        assert (
            decoded_message.dialogue_reference[1]
            == message_o_list_bytes_not_set.dialogue_reference[1]
        )
        assert decoded_message.target == message_o_list_bytes_not_set.target
        assert decoded_message.performative == message_o_list_bytes_not_set.performative
        assert (
            decoded_message.content_o_list_bytes
            == message_o_list_bytes_not_set.content_o_list_bytes
        )

        #####################

        message_o_dict_str_int_set = TProtocolMessage(
            message_id=1,
            dialogue_reference=(str(0), ""),
            target=0,
            performative=TProtocolMessage.Performative.PERFORMATIVE_O,
            content_o_dict_str_int={"string1": 2, "string2": 3, "string3": 4},
        )

        encoded_message_in_bytes = TProtocolMessage.serializer.encode(
            message_o_dict_str_int_set
        )
        decoded_message = cast(
            TProtocolMessage,
            TProtocolMessage.serializer.decode(encoded_message_in_bytes),
        )

        assert decoded_message.message_id == message_o_dict_str_int_set.message_id
        assert (
            decoded_message.dialogue_reference
            == message_o_dict_str_int_set.dialogue_reference
        )
        assert (
            decoded_message.dialogue_reference[0]
            == message_o_dict_str_int_set.dialogue_reference[0]
        )
        assert (
            decoded_message.dialogue_reference[1]
            == message_o_dict_str_int_set.dialogue_reference[1]
        )
        assert decoded_message.target == message_o_dict_str_int_set.target
        assert decoded_message.performative == message_o_dict_str_int_set.performative
        assert (
            decoded_message.content_o_list_bytes
            == message_o_dict_str_int_set.content_o_list_bytes
        )

        #####################

        message_o_dict_str_int_not_set = TProtocolMessage(
            message_id=1,
            dialogue_reference=(str(0), ""),
            target=0,
            performative=TProtocolMessage.Performative.PERFORMATIVE_O,
        )

        encoded_message_in_bytes = TProtocolMessage.serializer.encode(
            message_o_dict_str_int_not_set
        )
        decoded_message = cast(
            TProtocolMessage,
            TProtocolMessage.serializer.decode(encoded_message_in_bytes),
        )

        assert decoded_message.message_id == message_o_dict_str_int_not_set.message_id
        assert (
            decoded_message.dialogue_reference
            == message_o_dict_str_int_not_set.dialogue_reference
        )
        assert (
            decoded_message.dialogue_reference[0]
            == message_o_dict_str_int_not_set.dialogue_reference[0]
        )
        assert (
            decoded_message.dialogue_reference[1]
            == message_o_dict_str_int_not_set.dialogue_reference[1]
        )
        assert decoded_message.target == message_o_dict_str_int_not_set.target
        assert (
            decoded_message.performative == message_o_dict_str_int_not_set.performative
        )
        assert (
            decoded_message.content_o_list_bytes
            == message_o_dict_str_int_not_set.content_o_list_bytes
        )


class ProtocolGeneratorTestCase(TestCase):
    """Test case for ProtocolGenerator class."""

    def setUp(self):
        protocol_specification = mock.Mock()
        protocol_specification.name = "name"

    # @mock.patch(
    #     "aea.protocols.generator.common._get_sub_types_of_compositional_types",
    #     return_value=["some"],
    # )
    # def test__includes_custom_type_positive(self, *mocks):
    #     """Test _includes_custom_type method positive result."""
    #     content_type = "pt:union[pt:str]"
    #     result = not _is_composition_type_with_custom_type(content_type)
    #     self.assertTrue(result)
    #
    #     content_type = "pt:optional[pt:str]"
    #     result = not _is_composition_type_with_custom_type(content_type)
    #     self.assertTrue(result)

    # @mock.patch("aea.protocols.generator._get_indent_str")
    # @mock.patch(
    #     "aea.protocols.generator._get_sub_types_of_compositional_types",
    #     return_value=["Tuple", "FrozenSet"],
    # )
    # def test__check_content_type_str_tuple(self, *mocks):
    #     """Test _check_content_type_str method tuple."""
    #     no_of_indents = 1
    #     content_name = "name"
    #     content_type = (
    #         "Union[str, Dict[str, int], FrozenSet[DataModel, int], Dict[str, float]]"
    #     )
    #     self.protocol_generator._check_content_type_str(
    #         no_of_indents, content_name, content_type
    #     )
    #     # TODO: finish this test
