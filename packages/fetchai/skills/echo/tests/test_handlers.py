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
"""This module contains the tests of the handler class of the echo skill."""
# pylint: skip-file

import inspect
import logging
import os
from pathlib import Path
from typing import cast
from unittest.mock import patch

from aea.protocols.dialogue.base import DialogueMessage
from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.protocols.default.message import DefaultMessage
from packages.fetchai.skills.echo.dialogues import DefaultDialogues
from packages.fetchai.skills.echo.handlers import EchoHandler


CUR_PATH = os.path.dirname(inspect.getfile(inspect.currentframe()))  # type: ignore


class TestEchoHandler(BaseSkillTestCase):
    """Test EchoHandler of echo."""

    path_to_skill = Path(CUR_PATH, "..")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.echo_handler = cast(EchoHandler, cls._skill.skill_context.handlers.echo)
        cls.logger = cls._skill.skill_context.logger

        cls.default_dialogues = cast(
            DefaultDialogues, cls._skill.skill_context.default_dialogues
        )

        cls.content = b"some_content"
        cls.list_of_messages = (
            DialogueMessage(
                DefaultMessage.Performative.BYTES, {"content": cls.content}
            ),
        )

    def test_setup(self):
        """Test the setup method of the echo handler."""
        with patch.object(self.logger, "log") as mock_logger:
            assert self.echo_handler.setup() is None

        # after
        self.assert_quantity_in_outbox(0)

        mock_logger.assert_any_call(logging.INFO, "Echo Handler: setup method called.")

    def test_handle_unidentified_dialogue(self):
        """Test the _handle_unidentified_dialogue method of the oef_search handler."""
        # setup
        incorrect_dialogue_reference = ("", "")
        incoming_message = self.build_incoming_message(
            message_type=DefaultMessage,
            dialogue_reference=incorrect_dialogue_reference,
            performative=DefaultMessage.Performative.BYTES,
            content=self.content,
            to=self.skill.skill_context.agent_name,
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.echo_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received invalid default message={incoming_message}, unidentified dialogue.",
        )

    def test_handle_error(self):
        """Test the _handle_error method of the oef_search handler."""
        # setup
        default_dialogue = self.prepare_skill_dialogue(
            dialogues=self.default_dialogues,
            messages=self.list_of_messages[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=default_dialogue,
            performative=DefaultMessage.Performative.ERROR,
            error_code=DefaultMessage.ErrorCode.INVALID_DIALOGUE,
            error_msg="Invalid dialogue.",
            error_data={"default_message": b"some_bytes"},
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.echo_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received default error message={incoming_message} in dialogue={default_dialogue}.",
        )

    def test_handle_bytes(self):
        """Test the _handle_error method of the oef_search handler."""
        # setup
        default_dialogue = self.prepare_skill_dialogue(
            dialogues=self.default_dialogues,
            messages=self.list_of_messages[:1],
        )
        incoming_message = cast(
            DefaultMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=default_dialogue,
                performative=DefaultMessage.Performative.BYTES,
                content=self.content,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.echo_handler.handle(incoming_message)

        # after
        self.assert_quantity_in_outbox(1)

        mock_logger.assert_any_call(
            logging.INFO,
            f"Echo Handler: message={incoming_message}, sender={incoming_message.sender}",
        )

        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=DefaultMessage,
            performative=DefaultMessage.Performative.BYTES,
            to=incoming_message.sender,
            sender=self.skill.skill_context.agent_name,
            target=incoming_message.message_id,
            content=incoming_message.content,
        )
        assert has_attributes, error_str

    def test_handle_invalid(self):
        """Test the _handle_invalid method of the echo handler."""
        # setup
        default_dialogue = self.prepare_skill_dialogue(
            dialogues=self.default_dialogues,
            messages=self.list_of_messages[:1],
        )
        incoming_message = cast(
            DefaultMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=default_dialogue,
                performative=DefaultMessage.Performative.END,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.echo_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received invalid message={incoming_message} in dialogue={self.default_dialogues.get_dialogue(incoming_message)}.",
        )

    def test_retrieve_protocol_dialogues_from_handler(self):
        """Test retrieve protocol dialogues from handler"""
        assert self.echo_handler.protocol_dialogues() is self.default_dialogues

    def test_teardown(self):
        """Test the teardown method of the echo handler."""
        with patch.object(self.logger, "log") as mock_logger:
            assert self.echo_handler.teardown() is None

        # after
        self.assert_quantity_in_outbox(0)

        mock_logger.assert_any_call(
            logging.INFO, "Echo Handler: teardown method called."
        )
