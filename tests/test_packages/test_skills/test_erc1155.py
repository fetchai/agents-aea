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
"""This test module contains the integration test for the generic buyer and seller skills."""

import pytest

from aea.test_tools.test_cases import AEATestCaseMany, UseOef

from tests.conftest import (
    ETHEREUM,
    ETHEREUM_PRIVATE_KEY_FILE,
    FUNDED_ETH_PRIVATE_KEY_1,
    FUNDED_ETH_PRIVATE_KEY_2,
    MAX_FLAKY_RERUNS_ETH,
)


class TestERCSkillsEthereumLedger(AEATestCaseMany, UseOef):
    """Test that erc1155 skills work."""

    @pytest.mark.integration
    @pytest.mark.ledger
    @pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS_ETH)  # cause possible network issues
    def test_generic(self):
        """Run the generic skills sequence."""
        deploy_aea_name = "deploy_aea"
        client_aea_name = "client_aea"

        self.create_agents(deploy_aea_name, client_aea_name)

        # add ethereum ledger in both configuration files
        default_routing = {
            "fetchai/ledger_api:0.1.0": "fetchai/ledger:0.2.0",
            "fetchai/contract_api:0.1.0": "fetchai/ledger:0.2.0",
        }

        # add packages for agent one
        self.set_agent_context(deploy_aea_name)
        self.add_item("connection", "fetchai/p2p_libp2p:0.5.0")
        self.add_item("connection", "fetchai/ledger:0.2.0")
        self.set_config("agent.default_connection", "fetchai/p2p_libp2p:0.5.0")
        self.set_config("agent.default_ledger", ETHEREUM)
        setting_path = "agent.default_routing"
        self.force_set_config(setting_path, default_routing)
        self.add_item("skill", "fetchai/erc1155_deploy:0.9.0")

        diff = self.difference_to_fetched_agent(
            "fetchai/erc1155_deployer:0.9.0", deploy_aea_name
        )
        assert (
            diff == []
        ), "Difference between created and fetched project for files={}".format(diff)

        self.generate_private_key(ETHEREUM)
        self.add_private_key(ETHEREUM, ETHEREUM_PRIVATE_KEY_FILE)
        self.replace_private_key_in_file(
            FUNDED_ETH_PRIVATE_KEY_1, ETHEREUM_PRIVATE_KEY_FILE
        )
        # stdout = self.get_wealth(ETHEREUM)
        # if int(stdout) < 100000000000000000:
        #     pytest.skip("The agent needs more funds for the test to pass.")
        self.run_install()

        # add packages for agent two
        self.set_agent_context(client_aea_name)
        self.add_item("connection", "fetchai/p2p_libp2p:0.5.0")
        self.add_item("connection", "fetchai/ledger:0.2.0")
        self.set_config("agent.default_connection", "fetchai/p2p_libp2p:0.5.0")
        self.set_config("agent.default_ledger", ETHEREUM)
        setting_path = "agent.default_routing"
        self.force_set_config(setting_path, default_routing)
        self.add_item("skill", "fetchai/erc1155_client:0.8.0")

        diff = self.difference_to_fetched_agent(
            "fetchai/erc1155_client:0.9.0", client_aea_name
        )
        assert (
            diff == []
        ), "Difference between created and fetched project for files={}".format(diff)

        self.generate_private_key(ETHEREUM)
        self.add_private_key(ETHEREUM, ETHEREUM_PRIVATE_KEY_FILE)
        self.replace_private_key_in_file(
            FUNDED_ETH_PRIVATE_KEY_2, ETHEREUM_PRIVATE_KEY_FILE
        )
        # stdout = self.get_wealth(ETHEREUM)
        # if int(stdout) < 100000000000000000:
        #     pytest.skip("The agent needs more funds for the test to pass.")
        self.run_install()

        # run agents
        self.set_agent_context(deploy_aea_name)
        deploy_aea_process = self.run_agent()

        check_strings = (
            "starting balance on ethereum ledger=",
            "received raw transaction=",
            "proposing the transaction to the decision maker. Waiting for confirmation ...",
            "transaction signing was successful.",
            "sending transaction to ledger.",
            "transaction was successfully submitted. Transaction digest=",
            "requesting transaction receipt.",
            "transaction was successfully settled. Transaction receipt=",
            "Requesting create batch transaction...",
            "Requesting mint batch transaction...",
        )
        missing_strings = self.missing_from_output(
            deploy_aea_process, check_strings, timeout=420, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in deploy_aea output.".format(missing_strings)

        self.set_agent_context(client_aea_name)
        client_aea_process = self.run_agent()

        check_strings = (
            "Sending PROPOSE to agent=",
            "received ACCEPT_W_INFORM from sender=",
            "Requesting single atomic swap transaction...",
            "received raw transaction=",
            "proposing the transaction to the decision maker. Waiting for confirmation ...",
            "transaction signing was successful.",
            "sending transaction to ledger.",
            "transaction was successfully submitted. Transaction digest=",
            "requesting transaction receipt.",
            "transaction was successfully settled. Transaction receipt=",
            "Demo finished!",
        )
        missing_strings = self.missing_from_output(
            deploy_aea_process, check_strings, timeout=360, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in deploy_aea output.".format(missing_strings)

        check_strings = (
            "found agents=",
            "sending CFP to agent=",
            "received valid PROPOSE from sender=",
            "requesting single hash message from contract api...",
            "received raw message=",
            "proposing the transaction to the decision maker. Waiting for confirmation ...",
            "sending ACCEPT_W_INFORM to agent=",
        )
        missing_strings = self.missing_from_output(
            client_aea_process, check_strings, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in client_aea output.".format(missing_strings)

        self.terminate_agents(deploy_aea_process, client_aea_process)
        assert (
            self.is_successfully_terminated()
        ), "Agents weren't successfully terminated."
