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

import pytest

import aea
from aea.configurations.constants import DEFAULT_CONNECTION

from .test_base import TempCWD, create_app
from ..conftest import CUR_PATH


@pytest.mark.unstable
def test_create_and_run_agent():
    """Test for running and agent, reading TTY and errors."""
    # Set up a temporary current working directory in which to make agents
    with TempCWD() as temp_cwd:
        app = create_app()

        # copy the 'packages' directory in the parent of the agent folder.
        shutil.copytree(
            Path(CUR_PATH, "..", "packages"), Path(temp_cwd.temp_dir, "packages")
        )

        agent_id = "test_agent"

        # Make an agent
        response_create = app.post(
            "api/agent", content_type="application/json", data=json.dumps(agent_id)
        )
        assert response_create.status_code == 201
        data = json.loads(response_create.get_data(as_text=True))
        assert data == agent_id

        # Add the local connection
        response_add = app.post(
            "api/agent/" + agent_id + "/connection",
            content_type="application/json",
            data=json.dumps("fetchai/local:0.1.0"),
        )
        assert response_add.status_code == 201

        # Get the running status before we have run it
        response_status = app.get(
            "api/agent/" + agent_id + "/run",
            data=None,
            content_type="application/json",
        )
        assert response_status.status_code == 200
        data = json.loads(response_status.get_data(as_text=True))
        assert "NOT_STARTED" in data["status"]

        # run the agent with a non existent connection
        response_run = app.post(
            "api/agent/" + agent_id + "/run",
            content_type="application/json",
            data=json.dumps("author/non-existent-connection:0.1.0"),
        )
        assert response_run.status_code == 400

        # run the agent with default connection - should be something in the error output?
        response_run = app.post(
            "api/agent/" + agent_id + "/run",
            content_type="application/json",
            data=json.dumps(""),
        )
        assert response_run.status_code == 201
        time.sleep(2)

        # Stop the agent running
        response_stop = app.delete(
            "api/agent/" + agent_id + "/run",
            data=None,
            content_type="application/json",
        )
        assert response_stop.status_code == 200
        time.sleep(2)

        # run the agent with stub connection (as no OEF node is running)
        response_run = app.post(
            "api/agent/" + agent_id + "/run",
            content_type="application/json",
            data=json.dumps(str(DEFAULT_CONNECTION)),
        )
        assert response_run.status_code == 201

        time.sleep(2)

        # Try running it again (this should fail)
        response_run = app.post(
            "api/agent/" + agent_id + "/run",
            content_type="application/json",
            data=json.dumps(str(DEFAULT_CONNECTION)),
        )
        assert response_run.status_code == 400

        # Get the running status
        response_status = app.get(
            "api/agent/" + agent_id + "/run",
            data=None,
            content_type="application/json",
        )
        assert response_status.status_code == 200
        data = json.loads(response_status.get_data(as_text=True))

        assert data["error"] == ""
        assert "RUNNING" in data["status"]

        # Create a stop agent function that behaves as if the agent had stopped itself
        def _stop_agent_override(loc_agent_id: str):
            # Test if we have the process id
            assert loc_agent_id in aea.cli_gui.app_context.agent_processes

            aea.cli_gui.app_context.agent_processes[loc_agent_id].terminate()
            aea.cli_gui.app_context.agent_processes[loc_agent_id].wait()

            return "stop_agent: All fine {}".format(loc_agent_id), 200  # 200 (OK)

        with unittest.mock.patch("aea.cli_gui._stop_agent", _stop_agent_override):
            app.delete(
                "api/agent/" + agent_id + "/run",
                data=None,
                content_type="application/json",
            )
        time.sleep(1)

        # Get the running status
        response_status = app.get(
            "api/agent/" + agent_id + "/run",
            data=None,
            content_type="application/json",
        )
        assert response_status.status_code == 200
        data = json.loads(response_status.get_data(as_text=True))
        assert "process terminate" in data["error"]
        assert "FINISHED" in data["status"]

        # run the agent again (takes a different path through code)
        response_run = app.post(
            "api/agent/" + agent_id + "/run",
            content_type="application/json",
            data=json.dumps(str(DEFAULT_CONNECTION)),
        )
        assert response_run.status_code == 201

        time.sleep(2)

        # Get the running status
        response_status = app.get(
            "api/agent/" + agent_id + "/run",
            data=None,
            content_type="application/json",
        )
        assert response_status.status_code == 200
        data = json.loads(response_status.get_data(as_text=True))

        assert data["error"] == ""
        assert "RUNNING" in data["status"]

        # Stop the agent running
        response_stop = app.delete(
            "api/agent/" + agent_id + "/run",
            data=None,
            content_type="application/json",
        )
        assert response_stop.status_code == 200
        time.sleep(2)

        # Get the running status
        response_status = app.get(
            "api/agent/" + agent_id + "/run",
            data=None,
            content_type="application/json",
        )
        assert response_status.status_code == 200
        data = json.loads(response_status.get_data(as_text=True))

        assert "process terminate" in data["error"]
        assert "NOT_STARTED" in data["status"]

        # Stop a none existent agent running
        response_stop = app.delete(
            "api/agent/" + agent_id + "_NOT" + "/run",
            data=None,
            content_type="application/json",
        )
        assert response_stop.status_code == 400
        time.sleep(2)

        genuine_func = aea.cli_gui._call_aea_async

        def _dummy_call_aea_async(param_list, dir_arg):
            assert param_list[0] == sys.executable
            assert param_list[1] == "-m"
            assert param_list[2] == "aea.cli"
            if param_list[3] == "run":
                return None
            else:
                return genuine_func(param_list, dir_arg)

        # Run when process files (but other call - such as status should not fail)
        with unittest.mock.patch("aea.cli_gui._call_aea_async", _dummy_call_aea_async):
            response_run = app.post(
                "api/agent/" + agent_id + "/run",
                content_type="application/json",
                data=json.dumps(str(DEFAULT_CONNECTION)),
            )
        assert response_run.status_code == 400
