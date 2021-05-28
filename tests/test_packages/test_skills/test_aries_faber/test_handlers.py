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
"""This module contains the tests of the handler classes of the aries_faber skill."""
import json
import logging
from typing import cast
from unittest.mock import patch

import pytest

from packages.fetchai.protocols.default.message import DefaultMessage
from packages.fetchai.protocols.http.message import HttpMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.aries_faber.dialogues import (
    HttpDialogue,
    OefSearchDialogue,
)
from packages.fetchai.skills.aries_faber.handlers import SUPPORT_REVOCATION
from packages.fetchai.skills.aries_faber.strategy import (
    ADMIN_COMMAND_CREATE_INVITATION,
    ADMIN_COMMAND_CREDDEF,
    ADMIN_COMMAND_SCEHMAS,
    ADMIN_COMMAND_STATUS,
    FABER_ACA_IDENTITY,
    LEDGER_COMMAND_REGISTER_DID,
)

from tests.test_packages.test_skills.test_aries_faber.intermediate_class import (
    AriesFaberTestCase,
)


class TestHttpHandler(AriesFaberTestCase):
    """Test http handler of aries_faber."""

    is_agent_to_agent_messages = False

    def test__init__i(self):
        """Test the __init__ method of the http_request behaviour."""
        assert self.http_handler.faber_identity == FABER_ACA_IDENTITY
        assert self.http_handler.seed[:-6] == "d_000000000000000000000000"
        assert self.http_handler.did is None
        assert self.http_handler._schema_id is None
        assert self.http_handler.credential_definition_id is None
        assert self.http_handler.connection_id is None
        assert self.http_handler.is_connected_to_Alice is False

    def test_setup(self):
        """Test the setup method of the http_handler handler."""
        assert self.http_handler.setup() is None
        self.assert_quantity_in_outbox(0)

    def test_properties(self):
        """Test the properties of the http_handler handler."""
        self.http_handler._schema_id = None
        with pytest.raises(ValueError, match="schema_id not set"):
            assert self.http_handler.schema_id is None
        self.http_handler._schema_id = "some_schema_id"
        assert self.http_handler.schema_id == "some_schema_id"

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
            "something went wrong when adding the incoming HTTP message to the dialogue.",
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
        mock_logger.assert_any_call(
            logging.INFO, f"Received webhook message content:{str(body)}"
        )
        mock_logger.assert_any_call(logging.INFO, "Connected to Alice")
        assert self.http_handler.is_connected_to_Alice is True

    def test_handle_response_i(self):
        """Test the handle method of the http handler where performative is RESPONSE and content has version."""
        # setup
        data = {
            "alias": self.http_handler.faber_identity,
            "seed": self.http_handler.seed,
            "role": "TRUST_ANCHOR",
        }
        http_dialogue = cast(
            HttpDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.http_dialogues, messages=self.list_of_http_messages[:1],
            ),
        )

        body = {"version": "some_version"}
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
        with patch.object(
            self.faber_behaviour, "send_http_request_message"
        ) as mock_http_req:
            with patch.object(self.logger, "log") as mock_logger:
                self.http_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(logging.INFO, f"Received message: {str(body)}")

        mock_logger.assert_any_call(
            logging.INFO,
            f"Registering Faber_ACA with seed {str(self.http_handler.seed)}",
        )
        mock_http_req.assert_any_call(
            method="POST",
            url=self.strategy.ledger_url + LEDGER_COMMAND_REGISTER_DID,
            content=data,
        )

    def test_handle_response_ii(self):
        """Test the handle method of the http handler where performative is RESPONSE and content has did."""
        # setup
        did = "some_did"
        schema_body = {
            "schema_name": "degree schema",
            "schema_version": "0.0.1",
            "attributes": ["name", "date", "degree", "age", "timestamp"],
        }
        http_dialogue = cast(
            HttpDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.http_dialogues, messages=self.list_of_http_messages[:1],
            ),
        )

        body = {"did": did}
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
        with patch.object(
            self.faber_behaviour, "send_http_request_message"
        ) as mock_http_req:
            with patch.object(self.logger, "log") as mock_logger:
                self.http_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(logging.INFO, f"Received message: {str(body)}")

        mock_logger.assert_any_call(
            logging.INFO, f"Registering schema {str(schema_body)}"
        )
        assert self.http_handler.did == did
        mock_http_req.assert_any_call(
            method="POST",
            url=self.strategy.admin_url + ADMIN_COMMAND_SCEHMAS,
            content=schema_body,
        )

    def test_handle_response_iii(self):
        """Test the handle method of the http handler where performative is RESPONSE and content has schema_id."""
        # setup
        schema_id = "some_schema_id"
        credential_definition_body = {
            "schema_id": schema_id,
            "support_revocation": SUPPORT_REVOCATION,
        }
        http_dialogue = cast(
            HttpDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.http_dialogues, messages=self.list_of_http_messages[:1],
            ),
        )

        body = {"schema_id": schema_id}
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
        with patch.object(
            self.faber_behaviour, "send_http_request_message"
        ) as mock_http_req:
            with patch.object(self.logger, "log") as mock_logger:
                self.http_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(logging.INFO, f"Received message: {str(body)}")

        assert self.http_handler.schema_id == schema_id
        mock_http_req.assert_any_call(
            method="POST",
            url=self.strategy.admin_url + ADMIN_COMMAND_CREDDEF,
            content=credential_definition_body,
        )

    def test_handle_response_iv(self):
        """Test the handle method of the http handler where performative is RESPONSE and content has credential_definition_id."""
        # setup
        credential_definition_id = "some_credential_definition_id"
        http_dialogue = cast(
            HttpDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.http_dialogues, messages=self.list_of_http_messages[:1],
            ),
        )

        body = {"credential_definition_id": credential_definition_id}
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
        with patch.object(
            self.faber_behaviour, "send_http_request_message"
        ) as mock_http_req:
            with patch.object(self.logger, "log") as mock_logger:
                self.http_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(logging.INFO, f"Received message: {str(body)}")

        assert self.http_handler.credential_definition_id == credential_definition_id
        mock_http_req.assert_any_call(
            method="POST", url=self.strategy.admin_url + ADMIN_COMMAND_CREATE_INVITATION
        )

    def test_handle_response_v(self):
        """Test the handle method of the http handler where performative is RESPONSE and content has connection_id."""
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
        self.assert_quantity_in_outbox(1)

        mock_logger.assert_any_call(logging.INFO, f"Received message: {str(body)}")

        assert self.http_handler.connection_id == connection_id
        mock_logger.assert_any_call(logging.INFO, f"connection: {str(body)}")
        mock_logger.assert_any_call(logging.INFO, f"connection id: {connection_id}")
        mock_logger.assert_any_call(logging.INFO, f"invitation: {str(invitation)}")
        mock_logger.assert_any_call(
            logging.INFO,
            "Sent invitation to Alice. Waiting for the invitation from Alice to finalise the connection...",
        )

        # _send_default_message
        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=DefaultMessage,
            performative=DefaultMessage.Performative.BYTES,
            to=self.strategy.alice_aea_address,
            sender=self.skill.skill_context.agent_address,
            content=json.dumps(invitation).encode("utf-8"),
        )
        assert has_attributes, error_str

    def test_teardown(self):
        """Test the teardown method of the http handler."""
        assert self.http_handler.teardown() is None
        self.assert_quantity_in_outbox(0)


