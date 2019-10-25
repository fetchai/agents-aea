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

"""This module contains the tests for the base classes for the skills."""
import os
from pathlib import Path
from queue import Queue

from aea.aea import AEA
from aea.connections.local.connection import LocalNode, OEFLocalConnection
from aea.crypto.wallet import Wallet
from aea.decision_maker.base import OwnershipState, Preferences
from aea.mail.base import MailBox
from aea.skills.base import SkillContext
from tests.conftest import CUR_PATH


class TestSkillContext:
    """Test the skill context."""

    @classmethod
    def setup_class(cls):
        """Test the initialisation of the AEA."""
        cls.node = LocalNode()
        private_key_pem_path = os.path.join(CUR_PATH, "data", "priv.pem")
        cls.wallet = Wallet({'default': private_key_pem_path}, {})
        cls.mailbox1 = MailBox(OEFLocalConnection(cls.wallet.public_keys['default'], cls.node))
        cls.my_aea = AEA("Agent0", cls.mailbox1, cls.wallet, directory=str(Path(CUR_PATH, "data/dummy_aea")))
        cls.skill_context = SkillContext(cls.my_aea.context)

    def test_agent_name(self):
        """Test the agent's name."""
        assert self.skill_context.agent_name == self.my_aea.name

    def test_agent_public_keys(self):
        """Test the agent's public keys."""
        assert self.skill_context.agent_public_keys == self.my_aea.wallet.public_keys

    def test_agent_addresses(self):
        """Test the agent's address."""
        assert self.skill_context.agent_addresses == self.my_aea.wallet.addresses

    def test_agent_address(self):
        """Test the default agent's address."""
        assert self.skill_context.agent_address == self.my_aea.wallet.addresses['default']

    def test_decision_maker_message_queue(self):
        """Test the decision maker's queue."""
        assert isinstance(self.skill_context.decision_maker_message_queue, Queue)

    def test_agent_ownership_state(self):
        """Test the ownership state."""
        assert isinstance(self.skill_context.agent_ownership_state, OwnershipState)

    def test_agent_preferences(self):
        """Test the agents_preferences."""
        assert isinstance(self.skill_context.agent_preferences, Preferences)

    def test_agent_is_ready_to_pursuit_goals(self):
        """Test if the agent is ready to pursuit his goals."""
        assert not self.skill_context.agent_is_ready_to_pursuit_goals

    @classmethod
    def teardown(cls):
        """Test teardown."""
        pass
