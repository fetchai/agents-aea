# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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
"""This module contains the tests for generator/common.py module."""
import logging
import os
import shutil
import tempfile
from pathlib import Path
from subprocess import CalledProcessError  # nosec
from unittest import TestCase, mock

from aea.protocols.generator.common import (
    _camel_case_to_snake_case,
    _create_protocol_file,
    _get_sub_types_of_compositional_types,
    _has_matched_brackets,
    _includes_custom_type,
    _match_brackets,
    _python_pt_or_ct_type_to_proto_type,
    _to_camel_case,
    _union_sub_type_to_protobuf_variable_name,
    apply_protolint,
    base_protolint_command,
    check_prerequisites,
    check_protobuf_using_protoc,
    compile_protobuf_using_protoc,
    is_installed,
    load_protocol_specification,
    try_run_black_formatting,
    try_run_isort_formatting,
    try_run_protoc,
)

from tests.test_protocols.test_generator.common import (
    PATH_TO_T_PROTOCOL_SPECIFICATION,
    T_PROTOCOL_NAME,
)


logger = logging.getLogger("aea")
logging.basicConfig(level=logging.INFO)


def isort_is_not_installed_side_effect(*args, **kwargs):
    """Isort not installed."""
    return not args[0] == "isort"


def protolint_is_not_installed_side_effect(*args, **kwargs):
    """Protolint not installed."""
    return not args[0] == "protolint"


def black_is_not_installed_side_effect(*args, **kwargs):
    """Black not installed."""
    return not args[0] == "black"


def protoc_is_not_installed_side_effect(*args, **kwargs):
    """Protoco not installed."""
    return not args[0] == "protoc"


