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
"""This module contains the tests of the dialogue classes of the generic buyer skill."""

from pathlib import Path
from typing import cast

from aea.test_tools.test_skill import COUNTERPARTY_AGENT_ADDRESS

from packages.fetchai.protocols.http.message import HttpMessage
from packages.fetchai.skills.confirmation_aw3.dialogues import (
    HttpDialogue,
    HttpDialogues,
)

from tests.conftest import ROOT_DIR
from tests.test_packages.test_skills.test_confirmation_aw3.intermediate_class import (
    ConfirmationAW3TestCase,
)


class TestDialogues(ConfirmationAW3TestCase):
    """Test dialogue classes of confirmation aw3."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "confirmation_aw3")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()

        cls.http_dialogues = cast(
            HttpDialogues, cls._skill.skill_context.http_dialogues
        )

    def test_http_dialogues(self):
        """Test the HttpDialogues class."""
        _, dialogue = self.http_dialogues.create(
            counterparty=COUNTERPARTY_AGENT_ADDRESS,
            performative=HttpMessage.Performative.REQUEST,
            method="some_method",
            url="some_url",
            version="some_version",
            headers="some_headers",
            body=b"some_body",
        )
        assert dialogue.role == HttpDialogue.Role.CLIENT
        assert dialogue.self_address == str(self.skill.skill_context.skill_id)
