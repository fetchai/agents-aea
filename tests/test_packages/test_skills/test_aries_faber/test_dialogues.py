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
"""This module contains the tests of the dialogue classes of the aries_faber skill."""

from aea.test_tools.test_skill import COUNTERPARTY_AGENT_ADDRESS

from packages.fetchai.protocols.default.message import DefaultMessage
from packages.fetchai.protocols.http.message import HttpMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.aries_faber.dialogues import (
    DefaultDialogue,
    HttpDialogue,
    OefSearchDialogue,
)

from tests.test_packages.test_skills.test_aries_faber.intermediate_class import (
    AriesFaberTestCase,
)


class TestDialogues(AriesFaberTestCase):
    """Test dialogue classes of aries_faber."""

    def test_default_dialogues(self):
        """Test the DefaultDialogues class."""
        _, dialogue = self.default_dialogues.create(
            counterparty=COUNTERPARTY_AGENT_ADDRESS,
            performative=DefaultMessage.Performative.BYTES,
            content=self.body_bytes,
        )
        assert dialogue.role == DefaultDialogue.Role.AGENT
        assert dialogue.self_address == self.skill.skill_context.agent_address

    def test_http_dialogues(self):
        """Test the HttpDialogues class."""
        _, dialogue = self.http_dialogues.create(
            counterparty=COUNTERPARTY_AGENT_ADDRESS,
            performative=HttpMessage.Performative.REQUEST,
            method=self.mocked_method,
            url=self.mocked_url,
            version=self.mocked_version,
            headers=self.mocked_headers,
            body=self.mocked_body_bytes,
        )
        assert dialogue.role == HttpDialogue.Role.CLIENT
        assert dialogue.self_address == str(self.skill.skill_context.skill_id)

    def test_oef_search_dialogues(self):
        """Test the OefSearchDialogues class."""
        _, dialogue = self.oef_search_dialogues.create(
            counterparty=COUNTERPARTY_AGENT_ADDRESS,
            performative=OefSearchMessage.Performative.SEARCH_SERVICES,
            query=self.mocked_query,
        )
        assert dialogue.role == OefSearchDialogue.Role.AGENT
        assert dialogue.self_address == str(self.skill.skill_context.skill_id)
