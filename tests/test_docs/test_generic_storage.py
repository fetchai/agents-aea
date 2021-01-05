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

"""This module contains the tests for the content of generic-storage.md file."""
import inspect
import re
from pathlib import Path

from aea.helpers.storage.generic_storage import SyncCollection
from aea.skills.behaviours import TickerBehaviour

from tests.conftest import ROOT_DIR
from tests.test_docs.helper import BaseTestMarkdownDocs


class TestGenericStorage(BaseTestMarkdownDocs):
    """Test generic-storage.md documentation."""

    DOC_PATH = Path(ROOT_DIR, "docs", "generic-storage.md")

    @classmethod
    def setup_class(cls):
        """
        Set up test.

        We test only the signatures and the
        docstrings of 'SyncCollection' methods. Hence,
        we need to remove the return statement.
        """
        super().setup_class()
        cls.content = inspect.getsource(SyncCollection)
        cls.content = re.sub("\n +return.*", "", cls.content)

    def test_storage_abstract_methods(self):
        """
        Test storage abstract methods.

        Note: the block index of the abstract methods is 0.
        Please check generic-storage.md
        """
        block_index = 1
        assert self.code_blocks[block_index]["text"] in self.content

    def test_test_behaviour(self):
        """Test that the 'TestBehaviour' code is compilable."""
        block_index = 2
        code = self.code_blocks[block_index]["text"]
        exec(code, {}, dict(TickerBehaviour=TickerBehaviour))  # nosec
