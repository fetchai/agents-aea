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

"""This module contains the tests for the base classes for the skills."""

import os
import shutil
import tempfile
from pathlib import Path
from queue import Queue
from unittest import TestCase, mock

import aea.registries.base
from aea.aea import AEA, Resources
from aea.connections.base import ConnectionStatus
from aea.crypto.ethereum import ETHEREUM
from aea.crypto.fetchai import FETCHAI
from aea.crypto.ledger_apis import LedgerApis
from aea.crypto.wallet import Wallet
from aea.decision_maker.base import GoalPursuitReadiness, OwnershipState, Preferences
from aea.identity.base import Identity
from aea.skills.base import Skill, SkillComponent, SkillContext

from ..conftest import CUR_PATH, DUMMY_CONNECTION_PUBLIC_ID, DummyConnection


def test_agent_context_ledger_apis():
    """Test that the ledger apis configurations are loaded correctly."""
    private_key_path = os.path.join(CUR_PATH, "data", "fet_private_key.txt")
    wallet = Wallet({FETCHAI: private_key_path})
    connections = [DummyConnection(connection_id=DUMMY_CONNECTION_PUBLIC_ID)]
    ledger_apis = LedgerApis({"fetchai": {"network": "testnet"}}, FETCHAI)
    identity = Identity("name", address=wallet.addresses[FETCHAI])
    my_aea = AEA(
        identity,
        connections,
        wallet,
        ledger_apis,
        resources=Resources(str(Path(CUR_PATH, "data", "dummy_aea"))),
        is_programmatic=False,
    )

    assert set(my_aea.context.ledger_apis.apis.keys()) == {"fetchai"}


class TestSkillContext:
    """Test the skill context."""

    @classmethod
    def setup_class(cls):
        """Test the initialisation of the AEA."""
        eth_private_key_path = os.path.join(CUR_PATH, "data", "eth_private_key.txt")
        fet_private_key_path = os.path.join(CUR_PATH, "data", "fet_private_key.txt")
        cls.wallet = Wallet(
            {ETHEREUM: eth_private_key_path, FETCHAI: fet_private_key_path}
        )
        cls.ledger_apis = LedgerApis({FETCHAI: {"network": "testnet"}}, FETCHAI)
        cls.connections = [DummyConnection(connection_id=DUMMY_CONNECTION_PUBLIC_ID)]
        cls.identity = Identity(
            "name", addresses=cls.wallet.addresses, default_address_key=FETCHAI
        )
        cls.my_aea = AEA(
            cls.identity,
            cls.connections,
            cls.wallet,
            cls.ledger_apis,
            resources=Resources(str(Path(CUR_PATH, "data", "dummy_aea"))),
            is_programmatic=False,
        )
        cls.skill_context = SkillContext(cls.my_aea.context)

    def test_agent_name(self):
        """Test the agent's name."""
        assert self.skill_context.agent_name == self.my_aea.name

    def test_agent_addresses(self):
        """Test the agent's address."""
        assert self.skill_context.agent_addresses == self.my_aea.identity.addresses

    def test_agent_address(self):
        """Test the default agent's address."""
        assert self.skill_context.agent_address == self.my_aea.identity.address

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
        assert isinstance(
            self.skill_context.agent_goal_pursuit_readiness, GoalPursuitReadiness
        )

    def test_message_in_queue(self):
        """Test the 'message_in_queue' property."""
        assert isinstance(self.skill_context.message_in_queue, Queue)

    def test_ledger_apis(self):
        """Test the 'ledger_apis' property."""
        assert isinstance(self.skill_context.ledger_apis, LedgerApis)
        assert set(self.skill_context.ledger_apis.apis.keys()) == {"fetchai"}

    @classmethod
    def teardown(cls):
        """Test teardown."""
        pass


