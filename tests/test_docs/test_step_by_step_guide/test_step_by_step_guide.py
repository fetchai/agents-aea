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

from ..helper import extract_code_blocks
from ...conftest import ROOT_DIR

logger = logging.getLogger(__name__)


class TestDemoDocs:
    """This class contains the tests for the python-blocks in thermometer-skills-step-by-step.md file."""

    @classmethod
    def setup_class(cls):
        """Setup the test class."""
        md_path = os.path.join(ROOT_DIR, "docs", "thermometer-skills-step-by-step.md")
        code_blocks = extract_code_blocks(filepath=md_path, filter="python")
        cls.thermometer = code_blocks[0:11]
        cls.thermometer_client = code_blocks[11 : len(code_blocks)]

    def test_thermometer_skill_behaviour(self):
        """Test behaviours.py of thermometer skill."""
        path = Path(
            os.getcwd(), "packages", "fetchai", "skills", "thermometer", "behaviours.py"
        )
        with open(path, "r") as file:
            python_code = file.read()
            assert self.thermometer[0] in python_code, "Code is not identical."

    def test_thermometer_skill_handler(self):
        """Test handlers.py of thermometer skill."""
        path = Path(
            os.getcwd(), "packages", "fetchai", "skills", "thermometer", "handlers.py"
        )

        with open(path, "r") as file:
            python_code = file.read()
        for code_block in self.thermometer[1:7]:
            assert code_block in python_code, "Code is not identical."

    def test_thermometer_skill_strategy(self):
        """Test strategy.py of thermometer skill."""
        path = Path(
            os.getcwd(), "packages", "fetchai", "skills", "thermometer", "strategy.py"
        )
        with open(path, "r") as file:
            python_code = file.read()

        for code_block in self.thermometer[7:9]:
            assert code_block in python_code, "Code is not identical."

    def test_thermometer_skill_dialogues(self):
        """Test dialogues.py of thermometer skill."""
        path = Path(
            os.getcwd(), "packages", "fetchai", "skills", "thermometer", "dialogues.py"
        )
        with open(path, "r") as file:
            python_code = file.read()
        assert self.thermometer[9] in python_code, "Code is not identical."

    def test_thermometer_skill_data_model(self):
        """Test thermometer_data_model.py of thermometer skill."""
        path = Path(
            os.getcwd(),
            "packages",
            "fetchai",
            "skills",
            "thermometer",
            "thermometer_data_model.py",
        )
        with open(path, "r") as file:
            python_code = file.read()
        assert self.thermometer[10] in python_code, "Code is not identical."

    def test_thermometer_client_skill_behaviour(self):
        """Test that the code blocks exist in the thermometer_client_skill."""
        path = Path(
            os.getcwd(),
            "packages",
            "fetchai",
            "skills",
            "thermometer_client",
            "behaviours.py",
        )
        with open(path, "r") as file:
            python_code = file.read()
            assert self.thermometer_client[0] in python_code, "Code is not identical."

    def test_thermometer_client_skill_handler(self):
        """Test handlers.py of thermometer skill."""
        path = Path(
            os.getcwd(),
            "packages",
            "fetchai",
            "skills",
            "thermometer_client",
            "handlers.py",
        )

        with open(path, "r") as file:
            python_code = file.read()
        for code_block in self.thermometer_client[1:9]:
            assert code_block in python_code, "Code is not identical."

    def test_thermometer_client_skill_strategy(self):
        """Test strategy.py correctness of thermometer client skill."""
        path = Path(
            os.getcwd(),
            "packages",
            "fetchai",
            "skills",
            "thermometer_client",
            "strategy.py",
        )

        with open(path, "r") as file:
            python_code = file.read()
        for code_block in self.thermometer_client[9:13]:
            assert code_block in python_code, "Code is not identical."

    def test_thermometer_client_skill_dialogues(self):
        """Test dialogues.py of thermometer client skill."""
        path = Path(
            os.getcwd(),
            "packages",
            "fetchai",
            "skills",
            "thermometer_client",
            "dialogues.py",
        )
        with open(path, "r") as file:
            python_code = file.read()
            assert self.thermometer_client[13] in python_code, "Code is not identical."
