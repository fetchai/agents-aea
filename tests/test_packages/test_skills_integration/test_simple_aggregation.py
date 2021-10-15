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
"""This test module contains the integration test for the simple aggregation skill."""
import json

import pytest
from aea_ledger_fetchai import FetchAICrypto

from aea.test_tools.test_cases import AEATestCaseManyFlaky

from packages.fetchai.connections.p2p_libp2p.connection import LIBP2P_SUCCESS_MESSAGE

from tests.conftest import (
    FETCHAI_PRIVATE_KEY_FILE,
    FETCHAI_PRIVATE_KEY_FILE_CONNECTION,
    UseSOEF,
)


MAX_RERUNS = 1

COIN_URLS = [
    "https://api.coinbase.com/v2/prices/BTC-USD/buy",
    "https://api.coinpaprika.com/v1/tickers/btc-bitcoin",
    "https://api.cryptowat.ch/markets/kraken/btcusd/price",
    "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd",
]
JSON_PATHS = [
    "data.amount",
    "quotes.USD.price",
    "result.price",
    "bitcoin.usd",
]
SERVICE_ID = "generic_aggregation_service"


@pytest.mark.integration
class TestSimpleAggregationSkill(AEATestCaseManyFlaky, UseSOEF):
    """Test that simple aggregation skill works."""

    @pytest.mark.flaky(reruns=MAX_RERUNS)  # cause possible network issues
    def test_simple_aggregation(self):
        """Run the simple aggregation skill sequence."""

        agg0_name = "agg0_aea"
        agg1_name = "agg1_aea"
        agg2_name = "agg2_aea"
        agg3_name = "agg3_aea"

        agents = (agg0_name, agg1_name, agg2_name, agg3_name)

        self.create_agents(*agents)

        aea_processes = []
        for (i, agent) in enumerate(agents):
            # add packages for agent
            self.set_agent_context(agent)
            self.add_item("connection", "fetchai/p2p_libp2p:0.25.0")
            self.add_item("connection", "fetchai/http_client:0.23.0")
            self.add_item("connection", "fetchai/http_server:0.22.0")
            self.add_item("connection", "fetchai/soef:0.26.0")
            self.add_item("connection", "fetchai/prometheus:0.8.0")
            self.set_config("agent.default_connection", "fetchai/p2p_libp2p:0.25.0")
            self.nested_set_config(
                "agent.required_ledgers", [FetchAICrypto.identifier],
            )
            self.add_item("skill", "fetchai/advanced_data_request:0.6.0")
            self.add_item("skill", "fetchai/simple_aggregation:0.2.0")

            self.set_config(
                "vendor.fetchai.skills.advanced_data_request.models.advanced_data_request_model.args.decimals",
                0,
                type_="int",
            )
            self.set_config(
                "vendor.fetchai.skills.advanced_data_request.models.advanced_data_request_model.args.use_http_server",
                "false",
                type_="bool",
            )
            setting_path = (
                "vendor.fetchai.connections.http_server.config.target_skill_id"
            )
            self.set_config(setting_path, "fetchai/advanced_data_request:0.6.0")
            self.set_config(
                "vendor.fetchai.skills.simple_aggregation.models.strategy.args.quantity_name",
                "price",
            )
            self.set_config(
                "vendor.fetchai.skills.simple_aggregation.models.strategy.args.aggregation_function",
                "mean",
            )
            self.set_config(
                "vendor.fetchai.skills.simple_aggregation.models.strategy.args.search_query.search_value",
                SERVICE_ID,
            )
            self.set_config(
                "vendor.fetchai.skills.simple_aggregation.models.strategy.args.service_id",
                SERVICE_ID,
            )

            self.generate_private_key(FetchAICrypto.identifier)
            self.add_private_key(FetchAICrypto.identifier, FETCHAI_PRIVATE_KEY_FILE)
            self.generate_private_key(
                FetchAICrypto.identifier, FETCHAI_PRIVATE_KEY_FILE_CONNECTION
            )
            self.add_private_key(
                FetchAICrypto.identifier,
                FETCHAI_PRIVATE_KEY_FILE_CONNECTION,
                connection=True,
            )
            self.run_install()
            self.run_cli_command("issue-certificates", cwd=self._get_cwd())
            self.run_cli_command("build", cwd=self._get_cwd())
            setting_path = "vendor.fetchai.connections.p2p_libp2p.cert_requests"
            settings = json.dumps(
                [
                    {
                        "identifier": "acn",
                        "ledger_id": FetchAICrypto.identifier,
                        "not_after": "2022-01-01",
                        "not_before": "2021-01-01",
                        "public_key": FetchAICrypto.identifier,
                        "message_format": "{public_key}",
                        "save_path": ".certs/conn_cert.txt",
                    }
                ]
            )
            self.set_config(setting_path, settings, type_="list")

            if i == 0:
                diff = self.difference_to_fetched_agent(
                    "fetchai/simple_aggregator:0.4.0", agent
                )
                assert (
                    diff == []
                ), "Difference between created and fetched project for files={}".format(
                    diff
                )

                result = self.run_cli_command(
                    "get-multiaddress", "fetchai", "--connection", cwd=self._get_cwd()
                )
                multiaddr = result.stdout
            else:
                setting_path = "vendor.fetchai.connections.p2p_libp2p.config"
                settings = json.dumps(
                    {
                        "delegate_uri": f"127.0.0.1:{11000 + i}",
                        "entry_peers": [f"/dns4/127.0.0.1/tcp/9000/p2p/{multiaddr}"],
                        "local_uri": f"127.0.0.1:{9000 + i}",
                        "log_file": "libp2p_node.log",
                        "public_uri": f"127.0.0.1:{9000 + i}",
                    }
                )
                self.set_config(setting_path, settings, type_="dict")
                setting_path = "vendor.fetchai.connections.prometheus.config.port"
                self.set_config(setting_path, 20000 + i)
                setting_path = "vendor.fetchai.connections.http_server.config.port"
                self.set_config(setting_path, 8000 + i)

            # set SOEF configuration
            setting_path = "vendor.fetchai.connections.soef.config.is_https"
            self.set_config(setting_path, False)
            setting_path = "vendor.fetchai.connections.soef.config.soef_addr"
            self.set_config(setting_path, "127.0.0.1")
            setting_path = "vendor.fetchai.connections.soef.config.soef_port"
            self.set_config(setting_path, 12002)

            # set up data request skill to fetch coin price
            self.set_config(
                "vendor.fetchai.skills.advanced_data_request.models.advanced_data_request_model.args.url",
                COIN_URLS[i],
                type_="str",
            )
            self.set_config(
                "vendor.fetchai.skills.advanced_data_request.models.advanced_data_request_model.args.outputs",
                f'[{{"name": "price", "json_path": "{JSON_PATHS[i]}"}}]',
                type_="list",
            )

            # run agent
            aea_processes.append(self.run_agent())

        for agent in agents:
            self.set_agent_context(agent)
            check_strings = (
                "Starting libp2p node...",
                "Connecting to libp2p node...",
                "Successfully connected to libp2p node!",
                LIBP2P_SUCCESS_MESSAGE,
            )
            missing_strings = self.missing_from_output(
                aea_processes[0], check_strings, timeout=30, is_terminating=False
            )
            assert (
                missing_strings == []
            ), "Strings {} didn't appear in aea output.".format(missing_strings)

        for agent in agents:
            self.set_agent_context(agent)
            check_strings = (
                "setting up HttpHandler",
                "setting up PrometheusHandler",
                "setting up AdvancedDataRequestBehaviour",
                "Adding Prometheus metric: num_retrievals",
                "Adding Prometheus metric: num_requests",
                "registering agent on SOEF.",
                "registering agent's service on the SOEF.",
                "registering agent's personality genus on the SOEF.",
                "registering agent's personality classification on the SOEF.",
                "Start processing messages...",
                "Fetching data from",
                "Observation: {'price': {'value': ",
                "found agents=",
                "sending observation to peer=",
                "received observation from sender=",
                "Observations:",
                "Aggregation (mean):",
            )
            missing_strings = self.missing_from_output(
                aea_processes[0], check_strings, timeout=30, is_terminating=False
            )
            assert (
                missing_strings == []
            ), "Strings {} didn't appear in aea output.".format(missing_strings)

        self.terminate_agents(*aea_processes, timeout=30)
        assert (
            self.is_successfully_terminated()
        ), "Agents weren't successfully terminated."
