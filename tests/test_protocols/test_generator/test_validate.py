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
"""This module contains the tests for generator/validate.py module."""
import logging
from unittest import TestCase

from aea.protocols.generator.validate import (
    _has_brackets,
    _is_reserved_name,
    _is_valid_ct,
    _is_valid_dict,
    _is_valid_list,
    _is_valid_pt,
    _is_valid_regex,
    _is_valid_set,
    _is_valid_union,
)

logger = logging.getLogger("aea")
logging.basicConfig(level=logging.INFO)


class TestValidate(TestCase):
    """Test for generator/validate.py."""

    def test_is_reserved_name(self):
        """Test for the '_is_reserved_name' method."""
        invalid_content_name_1 = "body"
        assert _is_reserved_name(invalid_content_name_1) is True

        invalid_content_name_2 = "message_id"
        assert _is_reserved_name(invalid_content_name_2) is True

        invalid_content_name_3 = "dialogue_reference"
        assert _is_reserved_name(invalid_content_name_3) is True

        invalid_content_name_4 = "target"
        assert _is_reserved_name(invalid_content_name_4) is True

        invalid_content_name_5 = "performative"
        assert _is_reserved_name(invalid_content_name_5) is True

        valid_content_nam_1 = "content_name"
        assert _is_reserved_name(valid_content_nam_1) is False

        valid_content_name_2 = "query"
        assert _is_reserved_name(valid_content_name_2) is False

        valid_content_name_3 = "ThiSiSAConTEnT234"
        assert _is_reserved_name(valid_content_name_3) is False

    def test_is_valid_regex(self):
        """Test for the '_is_valid_regex' method."""
        regex_1 = "^[0-9][a-zA-Z0-9]*[A-Z]$"

        valid_text_1 = "53453hKb35nDkG"
        assert _is_valid_regex(regex_1, valid_text_1) is True

        invalid_text_1 = "hKbnDkG"
        assert _is_valid_regex(regex_1, invalid_text_1) is False

        invalid_text_2 = "4f nkG"
        assert _is_valid_regex(regex_1, invalid_text_2) is False

    def test_has_brackets(self):
        """Test for the '_has_brackets' method."""
        valid_content_type_1 = "pt:set[pt:int]"
        assert _has_brackets(valid_content_type_1) is True

        valid_content_type_2 = "pt:union[hskdjf-8768&^${]hsdkjhfk]"
        assert _has_brackets(valid_content_type_2) is True

        valid_content_type_3 = "pt:optional[[]]"
        assert _has_brackets(valid_content_type_3) is True

        ###################################################

        invalid_content_type_1 = "ct:set[pt:int]"
        with self.assertRaises(SyntaxError) as cm:
            _has_brackets(invalid_content_type_1)
        self.assertEqual(
            str(cm.exception), "Content type must be a compositional type!"
        )

        invalid_content_type_2 = "pt:tuple[pt:float]"
        with self.assertRaises(SyntaxError) as cm:
            _has_brackets(invalid_content_type_2)
        self.assertEqual(
            str(cm.exception), "Content type must be a compositional type!"
        )

        invalid_content_type_3 = "pt:optinal[pt:bool]"
        with self.assertRaises(SyntaxError) as cm:
            _has_brackets(invalid_content_type_3)
        self.assertEqual(
            str(cm.exception), "Content type must be a compositional type!"
        )

        ###################################################

        invalid_content_type_4 = "pt:optional{}"
        assert _has_brackets(invalid_content_type_4) is False

        invalid_content_type_5 = "pt:set[]7657"
        assert _has_brackets(invalid_content_type_5) is False

        invalid_content_type_6 = "pt:union [pt:int, pt:bool]"
        assert _has_brackets(invalid_content_type_6) is False

        invalid_content_type_7 = "pt:dict[pt:int, pt:bool] "
        assert _has_brackets(invalid_content_type_7) is False

    def test_is_valid_ct(self):
        """Test for the '_is_valid_ct' method."""
        valid_content_type_1 = "ct:DataModel"
        assert _is_valid_ct(valid_content_type_1) is True

        valid_content_type_2 = "ct:ThisIsACustomContent"
        assert _is_valid_ct(valid_content_type_2) is True

        valid_content_type_3 = "ct:Query"
        assert _is_valid_ct(valid_content_type_3) is True

        valid_content_type_4 = "   ct:Proposal "
        assert _is_valid_ct(valid_content_type_4) is True

        valid_content_type_5 = "ct:DSA"
        assert _is_valid_ct(valid_content_type_5) is True

        valid_content_type_6 = "ct:DataF"
        assert _is_valid_ct(valid_content_type_6) is True

        ###################################################

        invalid_content_type_1 = "ct:data"
        assert _is_valid_ct(invalid_content_type_1) is False

        invalid_content_type_2 = "Model"
        assert _is_valid_ct(invalid_content_type_2) is False

        invalid_content_type_3 = "ct: DataModel"
        assert _is_valid_ct(invalid_content_type_3) is False

        invalid_content_type_4 = "ct:E3"
        assert _is_valid_ct(invalid_content_type_4) is False

    def test_is_valid_pt(self):
        """Test for the '_is_valid_pt' method."""
        valid_content_type_1 = "pt:bytes"
        assert _is_valid_pt(valid_content_type_1) is True

        valid_content_type_2 = "pt:int"
        assert _is_valid_pt(valid_content_type_2) is True

        valid_content_type_3 = "pt:float"
        assert _is_valid_pt(valid_content_type_3) is True

        valid_content_type_4 = "pt:bool"
        assert _is_valid_pt(valid_content_type_4) is True

        valid_content_type_5 = "pt:str"
        assert _is_valid_pt(valid_content_type_5) is True

        valid_content_type_6 = "  pt:int  "
        assert _is_valid_pt(valid_content_type_6) is True

        ###################################################

        invalid_content_type_1 = "pt:integer"
        assert _is_valid_pt(invalid_content_type_1) is False

        invalid_content_type_2 = "bool"
        assert _is_valid_pt(invalid_content_type_2) is False

        invalid_content_type_3 = "pt: str"
        assert _is_valid_pt(invalid_content_type_3) is False

        invalid_content_type_4 = "pt;float"
        assert _is_valid_pt(invalid_content_type_4) is False

    def test_is_valid_set(self):
        """Test for the '_is_valid_set' method."""
        valid_content_type_1 = "pt:set[pt:bytes]"
        assert _is_valid_set(valid_content_type_1) is True

        valid_content_type_2 = "pt:set[pt:int]"
        assert _is_valid_set(valid_content_type_2) is True

        valid_content_type_3 = "pt:set[pt:float]"
        assert _is_valid_set(valid_content_type_3) is True

        valid_content_type_4 = "pt:set[pt:bool]"
        assert _is_valid_set(valid_content_type_4) is True

        valid_content_type_5 = "pt:set[pt:str]"
        assert _is_valid_set(valid_content_type_5) is True

        valid_content_type_6 = " pt:set[   pt:int ]   "
        assert _is_valid_set(valid_content_type_6) is True

        ###################################################

        invalid_content_type_1 = "pt:frozenset[pt:int]"
        assert _is_valid_set(invalid_content_type_1) is False

        invalid_content_type_2 = "set[pt:int]"
        assert _is_valid_set(invalid_content_type_2) is False

        invalid_content_type_3 = "pt: set[pt:int]"
        assert _is_valid_set(invalid_content_type_3) is False

        invalid_content_type_4 = "pt:set[integer]"
        assert _is_valid_set(invalid_content_type_4) is False

        invalid_content_type_5 = "pt:set[int]"
        assert _is_valid_set(invalid_content_type_5) is False

        invalid_content_type_6 = "pt:set{int]"
        assert _is_valid_set(invalid_content_type_6) is False

        invalid_content_type_7 = "pt:set[pt:int, pt:str]"
        assert _is_valid_set(invalid_content_type_7) is False

        invalid_content_type_8 = "pt:set[]"
        assert _is_valid_set(invalid_content_type_8) is False

        invalid_content_type_9 = "pt:set[pt:list[pt:int, pt:list[pt:bool]]"
        assert _is_valid_set(invalid_content_type_9) is False

        invalid_content_type_10 = "pt:set"
        assert _is_valid_set(invalid_content_type_10) is False

    def test_is_valid_list(self):
        """Test for the '_is_valid_list' method."""
        valid_content_type_1 = "pt:list[pt:bytes]"
        assert _is_valid_list(valid_content_type_1) is True

        valid_content_type_2 = "pt:list[pt:int]"
        assert _is_valid_list(valid_content_type_2) is True

        valid_content_type_3 = "pt:list[pt:float]"
        assert _is_valid_list(valid_content_type_3) is True

        valid_content_type_4 = "pt:list[pt:bool]"
        assert _is_valid_list(valid_content_type_4) is True

        valid_content_type_5 = "pt:list[pt:str]"
        assert _is_valid_list(valid_content_type_5) is True

        valid_content_type_6 = " pt:list[   pt:bool ]   "
        assert _is_valid_list(valid_content_type_6) is True

        ###################################################

        invalid_content_type_1 = "pt:tuple[pt:bytes]"
        assert _is_valid_list(invalid_content_type_1) is False

        invalid_content_type_2 = "list[pt:bool]"
        assert _is_valid_list(invalid_content_type_2) is False

        invalid_content_type_3 = "pt: list[pt:float]"
        assert _is_valid_list(invalid_content_type_3) is False

        invalid_content_type_4 = "pt:list[string]"
        assert _is_valid_list(invalid_content_type_4) is False

        invalid_content_type_5 = "pt:list[bool]"
        assert _is_valid_list(invalid_content_type_5) is False

        invalid_content_type_6 = "pt:list[bytes"
        assert _is_valid_list(invalid_content_type_6) is False

        invalid_content_type_7 = "pt:list[pt:float, pt:bool]"
        assert _is_valid_list(invalid_content_type_7) is False

        invalid_content_type_8 = "pt:list[]"
        assert _is_valid_list(invalid_content_type_8) is False

        invalid_content_type_9 = "pt:list[pt:set[pt:bool, pt:set[pt:str]]"
        assert _is_valid_list(invalid_content_type_9) is False

        invalid_content_type_10 = "pt:list"
        assert _is_valid_list(invalid_content_type_10) is False

    def test_is_valid_dict(self):
        """Test for the '_is_valid_dict' method."""
        valid_content_type_1 = "pt:dict[pt:bytes, pt:int]"
        assert _is_valid_dict(valid_content_type_1) is True

        valid_content_type_2 = "pt:dict[pt:int, pt:int]"
        assert _is_valid_dict(valid_content_type_2) is True

        valid_content_type_3 = "pt:dict[pt:float, pt:str]"
        assert _is_valid_dict(valid_content_type_3) is True

        valid_content_type_4 = "pt:dict[pt:bool, pt:str]"
        assert _is_valid_dict(valid_content_type_4) is True

        valid_content_type_5 = "pt:dict[pt:bool,pt:float]"
        assert _is_valid_dict(valid_content_type_5) is True

        valid_content_type_6 = "   pt:dict[  pt:bytes  ,   pt:int   ] "
        assert _is_valid_dict(valid_content_type_6) is True

        ###################################################

        invalid_content_type_1 = "pt:map[pt:bool, pt:str]"
        assert _is_valid_dict(invalid_content_type_1) is False

        invalid_content_type_2 = "dict[pt:int, pt:float]"
        assert _is_valid_dict(invalid_content_type_2) is False

        invalid_content_type_3 = "pt: dict[pt:bytes, pt:bool]"
        assert _is_valid_dict(invalid_content_type_3) is False

        invalid_content_type_4 = "pt:dict[float, pt:str]"
        assert _is_valid_dict(invalid_content_type_4) is False

        invalid_content_type_5 = "pt:dict[pt:bool, pt:integer]"
        assert _is_valid_dict(invalid_content_type_5) is False

        invalid_content_type_6 = "pt:dict(pt:boolean, pt:int"
        assert _is_valid_dict(invalid_content_type_6) is False

        invalid_content_type_7 = "pt:dict[pt:boolean]"
        assert _is_valid_dict(invalid_content_type_7) is False

        invalid_content_type_8 = "pt:dict[]"
        assert _is_valid_dict(invalid_content_type_8) is False

        invalid_content_type_9 = "pt:dict[pt:str, pt:float, pt:int, pt:bytes]"
        assert _is_valid_dict(invalid_content_type_9) is False

        invalid_content_type_10 = "pt:dict[pt:set[pt:bool, pt:str]"
        assert _is_valid_dict(invalid_content_type_10) is False

        invalid_content_type_11 = "pt:dict"
        assert _is_valid_dict(invalid_content_type_11) is False

    def test_is_valid_union(self):
        """Test for the '_is_valid_union' method."""
        valid_content_type_1 = (
            "pt:union[pt:bytes, pt:int, pt:float, pt:bool, pt:str, pt:set[pt:bytes], "
            "pt:set[pt:int], pt:set[pt:float], pt:set[pt:bool], pt:set[pt:str], "
            "pt:list[pt:bytes], pt:list[pt:int], pt:list[pt:float], pt:list[pt:bool], pt:list[pt:str], "
            "pt:dict[pt:bytes, pt:bytes],    pt:dict[  pt:bytes  ,   pt:int   ]  , pt:dict[pt:bytes, pt:float], pt:dict[pt:bytes, pt:bool], pt:dict[pt:bytes, pt:str], "
            "pt:dict[pt:int, pt:bytes], pt:dict[pt:int, pt:int], pt:dict[pt:int, pt:float], pt:dict[pt:int, pt:bool], pt:dict[pt:int, pt:str], "
            "pt:dict[pt:float, pt:bytes], pt:dict[pt:float, pt:int], pt:dict[pt:float, pt:float], pt:dict[pt:float, pt:bool], pt:dict[pt:float, pt:str], "
            "pt:dict[pt:bool, pt:bytes], pt:dict[pt:bool, pt:int], pt:dict[pt:bool,pt:float], pt:dict[pt:bool, pt:bool], pt:dict[pt:bool, pt:str], "
            "pt:dict[pt:str, pt:bytes], pt:dict[pt:str, pt:int], pt:dict[pt:str,pt:float], pt:dict[pt:str, pt:bool], pt:dict[pt:str, pt:str]]"
        )
        assert _is_valid_union(valid_content_type_1) is True

        valid_content_type_2 = "pt:union[pt:bytes, pt:set[pt:int]]"
        assert _is_valid_union(valid_content_type_2) is True

        valid_content_type_3 = "pt:union[pt:float, pt:bool]"
        assert _is_valid_union(valid_content_type_3) is True

        valid_content_type_4 = "pt:union[pt:set[pt:int], pt:set[pt:float]]"
        assert _is_valid_union(valid_content_type_4) is True

        valid_content_type_5 = "pt:union[pt:bool,pt:bytes]"
        assert _is_valid_union(valid_content_type_5) is True

        valid_content_type_6 = "   pt:union[  pt:bytes  ,   pt:set[  pt:int  ]   ] "
        assert _is_valid_union(valid_content_type_6) is True

        ###################################################

        invalid_content_type_1 = "pt:onion[pt:bool, pt:str]"
        assert _is_valid_union(invalid_content_type_1) is False

        invalid_content_type_2 = "union[pt:int, pt:float]"
        assert _is_valid_union(invalid_content_type_2) is False

        invalid_content_type_3 = "pt: union[pt:set[pt:int], pt:bool]"
        assert _is_valid_union(invalid_content_type_3) is False

        invalid_content_type_4 = "pt:union[float, pt:str"
        assert _is_valid_union(invalid_content_type_4) is False

        invalid_content_type_5 = "pt:union[pt:int, pt:dict[pt:str, pt:bool]"
        assert _is_valid_union(invalid_content_type_5) is False

        invalid_content_type_6 = "pt:union{pt:boolean, pt:int]"
        assert _is_valid_union(invalid_content_type_6) is False

        invalid_content_type_7 = "pt:union[pt:boolean]"
        assert _is_valid_union(invalid_content_type_7) is False

        invalid_content_type_8 = "pt:union[]"
        assert _is_valid_union(invalid_content_type_8) is False

        invalid_content_type_9 = "pt:union[pt:str, pt:int, pt:str]"
        assert _is_valid_union(invalid_content_type_9) is False

        invalid_content_type_10 = "pt:union[pt:set[pt:integer], pt:float]"
        assert _is_valid_union(invalid_content_type_10) is False

        invalid_content_type_11 = (
            "pt:union[pt:dict[pt:set[pt:bool]], pt:list[pt:set[pt:str]]]"
        )
        assert _is_valid_union(invalid_content_type_11) is False

        invalid_content_type_12 = "pt:union"
        assert _is_valid_union(invalid_content_type_12) is False
