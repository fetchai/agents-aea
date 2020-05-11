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

"""This module contains helper function to extract code from the .md files."""
import re
import traceback
from typing import Dict

import pytest


def extract_code_blocks(filepath, filter=None):
    """Extract code blocks from .md files."""
    code_blocks = []
    with open(filepath, "r", encoding="utf-8") as f:
        while True:
            line = f.readline()
            if not line:
                # EOF
                break

            out = re.match("[^`]*```(.*)$", line)
            if out:
                if filter and filter.strip() != out.group(1).strip():
                    continue
                code_block = [f.readline()]
                while re.search("```", code_block[-1]) is None:
                    code_block.append(f.readline())
                code_blocks.append("".join(code_block[:-1]))
    return code_blocks


def extract_python_code(filepath):
    """Removes the license part from the scripts"""
    python_str = ""
    with open(filepath, "r") as python_file:
        read_python_file = python_file.readlines()
    for i in range(21, len(read_python_file)):
        python_str += read_python_file[i]

    return python_str


def read_md_file(filepath):
    """Reads an md file and returns the string."""
    with open(filepath, "r", encoding="utf-8") as md_file:
        md_file_str = md_file.read()
    return md_file_str


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
