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

"""This module contains the tests for the code-blocks in the standalone-transaction.md file."""

import logging
import os
import shutil
import tempfile
from unittest.mock import patch

import pytest

from .decision_maker_transaction import (
    logger,
    run,
)
from ..helper import extract_code_blocks, extract_python_code
from ...conftest import CUR_PATH, ROOT_DIR

MD_FILE = "docs/decision-maker-transaction.md"
PY_FILE = "test_docs/test_decision_maker_transaction/decision_maker_transaction.py"

test_logger = logging.getLogger(__name__)


class TestDecisionMakerTransaction:
    """This class contains the tests for the code-blocks in the agent-vs-aea.md file."""

    @classmethod
    def _patch_logger(cls):
        cls.patch_logger_info = patch.object(logger, "info")
        cls.mocked_logger_info = cls.patch_logger_info.__enter__()

    @classmethod
    def _unpatch_logger(cls):
        cls.mocked_logger_info.__exit__()

    @classmethod
    def setup_class(cls):
        """Setup the test class."""
        cls._patch_logger()
        cls.path = os.path.join(ROOT_DIR, MD_FILE)
        cls.code_blocks = extract_code_blocks(filepath=cls.path, filter="python")
        path = os.path.join(CUR_PATH, PY_FILE)
        cls.python_file = extract_python_code(path)
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

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

    def test_run_end_to_end(self, pytestconfig):
        """Run the transaction from the file."""
        if pytestconfig.getoption("ci"):
            pytest.skip("Skipping the test since it doesn't work in CI.")

        try:
            run()
            self.mocked_logger_info.assert_any_call("Transaction was not successful.")
        except RuntimeError:
            test_logger.info("RuntimeError: Some transactions have failed")

    @classmethod
    def teardown_class(cls):
        cls._unpatch_logger()
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass
