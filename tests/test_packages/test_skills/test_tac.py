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
"""This test module contains the integration test for the tac skills."""

import datetime

import pytest

from aea.test_tools.test_cases import AEATestCaseMany

from tests.conftest import (
    COSMOS,
    COSMOS_PRIVATE_KEY_FILE_CONNECTION,
    ETHEREUM,
    ETHEREUM_PRIVATE_KEY_FILE,
    FETCHAI,
    FETCHAI_PRIVATE_KEY_FILE,
    FUNDED_ETH_PRIVATE_KEY_1,
    FUNDED_ETH_PRIVATE_KEY_2,
    FUNDED_ETH_PRIVATE_KEY_3,
    MAX_FLAKY_RERUNS_ETH,
    MAX_FLAKY_RERUNS_INTEGRATION,
    NON_FUNDED_COSMOS_PRIVATE_KEY_1,
    NON_GENESIS_CONFIG,
    NON_GENESIS_CONFIG_TWO,
)


class TestTacSkills(AEATestCaseMany):
    """Test that tac skills work."""

    @pytest.mark.integration
    @pytest.mark.flaky(
        reruns=MAX_FLAKY_RERUNS_INTEGRATION
    )  # cause possible network issues
    def test_tac(self):
        """Run the tac skills sequence."""
        tac_aea_one = "tac_participant_one"
        tac_aea_two = "tac_participant_two"
        tac_controller_name = "tac_controller"

        # create tac controller, agent one and agent two
        self.create_agents(
            tac_aea_one, tac_aea_two, tac_controller_name,
        )

        default_routing = {
            "fetchai/oef_search:0.5.0": "fetchai/soef:0.7.0",
        }

        # prepare tac controller for test
        self.set_agent_context(tac_controller_name)
        self.add_item("connection", "fetchai/p2p_libp2p:0.8.0")
        self.set_config("agent.default_connection", "fetchai/p2p_libp2p:0.8.0")
        self.add_item("connection", "fetchai/soef:0.7.0")
        self.add_item("skill", "fetchai/tac_control:0.6.0")
        self.set_config("agent.default_ledger", FETCHAI)
        setting_path = "agent.default_routing"
        self.force_set_config(setting_path, default_routing)
        self.run_install()

        diff = self.difference_to_fetched_agent(
            "fetchai/tac_controller:0.8.0", tac_controller_name
        )
        assert (
            diff == []
        ), "Difference between created and fetched project for files={}".format(diff)

        # add keys
        self.generate_private_key(FETCHAI)
        self.generate_private_key(COSMOS, COSMOS_PRIVATE_KEY_FILE_CONNECTION)
        self.add_private_key(FETCHAI, FETCHAI_PRIVATE_KEY_FILE)
        self.add_private_key(
            COSMOS, COSMOS_PRIVATE_KEY_FILE_CONNECTION, connection=True
        )
        self.replace_private_key_in_file(
            NON_FUNDED_COSMOS_PRIVATE_KEY_1, COSMOS_PRIVATE_KEY_FILE_CONNECTION
        )
        setting_path = "vendor.fetchai.connections.p2p_libp2p.config.ledger_id"
        self.force_set_config(setting_path, COSMOS)

        default_routing = {
            "fetchai/ledger_api:0.3.0": "fetchai/ledger:0.4.0",
            "fetchai/oef_search:0.5.0": "fetchai/soef:0.7.0",
        }

        # prepare agents for test
        for agent_name, config in (
            (tac_aea_one, NON_GENESIS_CONFIG),
            (tac_aea_two, NON_GENESIS_CONFIG_TWO),
        ):
            self.set_agent_context(agent_name)
            self.add_item("connection", "fetchai/p2p_libp2p:0.8.0")
            self.set_config("agent.default_connection", "fetchai/p2p_libp2p:0.8.0")
            self.add_item("connection", "fetchai/soef:0.7.0")
            self.add_item("connection", "fetchai/ledger:0.4.0")
            self.add_item("skill", "fetchai/tac_participation:0.7.0")
            self.add_item("skill", "fetchai/tac_negotiation:0.8.0")
            self.set_config("agent.default_ledger", FETCHAI)
            setting_path = "agent.default_routing"
            self.force_set_config(setting_path, default_routing)
            self.run_install()
            diff = self.difference_to_fetched_agent(
                "fetchai/tac_participant:0.9.0", agent_name
            )
            assert (
                diff == []
            ), "Difference between created and fetched project for files={}".format(
                diff
            )

            # add keys
            self.generate_private_key(FETCHAI)
            self.generate_private_key(COSMOS, COSMOS_PRIVATE_KEY_FILE_CONNECTION)
            self.add_private_key(FETCHAI, FETCHAI_PRIVATE_KEY_FILE)
            self.add_private_key(
                COSMOS, COSMOS_PRIVATE_KEY_FILE_CONNECTION, connection=True
            )

            # set p2p configs
            setting_path = "vendor.fetchai.connections.p2p_libp2p.config"
            self.force_set_config(setting_path, config)
            setting_path = "vendor.fetchai.connections.p2p_libp2p.config.ledger_id"
            self.force_set_config(setting_path, COSMOS)

        # run tac controller
        self.set_agent_context(tac_controller_name)
        now = datetime.datetime.now().strftime("%d %m %Y %H:%M")
        now_min = datetime.datetime.strptime(now, "%d %m %Y %H:%M")
        fut = now_min + datetime.timedelta(0, 120)
        start_time = fut.strftime("%d %m %Y %H:%M")
        setting_path = (
            "vendor.fetchai.skills.tac_control.models.parameters.args.start_time"
        )
        self.set_config(setting_path, start_time)
        tac_controller_process = self.run_agent()

        check_strings = (
            "Downloading golang dependencies. This may take a while...",
            "Finished downloading golang dependencies.",
            "Starting libp2p node...",
            "Connecting to libp2p node...",
            "Successfully connected to libp2p node!",
            "My libp2p addresses:",
        )
        missing_strings = self.missing_from_output(
            tac_controller_process, check_strings, timeout=240, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in tac_controller output.".format(missing_strings)

        # run two agents (participants)
        self.set_agent_context(tac_aea_one)
        tac_aea_one_process = self.run_agent()

        self.set_agent_context(tac_aea_two)
        tac_aea_two_process = self.run_agent()

        check_strings = (
            "Downloading golang dependencies. This may take a while...",
            "Finished downloading golang dependencies.",
            "Starting libp2p node...",
            "Connecting to libp2p node...",
            "Successfully connected to libp2p node!",
            "My libp2p addresses:",
        )
        missing_strings = self.missing_from_output(
            tac_aea_one_process, check_strings, timeout=240, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in tac_aea_one output.".format(missing_strings)

        check_strings = (
            "Downloading golang dependencies. This may take a while...",
            "Finished downloading golang dependencies.",
            "Starting libp2p node...",
            "Connecting to libp2p node...",
            "Successfully connected to libp2p node!",
            "My libp2p addresses:",
        )
        missing_strings = self.missing_from_output(
            tac_aea_two_process, check_strings, timeout=240, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in tac_aea_two output.".format(missing_strings)

        check_strings = (
            "registering agent on SOEF.",
            "registering TAC data model on SOEF.",
            "TAC open for registration until:",
            "agent registered: 'tac_participant_one'",
            "agent registered: 'tac_participant_two'",
            "started competition:",
            "unregistering TAC data model from SOEF.",
            "handling valid transaction:",
            "Current good & money allocation & score: ",
        )
        missing_strings = self.missing_from_output(
            tac_controller_process, check_strings, timeout=240, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in tac_controller output.".format(missing_strings)

        check_strings = (
            "searching for TAC, search_id=",
            "found the TAC controller. Registering...",
            "received start event from the controller. Starting to compete...",
            "registering agent on SOEF.",
            "searching for sellers, search_id=",
            "searching for buyers, search_id=",
            "found potential sellers agents=",
            "sending CFP to agent=",
            "accepting propose",
            "sending signing_msg=",
            "message signed by decision maker.",
            "sending transaction to controller.",
            "sending match accept to",
            # "Received transaction confirmation from the controller: transaction_id=", # noqa: E800
            "Applying state update!",
            "found potential buyers agents=",
            "sending CFP to agent=",
            "declining propose",
        )
        missing_strings = self.missing_from_output(
            tac_aea_one_process, check_strings, timeout=240, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in tac_aea_one output.".format(missing_strings)

        # Note, we do not need to check std output of the other participant as it is implied

        self.terminate_agents(
            tac_controller_process, tac_aea_one_process, tac_aea_two_process
        )
        assert (
            self.is_successfully_terminated()
        ), "Agents weren't successfully terminated."


@pytest.mark.ledger
class TestTacSkillsContract(AEATestCaseMany):
    """Test that tac skills work."""

    @pytest.mark.unstable
    @pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS_ETH)  # cause possible network issues
    def test_tac(self):
        """Run the tac skills sequence."""
        tac_aea_one = "tac_participant_one"
        tac_aea_two = "tac_participant_two"
        tac_controller_name = "tac_controller"

        # create tac controller, agent one and agent two
        self.create_agents(
            tac_aea_one, tac_aea_two, tac_controller_name,
        )

        # prepare tac controller for test
        self.set_agent_context(tac_controller_name)
        self.add_item("connection", "fetchai/p2p_libp2p:0.8.0")
        self.set_config("agent.default_connection", "fetchai/p2p_libp2p:0.8.0")
        self.add_item("skill", "fetchai/tac_control_contract:0.7.0")
        self.set_config("agent.default_ledger", ETHEREUM)
        self.run_install()

        diff = self.difference_to_fetched_agent(
            "fetchai/tac_controller_contract:0.9.0", tac_controller_name
        )
        assert (
            diff == []
        ), "Difference between created and fetched project for files={}".format(diff)

        self.generate_private_key(ETHEREUM)
        self.add_private_key(ETHEREUM, ETHEREUM_PRIVATE_KEY_FILE)
        self.replace_private_key_in_file(
            FUNDED_ETH_PRIVATE_KEY_1, ETHEREUM_PRIVATE_KEY_FILE
        )

        # prepare agents for test
        for agent_name, eth_private_key in zip(
            (tac_aea_one, tac_aea_two),
            (FUNDED_ETH_PRIVATE_KEY_2, FUNDED_ETH_PRIVATE_KEY_3),
        ):
            self.set_agent_context(agent_name)
            self.add_item("connection", "fetchai/p2p_libp2p:0.8.0")
            self.set_config("agent.default_connection", "fetchai/p2p_libp2p:0.8.0")
            self.add_item("skill", "fetchai/tac_participation:0.7.0")
            self.add_item("skill", "fetchai/tac_negotiation:0.8.0")
            self.set_config("agent.default_ledger", ETHEREUM)
            self.set_config(
                "vendor.fetchai.skills.tac_participation.models.game.args.is_using_contract",
                True,
                "bool",
            )
            self.set_config(
                "vendor.fetchai.skills.tac_negotiation.models.strategy.args.is_contract_tx",
                True,
                "bool",
            )
            self.run_install()
            diff = self.difference_to_fetched_agent(
                "fetchai/tac_participant:0.9.0", agent_name
            )
            assert (
                diff == []
            ), "Difference between created and fetched project for files={}".format(
                diff
            )
            self.generate_private_key(ETHEREUM)
            self.add_private_key(ETHEREUM, ETHEREUM_PRIVATE_KEY_FILE)
            self.replace_private_key_in_file(eth_private_key, ETHEREUM_PRIVATE_KEY_FILE)

        # run tac controller
        self.set_agent_context(tac_controller_name)
        now = datetime.datetime.now().strftime("%d %m %Y %H:%M")
        now_min = datetime.datetime.strptime(now, "%d %m %Y %H:%M")
        fut = now_min + datetime.timedelta(0, 360)
        start_time = fut.strftime("%d %m %Y %H:%M")
        setting_path = "vendor.fetchai.skills.tac_control_contract.models.parameters.args.start_time"
        self.set_config(setting_path, start_time)
        tac_controller_process = self.run_agent(
            "--connections", "fetchai/p2p_libp2p:0.8.0"
        )

        check_strings = (
            "Sending deploy transaction to decision maker.",
            "Sending deployment transaction to the ledger...",
            "The contract was successfully deployed. Contract address:",
            "Registering TAC data model",
            "TAC open for registration until:",
        )
        missing_strings = self.missing_from_output(
            tac_controller_process, check_strings, timeout=240, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in tac_controller output.".format(missing_strings)

        # run two participants as well
        self.set_agent_context(tac_aea_one)
        tac_aea_one_process = self.run_agent(
            "--connections", "fetchai/p2p_libp2p:0.8.0"
        )

        self.set_agent_context(tac_aea_two)
        tac_aea_two_process = self.run_agent(
            "--connections", "fetchai/p2p_libp2p:0.8.0"
        )

        check_strings = (
            "Agent registered:",
            "Closing registration!",
            "Setting Up the TAC game.",
            "Unregistering TAC data model",
            "Registering TAC data model",
            "Sending create_items transaction to decision maker.",
            "Sending creation transaction to the ledger..",
            "Successfully created the tokens. Transaction hash:",
            "Sending mint_items transactions to decision maker.",
            "Sending minting transaction to the ledger...",
            "Successfully minted the tokens for agent_addr=",
            "All tokens minted!",
            "Starting competition with configuration:",
            "Current good & money allocation & score:",
        )
        missing_strings = self.missing_from_output(
            tac_controller_process, check_strings, timeout=300, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in tac_controller output.".format(missing_strings)

        check_strings = (
            "Searching for TAC, search_id=",
            "Found the TAC controller. Registering...",
            "Received start event from the controller. Starting to compete...",
            "Searching for sellers which match the demand of the agent, search_id=",
            "Searching for buyers which match the supply of the agent, search_id=",
            "found potential sellers agents=",
            "sending CFP to agent=",
            "Accepting propose",
            "sending match accept to",
            "sending atomic swap tx to ledger.",
            "tx_digest=",
            "waiting for tx to confirm. Sleeping for 3 seconds ...",
            "Successfully conducted atomic swap. Transaction digest:",
            "found potential buyers agents=",
            "sending CFP to agent=",
            "Declining propose",
        )
        missing_strings = self.missing_from_output(
            tac_aea_one_process, check_strings, timeout=360, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in tac_aea_one output.".format(missing_strings)

        # Note, we do not need to check std output of the other participant as it is implied

        self.terminate_agents(
            tac_controller_process, tac_aea_one_process, tac_aea_two_process
        )
        assert (
            self.is_successfully_terminated()
        ), "Agents weren't successfully terminated."
