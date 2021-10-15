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

"""This test module contains the integration test for the coin price skill."""

import time
from typing import Dict

import pytest

from aea.helpers import http_requests as requests
from aea.test_tools.test_cases import AEATestCaseEmpty


def parse_prometheus_output(prom_data: bytes) -> Dict[str, float]:
    """Convert prometheus text output to a dict of {"metric": value}"""
    metrics = {}
    for line in prom_data.decode().splitlines():
        tokens = line.split()
        if tokens[0] != "#":
            metrics.update({tokens[0]: float(tokens[1])})
    return metrics


@pytest.mark.integration
class TestCoinPriceSkill(AEATestCaseEmpty):
    """Test that coin price skill works."""

    def test_coin_price(self):
        """Run the coin price skill sequence."""

        coin_price_feed_aea_name = self.agent_name

        self.generate_private_key()
        self.add_private_key()
        self.add_item("connection", "fetchai/http_client:0.23.0")
        self.add_item("connection", "fetchai/http_server:0.22.0")
        self.add_item("connection", "fetchai/prometheus:0.8.0")
        self.add_item("skill", "fetchai/advanced_data_request:0.6.0")
        self.set_config("agent.default_connection", "fetchai/http_server:0.22.0")

        default_routing = {
            "fetchai/http:1.0.0": "fetchai/http_client:0.23.0",
            "fetchai/prometheus:1.0.0": "fetchai/prometheus:0.8.0",
        }
        setting_path = "agent.default_routing"
        self.nested_set_config(setting_path, default_routing)

        # set 'api spec path' *after* comparison with fetched agent.
        self.set_config(
            "vendor.fetchai.connections.http_server.config.api_spec_path",
            "vendor/fetchai/skills/advanced_data_request/api_spec.yaml",
        )
        self.set_config(
            "vendor.fetchai.connections.http_server.config.target_skill_id",
            "fetchai/advanced_data_request:0.6.0",
        )
        self.set_config(
            "vendor.fetchai.skills.advanced_data_request.models.advanced_data_request_model.args.use_http_server",
            True,
            type_="bool",
        )
        self.set_config(
            "vendor.fetchai.skills.advanced_data_request.models.advanced_data_request_model.args.url",
            "https://api.coingecko.com/api/v3/simple/price?ids=fetch-ai&vs_currencies=usd",
            type_="str",
        )
        self.set_config(
            "vendor.fetchai.skills.advanced_data_request.models.advanced_data_request_model.args.outputs",
            '[{"name": "price", "json_path": "fetch-ai.usd"}]',
            type_="list",
        )

        diff = self.difference_to_fetched_agent(
            "fetchai/coin_price_feed:0.14.0", coin_price_feed_aea_name
        )
        assert (
            diff == []
        ), "Difference between created and fetched project for files={}".format(diff)

        self.run_install()

        process = self.run_agent()
        is_running = self.is_running(process)
        assert is_running, "AEA not running within timeout!"

        time.sleep(6)  # we wait a bit longer than the tick rate of the behaviour

        response = requests.get("http://127.0.0.1:8000/data")
        assert response.status_code == 200, "Failed to get response code 200"
        coin_price = response.json()
        assert "price" in coin_price, "Response does not contain 'price'"

        response = requests.get("http://127.0.0.1:8000")
        assert response.status_code == 404
        assert response.content == b"", "Get request should not work without valid path"

        response = requests.post("http://127.0.0.1:8000/data")
        assert response.status_code == 404
        assert response.content == b"", "Post not allowed"

        # test prometheus metrics
        prom_response = requests.get("http://127.0.0.1:9090/metrics")
        metrics = parse_prometheus_output(prom_response.content)
        assert metrics["num_retrievals"] > 0.0, "num_retrievals metric not updated"
        assert metrics["num_requests"] == 1.0, "num_requests metric not equal to 1"

        self.terminate_agents()
        assert (
            self.is_successfully_terminated()
        ), "Http echo agent wasn't successfully terminated."
