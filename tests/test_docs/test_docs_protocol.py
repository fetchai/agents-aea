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

"""This module contains the tests for the code-blocks in the protocol.md file."""
from pathlib import Path

import mistune
import pytest

from packages.fetchai.protocols.oef_search.custom_types import (
    OefErrorOperation as ExpectedOefErrorOperation,
)
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from .helper import compile_and_exec, compare_enum_classes
from ..conftest import ROOT_DIR


class TestProtocolDocs:
    """Test the integrity of the code-blocks in skill.md"""

    @classmethod
    def setup_class(cls):
        """Test skill.md"""
        markdown_parser = mistune.create_markdown(renderer=mistune.AstRenderer())

        skill_doc_file = Path(ROOT_DIR, "docs", "protocol.md")
        doc = markdown_parser(skill_doc_file.read_text())
        # get only code blocks
        cls.code_blocks = list(filter(lambda x: x["type"] == "block_code", doc))

    def test_custom_protocol(self):
        """Test the code in the 'Custom protocol' section."""
        # this is the offset of code blocks for the section under testing
        offset = 0
        locals_dict = {}
        compile_and_exec(self.code_blocks[offset]["text"], locals_dict=locals_dict)
        Performative = locals_dict["Performative"]

        # test that we can allocate a performative
        Performative("bytes")
        Performative("error")

        # test the values of this enum
        assert hasattr(Performative, "BYTES")
        assert hasattr(Performative, "ERROR")

        # load the example of default message of type BYTES
        compile_and_exec(self.code_blocks[offset + 1]["text"], locals_dict=locals_dict)

        # load the definition of the ErrorCode enumeration
        compile_and_exec(self.code_blocks[offset + 2]["text"], locals_dict=locals_dict)
        ErrorCode = locals_dict["ErrorCode"]
        ErrorCode(0)

        # load the example of default message of type ERROR
        _ = compile_and_exec(
            self.code_blocks[offset + 3]["text"], locals_dict=locals_dict
        )

    def test_oef_search_protocol(self):
        """Test the fetchai/oef_search:0.1.0 protocol documentation."""
        # this is the offset of code blocks for the section under testing
        offset = 4

        # define a data model and a description
        from enum import Enum

        locals_dict = {"Enum": Enum}
        compile_and_exec(self.code_blocks[offset]["text"], locals_dict=locals_dict)
        ActualPerformative = locals_dict["Performative"]
        compare_enum_classes(OefSearchMessage.Performative, ActualPerformative)

        compile_and_exec(self.code_blocks[offset + 1]["text"], locals_dict=locals_dict)
        # mind the indexes: +3 before +2
        compile_and_exec(self.code_blocks[offset + 3]["text"], locals_dict=locals_dict)
        compile_and_exec(self.code_blocks[offset + 2]["text"], locals_dict=locals_dict)

        # test the construction of OEF Search Messages
        locals_dict["OefSearchMessage"] = OefSearchMessage
        compile_and_exec(self.code_blocks[offset + 4]["text"], locals_dict=locals_dict)
        compile_and_exec(self.code_blocks[offset + 5]["text"], locals_dict=locals_dict)
        compile_and_exec(self.code_blocks[offset + 6]["text"], locals_dict=locals_dict)
        compile_and_exec(self.code_blocks[offset + 7]["text"], locals_dict=locals_dict)
        compile_and_exec(self.code_blocks[offset + 8]["text"], locals_dict=locals_dict)
        compile_and_exec(self.code_blocks[offset + 9]["text"], locals_dict=locals_dict)

        assert locals_dict["query_data"] == {
            "search_term": "country",
            "search_value": "UK",
            "constraint_type": "==",
        }

        # test the definition of OefErrorOperation
        compile_and_exec(self.code_blocks[offset + 10]["text"], locals_dict=locals_dict)
        ActualOefErrorOperation = locals_dict["OefErrorOperation"]
        compare_enum_classes(ExpectedOefErrorOperation, ActualOefErrorOperation)
