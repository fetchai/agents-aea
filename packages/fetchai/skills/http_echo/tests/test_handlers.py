# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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
"""This module contains the tests of the handler class of the http_echo skill."""
# pylint: skip-file

import json
import logging
from pathlib import Path
from typing import cast
from unittest.mock import patch

from aea.protocols.dialogue.base import DialogueMessage
from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.protocols.default.message import DefaultMessage
from packages.fetchai.protocols.http.message import HttpMessage
from packages.fetchai.skills.http_echo.dialogues import HttpDialogues
from packages.fetchai.skills.http_echo.handlers import HttpHandler


PACKAGE_DIR = Path(__file__).parent.parent


class TestHttpHandler(BaseSkillTestCase):
    """Test HttpHandler of http_echo."""

    path_to_skill = PACKAGE_DIR

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.http_handler = cast(
            HttpHandler, cls._skill.skill_context.handlers.http_handler
        )
        cls.logger = cls._skill.skill_context.logger

        cls.http_dialogues = cast(
            HttpDialogues, cls._skill.skill_context.http_dialogues
        )

        cls.get_method = "get"
        cls.post_method = "post"
        cls.url = "some_url"
        cls.version = "some_version"
        cls.headers = "some_headers"
        cls.body = b"some_body"
        cls.sender = "fetchai/some_skill:0.1.0"
        cls.skill_id = str(cls._skill.skill_context.skill_id)

        cls.status_code = 100
        cls.status_text = "some_status_text"

        cls.content = b"some_content"
        cls.list_of_messages = (
            DialogueMessage(
                HttpMessage.Performative.REQUEST,
                {
                    "method": cls.get_method,
                    "url": cls.url,
                    "version": cls.version,
                    "headers": cls.headers,
                    "body": cls.body,
                },
            ),
        )

    def test_setup(self):
        """Test the setup method of the http_echo handler."""
        assert self.http_handler.setup() is None
        self.assert_quantity_in_outbox(0)

    def test_handle_unidentified_dialogue(self):
        """Test the _handle_unidentified_dialogue method of the http_echo handler."""
        # setup
        incorrect_dialogue_reference = ("", "")
        incoming_message = self.build_incoming_message(
            message_type=HttpMessage,
            dialogue_reference=incorrect_dialogue_reference,
            performative=HttpMessage.Performative.REQUEST,
            to=self.skill_id,
            method=self.get_method,
            url=self.url,
            version=self.version,
            headers=self.headers,
            body=self.body,
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.http_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_outbox(1)

        mock_logger.assert_any_call(
            logging.INFO,
            f"received invalid http message={incoming_message}, unidentified dialogue.",
        )

        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=DefaultMessage,
            performative=DefaultMessage.Performative.ERROR,
            to=incoming_message.sender,
            sender=self.skill.skill_context.agent_address,
            error_code=DefaultMessage.ErrorCode.INVALID_DIALOGUE,
            error_msg="Invalid dialogue.",
            error_data={"http_message": incoming_message.encode()},
        )
        assert has_attributes, error_str

    def test_handle_request_get(self):
        """Test the _handle_request method of the http_echo handler where method is get."""
        # setup
        incoming_message = cast(
            HttpMessage,
            self.build_incoming_message(
                message_type=HttpMessage,
                performative=HttpMessage.Performative.REQUEST,
                to=self.skill_id,
                sender=self.sender,
                method=self.get_method,
                url=self.url,
                version=self.version,
                headers=self.headers,
                body=self.body,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.http_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_outbox(1)

        mock_logger.assert_any_call(
            logging.INFO,
            "received http request with method={}, url={} and body={!r}".format(
                incoming_message.method, incoming_message.url, incoming_message.body
            ),
        )

        # _handle_get
        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=HttpMessage,
            performative=HttpMessage.Performative.RESPONSE,
            to=incoming_message.sender,
            sender=incoming_message.to,
            version=incoming_message.version,
            status_code=200,
            status_text="Success",
            headers=incoming_message.headers,
            body=json.dumps({"tom": {"type": "cat", "age": 10}}).encode("utf-8"),
        )
        assert has_attributes, error_str

        mock_logger.assert_any_call(
            logging.INFO,
            f"responding with: {message}",
        )

    def test_handle_request_post(self):
        """Test the _handle_request method of the http_echo handler where method is post."""
        # setup
        incoming_message = cast(
            HttpMessage,
            self.build_incoming_message(
                message_type=HttpMessage,
                performative=HttpMessage.Performative.REQUEST,
                to=self.skill_id,
                sender=self.sender,
                method=self.post_method,
                url=self.url,
                version=self.version,
                headers=self.headers,
                body=self.body,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.http_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_outbox(1)

        mock_logger.assert_any_call(
            logging.INFO,
            "received http request with method={}, url={} and body={!r}".format(
                incoming_message.method, incoming_message.url, incoming_message.body
            ),
        )

        # _handle_post
        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=HttpMessage,
            performative=HttpMessage.Performative.RESPONSE,
            to=incoming_message.sender,
            sender=incoming_message.to,
            version=incoming_message.version,
            status_code=200,
            status_text="Success",
            headers=incoming_message.headers,
            body=self.body,
        )
        assert has_attributes, error_str

        mock_logger.assert_any_call(
            logging.INFO,
            f"responding with: {message}",
        )

    def test_handle_invalid(self):
        """Test the _handle_invalid method of the http_echo handler."""
        # setup
        http_dialogue = self.prepare_skill_dialogue(
            dialogues=self.http_dialogues,
            messages=self.list_of_messages[:1],
        )
        incoming_message = cast(
            HttpMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=http_dialogue,
                performative=HttpMessage.Performative.RESPONSE,
                version=self.version,
                status_code=self.status_code,
                status_text=self.status_text,
                headers=self.headers,
                body=self.body,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.http_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.WARNING,
            f"cannot handle http message of performative={incoming_message.performative} in dialogue={http_dialogue}.",
        )

    def test_teardown(self):
        """Test the teardown method of the http_echo handler."""
        assert self.http_handler.teardown() is None
        self.assert_quantity_in_outbox(0)
