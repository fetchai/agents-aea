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
"""This module contains the tests of the behaviour classes of the fetch beacon skill."""

from pathlib import Path
from typing import cast

from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.protocols.http.message import HttpMessage
from packages.fetchai.skills.fetch_beacon.behaviours import FetchBeaconBehaviour

from tests.conftest import ROOT_DIR


class TestSkillBehaviour(BaseSkillTestCase):
    """Test behaviours of fetch beacon."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "fetch_beacon")

    @classmethod
    def setup(cls, **kwargs):
        """Setup the test class."""
        super().setup()
        cls.fetch_beacon_behaviour = cast(
            FetchBeaconBehaviour,
            cls._skill.skill_context.behaviours.fetch_beacon_behaviour,
        )

    def test_send_http_request_message(self):
        """Test the send_http_request_message method of the fetch_beacon behaviour."""
        self.fetch_beacon_behaviour.send_http_request_message("GET", "some_url")
        self.assert_quantity_in_outbox(1)
        msg = cast(HttpMessage, self.get_message_from_outbox())
        has_attributes, error_str = self.message_has_attributes(
            actual_message=msg,
            message_type=HttpMessage,
            performative=HttpMessage.Performative.REQUEST,
            method="GET",
            url="some_url",
        )
        assert has_attributes, error_str

    def test_setup(self):
        """Test that the setup method puts no messages in the outbox by default."""
        self.fetch_beacon_behaviour.setup()
        self.assert_quantity_in_outbox(0)

    def test_act(self):
        """Test that the act method of the fetch_beacon behaviour puts the correct message in the outbox."""
        self.fetch_beacon_behaviour.act()
        self.assert_quantity_in_outbox(1)
        msg = cast(HttpMessage, self.get_message_from_outbox())
        has_attributes, error_str = self.message_has_attributes(
            actual_message=msg,
            message_type=HttpMessage,
            performative=HttpMessage.Performative.REQUEST,
            method="GET",
            url=self.fetch_beacon_behaviour.beacon_url,
        )
        assert has_attributes, error_str

    def test_teardown(self):
        """Test that the teardown method of the fetch_beacon behaviour leaves no messages in the outbox."""
        assert self.fetch_beacon_behaviour.teardown() is None
        self.assert_quantity_in_outbox(0)
