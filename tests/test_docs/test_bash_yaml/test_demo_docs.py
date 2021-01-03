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

import logging
import os
from pathlib import Path

from tests.conftest import ROOT_DIR
from tests.test_docs.helper import extract_code_blocks


logger = logging.getLogger(__name__)


class TestDemoDocs:
    """This class contains the tests for the bash/yaml-blocks in *.md file."""

    BASH_DIR_PATH = Path(ROOT_DIR, "tests", "test_docs", "test_bash_yaml", "md_files")

    def _test_blocks(self, filename: str, filter_: str):
        """Test code blocks of a certain type determined by 'filter_' param."""
        bash_file = Path(self.BASH_DIR_PATH, filename).read_text(encoding="utf-8")
        md_path = os.path.join(ROOT_DIR, "docs", filename.replace("bash-", ""))

        bash_code_blocks = extract_code_blocks(filepath=md_path, filter_=filter_)
        for blocks in bash_code_blocks:
            assert blocks in bash_file, "[{}]: FAILED. Code must be identical".format(
                filename
            )
        logger.info(
            f"[{filename}]: PASSED. Tested {len(bash_code_blocks)} '{filter_}' blocks."
        )

    def test_code_blocks_exist(self):
        """Test that all the code-blocks exist in the python file."""
        logger.info(os.listdir(self.BASH_DIR_PATH))
        for file in os.listdir(self.BASH_DIR_PATH):
            if not file.endswith(".md"):
                continue
            # in the future, we might add other filters like "python"
            self._test_blocks(file, "bash")
            self._test_blocks(file, "yaml")
