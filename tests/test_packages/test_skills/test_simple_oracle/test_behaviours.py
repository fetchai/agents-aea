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

import logging
from pathlib import Path
from typing import cast
from unittest.mock import patch

from aea.test_tools.test_skill import BaseSkillTestCase

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

    def test_add_prometheus_metric(self):
        """Test the send_http_request_message method of the coin_price behaviour."""
        self.coin_price_behaviour.add_prometheus_metric("some_metric", "Gauge", "some_description", {"label_key": "label_value"}) 
        self.assert_quantity_in_outbox(1)

    def test_update_prometheus_metric(self):
        """Test the test_update_prometheus_metric method of the coin_price behaviour."""
        self.coin_price_behaviour.update_prometheus_metric("some_metric", "set", 0.0, {"label_key": "label_value"}) 
        self.assert_quantity_in_outbox(1)

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
