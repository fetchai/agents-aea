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
"""This module contains the tests of the dialogue classes of the registration_aw1 skill."""

from pathlib import Path

from aea.helpers.transaction.base import RawTransaction, Terms
from aea.test_tools.test_skill import COUNTERPARTY_AGENT_ADDRESS

from packages.fetchai.protocols.register.message import RegisterMessage
from packages.fetchai.protocols.signing.message import SigningMessage
from packages.fetchai.skills.registration_aw1.dialogues import (
    RegisterDialogue,
    SigningDialogue,
)

from tests.conftest import ROOT_DIR
from tests.test_packages.test_skills.test_registration_aw1.intermediate_class import (
    RegiatrationAW1TestCase,
)


class TestDialogues(RegiatrationAW1TestCase):
    """Test dialogue classes of registration_aw1."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "registration_aw1")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()

    def test_register_dialogues(self):
        """Test the FipaDialogues class."""
        _, dialogue = self.register_dialogues.create(
            counterparty=COUNTERPARTY_AGENT_ADDRESS,
            performative=RegisterMessage.Performative.REGISTER,
            info={"some_key": "some_value"},
        )
        assert dialogue.role == RegisterDialogue.Role.AGENT
        assert dialogue.self_address == self.skill.skill_context.agent_address

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
