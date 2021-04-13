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

from tests.conftest import (
    FETCHAI_PRIVATE_KEY_FILE,
    FETCHAI_PRIVATE_KEY_FILE_CONNECTION,
)

from packages.fetchai.connections.p2p_libp2p.connection import LIBP2P_SUCCESS_MESSAGE

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

@pytest.mark.integration
class TestSimpleAggregationSkill(AEATestCaseManyFlaky):
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

        for (i, agent) in enumerate(agents):
            # add packages for agent
            self.set_agent_context(agent)
            self.add_item("connection", "fetchai/p2p_libp2p:0.21.0")
            self.add_item("connection", "fetchai/http_client:0.22.0")
            self.add_item("connection", "fetchai/http_server:0.21.0")
            self.add_item("connection", "fetchai/soef:0.22.0")
            self.add_item("connection", "fetchai/prometheus:0.7.0")
            self.set_config("agent.default_connection", "fetchai/p2p_libp2p:0.21.0")
            self.nested_set_config(
                "agent.required_ledgers", [FetchAICrypto.identifier],
            )
            self.add_item("skill", "fetchai/advanced_data_request:0.4.0")
            self.add_item("skill", "fetchai/simple_aggregation:0.1.0")

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
        self.run_install()

        # run first agent
        self.set_agent_context(agents[0])
        self.run_cli_command("build", cwd=self._get_cwd())
        self.run_cli_command("issue-certificates", cwd=self._get_cwd())
        aea_processes = [self.run_agent()]

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
        ), "Strings {} didn't appear in deploy_aea output.".format(missing_strings)


        # # Get oracle contract address from file
        # with open(ORACLE_CONTRACT_ADDRESS_FILE) as file:
        #     oracle_address = file.read()

        # # run oracle client agent
        # self.set_agent_context(client_agent_name)

        # # set oracle contract address in oracle client
        # setting_path = "vendor.fetchai.skills.simple_oracle_client.models.strategy.args.oracle_contract_address"
        # self.set_config(setting_path, oracle_address)

        # client_aea_process = self.run_agent()


        self.terminate_agents(aea_processes)
        assert (
            self.is_successfully_terminated()
        ), "Agents weren't successfully terminated."
