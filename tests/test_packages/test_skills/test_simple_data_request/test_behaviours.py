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
"""This module contains the tests of the behaviour classes of the simple_data_request skill."""

import json
from typing import cast

import pytest

from packages.fetchai.protocols.http.message import HttpMessage
from packages.fetchai.skills.simple_data_request.behaviours import (
    HTTP_CLIENT_PUBLIC_ID,
    HttpRequestBehaviour,
)

from tests.test_packages.test_skills.test_simple_data_request.intermediate_class import (
    SimpleDataRequestTestCase,
)


class TestHttpRequestBehaviour(SimpleDataRequestTestCase):
    """Test http_request behaviour of http_request."""

    is_agent_to_agent_messages = False

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.http_request_behaviour = cast(
            HttpRequestBehaviour, cls._skill.skill_context.behaviours.http_request
        )

    def test__init__i(self):
        """Test the __init__ method of the http_request behaviour."""
        assert self.http_request_behaviour.url == "some_url"
        assert self.http_request_behaviour.method == "some_method"
        assert self.http_request_behaviour.body == ""

    def test__init__ii(self):
        """Test the __init__ method of the http_request behaviour where ValueError is raise."""
        with pytest.raises(ValueError, match="Url, method and body must be provided."):
            self.http_request_behaviour.__init__(
                url=None, method="some_method", body="some_body"
            )

    def test_setup(self):
        """Test the setup method of the http_request behaviour."""
        assert self.http_request_behaviour.setup() is None
        self.assert_quantity_in_outbox(0)

    def test_act_i(self):
        """Test the act method of the http_request behaviour where lookup_termination_key IS None."""
        # setup
        self.http_request_behaviour.lookup_termination_key = None

        # operation
        self.http_request_behaviour.act()

        # after
        self.assert_quantity_in_outbox(1)
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=HttpMessage,
            performative=HttpMessage.Performative.REQUEST,
            to=str(HTTP_CLIENT_PUBLIC_ID),
            sender=str(self.skill.skill_context.skill_id),
            method=self.mocked_method,
            url=self.mocked_url,
            headers="",
            version="",
            body=json.dumps(self.http_request_behaviour.body).encode("utf-8"),
        )
        assert has_attributes, error_str

    def test_act_ii(self):
        """Test the act method of the http_request behaviour where lookup_termination_key is NOT None and lookup_termination_key is False."""
        # setup
        key = "some_key"
        self.http_request_behaviour.lookup_termination_key = key
        self.skill.skill_context.shared_state[key] = False

        # operation
        self.http_request_behaviour.act()

        # after
        self.assert_quantity_in_outbox(0)

    def test_act_iii(self):
        """Test the act method of the http_request behaviour where lookup_termination_key is NOT None and lookup_termination_key is True."""
        # setup
        key = "some_key"
        self.http_request_behaviour.lookup_termination_key = key
        self.skill.skill_context.shared_state[key] = True

        # operation
        self.http_request_behaviour.act()

        # after
        self.assert_quantity_in_outbox(1)
        has_attributes, error_str = self.message_has_attributes(
            actual_message=self.get_message_from_outbox(),
            message_type=HttpMessage,
            performative=HttpMessage.Performative.REQUEST,
            to=str(HTTP_CLIENT_PUBLIC_ID),
            sender=str(self.skill.skill_context.skill_id),
            method=self.mocked_method,
            url=self.mocked_url,
            headers="",
            version="",
            body=json.dumps(self.http_request_behaviour.body).encode("utf-8"),
        )
        assert has_attributes, error_str

    def test_teardown(self):
        """Test the teardown method of the http_request behaviour."""
        assert self.http_request_behaviour.teardown() is None
        self.assert_quantity_in_outbox(0)
