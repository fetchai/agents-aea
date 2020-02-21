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

from ...helper import extract_code_blocks, extract_python_code
from ....conftest import CUR_PATH, ROOT_DIR

MD_FILE = "docs/multiplexer-standalone.md"
BASH_FILE = "test_docs/test_demos/test_carpark/car-park-skills-bash.md"

logger = logging.getLogger(__name__)


class TestCarParkDocs:
    """This class contains the tests for the bash-blocks in the car-park-skills.md file."""

    @classmethod
    def setup_class(cls):
        """Setup the test class."""
        cls.path = os.path.join(ROOT_DIR, MD_FILE)
        cls.code_blocks = extract_code_blocks(file=cls.path, filter="bash")
        path = os.path.join(CUR_PATH, BASH_FILE)
        cls.bash_file = extract_python_code(path)

    def test_code_blocks_exist(self):
        """Test that all the code-blocks exist in the python file."""
        for blocks in self.code_blocks:
            assert (
                blocks in self.bash_file
            ), "Code-block doesn't exist in the python file."
