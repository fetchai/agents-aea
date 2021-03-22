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
"""This module contains the tests for generator/extract_specification.py module."""
import logging
import os
import shutil
import tempfile
from unittest import TestCase

from aea.configurations.base import ProtocolSpecificationParseError
from aea.protocols.generator.common import load_protocol_specification
from aea.protocols.generator.extract_specification import (
    PythonicProtocolSpecification,
    _ct_specification_type_to_python_type,
    _mt_specification_type_to_python_type,
    _optional_specification_type_to_python_type,
    _pct_specification_type_to_python_type,
    _pmt_specification_type_to_python_type,
    _pt_specification_type_to_python_type,
    _specification_type_to_python_type,
    extract,
)

from tests.test_protocols.test_generator.common import PATH_TO_T_PROTOCOL_SPECIFICATION


logger = logging.getLogger("aea")
logging.basicConfig(level=logging.INFO)


class TestExtractSpecification(TestCase):
    """Test for generator/extract_specification.py."""

    @classmethod
    def setup_class(cls):
        """Setup class."""
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
        self.assertEqual(
            str(cm.exception), "Unsupported type: '{}'".format(specification_type_8)
        )

        specification_type_9 = "pt:integer"
        with self.assertRaises(ProtocolSpecificationParseError) as cm:
            _specification_type_to_python_type(specification_type_9)
        self.assertEqual(
            str(cm.exception), "Unsupported type: '{}'".format(specification_type_9)
        )

        specification_type_10 = "pt: list"
        with self.assertRaises(ProtocolSpecificationParseError) as cm:
            _specification_type_to_python_type(specification_type_10)
        self.assertEqual(
            str(cm.exception), "Unsupported type: '{}'".format(specification_type_10)
        )

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
        assert spec.initial_performatives == ["PERFORMATIVE_CT", "PERFORMATIVE_PT"]
        assert spec.reply == {
            "performative_ct": ["performative_pct"],
            "performative_pt": ["performative_pt", "performative_pmt"],
            "performative_pct": ["performative_mt", "performative_o"],
            "performative_pmt": ["performative_mt", "performative_o"],
            "performative_mt": [],
            "performative_o": [],
            "performative_empty_contents": ["performative_empty_contents"],
        }
        assert spec.terminal_performatives == [
            "PERFORMATIVE_MT",
            "PERFORMATIVE_O",
        ]
        assert spec.roles == ["role_1", "role_2"]
        assert spec.end_states == ["end_state_1", "end_state_2", "end_state_3"]
        assert spec.typing_imports == {
            "Set": True,
            "Tuple": True,
            "cast": True,
            "FrozenSet": True,
            "Dict": True,
            "Union": True,
            "Optional": True,
        }

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass
