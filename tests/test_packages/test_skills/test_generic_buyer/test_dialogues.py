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

import pytest

from aea.exceptions import AEAEnforceError
from aea.helpers.transaction.base import Terms
from aea.protocols.default.dialogues import DefaultDialogue as BaseDefaultDialogue
from aea.protocols.default.message import DefaultMessage
from aea.protocols.dialogue.base import DialogueLabel
from aea.test_tools.test_skill import BaseSkillTestCase, COUNTERPARTY_NAME

from packages.fetchai.skills.generic_buyer.dialogues import (
    DefaultDialogue,
    DefaultDialogues,
    FipaDialogue,
    LedgerApiDialogue,
)

from tests.conftest import ROOT_DIR


class TestDefaultDialogues(BaseSkillTestCase):
    """Test default dialogues of generic buyer."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "generic_buyer")

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
            counterparty=COUNTERPARTY_NAME,
            performative=DefaultMessage.Performative.BYTES,
            content=b"some_content",
        )
        assert dialogue.role == BaseDefaultDialogue.Role.AGENT

    def test_fipa_dialogue(self):
        """Test the DefaultDialogues class."""
        fipa_dialogue = FipaDialogue(
            DialogueLabel(
                ("", ""), COUNTERPARTY_NAME, self.skill.skill_context.agent_address,
            ),
            self.skill.skill_context.agent_address,
            role=DefaultDialogue.Role.AGENT,
        )

        # terms
        with pytest.raises(AEAEnforceError, match="Terms not set!"):
            assert fipa_dialogue.terms
        terms = Terms(
            "some_ledger_id",
            self.skill.skill_context.agent_address,
            "counterprty",
            {"currency_id": 50},
            {"good_id": -10},
            "some_nonce",
        )
        fipa_dialogue.terms = terms
        with pytest.raises(AEAEnforceError, match="Terms already set!"):
            fipa_dialogue.terms = terms
        assert fipa_dialogue.terms == terms

        # associated_ledger_api_dialogue
        with pytest.raises(AEAEnforceError, match="LedgerApiDialogue not set!"):
            assert fipa_dialogue.associated_ledger_api_dialogue
        ledger_api_dialogue = LedgerApiDialogue(
            DialogueLabel(
                ("", ""), COUNTERPARTY_NAME, self.skill.skill_context.agent_address,
            ),
            self.skill.skill_context.agent_address,
            role=LedgerApiDialogue.Role.AGENT,
        )
        fipa_dialogue.associated_ledger_api_dialogue = ledger_api_dialogue
        with pytest.raises(AEAEnforceError, match="LedgerApiDialogue already set!"):
            fipa_dialogue.associated_ledger_api_dialogue = ledger_api_dialogue
        assert fipa_dialogue.associated_ledger_api_dialogue == ledger_api_dialogue
