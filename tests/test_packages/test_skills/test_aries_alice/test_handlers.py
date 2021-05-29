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
"""This module contains the tests of the handler classes of the aries_alice skill."""
import json
import logging
from typing import cast
from unittest.mock import patch

from aea.protocols.dialogue.base import Dialogues

from packages.fetchai.protocols.default.message import DefaultMessage
from packages.fetchai.protocols.http.message import HttpMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.aries_alice.dialogues import (
    HttpDialogue,
    OefSearchDialogue,
)
from packages.fetchai.skills.aries_alice.handlers import ADMIN_COMMAND_RECEIVE_INVITE

from tests.test_packages.test_skills.test_aries_alice.intermediate_class import (
    AriesAliceTestCase,
)


class TestDefaultHandler(AriesAliceTestCase):
    """Test default handler of aries_alice."""

    def test_setup(self):
        """Test the setup method of the default handler."""
        assert self.default_handler.setup() is None
        self.assert_quantity_in_outbox(0)

    def test_handle_i(self):
        """Test the handle method of the default handler where @type is in content."""
        # setup
        content = "@type=something"
        content_bytes = json.dumps(content).encode("utf-8")
        details = "some_details"
        incoming_message = cast(
            DefaultMessage,
            self.build_incoming_message(
                message_type=DefaultMessage,
                performative=DefaultMessage.Performative.BYTES,
                dialogue_reference=Dialogues.new_self_initiated_dialogue_reference(),
                content=content_bytes,
            ),
        )

        # operation
        with patch.object(
            self.default_handler, "_handle_received_invite", return_value=details
        ) as mock_invite:
            with patch.object(
                self.alice_behaviour, "send_http_request_message"
            ) as mock_send:
                with patch.object(self.logger, "log") as mock_logger:
                    self.default_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO, f"Received message content:{content}",
        )
        mock_invite.assert_called_once()
        mock_send.assert_any_call(
            method="POST",
            url=self.strategy.admin_url + ADMIN_COMMAND_RECEIVE_INVITE,
            content=details,
        )

    def test_handle_ii(self):
        """Test the handle method of the default handler where http_dialogue is None."""
        # setup
        details = "some_details"
        incoming_message = cast(
            DefaultMessage,
            self.build_incoming_message(
                message_type=DefaultMessage,
                performative=DefaultMessage.Performative.ERROR,
                dialogue_reference=("", ""),
                error_code=DefaultMessage.ErrorCode.INVALID_DIALOGUE,
                error_msg="some_error_msg",
                error_data={"some_key": b"some_bytes"},
            ),
        )

        # operation
        with patch.object(
            self.default_handler, "_handle_received_invite", return_value=details
        ) as mock_invite:
            with patch.object(
                self.alice_behaviour, "send_http_request_message"
            ) as mock_send:
                with patch.object(self.logger, "log") as mock_logger:
                    self.default_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.ERROR,
            "alice -> default_handler -> handle(): something went wrong when adding the incoming default message to the dialogue.",
        )
        mock_invite.assert_not_called()
        mock_send.assert_not_called()

    def test_teardown(self):
        """Test the teardown method of the default handler."""
        assert self.default_handler.teardown() is None
        self.assert_quantity_in_outbox(0)


