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
"""This module contains the tests for the protocol generator."""
import filecmp
import logging
import os
import shutil
import tempfile
import time
from pathlib import Path
from threading import Thread
from typing import Optional, cast
from unittest import TestCase, mock

import pytest

from aea.aea_builder import AEABuilder
from aea.configurations.base import (
    ComponentType,
    ProtocolId,
    ProtocolSpecificationParseError,
    PublicId,
    SkillConfig,
)
from aea.configurations.constants import DEFAULT_LEDGER, DEFAULT_PRIVATE_KEY_FILE
from aea.crypto.helpers import create_private_key
from aea.mail.base import Envelope
from aea.protocols.base import Message
from aea.protocols.generator.base import ProtocolGenerator
from aea.protocols.generator.common import (
    _camel_case_to_snake_case,
    _create_protocol_file,
    _get_sub_types_of_compositional_types,
    _includes_custom_type,
    _python_pt_or_ct_type_to_proto_type,
    _to_camel_case,
    _union_sub_type_to_protobuf_variable_name,
    load_protocol_specification,
)
from aea.protocols.generator.extract_specification import (
    _ct_specification_type_to_python_type,
    _mt_specification_type_to_python_type,
    _optional_specification_type_to_python_type,
    _pt_specification_type_to_python_type,
    _pct_specification_type_to_python_type,
    _pmt_specification_type_to_python_type,
    _specification_type_to_python_type,
    extract,
    PythonicProtocolSpecification,
)
from aea.protocols.generator.extract_specification import (
    _specification_type_to_python_type,
)
from aea.skills.base import Handler, Skill, SkillContext
from aea.test_tools.test_cases import UseOef

from tests.conftest import ROOT_DIR
from tests.data.generator.t_protocol.message import (  # type: ignore
    TProtocolMessage,
)


logger = logging.getLogger("aea")
logging.basicConfig(level=logging.INFO)

T_PROTOCOL_NAME = "t_protocol"
PATH_TO_T_PROTOCOL_SPECIFICATION = os.path.join(
    ROOT_DIR, "tests", "data", "sample_specification.yaml"
)
PATH_TO_T_PROTOCOL = os.path.join(
    ROOT_DIR, "tests", "data", "generator", T_PROTOCOL_NAME
)


