# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2022 Fetch.AI Limited
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
"""This module contains the tests of the behaviour classes of the fetch block skill."""

from pathlib import Path
from typing import cast

from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.protocols.ledger_api.custom_types import Kwargs
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.skills.fetch_block.behaviours import FetchBlockBehaviour

from tests.conftest import ROOT_DIR


LEDGER_ID = "fetchai"


class TestSkillBehaviour(BaseSkillTestCase):
    """Test behaviours of fetch block."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "fetch_block")

    @classmethod
    def setup(cls, **kwargs):
        """Setup the test class."""
        super().setup()
        cls.fetch_block_behaviour = cast(
            FetchBlockBehaviour,
            cls._skill.skill_context.behaviours.fetch_block_behaviour,
        )

    def test__get_block(self):
        """Test that the _get_block function sends the right message to the ledger_api."""

        self.fetch_block_behaviour._get_block()
        self.assert_quantity_in_outbox(1)

        msg = cast(LedgerApiMessage, self.get_message_from_outbox())
        has_attributes, error_str = self.message_has_attributes(
            actual_message=msg,
            message_type=LedgerApiMessage,
            performative=LedgerApiMessage.Performative.GET_STATE,
            ledger_id=LEDGER_ID,
            callable="blocks",
            args=("latest",),
            kwargs=Kwargs({}),
        )
        assert has_attributes, error_str

    def test_setup(self):
        """Test that the setup method puts no messages in the outbox by default."""
        self.fetch_block_behaviour.setup()
        self.assert_quantity_in_outbox(0)

    def test_act(self):
        """Test that the act method of the fetch_block behaviour puts the correct message in the outbox."""
        self.fetch_block_behaviour.act()
        self.assert_quantity_in_outbox(1)
        msg = cast(LedgerApiMessage, self.get_message_from_outbox())
        has_attributes, error_str = self.message_has_attributes(
            actual_message=msg,
            message_type=LedgerApiMessage,
            performative=LedgerApiMessage.Performative.GET_STATE,
            ledger_id=LEDGER_ID,
            callable="blocks",
            args=("latest",),
            kwargs=Kwargs({}),
        )
        assert has_attributes, error_str

    def test_teardown(self):
        """Test that the teardown method of the fetch_block behaviour leaves no messages in the outbox."""
        assert self.fetch_block_behaviour.teardown() is None
        self.assert_quantity_in_outbox(0)