class TestSkillFromDir:
    """Test the 'Skill.from_dir' method."""

    @classmethod
    def _patch_logger(cls):
        cls.patch_logger_warning = mock.patch.object(aea.skills.base.logger, "warning")
        cls.mocked_logger_warning = cls.patch_logger_warning.__enter__()

    @classmethod
    def _unpatch_logger(cls):
        cls.mocked_logger_warning.__exit__()

    @classmethod
    def setup_class(cls):
        """Set the tests up."""
        cls._patch_logger()

        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        cls.skill_directory = Path(cls.t, "dummy_skill")
        shutil.copytree(Path(CUR_PATH, "data", "dummy_skill"), cls.skill_directory)
        os.chdir(cls.t)

        private_key_path = os.path.join(CUR_PATH, "data", "fet_private_key.txt")
        cls.wallet = Wallet({FETCHAI: private_key_path})
        ledger_apis = LedgerApis({}, FETCHAI)
        cls.connections = [DummyConnection(connection_id=DUMMY_CONNECTION_PUBLIC_ID)]
        cls.identity = Identity("name", address=cls.wallet.addresses[FETCHAI])
        cls.my_aea = AEA(
            cls.identity,
            cls.connections,
            cls.wallet,
            ledger_apis,
            resources=Resources(str(Path(CUR_PATH, "data", "dummy_aea"))),
            is_programmatic=False,
        )
        cls.agent_context = cls.my_aea.context

    def test_missing_handler(self):
        """Test that when parsing a skill and an handler is missing, we behave correctly."""
        Path(self.skill_directory, "handlers.py").write_text("")
        Skill.from_dir(self.skill_directory, self.agent_context)
        self.mocked_logger_warning.assert_called_with(
            "Handler 'DummyInternalHandler' cannot be found."
        )

    def test_missing_behaviour(self):
        """Test that when parsing a skill and a behaviour is missing, we behave correctly."""
        Path(self.skill_directory, "behaviours.py").write_text("")
        Skill.from_dir(self.skill_directory, self.agent_context)
        self.mocked_logger_warning.assert_called_with(
            "Behaviour 'DummyBehaviour' cannot be found."
        )

    def test_missing_model(self):
        """Test that when parsing a skill and a model is missing, we behave correctly."""
        Path(self.skill_directory, "dummy.py").write_text("")
        Skill.from_dir(self.skill_directory, self.agent_context)
        self.mocked_logger_warning.assert_called_with(
            "Model 'DummyModel' cannot be found."
        )

    @classmethod
    def teardown_class(cls):
        """Tear the tests down."""
        cls._unpatch_logger()
        shutil.rmtree(cls.t)
        os.chdir(cls.cwd)


class SkillContextTestCase(TestCase):
    """Test case for SkillContext class."""

    def test_shared_state_positive(self):
        """Test shared_state property positive result"""
        agent_context = mock.Mock()
        agent_context.shared_state = "shared_state"
        obj = SkillContext(agent_context)
        obj.shared_state

    def test_skill_id_positive(self):
        """Test skill_id property positive result"""
        obj = SkillContext("agent_context")
        obj._skill = mock.Mock()
        obj._skill.config = mock.Mock()
        obj._skill.config.public_id = "public_id"
        obj.skill_id

    @mock.patch("aea.skills.base.logger.debug")
    @mock.patch("aea.skills.base.SkillContext.skill_id")
    def test_is_active_positive(self, skill_id_mock, debug_mock):
        """Test is_active setter positive result"""
        obj = SkillContext("agent_context")
        obj.is_active = "value"
        debug_mock.assert_called_once()

    def test_task_manager_positive(self):
        """Test task_manager property positive result"""
        agent_context = mock.Mock()
        agent_context.task_manager = "task_manager"
        obj = SkillContext(agent_context)
        with self.assertRaises(AssertionError):
            obj.task_manager
        obj._skill = mock.Mock()
        obj.task_manager

    @mock.patch("aea.skills.base.SimpleNamespace")
    def test_handlers_positive(self, *mocks):
        """Test handlers property positive result"""
        obj = SkillContext("agent_context")
        with self.assertRaises(AssertionError):
            obj.handlers
        obj._skill = mock.Mock()
        obj._skill.handlers = {}
        obj.handlers

    @mock.patch("aea.skills.base.SimpleNamespace")
    def test_behaviours_positive(self, *mocks):
        """Test behaviours property positive result"""
        obj = SkillContext("agent_context")
        with self.assertRaises(AssertionError):
            obj.behaviours
        obj._skill = mock.Mock()
        obj._skill.behaviours = {}
        obj.behaviours

    def test_logger_positive(self):
        """Test logger property positive result"""
        obj = SkillContext("agent_context")
        with self.assertRaises(AssertionError):
            obj.logger
        obj._logger = mock.Mock()
        obj.logger


class SkillComponentTestCase(TestCase):
    """Test case for SkillComponent class."""

    def setUp(self):
        """Set the test up."""

        class TestComponent(SkillComponent):
            """Test class for SkillComponent"""

            def parse_module(self, *args):
                """Parse module."""
                pass

            def setup(self, *args):
                """Set up."""
                pass

            def teardown(self, *args):
                """Tear down."""
                pass

        self.TestComponent = TestComponent

    def test_init_no_ctx(self):
        """Test init method no context provided."""

        with self.assertRaises(ValueError):
            self.TestComponent()
        with self.assertRaises(ValueError):
            self.TestComponent(skill_context="skill_context")

    def test_skill_id_positive(self):
        """Test skill_id property positive."""
        ctx = mock.Mock()
        ctx.skill_id = "skill_id"
        component = self.TestComponent(skill_context=ctx, name="name")
        component.skill_id

    def test_config_positive(self):
        """Test config property positive."""
        component = self.TestComponent(skill_context="ctx", name="name")
        component.config
