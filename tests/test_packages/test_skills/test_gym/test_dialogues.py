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
"""This module contains the tests of the dialogue classes of the ml_train skill."""

from aea.test_tools.test_skill import COUNTERPARTY_AGENT_ADDRESS

from packages.fetchai.protocols.default.message import DefaultMessage
from packages.fetchai.protocols.gym.message import GymMessage
from packages.fetchai.skills.gym.dialogues import DefaultDialogue, GymDialogue

from tests.test_packages.test_skills.test_gym.intermediate_class import GymTestCase


class TestDialogues(GymTestCase):
    """Test dialogue classes of gym."""

    def test_default_dialogues(self):
        """Test the DefaultDialogues class."""
        _, dialogue = self.default_dialogues.create(
            counterparty=COUNTERPARTY_AGENT_ADDRESS,
            performative=DefaultMessage.Performative.BYTES,
            content=self.content_bytes,
        )
        assert dialogue.role == DefaultDialogue.Role.AGENT
        assert dialogue.self_address == str(self.skill.skill_context.skill_id)

    def test_gym_dialogues(self):
        """Test the GymDialogues class."""
        _, dialogue = self.gym_dialogues.create(
            counterparty=COUNTERPARTY_AGENT_ADDRESS,
            performative=GymMessage.Performative.RESET,
        )
        assert dialogue.role == GymDialogue.Role.AGENT
        assert dialogue.self_address == str(self.skill.skill_context.skill_id)
