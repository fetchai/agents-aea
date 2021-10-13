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

"""This test module contains the integration test for the fetch beacon skill."""

import pytest

from aea.test_tools.test_cases import AEATestCaseEmpty


@pytest.mark.integration
class TestFetchBeaconSkill(AEATestCaseEmpty):
    """Test that fetch beacon skill works."""

    def test_fetch_beacon(self):
        """Run the fetch beacon skill sequence."""
        self.generate_private_key()
        self.add_private_key()
        self.add_item("connection", "fetchai/ledger:0.19.0")
        self.add_item("skill", "fetchai/fetch_beacon:0.12.0")
        self.set_config("agent.default_connection", "fetchai/ledger:0.19.0")

        self.run_install()

        process = self.run_agent()
        is_running = self.is_running(process)
        assert is_running, "AEA not running within timeout!"

        check_strings = (
            "setting up FetchBeaconBehaviour",
            "Fetching random beacon value...",
            "Beacon info:",
            "entropy not present",
        )
        missing_strings = self.missing_from_output(process, check_strings)
        assert len(missing_strings) in [
            0,
            1,
        ], "Strings {} didn't appear in agent output.".format(missing_strings)

        self.terminate_agents()
        assert (
            self.is_successfully_terminated()
        ), "Http echo agent wasn't successfully terminated."
