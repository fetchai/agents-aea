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

import pytest

from aea import AEA_DIR
from aea.configurations.base import DEFAULT_VERSION
from aea.test_tools.test_cases import AEATestCaseMany

from tests.conftest import (
    AUTHOR,
    COSMOS,
    COSMOS_PRIVATE_KEY_FILE,
    FUNDED_COSMOS_PRIVATE_KEY_1,
    MAX_FLAKY_RERUNS_INTEGRATION,
    NON_FUNDED_COSMOS_PRIVATE_KEY_1,
    NON_GENESIS_CONFIG,
    ROOT_DIR,
    wait_for_localhost_ports_to_close,
)
from tests.test_docs.helper import extract_code_blocks


MD_FILE = "docs/skill-guide.md"


@pytest.mark.integration
class TestBuildSkill(AEATestCaseMany):
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

    @pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS_INTEGRATION)
    def test_update_skill_and_run(self):
        """Test that the resource folder contains scaffold handlers.py module."""
        self.initialize_aea(AUTHOR)

        simple_service_registration_aea = "simple_service_registration"
        self.fetch_agent(
            "fetchai/simple_service_registration:0.8.0", simple_service_registration_aea
        )
        self.set_agent_context(simple_service_registration_aea)
        # add non-funded key
        self.generate_private_key(COSMOS)
        self.add_private_key(COSMOS, COSMOS_PRIVATE_KEY_FILE)
        self.add_private_key(COSMOS, COSMOS_PRIVATE_KEY_FILE, connection=True)
        self.replace_private_key_in_file(
            NON_FUNDED_COSMOS_PRIVATE_KEY_1, COSMOS_PRIVATE_KEY_FILE
        )

        default_routing = {
            "fetchai/oef_search:0.3.0": "fetchai/soef:0.5.0",
        }

        search_aea = "search_aea"
        self.create_agents(search_aea)
        self.set_agent_context(search_aea)
        skill_name = "my_search"
        skill_id = AUTHOR + "/" + skill_name + ":" + DEFAULT_VERSION
        self.scaffold_item("skill", skill_name)
        self.add_item("connection", "fetchai/p2p_libp2p:0.5.0")
        self.add_item("connection", "fetchai/soef:0.5.0")
        self.set_config("agent.default_connection", "fetchai/p2p_libp2p:0.5.0")
        setting_path = "agent.default_routing"
        self.force_set_config(setting_path, default_routing)

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
        original = Path(AEA_DIR, "skills", "scaffold", "my_model.py")
        assert filecmp.cmp(path, original)
        with open(path, "w") as file:
            file.write(self.code_blocks[2])  # block three is dialogues

        path_new = Path(self.t, search_aea, "skills", skill_name, "dialogues.py")
        os.rename(path, path_new)

        path = Path(self.t, search_aea, "skills", skill_name, "skill.yaml")
        yaml_code_block = extract_code_blocks(self.doc_path, filter="yaml")
        with open(path, "w") as file:
            file.write(yaml_code_block[0])  # block one is yaml

        # update fingerprint
        self.fingerprint_item("skill", skill_id)

        # add funded key
        self.generate_private_key(COSMOS)
        self.add_private_key(COSMOS, COSMOS_PRIVATE_KEY_FILE)
        self.add_private_key(COSMOS, COSMOS_PRIVATE_KEY_FILE, connection=True)
        self.replace_private_key_in_file(
            FUNDED_COSMOS_PRIVATE_KEY_1, COSMOS_PRIVATE_KEY_FILE
        )
        setting_path = "vendor.fetchai.connections.p2p_libp2p.config"
        self.force_set_config(setting_path, NON_GENESIS_CONFIG)

        # run agents
        self.set_agent_context(simple_service_registration_aea)
        simple_service_registration_aea_process = self.run_agent()

        check_strings = (
            "Downloading golang dependencies. This may take a while...",
            "Finished downloading golang dependencies.",
            "Starting libp2p node...",
            "Connecting to libp2p node...",
            "Successfully connected to libp2p node!",
            "My libp2p addresses:",
        )
        missing_strings = self.missing_from_output(
            simple_service_registration_aea_process,
            check_strings,
            timeout=240,
            is_terminating=False,
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in simple_service_registration_aea output.".format(
            missing_strings
        )

        self.set_agent_context(search_aea)
        search_aea_process = self.run_agent()

        check_strings = (
            "Downloading golang dependencies. This may take a while...",
            "Finished downloading golang dependencies.",
            "Starting libp2p node...",
            "Connecting to libp2p node...",
            "Successfully connected to libp2p node!",
            "My libp2p addresses:",
        )
        missing_strings = self.missing_from_output(
            search_aea_process, check_strings, timeout=240, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in search_aea output.".format(missing_strings)

        check_strings = (
            "registering agent on SOEF.",
            "registering service on SOEF.",
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
        wait_for_localhost_ports_to_close([9000, 9001])
