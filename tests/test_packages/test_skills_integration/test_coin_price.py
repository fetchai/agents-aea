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

from pathlib import Path
from typing import Dict

import pytest
import requests

from aea.test_tools.test_cases import AEATestCaseEmpty

from tests.conftest import ROOT_DIR


API_SPEC_PATH = str(
    Path(
        ROOT_DIR, "packages", "fetchai", "skills", "coin_price", "coin_api_spec.yaml"
    ).absolute()
)


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
        self.add_item("connection", "fetchai/http_client:0.15.0")
        self.add_item("connection", "fetchai/http_server:0.14.0")
        self.add_item("connection", "fetchai/prometheus:0.1.0")
        self.add_item("skill", "fetchai/coin_price:0.2.0")
        self.set_config("agent.default_connection", "fetchai/http_server:0.14.0")

        default_routing = {
            "fetchai/http:0.13.0": "fetchai/http_client:0.15.0",
            "fetchai/prometheus:0.1.0": "fetchai/prometheus:0.1.0",
        }
        setting_path = "agent.default_routing"
        self.nested_set_config(setting_path, default_routing)

        self.set_config(
            "vendor.fetchai.connections.http_server.config.api_spec_path", API_SPEC_PATH
        )
        self.set_config(
            "vendor.fetchai.skills.coin_price.models.coin_price_model.args.use_http_server",
            True,
            type_="bool",
        )

        self.run_install()

        process = self.run_agent()
        is_running = self.is_running(process)
        assert is_running, "AEA not running within timeout!"

        response = requests.get("http://127.0.0.1:8000/price")
        assert response.status_code == 200, "Failed to get response code 200"
        coin_price = response.content.decode("utf-8")
        assert "value" in coin_price, "Response does not contain 'value'"
        assert "decimals" in coin_price, "Response does not contain 'decimals'"

        response = requests.get("http://127.0.0.1:8000")
        assert response.status_code == 404
        assert response.content == b"", "Get request should not work without valid path"

        response = requests.post("http://127.0.0.1:8000/price")
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
