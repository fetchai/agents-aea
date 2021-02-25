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
"""This module contains the tests of the handler classes of the confirmation aw3 skill."""

import logging
from pathlib import Path
from typing import cast
from unittest.mock import patch

from aea.crypto.ledger_apis import LedgerApis
from aea.protocols.dialogue.base import DialogueMessage

from packages.fetchai.protocols.default.dialogues import DefaultDialogue
from packages.fetchai.protocols.default.message import DefaultMessage
from packages.fetchai.protocols.http.message import HttpMessage
from packages.fetchai.skills.confirmation_aw3.dialogues import (
    DefaultDialogues,
    HttpDialogue,
    HttpDialogues,
)
from packages.fetchai.skills.confirmation_aw3.handlers import (
    DefaultHandler,
    HttpHandler,
)
from packages.fetchai.skills.confirmation_aw3.strategy import Strategy

from tests.conftest import ROOT_DIR
from tests.test_packages.test_skills.test_confirmation_aw3.intermediate_class import (
    ConfirmationAW3TestCase,
)


class TestDefaultHandler(ConfirmationAW3TestCase):
    """Test default handler of confirmation aw3."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "confirmation_aw3")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.default_handler = cast(
            DefaultHandler, cls._skill.skill_context.handlers.default_handler
        )
        cls.logger = cls._skill.skill_context.logger
        cls.strategy = cast(Strategy, cls._skill.skill_context.strategy)

        cls.default_dialogues = cast(
            DefaultDialogues, cls._skill.skill_context.default_dialogues
        )

        cls.list_of_default_messages = (
            DialogueMessage(
                DefaultMessage.Performative.BYTES, {"content": b"some_content"}
            ),
        )

        cls.confirmed_aea = b"ConfirmedAEA"
        cls.developer_handle = b"DeveloperHandle"

    def test_setup(self):
        """Test the setup method of the default handler."""
        assert self.default_handler.setup() is None
        self.assert_quantity_in_outbox(0)

    def test_handle_unidentified_dialogue(self):
        """Test the _handle_unidentified_dialogue method of the register handler."""
        # setup
        incorrect_dialogue_reference = ("", "")
        incoming_message = self.build_incoming_message(
            message_type=DefaultMessage,
            dialogue_reference=incorrect_dialogue_reference,
            performative=DefaultMessage.Performative.BYTES,
            content=b"some_content",
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.default_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received invalid default message={incoming_message}, unidentified dialogue.",
        )

    def test_handle_bytes_i(self):
        """Test the _handle_bytes method of the default handler where the sender IS aw1_aea."""
        # setup
        incoming_message = cast(
            DefaultMessage,
            self.build_incoming_message(
                message_type=DefaultMessage,
                performative=DefaultMessage.Performative.BYTES,
                content=self.confirmed_aea + b"_" + self.developer_handle,
                sender=self.aw1_aea,
            ),
        )

        # operation
        with patch.object(LedgerApis, "is_valid_address", return_value=True):
            with patch.object(self.logger, "log") as mock_logger:
                with patch.object(
                    self.strategy, "register_counterparty"
                ) as mock_register:
                    self.default_handler.handle(incoming_message)

        # after
        mock_register.called_once()

        mock_logger.assert_any_call(
            logging.INFO,
            f"adding confirmed_aea={self.confirmed_aea.decode('utf-8')} with developer_handle={self.developer_handle.decode('utf-8')} to db.",
        )

    def test_handle_bytes_ii(self):
        """Test the _handle_bytes method of the default handler where the content is undecodable."""
        # setup
        incorrect_content = "some_incorrect_content"

        incoming_message = cast(
            DefaultMessage,
            self.build_incoming_message(
                message_type=DefaultMessage,
                performative=DefaultMessage.Performative.BYTES,
                content=incorrect_content,
                sender=self.aw1_aea,
            ),
        )

        # operation
        with patch.object(LedgerApis, "is_valid_address", return_value=True):
            with patch.object(self.logger, "log") as mock_logger:
                with patch.object(
                    self.strategy, "register_counterparty"
                ) as mock_register:
                    self.default_handler.handle(incoming_message)

        # after
        mock_register.called_once()

        mock_logger.assert_any_call(
            logging.WARNING, "received invalid developer_handle=."
        )

    def test_handle_bytes_iii(self):
        """Test the _handle_bytes method of the default handler where is_valid_address is False."""
        # setup
        incoming_message = cast(
            DefaultMessage,
            self.build_incoming_message(
                message_type=DefaultMessage,
                performative=DefaultMessage.Performative.BYTES,
                content=self.confirmed_aea + b"_" + self.developer_handle,
                sender=self.aw1_aea,
            ),
        )

        # operation
        with patch.object(LedgerApis, "is_valid_address", return_value=False):
            with patch.object(self.logger, "log") as mock_logger:
                with patch.object(
                    self.strategy, "register_counterparty"
                ) as mock_register:
                    self.default_handler.handle(incoming_message)

        # after
        mock_register.called_once()

        default_dialogue = cast(
            DefaultDialogue, self.default_dialogues.get_dialogue(incoming_message)
        )

        mock_logger.assert_any_call(
            logging.WARNING,
            f"received invalid address={self.confirmed_aea.decode('utf-8')} in dialogue={default_dialogue}.",
        )

    def test_handle_bytes_iv(self):
        """Test the _handle_bytes method of the default handler where the sender is NOT aw1_aea."""
        # setup
        incoming_message = cast(
            DefaultMessage,
            self.build_incoming_message(
                message_type=DefaultMessage,
                performative=DefaultMessage.Performative.BYTES,
                content=self.confirmed_aea + b"_" + self.developer_handle,
                sender="some_other_aea",
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            with patch.object(self.strategy, "register_counterparty") as mock_register:
                self.default_handler.handle(incoming_message)

        # after
        mock_register.called_once()

        default_dialogue = cast(
            DefaultDialogue, self.default_dialogues.get_dialogue(incoming_message)
        )

        mock_logger.assert_any_call(
            logging.WARNING,
            f"cannot handle default message of performative={incoming_message.performative} in dialogue={default_dialogue}. Invalid sender={incoming_message.sender}",
        )

    def test_handle_invalid(self):
        """Test the _handle_invalid method of the default handler."""
        # setup
        default_dialogue = cast(
            DefaultDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.default_dialogues,
                messages=self.list_of_default_messages[:1],
            ),
        )
        incoming_message = cast(
            DefaultMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=default_dialogue,
                performative=DefaultMessage.Performative.ERROR,
                error_code=DefaultMessage.ErrorCode.DECODING_ERROR,
                error_msg="some_error_message",
                error_data={"some_key": b"some_value"},
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.default_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.WARNING,
            f"cannot handle default message of performative={incoming_message.performative} in dialogue={default_dialogue}.",
        )

    def test_teardown(self):
        """Test the teardown method of the default handler."""
        assert self.default_handler.teardown() is None
        self.assert_quantity_in_outbox(0)


class TestHttpHandler(ConfirmationAW3TestCase):
    """Test http handler of confirmation aw3."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "confirmation_aw3")
    is_agent_to_agent_messages = False

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.http_handler = cast(
            HttpHandler, cls._skill.skill_context.handlers.http_handler
        )
        cls.logger = cls._skill.skill_context.logger
        cls.strategy = cast(Strategy, cls._skill.skill_context.strategy)

        cls.http_dialogues = cast(
            HttpDialogues, cls._skill.skill_context.http_dialogues
        )

        cls.method = "some_method"
        cls.url = "some_url"
        cls.version = "some_version"
        cls.headers = "some_headers"
        cls.body = b"some_body"

        cls.list_of_http_messages = (
            DialogueMessage(
                HttpMessage.Performative.REQUEST,
                {
                    "method": cls.method,
                    "url": cls.url,
                    "version": cls.version,
                    "headers": cls.headers,
                    "body": cls.body,
                },
            ),
        )

        cls.confirmed_aea = b"ConfirmedAEA"
        cls.developer_handle = b"DeveloperHandle"

    def test_setup(self):
        """Test the setup method of the http handler."""
        assert self.http_handler.setup() is None
        self.assert_quantity_in_outbox(0)

    def test_handle_unidentified_dialogue(self):
        """Test the _handle_unidentified_dialogue method of the register handler."""
        # setup
        incorrect_dialogue_reference = ("", "")
        incoming_message = self.build_incoming_message(
            message_type=HttpMessage,
            dialogue_reference=incorrect_dialogue_reference,
            performative=HttpMessage.Performative.RESPONSE,
            version=self.version,
            status_code=200,
            status_text="some_status_text",
            headers=self.headers,
            body=self.body,
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.http_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received invalid http message={incoming_message}, unidentified dialogue.",
        )

    def test__handle_response(self):
        """Test the _handle_bytes method of the http handler where the sender IS aw1_aea."""
        # setup
        status_code = 200
        status_text = "some_status_text"

        http_dialogue = cast(
            HttpDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.http_dialogues, messages=self.list_of_http_messages[:1],
            ),
        )

        incoming_message = cast(
            HttpMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=http_dialogue,
                performative=HttpMessage.Performative.RESPONSE,
                version=self.version,
                status_code=status_code,
                status_text=status_text,
                headers=self.headers,
                body=self.body,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.http_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            "received http response with status_code={}, status_text={} and body={!r} in dialogue={}".format(
                status_code, status_text, self.body, http_dialogue
            ),
        )

    def test_handle_invalid(self):
        """Test the _handle_invalid method of the http handler."""
        # setup
        incoming_message = cast(
            HttpMessage,
            self.build_incoming_message(
                message_type=HttpMessage,
                performative=HttpMessage.Performative.REQUEST,
                method=self.method,
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
        http_dialogue = cast(
            HttpDialogue, self.http_dialogues.get_dialogue(incoming_message)
        )
        mock_logger.assert_any_call(
            logging.WARNING,
            f"cannot handle http message of performative={incoming_message.performative} in dialogue={http_dialogue}.",
        )

    def test_teardown(self):
        """Test the teardown method of the http handler."""
        assert self.http_handler.teardown() is None
        self.assert_quantity_in_outbox(0)
