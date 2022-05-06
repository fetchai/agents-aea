# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2022 Fetch.AI Limited
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

"""This test module contains the integration test for the fetch block skill."""

import pytest

from aea.test_tools.test_cases import AEATestCaseEmpty


@pytest.mark.integration
class TestFetchBlockSkill(AEATestCaseEmpty):
    """Test that fetch block skill works."""

    def test_fetch_block(self):
        """Run the fetch block skill sequence."""
        self.generate_private_key()
        self.add_private_key()
        self.add_item("connection", "fetchai/ledger:0.21.0")
        self.add_item("skill", "fetchai/fetch_block:0.12.1")
        self.set_config("agent.default_connection", "fetchai/ledger:0.21.0")

        self.run_install()

        process = self.run_agent()
        is_running = self.is_running(process)
        assert is_running, "AEA not running within timeout!"

        check_strings = (
            "setting up FetchBlockBehaviour",
            "Fetching latest block...",
            "Retrieved latest block:",
        )
        missing_strings = self.missing_from_output(process, check_strings)
        assert len(missing_strings) in [
            0,
            1,
        ], "Strings {} didn't appear in agent output.".format(missing_strings)

        self.terminate_agents()
        assert self.is_successfully_terminated(), "AEA wasn't successfully terminated."
