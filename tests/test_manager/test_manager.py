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
"""This module contains tests for aea manager."""
import asyncio
import os
import re
import sys
from contextlib import suppress
from pathlib import Path
from shutil import rmtree
from tempfile import TemporaryDirectory
from typing import Optional
from unittest.case import TestCase
from unittest.mock import Mock, patch

import pytest

from aea.configurations.base import PublicId
from aea.crypto.helpers import create_private_key
from aea.crypto.plugin import load_all_plugins
from aea.crypto.registries import crypto_registry
from aea.helpers.install_dependency import run_install_subprocess
from aea.manager import MultiAgentManager

from packages.fetchai.connections.stub.connection import StubConnection
from packages.fetchai.skills.echo import PUBLIC_ID as ECHO_SKILL_PUBLIC_ID

from tests.common.utils import wait_for_condition
from tests.conftest import MY_FIRST_AEA_PUBLIC_ID, PACKAGES_DIR, ROOT_DIR


@patch("aea.aea_builder.AEABuilder.install_pypi_dependencies")
class BaseTestMultiAgentManager(TestCase):
    """Base test class for multi-agent manager"""

    MODE = "async"
    PASSWORD: Optional[str] = None

    echo_skill_id = ECHO_SKILL_PUBLIC_ID

    def setUp(self):
        """Set test case."""
        self.agent_name = "test_what_ever12"
        self.working_dir = "MultiAgentManager_dir"
        self.project_public_id = MY_FIRST_AEA_PUBLIC_ID
        self.project_path = os.path.join(
            self.working_dir, self.project_public_id.author, self.project_public_id.name
        )
        assert not os.path.exists(self.working_dir)
        self.manager = MultiAgentManager(
            self.working_dir, mode=self.MODE, password=self.PASSWORD
        )

    def tearDown(self):
        """Tear down test case."""
        self.manager.stop_manager()
        if os.path.exists(self.working_dir):
            rmtree(self.working_dir)

    def test_plugin_dependencies(self, *args):
        """Test plugin installed and loaded as a depencndecy."""
        plugin_path = str(Path(ROOT_DIR) / "plugins" / "aea-ledger-fetchai")
        install_cmd = f"{sys.executable} -m pip install --no-deps {plugin_path}".split(
            " "
        )
        try:
            self.manager.start_manager()
            run_install_subprocess(
                f"{sys.executable} -m pip uninstall aea-ledger-fetchai -y".split(" ")
            )
            from aea.crypto.registries import ledger_apis_registry

            ledger_apis_registry.specs.pop("fetchai", None)
            load_all_plugins(is_raising_exception=False)
            assert "fetchai" not in ledger_apis_registry.specs

            self.manager.add_project(self.project_public_id, local=True)
            assert "fetchai" not in ledger_apis_registry.specs

            self.manager.remove_project(self.project_public_id)

            def install_deps(*_):
                assert run_install_subprocess(install_cmd) == 0, install_cmd

            with patch(
                "aea.aea_builder.AEABuilder.install_pypi_dependencies", install_deps
            ):
                self.manager.add_project(self.project_public_id, local=True)

            assert "fetchai" in ledger_apis_registry.specs
        finally:
            run_install_subprocess(
                f"{sys.executable} -m pip uninstall aea-ledger-fetchai -y".split(" ")
            )
            run_install_subprocess(install_cmd)

    def test_workdir_created_removed(self, *args):
        """Check work dit created removed on MultiAgentManager start and stop."""
        assert not os.path.exists(self.working_dir)
        self.manager.start_manager()
        assert os.path.exists(self.working_dir)
        self.manager.stop_manager()
        assert not os.path.exists(self.working_dir)
        assert not os.path.exists(self.working_dir)

    def test_projects_property(self, *args):
        """Test projects property."""
        self.assertEqual(self.manager.projects, self.manager._projects)

    def test_data_dir_presents(self, *args):
        """Check not fails on exists data dir."""
        try:
            os.makedirs(self.working_dir)
            os.makedirs(self.manager._data_dir)
            self.manager.start_manager()
            self.manager.stop_manager()
        finally:
            with suppress(Exception):
                rmtree(self.working_dir)

    def test_MultiAgentManager_is_running(self, *args):
        """Check MultiAgentManager is running property reflects state."""
        assert not self.manager.is_running
        self.manager.start_manager()
        assert self.manager.is_running
        self.manager.stop_manager()
        assert not self.manager.is_running

    def test_add_remove_project(self, *args):
        """Test add and remove project."""
        self.manager.start_manager()

        self.manager.add_project(self.project_public_id, local=True)

        assert self.project_public_id in self.manager.list_projects()
        assert os.path.exists(self.project_path)

        with pytest.raises(ValueError, match=r".*was already added.*"):
            self.manager.add_project(self.project_public_id, local=True)

        self.manager.remove_project(self.project_public_id)
        assert self.project_public_id not in self.manager.list_projects()

        with pytest.raises(ValueError, match=r"is not present"):
            self.manager.remove_project(self.project_public_id)

        self.manager.add_project(self.project_public_id, local=True)
        assert self.project_public_id in self.manager.list_projects()
        assert os.path.exists(self.project_path)

    def test_add_agent(self, *args):
        """Test add agent alias."""
        self.manager.start_manager()

        self.manager.add_project(self.project_public_id, local=True)

        new_tick_interval = 0.2111

        component_overrides = [
            {
                **self.echo_skill_id.json,
                "type": "skill",
                "behaviours": {"echo": {"args": {"tick_interval": new_tick_interval}}},
            }
        ]
        self.manager.add_agent(
            self.project_public_id,
            self.agent_name,
            component_overrides=component_overrides,
        )
        agent_alias = self.manager.get_agent_alias(self.agent_name)
        assert agent_alias.agent_name == self.agent_name
        assert (
            agent_alias.get_aea_instance()
            .resources.get_behaviour(self.echo_skill_id, "echo")
            .tick_interval
            == new_tick_interval
        )

        with pytest.raises(ValueError, match="already exists"):
            self.manager.add_agent(
                self.project_public_id, self.agent_name,
            )

    def test_set_overrides(self, *args):
        """Test agent set overrides."""
        self.test_add_agent()
        new_tick_interval = 1000.0
        component_overrides = [
            {
                **self.echo_skill_id.json,
                "type": "skill",
                "behaviours": {"echo": {"args": {"tick_interval": new_tick_interval}}},
            }
        ]
        self.manager.set_agent_overrides(
            self.agent_name,
            agent_overides=None,
            components_overrides=component_overrides,
        )
        agent_alias = self.manager.get_agent_alias(self.agent_name)
        assert agent_alias.agent_name == self.agent_name
        assert (
            agent_alias.get_aea_instance()
            .resources.get_behaviour(self.echo_skill_id, "echo")
            .tick_interval
            == new_tick_interval
        )

    def test_remove_agent(self, *args):
        """Test remove agent alias."""
        self.test_add_agent()
        assert self.agent_name in self.manager.list_agents()
        self.manager.remove_agent(self.agent_name)
        assert self.agent_name not in self.manager.list_agents()

        with pytest.raises(ValueError, match="does not exist!"):
            self.manager.remove_agent(self.agent_name)

    def test_remove_project_with_alias(self, *args):
        """Test remove project with alias presents."""
        self.test_add_agent()

        with pytest.raises(
            ValueError, match="Can not remove projects with aliases exists"
        ):
            self.manager.remove_project(self.project_public_id)

    def test_add_agent_for_non_exist_project(self, *args):
        """Test add agent when no project added."""
        with pytest.raises(ValueError, match=" project is not added"):
            self.manager.add_agent(PublicId("test", "test", "0.1.0"), "another_agent")

    def test_agent_actually_running(self, *args):
        """Test MultiAgentManager starts agent correctly and agent perform acts."""
        self.test_add_agent()

        self.manager.start_all_agents()
        agent = self.manager._agents_tasks[self.agent_name].agent
        behaviour = agent.resources.get_behaviour(self.echo_skill_id, "echo")
        assert behaviour

        with patch.object(behaviour, "act") as act_mock:
            wait_for_condition(lambda: act_mock.call_count > 0, timeout=10)

    def test_exception_handling(self, *args):
        """Test error callback works."""
        self.test_add_agent()
        self.manager.start_all_agents()
        agent = self.manager._agents_tasks[self.agent_name].agent
        behaviour = agent.resources.get_behaviour(self.echo_skill_id, "echo")
        assert behaviour

        callback_mock = Mock()

        self.manager.add_error_callback(callback_mock)

        with patch.object(behaviour, "act", side_effect=ValueError("expected")):
            self.manager.start_all_agents()
            wait_for_condition(lambda: callback_mock.call_count > 0, timeout=10)

    def test_default_exception_handling(self, *args):
        """Test that the default error callback works."""
        self.test_add_agent()
        self.manager.start_all_agents()
        agent = self.manager._agents_tasks[self.agent_name].agent
        behaviour = agent.resources.get_behaviour(self.echo_skill_id, "echo")
        assert behaviour

        with patch.object(
            self.manager,
            "_print_exception_occurred_but_no_error_callback",
            side_effect=self.manager._print_exception_occurred_but_no_error_callback,
        ) as callback_mock:
            with patch.object(behaviour, "act", side_effect=ValueError("expected")):
                wait_for_condition(lambda: callback_mock.call_count > 0, timeout=10)
                callback_mock.assert_called_once()

    def test_stop_from_exception_handling(self, *args):
        """Test stop MultiAgentManager from error callback."""
        self.test_add_agent()
        self.manager.start_all_agents()
        agent = self.manager._agents_tasks[self.agent_name].agent
        behaviour = agent.resources.get_behaviour(self.echo_skill_id, "echo")

        def handler(*args, **kwargs):
            self.manager.stop_manager()

        self.manager.add_error_callback(handler)

        assert behaviour

        with patch.object(behaviour, "act", side_effect=ValueError("expected")):
            self.manager.start_all_agents()
            wait_for_condition(lambda: not self.manager.is_running, timeout=10)

    def test_start_all(self, *args):
        """Test MultiAgentManager start all agents."""
        self.test_add_agent()
        assert self.agent_name in self.manager.list_agents()
        assert self.agent_name not in self.manager.list_agents(running_only=True)
        self.manager.start_all_agents()
        assert self.agent_name in self.manager.list_agents(running_only=True)

        self.manager.start_all_agents()

        with pytest.raises(ValueError, match="is already started!"):
            self.manager.start_agents(self.manager.list_agents())

        with pytest.raises(ValueError, match="is already started!"):
            self.manager.start_agent(self.agent_name)

        with pytest.raises(ValueError, match="is not registered!"):
            self.manager.start_agent("non_exists_agent")

    def test_stop_agent(self, *args):
        """Test stop agent."""
        self.test_start_all()
        wait_for_condition(
            lambda: self.manager.list_agents(running_only=True), timeout=10
        )
        self.manager.stop_all_agents()

        assert not self.manager.list_agents(running_only=True)

        with pytest.raises(ValueError, match=" is not running!"):
            self.manager.stop_agent(self.agent_name)

        with pytest.raises(ValueError, match=" is not running!"):
            self.manager.stop_agents([self.agent_name])

    def test_do_no_allow_override_some_fields(self, *args):
        """Do not allo to override some values in agent config."""
        self.manager.start_manager()

        self.manager.add_project(self.project_public_id, local=True)

        BAD_OVERRIDES = [
            "skills",
            "connections",
            "contracts",
            "protocols",
            "some_field?",
        ]

        for bad_override in BAD_OVERRIDES:
            with pytest.raises(
                ValueError, match=r"Attribute `.*` is not allowed to be updated!"
            ):
                self.manager.add_agent(
                    self.project_public_id,
                    self.agent_name,
                    agent_overrides={bad_override: "some value"},
                )

    @staticmethod
    def test_invalid_mode(*args):
        """Test MultiAgentManager fails on invalid mode."""
        with pytest.raises(ValueError, match="Invalid mode"):
            MultiAgentManager("test_dir", mode="invalid_mode")

    def test_double_start(self, *args):
        """Test double MultiAgentManager start."""
        self.manager.start_manager()
        assert self.manager.is_running
        self.manager.start_manager()
        assert self.manager.is_running

    def test_double_stop(self, *args):
        """Test double MultiAgentManager stop."""
        self.manager.start_manager()
        assert self.manager.is_running
        self.manager.stop_manager()
        assert not self.manager.is_running
        self.manager.stop_manager()
        assert not self.manager.is_running

    def test_run_loop_direct_call(self, *args):
        """Test do not allow to run MultiAgentManager_loop directly."""
        loop = asyncio.new_event_loop()
        with pytest.raises(
            ValueError, match="Do not use this method directly, use start_manager"
        ):
            loop.run_until_complete(self.manager._manager_loop())

    def test_remove_running_agent(self, *args):
        """Test fail on remove running agent."""
        self.test_start_all()
        with pytest.raises(ValueError, match="Agent is running. stop it first!"):
            self.manager.remove_agent(self.agent_name)

        self.manager.stop_all_agents()
        wait_for_condition(
            lambda: self.agent_name not in self.manager.list_agents(running_only=True),
            timeout=5,
        )
        self.manager.remove_agent(self.agent_name)
        assert self.agent_name not in self.manager.list_agents()

    def test_save_load_positive(self, *args):
        """Test save-load func of MultiAgentManager for positive result."""
        self.manager.start_manager()
        self.manager.add_project(self.project_public_id, local=True)

        self.manager.add_agent(self.project_public_id, self.agent_name)
        self.manager.stop_manager(save=True)
        assert os.path.exists(self.manager._save_path)

        self.manager.start_manager()
        assert self.project_public_id in self.manager._projects.keys()
        assert self.agent_name in self.manager._agents.keys()

    def test_list_agents_info_positive(self, *args):
        """Test list_agents_info method for positive result."""
        self.manager.start_manager()
        self.manager.add_project(self.project_public_id, local=True)

        self.manager.add_agent(self.project_public_id, self.agent_name)
        result = self.manager.list_agents_info()
        expected_result = [
            {
                "agent_name": self.agent_name,
                "public_id": str(self.project_public_id),
                "addresses": self.manager.get_agent_alias(
                    self.agent_name
                ).get_addresses(),
                "is_running": False,
            }
        ]
        assert result == expected_result

    def test_add_same_project_versions(self, *args):
        """Test add the same project twice."""
        self.manager.start_manager()

        self.manager.add_project(self.project_public_id, local=True)
        with pytest.raises(
            ValueError, match=r"The project \(fetchai/my_first_aea\) was already added!"
        ):
            self.manager.add_project(
                PublicId.from_str("fetchai/my_first_aea:0.15.0"), local=False
            )

    def test_get_overridables(self, *args):
        """Test get overridables."""
        self.manager.start_manager()
        self.manager.add_project(self.project_public_id, local=True)
        self.manager.add_agent(self.project_public_id, self.agent_name)

        (
            agent_overridables,
            components_overridables,
        ) = self.manager.get_agent_overridables(self.agent_name)
        assert "default_ledger" in agent_overridables
        assert "timeout" in agent_overridables
        assert "description" in agent_overridables
        assert len(components_overridables) == 2
        assert "is_abstract" in components_overridables[0]

    def test_issue_certificates(self, *args):
        """Test agent alias issue certificates."""
        self.manager.start_manager()
        self.manager.add_project(self.project_public_id, local=True)

        cert_filename = "cert.txt"
        cert_path = os.path.join(self.manager.data_dir, self.agent_name, cert_filename)
        assert not os.path.exists(cert_filename)

        priv_key_path = os.path.abspath(os.path.join(self.working_dir, "priv_key.txt"))
        create_private_key("fetchai", priv_key_path, password=self.PASSWORD)
        assert os.path.exists(priv_key_path)

        component_overrides = [
            {
                **StubConnection.connection_id.json,
                "type": "connection",
                "cert_requests": [
                    {
                        "identifier": "acn",
                        "ledger_id": "fetchai",
                        "not_after": "2022-01-01",
                        "not_before": "2021-01-01",
                        "public_key": "fetchai",
                        "message_format": "{public_key}",
                        "save_path": cert_filename,
                    }
                ],
            }
        ]

        agent_overrides = {
            "private_key_paths": {"fetchai": priv_key_path},
            "connection_private_key_paths": {"fetchai": priv_key_path},
        }
        self.manager.add_agent(
            self.project_public_id,
            self.agent_name,
            agent_overrides=agent_overrides,
            component_overrides=component_overrides,
        )
        agent_alias = self.manager.get_agent_alias(self.agent_name)

        agent_alias.issue_certificates()

        assert os.path.exists(cert_path)

    def test_get_addresses(self, *args) -> None:
        """Test get addresses for agent alias."""
        self.test_add_agent()
        agent_alias = self.manager.get_agent_alias(self.agent_name)
        keys = {
            name: agent_alias._create_private_key(
                ledger=name, replace=True, is_connection=False
            )
            for name in crypto_registry.supported_ids
        }

        connection_keys = {
            name: agent_alias._create_private_key(
                ledger=name, replace=True, is_connection=True
            )
            for name in crypto_registry.supported_ids
        }
        agent_alias.set_overrides(
            {"private_key_paths": keys, "connection_private_key_paths": connection_keys}
        )

        assert len(agent_alias.get_addresses()) == len(crypto_registry.supported_ids)
        assert len(agent_alias.get_connections_addresses()) == len(
            crypto_registry.supported_ids
        )

    def test_addresses_autoadded(self, *args) -> None:
        """Test addresses automatically added on creation."""
        self.test_add_agent()
        agent_alias = self.manager.get_agent_alias(self.agent_name)
        assert len(agent_alias.get_addresses()) == 1
        assert len(agent_alias.get_connections_addresses()) == 1