class TestCommon(TestCase):
    """Test for generator/common.py."""

    @classmethod
    def setup_class(cls):
        """Setup test."""
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

    def test_match_brackets(
        self,
    ):
        """Positive test the '_match_brackets' method."""
        text_1 = "[so[met[hi]]ng]"
        assert _match_brackets(text_1, 0) == 14
        assert _match_brackets(text_1, 3) == 11
        assert _match_brackets(text_1, 7) == 10

        text_2 = "[]]som[]et[hi[ng][sf]"
        index_2 = 4
        with self.assertRaises(SyntaxError) as cm:
            _match_brackets(text_2, index_2)
        self.assertEqual(
            str(cm.exception),
            "Index {} in 'text' is not an open bracket '['. It is {}".format(
                index_2,
                text_2[index_2],
            ),
        )

        index_3 = 2
        with self.assertRaises(SyntaxError) as cm:
            _match_brackets(text_2, index_3)
        self.assertEqual(
            str(cm.exception),
            "Index {} in 'text' is not an open bracket '['. It is {}".format(
                index_3,
                text_2[index_3],
            ),
        )

        index_4 = 10
        with self.assertRaises(SyntaxError) as cm:
            _match_brackets(text_2, index_4)
        self.assertEqual(
            str(cm.exception),
            "No matching closing bracket ']' for the opening bracket '[' at {} "
            + str(index_4),
        )

    def test_has_matched_brackets(
        self,
    ):
        """Positive test the '_has_matched_brackets' method."""
        valid_text_1 = "[so[met[hi]]ng]"
        assert _has_matched_brackets(valid_text_1) is True

        valid_text_2 = "[[][[]]]"
        assert _has_matched_brackets(valid_text_2) is True

        valid_text_3 = "[[[[[[[]]]]]]]"
        assert _has_matched_brackets(valid_text_3) is True

        invalid_text_1 = "[]]som[]et[hi[ng][sf]"
        assert _has_matched_brackets(invalid_text_1) is False

        invalid_text_2 = "[]][][[][]"
        assert _has_matched_brackets(invalid_text_2) is False

        invalid_text_3 = "[]]"
        assert _has_matched_brackets(invalid_text_3) is False

        invalid_text_4 = "[[]"
        assert _has_matched_brackets(invalid_text_4) is False

    def test_get_sub_types_of_compositional_types_positive(
        self,
    ):
        """Positive test the '_get_sub_types_of_compositional_types' method."""
        composition_type_1 = "pt:set[pt:int, integer, bool]"
        expected_1 = ("pt:int", "integer", "bool")
        assert _get_sub_types_of_compositional_types(composition_type_1) == expected_1

        composition_type_2 = "FrozenSet[something, anotherthing]"
        expected_2 = ("something", "anotherthing")
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

        composition_type_7 = "pt:union[ct:DataModel, pt:bytes, pt:int, pt:bool, pt:float, pt:str, pt:set[pt:int], pt:list[pt:bool], pt:dict[pt:str,pt:str]]"
        expected_7 = (
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
        assert _get_sub_types_of_compositional_types(composition_type_7) == expected_7

        composition_type_8 = "Union[int, Tuple[bool, ...]]"
        expected_8 = ("int", "Tuple[bool, ...]")
        assert _get_sub_types_of_compositional_types(composition_type_8) == expected_8

        composition_type_9 = (
            "Union[DataModel, FrozenSet[int], Tuple[bool, ...], bytes, Dict[bool,float], int, "
            "FrozenSet[bool], Dict[int, str], Tuple[str, ...], bool, float, str, Dict[str, str]]"
        )
        expected_9 = (
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
        assert _get_sub_types_of_compositional_types(composition_type_9) == expected_9

        composition_type_10 = "pt:optional[pt:union[ct:DataModel, pt:bytes, pt:int, pt:bool, pt:float, pt:str, pt:set[pt:int], pt:list[pt:bool], pt:dict[pt:str,pt:str]]]"
        expected_10 = (
            "pt:union[ct:DataModel, pt:bytes, pt:int, pt:bool, pt:float, pt:str, pt:set[pt:int], pt:list[pt:bool], pt:dict[pt:str,pt:str]]",
        )
        assert _get_sub_types_of_compositional_types(composition_type_10) == expected_10

        composition_type_11 = "Optional[Union[DataModel, bytes, int, bool, float, str, FrozenSet[int], Tuple[bool, ...], Dict[str,str]]]"
        expected_11 = (
            "Union[DataModel, bytes, int, bool, float, str, FrozenSet[int], Tuple[bool, ...], Dict[str,str]]",
        )
        assert _get_sub_types_of_compositional_types(composition_type_11) == expected_11

    def test_get_sub_types_of_compositional_types_negative(
        self,
    ):
        """Negative test the '_get_sub_types_of_compositional_types' method"""
        composition_type_1 = "pt:int"
        with self.assertRaises(SyntaxError) as cm:
            _get_sub_types_of_compositional_types(composition_type_1)
        self.assertEqual(
            str(cm.exception),
            "{} is not a valid compositional type.".format(composition_type_1),
        )

        composition_type_2 = "pt:int[pt:DataModel]"
        with self.assertRaises(SyntaxError) as cm:
            _get_sub_types_of_compositional_types(composition_type_2)
        self.assertEqual(
            str(cm.exception),
            "{} is not a valid compositional type.".format(composition_type_2),
        )

        composition_type_3 = "pt:dict[pt:set[int, pt:list[pt:bool]]"
        with self.assertRaises(SyntaxError) as cm:
            _get_sub_types_of_compositional_types(composition_type_3)
        self.assertEqual(
            str(cm.exception),
            "Bad formatting. No matching close bracket ']' for the open bracket at pt:set[",
        )

    def test_union_sub_type_to_protobuf_variable_name(
        self,
    ):
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

    def test_python_pt_or_ct_type_to_proto_type(
        self,
    ):
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

    def test_includes_custom_type(
        self,
    ):
        """Test the '_includes_custom_type' method"""
        content_type_includes_1 = "Optional[DataModel]"
        assert _includes_custom_type(content_type_includes_1) is True

        content_type_includes_2 = "Union[int, DataModel]"
        assert _includes_custom_type(content_type_includes_2) is True

        content_type_includes_3 = "Optional[Union[int, float, DataModel, Query, float]]"
        assert _includes_custom_type(content_type_includes_3) is True

        content_type_not_includes_1 = "Optional[int]"
        assert _includes_custom_type(content_type_not_includes_1) is False

        content_type_not_includes_2 = "Union[int, float, str]"
        assert _includes_custom_type(content_type_not_includes_2) is False

        content_type_not_includes_3 = (
            "Optional[Union[int, float, FrozenSet[int], Tuple[bool, ...], float]]"
        )
        assert _includes_custom_type(content_type_not_includes_3) is False

    @mock.patch("shutil.which", return_value="some string")
    def test_is_installed_positive(self, mocked_shutil_which):
        """Positive test for the 'is_installed' method"""
        assert is_installed("some_programme") is True

    @mock.patch("shutil.which", return_value=None)
    def test_is_installed_negative(self, mocked_shutil_which):
        """Negative test for the 'is_installed' method: programme is not installed"""
        assert is_installed("some_programme") is False

    def test_base_protolint_command(self):
        """Tests the 'base_protolint_command' method"""
        assert (
            base_protolint_command() == "protolint"
            or "PATH=${PATH}:${GOPATH}/bin/:~/go/bin protolint"
        )

    @mock.patch("aea.protocols.generator.common.is_installed", return_value=True)
    def test_check_prerequisites_positive(self, mocked_is_installed):
        """Positive test for the 'check_prerequisites' method"""
        try:
            check_prerequisites()
        except FileNotFoundError:
            self.assertTrue(False)

    @mock.patch(
        "aea.protocols.generator.common.is_installed",
        side_effect=black_is_not_installed_side_effect,
    )
    def test_check_prerequisites_negative_black_is_not_installed(
        self, mocked_is_installed
    ):
        """Negative test for the 'check_prerequisites' method: black isn't installed"""
        with self.assertRaises(FileNotFoundError):
            check_prerequisites()

    @mock.patch(
        "aea.protocols.generator.common.is_installed",
        side_effect=isort_is_not_installed_side_effect,
    )
    def test_check_prerequisites_negative_isort_is_not_installed(
        self, mocked_is_installed
    ):
        """Negative test for the 'check_prerequisites' method: isort isn't installed"""
        with self.assertRaises(FileNotFoundError):
            check_prerequisites()

    @mock.patch(
        "aea.protocols.generator.common.subprocess.call",
        return_value=1,
    )
    def test_check_prerequisites_negative_protolint_is_not_installed(
        self, mocked_is_installed
    ):
        """Negative test for the 'check_prerequisites' method: protolint isn't installed"""
        with self.assertRaises(FileNotFoundError):
            check_prerequisites()

    @mock.patch(
        "aea.protocols.generator.common.is_installed",
        side_effect=protoc_is_not_installed_side_effect,
    )
    def test_check_prerequisites_negative_protoc_is_not_installed(
        self, mocked_is_installed
    ):
        """Negative test for the 'check_prerequisites' method: protoc isn't installed"""
        with self.assertRaises(FileNotFoundError):
            check_prerequisites()

    def test_load_protocol_specification(
        self,
    ):
        """Test the 'load_protocol_specification' method"""
        spec = load_protocol_specification(PATH_TO_T_PROTOCOL_SPECIFICATION)
        assert spec.name == T_PROTOCOL_NAME
        assert spec.version == "0.1.0"
        assert spec.author == "fetchai"
        assert spec.license == "Apache-2.0"
        assert spec.aea_version == ">=1.0.0, <2.0.0"
        assert spec.description == "A protocol for testing purposes."
        assert spec.speech_acts is not None
        assert spec.protobuf_snippets is not None and spec.protobuf_snippets != ""

    def test_create_protocol_file(
        self,
    ):
        """Test the '_create_protocol_file' method"""
        file_name = "temp_file"
        file_content = "this is a temporary file"

        _create_protocol_file(self.t, file_name, file_content)
        path_to_the_file = os.path.join(self.t, file_name)

        assert Path(path_to_the_file).exists()
        assert Path(path_to_the_file).read_text() == file_content

    @mock.patch("subprocess.run")
    def test_try_run_black_formatting(self, mocked_subprocess):
        """Test the 'try_run_black_formatting' method"""
        try_run_black_formatting("some_path")
        mocked_subprocess.assert_called_once()

    @mock.patch("subprocess.run")
    def test_try_run_isort_formatting(self, mocked_subprocess):
        """Test the 'try_run_isort_formatting' method"""
        try_run_isort_formatting("some_path")
        mocked_subprocess.assert_called_once()

    @mock.patch("subprocess.run")
    def test_try_run_protoc(self, mocked_subprocess):
        """Test the 'try_run_protoc' method"""
        try_run_protoc("some_path", "some_name")
        mocked_subprocess.assert_called_once()

    @mock.patch("subprocess.run")
    def test_try_run_protolint(self, mocked_subprocess):
        """Test the 'try_run_protolint' method"""
        try_run_protoc("some_path", "some_name")
        mocked_subprocess.assert_called_once()

    @mock.patch("aea.protocols.generator.common.try_run_protoc")
    def test_check_protobuf_using_protoc_positive(self, mocked_try_run_protoc):
        """Positive test for the 'check_protobuf_using_protoc' method"""
        protocol_name = "protocol_name"
        file_name = protocol_name + "_pb2.py"

        new_file = open(os.path.join(self.t, file_name), "w+")
        new_file.close()
        result, msg = check_protobuf_using_protoc(self.t, protocol_name)

        assert not Path(self.t, file_name).exists()
        assert result is True
        assert msg == "protobuf file is valid"

    @mock.patch(
        "subprocess.run",
        side_effect=CalledProcessError(
            1, "some_command", stderr="name.proto:12:45: some_protoc_error\n"
        ),
    )
    def test_check_protobuf_using_protoc_nagative(self, mocked_subprocess):
        """Negative test for the 'check_protobuf_using_protoc' method: protoc has some errors"""
        result, msg = check_protobuf_using_protoc("some_path", "name")
        assert result is False
        assert msg == "some_protoc_error"

    @mock.patch("aea.protocols.generator.common.try_run_protoc")
    def test_compile_protobuf_using_protoc_positive(self, mocked_try_run_protoc):
        """Positive test for the 'compile_protobuf_using_protoc' method"""
        protocol_name = "protocol_name"

        result, msg = compile_protobuf_using_protoc(self.t, protocol_name, "python")

        mocked_try_run_protoc.assert_called_once()
        assert result is True
        assert msg == "protobuf schema successfully compiled"

    @mock.patch(
        "subprocess.run",
        side_effect=CalledProcessError(
            1, "some_command", stderr="protocol_name.proto:12:45: some_protoc_error\n"
        ),
    )
    def test_compile_protobuf_using_protoc_nagative(self, mocked_subprocess):
        """Negative test for the 'check_protobuf_using_protoc' method: protoc has some errors"""
        protocol_name = "protocol_name"
        result, msg = compile_protobuf_using_protoc(self.t, protocol_name, "python")
        assert result is False
        assert msg == "some_protoc_error"

    @mock.patch("aea.protocols.generator.common.try_run_protolint")
    def test_apply_protolint_positive(self, mocked_try_run_protoc):
        """Positive test for the 'apply_protolint' method"""
        protocol_name = "protocol_name"

        result, msg = apply_protolint(self.t, protocol_name)

        mocked_try_run_protoc.assert_called_once()
        assert result is True
        assert msg == "protolint has no output"

    @mock.patch(
        "subprocess.run",
        side_effect=CalledProcessError(
            1,
            "some_command",
            stderr="protocol_name.proto:12:45: some_protoc_error\nprotocol_name.proto:12:45: incorrect indentation style ...",
        ),
    )
    def test_apply_protolint_nagative(self, mocked_subprocess):
        """Negative test for the 'apply_protolint' method: protoc has some errors"""
        protocol_name = "protocol_name"
        result, msg = apply_protolint(self.t, protocol_name)
        assert result is False
        assert msg == "protocol_name.proto:12:45: some_protoc_error"

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass
