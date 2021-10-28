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
from random import uniform

import pytest
from aea_ledger_fetchai import FetchAICrypto

from aea import AEA_DIR
from aea.configurations.base import DEFAULT_VERSION
from aea.test_tools.test_cases import AEATestCaseManyFlaky

from packages.fetchai.connections.p2p_libp2p.connection import LIBP2P_SUCCESS_MESSAGE

from tests.conftest import (
    AUTHOR,
    FETCHAI_PRIVATE_KEY_FILE,
    FETCHAI_PRIVATE_KEY_FILE_CONNECTION,
    MAX_FLAKY_RERUNS_INTEGRATION,
    NON_FUNDED_FETCHAI_PRIVATE_KEY_1,
    NON_GENESIS_CONFIG,
    ROOT_DIR,
    wait_for_localhost_ports_to_close,
)
from tests.test_docs.helper import extract_code_blocks


MD_FILE = "docs/skill-guide.md"


@pytest.mark.integration
class TestBuildSkill(AEATestCaseManyFlaky):
    """This class contains the tests for the code-blocks in the skill-guide.md file."""

    capture_log = True

    @classmethod
    def setup_class(cls):
        """Setup the test class."""
        super().setup_class()
        cls.doc_path = os.path.join(ROOT_DIR, MD_FILE)
        cls.code_blocks = extract_code_blocks(filepath=cls.doc_path, filter_="python")

    @pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS_INTEGRATION)
    def test_update_skill_and_run(self):
        """Test that the resource folder contains scaffold handlers.py module."""
        assert self.code_blocks != [], "File must not be empty."

        self.initialize_aea(AUTHOR)

        # generate random location
        location = {
            "latitude": round(uniform(-90, 90), 2),  # nosec
            "longitude": round(uniform(-180, 180), 2),  # nosec
        }

        simple_service_registration_aea = "simple_service_registration"
        self.fetch_agent(
            "fetchai/simple_service_registration:0.31.0",
            simple_service_registration_aea,
        )
        self.set_agent_context(simple_service_registration_aea)
        # add non-funded key
        self.generate_private_key(FetchAICrypto.identifier)
        self.generate_private_key(
            FetchAICrypto.identifier, FETCHAI_PRIVATE_KEY_FILE_CONNECTION
        )
        self.add_private_key(FetchAICrypto.identifier, FETCHAI_PRIVATE_KEY_FILE)
        self.add_private_key(
            FetchAICrypto.identifier,
            FETCHAI_PRIVATE_KEY_FILE_CONNECTION,
            connection=True,
        )
        self.replace_private_key_in_file(
            NON_FUNDED_FETCHAI_PRIVATE_KEY_1, FETCHAI_PRIVATE_KEY_FILE_CONNECTION
        )
        setting_path = "vendor.fetchai.connections.p2p_libp2p.config.ledger_id"
        self.set_config(setting_path, FetchAICrypto.identifier)

        default_routing = {
            "fetchai/oef_search:1.0.0": "fetchai/soef:0.26.0",
        }

        # replace location
        setting_path = "vendor.fetchai.skills.simple_service_registration.models.strategy.args.location"
        self.nested_set_config(setting_path, location)

        search_aea = "search_aea"
        self.create_agents(search_aea)
        self.set_agent_context(search_aea)
        skill_name = "my_search"
        skill_id = AUTHOR + "/" + skill_name + ":" + DEFAULT_VERSION
        self.scaffold_item("skill", skill_name)
        self.add_item("connection", "fetchai/p2p_libp2p:0.25.0")
        self.add_item("connection", "fetchai/soef:0.26.0")
        self.set_config("agent.default_connection", "fetchai/p2p_libp2p:0.25.0")
        setting_path = "agent.default_routing"
        self.nested_set_config(setting_path, default_routing)

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
        yaml_code_block = extract_code_blocks(self.doc_path, filter_="yaml")
        with open(path, "w") as file:
            file.write(yaml_code_block[0])  # block one is yaml

        path = Path(self.t, search_aea, "skills", skill_name, "__init__.py")
        original = Path(AEA_DIR, "skills", "scaffold", "__init__.py")
        assert not filecmp.cmp(path, original)  # the public id gets updated
        with open(path, "w") as file:
            file.write(self.code_blocks[3])  # block four is init

        # update fingerprint
        self.fingerprint_item("skill", skill_id)

        # add keys
        self.generate_private_key(FetchAICrypto.identifier)
        self.generate_private_key(
            FetchAICrypto.identifier, FETCHAI_PRIVATE_KEY_FILE_CONNECTION
        )
        self.add_private_key(FetchAICrypto.identifier, FETCHAI_PRIVATE_KEY_FILE)
        self.add_private_key(
            FetchAICrypto.identifier,
            FETCHAI_PRIVATE_KEY_FILE_CONNECTION,
            connection=True,
        )

        # fund key
        self.generate_wealth(FetchAICrypto.identifier)

        # set p2p configs
        setting_path = "vendor.fetchai.connections.p2p_libp2p.config"
        self.nested_set_config(setting_path, NON_GENESIS_CONFIG)

        # replace location
        setting_path = "skills.{}.behaviours.my_search_behaviour.args.location".format(
            skill_name
        )
        self.nested_set_config(setting_path, location)

        # run agents
        self.set_agent_context(simple_service_registration_aea)
        self.run_cli_command("build", cwd=self._get_cwd())
        self.run_cli_command("issue-certificates", cwd=self._get_cwd())
        simple_service_registration_aea_process = self.run_agent()

        check_strings = (
            "Starting libp2p node...",
            "Connecting to libp2p node...",
            "Successfully connected to libp2p node!",
            LIBP2P_SUCCESS_MESSAGE,
        )
        missing_strings = self.missing_from_output(
            simple_service_registration_aea_process,
            check_strings,
            timeout=30,
            is_terminating=False,
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in simple_service_registration_aea output.".format(
            missing_strings
        )

        self.set_agent_context(search_aea)
        self.run_cli_command("build", cwd=self._get_cwd())
        self.run_cli_command("issue-certificates", cwd=self._get_cwd())
        search_aea_process = self.run_agent()

        check_strings = (
            "Starting libp2p node...",
            "Connecting to libp2p node...",
            "Successfully connected to libp2p node!",
            LIBP2P_SUCCESS_MESSAGE,
        )
        missing_strings = self.missing_from_output(
            search_aea_process, check_strings, timeout=30, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in search_aea output.".format(missing_strings)

        check_strings = (
            "registering agent on SOEF.",
            "registering agent's service on the SOEF.",
            "registering agent's personality genus on the SOEF.",
            "registering agent's personality classification on the SOEF.",
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
