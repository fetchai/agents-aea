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
"""This module contains the tests of the behaviour classes of the aries_alice skill."""

import json
import logging
from unittest.mock import patch

from packages.fetchai.protocols.http.message import HttpMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.aries_alice.behaviours import HTTP_CLIENT_PUBLIC_ID

from tests.test_packages.test_skills.test_aries_alice.intermediate_class import (
    AriesAliceTestCase,
)


class TestAliceBehaviour(AriesAliceTestCase):
    """Test alice behaviour of aries_alice."""

    def test_init(self):
        """Test the __init__ method of the alice behaviour."""
        assert self.alice_behaviour.failed_registration_msg is None
        assert self.alice_behaviour._nb_retries == 0

    def test_send_http_request_message(self):
        """Test the send_http_request_message method of the alice behaviour."""
        # operation
        self.alice_behaviour.send_http_request_message(
            self.mocked_method, self.mocked_url, self.body_dict
        )

        # after
        self.assert_quantity_in_outbox(1)

        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=HttpMessage,
            performative=HttpMessage.Performative.REQUEST,
            to=str(HTTP_CLIENT_PUBLIC_ID),
            sender=str(self.skill.skill_context.skill_id),
            method=self.mocked_method,
            url=self.mocked_url,
            headers="",
            version="",
            body=json.dumps(self.body_dict).encode("utf-8"),
        )
        assert has_attributes, error_str

    def test_setup(self):
        """Test the setup method of the alice behaviour."""
        # operation
        with patch.object(
            self.strategy,
            "get_location_description",
            return_value=self.mocked_registration_description,
        ) as mock_desc:
            with patch.object(self.logger, "log") as mock_logger:
                self.alice_behaviour.setup()

        # after
        self.assert_quantity_in_outbox(1)

        mock_logger.assert_any_call(
            logging.INFO, f"My address is: {self.skill.skill_context.agent_address}"
        )

        mock_desc.assert_called_once()

        # _register_agent
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=OefSearchMessage,
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            to=self.skill.skill_context.search_service_address,
            sender=str(self.skill.skill_context.skill_id),
            service_description=self.mocked_registration_description,
        )
        assert has_attributes, error_str

        mock_logger.assert_any_call(logging.INFO, "registering agent on SOEF.")

    def test_act_i(self):
        """Test the act method of the alice behaviour where failed_registration_msg is NOT None."""
        # setup
        self.alice_behaviour.failed_registration_msg = self.registration_message

        with patch.object(self.logger, "log") as mock_logger:
            self.alice_behaviour.act()

        # after
        self.assert_quantity_in_outbox(1)

        # _retry_failed_registration
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=type(self.registration_message),
            performative=self.registration_message.performative,
            to=self.registration_message.to,
            sender=str(self.skill.skill_context.skill_id),
            service_description=self.registration_message.service_description,
        )
        assert has_attributes, error_str

        mock_logger.assert_any_call(
            logging.INFO,
            f"Retrying registration on SOEF. Retry {self.alice_behaviour._nb_retries} out of {self.alice_behaviour._max_soef_registration_retries}.",
        )
        assert self.alice_behaviour.failed_registration_msg is None

    def test_act_ii(self):
        """Test the act method of the alice behaviour where failed_registration_msg is NOT None and max retries is reached."""
        # setup
        self.alice_behaviour.failed_registration_msg = self.registration_message
        self.alice_behaviour._max_soef_registration_retries = 2
        self.alice_behaviour._nb_retries = 2

        self.alice_behaviour.act()

        # after
        self.assert_quantity_in_outbox(0)
        assert self.skill.skill_context.is_active is False

    def test_register_service(self):
        """Test the register_service method of the alice behaviour."""
        # operation
        with patch.object(
            self.strategy,
            "get_register_service_description",
            return_value=self.mocked_registration_description,
        ):
            with patch.object(self.logger, "log") as mock_logger:
                self.alice_behaviour.register_service()

        # after
        self.assert_quantity_in_outbox(1)

        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=OefSearchMessage,
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            to=self.skill.skill_context.search_service_address,
            sender=str(self.skill.skill_context.skill_id),
            service_description=self.mocked_registration_description,
        )
        assert has_attributes, error_str
        mock_logger.assert_any_call(
            logging.INFO, "registering agent's service on the SOEF."
        )

    def test_register_genus(self):
        """Test the register_genus method of the alice behaviour."""
        # operation
        with patch.object(
            self.strategy,
            "get_register_personality_description",
            return_value=self.mocked_registration_description,
        ):
            with patch.object(self.logger, "log") as mock_logger:
                self.alice_behaviour.register_genus()

        # after
        self.assert_quantity_in_outbox(1)

        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=OefSearchMessage,
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            to=self.skill.skill_context.search_service_address,
            sender=str(self.skill.skill_context.skill_id),
            service_description=self.mocked_registration_description,
        )
        assert has_attributes, error_str
        mock_logger.assert_any_call(
            logging.INFO, "registering agent's personality genus on the SOEF."
        )

    def test_register_classification(self):
        """Test the register_classification method of the alice behaviour."""
        # operation
        with patch.object(
            self.strategy,
            "get_register_classification_description",
            return_value=self.mocked_registration_description,
        ):
            with patch.object(self.logger, "log") as mock_logger:
                self.alice_behaviour.register_classification()

        # after
        self.assert_quantity_in_outbox(1)

        message = self.get_message_from_outbox()
        has_attributes, error_str = self.message_has_attributes(
            actual_message=message,
            message_type=OefSearchMessage,
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            to=self.skill.skill_context.search_service_address,
            sender=str(self.skill.skill_context.skill_id),
            service_description=self.mocked_registration_description,
        )
        assert has_attributes, error_str
        mock_logger.assert_any_call(
            logging.INFO, "registering agent's personality classification on the SOEF."
        )

    def test_teardown(self):
        """Test the teardown method of the alice behaviour."""
        # operation
        with patch.object(
            self.strategy,
            "get_unregister_service_description",
            return_value=self.mocked_registration_description,
        ):
            with patch.object(
                self.strategy,
                "get_location_description",
                return_value=self.mocked_registration_description,
            ):
                with patch.object(self.logger, "log") as mock_logger:
                    self.alice_behaviour.teardown()

        # after
        self.assert_quantity_in_outbox(2)

        # _unregister_service
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=OefSearchMessage,
            performative=OefSearchMessage.Performative.UNREGISTER_SERVICE,
            to=self.skill.skill_context.search_service_address,
            sender=str(self.skill.skill_context.skill_id),
            service_description=self.mocked_registration_description,
        )
        assert has_attributes, error_str
        mock_logger.assert_any_call(logging.INFO, "unregistering service from SOEF.")

        # _unregister_agent
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=OefSearchMessage,
            performative=OefSearchMessage.Performative.UNREGISTER_SERVICE,
            to=self.skill.skill_context.search_service_address,
            sender=str(self.skill.skill_context.skill_id),
            service_description=self.mocked_registration_description,
        )
        assert has_attributes, error_str
        mock_logger.assert_any_call(logging.INFO, "unregistering agent from SOEF.")
