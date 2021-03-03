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
"""This module contains the tests of the behaviour classes of the advanced data request skill."""

from pathlib import Path
from typing import cast

from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.protocols.http.message import HttpMessage
from packages.fetchai.protocols.prometheus.message import PrometheusMessage
from packages.fetchai.skills.advanced_data_request.behaviours import (
    AdvancedDataRequestBehaviour,
)
from packages.fetchai.skills.advanced_data_request.models import (
    AdvancedDataRequestModel,
)

from tests.conftest import ROOT_DIR


class TestSkillBehaviour(BaseSkillTestCase):
    """Test behaviours of advanced data request."""

    path_to_skill = Path(
        ROOT_DIR, "packages", "fetchai", "skills", "advanced_data_request"
    )

    @classmethod
    def setup(cls, **kwargs):
        """Setup the test class."""
        super().setup()
        cls.advanced_data_request_behaviour = cast(
            AdvancedDataRequestBehaviour,
            cls._skill.skill_context.behaviours.advanced_data_request_behaviour,
        )
        cls.advanced_data_request_model = cast(
            AdvancedDataRequestModel,
            cls.advanced_data_request_behaviour.context.advanced_data_request_model,
        )
        cls.advanced_data_request_model.url = "some_url"

    def test_send_http_request_message(self):
        """Test the send_http_request_message method of the advanced_data_request behaviour."""
        self.advanced_data_request_behaviour.send_http_request_message()
        self.assert_quantity_in_outbox(1)
        msg = cast(HttpMessage, self.get_message_from_outbox())
        has_attributes, error_str = self.message_has_attributes(
            actual_message=msg,
            message_type=HttpMessage,
            performative=HttpMessage.Performative.REQUEST,
            url="some_url",
        )
        assert has_attributes, error_str

    def test_add_prometheus_metric(self):
        """Test the add_prometheus_metric method of the advanced_data_request behaviour."""
        self.advanced_data_request_behaviour.add_prometheus_metric(
            "some_metric", "Gauge", "some_description", {"label_key": "label_value"}
        )
        self.assert_quantity_in_outbox(1)
        msg = cast(PrometheusMessage, self.get_message_from_outbox())
        has_attributes, error_str = self.message_has_attributes(
            actual_message=msg,
            message_type=PrometheusMessage,
            performative=PrometheusMessage.Performative.ADD_METRIC,
            type="Gauge",
            title="some_metric",
            description="some_description",
            labels={"label_key": "label_value"},
        )
        assert has_attributes, error_str

    def test_update_prometheus_metric(self):
        """Test the update_prometheus_metric method of the advanced_data_request behaviour."""
        self.advanced_data_request_behaviour.update_prometheus_metric(
            "some_metric", "set", 0.0, {"label_key": "label_value"}
        )
        self.assert_quantity_in_outbox(1)
        msg = cast(PrometheusMessage, self.get_message_from_outbox())
        has_attributes, error_str = self.message_has_attributes(
            actual_message=msg,
            message_type=PrometheusMessage,
            performative=PrometheusMessage.Performative.UPDATE_METRIC,
            callable="set",
            title="some_metric",
            value=0.0,
            labels={"label_key": "label_value"},
        )
        assert has_attributes, error_str

    def test_setup(self):
        """Test that the setup method puts two messages (prometheus metrics) in the outbox by default."""
        self.advanced_data_request_behaviour.setup()
        self.assert_quantity_in_outbox(2)

        msg = cast(PrometheusMessage, self.get_message_from_outbox())
        has_attributes, error_str = self.message_has_attributes(
            actual_message=msg,
            message_type=PrometheusMessage,
            performative=PrometheusMessage.Performative.ADD_METRIC,
            type="Gauge",
            title="num_retrievals",
        )
        assert has_attributes, error_str

        msg = cast(PrometheusMessage, self.get_message_from_outbox())
        has_attributes, error_str = self.message_has_attributes(
            actual_message=msg,
            message_type=PrometheusMessage,
            performative=PrometheusMessage.Performative.ADD_METRIC,
            type="Gauge",
            title="num_requests",
        )
        assert has_attributes, error_str

    def test_act(self):
        """Test that the act method of the advanced_data_request behaviour puts one message (http request) in the outbox."""

        self.advanced_data_request_behaviour.act()
        self.assert_quantity_in_outbox(1)

        msg = cast(HttpMessage, self.get_message_from_outbox())
        has_attributes, error_str = self.message_has_attributes(
            actual_message=msg,
            message_type=HttpMessage,
            performative=HttpMessage.Performative.REQUEST,
            url=self.advanced_data_request_model.url,
        )
        assert has_attributes, error_str

    def test_teardown(self):
        """Test that the teardown method of the advanced_data_request behaviour leaves no messages in the outbox."""
        assert self.advanced_data_request_behaviour.teardown() is None
        self.assert_quantity_in_outbox(0)
