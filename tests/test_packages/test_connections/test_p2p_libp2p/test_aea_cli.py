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

"""This test module contains AEA cli tests for P2PLibp2p connection."""

import pytest

from aea.test_tools.test_cases import AEATestCaseEmpty

from ....conftest import MAX_FLAKY_RERUNS, skip_test_windows

DEFAULT_PORT = 10234
DEFAULT_DELEGATE_PORT = 11234
DEFAULT_NET_SIZE = 4

DEFAULT_LAUNCH_TIMEOUT = 25


@skip_test_windows
class SkipTestP2PLibp2pConnectionAEARunningDefaultConfigNode(AEATestCaseEmpty):
    """Test AEA with p2p_libp2p connection is correctly run"""

    @pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)  # cause to investigate
    def test_agent(self):
        self.add_item("connection", "fetchai/p2p_libp2p:0.2.0")
        self.set_config(
            "agent.default_connection", "fetchai/p2p_libp2p:0.2.0"
        )  # TOFIX(LR) not sure is needed

        process = self.run_agent()

        is_running = self.is_running(process, timeout=DEFAULT_LAUNCH_TIMEOUT)
        assert is_running, "AEA not running within timeout!"

        check_strings = "My libp2p addresses: ["
        missing_strings = self.missing_from_output(process, check_strings)
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in agent output.".format(missing_strings)

        self.terminate_agents(process)
        assert self.is_successfully_terminated(
            process
        ), "AEA wasn't successfully terminated."


@skip_test_windows
class SkipTestP2PLibp2pConnectionAEARunningFullNode(AEATestCaseEmpty):
    """Test AEA with p2p_libp2p connection is correctly run"""

    @pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)  # cause to investigate
    def test_agent(self):
        self.add_item("connection", "fetchai/p2p_libp2p:0.2.0")

        # setup a full node: with public uri, relay service, and delegate service
        config_path = "vendor.fetchai.connections.p2p_libp2p.config"
        self.set_config(
            "{}.local_uri".format(config_path), "127.0.0.1:{}".format(DEFAULT_PORT)
        )
        self.set_config(
            "{}.public_uri".format(config_path), "127.0.0.1:{}".format(DEFAULT_PORT)
        )
        self.set_config(
            "{}.delegate_uri".format(config_path),
            "127.0.0.1:{}".format(DEFAULT_DELEGATE_PORT),
        )

        process = self.run_agent()

        is_running = self.is_running(process, timeout=DEFAULT_LAUNCH_TIMEOUT)
        assert is_running, "AEA not running within timeout!"

        check_strings = "My libp2p addresses: ['/dns4/"
        missing_strings = self.missing_from_output(process, check_strings)
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in agent output.".format(missing_strings)

        self.terminate_agents(process)
        assert self.is_successfully_terminated(
            process
        ), "AEA wasn't successfully terminated."
