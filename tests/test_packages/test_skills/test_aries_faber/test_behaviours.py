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
"""This module contains the tests of the behaviour classes of the aries_faber skill."""

import json
import logging
from unittest.mock import patch

from packages.fetchai.protocols.http.message import HttpMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.aries_faber.behaviours import HTTP_CLIENT_PUBLIC_ID

from tests.test_packages.test_skills.test_aries_faber.intermediate_class import (
    AriesFaberTestCase,
)


class TestFaberBehaviour(AriesFaberTestCase):
    """Test registration behaviour of aries_faber."""

    def test_send_http_request_message(self):
        """Test the send_http_request_message method of the faber behaviour."""
        # operation
        self.faber_behaviour.send_http_request_message(
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
        """Test the setup method of the faber behaviour."""
        # operation
        self.faber_behaviour.setup()

        # after
        self.assert_quantity_in_outbox(0)
        assert self.strategy.is_searching is True

    def test_act_is_searching(self):
        """Test the act method of the faber behaviour where is_searching is True."""
        # setup
        self.strategy._is_searching = True

        # operation
        with patch.object(
            self.strategy,
            "get_location_and_service_query",
            return_value=self.mocked_query,
        ):
            with patch.object(self.logger, "log") as mock_logger:
                self.faber_behaviour.act()

        # after
        self.assert_quantity_in_outbox(1)
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=OefSearchMessage,
            performative=OefSearchMessage.Performative.SEARCH_SERVICES,
            to=self.skill.skill_context.search_service_address,
            sender=str(self.skill.public_id),
            query=self.mocked_query,
        )
        assert has_attributes, error_str

        mock_logger.assert_any_call(
            logging.INFO, "Searching for Alice on SOEF...",
        )

    def test_teardown(self):
        """Test the teardown method of the service_registration behaviour."""
        self.faber_behaviour.teardown()
        self.assert_quantity_in_outbox(0)
