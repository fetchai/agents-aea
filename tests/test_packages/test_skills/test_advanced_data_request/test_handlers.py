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
"""This module contains the tests of the handler classes of the simple_data_request skill."""

import logging
from pathlib import Path
from typing import cast
from unittest.mock import patch

from aea.protocols.dialogue.base import DialogueMessage
from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.connections.http_server.connection import (
    PUBLIC_ID as HTTP_SERVER_ID,
)
from packages.fetchai.protocols.http.message import HttpMessage
from packages.fetchai.protocols.prometheus.message import PrometheusMessage
from packages.fetchai.skills.advanced_data_request.dialogues import (
    HttpDialogues,
    PrometheusDialogues,
)
from packages.fetchai.skills.advanced_data_request.handlers import (
    HttpHandler,
    PrometheusHandler,
)
from packages.fetchai.skills.advanced_data_request.models import (
    AdvancedDataRequestModel,
)

from tests.conftest import ROOT_DIR


class TestHttpHandler(BaseSkillTestCase):
    """Test http handler of advanced_data_request skill."""

    path_to_skill = Path(
        ROOT_DIR, "packages", "fetchai", "skills", "advanced_data_request"
    )
    is_agent_to_agent_messages = False

    @classmethod
    def setup(cls, **kwargs):
        """Setup the test class."""
        super().setup()
        cls.http_handler = cast(HttpHandler, cls._skill.skill_context.handlers.http)
        cls.logger = cls._skill.skill_context.logger

        cls.advanced_data_request_model = cast(
            AdvancedDataRequestModel,
            cls._skill.skill_context.advanced_data_request_model,
        )

        cls.advanced_data_request_model.url = "http://some-url"
        cls.advanced_data_request_model.outputs = [
            {"name": "output1", "json_path": "in1.in2"},
            {"name": "output2", "json_path": "id"},
        ]

        cls.http_dialogues = cast(
            HttpDialogues, cls._skill.skill_context.http_dialogues
        )

        cls.list_of_messages = (
            DialogueMessage(
                HttpMessage.Performative.REQUEST,
                {
                    "method": "get",
                    "url": "some_url",
                    "headers": "",
                    "version": "",
                    "body": b"",
                },
            ),
        )

    def test_setup(self):
        """Test the setup method of the http handler."""
        assert self.http_handler.setup() is None
        self.assert_quantity_in_outbox(0)

    def test_setup_with_http_server(self):
        """Test the setup method of the http handler."""
        self.advanced_data_request_model.use_http_server = True
        assert self.http_handler.setup() is None

        assert self.http_handler._http_server_id == HTTP_SERVER_ID
        self.assert_quantity_in_outbox(0)

    def test_handle_response(self):
        """Test the _handle_response method of the http handler to a valid response."""
        # setup
        http_dialogue = self.prepare_skill_dialogue(
            dialogues=self.http_dialogues, messages=self.list_of_messages[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=http_dialogue,
            performative=HttpMessage.Performative.RESPONSE,
            version="",
            status_code=200,
            status_text="",
            headers="",
            body=b'{"in1": {"in2": 1.0}, "id": "XXX"}',
        )

        # handle message
        self.http_handler.handle(incoming_message)

        # check that data was correctly entered into shared state
        observation = {
            "output1": {"value": 100000, "decimals": 5},
            "output2": {"value": "XXX"},
        }
        assert (
            self.http_handler.context.shared_state["output1"] == observation["output1"]
        )
        assert (
            self.http_handler.context.shared_state["output2"] == observation["output2"]
        )

        # check that outbox contains update_prometheus metric message
        self.assert_quantity_in_outbox(1)

    def test_handle__handle_unidentified_dialogue(self):
        """Test handling an unidentified dialogoue"""
        # setup
        incorrect_dialogue_reference = ("", "")
        incoming_message = self.build_incoming_message(
            message_type=HttpMessage,
            dialogue_reference=incorrect_dialogue_reference,
            performative=HttpMessage.Performative.RESPONSE,
            version="",
            status_code=200,
            status_text="",
            headers="",
            body=b"{}",
        )

        # operation
        with patch.object(self.http_handler.context.logger, "log") as mock_logger:
            self.http_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received invalid message={incoming_message}, unidentified dialogue.",
        )

        self.assert_quantity_in_outbox(0)

    def test_handle_response_invalid_body(self):
        """Test the _handle_response method of the http handler to an unexpected response."""
        # setup
        http_dialogue = self.prepare_skill_dialogue(
            dialogues=self.http_dialogues, messages=self.list_of_messages[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=http_dialogue,
            performative=HttpMessage.Performative.RESPONSE,
            version="",
            status_code=200,
            status_text="",
            headers="",
            body=b"{}",
        )

        # handle message with logging
        with patch.object(self.logger, "log") as mock_logger:
            self.http_handler.handle(incoming_message)

        assert "output1" not in self.http_handler.context.shared_state

        # after
        mock_logger.assert_any_call(
            logging.WARNING, "No valid output for output1 found in response.",
        )

    def test_handle_response_missing_output(self):
        """Test the _handle_response method of the http handler to a response with a missing output."""
        # setup
        http_dialogue = self.prepare_skill_dialogue(
            dialogues=self.http_dialogues, messages=self.list_of_messages[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=http_dialogue,
            performative=HttpMessage.Performative.RESPONSE,
            version="",
            status_code=200,
            status_text="",
            headers="",
            body=b'{"in1": {}, "id": "XXX"}',
        )

        # handle message with logging
        with patch.object(self.logger, "log") as mock_logger:
            self.http_handler.handle(incoming_message)

        assert self.http_handler.context.shared_state["output2"] == {"value": "XXX"}

        # after
        mock_logger.assert_any_call(
            logging.WARNING, "No valid output for output1 found in response.",
        )
        mock_logger.assert_any_call(
            logging.INFO, "Observation: {'output2': {'value': 'XXX'}}",
        )

    def test_handle_response_bad_response_code(self):
        """Test the _handle_response method of the http handler to a response with a code that is not 200."""
        # setup
        http_dialogue = self.prepare_skill_dialogue(
            dialogues=self.http_dialogues, messages=self.list_of_messages[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=http_dialogue,
            performative=HttpMessage.Performative.RESPONSE,
            version="",
            status_code=999,
            status_text="",
            headers="",
            body=b'{"in1": {"in2": 1.0}, "id": "XXX"}',
        )

        # handle message with logging
        with patch.object(self.logger, "log") as mock_logger:
            self.http_handler.handle(incoming_message)

        assert "output1" not in self.http_handler.context.shared_state

        # after
        mock_logger.assert_any_call(
            logging.INFO, "got unexpected http message: code = 999",
        )

    def test_handle_request_get(self):
        """Test the _handle_request method of the http handler with 'get' method."""

        incoming_message = self.build_incoming_message(
            message_type=HttpMessage,
            performative=HttpMessage.Performative.REQUEST,
            method="get",
            url="some_url",
            headers="",
            version="",
            body=b"",
        )

        self.http_handler._http_server_id = "some_id"

        # handle message with logging
        with patch.object(self.logger, "log") as mock_logger:
            self.http_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            "received http request with method=get, url=some_url and body=b''",
        )

        # check that outbox contains the http response prometheus metric update messages
        self.assert_quantity_in_outbox(2)

    def test_handle_request_post(self):
        """Test the _handle_request method of the http handler with 'post' method."""

        incoming_message = self.build_incoming_message(
            message_type=HttpMessage,
            performative=HttpMessage.Performative.REQUEST,
            method="post",
            url="some_url",
            headers="",
            version="",
            body=b"",
        )

        self.http_handler._http_server_id = "some_id"

        # handle message with logging
        with patch.object(self.logger, "log") as mock_logger:
            self.http_handler.handle(incoming_message)

        mock_logger.assert_any_call(
            logging.INFO, "method 'post' is not supported.",
        )
        # check that outbox is empty
        self.assert_quantity_in_outbox(0)

    def test_handle_request_no_http_server(self):
        """Test the _handle_request method of the http handler when http server is disabled."""

        incoming_message = self.build_incoming_message(
            message_type=HttpMessage,
            performative=HttpMessage.Performative.REQUEST,
            method="get",
            url="some_url",
            headers="",
            version="",
            body=b"",
        )

        # handle message with logging
        with patch.object(self.logger, "log") as mock_logger:
            self.http_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            "received http request with method=get, url=some_url and body=b''",
        )

        mock_logger.assert_any_call(
            logging.INFO, "http server is not enabled.",
        )
        # check that outbox is empty
        self.assert_quantity_in_outbox(0)

    def test_teardown(self):
        """Test the teardown method of the http handler."""
        assert self.http_handler.teardown() is None
        self.assert_quantity_in_outbox(0)


class TestPrometheusHandler(BaseSkillTestCase):
    """Test prometheus handler of advanced_data_request skill."""

    path_to_skill = Path(
        ROOT_DIR, "packages", "fetchai", "skills", "advanced_data_request"
    )
    is_agent_to_agent_messages = False

    @classmethod
    def setup(cls, **kwargs):
        """Setup the test class."""
        super().setup()
        cls.prometheus_handler = cast(
            PrometheusHandler, cls._skill.skill_context.handlers.prometheus
        )
        cls.logger = cls._skill.skill_context.logger

        cls.advanced_data_request_model = cast(
            AdvancedDataRequestModel,
            cls._skill.skill_context.advanced_data_request_model,
        )

        cls.prometheus_dialogues = cast(
            PrometheusDialogues, cls._skill.skill_context.prometheus_dialogues
        )

        cls.list_of_messages = (
            DialogueMessage(
                PrometheusMessage.Performative.ADD_METRIC,
                {
                    "type": "Gauge",
                    "title": "some_title",
                    "description": "some_description",
                    "labels": {},
                },
            ),
        )

    def test_setup(self):
        """Test the setup method of the prometheus handler."""
        assert self.prometheus_handler.setup() is None
        self.assert_quantity_in_outbox(0)

    def test_handle_response(self):
        """Test the _handle_response method of the prometheus handler to a valid response."""
        # setup
        prometheus_dialogue = self.prepare_skill_dialogue(
            dialogues=self.prometheus_dialogues, messages=self.list_of_messages[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=prometheus_dialogue,
            performative=PrometheusMessage.Performative.RESPONSE,
            code=200,
            message="some_message",
        )

        # handle message with logging
        with patch.object(self.logger, "log") as mock_logger:
            self.prometheus_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.DEBUG, "Prometheus response (200): some_message"
        )

    def test_handle_unidentified_dialogue(self):
        """Test the _handle_response method of the prometheus handler to an unidentified dialogue."""
        # setup
        incoming_message = self.build_incoming_message(
            message_type=PrometheusMessage,
            performative=PrometheusMessage.Performative.RESPONSE,
            code=200,
            message="some_message",
        )

        # handle message with logging
        with patch.object(self.logger, "log") as mock_logger:
            self.prometheus_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received invalid message={incoming_message}, unidentified dialogue.",
        )

    def test_teardown(self):
        """Test the teardown method of the prometheus handler."""
        assert self.prometheus_handler.teardown() is None
        self.assert_quantity_in_outbox(0)
