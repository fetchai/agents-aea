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

"""This test module contains the integration test for the thermometer skills."""

from aea.test_tools.test_cases import AEATestCaseMany, UseOef

from ...conftest import FUNDED_FET_PRIVATE_KEY_1


class TestThermometerSkill(AEATestCaseMany, UseOef):
    """Test that thermometer skills work."""

    def test_thermometer(self):
        """Run the thermometer skills sequence."""

        thermometer_aea_name = "my_thermometer"
        thermometer_client_aea_name = "my_thermometer_client"
        self.create_agents(thermometer_aea_name, thermometer_client_aea_name)

        # add packages for agent one and run it
        self.set_agent_context(thermometer_aea_name)
        self.add_item("connection", "fetchai/oef:0.4.0")
        self.set_config("agent.default_connection", "fetchai/oef:0.4.0")
        self.add_item("skill", "fetchai/thermometer:0.3.0")
        setting_path = (
            "vendor.fetchai.skills.thermometer.models.strategy.args.is_ledger_tx"
        )
        self.set_config(setting_path, False, "bool")
        self.run_install()

        # add packages for agent two and run it
        self.set_agent_context(thermometer_client_aea_name)
        self.add_item("connection", "fetchai/oef:0.4.0")
        self.set_config("agent.default_connection", "fetchai/oef:0.4.0")
        self.add_item("skill", "fetchai/thermometer_client:0.2.0")
        setting_path = (
            "vendor.fetchai.skills.thermometer_client.models.strategy.args.is_ledger_tx"
        )
        self.set_config(setting_path, False, "bool")
        self.run_install()

        # run AEAs
        self.set_agent_context(thermometer_aea_name)
        thermometer_aea_process = self.run_agent("--connections", "fetchai/oef:0.4.0")

        self.set_agent_context(thermometer_client_aea_name)
        thermometer_client_aea_process = self.run_agent(
            "--connections", "fetchai/oef:0.4.0"
        )

        check_strings = (
            "updating thermometer services on OEF service directory.",
            "received CFP from sender=",
            "sending a PROPOSE with proposal=",
            "received ACCEPT from sender=",
            "sending MATCH_ACCEPT_W_INFORM to sender=",
            "received INFORM from sender=",
            "unregistering thermometer station services from OEF service directory.",
        )
        missing_strings = self.missing_from_output(
            thermometer_aea_process, check_strings, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in thermometer_aea output.".format(missing_strings)

        check_strings = (
            "found agents=",
            "sending CFP to agent=",
            "received proposal=",
            "accepting the proposal from sender=",
            "informing counterparty=",
            "received INFORM from sender=",
            "received the following thermometer data=",
        )
        missing_strings = self.missing_from_output(
            thermometer_client_aea_process, check_strings, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in thermometer_client_aea output.".format(
            missing_strings
        )

        self.terminate_agents(thermometer_aea_process, thermometer_client_aea_process)
        assert (
            self.is_successfully_terminated()
        ), "Agents weren't successfully terminated."


class TestThermometerSkillFetchaiLedger(AEATestCaseMany, UseOef):
    """Test that thermometer skills work."""

    def test_thermometer(self):
        """Run the thermometer skills sequence."""

        thermometer_aea_name = "my_thermometer"
        thermometer_client_aea_name = "my_thermometer_client"
        self.create_agents(thermometer_aea_name, thermometer_client_aea_name)

        ledger_apis = {"fetchai": {"network": "testnet"}}

        # add packages for agent one and run it
        self.set_agent_context(thermometer_aea_name)
        self.add_item("connection", "fetchai/oef:0.4.0")
        self.set_config("agent.default_connection", "fetchai/oef:0.4.0")
        self.add_item("skill", "fetchai/thermometer:0.3.0")
        setting_path = "agent.ledger_apis"
        self.force_set_config(setting_path, ledger_apis)
        self.run_install()

        diff = self.difference_to_fetched_agent(
            "fetchai/thermometer_aea:0.3.0", thermometer_aea_name
        )
        assert (
            diff == []
        ), "Difference between created and fetched project for files={}".format(diff)

        # add packages for agent two and run it
        self.set_agent_context(thermometer_client_aea_name)
        self.add_item("connection", "fetchai/oef:0.4.0")
        self.set_config("agent.default_connection", "fetchai/oef:0.4.0")
        self.add_item("skill", "fetchai/thermometer_client:0.2.0")
        setting_path = "agent.ledger_apis"
        self.force_set_config(setting_path, ledger_apis)
        self.run_install()

        diff = self.difference_to_fetched_agent(
            "fetchai/thermometer_client:0.3.0", thermometer_client_aea_name
        )
        assert (
            diff == []
        ), "Difference between created and fetched project for files={}".format(diff)

        self.generate_private_key("fetchai")
        self.add_private_key("fetchai", "fet_private_key.txt")
        self.replace_private_key_in_file(
            FUNDED_FET_PRIVATE_KEY_1, "fet_private_key.txt"
        )

        # run AEAs
        self.set_agent_context(thermometer_aea_name)
        thermometer_aea_process = self.run_agent("--connections", "fetchai/oef:0.4.0")

        self.set_agent_context(thermometer_client_aea_name)
        thermometer_client_aea_process = self.run_agent(
            "--connections", "fetchai/oef:0.4.0"
        )

        # TODO: finish test
        check_strings = (
            "updating thermometer services on OEF service directory.",
            "unregistering thermometer station services from OEF service directory.",
            "received CFP from sender=",
            "sending a PROPOSE with proposal=",
            "received ACCEPT from sender=",
            "sending MATCH_ACCEPT_W_INFORM to sender=",
            "received INFORM from sender=",
            "checking whether transaction=",
            "transaction=",
        )
        missing_strings = self.missing_from_output(
            thermometer_aea_process, check_strings, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in thermometer_aea output.".format(missing_strings)

        check_strings = (
            "found agents=",
            "sending CFP to agent=",
            "received proposal=",
            "accepting the proposal from sender=",
            "received MATCH_ACCEPT_W_INFORM from sender=",
            "proposing the transaction to the decision maker. Waiting for confirmation ...",
            "Settling transaction on chain!",
            "transaction was successful.",
            "informing counterparty=",
            "received INFORM from sender=",
            "received the following thermometer data=",
        )
        missing_strings = self.missing_from_output(
            thermometer_client_aea_process, check_strings, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in thermometer_client_aea output.".format(
            missing_strings
        )

        self.terminate_agents(thermometer_aea_process, thermometer_client_aea_process)
        assert (
            self.is_successfully_terminated()
        ), "Agents weren't successfully terminated."