class TestHttpHandler(AriesAliceTestCase):
    """Test http handler of aries_alice."""

    is_agent_to_agent_messages = False

    def test_setup(self):
        """Test the setup method of the http_handler handler."""
        assert self.http_handler.setup() is None
        self.assert_quantity_in_outbox(0)

    def test_handle_unidentified_dialogue(self):
        """Test the handle method of the http handler where incoming message is invalid."""
        # setup
        incorrect_dialogue_reference = ("", "")
        incoming_message = cast(
            HttpMessage,
            self.build_incoming_message(
                message_type=HttpMessage,
                dialogue_reference=incorrect_dialogue_reference,
                performative=HttpMessage.Performative.REQUEST,
                method=self.mocked_method,
                url=self.mocked_url,
                headers=self.mocked_headers,
                version=self.mocked_version,
                body=self.mocked_body_bytes,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.http_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.ERROR,
            "alice -> http_handler -> handle() -> REQUEST: something went wrong when adding the incoming HTTP webhook request message to the dialogue.",
        )

    def test_handle_request(self):
        """Test the handle method of the http handler where performative is REQUEST."""
        # setup
        self.http_handler.connection_id = 123
        self.http_handler.is_connected_to_Faber = False

        body = {"connection_id": 123, "state": "active"}
        mocked_body_bytes = json.dumps(body).encode("utf-8")
        incoming_message = cast(
            HttpMessage,
            self.build_incoming_message(
                message_type=HttpMessage,
                performative=HttpMessage.Performative.REQUEST,
                method=self.mocked_method,
                url=self.mocked_url,
                headers=self.mocked_headers,
                version=self.mocked_version,
                body=mocked_body_bytes,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.http_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(logging.INFO, "Connected to Faber")
        assert self.http_handler.is_connected_to_Faber is True

    def test_handle_response_i(self):
        """Test the handle method of the http handler where performative is RESPONSE and content has Error."""
        # setup
        http_dialogue = cast(
            HttpDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.http_dialogues, messages=self.list_of_http_messages[:1],
            ),
        )

        body = {"Error": "something"}
        mocked_body_bytes = json.dumps(body).encode("utf-8")
        incoming_message = cast(
            HttpMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=http_dialogue,
                performative=HttpMessage.Performative.RESPONSE,
                status_code=200,
                status_text="some_status_code",
                headers=self.mocked_headers,
                version=self.mocked_version,
                body=mocked_body_bytes,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.http_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.ERROR,
            "Something went wrong after I sent the administrative command of 'invitation receive'",
        )

    def test_handle_response_ii(self):
        """Test the handle method of the http handler where performative is RESPONSE and content does NOT have Error."""
        # setup
        connection_id = 2342
        invitation = {"some_key": "some_value"}
        http_dialogue = cast(
            HttpDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.http_dialogues, messages=self.list_of_http_messages[:1],
            ),
        )

        body = {"connection_id": connection_id, "invitation": invitation}
        mocked_body_bytes = json.dumps(body).encode("utf-8")
        incoming_message = cast(
            HttpMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=http_dialogue,
                performative=HttpMessage.Performative.RESPONSE,
                status_code=200,
                status_text="some_status_code",
                headers=self.mocked_headers,
                version=self.mocked_version,
                body=mocked_body_bytes,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.http_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO, f"Received http response message content:{body}"
        )
        assert self.http_handler.connection_id == connection_id
        mock_logger.assert_any_call(logging.INFO, f"invitation response: {str(body)}")
        mock_logger.assert_any_call(logging.INFO, f"connection id: {connection_id}")
        mock_logger.assert_any_call(logging.INFO, f"invitation: {str(invitation)}")

    def test_teardown(self):
        """Test the teardown method of the http handler."""
        assert self.http_handler.teardown() is None
        self.assert_quantity_in_outbox(0)


class TestOefSearchHandler(AriesAliceTestCase):
    """Test oef_search handler of aries_alice."""

    is_agent_to_agent_messages = False

    def test_setup(self):
        """Test the setup method of the oef_search handler."""
        assert self.oef_search_handler.setup() is None
        self.assert_quantity_in_outbox(0)

    def test_handle_unidentified_dialogue(self):
        """Test the _handle_unidentified_dialogue method of the oef_search handler."""
        # setup
        incorrect_dialogue_reference = ("", "")
        incoming_message = cast(
            OefSearchMessage,
            self.build_incoming_message(
                message_type=OefSearchMessage,
                dialogue_reference=incorrect_dialogue_reference,
                performative=OefSearchMessage.Performative.OEF_ERROR,
                oef_error_operation=OefSearchMessage.OefErrorOperation.REGISTER_SERVICE,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received invalid oef_search message={incoming_message}, unidentified dialogue.",
        )

    def test_handle_error(self):
        """Test the _handle_error method of the oef_search handler."""
        # setup
        oef_search_dialogue = cast(
            OefSearchDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.oef_search_dialogues,
                messages=self.list_of_messages_register_location[:1],
            ),
        )
        incoming_message = cast(
            OefSearchMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=oef_search_dialogue,
                performative=OefSearchMessage.Performative.OEF_ERROR,
                oef_error_operation=OefSearchMessage.OefErrorOperation.REGISTER_SERVICE,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received oef_search error message={incoming_message} in dialogue={oef_search_dialogue}.",
        )

    def test_handle_success_i(self):
        """Test the _handle_success method of the oef_search handler where the oef success targets register_service WITH location_agent data model description."""
        # setup
        oef_dialogue = self.prepare_skill_dialogue(
            dialogues=self.oef_search_dialogues,
            messages=self.list_of_messages_register_location[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=oef_dialogue,
            performative=OefSearchMessage.Performative.SUCCESS,
            agents_info=OefSearchMessage.AgentsInfo({"address": {"key": "value"}}),
        )

        # operation
        with patch.object(self.oef_search_handler.context.logger, "log") as mock_logger:
            with patch.object(self.alice_behaviour, "register_service",) as mock_reg:
                self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received oef_search success message={incoming_message} in dialogue={oef_dialogue}.",
        )
        mock_reg.assert_called_once()

    def test_handle_success_ii(self):
        """Test the _handle_success method of the oef_search handler where the oef success targets register_service WITH set_service_key data model description."""
        # setup
        oef_dialogue = self.prepare_skill_dialogue(
            dialogues=self.oef_search_dialogues,
            messages=self.list_of_messages_register_service[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=oef_dialogue,
            performative=OefSearchMessage.Performative.SUCCESS,
            agents_info=OefSearchMessage.AgentsInfo({"address": {"key": "value"}}),
        )

        # operation
        with patch.object(self.oef_search_handler.context.logger, "log") as mock_logger:
            with patch.object(self.alice_behaviour, "register_genus",) as mock_reg:
                self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received oef_search success message={incoming_message} in dialogue={oef_dialogue}.",
        )
        mock_reg.assert_called_once()

    def test_handle_success_iii(self):
        """Test the _handle_success method of the oef_search handler where the oef success targets register_service WITH personality_agent data model and genus value description."""
        # setup
        oef_dialogue = self.prepare_skill_dialogue(
            dialogues=self.oef_search_dialogues,
            messages=self.list_of_messages_register_genus[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=oef_dialogue,
            performative=OefSearchMessage.Performative.SUCCESS,
            agents_info=OefSearchMessage.AgentsInfo({"address": {"key": "value"}}),
        )

        # operation
        with patch.object(self.oef_search_handler.context.logger, "log") as mock_logger:
            with patch.object(
                self.alice_behaviour, "register_classification",
            ) as mock_reg:
                self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received oef_search success message={incoming_message} in dialogue={oef_dialogue}.",
        )
        mock_reg.assert_called_once()

    def test_handle_success_iv(self):
        """Test the _handle_success method of the oef_search handler where the oef success targets register_service WITH personality_agent data model and classification value description."""
        # setup
        oef_dialogue = self.prepare_skill_dialogue(
            dialogues=self.oef_search_dialogues,
            messages=self.list_of_messages_register_classification[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=oef_dialogue,
            performative=OefSearchMessage.Performative.SUCCESS,
            agents_info=OefSearchMessage.AgentsInfo({"address": {"key": "value"}}),
        )

        # operation
        with patch.object(self.oef_search_handler.context.logger, "log") as mock_logger:
            self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received oef_search success message={incoming_message} in dialogue={oef_dialogue}.",
        )

        mock_logger.assert_any_call(
            logging.INFO,
            "the agent, with its genus and classification, and its service are successfully registered on the SOEF.",
        )

    def test_handle_success_v(self):
        """Test the _handle_success method of the oef_search handler where the oef success targets unregister_service."""
        # setup
        oef_dialogue = self.prepare_skill_dialogue(
            dialogues=self.oef_search_dialogues,
            messages=self.list_of_messages_register_invalid[:1],
        )
        incoming_message = self.build_incoming_message_for_skill_dialogue(
            dialogue=oef_dialogue,
            performative=OefSearchMessage.Performative.SUCCESS,
            agents_info=OefSearchMessage.AgentsInfo({"address": {"key": "value"}}),
        )

        # operation
        with patch.object(self.oef_search_handler.context.logger, "log") as mock_logger:
            self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO,
            f"received oef_search success message={incoming_message} in dialogue={oef_dialogue}.",
        )
        mock_logger.assert_any_call(
            logging.WARNING,
            f"received soef SUCCESS message as a reply to the following unexpected message: {oef_dialogue.get_message_by_id(incoming_message.target)}",
        )

    def test_handle_invalid(self):
        """Test the _handle_invalid method of the oef_search handler."""
        # setup
        incoming_message = cast(
            OefSearchMessage,
            self.build_incoming_message(
                message_type=OefSearchMessage,
                performative=OefSearchMessage.Performative.REGISTER_SERVICE,
                service_description=self.mocked_proposal,
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.WARNING,
            f"cannot handle oef_search message of performative={incoming_message.performative} in dialogue={self.oef_search_dialogues.get_dialogue(incoming_message)}.",
        )

    def test_teardown(self):
        """Test the teardown method of the oef_search handler."""
        assert self.oef_search_handler.teardown() is None
        self.assert_quantity_in_outbox(0)
