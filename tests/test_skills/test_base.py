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
import shutil
import tempfile
import unittest.mock
from pathlib import Path
from queue import Queue


import aea.registries.base
from aea.aea import AEA, Resources
from aea.connections.base import ConnectionStatus
from aea.crypto.wallet import Wallet
from aea.crypto.ledger_apis import LedgerApis
from aea.decision_maker.base import OwnershipState, Preferences
from aea.mail.base import MailBox
from aea.skills.base import SkillContext, Skill
from tests.conftest import CUR_PATH, DummyConnection


def test_agent_context_ledger_apis():
    """Test that the ledger apis configurations are loaded correctly."""
    private_key_pem_path = os.path.join(CUR_PATH, "data", "priv.pem")
    wallet = Wallet({'default': private_key_pem_path})
    mailbox1 = MailBox([DummyConnection()])
    ledger_apis = LedgerApis({"fetchai": ('alpha.fetch-ai.com', 80)})
    my_aea = AEA("Agent0", mailbox1, wallet, ledger_apis, resources=Resources(str(Path(CUR_PATH, "data", "dummy_aea"))))

    assert set(my_aea.context.ledger_apis.apis.keys()) == {"fetchai"}
    fetchai_ledger_api_obj = my_aea.context.ledger_apis.apis["fetchai"]
    assert fetchai_ledger_api_obj.tokens.host == 'alpha.fetch-ai.com'
    assert fetchai_ledger_api_obj.tokens.port == 80


class TestSkillContext:
    """Test the skill context."""

    @classmethod
    def setup_class(cls):
        """Test the initialisation of the AEA."""
        private_key_pem_path = os.path.join(CUR_PATH, "data", "priv.pem")
        cls.wallet = Wallet({'default': private_key_pem_path})
        cls.ledger_apis = LedgerApis({"fetchai": ("alpha.fetch-ai.com", 80)})
        cls.mailbox1 = MailBox([DummyConnection()])
        cls.my_aea = AEA("Agent0", cls.mailbox1, cls.wallet, cls.ledger_apis, resources=Resources(str(Path(CUR_PATH, "data", "dummy_aea"))))
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

    def test_connection_status(self):
        """Test the default agent's connection status."""
        assert isinstance(self.skill_context.connection_status, ConnectionStatus)

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

    def test_message_in_queue(self):
        """Test the 'message_in_queue' property."""
        assert isinstance(self.skill_context.message_in_queue, Queue)

    def test_ledger_apis(self):
        """Test the 'ledger_apis' property."""
        assert isinstance(self.skill_context.ledger_apis, LedgerApis)
        assert set(self.skill_context.ledger_apis.apis.keys()) == {'fetchai'}
        assert self.skill_context.ledger_apis.apis.get("fetchai").tokens.host == "alpha.fetch-ai.com"
        assert self.skill_context.ledger_apis.apis.get("fetchai").tokens.port == 80

    @classmethod
    def teardown(cls):
        """Test teardown."""
        pass


class TestSkillFromDir:
    """Test the 'Skill.from_dir' method."""

    @classmethod
    def _patch_logger(cls):
        cls.patch_logger_warning = unittest.mock.patch.object(aea.skills.base.logger, 'warning')
        cls.mocked_logger_warning = cls.patch_logger_warning.__enter__()

    @classmethod
    def _unpatch_logger(cls):
        cls.mocked_logger_warning.__exit__()

    @classmethod
    def setup_class(cls):
        """Set the tests up."""
        cls._patch_logger()

        cls.cwd = os.getcwd()
        cls.t = tempfile.mktemp()
        shutil.copytree(Path(CUR_PATH, "data", "dummy_skill"), cls.t)
        os.chdir(cls.t)

        private_key_pem_path = os.path.join(CUR_PATH, "data", "priv.pem")
        cls.wallet = Wallet({'default': private_key_pem_path})
        ledger_apis = LedgerApis({})
        cls.mailbox1 = MailBox([DummyConnection()])
        cls.my_aea = AEA("agent_name", cls.mailbox1, cls.wallet, ledger_apis, resources=Resources(str(Path(CUR_PATH, "data", "dummy_aea"))))
        cls.agent_context = cls.my_aea.context

    def test_missing_handler(self):
        """Test that when parsing a skill and an handler is missing, we behave correctly."""
        Path(self.t, "handlers.py").write_text("")
        Skill.from_dir(self.t, self.agent_context)
        self.mocked_logger_warning.assert_called_with("Handler 'DummyHandler' cannot be found.")

    def test_missing_behaviour(self):
        """Test that when parsing a skill and a behaviour is missing, we behave correctly."""
        Path(self.t, "behaviours.py").write_text("")
        Skill.from_dir(self.t, self.agent_context)
        self.mocked_logger_warning.assert_called_with("Behaviour 'DummyBehaviour' cannot be found.")

    def test_missing_task(self):
        """Test that when parsing a skill and a task is missing, we behave correctly."""
        Path(self.t, "tasks.py").write_text("")
        Skill.from_dir(self.t, self.agent_context)
        self.mocked_logger_warning.assert_called_with("Task 'DummyTask' cannot be found.")

    def test_missing_shared_class(self):
        """Test that when parsing a skill and a shared_class is missing, we behave correctly."""
        Path(self.t, "dummy.py").write_text("")
        Skill.from_dir(self.t, self.agent_context)
        self.mocked_logger_warning.assert_called_with("Shared class 'DummySharedClass' cannot be found.")

    @classmethod
    def teardown_class(cls):
        """Tear the tests down."""
        cls._unpatch_logger()
        shutil.rmtree(cls.t)
        os.chdir(cls.cwd)
