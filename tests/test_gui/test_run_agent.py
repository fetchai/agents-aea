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
import time
from .test_base import create_app, TempCWD


def test_create_and_run_agent():
    """Test for running and agent, reading TTY and errors."""
    # Set up a temporary current working directory to make agents in
    temp_cwd = TempCWD()
    app = create_app()

    agent_id = "test_agent"

    # Make an agent
    response_create = app.post(
        'api/agent',
        content_type='application/json',
        data=json.dumps(agent_id))
    assert response_create.status_code == 201
    data = json.loads(response_create.get_data(as_text=True))
    assert data == agent_id

    # Add the local connection
    response_add = app.post(
        'api/agent/' + agent_id + "/connection",
        content_type='application/json',
        data=json.dumps("local")
    )
    assert response_add.status_code == 201

    # run the agent with local connection (as no OEF node is running)
    response_run = app.post(
        'api/agent/' + agent_id + "/run",
        content_type='application/json',
        data=json.dumps("local")
    )
    assert response_run.status_code == 201

    time.sleep(2)

    # Get the running status
    response_status = app.get(
        'api/agent/' + agent_id + "/run",
        data=None,
        content_type='application/json',
    )
    assert response_status.status_code == 200
    data = json.loads(response_status.get_data(as_text=True))

    assert data["error"] == ""
    assert "RUNNING" in data["status"]

    # Stop the agent running
    response_stop = app.delete(
        'api/agent/' + agent_id + "/run",
        data=None,
        content_type='application/json',
    )
    assert response_stop.status_code == 200

    # Get the running status
    response_status = app.get(
        'api/agent/' + agent_id + "/run",
        data=None,
        content_type='application/json',
    )
    assert response_status.status_code == 200
    data = json.loads(response_status.get_data(as_text=True))

    # this is flakey - just remove for the moment.
    # assert "process terminate" in data["error"]
    assert "NOT_STARTED" in data["status"]

    # run the agent again (takes a different path through code)
    response_run = app.post(
        'api/agent/' + agent_id + "/run",
        content_type='application/json',
        data=json.dumps("local")
    )
    assert response_run.status_code == 201

    time.sleep(2)

    # Get the running status
    response_status = app.get(
        'api/agent/' + agent_id + "/run",
        data=None,
        content_type='application/json',
    )
    assert response_status.status_code == 200
    data = json.loads(response_status.get_data(as_text=True))

    assert data["error"] == ""
    assert "RUNNING" in data["status"]

    # Destroy the temporary current working directory and put cwd back to what it was before
    temp_cwd.destroy()
