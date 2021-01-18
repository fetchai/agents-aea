# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2020 Fetch.AI Limited
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

"""This module contains the tests for the code-blocks in thermometer-skills-step-by-step.md file."""

import logging
import os
from pathlib import Path

from tests.conftest import ROOT_DIR
from tests.test_docs.helper import extract_code_blocks


logger = logging.getLogger(__name__)


class TestDemoDocs:
    """This class contains the tests for the python-blocks in thermometer-skills-step-by-step.md file."""

    @classmethod
    def setup_class(cls):
        """Setup the test class."""
        md_path = os.path.join(ROOT_DIR, "docs", "generic-skills-step-by-step.md")
        code_blocks = extract_code_blocks(filepath=md_path, filter_="python")
        cls.generic_seller = code_blocks[0:11]
        cls.generic_buyer = code_blocks[11 : len(code_blocks)]

    def test_generic_seller_skill_behaviour(self):
        """Test behaviours.py of generic_seller skill."""
        path = Path(
            ROOT_DIR, "packages", "fetchai", "skills", "generic_seller", "behaviours.py"
        )
        with open(path, "r") as file:
            python_code = file.read()
            assert self.generic_seller[0] in python_code, "Code is not identical."

    def test_generic_seller_skill_handler(self):
        """Test handlers.py of generic_seller skill."""
        path = Path(
            ROOT_DIR, "packages", "fetchai", "skills", "generic_seller", "handlers.py"
        )

        with open(path, "r") as file:
            python_code = file.read()
        for code_block in self.generic_seller[1:8]:
            assert code_block in python_code, "Code is not identical."

    def test_generic_seller_skill_strategy(self):
        """Test strategy.py of generic_seller skill."""
        path = Path(
            ROOT_DIR, "packages", "fetchai", "skills", "generic_seller", "strategy.py"
        )
        with open(path, "r") as file:
            python_code = file.read()

        for code_block in self.generic_seller[8:10]:
            assert code_block in python_code, "Code is not identical."

    def test_generic_seller_skill_dialogues(self):
        """Test dialogues.py of generic_seller skill."""
        path = Path(
            ROOT_DIR, "packages", "fetchai", "skills", "generic_seller", "dialogues.py"
        )
        with open(path, "r") as file:
            python_code = file.read()
        assert self.generic_seller[10] in python_code, "Code is not identical."

    def test_generic_buyer_skill_behaviour(self):
        """Test that the code blocks exist in the generic_buyer skill."""
        path = Path(
            ROOT_DIR, "packages", "fetchai", "skills", "generic_buyer", "behaviours.py",
        )
        with open(path, "r") as file:
            python_code = file.read()
            assert self.generic_buyer[0] in python_code, "Code is not identical."

    def test_generic_buyer_skill_handler(self):
        """Test handlers.py of generic_buyer skill."""
        path = Path(
            ROOT_DIR, "packages", "fetchai", "skills", "generic_buyer", "handlers.py",
        )

        with open(path, "r") as file:
            python_code = file.read()
        for code_block in self.generic_buyer[1:9]:
            assert code_block in python_code, "Code is not identical."

    def test_generic_buyer_skill_strategy(self):
        """Test strategy.py correctness of generic_buyer skill."""
        path = Path(
            ROOT_DIR, "packages", "fetchai", "skills", "generic_buyer", "strategy.py",
        )

        with open(path, "r") as file:
            python_code = file.read()
        for code_block in self.generic_buyer[9:13]:
            assert code_block in python_code, "Code is not identical."

    def test_generic_buyer_skill_dialogues(self):
        """Test dialogues.py of generic_buyer skill."""
        path = Path(
            ROOT_DIR, "packages", "fetchai", "skills", "generic_buyer", "dialogues.py",
        )
        with open(path, "r") as file:
            python_code = file.read()
            assert self.generic_buyer[13] in python_code, "Code is not identical."