class TestMultiAgentManagerAsyncMode(
    BaseTestMultiAgentManager
):  # pylint: disable=unused-argument,protected-access,attribute-defined-outside-init
    """Tests for MultiAgentManager in async mode."""


class TestMultiAgentManagerAsyncModeWithPassword(
    BaseTestMultiAgentManager
):  # pylint: disable=unused-argument,protected-access,attribute-defined-outside-init
    """Tests for MultiAgentManager in async mode, with password."""

    PASSWORD = "password"  # nosec


class TestMultiAgentManagerThreadedMode(BaseTestMultiAgentManager):
    """Tests for MultiAgentManager in threaded mode."""

    MODE = "threaded"


class TestMultiAgentManagerThreadedModeWithPassword(BaseTestMultiAgentManager):
    """Tests for MultiAgentManager in threaded mode, with password."""

    MODE = "threaded"
    PASSWORD = "password"  # nosec


def test_project_auto_added_removed():
    """Check project auto added and auto removed on agent added/removed."""
    agent_name = "test_agent"
    with TemporaryDirectory() as tmp_dir, patch(
        "aea.manager.project.Project.build"
    ), patch("aea.manager.project.Project.install_pypi_dependencies"):
        manager = MultiAgentManager(
            tmp_dir,
            mode="async",
            registry_path=PACKAGES_DIR,
            auto_add_remove_project=True,
        )
        try:
            manager.start_manager()
            assert not manager.list_projects()
            manager.add_agent(
                PublicId("fetchai", "my_first_aea"), agent_name, local=True
            )
            assert manager.list_projects()
            assert manager.list_agents()
            manager.remove_agent(agent_name)
            assert not manager.list_agents()
            assert not manager.list_projects()
        finally:
            manager.stop_manager()


