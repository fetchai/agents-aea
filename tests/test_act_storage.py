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
"""This module contains tests behaviour storage access."""
import os

import pytest

from aea.aea_builder import AEABuilder
from aea.configurations.base import SkillConfig
from aea.configurations.constants import DEFAULT_LEDGER
from aea.skills.base import Skill, SkillContext
from aea.skills.behaviours import TickerBehaviour
from tests.common.utils import wait_for_condition


class TestBehaviour(TickerBehaviour):
    """Simple behaviour to count how many acts were called."""

    OBJ_ID = "some"
    OBJ_BODY = {"data": 12}
    COL_NAME = "test"

    def setup(self) -> None:
        """Set up behaviour."""
        self.counter = 0

    def act(self) -> None:
        """Make an action."""
        if self.context.storage and self.context.storage.is_connected:
            col = self.context.storage.get_sync_collection(self.COL_NAME)
            col.put(self.OBJ_ID, self.OBJ_BODY)
        self.counter += 1


def test_storage_access_from_behaviour():
    """Test storage access from components."""
    builder = AEABuilder()
    builder.set_name("aea_1")
    builder.add_private_key(DEFAULT_LEDGER)

    skill_context = SkillContext()
    behaviour = TestBehaviour(name="behaviour", skill_context=skill_context)
    test_skill = Skill(
        SkillConfig(name="test_skill", author="fetchai"),
        skill_context=skill_context,
        handlers={},
        behaviours={"behaviour": behaviour},
    )

    builder.add_component_instance(test_skill)
    aea = builder.build()
    skill_context.set_agent_context(aea.context)

    aea.runtime._threaded = True
    aea.runtime.start()

    try:
        wait_for_condition(lambda: aea.is_running, timeout=10)
        wait_for_condition(lambda: behaviour.counter > 0, timeout=10)

        col = skill_context.storage.get_sync_collection(behaviour.COL_NAME)
        assert col.get(behaviour.OBJ_ID) == behaviour.OBJ_BODY
    finally:
        aea.runtime.stop()
        aea.runtime.wait_completed(sync=True, timeout=10)


if __name__ == "__main__":
    pytest.main([os.path.basename(__file__)])