class TestCompareLatestGeneratorOutputWithTestProtocol:
    """Test that the "t_protocol" test protocol matches with the latest generator output based on its specification."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

    def test_compare_latest_generator_output_with_test_protocol(self):
        """Test that the "t_protocol" test protocol matches with the latest generator output based on its specification."""
        # Specification

        path_to_generated_protocol = self.t
        dotted_path_to_package_for_imports = "tests.data.generator."

        # Generate the protocol
        try:
            protocol_generator = ProtocolGenerator(
                path_to_protocol_specification=PATH_TO_T_PROTOCOL_SPECIFICATION,
                output_path=path_to_generated_protocol,
                path_to_protocol_package=dotted_path_to_package_for_imports,
            )
            protocol_generator.generate()
        except Exception as e:
            pytest.skip(
                "Something went wrong when generating the protocol. The exception:"
                + str(e)
            )

        # # compare __init__.py
        # init_file_generated = Path(self.t, protocol_name, "__init__.py")
        # init_file_original = Path(path_to_original_protocol, "__init__.py",)
        # assert filecmp.cmp(init_file_generated, init_file_original)

        # # compare protocol.yaml
        # protocol_yaml_file_generated = Path(self.t, protocol_name, "protocol.yaml")
        # protocol_yaml_file_original = Path(path_to_original_protocol, "protocol.yaml",)
        # assert filecmp.cmp(protocol_yaml_file_generated, protocol_yaml_file_original)

        # compare message.py
        message_file_generated = Path(self.t, T_PROTOCOL_NAME, "message.py")
        message_file_original = Path(PATH_TO_T_PROTOCOL, "message.py",)
        assert filecmp.cmp(message_file_generated, message_file_original)

        # compare serialization.py
        serialization_file_generated = Path(self.t, T_PROTOCOL_NAME, "serialization.py")
        serialization_file_original = Path(PATH_TO_T_PROTOCOL, "serialization.py",)
        assert filecmp.cmp(serialization_file_generated, serialization_file_original)

        # compare .proto
        proto_file_generated = Path(
            self.t, T_PROTOCOL_NAME, "{}.proto".format(T_PROTOCOL_NAME)
        )
        proto_file_original = Path(
            PATH_TO_T_PROTOCOL, "{}.proto".format(T_PROTOCOL_NAME),
        )
        assert filecmp.cmp(proto_file_generated, proto_file_original)

        # compare _pb2.py
        pb2_file_generated = Path(
            self.t, T_PROTOCOL_NAME, "{}_pb2.py".format(T_PROTOCOL_NAME)
        )
        pb2_file_original = Path(
            PATH_TO_T_PROTOCOL, "{}_pb2.py".format(T_PROTOCOL_NAME),
        )
        assert filecmp.cmp(pb2_file_generated, pb2_file_original)

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


class TestEndToEndGenerator(UseOef):
    """
    Test that the generating a protocol works correctly in correct preconditions.

    Note: Types involving Floats seem to lose some precision when serialised then deserialised using protobuf.
    So tests for these types are commented out throughout for now.
    """

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)
        cls.private_key_path_1 = os.path.join(cls.t, DEFAULT_PRIVATE_KEY_FILE + "_1")
        cls.private_key_path_2 = os.path.join(cls.t, DEFAULT_PRIVATE_KEY_FILE + "_2")
        create_private_key(DEFAULT_LEDGER, cls.private_key_path_1)
        create_private_key(DEFAULT_LEDGER, cls.private_key_path_2)

    def test_generated_protocol_end_to_end(self):
        """Test that a generated protocol could be used in exchanging messages between two agents."""
        agent_name_1 = "my_aea_1"
        agent_name_2 = "my_aea_2"
        builder_1 = AEABuilder()
        builder_1.set_name(agent_name_1)
        builder_1.add_private_key(DEFAULT_LEDGER, self.private_key_path_1)
        builder_1.set_default_ledger(DEFAULT_LEDGER)
        builder_1.set_default_connection(PublicId.from_str("fetchai/oef:0.6.0"))
        builder_1.add_protocol(
            Path(ROOT_DIR, "packages", "fetchai", "protocols", "fipa")
        )
        builder_1.add_protocol(
            Path(ROOT_DIR, "packages", "fetchai", "protocols", "oef_search")
        )
        builder_1.add_component(
            ComponentType.PROTOCOL,
            Path(ROOT_DIR, "tests", "data", "generator", "t_protocol"),
            skip_consistency_check=True,
        )
        builder_1.add_connection(
            Path(ROOT_DIR, "packages", "fetchai", "connections", "oef")
        )

        builder_2 = AEABuilder()
        builder_2.set_name(agent_name_2)
        builder_2.add_private_key(DEFAULT_LEDGER, self.private_key_path_2)
        builder_2.set_default_ledger(DEFAULT_LEDGER)
        builder_2.add_protocol(
            Path(ROOT_DIR, "packages", "fetchai", "protocols", "fipa")
        )
        builder_2.add_protocol(
            Path(ROOT_DIR, "packages", "fetchai", "protocols", "oef_search")
        )
        builder_2.set_default_connection(PublicId.from_str("fetchai/oef:0.6.0"))
        builder_2.add_component(
            ComponentType.PROTOCOL,
            Path(ROOT_DIR, "tests", "data", "generator", "t_protocol"),
            skip_consistency_check=True,
        )
        builder_2.add_connection(
            Path(ROOT_DIR, "packages", "fetchai", "connections", "oef")
        )

        # create AEAs
        aea_1 = builder_1.build(connection_ids=[PublicId.from_str("fetchai/oef:0.6.0")])
        aea_2 = builder_2.build(connection_ids=[PublicId.from_str("fetchai/oef:0.6.0")])

        # message 1
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
        message.counterparty = aea_2.identity.address
        envelope = Envelope(
            to=aea_2.identity.address,
            sender=aea_1.identity.address,
            protocol_id=TProtocolMessage.protocol_id,
            message=message,
        )

        # message 2
        message_2 = TProtocolMessage(
            message_id=2,
            dialogue_reference=(str(0), ""),
            target=1,
            performative=TProtocolMessage.Performative.PERFORMATIVE_PT,
            content_bytes=b"some other bytes",
            content_int=43,
            content_float=43.7,
            content_bool=False,
            content_str="some other string",
        )
        message_2.counterparty = aea_1.identity.address

        # add handlers to AEA resources
        skill_context_1 = SkillContext(aea_1.context)
        skill_1 = Skill(SkillConfig("fake_skill", "fetchai", "0.1.0"), skill_context_1)
        skill_context_1._skill = skill_1

        agent_1_handler = Agent1Handler(
            skill_context=skill_context_1, name="fake_handler_1"
        )
        aea_1.resources._handler_registry.register(
            (
                PublicId.from_str("fetchai/fake_skill:0.1.0"),
                TProtocolMessage.protocol_id,
            ),
            agent_1_handler,
        )
        skill_context_2 = SkillContext(aea_2.context)
        skill_2 = Skill(SkillConfig("fake_skill", "fetchai", "0.1.0"), skill_context_2)
        skill_context_2._skill = skill_2

        agent_2_handler = Agent2Handler(
            message=message_2, skill_context=skill_context_2, name="fake_handler_2",
        )
        aea_2.resources._handler_registry.register(
            (
                PublicId.from_str("fetchai/fake_skill:0.1.0"),
                TProtocolMessage.protocol_id,
            ),
            agent_2_handler,
        )

        # Start threads
        t_1 = Thread(target=aea_1.start)
        t_2 = Thread(target=aea_2.start)
        try:
            t_1.start()
            t_2.start()
            time.sleep(1.0)
            aea_1.outbox.put(envelope)
            time.sleep(5.0)
            assert (
                agent_2_handler.handled_message.message_id == message.message_id
            ), "Message from Agent 1 to 2: message ids do not match"
            assert (
                agent_2_handler.handled_message.dialogue_reference
                == message.dialogue_reference
            ), "Message from Agent 1 to 2: dialogue references do not match"
            assert (
                agent_2_handler.handled_message.dialogue_reference[0]
                == message.dialogue_reference[0]
            ), "Message from Agent 1 to 2: dialogue reference[0]s do not match"
            assert (
                agent_2_handler.handled_message.dialogue_reference[1]
                == message.dialogue_reference[1]
            ), "Message from Agent 1 to 2: dialogue reference[1]s do not match"
            assert (
                agent_2_handler.handled_message.target == message.target
            ), "Message from Agent 1 to 2: targets do not match"
            assert (
                agent_2_handler.handled_message.performative == message.performative
            ), "Message from Agent 1 to 2: performatives do not match"
            assert (
                agent_2_handler.handled_message.content_bytes == message.content_bytes
            ), "Message from Agent 1 to 2: content_bytes do not match"
            assert (
                agent_2_handler.handled_message.content_int == message.content_int
            ), "Message from Agent 1 to 2: content_int do not match"
            # assert agent_2_handler.handled_message.content_float == message.content_float, "Message from Agent 1 to 2: content_float do not match"
            assert (
                agent_2_handler.handled_message.content_bool == message.content_bool
            ), "Message from Agent 1 to 2: content_bool do not match"
            assert (
                agent_2_handler.handled_message.content_str == message.content_str
            ), "Message from Agent 1 to 2: content_str do not match"

            assert (
                agent_1_handler.handled_message.message_id == message_2.message_id
            ), "Message from Agent 1 to 2: dialogue references do not match"
            assert (
                agent_1_handler.handled_message.dialogue_reference
                == message_2.dialogue_reference
            ), "Message from Agent 2 to 1: dialogue references do not match"
            assert (
                agent_1_handler.handled_message.dialogue_reference[0]
                == message_2.dialogue_reference[0]
            ), "Message from Agent 2 to 1: dialogue reference[0]s do not match"
            assert (
                agent_1_handler.handled_message.dialogue_reference[1]
                == message_2.dialogue_reference[1]
            ), "Message from Agent 2 to 1: dialogue reference[1]s do not match"
            assert (
                agent_1_handler.handled_message.target == message_2.target
            ), "Message from Agent 2 to 1: targets do not match"
            assert (
                agent_1_handler.handled_message.performative == message_2.performative
            ), "Message from Agent 2 to 1: performatives do not match"
            assert (
                agent_1_handler.handled_message.content_bytes == message_2.content_bytes
            ), "Message from Agent 2 to 1: content_bytes do not match"
            assert (
                agent_1_handler.handled_message.content_int == message_2.content_int
            ), "Message from Agent 2 to 1: content_int do not match"
            # assert agent_1_handler.handled_message.content_float == message_2.content_float, "Message from Agent 2 to 1: content_float do not match"
            assert (
                agent_1_handler.handled_message.content_bool == message_2.content_bool
            ), "Message from Agent 2 to 1: content_bool do not match"
            assert (
                agent_1_handler.handled_message.content_str == message_2.content_str
            ), "Message from Agent 2 to 1: content_str do not match"
            time.sleep(2.0)
        finally:
            aea_1.stop()
            aea_2.stop()
            t_1.join()
            t_2.join()

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestCommon:
    """Test for generator/common.py."""

    @classmethod
    def setup_class(cls):
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

    def test_to_camel_case(self):
        """Test the '_to_camel_case' method."""
        input_text_1 = "this_is_a_snake_case_text"
        expected_1 = "ThisIsASnakeCaseText"
        output_1 = _to_camel_case(input_text_1)
        assert output_1 == expected_1

        input_text_2 = "This_is_a_Snake_Case_text"
        expected_2 = "ThisIsASnakeCaseText"
        output_2 = _to_camel_case(input_text_2)
        assert output_2 == expected_2

    def test_camel_case_to_snake_case(self):
        """Test the '_camel_case_to_snake_case' method."""
        input_text_1 = "ThisIsASnakeCaseText"
        expected_1 = "this_is_a_snake_case_text"
        output_1 = _camel_case_to_snake_case(input_text_1)
        assert output_1 == expected_1

    def test_get_sub_types_of_compositional_types_positive(self,):
        """Positive test the '_get_sub_types_of_compositional_types' method."""
        composition_type_1 = "pt:set[pt:int]"
        expected_1 = ("pt:int",)
        assert _get_sub_types_of_compositional_types(composition_type_1) == expected_1

        composition_type_2 = "FrozenSet[bool]"
        expected_2 = ("bool",)
        assert _get_sub_types_of_compositional_types(composition_type_2) == expected_2

        composition_type_3 = "pt:list[pt:str]"
        expected_3 = ("pt:str",)
        assert _get_sub_types_of_compositional_types(composition_type_3) == expected_3

        composition_type_4 = "Tuple[bytes, ...]"
        expected_4 = ("bytes",)
        assert _get_sub_types_of_compositional_types(composition_type_4) == expected_4

        composition_type_5 = "pt:dict[pt:int, pt:int]"
        expected_5 = ("pt:int", "pt:int")
        assert _get_sub_types_of_compositional_types(composition_type_5) == expected_5

        composition_type_6 = "Dict[bool, float]"
        expected_6 = ("bool", "float")
        assert _get_sub_types_of_compositional_types(composition_type_6) == expected_6

        composition_type_6 = "pt:union[ct:DataModel, pt:bytes, pt:int, pt:bool, pt:float, pt:str, pt:set[pt:int], pt:list[pt:bool], pt:dict[pt:str,pt:str]]"
        expected_6 = (
            "ct:DataModel",
            "pt:bytes",
            "pt:int",
            "pt:bool",
            "pt:float",
            "pt:str",
            "pt:set[pt:int]",
            "pt:list[pt:bool]",
            "pt:dict[pt:str,pt:str]",
        )
        assert _get_sub_types_of_compositional_types(composition_type_6) == expected_6

        composition_type_7 = "Union[int, Tuple[bool, ...]]"
        expected_7 = ("int", "Tuple[bool, ...]")
        assert _get_sub_types_of_compositional_types(composition_type_7) == expected_7

        composition_type_8 = (
            "Union[DataModel, FrozenSet[int], Tuple[bool, ...], bytes, Dict[bool,float], int, "
            "FrozenSet[bool], Dict[int, str], Tuple[str, ...], bool, float, str, Dict[str, str]]"
        )
        expected_8 = (
            "DataModel",
            "FrozenSet[int]",
            "Tuple[bool, ...]",
            "bytes",
            "Dict[bool,float]",
            "int",
            "FrozenSet[bool]",
            "Dict[int, str]",
            "Tuple[str, ...]",
            "bool",
            "float",
            "str",
            "Dict[str, str]",
        )
        assert _get_sub_types_of_compositional_types(composition_type_8) == expected_8

        composition_type_9 = "pt:optional[pt:union[ct:DataModel, pt:bytes, pt:int, pt:bool, pt:float, pt:str, pt:set[pt:int], pt:list[pt:bool], pt:dict[pt:str,pt:str]]]"
        expected_9 = (
            "pt:union[ct:DataModel, pt:bytes, pt:int, pt:bool, pt:float, pt:str, pt:set[pt:int], pt:list[pt:bool], pt:dict[pt:str,pt:str]]",
        )
        assert _get_sub_types_of_compositional_types(composition_type_9) == expected_9

        composition_type_10 = "Optional[Union[DataModel, bytes, int, bool, float, str, FrozenSet[int], Tuple[bool, ...], Dict[str,str]]]"
        expected_10 = (
            "Union[DataModel, bytes, int, bool, float, str, FrozenSet[int], Tuple[bool, ...], Dict[str,str]]",
        )
        assert _get_sub_types_of_compositional_types(composition_type_10) == expected_10

    def test_get_sub_types_of_compositional_types_negative(self,):
        """Negative test the '_get_sub_types_of_compositional_types' method"""
        composition_type_1 = "pt:int"
        expected_1 = tuple()
        assert _get_sub_types_of_compositional_types(composition_type_1) == expected_1

        composition_type_2 = "pt:int[pt:DataModel]"
        expected_2 = tuple()
        assert _get_sub_types_of_compositional_types(composition_type_2) == expected_2

    def test_union_sub_type_to_protobuf_variable_name(self,):
        """Test the '_union_sub_type_to_protobuf_variable_name' method"""
        content_name = "proposal"

        content_type_1 = "FrozenSet[int]"
        assert (
            _union_sub_type_to_protobuf_variable_name(content_name, content_type_1)
            == "proposal_type_set_of_int"
        )

        content_type_2 = "Tuple[str, ...]"
        assert (
            _union_sub_type_to_protobuf_variable_name(content_name, content_type_2)
            == "proposal_type_list_of_str"
        )

        content_type_3 = "Dict[bool, float]"
        assert (
            _union_sub_type_to_protobuf_variable_name(content_name, content_type_3)
            == "proposal_type_dict_of_bool_float"
        )

        content_type_4 = "int"
        assert (
            _union_sub_type_to_protobuf_variable_name(content_name, content_type_4)
            == "proposal_type_int"
        )

        content_type_5 = "DataModel"
        assert (
            _union_sub_type_to_protobuf_variable_name(content_name, content_type_5)
            == "proposal_type_DataModel"
        )

    def test_python_pt_or_ct_type_to_proto_type(self,):
        """Test the '_python_pt_or_ct_type_to_proto_type' method"""
        content_type_bytes = "bytes"
        assert _python_pt_or_ct_type_to_proto_type(content_type_bytes) == "bytes"

        content_type_int = "int"
        assert _python_pt_or_ct_type_to_proto_type(content_type_int) == "int32"

        content_type_float = "float"
        assert _python_pt_or_ct_type_to_proto_type(content_type_float) == "float"

        content_type_bool = "bool"
        assert _python_pt_or_ct_type_to_proto_type(content_type_bool) == "bool"

        content_type_str = "str"
        assert _python_pt_or_ct_type_to_proto_type(content_type_str) == "string"

        content_type_ct = "Query"
        assert _python_pt_or_ct_type_to_proto_type(content_type_ct) == "Query"

    def test_includes_custom_type(self,):
        """Test the '_includes_custom_type' method"""
        content_type_includes_1 = "Optional[DataModel]"
        assert _includes_custom_type(content_type_includes_1) == True

        content_type_includes_2 = "Union[int, DataModel]"
        assert _includes_custom_type(content_type_includes_2) == True

        content_type_includes_3 = "Optional[Union[int, float, DataModel, Query, float]]"
        assert _includes_custom_type(content_type_includes_3) == True

        content_type_not_includes_1 = "Optional[int]"
        assert _includes_custom_type(content_type_not_includes_1) == False

        content_type_not_includes_2 = "Union[int, float, str]"
        assert _includes_custom_type(content_type_not_includes_2) == False

        content_type_not_includes_3 = (
            "Optional[Union[int, float, FrozenSet[int], Tuple[bool, ...], float]]"
        )
        assert _includes_custom_type(content_type_not_includes_3) == False

    def test_is_installed(self,):
        """Test the 'is_installed' method"""
        # ToDo
        pass

    def test_check_prerequisites(self,):
        """Test the 'check_prerequisites' method"""
        # ToDo
        pass

    def test_load_protocol_specification(self,):
        """Test the 'load_protocol_specification' method"""
        spec = load_protocol_specification(PATH_TO_T_PROTOCOL_SPECIFICATION)
        assert spec.name == T_PROTOCOL_NAME
        assert spec.version == "0.1.0"
        assert spec.author == "fetchai"
        assert spec.license == "Apache-2.0"
        assert spec.aea_version == ">=0.5.0, <0.6.0"
        assert spec.description == "A protocol for testing purposes."
        assert spec.speech_acts is not None
        assert spec.protobuf_snippets is not None and spec.protobuf_snippets is not ""

    def test_create_protocol_file(self,):
        """Test the '_create_protocol_file' method"""
        file_name = "temp_file"
        file_content = "this is a temporary file"

        _create_protocol_file(self.t, file_name, file_content)
        path_to_the_file = os.path.join(self.t, file_name)

        assert Path(path_to_the_file).exists()
        assert Path(path_to_the_file).read_text() == file_content

    def test_try_run_black_formatting(self,):
        """Test the 'try_run_black_formatting' method"""
        # ToDo
        pass

    def test_try_run_protoc(self,):
        """Test the 'try_run_protoc' method"""
        # ToDo
        pass

    def test_check_protobuf_using_protoc(self,):
        """Test the 'check_protobuf_using_protoc' method"""
        # ToDo
        pass

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestExtractSpecification(TestCase):
    """Test for generator/extract_specification.py."""

    @classmethod
    def setup_class(cls):
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

    def test_ct_specification_type_to_python_type(self):
        """Test the '_ct_specification_type_to_python_type' method."""
        specification_type_1 = "ct:DataModel"
        expected_1 = "DataModel"
        assert _ct_specification_type_to_python_type(specification_type_1) == expected_1

        specification_type_2 = "ct:Query"
        expected_2 = "Query"
        assert _ct_specification_type_to_python_type(specification_type_2) == expected_2

    def test_pt_specification_type_to_python_type(self):
        """Test the '_pt_specification_type_to_python_type' method."""
        specification_type_1 = "pt:bytes"
        expected_1 = "bytes"
        assert _pt_specification_type_to_python_type(specification_type_1) == expected_1

        specification_type_2 = "pt:int"
        expected_2 = "int"
        assert _pt_specification_type_to_python_type(specification_type_2) == expected_2

        specification_type_3 = "pt:float"
        expected_3 = "float"
        assert _pt_specification_type_to_python_type(specification_type_3) == expected_3

        specification_type_4 = "pt:bool"
        expected_4 = "bool"
        assert _pt_specification_type_to_python_type(specification_type_4) == expected_4

        specification_type_5 = "pt:str"
        expected_5 = "str"
        assert _pt_specification_type_to_python_type(specification_type_5) == expected_5

    def test_pct_specification_type_to_python_type(self):
        """Test the '_pct_specification_type_to_python_type' method."""
        specification_type_1 = "pt:set[pt:bytes]"
        expected_1 = "FrozenSet[bytes]"
        assert (
            _pct_specification_type_to_python_type(specification_type_1) == expected_1
        )

        specification_type_2 = "pt:set[pt:int]"
        expected_2 = "FrozenSet[int]"
        assert (
            _pct_specification_type_to_python_type(specification_type_2) == expected_2
        )

        specification_type_3 = "pt:set[pt:float]"
        expected_3 = "FrozenSet[float]"
        assert (
            _pct_specification_type_to_python_type(specification_type_3) == expected_3
        )

        specification_type_4 = "pt:set[pt:bool]"
        expected_4 = "FrozenSet[bool]"
        assert (
            _pct_specification_type_to_python_type(specification_type_4) == expected_4
        )

        specification_type_5 = "pt:set[pt:str]"
        expected_5 = "FrozenSet[str]"
        assert (
            _pct_specification_type_to_python_type(specification_type_5) == expected_5
        )

        specification_type_6 = "pt:list[pt:bytes]"
        expected_6 = "Tuple[bytes, ...]"
        assert (
            _pct_specification_type_to_python_type(specification_type_6) == expected_6
        )

        specification_type_7 = "pt:list[pt:int]"
        expected_7 = "Tuple[int, ...]"
        assert (
            _pct_specification_type_to_python_type(specification_type_7) == expected_7
        )

        specification_type_8 = "pt:list[pt:float]"
        expected_8 = "Tuple[float, ...]"
        assert (
            _pct_specification_type_to_python_type(specification_type_8) == expected_8
        )

        specification_type_9 = "pt:list[pt:bool]"
        expected_9 = "Tuple[bool, ...]"
        assert (
            _pct_specification_type_to_python_type(specification_type_9) == expected_9
        )

        specification_type_10 = "pt:list[pt:str]"
        expected_10 = "Tuple[str, ...]"
        assert (
            _pct_specification_type_to_python_type(specification_type_10) == expected_10
        )

    def test_pmt_specification_type_to_python_type(self):
        """Test the '_pmt_specification_type_to_python_type' method."""
        specification_type_1 = "pt:dict[pt:int, pt:bytes]"
        expected_1 = "Dict[int, bytes]"
        assert (
            _pmt_specification_type_to_python_type(specification_type_1) == expected_1
        )

        specification_type_2 = "pt:dict[pt:int, pt:int]"
        expected_2 = "Dict[int, int]"
        assert (
            _pmt_specification_type_to_python_type(specification_type_2) == expected_2
        )

        specification_type_3 = "pt:dict[pt:int, pt:float]"
        expected_3 = "Dict[int, float]"
        assert (
            _pmt_specification_type_to_python_type(specification_type_3) == expected_3
        )

        specification_type_4 = "pt:dict[pt:int, pt:bool]"
        expected_4 = "Dict[int, bool]"
        assert (
            _pmt_specification_type_to_python_type(specification_type_4) == expected_4
        )

        specification_type_5 = "pt:dict[pt:int, pt:str]"
        expected_5 = "Dict[int, str]"
        assert (
            _pmt_specification_type_to_python_type(specification_type_5) == expected_5
        )

        specification_type_6 = "pt:dict[pt:bool, pt:bytes]"
        expected_6 = "Dict[bool, bytes]"
        assert (
            _pmt_specification_type_to_python_type(specification_type_6) == expected_6
        )

        specification_type_7 = "pt:dict[pt:bool, pt:int]"
        expected_7 = "Dict[bool, int]"
        assert (
            _pmt_specification_type_to_python_type(specification_type_7) == expected_7
        )

        specification_type_8 = "pt:dict[pt:bool, pt:float]"
        expected_8 = "Dict[bool, float]"
        assert (
            _pmt_specification_type_to_python_type(specification_type_8) == expected_8
        )

        specification_type_9 = "pt:dict[pt:bool, pt:bool]"
        expected_9 = "Dict[bool, bool]"
        assert (
            _pmt_specification_type_to_python_type(specification_type_9) == expected_9
        )

        specification_type_10 = "pt:dict[pt:bool, pt:str]"
        expected_10 = "Dict[bool, str]"
        assert (
            _pmt_specification_type_to_python_type(specification_type_10) == expected_10
        )

        specification_type_11 = "pt:dict[pt:str, pt:bytes]"
        expected_11 = "Dict[str, bytes]"
        assert (
            _pmt_specification_type_to_python_type(specification_type_11) == expected_11
        )

        specification_type_12 = "pt:dict[pt:str, pt:int]"
        expected_12 = "Dict[str, int]"
        assert (
            _pmt_specification_type_to_python_type(specification_type_12) == expected_12
        )

        specification_type_13 = "pt:dict[pt:str, pt:float]"
        expected_13 = "Dict[str, float]"
        assert (
            _pmt_specification_type_to_python_type(specification_type_13) == expected_13
        )

        specification_type_14 = "pt:dict[pt:str, pt:bool]"
        expected_14 = "Dict[str, bool]"
        assert (
            _pmt_specification_type_to_python_type(specification_type_14) == expected_14
        )

        specification_type_15 = "pt:dict[pt:str, pt:str]"
        expected_15 = "Dict[str, str]"
        assert (
            _pmt_specification_type_to_python_type(specification_type_15) == expected_15
        )

    def test_mt_specification_type_to_python_type(self):
        """Test the '_mt_specification_type_to_python_type' method."""
        specification_type_1 = "pt:union[pt:int, pt:bytes]"
        expected_1 = "Union[int, bytes]"
        assert _mt_specification_type_to_python_type(specification_type_1) == expected_1

        specification_type_2 = "pt:union[ct:DataModel, pt:bytes, pt:int, pt:bool, pt:float, pt:str, pt:set[pt:int], pt:list[pt:bool], pt:dict[pt:str,pt:str]]"
        expected_2 = "Union[DataModel, bytes, int, bool, float, str, FrozenSet[int], Tuple[bool, ...], Dict[str, str]]"
        assert _mt_specification_type_to_python_type(specification_type_2) == expected_2

        specification_type_3 = (
            "pt:union[ct:DataModel, pt:set[pt:int], pt:list[pt:bool], pt:bytes, pt:dict[pt:bool,pt:float], pt:int, "
            "pt:set[pt:bool], pt:dict[pt:int, pt:str], pt:list[pt:str], pt:bool, pt:float, pt:str, pt:dict[pt:str, pt:str]]"
        )
        expected_3 = (
            "Union[DataModel, FrozenSet[int], Tuple[bool, ...], bytes, Dict[bool, float], int, "
            "FrozenSet[bool], Dict[int, str], Tuple[str, ...], bool, float, str, Dict[str, str]]"
        )
        assert _mt_specification_type_to_python_type(specification_type_3) == expected_3

    def test_optional_specification_type_to_python_type(self):
        """Test the '_optional_specification_type_to_python_type' method."""
        specification_type_1 = (
            "pt:optional[pt:union[ct:DataModel, pt:bytes, pt:int, pt:bool, pt:float, pt:str, pt:set[pt:int], "
            "pt:list[pt:bool], pt:dict[pt:str, pt:str]]]"
        )
        expected_1 = "Optional[Union[DataModel, bytes, int, bool, float, str, FrozenSet[int], Tuple[bool, ...], Dict[str, str]]]"
        assert (
            _optional_specification_type_to_python_type(specification_type_1)
            == expected_1
        )

        specification_type_2 = (
            "pt:optional[pt:union[ct:DataModel, pt:bytes, pt:int, pt:bool, pt:float, pt:str, pt:set[pt:int], "
            "pt:list[pt:bool], pt:dict[pt:str,pt:str]]]"
        )
        expected_2 = "Optional[Union[DataModel, bytes, int, bool, float, str, FrozenSet[int], Tuple[bool, ...], Dict[str, str]]]"
        assert (
            _optional_specification_type_to_python_type(specification_type_2)
            == expected_2
        )

        specification_type_3 = "pt:optional[ct:DataModel]"
        expected_3 = "Optional[DataModel]"
        assert (
            _optional_specification_type_to_python_type(specification_type_3)
            == expected_3
        )

    def test_specification_type_to_python_type(self):
        """Test the '_specification_type_to_python_type' method."""
        specification_type_1 = "ct:DataModel"
        expected_1 = "DataModel"
        assert _specification_type_to_python_type(specification_type_1) == expected_1

        specification_type_2 = "pt:bytes"
        expected_2 = "bytes"
        assert _specification_type_to_python_type(specification_type_2) == expected_2

        specification_type_3 = "pt:set[pt:int]"
        expected_3 = "FrozenSet[int]"
        assert _specification_type_to_python_type(specification_type_3) == expected_3

        specification_type_4 = "pt:list[pt:float]"
        expected_4 = "Tuple[float, ...]"
        assert _specification_type_to_python_type(specification_type_4) == expected_4

        specification_type_5 = "pt:dict[pt:bool, pt:str]"
        expected_5 = "Dict[bool, str]"
        assert _specification_type_to_python_type(specification_type_5) == expected_5

        specification_type_6 = "pt:union[pt:int, pt:bytes]"
        expected_6 = "Union[int, bytes]"
        assert _specification_type_to_python_type(specification_type_6) == expected_6

        specification_type_7 = (
            "pt:optional[pt:union[ct:DataModel, pt:bytes, pt:int, pt:bool, pt:float, pt:str, pt:set[pt:int], "
            "pt:list[pt:bool], pt:dict[pt:str,pt:str]]]"
        )
        expected_7 = "Optional[Union[DataModel, bytes, int, bool, float, str, FrozenSet[int], Tuple[bool, ...], Dict[str, str]]]"
        assert _specification_type_to_python_type(specification_type_7) == expected_7

        specification_type_8 = "wrong_type"
        with self.assertRaises(ProtocolSpecificationParseError) as cm:
            _specification_type_to_python_type(specification_type_8)
        self.assertEqual(str(cm.exception), "Unsupported type: '{}'".format(specification_type_8))

        specification_type_9 = "pt:integer"
        with self.assertRaises(ProtocolSpecificationParseError) as cm:
            _specification_type_to_python_type(specification_type_9)
        self.assertEqual(str(cm.exception), "Unsupported type: '{}'".format(specification_type_9))

        specification_type_10 = "pt: list"
        with self.assertRaises(ProtocolSpecificationParseError) as cm:
            _specification_type_to_python_type(specification_type_10)
        self.assertEqual(str(cm.exception), "Unsupported type: '{}'".format(specification_type_10))

        specification_type_11 = "pt:list[wrong_sub_type]"
        with self.assertRaises(ProtocolSpecificationParseError) as cm:
            _specification_type_to_python_type(specification_type_11)
        self.assertEqual(str(cm.exception), "Unsupported type: 'wrong_sub_type'")

    def test_pythonic_protocol_specification_class(self):
        """Test the 'PythonicProtocolSpecification' class."""
        spec = PythonicProtocolSpecification()
        assert spec.speech_acts == dict()
        assert spec.all_performatives == list()
        assert spec.all_unique_contents == dict()
        assert spec.all_custom_types == list()
        assert spec.custom_custom_types == dict()
        assert spec.initial_performatives == list()
        assert spec.reply == dict()
        assert spec.terminal_performatives == list()
        assert spec.roles == list()
        assert spec.end_states == list()
        assert spec.typing_imports == {
            "Set": True,
            "Tuple": True,
            "cast": True,
            "FrozenSet": False,
            "Dict": False,
            "Union": False,
            "Optional": False,
        }

    def test_extract_positive(self):
        """Positive test the 'extract' method."""
        protocol_specification = load_protocol_specification(
            PATH_TO_T_PROTOCOL_SPECIFICATION
        )
        spec = extract(protocol_specification)

        assert spec.speech_acts == {
            "performative_ct": {"content_ct": "DataModel"},
            "performative_pt": {
                "content_bytes": "bytes",
                "content_int": "int",
                "content_float": "float",
                "content_bool": "bool",
                "content_str": "str",
            },
            "performative_pct": {
                "content_set_bytes": "FrozenSet[bytes]",
                "content_set_int": "FrozenSet[int]",
                "content_set_float": "FrozenSet[float]",
                "content_set_bool": "FrozenSet[bool]",
                "content_set_str": "FrozenSet[str]",
                "content_list_bytes": "Tuple[bytes, ...]",
                "content_list_int": "Tuple[int, ...]",
                "content_list_float": "Tuple[float, ...]",
                "content_list_bool": "Tuple[bool, ...]",
                "content_list_str": "Tuple[str, ...]",
            },
            "performative_pmt": {
                "content_dict_int_bytes": "Dict[int, bytes]",
                "content_dict_int_int": "Dict[int, int]",
                "content_dict_int_float": "Dict[int, float]",
                "content_dict_int_bool": "Dict[int, bool]",
                "content_dict_int_str": "Dict[int, str]",
                "content_dict_bool_bytes": "Dict[bool, bytes]",
                "content_dict_bool_int": "Dict[bool, int]",
                "content_dict_bool_float": "Dict[bool, float]",
                "content_dict_bool_bool": "Dict[bool, bool]",
                "content_dict_bool_str": "Dict[bool, str]",
                "content_dict_str_bytes": "Dict[str, bytes]",
                "content_dict_str_int": "Dict[str, int]",
                "content_dict_str_float": "Dict[str, float]",
                "content_dict_str_bool": "Dict[str, bool]",
                "content_dict_str_str": "Dict[str, str]",
            },
            "performative_mt": {
                "content_union_1": "Union[DataModel, bytes, int, float, bool, str, FrozenSet[int], Tuple[bool, ...], Dict[str, int]]",
                "content_union_2": "Union[FrozenSet[bytes], FrozenSet[int], FrozenSet[str], Tuple[float, ...], Tuple[bool, ...], Tuple[bytes, ...], Dict[str, int], Dict[int, float], Dict[bool, bytes]]",
            },
            "performative_o": {
                "content_o_ct": "Optional[DataModel]",
                "content_o_bool": "Optional[bool]",
                "content_o_set_int": "Optional[FrozenSet[int]]",
                "content_o_list_bytes": "Optional[Tuple[bytes, ...]]",
                "content_o_dict_str_int": "Optional[Dict[str, int]]",
            },
            "performative_empty_contents": {},
        }
        assert spec.all_performatives == [
            "performative_ct",
            "performative_empty_contents",
            "performative_mt",
            "performative_o",
            "performative_pct",
            "performative_pmt",
            "performative_pt",
        ]
        assert spec.all_unique_contents == {
            "content_ct": "DataModel",
            "content_bytes": "bytes",
            "content_int": "int",
            "content_float": "float",
            "content_bool": "bool",
            "content_str": "str",
            "content_set_bytes": "FrozenSet[bytes]",
            "content_set_int": "FrozenSet[int]",
            "content_set_float": "FrozenSet[float]",
            "content_set_bool": "FrozenSet[bool]",
            "content_set_str": "FrozenSet[str]",
            "content_list_bytes": "Tuple[bytes, ...]",
            "content_list_int": "Tuple[int, ...]",
            "content_list_float": "Tuple[float, ...]",
            "content_list_bool": "Tuple[bool, ...]",
            "content_list_str": "Tuple[str, ...]",
            "content_dict_int_bytes": "Dict[int, bytes]",
            "content_dict_int_int": "Dict[int, int]",
            "content_dict_int_float": "Dict[int, float]",
            "content_dict_int_bool": "Dict[int, bool]",
            "content_dict_int_str": "Dict[int, str]",
            "content_dict_bool_bytes": "Dict[bool, bytes]",
            "content_dict_bool_int": "Dict[bool, int]",
            "content_dict_bool_float": "Dict[bool, float]",
            "content_dict_bool_bool": "Dict[bool, bool]",
            "content_dict_bool_str": "Dict[bool, str]",
            "content_dict_str_bytes": "Dict[str, bytes]",
            "content_dict_str_int": "Dict[str, int]",
            "content_dict_str_float": "Dict[str, float]",
            "content_dict_str_bool": "Dict[str, bool]",
            "content_dict_str_str": "Dict[str, str]",
            "content_union_1": "Union[DataModel, bytes, int, float, bool, str, FrozenSet[int], Tuple[bool, ...], Dict[str, int]]",
            "content_union_2": "Union[FrozenSet[bytes], FrozenSet[int], FrozenSet[str], Tuple[float, ...], Tuple[bool, ...], Tuple[bytes, ...], Dict[str, int], Dict[int, float], Dict[bool, bytes]]",
            "content_o_ct": "Optional[DataModel]",
            "content_o_bool": "Optional[bool]",
            "content_o_set_int": "Optional[FrozenSet[int]]",
            "content_o_list_bytes": "Optional[Tuple[bytes, ...]]",
            "content_o_dict_str_int": "Optional[Dict[str, int]]",
        }
        assert spec.all_custom_types == ["DataModel"]
        assert spec.custom_custom_types == {"DataModel": "CustomDataModel"}
        assert spec.initial_performatives == ['PERFORMATIVE_CT', 'PERFORMATIVE_PT']
        assert spec.reply == {'performative_ct': ['performative_pct'], 'performative_pt': ['performative_pmt'], 'performative_pct': ['performative_mt', 'performative_o'], 'performative_pmt': ['performative_mt', 'performative_o'], 'performative_mt': [], 'performative_o': [], 'performative_empty_contents': ['performative_empty_contents']}
        assert spec.terminal_performatives == ['PERFORMATIVE_MT', 'PERFORMATIVE_O', 'PERFORMATIVE_EMPTY_CONTENTS']
        assert spec.roles == ['role_1', 'role_2']
        assert spec.end_states == ['end_state_1', 'end_state_2', 'end_state_3']
        assert spec.typing_imports == {
            "Set": True,
            "Tuple": True,
            "cast": True,
            "FrozenSet": True,
            "Dict": True,
            "Union": True,
            "Optional": True,
        }

    @mock.patch(
        "aea.protocols.generator.validate.validate",
        return_value=[False, "some error."],
    )
    def test_extract_negative_invalid_specification(self, validate_mock):
        """Negative test the 'extract' method."""
        pytest.skip("todo")
        # ToDo
        protocol_specification = load_protocol_specification(
            PATH_TO_T_PROTOCOL_SPECIFICATION
        )
        with self.assertRaises(ProtocolSpecificationParseError) as cm:
            extract(protocol_specification)
        expected_msg = "some error."
        self.assertIn(expected_msg, str(cm))

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


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


class Agent1Handler(Handler):
    """The handler for agent 1."""

    SUPPORTED_PROTOCOL = TProtocolMessage.protocol_id  # type: Optional[ProtocolId]

    def __init__(self, **kwargs):
        """Initialize the handler."""
        super().__init__(**kwargs)
        self.kwargs = kwargs
        self.handled_message = None

    def setup(self) -> None:
        """Implement the setup for the handler."""
        pass

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :return: None
        """
        self.handled_message = message

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """


class Agent2Handler(Handler):
    """The handler for agent 2."""

    SUPPORTED_PROTOCOL = TProtocolMessage.protocol_id  # type: Optional[ProtocolId]

    def __init__(self, message, **kwargs):
        """Initialize the handler."""
        print("inside handler's initialisation method for agent 2")
        super().__init__(**kwargs)
        self.kwargs = kwargs
        self.handled_message = None
        self.message_2 = message

    def setup(self) -> None:
        """Implement the setup for the handler."""
        pass

    def handle(self, message: Message) -> None:
        """
        Implement the reaction to a message.

        :param message: the message
        :return: None
        """
        self.handled_message = message
        envelope = Envelope(
            to=message.counterparty,
            sender=self.context.agent_address,
            protocol_id=TProtocolMessage.protocol_id,
            message=self.message_2,
        )
        self.context.outbox.put(envelope)

    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """
