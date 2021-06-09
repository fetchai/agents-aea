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
import logging
import os
import shutil
import tempfile
from pathlib import Path
from typing import cast
from unittest import TestCase, mock

import pytest

from aea.configurations.base import (
    ProtocolSpecification,
    ProtocolSpecificationParseError,
)
from aea.configurations.constants import SUPPORTED_PROTOCOL_LANGUAGES
from aea.configurations.data_types import PublicId
from aea.protocols.generator.base import (
    CUSTOM_TYPES_DOT_PY_FILE_NAME,
    ProtocolGenerator,
)
from aea.protocols.generator.common import _to_camel_case

from tests.conftest import ROOT_DIR, match_files
from tests.data.generator.t_protocol.message import TProtocolMessage  # type: ignore
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
        is_matched, diff = match_files(init_file_generated, init_file_original)
        assert (
            is_matched or len(diff) == 194
        ), f"Difference Found between __init__.py files:\n{diff}"

        # compare message.py
        message_file_generated = Path(self.t, T_PROTOCOL_NAME, "message.py")
        message_file_original = Path(PATH_TO_T_PROTOCOL, "message.py",)
        is_matched, diff = match_files(message_file_generated, message_file_original)
        assert is_matched, f"Difference Found between message.py files:\n{diff}"

        # compare serialization.py
        serialization_file_generated = Path(self.t, T_PROTOCOL_NAME, "serialization.py")
        serialization_file_original = Path(PATH_TO_T_PROTOCOL, "serialization.py",)
        is_matched, diff = match_files(
            serialization_file_generated, serialization_file_original
        )
        assert is_matched, f"Difference Found between serialization.py files:\n{diff}"

        # compare dialogues.py
        dialogue_file_generated = Path(self.t, T_PROTOCOL_NAME, "dialogues.py")
        dialogue_file_original = Path(PATH_TO_T_PROTOCOL, "dialogues.py",)
        is_matched, diff = match_files(dialogue_file_generated, dialogue_file_original)
        assert is_matched, f"Difference Found between dialogues.py files:\n{diff}"

        # compare .proto
        proto_file_generated = Path(
            self.t, T_PROTOCOL_NAME, "{}.proto".format(T_PROTOCOL_NAME)
        )
        proto_file_original = Path(
            PATH_TO_T_PROTOCOL, "{}.proto".format(T_PROTOCOL_NAME),
        )
        is_matched, diff = match_files(proto_file_generated, proto_file_original)
        assert is_matched, f"Difference Found between .proto files:\n{diff}"

        # compare _pb2.py # noqa: E800
        # ToDo this part fails in CI. Investigate why?
        # pb2_file_generated = Path( # noqa: E800
        #     self.t, T_PROTOCOL_NAME, "{}_pb2.py".format(T_PROTOCOL_NAME) # noqa: E800
        # ) # noqa: E800
        # pb2_file_original = Path( # noqa: E800
        #     PATH_TO_T_PROTOCOL, "{}_pb2.py".format(T_PROTOCOL_NAME), # noqa: E800
        # ) # noqa: E800
        # is_matched, diff = match_files(pb2_file_generated, pb2_file_original) # noqa: E800
        # assert is_matched, f"Difference Found between _pb2.py files:\n{diff}" # noqa: E800

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestCompareLatestGeneratorOutputWithTestProtocolWithNoCustomTypes:
    """Test that the "t_protocol" test protocol matches with the latest generator output based on its specification."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

    def test_compare_latest_generator_output_with_test_protocol(self):
        """
        Test that the "t_protocol" test protocol matches with the latest generator output based on its specification.

        Note:
            - custom_types.py files are not compared as the generated one is only a template.
            - protocol.yaml files are consequently not compared either because the different
              custom_types.py files makes their IPFS hashes different.
        """

        protocol_name = "t_protocol_no_ct"
        path_to_protocol_specification_with_no_custom_types = os.path.join(
            ROOT_DIR, "tests", "data", "sample_specification_no_custom_types.yaml"
        )
        path_to_generated_protocol = self.t
        dotted_path_to_package_for_imports = "tests.data.generator."
        path_to_protocol = os.path.join(
            ROOT_DIR, "tests", "data", "generator", protocol_name
        )

        # Generate the protocol
        try:
            protocol_generator = ProtocolGenerator(
                path_to_protocol_specification=path_to_protocol_specification_with_no_custom_types,
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
        init_file_generated = Path(self.t, protocol_name, "__init__.py")
        init_file_original = Path(path_to_protocol, "__init__.py",)
        is_matched, diff = match_files(init_file_generated, init_file_original)
        assert (
            is_matched or len(diff) == 194
        ), f"Difference Found between __init__.py files:\n{diff}"

        # compare message.py
        message_file_generated = Path(self.t, protocol_name, "message.py")
        message_file_original = Path(path_to_protocol, "message.py",)
        is_matched, diff = match_files(message_file_generated, message_file_original)
        assert is_matched, f"Difference Found between message.py files:\n{diff}"

        # compare serialization.py
        serialization_file_generated = Path(self.t, protocol_name, "serialization.py")
        serialization_file_original = Path(path_to_protocol, "serialization.py",)
        is_matched, diff = match_files(
            serialization_file_generated, serialization_file_original
        )
        assert is_matched, f"Difference Found between serialization.py files:\n{diff}"

        # compare dialogues.py
        dialogue_file_generated = Path(self.t, protocol_name, "dialogues.py")
        dialogue_file_original = Path(path_to_protocol, "dialogues.py",)
        is_matched, diff = match_files(dialogue_file_generated, dialogue_file_original)
        assert is_matched, f"Difference Found between dialogues.py files:\n{diff}"

        # compare .proto
        proto_file_generated = Path(
            self.t, protocol_name, "{}.proto".format(protocol_name)
        )
        proto_file_original = Path(path_to_protocol, "{}.proto".format(protocol_name),)
        is_matched, diff = match_files(proto_file_generated, proto_file_original)
        assert is_matched, f"Difference Found between .proto files:\n{diff}"

        # compare _pb2.py # noqa: E800
        # ToDo this part fails in CI. Investigate why? # noqa: E800
        # pb2_file_generated = Path( # noqa: E800
        #     self.t, protocol_name, "{}_pb2.py".format(protocol_name) # noqa: E800
        # ) # noqa: E800
        # pb2_file_original = Path(path_to_protocol, "{}_pb2.py".format(protocol_name),) # noqa: E800
        # is_matched, diff = match_files(pb2_file_generated, pb2_file_original) # noqa: E800
        # assert is_matched, f"Difference Found between _pb2.py files:\n{diff}" # noqa: E800

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
        # assert decoded_message.content_float == message.content_float # noqa: E800
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
        # assert decoded_message.content_set_float == message.content_set_float # noqa: E800
        assert decoded_message.content_set_bool == message.content_set_bool
        assert decoded_message.content_set_str == message.content_set_str
        assert decoded_message.content_list_bytes == message.content_list_bytes
        assert decoded_message.content_list_int == message.content_list_int
        # assert decoded_message.content_list_float == message.content_list_float # noqa: E800
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
        # assert decoded_message.content_dict_int_float == message.content_dict_int_float # noqa: E800
        assert decoded_message.content_dict_int_bool == message.content_dict_int_bool
        assert decoded_message.content_dict_int_str == message.content_dict_int_str
        assert (
            decoded_message.content_dict_bool_bytes == message.content_dict_bool_bytes
        )
        assert decoded_message.content_dict_bool_int == message.content_dict_bool_int
        # assert decoded_message.content_dict_bool_float == message.content_dict_bool_float # noqa: E800
        assert decoded_message.content_dict_bool_bool == message.content_dict_bool_bool
        assert decoded_message.content_dict_bool_str == message.content_dict_bool_str
        assert decoded_message.content_dict_str_bytes == message.content_dict_str_bytes
        assert decoded_message.content_dict_str_int == message.content_dict_str_int
        # assert decoded_message.content_dict_str_float == message.content_dict_str_float # noqa: E800
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
    """Test for generator/base.py."""

    @classmethod
    def setup_class(cls):
        """Setup class."""
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

    def _mock_config(self):
        return """lint:
          rules:
            remove:
              - MESSAGE_NAMES_UPPER_CAMEL_CASE
              - ENUM_FIELD_NAMES_ZERO_VALUE_END_WITH
              - PACKAGE_NAME_LOWER_CASE
              - REPEATED_FIELD_NAMES_PLURALIZED
              - FIELD_NAMES_LOWER_SNAKE_CASE"""

    @mock.patch(
        "aea.protocols.generator.base.check_prerequisites",
        side_effect=FileNotFoundError("Some error!"),
    )
    def test_init_negative_no_prerequisits(self, mocked_check_prerequisites):
        """Negative test for the '__init__' method: check_prerequisites fails."""
        with self.assertRaises(FileNotFoundError) as cm:
            ProtocolGenerator(PATH_TO_T_PROTOCOL, self.t)
            expected_msg = "Some error!"
            assert str(cm.exception) == expected_msg

    @mock.patch(
        "aea.protocols.generator.base.load_protocol_specification",
        side_effect=ValueError("Some error!"),
    )
    def test_init_negative_loading_specification_fails(self, mocked_load):
        """Negative test for the '__init__' method: loading the specification fails."""
        with mock.patch("aea.protocols.generator.base.check_prerequisites"):
            with self.assertRaises(ValueError) as cm:
                ProtocolGenerator(PATH_TO_T_PROTOCOL, self.t)
                expected_msg = "Some error!"
                assert str(cm.exception) == expected_msg

    @mock.patch(
        "aea.protocols.generator.base.extract",
        side_effect=ProtocolSpecificationParseError("Some error!"),
    )
    def test_init_negative_extracting_specification_fails(self, mocked_extract):
        """Negative test for the '__init__' method: extracting the specification fails."""
        with mock.patch("aea.protocols.generator.base.check_prerequisites"):
            p_spec_mock = mock.MagicMock(ProtocolSpecification)
            p_spec_mock.name = "some_name"
            p_spec_mock.author = "some_author"
            with mock.patch(
                "aea.protocols.generator.base.load_protocol_specification",
                return_value=p_spec_mock,
            ):
                with mock.patch(
                    "aea.protocols.generator.base.validate",
                    return_value=(True, "valid!"),
                ):
                    with self.assertRaises(ProtocolSpecificationParseError) as cm:
                        ProtocolGenerator(
                            "some_path_to_protocol_specification", "some_path_to_output"
                        )
                        expected_msg = "Some error!"
                        assert str(cm.exception) == expected_msg

    @mock.patch(
        "aea.protocols.generator.base.validate", return_value=(False, "Some error!"),
    )
    def test_extract_negative_invalid_specification(self, mocked_validate):
        """Negative test the 'extract' method: invalid protocol specification"""
        with mock.patch("aea.protocols.generator.base.check_prerequisites"):
            p_spec_mock = mock.MagicMock(ProtocolSpecification)
            p_spec_mock.name = "some_name"
            p_spec_mock.author = "some_author"
            with mock.patch(
                "aea.protocols.generator.base.load_protocol_specification",
                return_value=p_spec_mock,
            ):
                with self.assertRaises(ProtocolSpecificationParseError) as cm:
                    ProtocolGenerator(
                        "some_path_to_protocol_specification", "some_path_to_output"
                    )
                    expected_msg = "Some error!"
                    assert str(cm.exception) == expected_msg

    def test_change_indent_negative_set_indent_to_negative_value(self):
        """Negative test for the '_change_indent' method: setting indent level to negative value."""
        with mock.patch("aea.protocols.generator.base.check_prerequisites"):
            p_spec_mock = mock.MagicMock(ProtocolSpecification)
            p_spec_mock.name = "some_name"
            p_spec_mock.author = "some_author"
            with mock.patch(
                "aea.protocols.generator.base.load_protocol_specification",
                return_value=p_spec_mock,
            ):
                with mock.patch(
                    "aea.protocols.generator.base.validate",
                    return_value=(True, "valid!"),
                ):
                    with mock.patch("aea.protocols.generator.base.extract"):
                        protocol_generator = ProtocolGenerator(
                            "some_path_to_protocol_specification", "some_path_to_output"
                        )
                        with self.assertRaises(ValueError) as cm:
                            protocol_generator._change_indent(-1, "s")
                            expected_msg = (
                                "Error: setting indent to be a negative number."
                            )
                            assert str(cm.exception) == expected_msg

    def test_change_indent_negative_decreasing_more_spaces_than_available(self):
        """Negative test for the '_change_indent' method: decreasing more spaces than available."""
        with mock.patch("aea.protocols.generator.base.check_prerequisites"):
            p_spec_mock = mock.MagicMock(ProtocolSpecification)
            p_spec_mock.name = "some_name"
            p_spec_mock.author = "some_author"
            with mock.patch(
                "aea.protocols.generator.base.load_protocol_specification",
                return_value=p_spec_mock,
            ):
                with mock.patch(
                    "aea.protocols.generator.base.validate",
                    return_value=(True, "valid!"),
                ):
                    with mock.patch("aea.protocols.generator.base.extract"):
                        protocol_generator = ProtocolGenerator(
                            "some_path_to_protocol_specification", "some_path_to_output"
                        )
                        protocol_generator.indent = "    "
                        with self.assertRaises(ValueError) as cm:
                            protocol_generator._change_indent(-2)
                            expected_msg = (
                                "Not enough spaces in the 'indent' variable to remove."
                            )
                            assert str(cm.exception) == expected_msg

    def test_import_from_custom_types_module_no_custom_types(self):
        """Test the '_import_from_custom_types_module' method: no custom types."""
        with mock.patch("aea.protocols.generator.base.check_prerequisites"):
            p_spec_mock = mock.MagicMock(ProtocolSpecification)
            p_spec_mock.name = "some_name"
            p_spec_mock.author = "some_author"
            with mock.patch(
                "aea.protocols.generator.base.load_protocol_specification",
                return_value=p_spec_mock,
            ):
                with mock.patch(
                    "aea.protocols.generator.base.validate",
                    return_value=(True, "valid!"),
                ):
                    with mock.patch("aea.protocols.generator.base.extract"):
                        protocol_generator = ProtocolGenerator(
                            "some_path_to_protocol_specification", "some_path_to_output"
                        )
                        protocol_generator.spec.all_custom_types = []
                        assert (
                            protocol_generator._import_from_custom_types_module() == ""
                        )

    def test_protocol_buffer_schema_str(self):
        """Negative test for the '_protocol_buffer_schema_str' method: 1 line protobuf snippet."""
        with mock.patch("aea.protocols.generator.base.check_prerequisites"):
            p_spec_mock = mock.MagicMock(ProtocolSpecification)
            p_spec_mock.name = "some_name"
            p_spec_mock.author = "some_author"
            p_spec_mock.protocol_specification_id = PublicId(
                "some_author", "some_protocol_name", "0.1.0"
            )

            with mock.patch(
                "aea.protocols.generator.base.load_protocol_specification",
                return_value=p_spec_mock,
            ):
                with mock.patch(
                    "aea.protocols.generator.base.validate",
                    return_value=(True, "valid!"),
                ):
                    with mock.patch("aea.protocols.generator.base.extract"):
                        protocol_generator = ProtocolGenerator(
                            "some_path_to_protocol_specification", "some_path_to_output"
                        )
                        protocol_generator.spec.all_custom_types = ["SomeCustomType"]
                        protocol_generator.protocol_specification.protobuf_snippets = {
                            "ct:SomeCustomType": "bytes description = 1;"
                        }
                        proto_buff_schema_str = (
                            protocol_generator._protocol_buffer_schema_str()
                        )
                        print(proto_buff_schema_str)
                        expected = (
                            'syntax = "proto3";\n\n'
                            "package aea.some_author.some_protocol_name.v0_1_0;\n\n"
                            "message SomeNameMessage{\n\n"
                            "    // Custom Types\n"
                            "    message SomeCustomType{\n"
                            "        bytes description = 1;    }\n\n\n"
                            "    // Performatives and contents\n\n"
                            "    oneof performative{\n"
                            "    }\n"
                            "}\n"
                        )
                        assert proto_buff_schema_str == expected

    def test_generate_protobuf_only_mode_positive_python(self):
        """Positive test for the 'generate_protobuf_only_mode' where language is Python."""
        protocol_generator = ProtocolGenerator(PATH_TO_T_PROTOCOL_SPECIFICATION, self.t)
        protocol_generator.generate_protobuf_only_mode()
        path_to_protobuf_schema_file = os.path.join(
            self.t, T_PROTOCOL_NAME, T_PROTOCOL_NAME + ".proto"
        )
        path_to_protobuf_python_implementation = os.path.join(
            self.t, T_PROTOCOL_NAME, T_PROTOCOL_NAME + "_pb2.py"
        )
        assert Path(path_to_protobuf_schema_file).exists()
        assert Path(path_to_protobuf_python_implementation).exists()

    def test_generate_protobuf_only_mode_positive_cpp(self):
        """Positive test for the 'generate_protobuf_only_mode' where language is C++."""
        protocol_generator = ProtocolGenerator(PATH_TO_T_PROTOCOL_SPECIFICATION, self.t)
        protocol_generator.generate_protobuf_only_mode(language="cpp")
        path_to_protobuf_schema_file = os.path.join(
            self.t, T_PROTOCOL_NAME, T_PROTOCOL_NAME + ".proto"
        )
        path_to_protobuf_cpp_headers = os.path.join(
            self.t, T_PROTOCOL_NAME, T_PROTOCOL_NAME + ".pb.h"
        )
        path_to_protobuf_cpp_implementation = os.path.join(
            self.t, T_PROTOCOL_NAME, T_PROTOCOL_NAME + ".pb.cc"
        )
        assert Path(path_to_protobuf_schema_file).exists()
        assert Path(path_to_protobuf_cpp_headers).exists()
        assert Path(path_to_protobuf_cpp_implementation).exists()

    def test_generate_protobuf_only_mode_positive_java(self):
        """Positive test for the 'generate_protobuf_only_mode' where language is Java."""
        protocol_generator = ProtocolGenerator(PATH_TO_T_PROTOCOL_SPECIFICATION, self.t)
        protocol_generator.generate_protobuf_only_mode(language="java")
        path_to_protobuf_schema_file = os.path.join(
            self.t, T_PROTOCOL_NAME, T_PROTOCOL_NAME + ".proto"
        )
        assert Path(path_to_protobuf_schema_file).exists()

        java_implementation_exists = False
        for _, _, files in os.walk(os.path.join(self.t, T_PROTOCOL_NAME)):
            for file in files:  # loops through directories and files
                if file == _to_camel_case(T_PROTOCOL_NAME) + ".java":
                    java_implementation_exists = True
                    break

        assert java_implementation_exists

    def test_generate_protobuf_only_mode_positive_csharp(self):
        """Positive test for the 'generate_protobuf_only_mode' where language is C#."""
        protocol_generator = ProtocolGenerator(PATH_TO_T_PROTOCOL_SPECIFICATION, self.t)
        protocol_generator.generate_protobuf_only_mode(language="csharp")
        path_to_protobuf_schema_file = os.path.join(
            self.t, T_PROTOCOL_NAME, T_PROTOCOL_NAME + ".proto"
        )
        path_to_protobuf_csharp_implementation = os.path.join(
            self.t, T_PROTOCOL_NAME, _to_camel_case(T_PROTOCOL_NAME) + ".cs"
        )
        assert Path(path_to_protobuf_schema_file).exists()
        assert Path(path_to_protobuf_csharp_implementation).exists()

    def test_generate_protobuf_only_mode_positive_ruby(self):
        """Positive test for the 'generate_protobuf_only_mode' where language is Ruby."""
        protocol_generator = ProtocolGenerator(PATH_TO_T_PROTOCOL_SPECIFICATION, self.t)
        protocol_generator.generate_protobuf_only_mode(language="ruby")
        path_to_protobuf_schema_file = os.path.join(
            self.t, T_PROTOCOL_NAME, T_PROTOCOL_NAME + ".proto"
        )
        path_to_protobuf_ruby_implementation = os.path.join(
            self.t, T_PROTOCOL_NAME, T_PROTOCOL_NAME + "_pb.rb"
        )
        assert Path(path_to_protobuf_schema_file).exists()
        assert Path(path_to_protobuf_ruby_implementation).exists()

    def test_generate_protobuf_only_mode_positive_objc(self):
        """Positive test for the 'generate_protobuf_only_mode' where language is objective-c."""
        protocol_generator = ProtocolGenerator(PATH_TO_T_PROTOCOL_SPECIFICATION, self.t)
        protocol_generator.generate_protobuf_only_mode(language="objc")
        path_to_protobuf_schema_file = os.path.join(
            self.t, T_PROTOCOL_NAME, T_PROTOCOL_NAME + ".proto"
        )
        path_to_protobuf_objc_headers = os.path.join(
            self.t, T_PROTOCOL_NAME, _to_camel_case(T_PROTOCOL_NAME) + ".pbobjc.h"
        )
        path_to_protobuf_objc_implementation = os.path.join(
            self.t, T_PROTOCOL_NAME, _to_camel_case(T_PROTOCOL_NAME) + ".pbobjc.m"
        )
        assert Path(path_to_protobuf_schema_file).exists()
        assert Path(path_to_protobuf_objc_headers).exists()
        assert Path(path_to_protobuf_objc_implementation).exists()

    def test_generate_protobuf_only_mode_positive_js(self):
        """Positive test for the 'generate_protobuf_only_mode' where language is JS."""
        protocol_generator = ProtocolGenerator(PATH_TO_T_PROTOCOL_SPECIFICATION, self.t)
        protocol_generator.generate_protobuf_only_mode(language="js")
        path_to_protobuf_schema_file = os.path.join(
            self.t, T_PROTOCOL_NAME, T_PROTOCOL_NAME + ".proto"
        )
        path_to_protobuf_js_implementation = os.path.join(
            self.t, T_PROTOCOL_NAME, T_PROTOCOL_NAME + "_pb.js"
        )
        assert Path(path_to_protobuf_schema_file).exists()
        assert Path(path_to_protobuf_js_implementation).exists()

    def test_generate_protobuf_only_mode_negative_incorrect_language(self):
        """Negative test for the 'generate_protobuf_only_mode' method: invalid language."""
        invalid_language = "wrong_language"
        protocol_generator = ProtocolGenerator(PATH_TO_T_PROTOCOL_SPECIFICATION, self.t)
        with self.assertRaises(ValueError) as cm:
            protocol_generator.generate_protobuf_only_mode(language=invalid_language)
            expected_msg = f"Unsupported language. Expected one of {SUPPORTED_PROTOCOL_LANGUAGES}. Found {invalid_language}."
            assert str(cm.exception) == expected_msg

    @mock.patch(
        "aea.protocols.generator.base.compile_protobuf_using_protoc",
        return_value=(False, "Some error!"),
    )
    def test_generate_protobuf_only_mode_negative_compile_fails(
        self, mocked_compile_protobuf
    ):
        """Negative test for the 'generate_protobuf_only_mode' method: compiling protobuf schema file fails"""
        protocol_generator = ProtocolGenerator(PATH_TO_T_PROTOCOL_SPECIFICATION, self.t)
        with self.assertRaises(SyntaxError) as cm:
            protocol_generator.generate_protobuf_only_mode()
            expected_msg = (
                "Error when trying to compile the protocol buffer schema file:\n"
                + "Some error!"
            )
            assert str(cm.exception) == expected_msg

        path_to_protobuf_file = os.path.join(
            self.t, T_PROTOCOL_NAME, T_PROTOCOL_NAME + ".proto"
        )
        assert not Path(path_to_protobuf_file).exists()

    @mock.patch(
        "aea.protocols.generator.base.apply_protolint",
        return_value=(False, "error line 1\nerror line 2"),
    )
    def test_generate_protobuf_only_mode_protolint_error(self, mocked_apply_protolint):
        """Positive test for the 'generate_protobuf_only_mode' where protolint has some error."""
        protocol_generator = ProtocolGenerator(PATH_TO_T_PROTOCOL_SPECIFICATION, self.t)
        output = protocol_generator.generate_protobuf_only_mode()
        expected_output = "Protolint warnings:\n" + "error line 1\nerror line 2"
        assert output == expected_output

    def test_generate_full_mode_negative_incorrect_language(self):
        """Negative test for the 'generate_protobuf_only_mode' method: invalid language."""
        invalid_language = "wrong_language"
        protocol_generator = ProtocolGenerator(PATH_TO_T_PROTOCOL_SPECIFICATION, self.t)
        with self.assertRaises(ValueError) as cm:
            protocol_generator.generate_full_mode(language=invalid_language)
            expected_msg = f"Unsupported language. Expected 'python' because currently the framework supports full generation of protocols only in Python. Found {invalid_language}."
            assert str(cm.exception) == expected_msg

    @mock.patch(
        "aea.protocols.generator.base.apply_protolint",
        return_value=(False, "error line 1\nerror line 2"),
    )
    def test_generate_full_mode_protolint_error(self, mocked_apply_protolint):
        """Positive test for the 'generate_full_mode' where protolint has some error."""
        protocol_generator = ProtocolGenerator(PATH_TO_T_PROTOCOL_SPECIFICATION, self.t)
        output = protocol_generator.generate_full_mode("python")
        expected_output = (
            "Protolint warnings:\n"
            + "error line 1\nerror line 2"
            + "The generated protocol is incomplete, because the protocol specification contains the following custom types: "
            + "{}. Update the generated '{}' file with the appropriate implementations of these custom types.".format(
                protocol_generator.spec.all_custom_types, CUSTOM_TYPES_DOT_PY_FILE_NAME
            )
        )
        assert output == expected_output

    @mock.patch(
        "aea.protocols.generator.base.ProtocolGenerator.generate_protobuf_only_mode"
    )
    @mock.patch("aea.protocols.generator.base.ProtocolGenerator.generate_full_mode")
    def test_generate_1(self, mocked_full_mode, mocked_protobuf_mode):
        """Test the 'generate' method: protobuf_only mode"""
        protocol_generator = ProtocolGenerator(PATH_TO_T_PROTOCOL_SPECIFICATION, self.t)
        protocol_generator.generate(protobuf_only=True)
        mocked_protobuf_mode.assert_called_once()
        mocked_full_mode.assert_not_called()

    @mock.patch(
        "aea.protocols.generator.base.ProtocolGenerator.generate_protobuf_only_mode"
    )
    @mock.patch("aea.protocols.generator.base.ProtocolGenerator.generate_full_mode")
    def test_generate_2(self, mocked_full_mode, mocked_protobuf_mode):
        """Test the 'generate' method: full mode"""
        protocol_generator = ProtocolGenerator(PATH_TO_T_PROTOCOL_SPECIFICATION, self.t)
        protocol_generator.generate(protobuf_only=False)
        mocked_protobuf_mode.assert_not_called()
        mocked_full_mode.assert_called_once()

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass
