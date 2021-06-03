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
"""This module contains the tests of the dialogue classes of the erc1155_deploy skill."""

import pytest

from aea.exceptions import AEAEnforceError
from aea.protocols.dialogue.base import DialogueLabel
from aea.test_tools.test_skill import COUNTERPARTY_AGENT_ADDRESS

from packages.fetchai.protocols.contract_api.message import ContractApiMessage
from packages.fetchai.protocols.default.message import DefaultMessage
from packages.fetchai.protocols.fipa.message import FipaMessage
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.protocols.signing.message import SigningMessage
from packages.fetchai.skills.erc1155_deploy.dialogues import (
    ContractApiDialogue,
    DefaultDialogue,
    FipaDialogue,
    LedgerApiDialogue,
    OefSearchDialogue,
    SigningDialogue,
)

from tests.test_packages.test_skills.test_erc1155_deploy.intermediate_class import (
    ERC1155DeployTestCase,
)


class TestDialogues(ERC1155DeployTestCase):
    """Test dialogue classes of erc1155_deploy."""

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

        # terms
        with pytest.raises(ValueError, match="Terms not set!"):
            assert contract_api_dialogue.terms
        contract_api_dialogue.terms = self.mocked_terms
        with pytest.raises(AEAEnforceError, match="Terms already set!"):
            contract_api_dialogue.terms = self.mocked_terms
        assert contract_api_dialogue.terms == self.mocked_terms

    def test_contract_api_dialogues(self):
        """Test the ContractApiDialogues class."""
        _, dialogue = self.contract_api_dialogues.create(
            counterparty=COUNTERPARTY_AGENT_ADDRESS,
            performative=ContractApiMessage.Performative.GET_DEPLOY_TRANSACTION,
            ledger_id=self.ledger_id,
            contract_id=self.contract_id,
            callable=self.callable,
            kwargs=self.kwargs,
        )
        assert dialogue.role == ContractApiDialogue.Role.AGENT
        assert dialogue.self_address == str(self.skill.skill_context.skill_id)

    def test_default_dialogues(self):
        """Test the DefaultDialogues class."""
        _, dialogue = self.default_dialogues.create(
            counterparty=COUNTERPARTY_AGENT_ADDRESS,
            performative=DefaultMessage.Performative.BYTES,
            content=b"some_content",
        )
        assert dialogue.role == DefaultDialogue.Role.AGENT
        assert dialogue.self_address == self.skill.skill_context.agent_address

    def test_fipa_dialogue(self):
        """Test the FipaDialogue class."""
        fipa_dialogue = FipaDialogue(
            DialogueLabel(
                ("", ""),
                COUNTERPARTY_AGENT_ADDRESS,
                self.skill.skill_context.agent_address,
            ),
            self.skill.skill_context.agent_address,
            role=FipaDialogue.Role.BUYER,
        )

        # proposal
        with pytest.raises(ValueError, match="Proposal not set!"):
            assert fipa_dialogue.proposal
        fipa_dialogue.proposal = self.mocked_registration_description
        with pytest.raises(AEAEnforceError, match="Proposal already set!"):
            fipa_dialogue.proposal = self.mocked_registration_description
        assert fipa_dialogue.proposal == self.mocked_registration_description

    def test_fipa_dialogues(self):
        """Test the FipaDialogues class."""
        _, dialogue = self.fipa_dialogues.create(
            counterparty=COUNTERPARTY_AGENT_ADDRESS,
            performative=FipaMessage.Performative.CFP,
            query=self.mocked_query,
        )
        assert dialogue.role == FipaDialogue.Role.SELLER
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
            role=ContractApiDialogue.Role.AGENT,
        )

        # associated_signing_dialogue
        with pytest.raises(ValueError, match="Associated signing dialogue not set!"):
            assert ledger_api_dialogue.associated_signing_dialogue
        signing_dialogue = SigningDialogue(
            DialogueLabel(
                ("", ""),
                COUNTERPARTY_AGENT_ADDRESS,
                self.skill.skill_context.agent_address,
            ),
            self.skill.skill_context.agent_address,
            role=SigningDialogue.Role.SKILL,
        )
        ledger_api_dialogue.associated_signing_dialogue = signing_dialogue
        with pytest.raises(
            AEAEnforceError, match="Associated signing dialogue already set!"
        ):
            ledger_api_dialogue.associated_signing_dialogue = signing_dialogue
        assert ledger_api_dialogue.associated_signing_dialogue == signing_dialogue

    def test_ledger_api_dialogues(self):
        """Test the LedgerApiDialogues class."""
        _, dialogue = self.ledger_api_dialogues.create(
            counterparty=COUNTERPARTY_AGENT_ADDRESS,
            performative=LedgerApiMessage.Performative.GET_BALANCE,
            ledger_id=self.ledger_id,
            address=self.address,
        )
        assert dialogue.role == LedgerApiDialogue.Role.AGENT
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

    def test_signing_dialogue(self):
        """Test the SigningDialogue class."""
        signing_dialogue = SigningDialogue(
            DialogueLabel(
                ("", ""),
                COUNTERPARTY_AGENT_ADDRESS,
                self.skill.skill_context.agent_address,
            ),
            self.skill.skill_context.agent_address,
            role=ContractApiDialogue.Role.AGENT,
        )

        # associated_contract_api_dialogue
        with pytest.raises(
            ValueError, match="Associated contract api dialogue not set!"
        ):
            assert signing_dialogue.associated_contract_api_dialogue
        contract_api_dialogue = ContractApiDialogue(
            DialogueLabel(
                ("", ""),
                COUNTERPARTY_AGENT_ADDRESS,
                self.skill.skill_context.agent_address,
            ),
            self.skill.skill_context.agent_address,
            role=ContractApiDialogue.Role.AGENT,
        )
        signing_dialogue.associated_contract_api_dialogue = contract_api_dialogue
        with pytest.raises(
            AEAEnforceError, match="Associated contract api dialogue already set!"
        ):
            signing_dialogue.associated_contract_api_dialogue = contract_api_dialogue
        assert (
            signing_dialogue.associated_contract_api_dialogue == contract_api_dialogue
        )

    def test_signing_dialogues(self):
        """Test the SigningDialogues class."""
        _, dialogue = self.signing_dialogues.create(
            counterparty=COUNTERPARTY_AGENT_ADDRESS,
            performative=SigningMessage.Performative.SIGN_TRANSACTION,
            terms=self.mocked_terms,
            raw_transaction=self.mocked_raw_tx,
        )
        assert dialogue.role == SigningDialogue.Role.SKILL
        assert dialogue.self_address == str(self.skill.skill_context.skill_id)
