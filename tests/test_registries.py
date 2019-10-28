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
import shutil
import tempfile
import unittest.mock
from pathlib import Path

import yaml

import aea
import aea.registries.base
from aea.aea import AEA
from aea.configurations.base import DEFAULT_AEA_CONFIG_FILE
from aea.crypto.wallet import Wallet
from aea.mail.base import MailBox
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
        cls.agent_name = "agent_dir_test"
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

        mailbox = MailBox(DummyConnection())
        private_key_pem_path = os.path.join(CUR_PATH, "data", "priv.pem")
        wallet = Wallet({'default': private_key_pem_path}, {})
        cls.aea = AEA("agent_name", mailbox, wallet, directory=cls.agent_folder)
        cls.resources = Resources.from_resource_dir(os.path.join(cls.agent_folder), cls.aea.context)

        cls.expected_skills = {"dummy", "error"}

    def test_unregister_handler(self):
        """Test that the unregister of handlers work correctly."""
        assert len(self.resources.handler_registry.fetch_all()) == 2
        error_handler = self.resources.handler_registry.fetch_by_skill("default", "error")
        self.resources.handler_registry.unregister("error")

        # unregister the handler and test that it has been actually unregistered.
        assert self.resources.handler_registry.fetch_by_skill("default", "error") is None
        handlers = self.resources.handler_registry.fetch_all()
        assert len(handlers) == 1
        assert handlers[0].__class__.__name__ == "DummyHandler"

        # restore the handler
        self.resources.handler_registry.register((None, "error"), [error_handler])
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
        dummy_behaviour = self.resources.behaviour_registry.fetch("dummy")
        self.resources.behaviour_registry.unregister("dummy")
        assert self.resources.behaviour_registry.fetch("dummy") is None

        self.resources.behaviour_registry.register((None, "dummy"), [dummy_behaviour])

    def test_task_registry(self):
        """Test that the task registry behaves as expected."""
        assert len(self.resources.task_registry.fetch_all()) == 1
        dummy_task = self.resources.task_registry.fetch("dummy")
        self.resources.task_registry.unregister("dummy")
        assert self.resources.task_registry.fetch("dummy") is None

        self.resources.task_registry.register((None, "dummy"), [dummy_task])

    @classmethod
    def teardown_class(cls):
        """Tear the tests down."""
        cls._unpatch_logger()
        shutil.rmtree(cls.t, ignore_errors=True)
        os.chdir(cls.oldcwd)
