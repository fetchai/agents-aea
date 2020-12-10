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
import os
from contextlib import suppress
from shutil import rmtree
from unittest.mock import Mock, patch

import pytest

from aea.configurations.base import PublicId
from aea.manager import MultiAgentManager

from packages.fetchai.skills.echo import PUBLIC_ID as ECHO_SKILL_PUBLIC_ID

from tests.common.utils import wait_for_condition
from tests.conftest import MY_FIRST_AEA_PUBLIC_ID


class TestMultiAgentManagerAsyncMode:  # pylint: disable=unused-argument,protected-access,attribute-defined-outside-init
    """Tests for MultiAgentManager in async mode."""

    MODE = "async"

    echo_skill_id = ECHO_SKILL_PUBLIC_ID

    def setup(self):
        """Set test case."""
        self.agent_name = "test_what_ever12"
        self.working_dir = "MultiAgentManager_dir"
        self.project_public_id = MY_FIRST_AEA_PUBLIC_ID
        self.project_path = os.path.join(
            self.working_dir, self.project_public_id.author, self.project_public_id.name
        )
        assert not os.path.exists(self.working_dir)
        self.manager = MultiAgentManager(self.working_dir, mode=self.MODE)

    def teardown(self):
        """Tear down test case."""
        self.manager.stop_manager()

    def test_workdir_created_removed(self):
        """Check work dit created removed on MultiAgentManager start and stop."""
        assert not os.path.exists(self.working_dir)
        self.manager.start_manager()
        assert os.path.exists(self.working_dir)
        self.manager.stop_manager()
        assert not os.path.exists(self.working_dir)
        assert not os.path.exists(self.working_dir)

    def test_keys_dir_presents(self):
        """Check not fails on exists key dir."""
        try:
            os.makedirs(self.working_dir)
            os.makedirs(self.manager._keys_dir)
            self.manager.start_manager()
            self.manager.stop_manager()
        finally:
            with suppress(Exception):
                rmtree(self.working_dir)

    def test_MultiAgentManager_is_running(self):
        """Check MultiAgentManager is running property reflects state."""
        assert not self.manager.is_running
        self.manager.start_manager()
        assert self.manager.is_running
        self.manager.stop_manager()
        assert not self.manager.is_running

    def test_add_remove_project(self):
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

    def test_add_agent(self):
        """Test add agent alias."""
        self.manager.start_manager()

        self.manager.add_project(self.project_public_id, local=True)

        new_tick_interval = 0.2111

        self.manager.add_agent(
            self.project_public_id,
            self.agent_name,
            component_overrides=[
                {
                    **self.echo_skill_id.json,
                    "type": "skill",
                    "behaviours": {
                        "echo": {"args": {"tick_interval": new_tick_interval}}
                    },
                }
            ],
        )
        agent_alias = self.manager.get_agent_alias(self.agent_name)
        assert agent_alias.agent_name == self.agent_name
        assert (
            agent_alias.agent.resources.get_behaviour(
                self.echo_skill_id, "echo"
            ).tick_interval
            == new_tick_interval
        )
        with pytest.raises(ValueError, match="already exists"):
            self.manager.add_agent(
                self.project_public_id, self.agent_name,
            )

    def test_remove_agent(self):
        """Test remove agent alias."""
        self.test_add_agent()
        assert self.agent_name in self.manager.list_agents()
        self.manager.remove_agent(self.agent_name)
        assert self.agent_name not in self.manager.list_agents()

        with pytest.raises(ValueError, match="does not exist!"):
            self.manager.remove_agent(self.agent_name)

    def test_remove_project_with_alias(self):
        """Test remove project with alias presents."""
        self.test_add_agent()

        with pytest.raises(
            ValueError, match="Can not remove projects with aliases exists"
        ):
            self.manager.remove_project(self.project_public_id)

    def test_add_agent_for_non_exist_project(self):
        """Test add agent when no project added."""
        with pytest.raises(ValueError, match=" project is not added"):
            self.manager.add_agent(PublicId("test", "test", "0.1.0"), "another_agent")

    def test_agent_actually_running(self):
        """Test MultiAgentManager starts agent correctly and agent perform acts."""
        self.test_add_agent()
        agent_alias = self.manager.get_agent_alias(self.agent_name)
        behaviour = agent_alias.agent.resources.get_behaviour(
            self.echo_skill_id, "echo"
        )
        assert behaviour
        with patch.object(behaviour, "act") as act_mock:
            self.manager.start_all_agents()
            wait_for_condition(lambda: act_mock.call_count > 0, timeout=10)

    def test_exception_handling(self):
        """Test erro callback works."""
        self.test_add_agent()
        agent_alias = self.manager.get_agent_alias(self.agent_name)
        behaviour = agent_alias.agent.resources.get_behaviour(
            self.echo_skill_id, "echo"
        )
        callback_mock = Mock()

        self.manager.add_error_callback(callback_mock)
        assert behaviour

        with patch.object(behaviour, "act", side_effect=ValueError("expected")):
            self.manager.start_all_agents()
            wait_for_condition(lambda: callback_mock.call_count > 0, timeout=10)

    def test_stop_from_exception_handling(self):
        """Test stop MultiAgentManager from erro callback."""
        self.test_add_agent()
        agent_alias = self.manager.get_agent_alias(self.agent_name)
        behaviour = agent_alias.agent.resources.get_behaviour(
            self.echo_skill_id, "echo"
        )

        def handler(*args, **kwargs):
            self.manager.stop_manager()

        self.manager.add_error_callback(handler)

        assert behaviour

        with patch.object(behaviour, "act", side_effect=ValueError("expected")):
            self.manager.start_all_agents()
            wait_for_condition(lambda: not self.manager.is_running, timeout=10)

    def test_start_all(self):
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

    def test_stop_agent(self):
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

    def test_do_no_allow_override_some_fields(self):
        """Do not allo to override some values in agent config."""
        self.manager.start_manager()

        self.manager.add_project(self.project_public_id, local=True)

        BAD_OVERRIDES = ["skills", "connections", "contracts", "protocols"]

        for bad_override in BAD_OVERRIDES:
            with pytest.raises(ValueError, match="Do not override any"):
                self.manager.add_agent(
                    self.project_public_id,
                    self.agent_name,
                    agent_overrides={bad_override: "some value"},
                )

    @staticmethod
    def test_invalid_mode():
        """Test MultiAgentManager fails on invalid mode."""
        with pytest.raises(ValueError, match="Invalid mode"):
            MultiAgentManager("test_dir", mode="invalid_mode")

    def test_double_start(self):
        """Test double MultiAgentManager start."""
        self.manager.start_manager()
        assert self.manager.is_running
        self.manager.start_manager()
        assert self.manager.is_running

    def test_double_stop(self):
        """Test double MultiAgentManager stop."""
        self.manager.start_manager()
        assert self.manager.is_running
        self.manager.stop_manager()
        assert not self.manager.is_running
        self.manager.stop_manager()
        assert not self.manager.is_running

    @pytest.mark.asyncio
    async def test_run_loop_direct_call(self):
        """Test do not allow to run MultiAgentManager_loop directly."""
        with pytest.raises(
            ValueError, match="Do not use this method directly, use start_manager"
        ):
            await self.manager._manager_loop()

    def test_remove_running_agent(self):
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

    def test_install_pypi_dependencies(self):
        """Test add agent alias."""
        self.manager.start_manager()

        self.manager.add_project(self.project_public_id, local=True)

        # check empty project, nothing should be installed
        with patch(
            "aea.aea_builder.AEABuilder.install_pypi_dependencies", return_value=None
        ) as install_mock:
            self.manager.install_pypi_dependencies()
            install_mock.assert_not_called()

        self.manager.add_agent(
            self.project_public_id, self.agent_name,
        )

        self.manager.add_agent(
            self.project_public_id, self.agent_name + "2222",
        )

        # check project with two agents, install once!
        with patch(
            "aea.aea_builder.AEABuilder.install_pypi_dependencies", return_value=None
        ) as install_mock:
            self.manager.install_pypi_dependencies()
            install_mock.assert_called_once()

    def test_save_load_positive(self):
        """Test save-load func of MultiAgentManager for positive result."""
        self.manager.start_manager()
        self.manager.add_project(self.project_public_id, local=True)

        self.manager.add_agent(self.project_public_id, self.agent_name)
        self.manager.stop_manager(save=True)
        assert os.path.exists(self.manager._save_path)

        self.manager.start_manager()
        assert self.project_public_id in self.manager._projects.keys()
        assert self.agent_name in self.manager._agents.keys()

    def test_list_agents_info_positive(self):
        """Test list_agents_info method for positive result."""
        self.manager.start_manager()
        self.manager.add_project(self.project_public_id, local=True)

        self.manager.add_agent(self.project_public_id, self.agent_name)
        result = self.manager.list_agents_info()
        expected_result = [
            {
                "agent_name": self.agent_name,
                "public_id": str(self.project_public_id),
                "is_running": False,
            }
        ]
        assert result == expected_result


class TestMultiAgentManagerThreadedMode(TestMultiAgentManagerAsyncMode):
    """Tests for MultiAgentManager in threaded mode."""

    MODE = "threaded"
