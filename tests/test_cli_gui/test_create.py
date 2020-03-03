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

"""This test module contains the tests for the `aea gui` sub-commands."""
import json
import shutil
import sys
import time
import unittest.mock
from pathlib import Path

from .test_base import TempCWD, create_app
from ..conftest import CUR_PATH


def test_create_agent():
    """Test creating an agent."""
    app = create_app()
    agent_name = "test_agent_id"

    def _dummy_call_aea(param_list, dir):
        assert param_list[0] == sys.executable
        assert param_list[1] == "-m"
        assert param_list[2] == "aea.cli"
        assert param_list[3] == "create"
        assert param_list[4] == agent_name
        return 0

    with unittest.mock.patch("aea.cli_gui._call_aea", _dummy_call_aea):
        # Ensure there is now one agent
        response_create = app.post(
            "api/agent", content_type="application/json", data=json.dumps(agent_name)
        )
    assert response_create.status_code == 201
    data = json.loads(response_create.get_data(as_text=True))
    assert data == agent_name


def test_create_agent_fail():
    """Test creating an agent and failing."""
    app = create_app()
    agent_name = "test_agent_id"

    def _dummy_call_aea(param_list, dir):
        assert param_list[0] == sys.executable
        assert param_list[1] == "-m"
        assert param_list[2] == "aea.cli"
        assert param_list[3] == "create"
        assert param_list[4] == agent_name
        return 1

    with unittest.mock.patch("aea.cli_gui._call_aea", _dummy_call_aea):
        # Ensure there is now one agent
        response_create = app.post(
            "api/agent", content_type="application/json", data=json.dumps(agent_name)
        )
    assert response_create.status_code == 400
    data = json.loads(response_create.get_data(as_text=True))
    assert data[
        "detail"
    ] == "Failed to create Agent {} - a folder of this name may exist already".format(
        agent_name
    )


def test_real_create():
    """Really create an agent (have to test the call_aea at some point)."""
    # Set up a temporary current working directory to make agents in
    with TempCWD() as temp_cwd:
        app = create_app()

        # copy the 'packages' directory in the parent of the agent folder.
        shutil.copytree(
            Path(CUR_PATH, "..", "packages"), Path(temp_cwd.temp_dir, "packages")
        )

        agent_id = "test_agent_id"
        response_create = app.post(
            "api/agent", content_type="application/json", data=json.dumps(agent_id)
        )
        assert response_create.status_code == 201
        data = json.loads(response_create.get_data(as_text=True))
        assert data == agent_id

        # Give it a bit of time so the polling funcionts get called
        time.sleep(1)

        # Check that we can actually see this agent too
        response_agents = app.get(
            "api/agent", data=None, content_type="application/json",
        )
        data = json.loads(response_agents.get_data(as_text=True))
        assert response_agents.status_code == 200
        assert len(data) == 1
        assert data[0]["id"] == agent_id
        assert data[0]["description"] == "placeholder description"

        # do same but this time find that this is not an agent directory.
        with unittest.mock.patch("os.path.isdir", return_value=False):
            response_agents = app.get(
                "api/agent", data=None, content_type="application/json",
            )
        data = json.loads(response_agents.get_data(as_text=True))
        assert response_agents.status_code == 200
        assert len(data) == 0
