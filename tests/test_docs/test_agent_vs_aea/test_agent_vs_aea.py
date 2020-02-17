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

"""This module contains the tests for the code-blocks in the agent-vs-aea.md file."""

import logging
import os

from .agent_code_block import run
from ..helper import extract_code_blocks
from ...conftest import CUR_PATH, ROOT_DIR

MD_FILE = "docs/agent-vs-aea.md"
PY_FILE = "test_docs/test_agent_vs_aea/agent_code_block.py"

logger = logging.getLogger(__name__)


class TestProgrammaticAEA:
    """This class contains the tests for the code-blocks in the agent-vs-aea.md file."""

    @classmethod
    def setup_class(cls):
        """Setup the test class."""
        cls.path = os.path.join(ROOT_DIR, MD_FILE)
        cls.code_blocks = extract_code_blocks(file=cls.path, filter="python")
        path = os.path.join(CUR_PATH, PY_FILE)
        with open(path, "r") as python_file:
            cls.read_python_file = python_file.read()

    def test_read_md_file(self):
        assert (
            self.code_blocks[-1] == self.read_python_file
        ), "Files must be exactly the same."

    def test_run_agent(self):
        """Run the agent from the file."""
        run()
        assert os.path.exists("input.txt")
        assert os.path.exists("output.txt")

    def test_code_blocks_exist(self):
        """Test that all the code-blocks exist in the python file."""
        for blocks in self.code_blocks:
            assert (
                blocks in self.read_python_file
            ), "Code-block doesn't exist in the python file."

    def test_input_file_message(self):
        """Test the input message is the correct one."""
        message_text = 'my_agent,other_agent,fetchai/default:0.1.0,{"type": "bytes", "content": "aGVsbG8="}'
        path = os.path.join(ROOT_DIR, "input.txt")
        with open(path, "r") as file:
            msg = file.read()
        assert msg == message_text, "The messages must be identical."

    def test_output_file_message(self):
        """Test the input message is the correct one."""
        message_text = 'other_agent,my_agent,fetchai/default:0.1.0,{"type": "bytes", "content": "aGVsbG8="}\n'
        path = os.path.join(ROOT_DIR, "output.txt")
        with open(path, "r") as file:
            msg = file.read()
        assert msg == message_text, "The messages must be identical."

    @classmethod
    def teardown_class(cls):
        """Teardown the test."""
        input_path = os.path.join(ROOT_DIR, "input.txt")
        output_path = os.path.join(ROOT_DIR, "output.txt")
        paths = [input_path, output_path]
        for path in paths:
            os.remove(path)
