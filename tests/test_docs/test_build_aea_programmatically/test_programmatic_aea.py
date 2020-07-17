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

"""This module contains the tests for the code-blocks in the build-aea-programmatically.md file."""

import os
from pathlib import Path

from aea.configurations.constants import DEFAULT_PRIVATE_KEY_FILE
from aea.test_tools.test_cases import BaseAEATestCase

from tests.conftest import CUR_PATH, ROOT_DIR, skip_test_windows
from tests.test_docs.helper import extract_code_blocks, extract_python_code

from .programmatic_aea import run

MD_FILE = "docs/build-aea-programmatically.md"
PY_FILE = "test_docs/test_build_aea_programmatically/programmatic_aea.py"


class TestProgrammaticAEA(BaseAEATestCase):
    """This class contains the tests for the code-blocks in the build-aea-programmatically.md file."""

    @classmethod
    def setup_class(cls):
        """Setup the test class."""
        BaseAEATestCase.setup_class()
        doc_path = os.path.join(ROOT_DIR, MD_FILE)
        cls.code_blocks = extract_code_blocks(filepath=doc_path, filter="python")
        test_code_path = os.path.join(CUR_PATH, PY_FILE)
        cls.python_file = extract_python_code(test_code_path)

    def test_read_md_file(self):
        """Read the code blocks. Last block should be the whole code."""
        assert (
            self.code_blocks[-1] == self.python_file
        ), "Files must be exactly the same."

    @skip_test_windows
    def test_run_agent(self):
        """Run the agent from the file."""
        run()
        assert os.path.exists(Path(self.t, "input_file"))
        assert os.path.exists(Path(self.t, "output_file"))
        assert os.path.exists(Path(self.t, DEFAULT_PRIVATE_KEY_FILE))

        message_text = (
            "other_agent,my_aea,fetchai/default:0.3.0,\x08\x01*\x07\n\x05hello,"
        )
        path = os.path.join(self.t, "output_file")
        with open(path, "r") as file:
            msg = file.read()
        assert msg == message_text

    def test_code_blocks_exist(self):
        """Test that all the code-blocks exist in the python file."""
        for block in self.code_blocks:
            assert (
                block in self.python_file
            ), "Code-block doesn't exist in the python file."
