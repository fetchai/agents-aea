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
from unittest import TestCase, mock

from aea.configurations.base import CRUDCollection, SpeechActContentConfig
from aea.protocols.generator.validate import (
    CONTENT_NAME_REGEX_PATTERN,
    END_STATE_REGEX_PATTERN,
    PERFORMATIVE_REGEX_PATTERN,
    ROLE_REGEX_PATTERN,
    _has_brackets,
    _is_reserved_name,
    _is_valid_content_type_format,
    _is_valid_ct,
    _is_valid_dict,
    _is_valid_list,
    _is_valid_optional,
    _is_valid_pt,
    _is_valid_regex,
    _is_valid_set,
    _is_valid_union,
    _validate_content_name,
    _validate_content_type,
    _validate_dialogue_section,
    _validate_end_states,
    _validate_field_existence,
    _validate_initiation,
    _validate_keep_terminal,
    _validate_performatives,
    _validate_protocol_buffer_schema_code_snippets,
    _validate_reply,
    _validate_roles,
    _validate_speech_acts_section,
    _validate_termination,
    validate,
)


logger = logging.getLogger("aea")
logging.basicConfig(level=logging.INFO)


class TestValidate(TestCase):
    """Test for generator/validate.py."""

    def test_is_reserved_name(self):
        """Test for the '_is_reserved_name' method."""
        invalid_content_name_1 = "_body"
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

    def test_is_valid_optional(self):
        """Test for the '_is_valid_optional' method."""
        valid_content_type_1 = (
            "pt:optional[pt:union[pt:bytes, pt:int, pt:float, pt:bool, pt:str, pt:set[pt:bytes], "
            "pt:set[pt:int], pt:set[pt:float], pt:set[pt:bool], pt:set[pt:str], "
            "pt:list[pt:bytes], pt:list[pt:int], pt:list[pt:float], pt:list[pt:bool], pt:list[pt:str], "
            "pt:dict[pt:bytes, pt:bytes],    pt:dict[  pt:bytes  ,   pt:int   ]  , pt:dict[pt:bytes, pt:float], pt:dict[pt:bytes, pt:bool], pt:dict[pt:bytes, pt:str], "
            "pt:dict[pt:int, pt:bytes], pt:dict[pt:int, pt:int], pt:dict[pt:int, pt:float], pt:dict[pt:int, pt:bool], pt:dict[pt:int, pt:str], "
            "pt:dict[pt:float, pt:bytes], pt:dict[pt:float, pt:int], pt:dict[pt:float, pt:float], pt:dict[pt:float, pt:bool], pt:dict[pt:float, pt:str], "
            "pt:dict[pt:bool, pt:bytes], pt:dict[pt:bool, pt:int], pt:dict[pt:bool,pt:float], pt:dict[pt:bool, pt:bool], pt:dict[pt:bool, pt:str], "
            "pt:dict[pt:str, pt:bytes], pt:dict[pt:str, pt:int], pt:dict[pt:str,pt:float], pt:dict[pt:str, pt:bool], pt:dict[pt:str, pt:str]]]"
        )
        assert _is_valid_optional(valid_content_type_1) is True

        valid_content_type_2 = "pt:optional[pt:union[pt:bytes, pt:set[pt:int]]]"
        assert _is_valid_optional(valid_content_type_2) is True

        valid_content_type_3 = "pt:optional[pt:bytes]"
        assert _is_valid_optional(valid_content_type_3) is True

        valid_content_type_4 = "pt:optional[pt:int]"
        assert _is_valid_optional(valid_content_type_4) is True

        valid_content_type_5 = "pt:optional[pt:float]"
        assert _is_valid_optional(valid_content_type_5) is True

        valid_content_type_6 = "pt:optional[pt:bool]"
        assert _is_valid_optional(valid_content_type_6) is True

        valid_content_type_7 = "pt:optional[pt:str]"
        assert _is_valid_optional(valid_content_type_7) is True

        valid_content_type_8 = "pt:optional[pt:set[pt:bytes]]"
        assert _is_valid_optional(valid_content_type_8) is True

        valid_content_type_9 = "pt:optional[pt:list[pt:int]]"
        assert _is_valid_optional(valid_content_type_9) is True

        valid_content_type_10 = (
            "     pt:optional[  pt:dict[   pt:float   ,  pt:bool ]   ] "
        )
        assert _is_valid_optional(valid_content_type_10) is True

        ###################################################

        invalid_content_type_1 = "pt:optinal[pt:bytes]"
        assert _is_valid_optional(invalid_content_type_1) is False

        invalid_content_type_2 = "optional[pt:int]"
        assert _is_valid_optional(invalid_content_type_2) is False

        invalid_content_type_3 = "pt: optional[pt:float]"
        assert _is_valid_optional(invalid_content_type_3) is False

        invalid_content_type_4 = "pt:optional[bool]"
        assert _is_valid_optional(invalid_content_type_4) is False

        invalid_content_type_5 = "pt:optional[pt:str"
        assert _is_valid_optional(invalid_content_type_5) is False

        invalid_content_type_6 = "pt:optional{pt:set[pt:int]]"
        assert _is_valid_optional(invalid_content_type_6) is False

        invalid_content_type_7 = "pt:optional[pt:string]"
        assert _is_valid_optional(invalid_content_type_7) is False

        invalid_content_type_8 = "pt:optional[]"
        assert _is_valid_optional(invalid_content_type_8) is False

        invalid_content_type_9 = "pt:optional[pt:str, pt:int, pt:list[pt:bool]]"
        assert _is_valid_optional(invalid_content_type_9) is False

        invalid_content_type_10 = "pt:optional[pt:list[pt:boolean]]"
        assert _is_valid_optional(invalid_content_type_10) is False

        invalid_content_type_11 = "pt:optional[pt:dict[pt:set[pt:int]]]"
        assert _is_valid_optional(invalid_content_type_11) is False

        invalid_content_type_12 = "pt:optional"
        assert _is_valid_optional(invalid_content_type_12) is False

    def test_is_valid_content_type_format(self):
        """Test for the '_is_valid_content_type_format' method."""
        valid_content_type_1 = "ct:DataModel"
        assert _is_valid_content_type_format(valid_content_type_1) is True

        valid_content_type_2 = "pt:int"
        assert _is_valid_content_type_format(valid_content_type_2) is True

        valid_content_type_3 = "pt:set[pt:float]"
        assert _is_valid_content_type_format(valid_content_type_3) is True

        valid_content_type_4 = "pt:list[pt:bool]"
        assert _is_valid_content_type_format(valid_content_type_4) is True

        valid_content_type_5 = "pt:dict[pt:bool,pt:float]"
        assert _is_valid_content_type_format(valid_content_type_5) is True

        valid_content_type_6 = (
            "pt:optional[pt:union[pt:bytes, pt:int, pt:float, pt:bool, pt:str, pt:set[pt:bytes], "
            "pt:set[pt:int], pt:set[pt:float], pt:set[pt:bool], pt:set[pt:str], "
            "pt:list[pt:bytes], pt:list[pt:int], pt:list[pt:float], pt:list[pt:bool], pt:list[pt:str], "
            "pt:dict[pt:bytes, pt:bytes],    pt:dict[  pt:bytes  ,   pt:int   ]  , pt:dict[pt:bytes, pt:float], pt:dict[pt:bytes, pt:bool], pt:dict[pt:bytes, pt:str], "
            "pt:dict[pt:int, pt:bytes], pt:dict[pt:int, pt:int], pt:dict[pt:int, pt:float], pt:dict[pt:int, pt:bool], pt:dict[pt:int, pt:str], "
            "pt:dict[pt:float, pt:bytes], pt:dict[pt:float, pt:int], pt:dict[pt:float, pt:float], pt:dict[pt:float, pt:bool], pt:dict[pt:float, pt:str], "
            "pt:dict[pt:bool, pt:bytes], pt:dict[pt:bool, pt:int], pt:dict[pt:bool,pt:float], pt:dict[pt:bool, pt:bool], pt:dict[pt:bool, pt:str], "
            "pt:dict[pt:str, pt:bytes], pt:dict[pt:str, pt:int], pt:dict[pt:str,pt:float], pt:dict[pt:str, pt:bool], pt:dict[pt:str, pt:str]]]"
        )
        assert _is_valid_content_type_format(valid_content_type_6) is True

        valid_content_type_7 = (
            "     pt:optional[  pt:dict[   pt:float   ,  pt:bool ]   ] "
        )
        assert _is_valid_content_type_format(valid_content_type_7) is True

        ###################################################

        invalid_content_type_1 = "ct:data"
        assert _is_valid_content_type_format(invalid_content_type_1) is False

        invalid_content_type_2 = "bool"
        assert _is_valid_content_type_format(invalid_content_type_2) is False

        invalid_content_type_3 = "pt: set[pt:int]"
        assert _is_valid_content_type_format(invalid_content_type_3) is False

        invalid_content_type_4 = "pt:list[string]"
        assert _is_valid_content_type_format(invalid_content_type_4) is False

        invalid_content_type_5 = "pt:dict[pt:bool, pt:integer]"
        assert _is_valid_content_type_format(invalid_content_type_5) is False

        invalid_content_type_6 = "pt:union{pt:boolean, pt:int]"
        assert _is_valid_content_type_format(invalid_content_type_6) is False

        invalid_content_type_7 = "pt:optional[pt:str, pt:int, pt:list[pt:bool]]"
        assert _is_valid_content_type_format(invalid_content_type_7) is False

    def test_validate_performatives(self):
        """Test for the '_validate_performatives' method."""
        valid_content_type_1 = "offer"
        valid_result_1, valid_msg_1 = _validate_performatives(valid_content_type_1)
        assert valid_result_1 is True
        assert valid_msg_1 == "Performative '{}' is valid.".format(valid_content_type_1)

        valid_content_type_2 = "send_HTTP_message"
        valid_result_2, valid_msg_2 = _validate_performatives(valid_content_type_2)
        assert valid_result_2 is True
        assert valid_msg_2 == "Performative '{}' is valid.".format(valid_content_type_2)

        valid_content_type_3 = "request_2PL"
        valid_result_3, valid_msg_3 = _validate_performatives(valid_content_type_3)
        assert valid_result_3 is True
        assert valid_msg_3 == "Performative '{}' is valid.".format(valid_content_type_3)

        valid_content_type_4 = "argue"
        valid_result_4, valid_msg_4 = _validate_performatives(valid_content_type_4)
        assert valid_result_4 is True
        assert valid_msg_4 == "Performative '{}' is valid.".format(valid_content_type_4)

        ###################################################

        invalid_content_type_1 = "_offer"
        invalid_result_1, invalid_msg_1 = _validate_performatives(
            invalid_content_type_1
        )
        assert invalid_result_1 is False
        assert (
            invalid_msg_1
            == "Invalid name for performative '{}'. Performative names must match the following regular expression: {} ".format(
                invalid_content_type_1, PERFORMATIVE_REGEX_PATTERN
            )
        )

        invalid_content_type_2 = "request_"
        invalid_result_2, invalid_msg_2 = _validate_performatives(
            invalid_content_type_2
        )
        assert invalid_result_2 is False
        assert (
            invalid_msg_2
            == "Invalid name for performative '{}'. Performative names must match the following regular expression: {} ".format(
                invalid_content_type_2, PERFORMATIVE_REGEX_PATTERN
            )
        )

        invalid_content_type_3 = "_query_"
        invalid_result_3, invalid_msg_3 = _validate_performatives(
            invalid_content_type_3
        )
        assert invalid_result_3 is False
        assert (
            invalid_msg_3
            == "Invalid name for performative '{}'. Performative names must match the following regular expression: {} ".format(
                invalid_content_type_3, PERFORMATIVE_REGEX_PATTERN
            )
        )

        invalid_content_type_4 = "$end"
        invalid_result_4, invalid_msg_4 = _validate_performatives(
            invalid_content_type_4
        )
        assert invalid_result_4 is False
        assert (
            invalid_msg_4
            == "Invalid name for performative '{}'. Performative names must match the following regular expression: {} ".format(
                invalid_content_type_4, PERFORMATIVE_REGEX_PATTERN
            )
        )

        invalid_content_type_5 = "create()"
        invalid_result_5, invalid_msg_5 = _validate_performatives(
            invalid_content_type_5
        )
        assert invalid_result_5 is False
        assert (
            invalid_msg_5
            == "Invalid name for performative '{}'. Performative names must match the following regular expression: {} ".format(
                invalid_content_type_5, PERFORMATIVE_REGEX_PATTERN
            )
        )

        invalid_content_type_6 = "_body"
        invalid_result_6, invalid_msg_6 = _validate_performatives(
            invalid_content_type_6
        )
        assert invalid_result_6 is False
        assert (
            invalid_msg_6
            == "Invalid name for performative '{}'. This name is reserved.".format(
                invalid_content_type_6,
            )
        )

        invalid_content_type_7 = "message_id"
        invalid_result_7, invalid_msg_7 = _validate_performatives(
            invalid_content_type_7
        )
        assert invalid_result_7 is False
        assert (
            invalid_msg_6
            == "Invalid name for performative '{}'. This name is reserved.".format(
                invalid_content_type_6,
            )
        )

    def test_validate_content_name(self):
        """Test for the '_validate_content_name' method."""
        performative = "some_performative"

        valid_content_type_1 = "content"
        valid_result_1, valid_msg_1 = _validate_content_name(
            valid_content_type_1, performative
        )
        assert valid_result_1 is True
        assert valid_msg_1 == "Content name '{}' of performative '{}' is valid.".format(
            valid_content_type_1, performative
        )

        valid_content_type_2 = "HTTP_msg_name"
        valid_result_2, valid_msg_2 = _validate_content_name(
            valid_content_type_2, performative
        )
        assert valid_result_2 is True
        assert valid_msg_2 == "Content name '{}' of performative '{}' is valid.".format(
            valid_content_type_2, performative
        )

        valid_content_type_3 = "number_of_3PLs"
        valid_result_3, valid_msg_3 = _validate_content_name(
            valid_content_type_3, performative
        )
        assert valid_result_3 is True
        assert valid_msg_3 == "Content name '{}' of performative '{}' is valid.".format(
            valid_content_type_3, performative
        )

        valid_content_type_4 = "model"
        valid_result_4, valid_msg_4 = _validate_content_name(
            valid_content_type_4, performative
        )
        assert valid_result_4 is True
        assert valid_msg_4 == "Content name '{}' of performative '{}' is valid.".format(
            valid_content_type_4, performative
        )

        ###################################################

        invalid_content_type_1 = "_content"
        invalid_result_1, invalid_msg_1 = _validate_content_name(
            invalid_content_type_1, performative
        )
        assert invalid_result_1 is False
        assert (
            invalid_msg_1
            == "Invalid name for content '{}' of performative '{}'. Content names must match the following regular expression: {} ".format(
                invalid_content_type_1, performative, CONTENT_NAME_REGEX_PATTERN
            )
        )

        invalid_content_type_2 = "content_"
        invalid_result_2, invalid_msg_2 = _validate_content_name(
            invalid_content_type_2, performative
        )
        assert invalid_result_2 is False
        assert (
            invalid_msg_2
            == "Invalid name for content '{}' of performative '{}'. Content names must match the following regular expression: {} ".format(
                invalid_content_type_2, performative, CONTENT_NAME_REGEX_PATTERN
            )
        )

        invalid_content_type_3 = "_content_"
        invalid_result_3, invalid_msg_3 = _validate_content_name(
            invalid_content_type_3, performative
        )
        assert invalid_result_3 is False
        assert (
            invalid_msg_3
            == "Invalid name for content '{}' of performative '{}'. Content names must match the following regular expression: {} ".format(
                invalid_content_type_3, performative, CONTENT_NAME_REGEX_PATTERN
            )
        )

        invalid_content_type_4 = "con^en^"
        invalid_result_4, invalid_msg_4 = _validate_content_name(
            invalid_content_type_4, performative
        )
        assert invalid_result_4 is False
        assert (
            invalid_msg_4
            == "Invalid name for content '{}' of performative '{}'. Content names must match the following regular expression: {} ".format(
                invalid_content_type_4, performative, CONTENT_NAME_REGEX_PATTERN
            )
        )

        invalid_content_type_5 = "some_content()"
        invalid_result_5, invalid_msg_5 = _validate_content_name(
            invalid_content_type_5, performative
        )
        assert invalid_result_5 is False
        assert (
            invalid_msg_5
            == "Invalid name for content '{}' of performative '{}'. Content names must match the following regular expression: {} ".format(
                invalid_content_type_5, performative, CONTENT_NAME_REGEX_PATTERN
            )
        )

        invalid_content_type_6 = "target"
        invalid_result_6, invalid_msg_6 = _validate_content_name(
            invalid_content_type_6, performative
        )
        assert invalid_result_6 is False
        assert (
            invalid_msg_6
            == "Invalid name for content '{}' of performative '{}'. This name is reserved.".format(
                invalid_content_type_6, performative,
            )
        )

        invalid_content_type_7 = "performative"
        invalid_result_7, invalid_msg_7 = _validate_content_name(
            invalid_content_type_7, performative
        )
        assert invalid_result_7 is False
        assert (
            invalid_msg_7
            == "Invalid name for content '{}' of performative '{}'. This name is reserved.".format(
                invalid_content_type_7, performative,
            )
        )

    def test_validate_content_type(self):
        """Test for the '_validate_content_type' method."""
        performative = "some_performative"
        content_name = "some_content_name"

        valid_content_type_1 = "ct:DataModel"
        valid_result_1, valid_msg_1 = _validate_content_type(
            valid_content_type_1, content_name, performative
        )
        assert valid_result_1 is True
        assert (
            valid_msg_1
            == "Type of content '{}' of performative '{}' is valid.".format(
                content_name, performative
            )
        )

        valid_content_type_2 = "pt:int"
        valid_result_2, valid_msg_2 = _validate_content_type(
            valid_content_type_2, content_name, performative
        )
        assert valid_result_2 is True
        assert (
            valid_msg_2
            == "Type of content '{}' of performative '{}' is valid.".format(
                content_name, performative
            )
        )

        valid_content_type_3 = "pt:set[pt:float]"
        valid_result_3, valid_msg_3 = _validate_content_type(
            valid_content_type_3, content_name, performative
        )
        assert valid_result_3 is True
        assert (
            valid_msg_3
            == "Type of content '{}' of performative '{}' is valid.".format(
                content_name, performative
            )
        )

        valid_content_type_4 = "pt:list[pt:bool]"
        valid_result_4, valid_msg_4 = _validate_content_type(
            valid_content_type_4, content_name, performative
        )
        assert valid_result_4 is True
        assert (
            valid_msg_4
            == "Type of content '{}' of performative '{}' is valid.".format(
                content_name, performative
            )
        )

        valid_content_type_5 = "pt:dict[pt:bool,pt:float]"
        valid_result_5, valid_msg_5 = _validate_content_type(
            valid_content_type_5, content_name, performative
        )
        assert valid_result_5 is True
        assert (
            valid_msg_5
            == "Type of content '{}' of performative '{}' is valid.".format(
                content_name, performative
            )
        )

        valid_content_type_6 = (
            "pt:optional[pt:union[pt:bytes, pt:int, pt:float, pt:bool, pt:str, pt:set[pt:bytes], "
            "pt:set[pt:int], pt:set[pt:float], pt:set[pt:bool], pt:set[pt:str], "
            "pt:list[pt:bytes], pt:list[pt:int], pt:list[pt:float], pt:list[pt:bool], pt:list[pt:str], "
            "pt:dict[pt:bytes, pt:bytes],    pt:dict[  pt:bytes  ,   pt:int   ]  , pt:dict[pt:bytes, pt:float], pt:dict[pt:bytes, pt:bool], pt:dict[pt:bytes, pt:str], "
            "pt:dict[pt:int, pt:bytes], pt:dict[pt:int, pt:int], pt:dict[pt:int, pt:float], pt:dict[pt:int, pt:bool], pt:dict[pt:int, pt:str], "
            "pt:dict[pt:float, pt:bytes], pt:dict[pt:float, pt:int], pt:dict[pt:float, pt:float], pt:dict[pt:float, pt:bool], pt:dict[pt:float, pt:str], "
            "pt:dict[pt:bool, pt:bytes], pt:dict[pt:bool, pt:int], pt:dict[pt:bool,pt:float], pt:dict[pt:bool, pt:bool], pt:dict[pt:bool, pt:str], "
            "pt:dict[pt:str, pt:bytes], pt:dict[pt:str, pt:int], pt:dict[pt:str,pt:float], pt:dict[pt:str, pt:bool], pt:dict[pt:str, pt:str]]]"
        )
        valid_result_6, valid_msg_6 = _validate_content_type(
            valid_content_type_6, content_name, performative
        )
        assert valid_result_6 is True
        assert (
            valid_msg_6
            == "Type of content '{}' of performative '{}' is valid.".format(
                content_name, performative
            )
        )

        valid_content_type_7 = (
            "     pt:optional[  pt:dict[   pt:float   ,  pt:bool ]   ] "
        )
        valid_result_7, valid_msg_7 = _validate_content_type(
            valid_content_type_7, content_name, performative
        )
        assert valid_result_7 is True
        assert (
            valid_msg_7
            == "Type of content '{}' of performative '{}' is valid.".format(
                content_name, performative
            )
        )

        ###################################################

        invalid_content_type_1 = "ct:data"
        invalid_result_1, invalid_msg_1 = _validate_content_type(
            invalid_content_type_1, content_name, performative
        )
        assert invalid_result_1 is False
        assert (
            invalid_msg_1
            == "Invalid type for content '{}' of performative '{}'. See documentation for the correct format of specification types.".format(
                content_name, performative,
            )
        )

        invalid_content_type_2 = "bool"
        invalid_result_2, invalid_msg_2 = _validate_content_type(
            invalid_content_type_2, content_name, performative
        )
        assert invalid_result_2 is False
        assert (
            invalid_msg_2
            == "Invalid type for content '{}' of performative '{}'. See documentation for the correct format of specification types.".format(
                content_name, performative,
            )
        )

        invalid_content_type_3 = "pt: set[pt:int]"
        invalid_result_3, invalid_msg_3 = _validate_content_type(
            invalid_content_type_3, content_name, performative
        )
        assert invalid_result_3 is False
        assert (
            invalid_msg_3
            == "Invalid type for content '{}' of performative '{}'. See documentation for the correct format of specification types.".format(
                content_name, performative,
            )
        )

        invalid_content_type_4 = "pt:list[string]"
        invalid_result_4, invalid_msg_4 = _validate_content_type(
            invalid_content_type_4, content_name, performative
        )
        assert invalid_result_4 is False
        assert (
            invalid_msg_4
            == "Invalid type for content '{}' of performative '{}'. See documentation for the correct format of specification types.".format(
                content_name, performative,
            )
        )

        invalid_content_type_5 = "pt:dict[pt:bool, pt:integer]"
        invalid_result_5, invalid_msg_5 = _validate_content_type(
            invalid_content_type_5, content_name, performative
        )
        assert invalid_result_5 is False
        assert (
            invalid_msg_5
            == "Invalid type for content '{}' of performative '{}'. See documentation for the correct format of specification types.".format(
                content_name, performative,
            )
        )

        invalid_content_type_6 = "pt:union{pt:boolean, pt:int]"
        invalid_result_6, invalid_msg_6 = _validate_content_type(
            invalid_content_type_6, content_name, performative
        )
        assert invalid_result_6 is False
        assert (
            invalid_msg_6
            == "Invalid type for content '{}' of performative '{}'. See documentation for the correct format of specification types.".format(
                content_name, performative,
            )
        )

        invalid_content_type_7 = "pt:optional[pt:str, pt:int, pt:list[pt:bool]]"
        invalid_result_7, invalid_msg_7 = _validate_content_type(
            invalid_content_type_7, content_name, performative
        )
        assert invalid_result_7 is False
        assert (
            invalid_msg_7
            == "Invalid type for content '{}' of performative '{}'. See documentation for the correct format of specification types.".format(
                content_name, performative,
            )
        )

    @mock.patch("aea.configurations.base.ProtocolSpecification",)
    def test_validate_speech_acts_section(self, mocked_spec):
        """Test for the '_validate_speech_acts_section' method."""
        valid_speech_act_content_config_1 = SpeechActContentConfig(
            content_1="ct:CustomType", content_2="pt:int"
        )
        valid_speech_act_content_config_2 = SpeechActContentConfig(
            content_3="ct:DataModel"
        )
        valid_speech_act_content_config_3 = SpeechActContentConfig()

        speech_act_1 = CRUDCollection()
        speech_act_1.create("perm_1", valid_speech_act_content_config_1)
        speech_act_1.create("perm_2", valid_speech_act_content_config_2)
        speech_act_1.create("perm_3", valid_speech_act_content_config_3)

        mocked_spec.speech_acts = speech_act_1

        (
            valid_result_1,
            valid_msg_1,
            valid_all_per_1,
            valid_all_content_1,
        ) = _validate_speech_acts_section(mocked_spec)
        assert valid_result_1 is True
        assert valid_msg_1 == "Speech-acts are valid."
        assert valid_all_per_1 == {"perm_1", "perm_2", "perm_3"}
        assert valid_all_content_1 == {"ct:CustomType", "ct:DataModel"}

        ###################################################

        speech_act_3 = CRUDCollection()
        invalid_perm = "_query_"
        speech_act_3.create(invalid_perm, valid_speech_act_content_config_1)

        mocked_spec.speech_acts = speech_act_3

        (
            invalid_result_1,
            invalid_msg_1,
            invalid_all_per_1,
            invalid_all_content_1,
        ) = _validate_speech_acts_section(mocked_spec)
        assert invalid_result_1 is False
        assert (
            invalid_msg_1
            == "Invalid name for performative '{}'. Performative names must match the following regular expression: {} ".format(
                invalid_perm, PERFORMATIVE_REGEX_PATTERN
            )
        )
        assert invalid_all_per_1 is None
        assert invalid_all_content_1 is None

        invalid_speech_act_content_config_1 = SpeechActContentConfig(target="pt:int")
        speech_act_4 = CRUDCollection()
        valid_perm = "perm_1"
        speech_act_4.create(valid_perm, invalid_speech_act_content_config_1)

        mocked_spec.speech_acts = speech_act_4

        (
            invalid_result_2,
            invalid_msg_2,
            invalid_all_per_2,
            invalid_all_content_2,
        ) = _validate_speech_acts_section(mocked_spec)
        assert invalid_result_2 is False
        assert (
            invalid_msg_2
            == "Invalid name for content '{}' of performative '{}'. This name is reserved.".format(
                "target", valid_perm,
            )
        )
        assert invalid_all_per_2 is None
        assert invalid_all_content_2 is None

        invalid_speech_act_content_config_2 = SpeechActContentConfig(
            content_name_1="pt: set[pt:int]"
        )
        speech_act_5 = CRUDCollection()
        speech_act_5.create(valid_perm, invalid_speech_act_content_config_2)

        mocked_spec.speech_acts = speech_act_5

        (
            invalid_result_3,
            invalid_msg_3,
            invalid_all_per_3,
            invalid_all_content_3,
        ) = _validate_speech_acts_section(mocked_spec)
        assert invalid_result_3 is False
        assert (
            invalid_msg_3
            == "Invalid type for content 'content_name_1' of performative '{}'. See documentation for the correct format of specification types.".format(
                valid_perm,
            )
        )
        assert invalid_all_per_3 is None
        assert invalid_all_content_3 is None

        speech_act_6 = CRUDCollection()
        mocked_spec.speech_acts = speech_act_6

        (
            invalid_result_4,
            invalid_msg_4,
            invalid_all_per_4,
            invalid_all_content_4,
        ) = _validate_speech_acts_section(mocked_spec)
        assert invalid_result_4 is False
        assert invalid_msg_4 == "Speech-acts cannot be empty!"
        assert invalid_all_per_4 is None
        assert invalid_all_content_4 is None

        invalid_speech_act_content_config_3 = SpeechActContentConfig(content_name_1=123)
        speech_act_7 = CRUDCollection()
        speech_act_7.create(valid_perm, invalid_speech_act_content_config_3)

        mocked_spec.speech_acts = speech_act_7

        (
            invalid_result_5,
            invalid_msg_5,
            invalid_all_per_5,
            invalid_all_content_5,
        ) = _validate_speech_acts_section(mocked_spec)
        assert invalid_result_5 is False
        assert (
            invalid_msg_5
            == f"Invalid type for '{'content_name_1'}'. Expected str. Found {type(123)}."
        )
        assert invalid_all_per_5 is None
        assert invalid_all_content_5 is None

        invalid_speech_act_content_config_4 = SpeechActContentConfig(
            content_name_1="pt:int"
        )
        invalid_speech_act_content_config_5 = SpeechActContentConfig(
            content_name_1="pt:float"
        )
        speech_act_8 = CRUDCollection()
        speech_act_8.create("perm_1", invalid_speech_act_content_config_4)
        speech_act_8.create("perm_2", invalid_speech_act_content_config_5)

        mocked_spec.speech_acts = speech_act_8

        (
            invalid_result_6,
            invalid_msg_6,
            invalid_all_per_6,
            invalid_all_content_6,
        ) = _validate_speech_acts_section(mocked_spec)
        assert invalid_result_6 is False
        assert (
            invalid_msg_6
            == "Content 'content_name_1' with type 'pt:float' under performative 'perm_2' is already defined under performative 'perm_1' with a different type ('pt:int')."
        )
        assert invalid_all_per_6 is None
        assert invalid_all_content_6 is None

    @mock.patch("aea.configurations.base.ProtocolSpecification",)
    def test_validate_protocol_buffer_schema_code_snippets(self, mocked_spec):
        """Test for the '_validate_protocol_buffer_schema_code_snippets' method."""
        valid_protobuf_snippet_1 = {
            "ct:DataModel": "bytes bytes_field = 1;\nint32 int_field = 2;\nfloat float_field = 3;\nbool bool_field = 4;\nstring str_field = 5;\nrepeated int32 set_field = 6;\nrepeated string list_field = 7;\nmap<int32, bool> dict_field = 8;\n"
        }
        valid_all_content_1 = {"ct:DataModel"}
        mocked_spec.protobuf_snippets = valid_protobuf_snippet_1

        valid_result_1, valid_msg_1, = _validate_protocol_buffer_schema_code_snippets(
            mocked_spec, valid_all_content_1
        )
        assert valid_result_1 is True
        assert valid_msg_1 == "Protobuf code snippet section is valid."

        valid_protobuf_snippet_2 = {}
        valid_all_content_2 = set()
        mocked_spec.protobuf_snippets = valid_protobuf_snippet_2

        valid_result_2, valid_msg_2, = _validate_protocol_buffer_schema_code_snippets(
            mocked_spec, valid_all_content_2
        )
        assert valid_result_2 is True
        assert valid_msg_2 == "Protobuf code snippet section is valid."

        ###################################################

        invalid_protobuf_snippet_1 = {
            "ct:DataModel": "bytes bytes_field = 1;\nint32 int_field = 2;\nfloat float_field = 3;\nbool bool_field = 4;\nstring str_field = 5;",
            "ct:Query": "bytes bytes_field = 1;",
        }
        invalid_all_content_1 = {"ct:DataModel"}
        mocked_spec.protobuf_snippets = invalid_protobuf_snippet_1

        (
            invalid_result_1,
            invalid_msg_1,
        ) = _validate_protocol_buffer_schema_code_snippets(
            mocked_spec, invalid_all_content_1
        )
        assert invalid_result_1 is False
        assert (
            invalid_msg_1
            == "Extra protobuf code snippet provided. Type 'ct:Query' is not used anywhere in your protocol definition."
        )

        invalid_protobuf_snippet_2 = {
            "ct:DataModel": "bytes bytes_field = 1;\nint32 int_field = 2;\nfloat float_field = 3;",
        }
        invalid_all_content_2 = {"ct:DataModel", "ct:Frame"}
        mocked_spec.protobuf_snippets = invalid_protobuf_snippet_2

        (
            invalid_result_2,
            invalid_msg_2,
        ) = _validate_protocol_buffer_schema_code_snippets(
            mocked_spec, invalid_all_content_2
        )
        assert invalid_result_2 is False
        assert (
            invalid_msg_2
            == "No protobuf code snippet is provided for the following custom types: {}".format(
                {"ct:Frame"},
            )
        )

    def test_validate_field_existence(self):
        """Test for the '_validate_field_existence' method."""
        valid_dialogue_config_1 = {
            "initiation": ["performative_ct", "performative_pt"],
            "reply": {
                "performative_ct": ["performative_pct"],
                "performative_pt": ["performative_pmt"],
                "performative_pct": ["performative_mt", "performative_o"],
                "performative_pmt": ["performative_mt", "performative_o"],
                "performative_mt": [],
                "performative_o": [],
                "performative_empty_contents": ["performative_empty_contents"],
            },
            "termination": [
                "performative_mt",
                "performative_o",
                "performative_empty_contents",
            ],
            "roles": {"role_1": None, "role_2": None},
            "end_states": ["end_state_1", "end_state_2", "end_state_3"],
            "keep_terminal_state_dialogues": True,
        }

        valid_result_1, valid_msg_1, = _validate_field_existence(
            valid_dialogue_config_1
        )
        assert valid_result_1 is True
        assert valid_msg_1 == "Dialogue section has all the required fields."

        ###################################################

        invalid_dialogue_config_1 = valid_dialogue_config_1.copy()
        invalid_dialogue_config_1.pop("initiation")

        invalid_result_1, invalid_msg_1, = _validate_field_existence(
            invalid_dialogue_config_1
        )
        assert invalid_result_1 is False
        assert (
            invalid_msg_1
            == "Missing required field 'initiation' in the dialogue section of the protocol specification."
        )

        invalid_dialogue_config_2 = valid_dialogue_config_1.copy()
        invalid_dialogue_config_2.pop("reply")

        invalid_result_2, invalid_msg_2, = _validate_field_existence(
            invalid_dialogue_config_2
        )
        assert invalid_result_2 is False
        assert (
            invalid_msg_2
            == "Missing required field 'reply' in the dialogue section of the protocol specification."
        )

    def test_validate_initiation(self):
        """Test for the '_validate_initiation' method."""
        valid_initiation_1 = ["perm_1", "perm_2"]
        valid_performatives_set = {"perm_1", "perm_2", "perm_3", "perm_4"}
        valid_result_1, valid_msg_1 = _validate_initiation(
            valid_initiation_1, valid_performatives_set
        )
        assert valid_result_1 is True
        assert valid_msg_1 == "Initial messages are valid."

        ###################################################

        invalid_initiation_1 = []
        invalid_result_1, invalid_msg_1 = _validate_initiation(
            invalid_initiation_1, valid_performatives_set
        )
        assert invalid_result_1 is False
        assert (
            invalid_msg_1
            == "At least one initial performative for this dialogue must be specified."
        )

        invalid_initiation_2 = ["perm_5"]
        invalid_result_2, invalid_msg_2 = _validate_initiation(
            invalid_initiation_2, valid_performatives_set
        )
        assert invalid_result_2 is False
        assert (
            invalid_msg_2
            == "Performative 'perm_5' specified in \"initiation\" is not defined in the protocol's speech-acts."
        )

        invalid_initiation_3 = "perm_1"
        invalid_result_3, invalid_msg_3 = _validate_initiation(
            invalid_initiation_3, valid_performatives_set
        )
        assert invalid_result_3 is False
        assert (
            invalid_msg_3
            == f"Invalid type for initiation. Expected list. Found '{type(invalid_initiation_3)}'."
        )

    def test_validate_reply(self):
        """Test for the '_validate_reply' method."""
        valid_reply_1 = {
            "performative_ct": ["performative_pct"],
            "performative_pt": ["performative_pmt"],
            "performative_pct": ["performative_mt", "performative_o"],
            "performative_pmt": ["performative_mt", "performative_o"],
            "performative_mt": [],
            "performative_o": [],
            "performative_empty_contents": ["performative_empty_contents"],
        }
        valid_performatives_set_1 = {
            "performative_ct",
            "performative_pt",
            "performative_pct",
            "performative_pmt",
            "performative_mt",
            "performative_o",
            "performative_empty_contents",
        }

        (
            valid_result_1,
            valid_msg_1,
            terminal_performatives_from_reply_1,
        ) = _validate_reply(valid_reply_1, valid_performatives_set_1)
        assert valid_result_1 is True
        assert valid_msg_1 == "Reply structure is valid."
        assert terminal_performatives_from_reply_1 == {
            "performative_mt",
            "performative_o",
        }

        ###################################################

        invalid_reply_1 = {
            "perm_1": ["perm_2"],
            "perm_2": ["perm_3"],
            "perm_3": ["perm_4"],
            "perm_4": [],
        }
        invalid_performatives_set_1 = {"perm_1", "perm_2", "perm_3", "perm_4", "perm_5"}

        (
            invalid_result_1,
            invalid_msg_1,
            invalid_terminal_performatives_from_reply_1,
        ) = _validate_reply(invalid_reply_1, invalid_performatives_set_1)
        assert invalid_result_1 is False
        assert (
            invalid_msg_1
            == "No reply is provided for the following performatives: {}".format(
                {"perm_5"},
            )
        )
        assert invalid_terminal_performatives_from_reply_1 is None

        invalid_reply_2 = {
            "perm_1": ["perm_2"],
            "perm_2": ["perm_3"],
            "perm_3": ["perm_4"],
            "perm_4": ["perm_5"],
            "perm_5": [],
        }
        invalid_performatives_set_2 = {"perm_1", "perm_2", "perm_3", "perm_4"}
        (
            invalid_result_2,
            invalid_msg_2,
            invalid_terminal_performatives_from_reply_2,
        ) = _validate_reply(invalid_reply_2, invalid_performatives_set_2)
        assert invalid_result_2 is False
        assert (
            invalid_msg_2
            == "Performative 'perm_5' in the list of replies for 'perm_4' is not defined in speech-acts."
        )
        assert invalid_terminal_performatives_from_reply_2 is None

        invalid_reply_3 = ["perm_1", "perm_2", "perm_3", "perm_4", "perm_5"]
        (
            invalid_result_3,
            invalid_msg_3,
            invalid_terminal_performatives_from_reply_3,
        ) = _validate_reply(invalid_reply_3, invalid_performatives_set_1)
        assert invalid_result_3 is False
        assert (
            invalid_msg_3
            == f"Invalid type for the reply definition. Expected dict. Found '{type(invalid_reply_3)}'."
        )
        assert invalid_terminal_performatives_from_reply_3 is None

        invalid_reply_4 = {
            "perm_1": {"perm_2"},
            "perm_2": {"perm_3"},
            "perm_3": {"perm_4"},
            "perm_4": {"perm_5"},
            "perm_5": set(),
        }
        (
            invalid_result_4,
            invalid_msg_4,
            invalid_terminal_performatives_from_reply_4,
        ) = _validate_reply(invalid_reply_4, invalid_performatives_set_1)
        assert invalid_result_4 is False
        assert (
            invalid_msg_4
            == f"Invalid type for replies of performative perm_1. Expected list. Found '{type({'perm_2'})}'."
        )
        assert invalid_terminal_performatives_from_reply_4 is None

        invalid_reply_5 = {
            "perm_1": ["perm_2"],
            "perm_2": ["perm_3"],
            "perm_3": ["perm_4"],
            "perm_4": ["perm_1"],
            "perm_5": [],
        }
        (
            invalid_result_5,
            invalid_msg_5,
            invalid_terminal_performatives_from_reply_5,
        ) = _validate_reply(invalid_reply_5, invalid_performatives_set_2)
        assert invalid_result_5 is False
        assert (
            invalid_msg_5
            == "Performative 'perm_5' specified in \"reply\" is not defined in the protocol's speech-acts."
        )
        assert invalid_terminal_performatives_from_reply_5 is None

    def test_validate_termination(self):
        """Test for the '_validate_termination' method."""
        valid_termination_1 = ["perm_4", "perm_3"]
        valid_performatives_set = {"perm_1", "perm_2", "perm_3", "perm_4"}
        valid_terminal_performatives_from_reply_1 = {"perm_4", "perm_3"}
        valid_result_1, valid_msg_1 = _validate_termination(
            valid_termination_1,
            valid_performatives_set,
            valid_terminal_performatives_from_reply_1,
        )
        assert valid_result_1 is True
        assert valid_msg_1 == "Terminal messages are valid."

        ###################################################

        invalid_termination_1 = []
        invalid_terminal_performatives_from_reply_1 = set()
        invalid_result_1, invalid_msg_1 = _validate_termination(
            invalid_termination_1,
            valid_performatives_set,
            invalid_terminal_performatives_from_reply_1,
        )
        assert invalid_result_1 is False
        assert (
            invalid_msg_1
            == "At least one terminal performative for this dialogue must be specified."
        )

        invalid_termination_2 = ["perm_5"]
        invalid_terminal_performatives_from_reply_2 = {"perm_5"}
        invalid_result_2, invalid_msg_2 = _validate_termination(
            invalid_termination_2,
            valid_performatives_set,
            invalid_terminal_performatives_from_reply_2,
        )
        assert invalid_result_2 is False
        assert (
            invalid_msg_2
            == "Performative 'perm_5' specified in \"termination\" is not defined in the protocol's speech-acts."
        )

        invalid_termination_3 = {"perm_5"}
        invalid_terminal_performatives_from_reply_3 = {"perm_5"}
        invalid_result_3, invalid_msg_3 = _validate_termination(
            invalid_termination_3,
            valid_performatives_set,
            invalid_terminal_performatives_from_reply_3,
        )
        assert invalid_result_3 is False
        assert (
            invalid_msg_3
            == f"Invalid type for termination. Expected list. Found '{type(invalid_termination_3)}'."
        )

        invalid_termination_4 = ["perm_4", "perm_3", "perm_4", "perm_3", "perm_1"]
        invalid_terminal_performatives_from_reply_4 = {"perm_4", "perm_3", "perm_1"}
        invalid_result_4, invalid_msg_4 = _validate_termination(
            invalid_termination_4,
            valid_performatives_set,
            invalid_terminal_performatives_from_reply_4,
        )
        assert invalid_result_4 is False
        assert (
            invalid_msg_4 == f'There are {2} duplicate performatives in "termination".'
        )

        invalid_termination_5 = ["perm_4", "perm_3"]
        invalid_terminal_performatives_from_reply_5 = {"perm_4"}
        invalid_result_5, invalid_msg_5 = _validate_termination(
            invalid_termination_5,
            valid_performatives_set,
            invalid_terminal_performatives_from_reply_5,
        )
        assert invalid_result_5 is False
        assert (
            invalid_msg_5
            == 'The terminal performative \'perm_3\' specified in "termination" is assigned replies in "reply".'
        )

        invalid_termination_6 = ["perm_4"]
        invalid_terminal_performatives_from_reply_6 = {"perm_4", "perm_3"}
        invalid_result_6, invalid_msg_6 = _validate_termination(
            invalid_termination_6,
            valid_performatives_set,
            invalid_terminal_performatives_from_reply_6,
        )
        assert invalid_result_6 is False
        assert (
            invalid_msg_6
            == "The performative 'perm_3' has no replies but is not listed as a terminal performative in \"termination\"."
        )

    def test_validate_roles(self):
        """Test for the '_validate_roles' method."""
        valid_roles_1 = {"role_1": None, "role_2": None}
        valid_result_1, valid_msg_1 = _validate_roles(valid_roles_1)
        assert valid_result_1 is True
        assert valid_msg_1 == "Dialogue roles are valid."

        valid_roles_2 = {"role_1": None}
        valid_result_2, valid_msg_2 = _validate_roles(valid_roles_2)
        assert valid_result_2 is True
        assert valid_msg_2 == "Dialogue roles are valid."

        ###################################################

        invalid_roles_1 = dict()
        invalid_result_1, invalid_msg_1 = _validate_roles(invalid_roles_1)
        assert invalid_result_1 is False
        assert (
            invalid_msg_1
            == "There must be either 1 or 2 roles defined in this dialogue. Found 0"
        )

        invalid_roles_2 = {"role_1": None, "role_2": None, "role_3": None}
        invalid_result_2, invalid_msg_2 = _validate_roles(invalid_roles_2)
        assert invalid_result_2 is False
        assert (
            invalid_msg_2
            == "There must be either 1 or 2 roles defined in this dialogue. Found 3"
        )

        invalid_roles_3 = {"_agent_": None}
        invalid_result_3, invalid_msg_3 = _validate_roles(invalid_roles_3)
        assert invalid_result_3 is False
        assert (
            invalid_msg_3
            == "Invalid name for role '_agent_'. Role names must match the following regular expression: {} ".format(
                ROLE_REGEX_PATTERN
            )
        )

        invalid_roles_4 = {"client"}
        invalid_result_4, invalid_msg_4 = _validate_roles(invalid_roles_4)
        assert invalid_result_4 is False
        assert (
            invalid_msg_4
            == f"Invalid type for roles. Expected dict. Found '{type(invalid_roles_4)}'."
        )

    def test_validate_end_states(self):
        """Test for the '_validate_end_states' method."""
        valid_end_states_1 = ["end_state_1", "end_state_2"]
        valid_result_1, valid_msg_1 = _validate_end_states(valid_end_states_1)
        assert valid_result_1 is True
        assert valid_msg_1 == "Dialogue end_states are valid."

        valid_end_states_2 = []
        valid_result_2, valid_msg_2 = _validate_end_states(valid_end_states_2)
        assert valid_result_2 is True
        assert valid_msg_2 == "Dialogue end_states are valid."

        ###################################################

        invalid_end_states_1 = ["_end_state_1"]
        invalid_result_1, invalid_msg_1 = _validate_end_states(invalid_end_states_1)
        assert invalid_result_1 is False
        assert (
            invalid_msg_1
            == "Invalid name for end_state '_end_state_1'. End_state names must match the following regular expression: {} ".format(
                END_STATE_REGEX_PATTERN
            )
        )

        invalid_end_states_2 = ["end_$tate_1"]
        invalid_result_2, invalid_msg_2 = _validate_end_states(invalid_end_states_2)
        assert invalid_result_2 is False
        assert (
            invalid_msg_2
            == "Invalid name for end_state 'end_$tate_1'. End_state names must match the following regular expression: {} ".format(
                END_STATE_REGEX_PATTERN
            )
        )

        invalid_end_states_3 = {"end_state_1"}
        invalid_result_3, invalid_msg_3 = _validate_end_states(invalid_end_states_3)
        assert invalid_result_3 is False
        assert (
            invalid_msg_3
            == f"Invalid type for roles. Expected list. Found '{type(invalid_end_states_3)}'."
        )

    def test_validate_keep_terminal(self):
        """Test for the '_validate_keep_terminal' method."""
        valid_keep_terminal_state_dialogues_1 = True
        valid_result_1, valid_msg_1 = _validate_keep_terminal(
            valid_keep_terminal_state_dialogues_1
        )
        assert valid_result_1 is True
        assert valid_msg_1 == "Dialogue keep_terminal_state_dialogues is valid."

        valid_keep_terminal_state_dialogues_2 = False
        valid_result_2, valid_msg_2 = _validate_keep_terminal(
            valid_keep_terminal_state_dialogues_2
        )
        assert valid_result_2 is True
        assert valid_msg_2 == "Dialogue keep_terminal_state_dialogues is valid."

        ###################################################

        invalid_keep_terminal_state_dialogues_1 = "some_non_boolean_value"
        invalid_result_1, invalid_msg_1 = _validate_keep_terminal(
            invalid_keep_terminal_state_dialogues_1
        )
        assert invalid_result_1 is False
        assert (
            invalid_msg_1
            == f"Invalid type for keep_terminal_state_dialogues. Expected bool. Found {type(invalid_keep_terminal_state_dialogues_1)}."
        )

    @mock.patch("aea.configurations.base.ProtocolSpecification",)
    def test_validate_dialogue_section(self, mocked_spec):
        """Test for the '_validate_dialogue_section' method."""
        valid_dialogue_config_1 = {
            "initiation": ["performative_ct", "performative_pt"],
            "reply": {
                "performative_ct": ["performative_pct"],
                "performative_pt": ["performative_pmt"],
                "performative_pct": ["performative_mt", "performative_o"],
                "performative_pmt": ["performative_mt", "performative_o"],
                "performative_mt": [],
                "performative_o": [],
                "performative_empty_contents": ["performative_empty_contents"],
            },
            "termination": ["performative_mt", "performative_o"],
            "roles": {"role_1": None, "role_2": None},
            "end_states": ["end_state_1", "end_state_2", "end_state_3"],
            "keep_terminal_state_dialogues": True,
        }
        valid_performatives_set_1 = {
            "performative_ct",
            "performative_pt",
            "performative_pct",
            "performative_pmt",
            "performative_mt",
            "performative_o",
            "performative_empty_contents",
        }
        mocked_spec.dialogue_config = valid_dialogue_config_1

        valid_result_1, valid_msg_1, = _validate_dialogue_section(
            mocked_spec, valid_performatives_set_1
        )
        assert valid_result_1 is True
        assert valid_msg_1 == "Dialogue section of the protocol specification is valid."

        ###################################################

        invalid_dialogue_config_1 = valid_dialogue_config_1.copy()
        invalid_dialogue_config_1["initiation"] = ["new_performative"]

        mocked_spec.dialogue_config = invalid_dialogue_config_1

        invalid_result_1, invalid_msg_1, = _validate_dialogue_section(
            mocked_spec, valid_performatives_set_1
        )
        assert invalid_result_1 is False
        assert (
            invalid_msg_1
            == "Performative 'new_performative' specified in \"initiation\" is not defined in the protocol's speech-acts."
        )

        invalid_dialogue_config_2 = valid_dialogue_config_1.copy()
        invalid_dialogue_config_2["reply"] = {
            "performative_ct": ["performative_pct"],
            "performative_pt": ["performative_pmt"],
            "performative_pct": ["performative_mt", "performative_o"],
            "performative_pmt": ["performative_mt", "performative_o"],
            "performative_mt": [],
            "performative_o": [],
        }

        mocked_spec.dialogue_config = invalid_dialogue_config_2

        invalid_result_2, invalid_msg_2, = _validate_dialogue_section(
            mocked_spec, valid_performatives_set_1
        )
        assert invalid_result_2 is False
        assert (
            invalid_msg_2
            == "No reply is provided for the following performatives: {}".format(
                {"performative_empty_contents"},
            )
        )

        invalid_dialogue_config_3 = valid_dialogue_config_1.copy()
        invalid_dialogue_config_3["termination"] = ["new_performative"]

        mocked_spec.dialogue_config = invalid_dialogue_config_3

        invalid_result_3, invalid_msg_3, = _validate_dialogue_section(
            mocked_spec, valid_performatives_set_1
        )
        assert invalid_result_3 is False
        assert (
            invalid_msg_3
            == "Performative 'new_performative' specified in \"termination\" is not defined in the protocol's speech-acts."
        )

        invalid_dialogue_config_4 = valid_dialogue_config_1.copy()
        invalid_dialogue_config_4["roles"] = {
            "role_1": None,
            "role_2": None,
            "role_3": None,
        }

        mocked_spec.dialogue_config = invalid_dialogue_config_4

        invalid_result_4, invalid_msg_4, = _validate_dialogue_section(
            mocked_spec, valid_performatives_set_1
        )
        assert invalid_result_4 is False
        assert (
            invalid_msg_4
            == "There must be either 1 or 2 roles defined in this dialogue. Found 3"
        )

        invalid_dialogue_config_5 = valid_dialogue_config_1.copy()
        invalid_dialogue_config_5["end_states"] = ["end_$tate_1"]

        mocked_spec.dialogue_config = invalid_dialogue_config_5

        invalid_result_5, invalid_msg_5, = _validate_dialogue_section(
            mocked_spec, valid_performatives_set_1
        )
        assert invalid_result_5 is False
        assert (
            invalid_msg_5
            == "Invalid name for end_state 'end_$tate_1'. End_state names must match the following regular expression: {} ".format(
                END_STATE_REGEX_PATTERN
            )
        )

        invalid_dialogue_config_6 = valid_dialogue_config_1.copy()
        invalid_dialogue_config_6.pop("termination")
        mocked_spec.dialogue_config = invalid_dialogue_config_6

        invalid_result_6, invalid_msg_6, = _validate_dialogue_section(
            mocked_spec, valid_performatives_set_1
        )
        assert invalid_result_6 is False
        assert (
            invalid_msg_6
            == "Missing required field 'termination' in the dialogue section of the protocol specification."
        )

        invalid_value = 521
        invalid_dialogue_config_7 = valid_dialogue_config_1.copy()
        invalid_dialogue_config_7["keep_terminal_state_dialogues"] = invalid_value
        mocked_spec.dialogue_config = invalid_dialogue_config_7

        invalid_result_7, invalid_msg_7, = _validate_dialogue_section(
            mocked_spec, valid_performatives_set_1
        )
        assert invalid_result_7 is False
        assert (
            invalid_msg_7
            == f"Invalid type for keep_terminal_state_dialogues. Expected bool. Found {type(invalid_value)}."
        )

    @mock.patch("aea.configurations.base.ProtocolSpecification")
    @mock.patch(
        "aea.protocols.generator.validate._validate_speech_acts_section",
        return_value=tuple([True, "Speech_acts are correct!", set(), set()]),
    )
    @mock.patch(
        "aea.protocols.generator.validate._validate_protocol_buffer_schema_code_snippets",
        return_value=tuple([True, "Protobuf snippets are correct!"]),
    )
    @mock.patch(
        "aea.protocols.generator.validate._validate_dialogue_section",
        return_value=tuple([True, "Dialogue section is correct!"]),
    )
    def test_validate_positive(
        self,
        mocked_spec,
        macked_validate_speech_acts,
        macked_validate_protobuf,
        macked_validate_dialogue,
    ):
        """Positive test for the 'validate' method: invalid dialogue section."""
        valid_result_1, valid_msg_1, = validate(mocked_spec)
        assert valid_result_1 is True
        assert valid_msg_1 == "Protocol specification is valid."

    @mock.patch("aea.configurations.base.ProtocolSpecification")
    @mock.patch(
        "aea.protocols.generator.validate._validate_speech_acts_section",
        return_value=tuple([False, "Some error on speech_acts.", None, None]),
    )
    def test_validate_negative_invalid_speech_acts(
        self, mocked_spec, macked_validate_speech_acts
    ):
        """Negative test for the 'validate' method: invalid speech_acts."""
        invalid_result_1, invalid_msg_1, = validate(mocked_spec)
        assert invalid_result_1 is False
        assert invalid_msg_1 == "Some error on speech_acts."

    @mock.patch("aea.configurations.base.ProtocolSpecification")
    @mock.patch(
        "aea.protocols.generator.validate._validate_speech_acts_section",
        return_value=tuple([True, "Speech_acts are correct!", set(), set()]),
    )
    @mock.patch(
        "aea.protocols.generator.validate._validate_protocol_buffer_schema_code_snippets",
        return_value=tuple([False, "Some error on protobuf snippets."]),
    )
    def test_validate_negative_invalid_protobuf_snippets(
        self, mocked_spec, macked_validate_speech_acts, macked_validate_protobuf
    ):
        """Negative test for the 'validate' method: invalid protobuf snippets."""
        invalid_result_1, invalid_msg_1, = validate(mocked_spec)
        assert invalid_result_1 is False
        assert invalid_msg_1 == "Some error on protobuf snippets."

    @mock.patch("aea.configurations.base.ProtocolSpecification")
    @mock.patch(
        "aea.protocols.generator.validate._validate_speech_acts_section",
        return_value=tuple([True, "Speech_acts are correct!", set(), set()]),
    )
    @mock.patch(
        "aea.protocols.generator.validate._validate_protocol_buffer_schema_code_snippets",
        return_value=tuple([True, "Protobuf snippets are correct!"]),
    )
    @mock.patch(
        "aea.protocols.generator.validate._validate_dialogue_section",
        return_value=tuple([False, "Some error on dialogue section."]),
    )
    def test_validate_negative_invalid_dialogue_section(
        self,
        mocked_spec,
        macked_validate_speech_acts,
        macked_validate_protobuf,
        macked_validate_dialogue,
    ):
        """Negative test for the 'validate' method: invalid dialogue section."""
        invalid_result_1, invalid_msg_1, = validate(mocked_spec)
        assert invalid_result_1 is False
        assert invalid_msg_1 == "Some error on dialogue section."
