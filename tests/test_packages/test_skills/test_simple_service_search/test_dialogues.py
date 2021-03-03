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
"""This module contains the tests of the dialogue classes of the simple_service_search skill."""

from pathlib import Path
from typing import cast

from aea.helpers.search.models import Description
from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.simple_service_search.dialogues import (
    OefSearchDialogue,
    OefSearchDialogues,
)

from tests.conftest import ROOT_DIR


class TestDialogues(BaseSkillTestCase):
    """Test dialogue class of simple_service_search."""

    path_to_skill = Path(
        ROOT_DIR, "packages", "fetchai", "skills", "simple_service_search"
    )

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.oef_search_dialogues = cast(
            OefSearchDialogues, cls._skill.skill_context.oef_search_dialogues
        )
        cls.mocked_description = Description({"foo1": 1, "bar1": 2})

    def test_oef_search_dialogues(self):
        """Test the OefSearchDialogues class."""
        _, dialogue = self.oef_search_dialogues.create(
            counterparty=self.skill.skill_context.search_service_address,
            performative=OefSearchMessage.Performative.REGISTER_SERVICE,
            service_description=self.mocked_description,
        )
        assert dialogue.role == OefSearchDialogue.Role.AGENT
        assert dialogue.self_address == str(self.skill.skill_context.skill_id)
