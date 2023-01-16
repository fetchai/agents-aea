# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2023 Fetch.AI Limited
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

"""This module contains helper function to extract code from the .md files."""
import re
import traceback
from functools import partial
from pathlib import Path
from typing import Dict, List, Optional, cast

import mistune
import pytest


MISTUNE_BLOCK_CODE_ID = "block_code"


def block_code_filter(b: Dict) -> bool:
    """Check Mistune block is a code block."""
    return b["type"] == MISTUNE_BLOCK_CODE_ID


def type_filter(type_: Optional[str], b: Dict) -> bool:
    """
    Check Mistune code block is of a certain type.

    If the field "info" is None, return False.
    If type_ is None, this function always return true.

    :param type_: the expected type of block (optional)
    :param b: the block dicionary.
    :return: True if the block should be accepted, false otherwise.
    """
    if type_ is None:
        return True
    return b["info"].strip() == type_ if b["info"] is not None else False


def extract_dicts(dictionary: Dict, collection_dict: List[Dict]) -> List[Dict]:
    """Extract code blocks from .md files."""
    if all(not isinstance(v, list) for v in dictionary.values()):
        collection_dict.append(dictionary)
    else:
        for dict_el in dictionary.values():
            if isinstance(dict_el, list):
                for list_el in dict_el:
                    if isinstance(list_el, dict):
                        extract_dicts(list_el, collection_dict)
    return collection_dict


def flatten_blocks(blocks: List[Dict]) -> List[Dict]:
    """Flatten a list of dicts with nested dicts, into a list of all dicts."""
    new_blocks = []
    if isinstance(blocks, list):
        for el in blocks:
            if isinstance(el, dict):
                extract_dicts(el, new_blocks)
    return new_blocks


def expand_block(block: Dict, code_blocks: List[Dict]) -> None:
    """Replace block with any sub-blocks it may have"""
    # import pdb;pdb.set_trace()
    text = cast(str, block["text"])
    indexes = [m.start() for m in re.finditer('```', text)]
    if indexes:
        if len(indexes) % 2 != 0:
            raise SyntaxError(f"un-matching ``` found in the block: {text}")
        while indexes:
            starting_index = indexes.pop(0)
            ending_index = indexes.pop(0) + 3
            sub_string = text[starting_index:ending_index]
            type_ = text[starting_index + 4:text.find("\n", starting_index + 4)]
            new_dict = {'type': 'block_code', 'text': sub_string, 'info': type_}
            code_blocks.insert(code_blocks.index(block), new_dict)
        code_blocks.remove(block)


def extract_code_blocks(filepath, filter_=None):
    """Extract code blocks from .md files."""
    content = Path(filepath).read_text(encoding="utf-8")
    markdown_parser = mistune.create_markdown(renderer=mistune.AstRenderer())
    blocks = markdown_parser(content)
    flat_blocks = flatten_blocks(blocks)
    actual_type_filter = partial(type_filter, filter_)
    code_blocks = list(filter(block_code_filter, flat_blocks))
    for block in code_blocks:
        expand_block(block, code_blocks)
    for block in code_blocks:
        if block["text"].startswith("``` python"):
            block["text"] = cast(str, block["text"]).strip()[11:]
            if block["text"].endswith("```"):
                block["text"] = cast(str, block["text"]).strip()[:-3]
            block["info"] = " python"
        elif block["text"].startswith("``` bash"):
            block["text"] = cast(str, block["text"]).strip()[9:]
            if block["text"].endswith("```"):
                block["text"] = cast(str, block["text"]).strip()[:-3]
            block["info"] = " bash"
    bash_code_blocks = filter(actual_type_filter, code_blocks)
    return list(b["text"] for b in bash_code_blocks)


def extract_python_code(filepath):
    """Removes the license part from the scripts"""
    python_str = ""
    with open(filepath, "r") as python_file:
        read_python_file = python_file.readlines()
    for i in range(21, len(read_python_file)):
        python_str += read_python_file[i]

    return python_str


def compile_and_exec(code: str, locals_dict: Dict = None) -> Dict:
    """
    Compile and exec the code.

    :param code: the code to execute.
    :param locals_dict: the dictionary of local variables.
    :return: the dictionary of locals.
    """
    locals_dict = {} if locals_dict is None else locals_dict
    try:
        code_obj = compile(code, "fakemodule", "exec")
        exec(code_obj, locals_dict)  # nosec
    except Exception:
        pytest.fail(
            "The execution of the following code:\n{}\nfailed with error:\n{}".format(
                code, traceback.format_exc()
            )
        )
    return locals_dict


def compare_enum_classes(expected_enum_class, actual_enum_class):
    """Compare enum classes."""
    try:
        # do some pre-processing
        expected_pairs = sorted(map(lambda x: (x.name, x.value), expected_enum_class))
        actual_pairs = sorted(map(lambda x: (x.name, x.value), actual_enum_class))
        assert expected_pairs == actual_pairs, "{} != {}".format(
            expected_pairs, actual_pairs
        )
    except AssertionError:
        pytest.fail(
            "Actual enum {} is different from the actual one {}".format(
                expected_enum_class, actual_enum_class
            )
        )


class BaseTestMarkdownDocs:
    """Base test class for testing Markdown documents."""

    DOC_PATH: Path
    blocks: List[Dict]
    flat_blocks: List[Dict]
    python_blocks: List[Dict]

    @classmethod
    def setup_class(cls):
        """Set up the test."""
        markdown_parser = mistune.create_markdown(renderer=mistune.AstRenderer())
        cls.doc_path = cls.DOC_PATH
        cls.doc_content = cls.doc_path.read_text()
        cls.blocks = markdown_parser(cls.doc_content)
        cls.flat_blocks = flatten_blocks(cls.blocks)
        cls.code_blocks = list(filter(block_code_filter, cls.flat_blocks))
        cls.python_blocks = list(filter(cls._python_selector, cls.flat_blocks))

    @classmethod
    def _python_selector(cls, block: Dict) -> bool:
        return block["type"] == MISTUNE_BLOCK_CODE_ID and (
            block["info"].strip() == "python" if block["info"] else False
        )


class BasePythonMarkdownDocs(BaseTestMarkdownDocs):
    """Test Markdown documentation by running Python snippets in sequence."""

    @classmethod
    def setup_class(cls):
        """
        Set up class.

        It sets the initial value of locals and globals.
        """
        super().setup_class()
        cls.locals = {}
        cls.globals = {}

    def _assert(self, locals_, *mocks):
        """Do assertions after Python code execution."""

    def test_python_blocks(self, *mocks):
        """Run Python code block in sequence."""
        python_blocks = self.python_blocks

        globals_, locals_ = self.globals, self.locals
        for python_block in python_blocks:
            python_code = python_block["text"]
            exec(python_code, globals_, locals_)  # nosec
        self._assert(locals_, *mocks)
