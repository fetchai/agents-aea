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
"""This module contains the tests of the dialogue classes of the echo skill."""

from pathlib import Path
from typing import cast

from aea.test_tools.test_skill import BaseSkillTestCase, COUNTERPARTY_AGENT_ADDRESS

from packages.fetchai.protocols.default.message import DefaultMessage
from packages.fetchai.skills.echo.dialogues import DefaultDialogue, DefaultDialogues

from tests.conftest import ROOT_DIR


class TestDialogues(BaseSkillTestCase):
    """Test dialogue class of echo."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "echo")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.default_dialogues = cast(
            DefaultDialogues, cls._skill.skill_context.default_dialogues
        )

    def test_default_dialogues(self):
        """Test the DefaultDialogues class."""
        _, dialogue = self.default_dialogues.create(
            counterparty=COUNTERPARTY_AGENT_ADDRESS,
            performative=DefaultMessage.Performative.BYTES,
            content=b"some_content",
        )
        assert dialogue.role == DefaultDialogue.Role.AGENT
        assert dialogue.self_address == self.skill.skill_context.agent_name
