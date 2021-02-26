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

import json
import logging
from pathlib import Path
from typing import cast
from unittest.mock import patch

from vyper.utils import keccak256

from aea.protocols.dialogue.base import DialogueMessage
from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.protocols.http.message import HttpMessage
from packages.fetchai.skills.fetch_beacon.dialogues import HttpDialogues
from packages.fetchai.skills.fetch_beacon.handlers import HttpHandler

from tests.conftest import ROOT_DIR


class TestHttpHandler(BaseSkillTestCase):
    """Test http handler of fetch_beacon skill."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "fetch_beacon")
    is_agent_to_agent_messages = False

    @classmethod
    def setup(cls, **kwargs):
        """Setup the test class."""
        super().setup(**kwargs)
        cls.http_handler = cast(HttpHandler, cls._skill.skill_context.handlers.http)
        cls.logger = cls._skill.skill_context.logger

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

    def test_handle_response(self):
        """Test the _handle_response method of the http handler to a valid fetch beacon response."""
        # setup
        http_dialogue = self.prepare_skill_dialogue(
            dialogues=self.http_dialogues, messages=self.list_of_messages[:1],
        )

        test_response = {
            "result": {
                "block_id": {"hash": "00000000"},
                "block": {
                    "header": {
                        "height": "1",
                        "entropy": {"group_signature": "SIGNATURE"},
                    }
                },
            }
        }

        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=http_dialogue,
            performative=HttpMessage.Performative.RESPONSE,
            version="",
            status_code=200,
            status_text="",
            headers="",
            body=json.dumps(test_response).encode("utf-8"),
        )

        # handle message
        self.http_handler.handle(incoming_message)

        # check that data was correctly entered into shared state
        beacon_data = {
            "entropy": keccak256("SIGNATURE".encode("utf-8")),
            "block_hash": bytes.fromhex("00000000"),
            "block_height": 1,
        }
        assert self.http_handler.context.shared_state["oracle_data"] == beacon_data

        # check that outbox is empty
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

        assert "oracle_data" not in self.http_handler.context.shared_state

        # after
        mock_logger.assert_any_call(
            logging.INFO, "entropy not present",
        )

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

    def test_teardown(self):
        """Test the teardown method of the http handler."""
        assert self.http_handler.teardown() is None
        self.assert_quantity_in_outbox(0)