class TestOefSearchHandler(AriesFaberTestCase):
    """Test oef_search handler of aries_faber."""

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
                messages=self.list_of_oef_search_messages[:1],
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

    def test_handle_search_i(self):
        """Test the _handle_search method of the oef_search handler where the number of agents found is NOT 0."""
        # setup
        alice_address = "alice"
        agents = (alice_address,)
        oef_search_dialogue = cast(
            OefSearchDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.oef_search_dialogues,
                messages=self.list_of_oef_search_messages[:1],
            ),
        )
        incoming_message = cast(
            OefSearchMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=oef_search_dialogue,
                performative=OefSearchMessage.Performative.SEARCH_RESULT,
                agents=agents,
                agents_info=OefSearchMessage.AgentsInfo(
                    {
                        "agent_1": {"key_1": "value_1", "key_2": "value_2"},
                        "agent_2": {"key_3": "value_3", "key_4": "value_4"},
                    }
                ),
            ),
        )

        # operation
        with patch.object(
            self.faber_behaviour, "send_http_request_message"
        ) as mock_http_req:
            with patch.object(self.logger, "log") as mock_logger:
                self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO, f"found Alice with address {alice_address}, stopping search.",
        )

        assert self.strategy.is_searching is False
        assert self.strategy.alice_aea_address is alice_address
        mock_http_req.assert_any_call(
            "GET", self.strategy.admin_url + ADMIN_COMMAND_STATUS
        )

    def test_handle_search_ii(self):
        """Test the _handle_search method of the oef_search handler where the number of agents found is 0."""
        # setup
        agents = tuple()
        oef_search_dialogue = cast(
            OefSearchDialogue,
            self.prepare_skill_dialogue(
                dialogues=self.oef_search_dialogues,
                messages=self.list_of_oef_search_messages[:1],
            ),
        )
        incoming_message = cast(
            OefSearchMessage,
            self.build_incoming_message_for_skill_dialogue(
                dialogue=oef_search_dialogue,
                performative=OefSearchMessage.Performative.SEARCH_RESULT,
                agents=agents,
                agents_info=OefSearchMessage.AgentsInfo({}),
            ),
        )

        # operation
        with patch.object(self.logger, "log") as mock_logger:
            self.oef_search_handler.handle(incoming_message)

        # after
        mock_logger.assert_any_call(
            logging.INFO, "did not find Alice. found 0 agents. continue searching.",
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
