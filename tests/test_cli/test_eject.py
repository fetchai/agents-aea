# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2020 Fetch.AI Limited
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
"""This test module contains the tests for commands in aea.cli.eject module."""

import os

from aea.test_tools.test_cases import AEATestCaseMany

from packages.fetchai.connections.gym.connection import (
    PUBLIC_ID as GYM_CONNECTION_PUBLIC_ID,
)
from packages.fetchai.contracts.erc1155.contract import PUBLIC_ID as ERC1155_PUBLIC_ID
from packages.fetchai.protocols.gym.message import GymMessage
from packages.fetchai.skills.gym import PUBLIC_ID as GYM_SKILL_PUBLIC_ID


class TestEjectCommands(AEATestCaseMany):
    """End-to-end test case for CLI eject commands."""

    def test_eject_commands_positive(self):
        """Test eject commands for positive result."""
        agent_name = "test_aea"
        self.create_agents(agent_name)

        self.set_agent_context(agent_name)
        cwd = os.path.join(self.t, agent_name)
        self.add_item("connection", str(GYM_CONNECTION_PUBLIC_ID))
        self.add_item("skill", str(GYM_SKILL_PUBLIC_ID))
        self.add_item("contract", str(ERC1155_PUBLIC_ID))

        self.eject_item("connection", str(GYM_CONNECTION_PUBLIC_ID))
        assert "gym" not in os.listdir(
            (os.path.join(cwd, "vendor", "fetchai", "connections"))
        )
        assert "gym" in os.listdir((os.path.join(cwd, "connections")))

        self.eject_item("protocol", str(GymMessage.protocol_id))
        assert "gym" not in os.listdir(
            (os.path.join(cwd, "vendor", "fetchai", "protocols"))
        )
        assert "gym" in os.listdir((os.path.join(cwd, "protocols")))

        self.eject_item("skill", str(GYM_SKILL_PUBLIC_ID))
        assert "gym" not in os.listdir(
            (os.path.join(cwd, "vendor", "fetchai", "skills"))
        )
        assert "gym" in os.listdir((os.path.join(cwd, "skills")))

        self.eject_item("contract", str(ERC1155_PUBLIC_ID))
        assert "erc1155" not in os.listdir(
            (os.path.join(cwd, "vendor", "fetchai", "contracts"))
        )
        assert "erc1155" in os.listdir((os.path.join(cwd, "contracts")))
