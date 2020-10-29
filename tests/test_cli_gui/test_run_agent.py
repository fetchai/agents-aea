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
from pathlib import Path
from unittest.mock import patch

import pytest

import aea
from aea.cli.create import create_aea
from aea.cli.utils.context import Context
from aea.test_tools.constants import DEFAULT_AUTHOR

from packages.fetchai.connections.local.connection import PUBLIC_ID as LOCAL_PUBLIC_ID
from packages.fetchai.connections.stub.connection import (
    PUBLIC_ID as STUB_CONNECTION_PUBLIC_ID,
)

from tests.conftest import CUR_PATH, MAX_FLAKY_RERUNS
from tests.test_cli_gui.test_base import TempCWD, create_app


@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
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
        # We do it programmatically as we need to create an agent with default author
        # that was prevented from GUI.
        ctx = Context(cwd=temp_cwd.temp_dir)
        ctx.set_config("is_local", True)
        create_aea(ctx, agent_id, local=True, author=DEFAULT_AUTHOR)

        # Add the local connection
        with patch("aea.cli_gui.app_context.local", True):
            response_add = app.post(
                "api/agent/" + agent_id + "/connection",
                content_type="application/json",
                data=json.dumps(str(LOCAL_PUBLIC_ID)),
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

        # run the agent with stub connection
        response_run = app.post(
            "api/agent/" + agent_id + "/run",
            content_type="application/json",
            data=json.dumps(str(STUB_CONNECTION_PUBLIC_ID)),
        )
        assert response_run.status_code == 201

        time.sleep(2)

        # Try running it again (this should fail)
        response_run = app.post(
            "api/agent/" + agent_id + "/run",
            content_type="application/json",
            data=json.dumps(str(STUB_CONNECTION_PUBLIC_ID)),
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
        assert "NOT_STARTED" in data["status"]

        # run the agent again (takes a different path through code)
        response_run = app.post(
            "api/agent/" + agent_id + "/run",
            content_type="application/json",
            data=json.dumps(str(STUB_CONNECTION_PUBLIC_ID)),
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

        genuine_func = aea.cli_gui.call_aea_async

        def _dummycall_aea_async(param_list, dir_arg):
            assert param_list[0] == sys.executable
            assert param_list[1] == "-m"
            assert param_list[2] == "aea.cli"
            if param_list[3] == "run":
                return None
            else:
                return genuine_func(param_list, dir_arg)

        # Run when process files (but other call - such as status should not fail)
        with patch("aea.cli_gui.call_aea_async", _dummycall_aea_async):
            response_run = app.post(
                "api/agent/" + agent_id + "/run",
                content_type="application/json",
                data=json.dumps(str(STUB_CONNECTION_PUBLIC_ID)),
            )
        assert response_run.status_code == 400
