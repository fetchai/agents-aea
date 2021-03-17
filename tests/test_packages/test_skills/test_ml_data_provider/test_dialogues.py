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
"""This module contains the tests of the dialogue classes of the ml_data_provider skill."""

import sys
from pathlib import Path
from typing import cast

import pytest

from aea.test_tools.test_skill import BaseSkillTestCase, COUNTERPARTY_AGENT_ADDRESS

from packages.fetchai.protocols.default.message import DefaultMessage
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.ml_trade.message import MlTradeMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.ml_data_provider.dialogues import (
    DefaultDialogue,
    DefaultDialogues,
    LedgerApiDialogue,
    LedgerApiDialogues,
    MlTradeDialogue,
    MlTradeDialogues,
    OefSearchDialogue,
    OefSearchDialogues,
)

from tests.conftest import ROOT_DIR


@pytest.mark.skipif(
    sys.version_info >= (3, 9),
    reason="These tests use tensorflow which, at the time of writing, does not yet support python version 3.9.",
)
class TestDialogues(BaseSkillTestCase):
    """Test dialogue classes of ml_data_provider."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "ml_data_provider")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.default_dialogues = cast(
            DefaultDialogues, cls._skill.skill_context.default_dialogues
        )
        cls.ml_dialogues = cast(
            MlTradeDialogues, cls._skill.skill_context.ml_trade_dialogues
        )
        cls.ledger_api_dialogues = cast(
            LedgerApiDialogues, cls._skill.skill_context.ledger_api_dialogues
        )
        cls.oef_search_dialogues = cast(
            OefSearchDialogues, cls._skill.skill_context.oef_search_dialogues
        )

    def test_default_dialogues(self):
        """Test the DefaultDialogues class."""
        _, dialogue = self.default_dialogues.create(
            counterparty=COUNTERPARTY_AGENT_ADDRESS,
            performative=DefaultMessage.Performative.BYTES,
            content=b"some_content",
        )
        assert dialogue.role == DefaultDialogue.Role.AGENT
        assert dialogue.self_address == self.skill.skill_context.agent_address

    def test_ml_dialogues(self):
        """Test the MlTradeDialogues class."""
        _, dialogue = self.ml_dialogues.create(
            counterparty=COUNTERPARTY_AGENT_ADDRESS,
            performative=MlTradeMessage.Performative.CFP,
            query="some_query",
        )
        assert dialogue.role == MlTradeDialogue.Role.SELLER
        assert dialogue.self_address == self.skill.skill_context.agent_address

    def test_ledger_api_dialogues(self):
        """Test the LedgerApiDialogues class."""
        _, dialogue = self.ledger_api_dialogues.create(
            counterparty=COUNTERPARTY_AGENT_ADDRESS,
            performative=LedgerApiMessage.Performative.GET_BALANCE,
            ledger_id="some_ledger_id",
            address="some_address",
        )
        assert dialogue.role == LedgerApiDialogue.Role.AGENT
        assert dialogue.self_address == str(self.skill.skill_context.skill_id)

    def test_oef_search_dialogues(self):
        """Test the OefSearchDialogues class."""
        _, dialogue = self.oef_search_dialogues.create(
            counterparty=COUNTERPARTY_AGENT_ADDRESS,
            performative=OefSearchMessage.Performative.SEARCH_SERVICES,
            query="some_query",
        )
        assert dialogue.role == OefSearchDialogue.Role.AGENT
        assert dialogue.self_address == str(self.skill.skill_context.skill_id)
