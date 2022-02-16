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
"""This module contains the tests for the code-blocks in the agent-vs-aea.md file."""

import os
from pathlib import Path

import pytest

from aea.test_tools.test_cases import AEATestCaseManyFlaky

from tests.conftest import CUR_PATH, MAX_FLAKY_RERUNS, ROOT_DIR
from tests.test_docs.helper import extract_code_blocks, extract_python_code
from tests.test_docs.test_agent_vs_aea.agent_code_block import run


MD_FILE = "docs/agent-vs-aea.md"
PY_FILE = "test_docs/test_agent_vs_aea/agent_code_block.py"


class TestFiles:
    """Test consistency of the files."""

    @classmethod
    def setup_class(cls):
        """Setup the test class."""
        doc_path = os.path.join(ROOT_DIR, MD_FILE)
        cls.code_blocks = extract_code_blocks(filepath=doc_path, filter_="python")
        test_code_path = os.path.join(CUR_PATH, PY_FILE)
        cls.python_file = extract_python_code(test_code_path)

    def test_read_md_file(self):
        """Test the last code block, that is the full listing of the demo from the Markdown."""
        assert (
            self.code_blocks[-1] == self.python_file
        ), "Files must be exactly the same."

    def test_code_blocks_exist(self):
        """Test that all the code-blocks exist in the python file."""
        for blocks in self.code_blocks:
            assert (
                blocks in self.python_file
            ), "Code-block doesn't exist in the python file."


class TestAgentVsAEA(AEATestCaseManyFlaky):
    """This class contains the tests for the code-blocks in the agent-vs-aea.md file."""

    @pytest.mark.flaky(
        reruns=MAX_FLAKY_RERUNS
    )  # TODO: check why test_run_agent raises permission error on file on windows platform!
    def test_run_agent(self):
        """Run the agent from the file."""
        run()
        assert os.path.exists(Path(self.t, "input_file"))

        message_text = b"other_agent,my_agent,fetchai/default:1.0.0,\x12\r\x08\x01*\t*\x07\n\x05hello,"
        path = os.path.join(self.t, "output_file")
        with open(path, "rb") as file:
            msg = file.read()
        assert msg == message_text, "The messages must be identical."
