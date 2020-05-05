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

#  import pytest

from aea.test_tools.decorators import skip_test_ci
from aea.test_tools.test_cases import AEATestCaseMany, UseOef

FUNDED_ETH_PRIVATE_KEY_1 = (
    "0xa337a9149b4e1eafd6c21c421254cf7f98130233595db25f0f6f0a545fb08883"
)


class TestTacSkills(AEATestCaseMany, UseOef):
    """Test that tac skills work."""

    @skip_test_ci
    def test_tac(self, pytestconfig):
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
        self.add_item("connection", "fetchai/oef:0.2.0")
        self.set_config("agent.default_connection", "fetchai/oef:0.2.0")
        self.add_item("skill", "fetchai/tac_control:0.1.0")
        self.set_config("agent.default_ledger", "ethereum")
        self.run_install()

        # prepare agents for test
        for agent_name in (tac_aea_one, tac_aea_two):
            self.set_agent_context(agent_name)
            self.add_item("connection", "fetchai/oef:0.2.0")
            self.set_config("agent.default_connection", "fetchai/oef:0.2.0")
            self.add_item("skill", "fetchai/tac_participation:0.1.0")
            self.add_item("skill", "fetchai/tac_negotiation:0.1.0")
            self.set_config("agent.default_ledger", "ethereum")
            self.run_install()

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
        tac_controller_process = self.run_agent("--connections", "fetchai/oef:0.2.0")

        # run two agents (participants)
        self.set_agent_context(tac_aea_one)
        tac_aea_one_process = self.run_agent("--connections", "fetchai/oef:0.2.0")

        self.set_agent_context(tac_aea_two)
        tac_aea_two_process = self.run_agent("--connections", "fetchai/oef:0.2.0")

        check_strings = (
            "Registering TAC data model",
            "TAC open for registration until:",
            "Agent registered: 'tac_participant_one'",
            "Agent registered: 'tac_participant_two'",
            "Started competition:",
            "Unregistering TAC data model",
            "Handling valid transaction:",
            "Current good & money allocation & score:",
        )
        missing_strings = self.missing_from_output(
            tac_controller_process, check_strings, timeout=180, is_terminating=False
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
            "transaction confirmed by decision maker, sending to controller.",
            "sending match accept to",
            "Received transaction confirmation from the controller: transaction_id=",
            "Applying state update!",
            "found potential buyers agents=",
            "sending CFP to agent=",
            "Declining propose",
        )
        missing_strings = self.missing_from_output(
            tac_aea_one_process, check_strings, timeout=180, is_terminating=False
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


class TestTacSkillsContract(AEATestCaseMany, UseOef):
    """Test that tac skills work."""

    @skip_test_ci
    def test_tac(self, pytestconfig):
        """Run the tac skills sequence."""
        tac_aea_one = "tac_participant_one"
        tac_aea_two = "tac_participant_two"
        tac_controller_name = "tac_controller"

        # create tac controller, agent one and agent two
        self.create_agents(
            tac_aea_one, tac_aea_two, tac_controller_name,
        )

        ledger_apis = {
            "ethereum": {
                "address": "https://ropsten.infura.io/v3/f00f7b3ba0e848ddbdc8941c527447fe",
                "chain_id": 3,
                "gas_price": 50,
            }
        }
        setting_path = "agent.ledger_apis"

        # prepare tac controller for test
        self.set_agent_context(tac_controller_name)
        self.force_set_config(setting_path, ledger_apis)
        self.add_item("connection", "fetchai/oef:0.2.0")
        self.set_config("agent.default_connection", "fetchai/oef:0.2.0")
        self.add_item("skill", "fetchai/tac_control_contract:0.1.0")
        self.set_config("agent.default_ledger", "ethereum")
        self.generate_private_key("ethereum")
        self.add_private_key("ethereum", "eth_private_key.txt")
        self.replace_private_key_in_file(
            FUNDED_ETH_PRIVATE_KEY_1, "eth_private_key.txt"
        )
        # stdout = self.get_wealth("ethereum")
        # if int(stdout) < 100000000000000000:
        #     pytest.skip("The agent needs more funds for the test to pass.")
        self.run_install()

        # prepare agents for test
        for agent_name in (tac_aea_one, tac_aea_two):
            self.set_agent_context(agent_name)
            self.force_set_config(setting_path, ledger_apis)
            self.add_item("connection", "fetchai/oef:0.2.0")
            self.set_config("agent.default_connection", "fetchai/oef:0.2.0")
            self.add_item("skill", "fetchai/tac_participation:0.1.0")
            self.add_item("skill", "fetchai/tac_negotiation:0.1.0")
            self.set_config("agent.default_ledger", "ethereum")
            self.set_config(
                "vendor.fetchai.skills.tac_participation.models.game.args.is_using_contract",
                True,
                "bool",
            )
            self.run_install()

        # run tac controller
        self.set_agent_context(tac_controller_name)
        now = datetime.datetime.now().strftime("%d %m %Y %H:%M")
        now_min = datetime.datetime.strptime(now, "%d %m %Y %H:%M")
        fut = now_min + datetime.timedelta(0, 240)
        start_time = fut.strftime("%d %m %Y %H:%M")
        setting_path = "vendor.fetchai.skills.tac_control_contract.models.parameters.args.start_time"
        self.set_config(setting_path, start_time)
        tac_controller_process = self.run_agent("--connections", "fetchai/oef:0.2.0")

        check_strings = (
            "Sending deploy transaction to decision maker.",
            "Sending deployment transaction to the ledger...",
            "The contract was successfully deployed. Contract address:",
            "Registering TAC data model",
            "TAC open for registration until:",
        )
        missing_strings = self.missing_from_output(
            tac_controller_process, check_strings, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in tac_controller output.".format(missing_strings)

        # run two participants as well
        self.set_agent_context(tac_aea_one)
        tac_aea_one_process = self.run_agent("--connections", "fetchai/oef:0.2.0")

        self.set_agent_context(tac_aea_two)
        tac_aea_two_process = self.run_agent("--connections", "fetchai/oef:0.2.0")

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
            "transaction confirmed by decision maker, sending to controller.",
            "sending match accept to",
            # "Received transaction confirmation from the controller: transaction_id=",
            # "Applying state update!",
            "found potential buyers agents=",
            "sending CFP to agent=",
            "Declining propose",
        )
        missing_strings = self.missing_from_output(
            tac_aea_one_process, check_strings, is_terminating=False
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
