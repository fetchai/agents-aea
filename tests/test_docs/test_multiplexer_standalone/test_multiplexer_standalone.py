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

"""This module contains the tests for the code-blocks in the multiplexer-standalone.md file."""
import os
from pathlib import Path

from aea.helpers.file_io import lock_file
from aea.test_tools.test_cases import BaseAEATestCase

from tests.common.utils import wait_for_condition
from tests.conftest import CUR_PATH, ROOT_DIR
from tests.test_docs.helper import extract_code_blocks, extract_python_code
from tests.test_docs.test_multiplexer_standalone.multiplexer_standalone import run


MD_FILE = "docs/multiplexer-standalone.md"
PY_FILE = "test_docs/test_multiplexer_standalone/multiplexer_standalone.py"


class TestMultiplexerStandAlone(BaseAEATestCase):
    """This class contains the tests for the code-blocks in the build-aea-programmatically.md file."""

    @classmethod
    def setup_class(cls):
        """Setup the test class."""
        super().setup_class()
        doc_path = os.path.join(ROOT_DIR, MD_FILE)
        cls.code_blocks = extract_code_blocks(filepath=doc_path, filter_="python")
        test_code_path = os.path.join(CUR_PATH, PY_FILE)
        cls.python_file = extract_python_code(test_code_path)

    def test_read_md_file(self):
        """Read the code blocks. Last block should be the whole code."""
        assert (
            self.code_blocks[-1] == self.python_file
        ), "Files must be exactly the same."

    def test_run_agent(self):
        """Run the agent from the file."""
        run()
        assert os.path.exists(Path(self.t, "input.txt"))
        assert os.path.exists(Path(self.t, "output.txt"))

        message_text = (
            b"some_agent,multiplexer,fetchai/default:1.0.0,\x08\x01*\x07\n\x05hello,"
        )
        msg = ""

        path = os.path.join(str(self.t), "output.txt")
        input_file = open(path, "rb+")

        def _read():
            nonlocal msg
            with lock_file(input_file):
                data = input_file.read()
                if data:
                    input_file.truncate(0)
                    input_file.seek(0)
                    msg = data
                    return True
            return False

        wait_for_condition(
            _read, timeout=10, error_msg="Output file empty!", period=0.1
        )
        assert msg == message_text, "The messages must be identical."

    def test_code_blocks_exist(self):
        """Test that all the code-blocks exist in the python file."""
        for blocks in self.code_blocks:
            assert (
                blocks in self.python_file
            ), "Code-block doesn't exist in the python file."
