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

"""This module contains the tests for the code-blocks in the skill-guide.md file."""

import logging
import os
import shutil
import signal
import sys
import time

from ..helper import extract_code_blocks
import filecmp
import json
import subprocess  # nosec
import tempfile
from pathlib import Path

import jsonschema
from jsonschema import Draft4Validator

from aea import AEA_DIR
from aea.cli import cli

from ...common.click_testing import CliRunner
from ...conftest import (
    CLI_LOG_OPTION,
    CONFIGURATION_SCHEMA_DIR,
    ROOT_DIR,
    SKILL_CONFIGURATION_SCHEMA,
)

MD_FILE = "docs/skill-guide.md"

logger = logging.getLogger(__name__)


class TestBuildSkill:
    """This class contains the tests for the code-blocks in the skill-guide.md file."""

    @classmethod
    def setup_class(cls):
        """Setup the test class."""
        cls.path = os.path.join(ROOT_DIR, MD_FILE)
        cls.code_blocks = extract_code_blocks(file=cls.path, filter="python")
        cls.runner = CliRunner()
        cls.agent_name = "myagent"
        cls.resource_name = "my_search"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()

        cls.schema = json.load(open(SKILL_CONFIGURATION_SCHEMA))
        cls.resolver = jsonschema.RefResolver(
            "file://{}/".format(Path(CONFIGURATION_SCHEMA_DIR).absolute()), cls.schema
        )
        cls.validator = Draft4Validator(cls.schema, resolver=cls.resolver)

        os.chdir(cls.t)
        result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "create", cls.agent_name], standalone_mode=False
        )
        assert result.exit_code == 0
        os.chdir(cls.agent_name)
        # scaffold skill
        cls.result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "scaffold", "skill", cls.resource_name],
            standalone_mode=False,
        )

    def test_read_md_file(self):
        assert (
            self.code_blocks != []
        ), "File must not be empty."

    def test_update_skill_and_run(self):
        """Test that the resource folder contains scaffold handlers.py module."""

        path = Path(self.t, self.agent_name, "skills", self.resource_name, "behaviours.py")
        original = Path(AEA_DIR, "skills", "scaffold", "behaviours.py")
        assert filecmp.cmp(path, original)
        with open(path, "w") as file:
            file.write(self.code_blocks[0])

        path = Path(self.t, self.agent_name, "skills", self.resource_name, "handlers.py")
        original = Path(AEA_DIR, "skills", "scaffold", "handlers.py")
        assert filecmp.cmp(path, original)
        with open(path, "w") as file:
            file.write(self.code_blocks[1])

        path = Path(self.t, self.agent_name, "skills", self.resource_name, "tasks.py")
        with open(path, "w+") as file:
            file.write(self.code_blocks[2])

        # Update the yaml file.
        path = Path(self.t, self.agent_name, "skills", self.resource_name, "skill.yaml")
        yaml_code_block = extract_code_blocks(self.path, filter='yaml')
        with open(path, 'w') as file:
            file.write(yaml_code_block[0])

        # run the agent
        process_one = subprocess.Popen(  # nosec
            [
                sys.executable,
                "-m",
                "aea.cli",
                "run",
                "--connections",
                "fetchai/oef:0.1.0",
            ],
            stdout=subprocess.PIPE,
            env=os.environ.copy(),
        )

        time.sleep(20.0)
        process_one.send_signal(signal.SIGINT)
        process_one.wait(timeout=20)

        poll_one = process_one.poll()
        if poll_one is None:
            process_one.terminate()
            process_one.wait(2)

    @classmethod
    def teardown_class(cls):
        """Teardowm the test."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass
