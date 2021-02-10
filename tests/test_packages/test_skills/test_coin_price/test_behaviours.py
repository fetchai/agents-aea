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
"""This module contains the tests of the behaviour classes of the coin price skill."""

from pathlib import Path
from typing import cast

from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.protocols.http.message import HttpMessage
from packages.fetchai.protocols.prometheus.message import PrometheusMessage
from packages.fetchai.skills.coin_price.behaviours import CoinPriceBehaviour

from tests.conftest import ROOT_DIR


class TestSkillBehaviour(BaseSkillTestCase):
    """Test behaviours of coin price."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "coin_price")

    @classmethod
    def setup(cls, **kwargs):
        """Setup the test class."""
        super().setup()
        cls.coin_price_behaviour = cast(
            CoinPriceBehaviour, cls._skill.skill_context.behaviours.coin_price_behaviour
        )

    def test_send_http_request_message(self):
        """Test the send_http_request_message method of the coin_price behaviour."""
        self.coin_price_behaviour.send_http_request_message("GET", "some_url")
        self.assert_quantity_in_outbox(1)
        msg = cast(HttpMessage, self.get_message_from_outbox())
        assert msg, "Wrong message type"
        assert (
            msg.performative == HttpMessage.Performative.REQUEST
        ), "Wrong message performative"
        assert msg.url == "some_url", "Wrong url"

    def test_add_prometheus_metric(self):
        """Test the send_http_request_message method of the coin_price behaviour."""
        self.coin_price_behaviour.add_prometheus_metric(
            "some_metric", "Gauge", "some_description", {"label_key": "label_value"}
        )
        self.assert_quantity_in_outbox(1)
        msg = cast(PrometheusMessage, self.get_message_from_outbox())
        assert msg, "Wrong message type"
        assert (
            msg.performative == PrometheusMessage.Performative.ADD_METRIC
        ), "Wrong message performative"
        assert msg.type == "Gauge", "Wrong metric type"
        assert msg.title == "some_metric", "Wrong metric title"
        assert msg.description == "some_description", "Wrong metric description"
        assert msg.labels == {"label_key": "label_value"}, "Wrong labels"

    def test_update_prometheus_metric(self):
        """Test the test_update_prometheus_metric method of the coin_price behaviour."""
        self.coin_price_behaviour.update_prometheus_metric(
            "some_metric", "set", 0.0, {"label_key": "label_value"}
        )
        self.assert_quantity_in_outbox(1)
        msg = cast(PrometheusMessage, self.get_message_from_outbox())
        assert msg, "Wrong message type"
        assert (
            msg.performative == PrometheusMessage.Performative.UPDATE_METRIC
        ), "Wrong message performative"
        assert msg.callable == "set", "Wrong metric callable"
        assert msg.title == "some_metric", "Wrong metric title"
        assert msg.value == 0.0, "Wrong metric value"
        assert msg.labels == {"label_key": "label_value"}, "Wrong labels"

    def test_setup(self):
        """Test that the setup method puts two messages (prometheus metrics) in the outbox by default."""
        self.coin_price_behaviour.setup()
        self.assert_quantity_in_outbox(2)

    def test_act(self):
        """Test that the act method of the coin_price behaviour puts one message (http request) in the outbox."""
        self.coin_price_behaviour.act()
        self.assert_quantity_in_outbox(1)

    def test_teardown(self):
        """Test that the teardown method of the coin_price behaviour leaves no messages in the outbox."""
        assert self.coin_price_behaviour.teardown() is None
        self.assert_quantity_in_outbox(0)
