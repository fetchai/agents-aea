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
"""This module contains the tests of the dialogue classes of the tac participation skill."""

from pathlib import Path
from typing import cast

from aea.test_tools.test_skill import BaseSkillTestCase, COUNTERPARTY_AGENT_ADDRESS

from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.protocols.state_update.message import StateUpdateMessage
from packages.fetchai.protocols.tac.message import TacMessage
from packages.fetchai.skills.tac_participation.dialogues import (
    OefSearchDialogue,
    OefSearchDialogues,
    StateUpdateDialogue,
    StateUpdateDialogues,
    TacDialogue,
    TacDialogues,
)

from tests.conftest import ROOT_DIR


class TestDialogues(BaseSkillTestCase):
    """Test dialogue classes of tac participation."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "tac_participation")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.oef_search_dialogues = cast(
            OefSearchDialogues, cls._skill.skill_context.oef_search_dialogues
        )
        cls.state_update_dialogues = cast(
            StateUpdateDialogues, cls._skill.skill_context.state_update_dialogues
        )
        cls.tac_dialogues = cast(TacDialogues, cls._skill.skill_context.tac_dialogues)

    def test_oef_search_dialogues(self):
        """Test the OefSearchDialogues class."""
        _, dialogue = self.oef_search_dialogues.create(
            counterparty=COUNTERPARTY_AGENT_ADDRESS,
            performative=OefSearchMessage.Performative.SEARCH_SERVICES,
            query="some_query",
        )
        assert dialogue.role == OefSearchDialogue.Role.AGENT
        assert dialogue.self_address == str(self.skill.skill_context.skill_id)

    def test_state_update_dialogues(self):
        """Test the StateUpdateDialogues class."""
        _, dialogue = self.state_update_dialogues.create(
            counterparty=COUNTERPARTY_AGENT_ADDRESS,
            performative=StateUpdateMessage.Performative.INITIALIZE,
            exchange_params_by_currency_id={"some_currency_id": 1.0},
            utility_params_by_good_id={"some_good_id": 2.0},
            amount_by_currency_id={"some_currency_id": 10},
            quantities_by_good_id={"some_good_id": 5},
        )
        assert dialogue.role == StateUpdateDialogue.Role.SKILL
        assert dialogue.self_address == str(self.skill.skill_context.skill_id)

    def test_tac_dialogues(self):
        """Test the TacDialogues class."""
        _, dialogue = self.tac_dialogues.create(
            counterparty=COUNTERPARTY_AGENT_ADDRESS,
            performative=TacMessage.Performative.REGISTER,
            agent_name="some_agent_name",
        )
        assert dialogue.role == TacDialogue.Role.PARTICIPANT
        assert dialogue.self_address == self.skill.skill_context.agent_address
