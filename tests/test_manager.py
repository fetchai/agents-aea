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
import time
from contextlib import suppress
from shutil import rmtree

import pytest

from aea.configurations.base import PublicId
from aea.manager import Manager


def test_manager():
    """Perform some tests."""
    # pydocsyle
    try:
        working_dir = "manager_dir"
        project_public_id = PublicId("fetchai", "my_first_aea", "0.11.0")
        project_path = os.path.join(
            working_dir, project_public_id.author, project_public_id.name
        )
        assert not os.path.exists(working_dir)
        manager = Manager(working_dir)
        manager.start_manager()
        assert os.path.exists(working_dir)
        assert manager.is_running

        manager.add_project(project_public_id)

        assert project_public_id in manager.list_projects()
        assert os.path.exists(project_path)
        assert manager._projects[project_public_id].path == project_path

        with pytest.raises(ValueError, match=r".*was already added.*"):
            manager.add_project(project_public_id)

        echo_skill_id = PublicId("fetchai", "echo", "0.7.0")
        new_tick_interval = 1.1111
        agent_name = "test_what_ever12"
        manager.add_agent(
            project_public_id,
            agent_name,
            component_overrides=[
                {
                    "type": "skill",
                    **echo_skill_id.json,
                    "behaviours": {
                        "echo": {
                            "args": {"tick_interval": new_tick_interval},
                            "class_name": "EchoBehaviour",
                        }
                    },
                }
            ],
        )
        agent_alias = manager.get_agent_details(agent_name)
        assert agent_alias.name == agent_name
        assert (
            agent_alias.agent.resources.get_behaviour(
                echo_skill_id, "echo"
            ).tick_interval
            == new_tick_interval
        )
        with pytest.raises(ValueError, match="already exists"):
            manager.add_agent(
                project_public_id, agent_name,
            )
        assert agent_name in manager.list_agents()
        manager.start_all_agents()
        assert agent_name in manager.list_agents(running_only=True)
        manager.start_all_agents()

        with pytest.raises(ValueError, match="is already started!"):
            manager.start_agents(manager.list_agents())

        with pytest.raises(ValueError, match="Agent is running. stop it first!"):
            manager.remove_agent(agent_name)

        time.sleep(2)
        manager.stop_all_agents()

        manager.remove_agent(agent_name)
        assert agent_name not in manager.list_agents()

        with pytest.raises(ValueError, match="does not exist!"):
            manager.remove_agent(agent_name)
        manager.remove_project(project_public_id)
        assert project_public_id not in manager._projects
        assert not os.path.exists(project_path)
        assert project_public_id not in manager.list_projects()

        with pytest.raises(ValueError, match=r"was not added"):
            manager.remove_project(project_public_id)
        manager.stop_manager()
        assert not os.path.exists(working_dir)
        assert not manager.is_running
    finally:
        with suppress(FileNotFoundError):
            rmtree(working_dir)
