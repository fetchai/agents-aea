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
"""This module contains the tests of the dialogue classes of the tac control contract skill."""

from pathlib import Path
from typing import cast

import pytest

from aea.exceptions import AEAEnforceError
from aea.helpers.search.models import (
    Attribute,
    Constraint,
    ConstraintType,
    DataModel,
    Description,
    Query,
)
from aea.helpers.transaction.base import RawTransaction, Terms
from aea.protocols.dialogue.base import DialogueLabel
from aea.test_tools.test_skill import BaseSkillTestCase, COUNTERPARTY_AGENT_ADDRESS

from packages.fetchai.protocols.contract_api.custom_types import Kwargs
from packages.fetchai.protocols.contract_api.message import ContractApiMessage
from packages.fetchai.protocols.cosm_trade.message import CosmTradeMessage
from packages.fetchai.protocols.default.message import DefaultMessage
from packages.fetchai.protocols.fipa.message import FipaMessage
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.protocols.signing.message import SigningMessage
from packages.fetchai.skills.tac_negotiation.dialogues import (
    ContractApiDialogue,
    ContractApiDialogues,
    CosmTradeDialogue,
    CosmTradeDialogues,
    DefaultDialogue,
    DefaultDialogues,
    FipaDialogue,
    FipaDialogues,
    LedgerApiDialogue,
    LedgerApiDialogues,
    OefSearchDialogue,
    OefSearchDialogues,
    SigningDialogue,
    SigningDialogues,
)
from packages.fetchai.skills.tac_negotiation.helpers import SUPPLY_DATAMODEL_NAME

from tests.conftest import ROOT_DIR


