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
"""This module contains the tests for aea/registries/base.py."""
import os
import random
import shutil
import tempfile
import unittest.mock
from pathlib import Path

import yaml

import aea
import aea.registries.base
from aea.aea import AEA
from aea.configurations.base import DEFAULT_AEA_CONFIG_FILE
from aea.crypto.ledger_apis import LedgerApis
from aea.crypto.wallet import Wallet
from aea.decision_maker.messages.transaction import TransactionMessage
from aea.protocols.base import Protocol
from aea.registries.base import ProtocolRegistry, Resources
from .conftest import CUR_PATH, DummyConnection


class TestProtocolRegistry:
    """Test the protocol registry."""

    @classmethod
    def setup_class(cls):
        """Set the tests up."""
        cls.patch = unittest.mock.patch.object(aea.registries.base.logger, 'exception')
        cls.mocked_logger = cls.patch.__enter__()

        cls.oldcwd = os.getcwd()
        cls.agent_name = "agent_dir_test"
        cls.t = tempfile.mkdtemp()
        cls.agent_folder = os.path.join(cls.t, cls.agent_name)
        shutil.copytree(os.path.join(CUR_PATH, "data", "dummy_aea"), cls.agent_folder)
        os.chdir(cls.agent_folder)

        # make fake protocol
        cls.fake_protocol_id = "fake"
        agent_config_path = Path(cls.agent_folder, DEFAULT_AEA_CONFIG_FILE)
        agent_config = yaml.safe_load(agent_config_path.read_text())
        agent_config.get("protocols").append(cls.fake_protocol_id)
        yaml.safe_dump(agent_config, open(agent_config_path, "w"))
        Path(cls.agent_folder, "protocols", cls.fake_protocol_id).mkdir()

        cls.registry = ProtocolRegistry()
        cls.registry.populate(cls.agent_folder)
        cls.expected_protocol_ids = {"default", "fipa"}

    def test_not_able_to_add_bad_formatted_protocol_message(self):
        """Test that the protocol registry has not been able to add the protocol 'bad'."""
        self.mocked_logger.assert_called_with("Not able to add protocol {}.".format(self.fake_protocol_id))

    def test_fetch_all(self):
        """Test that the 'fetch_all' method works as expected."""
        protocols = self.registry.fetch_all()
        assert all(isinstance(p, Protocol) for p in protocols)
        assert set(p.id for p in protocols) == self.expected_protocol_ids

    def test_unregister(self):
        """Test that the 'unregister' method works as expected."""
        protocol_id_removed = "default"
        protocol_removed = self.registry.fetch(protocol_id_removed)
        self.registry.unregister(protocol_id_removed)
        expected_protocols_ids = set(self.expected_protocol_ids)
        expected_protocols_ids.remove(protocol_id_removed)

        assert set(p.id for p in self.registry.fetch_all()) == expected_protocols_ids

        # restore the protocol
        self.registry.register((protocol_id_removed, None), protocol_removed)

    @classmethod
    def teardown_class(cls):
        """Tear down the tests."""
        cls.mocked_logger.__exit__()
        shutil.rmtree(cls.t, ignore_errors=True)
        os.chdir(cls.oldcwd)


