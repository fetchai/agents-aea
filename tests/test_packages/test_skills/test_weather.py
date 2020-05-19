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

from ...conftest import FUNDED_FET_PRIVATE_KEY_1


class TestWeatherSkills(AEATestCaseMany, UseOef):
    """Test that weather skills work."""

    def test_weather(self):
        """Run the weather skills sequence."""
        weather_station_aea_name = "my_weather_station"
        weather_client_aea_name = "my_weather_client"
        self.create_agents(weather_station_aea_name, weather_client_aea_name)

        # prepare agent one (weather station)
        self.set_agent_context(weather_station_aea_name)
        self.add_item("connection", "fetchai/oef:0.2.0")
        self.add_item("skill", "fetchai/weather_station:0.3.0")
        self.set_config("agent.default_connection", "fetchai/oef:0.2.0")
        dotted_path = (
            "vendor.fetchai.skills.weather_station.models.strategy.args.is_ledger_tx"
        )
        self.set_config(dotted_path, False, "bool")
        self.run_install()

        # prepare agent two (weather client)
        self.set_agent_context(weather_client_aea_name)
        self.add_item("connection", "fetchai/oef:0.2.0")
        self.add_item("skill", "fetchai/weather_client:0.2.0")
        self.set_config("agent.default_connection", "fetchai/oef:0.2.0")
        dotted_path = (
            "vendor.fetchai.skills.weather_client.models.strategy.args.is_ledger_tx"
        )
        self.set_config(dotted_path, False, "bool")
        self.run_install()

        # run agents
        self.set_agent_context(weather_station_aea_name)
        weather_station_process = self.run_agent("--connections", "fetchai/oef:0.2.0")

        self.set_agent_context(weather_client_aea_name)
        weather_client_process = self.run_agent("--connections", "fetchai/oef:0.2.0")

        check_strings = (
            "updating weather station services on OEF service directory.",
            "received CFP from sender=",
            "sending a PROPOSE with proposal=",
            "received ACCEPT from sender=",
            "sending MATCH_ACCEPT_W_INFORM to sender=",
            "received INFORM from sender=",
            "unregistering weather station services from OEF service directory.",
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
            "received the following weather data=",
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


class TestWeatherSkillsFetchaiLedger(AEATestCaseMany, UseOef):
    """Test that weather skills work."""

    def test_weather(self):
        """Run the weather skills sequence."""
        weather_station_aea_name = "my_weather_station"
        weather_client_aea_name = "my_weather_client"
        self.create_agents(weather_station_aea_name, weather_client_aea_name)

        # prepare ledger configurations
        ledger_apis = {"fetchai": {"network": "testnet"}}

        # add packages for agent one
        self.set_agent_context(weather_station_aea_name)
        self.add_item("connection", "fetchai/oef:0.2.0")
        self.set_config("agent.default_connection", "fetchai/oef:0.2.0")
        self.add_item("skill", "fetchai/weather_station:0.3.0")
        self.force_set_config("agent.ledger_apis", ledger_apis)
        self.run_install()

        diff = self.difference_to_fetched_agent(
            "fetchai/weather_station:0.4.0", weather_station_aea_name
        )
        assert (
            diff == []
        ), "Difference between created and fetched project for files={}".format(diff)

        # add packages for agent two
        self.set_agent_context(weather_client_aea_name)
        self.add_item("connection", "fetchai/oef:0.2.0")
        self.set_config("agent.default_connection", "fetchai/oef:0.2.0")
        self.add_item("skill", "fetchai/weather_client:0.2.0")
        self.force_set_config("agent.ledger_apis", ledger_apis)
        self.run_install()

        diff = self.difference_to_fetched_agent(
            "fetchai/weather_client:0.4.0", weather_client_aea_name
        )
        assert (
            diff == []
        ), "Difference between created and fetched project for files={}".format(diff)

        self.generate_private_key("fetchai")
        self.add_private_key("fetchai", "fet_private_key.txt")
        self.replace_private_key_in_file(
            FUNDED_FET_PRIVATE_KEY_1, "fet_private_key.txt"
        )

        self.set_agent_context(weather_station_aea_name)
        weather_station_process = self.run_agent("--connections", "fetchai/oef:0.2.0")

        self.set_agent_context(weather_client_aea_name)
        weather_client_process = self.run_agent("--connections", "fetchai/oef:0.2.0")

        check_strings = (
            "updating weather station services on OEF service directory.",
            "unregistering weather station services from OEF service directory.",
            "received CFP from sender=",
            "sending a PROPOSE with proposal=",
            "received ACCEPT from sender=",
            "sending MATCH_ACCEPT_W_INFORM to sender=",
            "received INFORM from sender=",
            "checking whether transaction=",
            "transaction=",
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
            "received MATCH_ACCEPT_W_INFORM from sender=",
            "proposing the transaction to the decision maker. Waiting for confirmation ...",
            "Settling transaction on chain!",
            "transaction was successful.",
            "informing counterparty=",
            "received INFORM from sender=",
            "received the following weather data=",
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