def test_handle_error_on_load_state():
    """Check project auto added and auto removed on agent added/removed."""
    agent_name = "test_agent"
    with TemporaryDirectory() as tmp_dir:
        manager = MultiAgentManager(
            tmp_dir,
            mode="async",
            registry_path=PACKAGES_DIR,
            auto_add_remove_project=True,
        )

        with pytest.raises(ValueError, match="Manager was not started"):
            manager.last_start_status

        try:
            manager.start_manager()
            state_loaded, *_ = manager.last_start_status
            assert not state_loaded
            assert not manager.list_projects()
            manager.add_agent(
                PublicId("fetchai", "my_first_aea"), agent_name, local=True
            )
            assert manager.list_projects()
            manager._save_state()
        finally:
            manager.stop_manager(cleanup=False)

        # check loaded well
        manager = MultiAgentManager(
            tmp_dir,
            mode="async",
            registry_path=PACKAGES_DIR,
            auto_add_remove_project=False,
        )
        try:
            manager.start_manager()
            state_loaded, loaded_ok, *_ = manager.last_start_status
            assert state_loaded
            assert len(loaded_ok) == 1
            assert manager.list_projects()
            assert manager.list_agents()
        finally:
            manager.stop_manager(cleanup=False)

        config_file = (
            Path(tmp_dir) / "fetchai/my_first_aea/vendor/fetchai/skills/echo/skill.yaml"
        )
        config_yaml = config_file.read_text()
        new_version = "'>=0.0.1, <0.0.2'"
        new_config = re.sub(
            r"'>=[0-9]+.[0-9]+.[0-9]+, <[0-9]+.[0-9]+.[0-9]+'",
            new_version,
            config_yaml,
        )
        assert new_version in new_config
        config_file.write_text(new_config)
        # check load fails
        manager = MultiAgentManager(
            tmp_dir,
            mode="async",
            registry_path=PACKAGES_DIR,
            auto_add_remove_project=False,
        )
        try:
            manager.start_manager()
            state_loaded, loaded_ok, load_failed = manager.last_start_status
            assert state_loaded
            assert len(loaded_ok) == 0
            assert len(load_failed) == 1
            assert isinstance(load_failed[0][0], PublicId)
            assert isinstance(load_failed[0][1], list)
            assert len(load_failed[0][1]) == 1
            assert isinstance(load_failed[0][1][0], dict)
            assert isinstance(load_failed[0][2], Exception)
            assert re.match(
                "Failed to load project: fetchai/my_first_aea:latest Error: The CLI version is .*, but package fetchai/echo:0.18.0 requires version <0.0.2,>=0.0.1",
                str(load_failed[0][2]),
            )
            assert not manager.list_projects()
            assert not manager.list_agents()
        finally:
            manager.stop_manager()
