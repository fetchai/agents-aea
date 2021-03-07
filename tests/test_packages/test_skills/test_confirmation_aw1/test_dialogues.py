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
from aea.protocols.dialogue.base import DialogueLabel
from aea.test_tools.test_skill import BaseSkillTestCase, COUNTERPARTY_AGENT_ADDRESS

from packages.fetchai.protocols.contract_api.custom_types import Kwargs
from packages.fetchai.protocols.contract_api.message import ContractApiMessage
from packages.fetchai.protocols.default.message import DefaultMessage
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.register.message import RegisterMessage
from packages.fetchai.protocols.signing.message import SigningMessage
from packages.fetchai.skills.confirmation_aw1.dialogues import (
    ContractApiDialogue,
    ContractApiDialogues,
    DefaultDialogue,
    DefaultDialogues,
    LedgerApiDialogue,
    LedgerApiDialogues,
    RegisterDialogue,
    RegisterDialogues,
    SigningDialogue,
    SigningDialogues,
)

from tests.conftest import ROOT_DIR


class TestDialogues(BaseSkillTestCase):
    """Test dialogue classes of confirmation aw1."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "confirmation_aw1")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.default_dialogues = cast(
            DefaultDialogues, cls._skill.skill_context.default_dialogues
        )
        cls.contract_api_dialogues = cast(
            ContractApiDialogues, cls._skill.skill_context.contract_api_dialogues
        )
        cls.register_dialogues = cast(
            RegisterDialogues, cls._skill.skill_context.register_dialogues
        )
        cls.ledger_api_dialogues = cast(
            LedgerApiDialogues, cls._skill.skill_context.ledger_api_dialogues
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

    def test_register_dialogue(self):
        """Test the RegisterDialogue class."""
        register_dialogue = RegisterDialogue(
            DialogueLabel(
                ("", ""),
                COUNTERPARTY_AGENT_ADDRESS,
                self.skill.skill_context.agent_address,
            ),
            self.skill.skill_context.agent_address,
            role=RegisterDialogue.Role.AGENT,
        )

        # terms
        with pytest.raises(AEAEnforceError, match="Terms not set!"):
            assert register_dialogue.terms
        terms = Terms(
            "some_ledger_id",
            self.skill.skill_context.agent_address,
            "counterprty",
            {"currency_id": 50},
            {"good_id": -10},
            "some_nonce",
        )
        register_dialogue.terms = terms
        with pytest.raises(AEAEnforceError, match="Terms already set!"):
            register_dialogue.terms = terms
        assert register_dialogue.terms == terms

    def test_register_dialogues(self):
        """Test the RegisterDialogues class."""
        _, dialogue = self.register_dialogues.create(
            counterparty=COUNTERPARTY_AGENT_ADDRESS,
            performative=RegisterMessage.Performative.REGISTER,
            info={"some_key": "some_value"},
        )
        assert dialogue.role == RegisterDialogue.Role.AGENT
        assert dialogue.self_address == self.skill.skill_context.agent_address

    def test_contract_api_dialogue(self):
        """Test the ContractApiDialogue class."""
        contract_api_dialogue = ContractApiDialogue(
            DialogueLabel(
                ("", ""),
                COUNTERPARTY_AGENT_ADDRESS,
                self.skill.skill_context.agent_address,
            ),
            self.skill.skill_context.agent_address,
            role=ContractApiDialogue.Role.AGENT,
        )

        # associated_register_dialogue
        with pytest.raises(ValueError, match="Associated register dialogue not set!"):
            assert contract_api_dialogue.associated_register_dialogue

        register_dialogue = RegisterDialogue(
            DialogueLabel(
                ("", ""),
                COUNTERPARTY_AGENT_ADDRESS,
                self.skill.skill_context.agent_address,
            ),
            self.skill.skill_context.agent_address,
            role=RegisterDialogue.Role.AGENT,
        )
        contract_api_dialogue.associated_register_dialogue = register_dialogue
        with pytest.raises(
            AEAEnforceError, match="Associated register dialogue already set!"
        ):
            contract_api_dialogue.associated_register_dialogue = register_dialogue
        assert contract_api_dialogue.associated_register_dialogue == register_dialogue

        # terms
        with pytest.raises(ValueError, match="Terms not set!"):
            assert contract_api_dialogue.terms
        terms = Terms(
            "some_ledger_id",
            self.skill.skill_context.agent_address,
            "counterprty",
            {"currency_id": 50},
            {"good_id": -10},
            "some_nonce",
        )
        contract_api_dialogue.terms = terms
        with pytest.raises(AEAEnforceError, match="Terms already set!"):
            contract_api_dialogue.terms = terms
        assert contract_api_dialogue.terms == terms

    def test_contract_api_dialogues(self):
        """Test the ContractApiDialogues class."""
        _, dialogue = self.contract_api_dialogues.create(
            counterparty=COUNTERPARTY_AGENT_ADDRESS,
            performative=ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION,
            ledger_id="some_ledger_id",
            contract_id="some_contract_id",
            callable="some_callable",
            kwargs=Kwargs({"some_key": "some_value"}),
        )
        assert dialogue.role == ContractApiDialogue.Role.AGENT
        assert dialogue.self_address == str(self.skill.skill_context.skill_id)

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

        # associated_register_dialogue
        with pytest.raises(AEAEnforceError, match="RegisterDialogue not set!"):
            assert ledger_api_dialogue.associated_register_dialogue
        register_dialogue = RegisterDialogue(
            DialogueLabel(
                ("", ""),
                COUNTERPARTY_AGENT_ADDRESS,
                self.skill.skill_context.agent_address,
            ),
            self.skill.skill_context.agent_address,
            role=RegisterDialogue.Role.AGENT,
        )
        ledger_api_dialogue.associated_register_dialogue = register_dialogue
        with pytest.raises(AEAEnforceError, match="RegisterDialogue already set!"):
            ledger_api_dialogue.associated_register_dialogue = register_dialogue
        assert ledger_api_dialogue.associated_register_dialogue == register_dialogue

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
        assert dialogue.self_address == str(self.skill.skill_context.skill_id)