class TestResources:
    """Test the resources class."""

    @classmethod
    def _patch_logger(cls):
        cls.patch_logger_exception = unittest.mock.patch.object(aea.registries.base.logger, 'exception')
        cls.mocked_logger_exception = cls.patch_logger_exception.__enter__()
        cls.patch_logger_warning = unittest.mock.patch.object(aea.registries.base.logger, 'warning')
        cls.mocked_logger_warning = cls.patch_logger_warning.__enter__()

    @classmethod
    def _unpatch_logger(cls):
        cls.mocked_logger_exception.__exit__()
        cls.mocked_logger_warning.__exit__()

    @classmethod
    def setup_class(cls):
        """Set the tests up."""
        cls._patch_logger()

        # create temp agent folder
        cls.oldcwd = os.getcwd()
        cls.agent_name = "agent_test" + str(random.randint(0, 1000))
        cls.t = tempfile.mkdtemp()
        cls.agent_folder = os.path.join(cls.t, cls.agent_name)
        shutil.copytree(os.path.join(CUR_PATH, "data", "dummy_aea"), cls.agent_folder)
        os.chdir(cls.agent_folder)

        # make fake skill
        cls.fake_skill_id = "fake"
        agent_config_path = Path(cls.agent_folder, DEFAULT_AEA_CONFIG_FILE)
        agent_config = yaml.safe_load(agent_config_path.read_text())
        agent_config.get("skills").append(cls.fake_skill_id)
        yaml.safe_dump(agent_config, open(agent_config_path, "w"))
        Path(cls.agent_folder, "skills", cls.fake_skill_id).mkdir()

        connections = [DummyConnection()]
        private_key_pem_path = os.path.join(CUR_PATH, "data", "priv.pem")
        wallet = Wallet({'default': private_key_pem_path})
        ledger_apis = LedgerApis({})
        cls.resources = Resources(os.path.join(cls.agent_folder))
        cls.aea = AEA(cls.agent_name, connections, wallet, ledger_apis, resources=cls.resources)
        cls.resources.load(cls.aea.context)

        cls.expected_skills = {"dummy", "error"}

    def test_unregister_handler(self):
        """Test that the unregister of handlers work correctly."""
        assert len(self.resources.handler_registry.fetch_all()) == 3
        error_handler = self.resources.handler_registry.fetch_by_skill("default", "error")
        self.resources.handler_registry.unregister("error")

        # unregister the handler and test that it has been actually unregistered.
        assert self.resources.handler_registry.fetch_by_skill("default", "error") is None
        handlers = self.resources.handler_registry.fetch_all()
        assert len(handlers) == 2
        assert handlers[0].__class__.__name__ == "DummyHandler"

        dummy_handler = self.resources.handler_registry.fetch_by_skill("default", "dummy")
        self.resources.handler_registry.unregister("dummy")
        assert len(self.resources.handler_registry.fetch_all()) == 0

        # restore the handlers
        self.resources.handler_registry.register((None, "error"), [error_handler])
        self.resources.handler_registry.register((None, "dummy"), [dummy_handler])
        assert len(self.resources.handler_registry.fetch_all()) == 2

    def test_fake_skill_loading_failed(self):
        """Test that when the skill is bad formatted, we print a log message."""
        s = "A problem occurred while parsing the skill directory {}. Exception: {}".format(
            os.path.join(self.agent_folder, "skills", "fake"),
            "[Errno 2] No such file or directory: '" + os.path.join(self.agent_folder, "skills", "fake", "skill.yaml") + "'")
        self.mocked_logger_warning.assert_called_once_with(s)

    def test_remove_skill(self):
        """Test that the 'remove skill' method works correctly."""
        error_skill = self.resources.get_skill("error")
        self.resources.remove_skill("error")
        assert self.resources.get_skill("error") is None
        self.resources.add_skill(error_skill)
        assert self.resources.get_skill("error") == error_skill

    def test_register_behaviour_with_already_existing_skill_id(self):
        """Test that registering a behaviour with an already existing skill id behaves as expected."""
        self.resources.behaviour_registry.register((None, "error"), [])
        self.mocked_logger_warning.assert_called_with("Behaviours already registered with skill id 'error'")

    def test_behaviour_registry(self):
        """Test that the behaviour registry behaves as expected."""
        assert len(self.resources.behaviour_registry.fetch_all()) == 1
        dummy_behaviours = self.resources.behaviour_registry.fetch("dummy")
        self.resources.behaviour_registry.unregister("dummy")
        assert self.resources.behaviour_registry.fetch("dummy") is None

        self.resources.behaviour_registry.register((None, "dummy"), dummy_behaviours)

    def test_register_task_with_already_existing_skill_id(self):
        """Test that registering a task with an already existing skill id behaves as expected."""
        self.resources.task_registry.register((None, "error"), [])
        self.mocked_logger_warning.assert_called_with("Tasks already registered with skill id 'error'")

    def test_task_registry(self):
        """Test that the task registry behaves as expected."""
        assert len(self.resources.task_registry.fetch_all()) == 1
        dummy_tasks = self.resources.task_registry.fetch("dummy")
        self.resources.task_registry.unregister("dummy")
        assert self.resources.task_registry.fetch("dummy") is None

        self.resources.task_registry.register((None, "dummy"), dummy_tasks)

    def test_skill_loading(self):
        """Test that the skills have been loaded correctly."""
        dummy_skill = self.resources.get_skill("dummy")
        error_skill_context = dummy_skill.skill_context

        handlers = dummy_skill.handlers
        behaviours = dummy_skill.behaviours
        tasks = dummy_skill.tasks
        shared_classes = dummy_skill.shared_classes

        assert handlers == error_skill_context.handlers
        assert behaviours == error_skill_context.behaviours
        assert tasks == error_skill_context.tasks
        assert getattr(error_skill_context, "agent_name") == self.agent_name

        assert handlers[0].context == dummy_skill.skill_context
        assert behaviours[0].context == dummy_skill.skill_context
        assert tasks[0].context == dummy_skill.skill_context
        assert shared_classes[0].context == dummy_skill.skill_context

    def test_handler_configuration_loading(self):
        """Test that the handler configurations are loaded correctly."""
        default_handlers = self.resources.handler_registry.fetch("default")
        assert len(default_handlers) == 2
        handler1, handler2 = default_handlers[0], default_handlers[1]
        dummy_handler = handler1 if handler1.__class__.__name__ == "DummyHandler" else handler2

        assert dummy_handler.config == {
            "handler_arg_1": 1,
            "handler_arg_2": "2"
        }

    def test_behaviour_configuration_loading(self):
        """Test that the behaviour configurations are loaded correctly."""
        dummy_behaviours = self.resources.behaviour_registry.fetch("dummy")
        assert len(dummy_behaviours) == 1
        dummy_behaviour = dummy_behaviours[0]

        assert dummy_behaviour.config == {
            "behaviour_arg_1": 1,
            "behaviour_arg_2": "2"
        }

    def test_task_configuration_loading(self):
        """Test that the task configurations are loaded correctly."""
        dummy_tasks = self.resources.task_registry.fetch("dummy")
        assert len(dummy_tasks) == 1
        dummy_task = dummy_tasks[0]

        assert dummy_task.config == {
            "task_arg_1": 1,
            "task_arg_2": "2"
        }

    def test_shared_class_configuration_loading(self):
        """Test that the shared class configurations are loaded correctly."""
        dummy_skill = self.resources.get_skill("dummy")
        assert len(dummy_skill.shared_classes) == 1
        dummy_shared_class = dummy_skill.shared_classes[0]

        assert dummy_shared_class.config == {
            "shared_class_arg_1": 1,
            "shared_class_arg_2": "2"
        }

    @classmethod
    def teardown_class(cls):
        """Tear the tests down."""
        cls._unpatch_logger()
        shutil.rmtree(cls.t, ignore_errors=True)
        os.chdir(cls.oldcwd)


