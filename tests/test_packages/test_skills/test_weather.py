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
import pytest


from aea.test_tools.test_cases import AEATestCaseMany

from tests.conftest import (
    COSMOS,
    COSMOS_PRIVATE_KEY_FILE,
    FUNDED_COSMOS_PRIVATE_KEY_1,
    MAX_FLAKY_RERUNS_INTEGRATION,
    NON_FUNDED_COSMOS_PRIVATE_KEY_1,
    NON_GENESIS_CONFIG,
    wait_for_localhost_ports_to_close,
)


@pytest.mark.integration
class TestWeatherSkills(AEATestCaseMany):
    """Test that weather skills work."""

    @pytest.mark.flaky(
        reruns=MAX_FLAKY_RERUNS_INTEGRATION
    )  # cause possible network issues
    def test_weather(self):
        """Run the weather skills sequence."""
        weather_station_aea_name = "my_weather_station"
        weather_client_aea_name = "my_weather_client"
        self.create_agents(weather_station_aea_name, weather_client_aea_name)

        default_routing = {
            "fetchai/ledger_api:0.1.0": "fetchai/ledger:0.2.0",
            "fetchai/oef_search:0.3.0": "fetchai/soef:0.5.0",
        }

        # prepare agent one (weather station)
        self.set_agent_context(weather_station_aea_name)
        self.add_item("connection", "fetchai/p2p_libp2p:0.5.0")
        self.add_item("connection", "fetchai/soef:0.5.0")
        self.set_config("agent.default_connection", "fetchai/p2p_libp2p:0.5.0")
        self.add_item("connection", "fetchai/ledger:0.2.0")
        self.add_item("skill", "fetchai/weather_station:0.7.0")
        self.set_config("agent.default_connection", "fetchai/p2p_libp2p:0.5.0")
        dotted_path = (
            "vendor.fetchai.skills.weather_station.models.strategy.args.is_ledger_tx"
        )
        self.set_config(dotted_path, False, "bool")
        setting_path = "agent.default_routing"
        self.force_set_config(setting_path, default_routing)
        self.run_install()

        # add non-funded key
        self.generate_private_key(COSMOS)
        self.add_private_key(COSMOS, COSMOS_PRIVATE_KEY_FILE)
        self.add_private_key(COSMOS, COSMOS_PRIVATE_KEY_FILE, connection=True)
        self.replace_private_key_in_file(
            NON_FUNDED_COSMOS_PRIVATE_KEY_1, COSMOS_PRIVATE_KEY_FILE
        )

        # prepare agent two (weather client)
        self.set_agent_context(weather_client_aea_name)
        self.add_item("connection", "fetchai/p2p_libp2p:0.5.0")
        self.add_item("connection", "fetchai/soef:0.5.0")
        self.set_config("agent.default_connection", "fetchai/p2p_libp2p:0.5.0")
        self.add_item("connection", "fetchai/ledger:0.2.0")
        self.add_item("skill", "fetchai/weather_client:0.6.0")
        self.set_config("agent.default_connection", "fetchai/p2p_libp2p:0.5.0")
        dotted_path = (
            "vendor.fetchai.skills.weather_client.models.strategy.args.is_ledger_tx"
        )
        self.set_config(dotted_path, False, "bool")
        setting_path = "agent.default_routing"
        self.force_set_config(setting_path, default_routing)
        self.run_install()

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
        self.set_agent_context(weather_station_aea_name)
        weather_station_process = self.run_agent()

        check_strings = (
            "Downloading golang dependencies. This may take a while...",
            "Finished downloading golang dependencies.",
            "Starting libp2p node...",
            "Connecting to libp2p node...",
            "Successfully connected to libp2p node!",
            "My libp2p addresses:",
        )
        missing_strings = self.missing_from_output(
            weather_station_process, check_strings, timeout=240, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in weather_station output.".format(missing_strings)

        self.set_agent_context(weather_client_aea_name)
        weather_client_process = self.run_agent()

        check_strings = (
            "Downloading golang dependencies. This may take a while...",
            "Finished downloading golang dependencies.",
            "Starting libp2p node...",
            "Connecting to libp2p node...",
            "Successfully connected to libp2p node!",
            "My libp2p addresses:",
        )
        missing_strings = self.missing_from_output(
            weather_client_process, check_strings, timeout=240, is_terminating=False,
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in weather_client output.".format(missing_strings)

        check_strings = (
            "registering agent on SOEF.",
            "registering service on SOEF.",
            "received CFP from sender=",
            "sending a PROPOSE with proposal=",
            "received ACCEPT from sender=",
            "sending MATCH_ACCEPT_W_INFORM to sender=",
            "received INFORM from sender=",
            "transaction confirmed, sending data=",
        )
        missing_strings = self.missing_from_output(
            weather_station_process, check_strings, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in weather_station output.".format(missing_strings)

        check_strings = (
            "found agents=",
            "sending CFP to agent=",
            "received proposal=",
            "accepting the proposal from sender=",
            "informing counterparty=",
            "received INFORM from sender=",
            "received the following data=",
        )
        missing_strings = self.missing_from_output(
            weather_client_process, check_strings, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in weather_client output.".format(missing_strings)

        self.terminate_agents(weather_station_process, weather_client_process)
        assert (
            self.is_successfully_terminated()
        ), "Agents weren't successfully terminated."
        wait_for_localhost_ports_to_close([9000, 9001])


@pytest.mark.integration
class TestWeatherSkillsFetchaiLedger(AEATestCaseMany):
    """Test that weather skills work."""

    @pytest.mark.flaky(
        reruns=MAX_FLAKY_RERUNS_INTEGRATION
    )  # cause possible network issues
    def test_weather(self):
        """Run the weather skills sequence."""
        weather_station_aea_name = "my_weather_station"
        weather_client_aea_name = "my_weather_client"
        self.create_agents(weather_station_aea_name, weather_client_aea_name)

        default_routing = {
            "fetchai/ledger_api:0.1.0": "fetchai/ledger:0.2.0",
            "fetchai/oef_search:0.3.0": "fetchai/soef:0.5.0",
        }

        # add packages for agent one
        self.set_agent_context(weather_station_aea_name)
        self.add_item("connection", "fetchai/p2p_libp2p:0.5.0")
        self.add_item("connection", "fetchai/soef:0.5.0")
        self.set_config("agent.default_connection", "fetchai/p2p_libp2p:0.5.0")
        self.add_item("connection", "fetchai/ledger:0.2.0")
        self.add_item("skill", "fetchai/weather_station:0.7.0")
        setting_path = "agent.default_routing"
        self.force_set_config(setting_path, default_routing)
        self.run_install()

        diff = self.difference_to_fetched_agent(
            "fetchai/weather_station:0.8.0", weather_station_aea_name
        )
        assert (
            diff == []
        ), "Difference between created and fetched project for files={}".format(diff)

        # add non-funded key
        self.generate_private_key(COSMOS)
        self.add_private_key(COSMOS, COSMOS_PRIVATE_KEY_FILE)
        self.add_private_key(COSMOS, COSMOS_PRIVATE_KEY_FILE, connection=True)
        self.replace_private_key_in_file(
            NON_FUNDED_COSMOS_PRIVATE_KEY_1, COSMOS_PRIVATE_KEY_FILE
        )

        # add packages for agent two
        self.set_agent_context(weather_client_aea_name)
        self.add_item("connection", "fetchai/p2p_libp2p:0.5.0")
        self.add_item("connection", "fetchai/soef:0.5.0")
        self.set_config("agent.default_connection", "fetchai/p2p_libp2p:0.5.0")
        self.add_item("connection", "fetchai/ledger:0.2.0")
        self.add_item("skill", "fetchai/weather_client:0.6.0")
        setting_path = "agent.default_routing"
        self.force_set_config(setting_path, default_routing)
        self.run_install()

        diff = self.difference_to_fetched_agent(
            "fetchai/weather_client:0.8.0", weather_client_aea_name
        )
        assert (
            diff == []
        ), "Difference between created and fetched project for files={}".format(diff)

        # add funded key
        self.generate_private_key(COSMOS)
        self.add_private_key(COSMOS, COSMOS_PRIVATE_KEY_FILE)
        self.add_private_key(COSMOS, COSMOS_PRIVATE_KEY_FILE, connection=True)
        self.replace_private_key_in_file(
            FUNDED_COSMOS_PRIVATE_KEY_1, COSMOS_PRIVATE_KEY_FILE
        )
        setting_path = "vendor.fetchai.connections.p2p_libp2p.config"
        self.force_set_config(setting_path, NON_GENESIS_CONFIG)

        self.set_agent_context(weather_station_aea_name)
        weather_station_process = self.run_agent()

        check_strings = (
            "Downloading golang dependencies. This may take a while...",
            "Finished downloading golang dependencies.",
            "Starting libp2p node...",
            "Connecting to libp2p node...",
            "Successfully connected to libp2p node!",
            "My libp2p addresses:",
        )
        missing_strings = self.missing_from_output(
            weather_station_process, check_strings, timeout=240, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in weather_station output.".format(missing_strings)

        self.set_agent_context(weather_client_aea_name)
        weather_client_process = self.run_agent()

        check_strings = (
            "Downloading golang dependencies. This may take a while...",
            "Finished downloading golang dependencies.",
            "Starting libp2p node...",
            "Connecting to libp2p node...",
            "Successfully connected to libp2p node!",
            "My libp2p addresses:",
        )
        missing_strings = self.missing_from_output(
            weather_client_process, check_strings, timeout=240, is_terminating=False,
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in weather_client output.".format(missing_strings)

        check_strings = (
            "registering agent on SOEF.",
            "registering service on SOEF.",
            "received CFP from sender=",
            "sending a PROPOSE with proposal=",
            "received ACCEPT from sender=",
            "sending MATCH_ACCEPT_W_INFORM to sender=",
            "received INFORM from sender=",
            "checking whether transaction=",
            "transaction confirmed, sending data=",
        )
        missing_strings = self.missing_from_output(
            weather_station_process, check_strings, timeout=240, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in weather_station output.".format(missing_strings)

        check_strings = (
            "found agents=",
            "sending CFP to agent=",
            "received proposal=",
            "accepting the proposal from sender=",
            "received MATCH_ACCEPT_W_INFORM from sender=",
            "requesting transfer transaction from ledger api...",
            "received raw transaction=",
            "proposing the transaction to the decision maker. Waiting for confirmation ...",
            "transaction signing was successful.",
            "sending transaction to ledger.",
            "transaction was successfully submitted. Transaction digest=",
            "informing counterparty=",
            "received INFORM from sender=",
            "received the following data=",
        )
        missing_strings = self.missing_from_output(
            weather_client_process, check_strings, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in weather_client output.".format(missing_strings)

        self.terminate_agents(weather_station_process, weather_client_process)
        assert (
            self.is_successfully_terminated()
        ), "Agents weren't successfully terminated."
        wait_for_localhost_ports_to_close([9000, 9001])
