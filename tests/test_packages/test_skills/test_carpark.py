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

"""This test module contains the integration test for the weather skills."""

from aea.test_tools.test_cases import AEATestCaseMany, UseOef


class TestCarPark(AEATestCaseMany, UseOef):
    """Test that carpark skills work."""

    def test_carpark(self):
        """Run the weather skills sequence."""
        carpark_aea_name = "my_carpark_aea"
        carpark_client_aea_name = "my_carpark_client_aea"
        self.create_agents(carpark_aea_name, carpark_client_aea_name)

        # Setup agent one
        self.set_agent_context(carpark_aea_name)
        self.add_item("connection", "fetchai/oef:0.2.0")
        self.add_item("skill", "fetchai/carpark_detection:0.3.0")
        self.set_config("agent.default_connection", "fetchai/oef:0.2.0")
        setting_path = "vendor.fetchai.skills.carpark_detection.models.strategy.args.db_is_rel_to_cwd"
        self.set_config(setting_path, False, "bool")
        setting_path = (
            "vendor.fetchai.skills.carpark_detection.models.strategy.args.is_ledger_tx"
        )
        self.set_config(setting_path, False, "bool")
        self.run_install()

        # Setup Agent two
        self.set_agent_context(carpark_client_aea_name)
        self.add_item("connection", "fetchai/oef:0.2.0")
        self.add_item("skill", "fetchai/carpark_client:0.3.0")
        self.set_config("agent.default_connection", "fetchai/oef:0.2.0")
        setting_path = (
            "vendor.fetchai.skills.carpark_client.models.strategy.args.is_ledger_tx"
        )
        self.set_config(setting_path, False, "bool")
        self.run_install()

        # Fire the sub-processes and the threads.
        self.set_agent_context(carpark_aea_name)
        carpark_aea_process = self.run_agent("--connections", "fetchai/oef:0.2.0")

        self.set_agent_context(carpark_client_aea_name)
        carpark_client_aea_process = self.run_agent(
            "--connections", "fetchai/oef:0.2.0"
        )

        check_strings = (
            "updating car park detection services on OEF.",
            "unregistering car park detection services from OEF.",
            "received CFP from sender=",
            "sending sender=",
            "received ACCEPT from sender=",
            "sending MATCH_ACCEPT_W_INFORM to sender=",
            "received INFORM from sender=",
            "did not receive transaction digest from sender=",
        )
        missing_strings = self.missing_from_output(
            carpark_aea_process, check_strings, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in carpark_aea output.".format(missing_strings)

        check_strings = (
            "found agents=",
            "sending CFP to agent=",
            "received proposal=",
            "accepting the proposal from sender=",
            "informing counterparty=",
        )
        missing_strings = self.missing_from_output(
            carpark_client_aea_process, check_strings, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in carpark_client_aea output.".format(
            missing_strings
        )

        self.terminate_agents(carpark_aea_process, carpark_client_aea_process)
        assert (
            self.is_successfully_terminated()
        ), "Agents weren't successfully terminated."


class TestCarParkFetchaiLedger(AEATestCaseMany, UseOef):
    """Test that carpark skills work."""

    def test_carpark(self):
        """Run the weather skills sequence."""
        carpark_aea_name = "my_carpark_aea"
        carpark_client_aea_name = "my_carpark_client_aea"
        self.create_agents(carpark_aea_name, carpark_client_aea_name)

        ledger_apis = {"fetchai": {"network": "testnet"}}

        # Setup agent one
        self.set_agent_context(carpark_aea_name)
        self.force_set_config("agent.ledger_apis", ledger_apis)
        self.add_item("connection", "fetchai/oef:0.2.0")
        self.add_item("skill", "fetchai/carpark_detection:0.3.0")
        self.set_config("agent.default_connection", "fetchai/oef:0.2.0")
        setting_path = "vendor.fetchai.skills.carpark_detection.models.strategy.args.db_is_rel_to_cwd"
        self.set_config(setting_path, False, "bool")
        self.run_install()

        # Setup Agent two
        self.set_agent_context(carpark_client_aea_name)
        self.force_set_config("agent.ledger_apis", ledger_apis)
        self.add_item("connection", "fetchai/oef:0.2.0")
        self.add_item("skill", "fetchai/carpark_client:0.3.0")
        self.set_config("agent.default_connection", "fetchai/oef:0.2.0")
        self.run_install()

        # Fire the sub-processes and the threads.
        self.set_agent_context(carpark_aea_name)
        carpark_aea_process = self.run_agent("--connections", "fetchai/oef:0.2.0")

        self.set_agent_context(carpark_client_aea_name)
        carpark_client_aea_process = self.run_agent(
            "--connections", "fetchai/oef:0.2.0"
        )

        # TODO: finish test
        check_strings = (
            "updating car park detection services on OEF.",
            "unregistering car park detection services from OEF.",
            "received CFP from sender=",
            "sending sender=",
            "received DECLINE from sender=",
            # "received ACCEPT from sender=",
            # "sending MATCH_ACCEPT_W_INFORM to sender=",
            # "received INFORM from sender=",
            # "did not receive transaction digest from sender=",
        )
        missing_strings = self.missing_from_output(
            carpark_aea_process, check_strings, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in carpark_aea output.".format(missing_strings)

        check_strings = (
            "found agents=",
            "sending CFP to agent=",
            "received proposal=",
            "declining the proposal from sender=",
            # "accepting the proposal from sender=",
            # "informing counterparty=",
        )
        missing_strings = self.missing_from_output(
            carpark_client_aea_process, check_strings, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in carpark_client_aea output.".format(
            missing_strings
        )

        self.terminate_agents(carpark_aea_process, carpark_client_aea_process)
        assert (
            self.is_successfully_terminated()
        ), "Agents weren't successfully terminated."