class TestDialogues(BaseSkillTestCase):
    """Test dialogue classes of tac negotiation."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "tac_negotiation")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.fipa_dialogues = cast(
            FipaDialogues, cls._skill.skill_context.fipa_dialogues
        )
        cls.contract_api_dialogues = cast(
            ContractApiDialogues, cls._skill.skill_context.contract_api_dialogues
        )
        cls.cosm_trade_dialogues = cast(
            CosmTradeDialogues, cls._skill.skill_context.cosm_trade_dialogues
        )
        cls.default_dialogues = cast(
            DefaultDialogues, cls._skill.skill_context.default_dialogues
        )
        cls.signing_dialogues = cast(
            SigningDialogues, cls._skill.skill_context.signing_dialogues
        )
        cls.ledger_api_dialogues = cast(
            LedgerApiDialogues, cls._skill.skill_context.ledger_api_dialogues
        )
        cls.oef_search_dialogues = cast(
            OefSearchDialogues, cls._skill.skill_context.oef_search_dialogues
        )
        cls.query = Query(
            [Constraint("some_attribute", ConstraintType("==", "some_service"))],
            DataModel(
                SUPPLY_DATAMODEL_NAME,
                [
                    Attribute(
                        "some_attribute", str, False, "Some attribute descriptions."
                    )
                ],
            ),
        )

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

        # counterparty_signature
        with pytest.raises(ValueError, match="counterparty_signature not set!"):
            assert fipa_dialogue.counterparty_signature
        fipa_dialogue.counterparty_signature = "some_counterparty_signature"
        with pytest.raises(
            AEAEnforceError, match="counterparty_signature already set!"
        ):
            fipa_dialogue.counterparty_signature = "some_other_counterparty_signature"
        assert fipa_dialogue.counterparty_signature == "some_counterparty_signature"

        # proposal
        with pytest.raises(ValueError, match="Proposal not set!"):
            assert fipa_dialogue.proposal
        description = Description({"foo1": 1, "bar1": 2})
        fipa_dialogue.proposal = description
        with pytest.raises(AEAEnforceError, match="Proposal already set!"):
            fipa_dialogue.proposal = description
        assert fipa_dialogue.proposal == description

        # terms
        with pytest.raises(ValueError, match="Terms not set!"):
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

    def test_fipa_dialogues(self):
        """Test the FipaDialogues class."""
        _, dialogue = self.fipa_dialogues.create(
            counterparty=COUNTERPARTY_AGENT_ADDRESS,
            performative=FipaMessage.Performative.CFP,
            query=self.query,
        )
        assert dialogue.role == FipaDialogue.Role.BUYER
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

        # associated_fipa_dialogue
        with pytest.raises(ValueError, match="associated_fipa_dialogue not set!"):
            assert contract_api_dialogue.associated_fipa_dialogue

        fipa_dialogue = FipaDialogue(
            DialogueLabel(
                ("", ""),
                COUNTERPARTY_AGENT_ADDRESS,
                self.skill.skill_context.agent_address,
            ),
            self.skill.skill_context.agent_address,
            role=FipaDialogue.Role.BUYER,
        )
        contract_api_dialogue.associated_fipa_dialogue = fipa_dialogue
        with pytest.raises(
            AEAEnforceError, match="associated_fipa_dialogue already set!"
        ):
            contract_api_dialogue.associated_fipa_dialogue = fipa_dialogue
        assert contract_api_dialogue.associated_fipa_dialogue == fipa_dialogue

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

    def test_cosm_trade_dialogues(self):
        """Test the CosmTradeDialogues class."""
        _, dialogue = self.cosm_trade_dialogues.create(
            counterparty=COUNTERPARTY_AGENT_ADDRESS,
            performative=CosmTradeMessage.Performative.INFORM_PUBLIC_KEY,
            public_key="some_public_key",
        )
        assert dialogue.role == CosmTradeDialogue.Role.AGENT
        assert dialogue.self_address == self.skill.skill_context.agent_address

    def test_default_dialogues(self):
        """Test the DefaultDialogues class."""
        _, dialogue = self.default_dialogues.create(
            counterparty=COUNTERPARTY_AGENT_ADDRESS,
            performative=DefaultMessage.Performative.BYTES,
            content=b"some_content",
        )
        assert dialogue.role == DefaultDialogue.Role.AGENT
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
            ledger_id="some_ledger_id",
            address="some_address",
        )
        assert dialogue.role == LedgerApiDialogue.Role.AGENT
        assert dialogue.self_address == str(self.skill.skill_context.skill_id)

    def test_oef_search_dialogue(self):
        """Test the OefSearchDialogue class."""
        oef_search_dialogue = OefSearchDialogue(
            DialogueLabel(
                ("", ""),
                COUNTERPARTY_AGENT_ADDRESS,
                self.skill.skill_context.agent_address,
            ),
            self.skill.skill_context.agent_address,
            role=ContractApiDialogue.Role.AGENT,
        )

        # is_seller_search
        with pytest.raises(ValueError, match="is_seller_search not set!"):
            assert oef_search_dialogue.is_seller_search
        oef_search_dialogue.is_seller_search = True
        with pytest.raises(AEAEnforceError, match="is_seller_search already set!"):
            oef_search_dialogue.is_seller_search = False
        assert oef_search_dialogue.is_seller_search is True

    def test_oef_search_dialogues(self):
        """Test the OefSearchDialogues class."""
        _, dialogue = self.oef_search_dialogues.create(
            counterparty=COUNTERPARTY_AGENT_ADDRESS,
            performative=OefSearchMessage.Performative.SEARCH_SERVICES,
            query=self.query,
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

        # associated_fipa_dialogue
        with pytest.raises(ValueError, match="associated_fipa_dialogue not set!"):
            assert signing_dialogue.associated_fipa_dialogue
        fipa_dialogue = FipaDialogue(
            DialogueLabel(
                ("", ""),
                COUNTERPARTY_AGENT_ADDRESS,
                self.skill.skill_context.agent_address,
            ),
            self.skill.skill_context.agent_address,
            role=FipaDialogue.Role.BUYER,
        )
        signing_dialogue.associated_fipa_dialogue = fipa_dialogue
        with pytest.raises(
            AEAEnforceError, match="associated_fipa_dialogue already set!"
        ):
            signing_dialogue.associated_fipa_dialogue = fipa_dialogue
        assert signing_dialogue.associated_fipa_dialogue == fipa_dialogue

        # associated_cosm_trade_dialogue
        cosm_trade_dialogue = CosmTradeDialogue(
            DialogueLabel(
                ("", ""),
                COUNTERPARTY_AGENT_ADDRESS,
                self.skill.skill_context.agent_address,
            ),
            self.skill.skill_context.agent_address,
            role=CosmTradeDialogue.Role.AGENT,
        )
        signing_dialogue.associated_cosm_trade_dialogue = cosm_trade_dialogue
        with pytest.raises(
            AEAEnforceError, match="associated_cosm_trade_dialogue already set!"
        ):
            signing_dialogue.associated_cosm_trade_dialogue = cosm_trade_dialogue
        assert signing_dialogue.associated_cosm_trade_dialogue == cosm_trade_dialogue

    def test_signing_dialogues(self):
        """Test the SigningDialogues class."""
        _, dialogue = self.signing_dialogues.create(
            counterparty=COUNTERPARTY_AGENT_ADDRESS,
            performative=SigningMessage.Performative.SIGN_TRANSACTION,
            terms=Terms(
                "some_ledger_id",
                "some_sender_address",
                "some_counterparty_address",
                dict(),
                dict(),
                "some_nonce",
            ),
            raw_transaction=RawTransaction(
                "some_ledger_id", {"some_key": "some_value"}
            ),
        )
        assert dialogue.role == SigningDialogue.Role.SKILL
        assert dialogue.self_address == str(self.skill.skill_context.skill_id)
