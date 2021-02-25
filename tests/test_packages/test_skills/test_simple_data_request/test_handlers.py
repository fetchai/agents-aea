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
from typing import cast
from unittest.mock import patch

import pytest

from aea.protocols.dialogue.base import DialogueMessage

from packages.fetchai.protocols.http.message import HttpMessage
from packages.fetchai.skills.simple_data_request.dialogues import HttpDialogues
from packages.fetchai.skills.simple_data_request.handlers import HttpHandler

from tests.test_packages.test_skills.test_simple_data_request.intermediate_class import (
    SimpleDataRequestTestCase,
)


class TestHttpHandler(SimpleDataRequestTestCase):
    """Test http handler of simple_data_request."""

    is_agent_to_agent_messages = False

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.http_handler = cast(HttpHandler, cls._skill.skill_context.handlers.http)
        cls.logger = cls._skill.skill_context.logger

        cls.http_dialogues = cast(
            HttpDialogues, cls._skill.skill_context.http_dialogues
        )

        cls.data = b"some_body"

        cls.list_of_messages = (
            DialogueMessage(
                HttpMessage.Performative.REQUEST,
                {
                    "method": "some_method",
                    "url": "some_url",
                    "headers": "some_headers",
                    "version": "some_version",
                    "body": b"some_body",
                },
            ),
        )

    def test__init__(self):
        """Test the __init__ method of the http handler where ValueError is raise."""
        with pytest.raises(ValueError, match="No shared_state_key provided!"):
            self.http_handler.__init__(shared_state_key=None)

    def test_setup(self):
        """Test the setup method of the http handler."""
        assert self.http_handler.setup() is None
        self.assert_quantity_in_outbox(0)

    def test_handle_unidentified_dialogue(self):
        """Test the _handle_unidentified_dialogue method of the http handler."""
        # setup
        incorrect_dialogue_reference = ("", "")
        incoming_message = self.build_incoming_message(
            message_type=HttpMessage,
            dialogue_reference=incorrect_dialogue_reference,
            performative=HttpMessage.Performative.RESPONSE,
            method="some_method",
            url="some_url",
            headers="some_headers",
            version="some_version",
            body=b"some_body",
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.http_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received invalid http message={incoming_message}, unidentified dialogue.",
        )

    def test_handle_response(self):
        """Test the _handle_response method of the http handler."""
        # setup
        http_dialogue = self.prepare_skill_dialogue(
            dialogues=self.http_dialogues, messages=self.list_of_messages[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=http_dialogue,
            performative=HttpMessage.Performative.RESPONSE,
            method="some_method",
            url="some_url",
            headers="some_headers",
            version="some_version",
            body=self.data,
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.http_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.DEBUG,
            f"received http response={incoming_message} in dialogue={http_dialogue}.",
        )

        mock_logger.assert_any_call(
            logging.INFO, "updating shared_state with received data=b'some_body'!",
        )

        assert (
            self.skill.skill_context._agent_context.shared_state[
                self.mocked_shared_state_key
            ]
            == self.data
        )

    def test_handle_invalid(self):
        """Test the _handle_invalid method of the http handler."""
        # setup
        incoming_message = self.build_incoming_message(
            message_type=HttpMessage,
            performative=HttpMessage.Performative.REQUEST,
            method="some_method",
            url="some_url",
            headers="some_headers",
            version="some_version",
            body=self.data,
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.http_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.WARNING,
            f"cannot handle http message of performative={incoming_message.performative} in dialogue={self.http_dialogues.get_dialogue(incoming_message)}.",
        )

    def test_teardown(self):
        """Test the teardown method of the http handler."""
        assert self.http_handler.teardown() is None
        self.assert_quantity_in_outbox(0)
