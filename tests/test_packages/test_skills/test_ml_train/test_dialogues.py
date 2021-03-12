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

from pathlib import Path
from typing import cast

import pytest

from aea.exceptions import AEAEnforceError
from aea.helpers.transaction.base import Terms
from aea.protocols.dialogue.base import DialogueLabel
from aea.test_tools.test_skill import BaseSkillTestCase, COUNTERPARTY_AGENT_ADDRESS

from packages.fetchai.protocols.default.message import DefaultMessage
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.ml_trade.message import MlTradeMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.protocols.signing.message import SigningMessage
from packages.fetchai.skills.ml_train.dialogues import (
    DefaultDialogue,
    DefaultDialogues,
    LedgerApiDialogue,
    LedgerApiDialogues,
    MlTradeDialogue,
    MlTradeDialogues,
    OefSearchDialogue,
    OefSearchDialogues,
    SigningDialogue,
    SigningDialogues,
)

from tests.conftest import ROOT_DIR


class TestDialogues(BaseSkillTestCase):
    """Test dialogue classes of ml_train."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "ml_train")

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
        cls.signing_dialogues = cast(
            SigningDialogues, cls._skill.skill_context.signing_dialogues
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

    def test_ml_dialogue(self):
        """Test the MlTradeDialogue class."""
        ml_dialogue = MlTradeDialogue(
            DialogueLabel(
                ("", ""),
                COUNTERPARTY_AGENT_ADDRESS,
                self.skill.skill_context.agent_address,
            ),
            self.skill.skill_context.agent_address,
            role=MlTradeDialogue.Role.BUYER,
        )

        # terms
        with pytest.raises(AEAEnforceError, match="Terms not set!"):
            assert ml_dialogue.terms
        terms = Terms(
            "some_ledger_id",
            self.skill.skill_context.agent_address,
            "counterprty",
            {"currency_id": 50},
            {"good_id": -10},
            "some_nonce",
        )
        ml_dialogue.terms = terms
        with pytest.raises(AEAEnforceError, match="Terms already set!"):
            ml_dialogue.terms = terms
        assert ml_dialogue.terms == terms

    def test_ml_dialogues(self):
        """Test the MlTradeDialogues class."""
        _, dialogue = self.ml_dialogues.create(
            counterparty=COUNTERPARTY_AGENT_ADDRESS,
            performative=MlTradeMessage.Performative.CFP,
            query="some_query",
        )
        assert dialogue.role == MlTradeDialogue.Role.BUYER
        assert dialogue.self_address == self.skill.skill_context.agent_address

    def test_ledger_api_dialogue(self):
        """Test the LedgerApiDialogue class."""
        ledger_api_dialogue = LedgerApiDialogue(
            DialogueLabel(
                ("", ""),
                COUNTERPARTY_AGENT_ADDRESS,
                self.skill.skill_context.agent_address,
            ),
            self.skill.skill_context.agent_address,
            role=LedgerApiDialogue.Role.AGENT,
        )

        # associated_ml_trade_dialogue
        with pytest.raises(AEAEnforceError, match="MlTradeDialogue not set!"):
            assert ledger_api_dialogue.associated_ml_trade_dialogue
        ml_dialogue = MlTradeDialogue(
            DialogueLabel(
                ("", ""),
                COUNTERPARTY_AGENT_ADDRESS,
                self.skill.skill_context.agent_address,
            ),
            self.skill.skill_context.agent_address,
            role=MlTradeDialogue.Role.BUYER,
        )
        ledger_api_dialogue.associated_ml_trade_dialogue = ml_dialogue
        with pytest.raises(AEAEnforceError, match="MlTradeDialogue already set!"):
            ledger_api_dialogue.associated_ml_trade_dialogue = ml_dialogue
        assert ledger_api_dialogue.associated_ml_trade_dialogue == ml_dialogue

    def test_ledger_api_dialogues(self):
        """Test the LedgerApiDialogues class."""
        _, dialogue = self.ledger_api_dialogues.create(
            counterparty=COUNTERPARTY_AGENT_ADDRESS,
            performative=LedgerApiMessage.Performative.GET_BALANCE,
            ledger_id="some_ledger_id",
            address="some_address",
        )
        assert dialogue.role == LedgerApiDialogue.Role.AGENT
        assert dialogue.self_address == str(self.skill.public_id)

    def test_oef_search_dialogues(self):
        """Test the OefSearchDialogues class."""
        _, dialogue = self.oef_search_dialogues.create(
            counterparty=COUNTERPARTY_AGENT_ADDRESS,
            performative=OefSearchMessage.Performative.SEARCH_SERVICES,
            query="some_query",
        )
        assert dialogue.role == OefSearchDialogue.Role.AGENT
        assert dialogue.self_address == str(self.skill.public_id)

    def test_signing_dialogue(self):
        """Test the SigningDialogue class."""
        signing_dialogue = SigningDialogue(
            DialogueLabel(
                ("", ""),
                COUNTERPARTY_AGENT_ADDRESS,
                self.skill.skill_context.agent_address,
            ),
            self.skill.skill_context.agent_address,
            role=SigningDialogue.Role.SKILL,
        )

        # associated_ledger_api_dialogue
        with pytest.raises(AEAEnforceError, match="LedgerApiDialogue not set!"):
            assert signing_dialogue.associated_ledger_api_dialogue
        ledger_api_dialogue = LedgerApiDialogue(
            DialogueLabel(
                ("", ""),
                COUNTERPARTY_AGENT_ADDRESS,
                self.skill.skill_context.agent_address,
            ),
            self.skill.skill_context.agent_address,
            role=LedgerApiDialogue.Role.AGENT,
        )
        signing_dialogue.associated_ledger_api_dialogue = ledger_api_dialogue
        with pytest.raises(AEAEnforceError, match="LedgerApiDialogue already set!"):
            signing_dialogue.associated_ledger_api_dialogue = ledger_api_dialogue
        assert signing_dialogue.associated_ledger_api_dialogue == ledger_api_dialogue

    def test_signing_dialogues(self):
        """Test the SigningDialogues class."""
        _, dialogue = self.signing_dialogues.create(
            counterparty=COUNTERPARTY_AGENT_ADDRESS,
            performative=SigningMessage.Performative.SIGN_TRANSACTION,
            terms="some_terms",
            raw_transaction="some_raw_transaction",
        )
        assert dialogue.role == SigningDialogue.Role.SKILL
        assert dialogue.self_address == str(self.skill.public_id)
