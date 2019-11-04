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

"""This test module contains the tests for the `aea create` sub-command."""
import json
import time
from .test_base import TestBase


class TestRunAgent(TestBase):
    """Test for running and agent, reading TTY and errors."""

    def test_create_and_run_agent(self):
        agent_name = "test_agent"

        # Make an agent
        assert self.create_agent(agent_name).status_code == 201

        # Add the local connection
        response_add = self.app.post(
            'api/agent/' + agent_name + "/connection",
            content_type='application/json',
            data=json.dumps("local")
        )
        assert response_add.status_code == 201

        # run the agent
        response_run = self.app.post(
            'api/agent/' + agent_name + "/run",
            data=None,
            content_type='application/json',
        )
        assert response_run.status_code == 201

        time.sleep(2)

        response_status = self.app.get(
            'api/agent/' + agent_name + "/run",
            data=None,
            content_type='application/json',
        )
        assert response_status.status_code == 200
        data = json.loads(response_status.get_data(as_text=True))

        assert data["error"] == ""
        assert "RUNNING" in data["status"]
        assert "do connected finished" in data["tty"]

        response_stop = self.app.delete(
            'api/agent/' + agent_name + "/run",
            data=None,
            content_type='application/json',
        )
        assert response_stop.status_code == 200