class TestFilter:
    """Test the resources class."""

    @classmethod
    def setup_class(cls):
        """Set the tests up."""
        # create temp agent folder
        cls.oldcwd = os.getcwd()
        cls.agent_name = "agent_test" + str(random.randint(0, 1000))
        cls.t = tempfile.mkdtemp()
        cls.agent_folder = os.path.join(cls.t, cls.agent_name)
        shutil.copytree(os.path.join(CUR_PATH, "data", "dummy_aea"), cls.agent_folder)
        os.chdir(cls.agent_folder)

        connections = [DummyConnection()]
        private_key_pem_path = os.path.join(CUR_PATH, "data", "priv.pem")
        wallet = Wallet({'default': private_key_pem_path})
        ledger_apis = LedgerApis({})
        cls.aea = AEA(cls.agent_name, connections, wallet, ledger_apis, resources=Resources(cls.agent_folder))

    def test_handle_internal_messages(self):
        """Test that the internal messages are handled."""
        self.aea.setup()
        t = TransactionMessage(performative=TransactionMessage.Performative.ACCEPT,
                               transaction_id="transaction0",
                               skill_ids=["internal", "dummy"],
                               sender="pk1",
                               counterparty="pk2",
                               is_sender_buyer=True,
                               currency_pbk="Unknown",
                               amount=2,
                               sender_tx_fee=0,
                               counterparty_tx_fee=0,
                               ledger_id="fetchai",
                               quantities_by_good_pbk={"Unknown": 10},
                               info={},
                               transaction_digest="this-is-a-digest")
        self.aea.decision_maker.message_out_queue.put(t)
        self.aea.filter.handle_internal_messages()

        internal_handler = self.aea.resources.handler_registry.fetch_by_skill("internal", "dummy")
        assert len(internal_handler.handled_internal_messages) == 1
        self.aea.teardown()

    @classmethod
    def teardown_class(cls):
        """Tear the tests down."""
        shutil.rmtree(cls.t, ignore_errors=True)
        os.chdir(cls.oldcwd)
