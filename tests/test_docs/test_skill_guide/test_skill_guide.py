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

import filecmp
import os
from pathlib import Path

from aea import AEA_DIR
from aea.configurations.base import DEFAULT_VERSION
from aea.test_tools.test_cases import AEATestCaseMany, UseOef

from ..helper import extract_code_blocks
from ...conftest import (
    AUTHOR,
    ROOT_DIR,
)

MD_FILE = "docs/skill-guide.md"


class TestBuildSkill(AEATestCaseMany, UseOef):
    """This class contains the tests for the code-blocks in the skill-guide.md file."""

    @classmethod
    def setup_class(cls):
        """Setup the test class."""
        AEATestCaseMany.setup_class()
        cls.doc_path = os.path.join(ROOT_DIR, MD_FILE)
        cls.code_blocks = extract_code_blocks(filepath=cls.doc_path, filter="python")

    def test_read_md_file(self):
        """Teat that the md file is not empty."""
        assert self.code_blocks != [], "File must not be empty."

    def test_update_skill_and_run(self):
        """Test that the resource folder contains scaffold handlers.py module."""
        self.initialize_aea(AUTHOR)

        simple_service_registration_aea = "simple_service_registration"
        self.fetch_agent(
            "fetchai/simple_service_registration:0.4.0", simple_service_registration_aea
        )

        search_aea = "search_aea"
        self.create_agents(search_aea)
        self.set_agent_context(search_aea)
        skill_name = "my_search"
        skill_id = AUTHOR + "/" + skill_name + ":" + DEFAULT_VERSION
        self.scaffold_item("skill", skill_name)
        self.add_item("connection", "fetchai/oef:0.3.0")
        self.set_config("agent.default_connection", "fetchai/oef:0.3.0")

        # manually change the files:
        path = Path(self.t, search_aea, "skills", skill_name, "behaviours.py")
        original = Path(AEA_DIR, "skills", "scaffold", "behaviours.py")
        assert filecmp.cmp(path, original)
        with open(path, "w") as file:
            file.write(self.code_blocks[0])  # block one is behaviour

        path = Path(self.t, search_aea, "skills", skill_name, "handlers.py")
        original = Path(AEA_DIR, "skills", "scaffold", "handlers.py")
        assert filecmp.cmp(path, original)
        with open(path, "w") as file:
            file.write(self.code_blocks[1])  # block two is handler

        path = Path(self.t, search_aea, "skills", skill_name, "my_model.py")
        os.remove(path)

        path = Path(self.t, search_aea, "skills", skill_name, "skill.yaml")
        yaml_code_block = extract_code_blocks(self.doc_path, filter="yaml")
        with open(path, "w") as file:
            file.write(yaml_code_block[0])  # block one is yaml

        # update fingerprint
        self.fingerprint_item("skill", skill_id)

        # run agents
        self.set_agent_context(simple_service_registration_aea)
        simple_service_registration_aea_process = self.run_agent(
            "--connections", "fetchai/oef:0.3.0"
        )

        self.set_agent_context(search_aea)
        search_aea_process = self.run_agent("--connections", "fetchai/oef:0.3.0")

        check_strings = (
            "updating services on OEF service directory.",
            "unregistering services from OEF service directory.",
        )
        missing_strings = self.missing_from_output(
            simple_service_registration_aea_process,
            check_strings,
            is_terminating=False,
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in simple_service_registration_aea output.".format(
            missing_strings
        )

        check_strings = (
            "sending search request to OEF search node, search_count=",
            "number of search requests sent=",
            "found number of agents=1, received search count=",
        )
        missing_strings = self.missing_from_output(
            search_aea_process, check_strings, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in search_aea output.".format(missing_strings)

        self.terminate_agents(
            simple_service_registration_aea_process, search_aea_process
        )
        assert (
            self.is_successfully_terminated()
        ), "Agents weren't successfully terminated."
