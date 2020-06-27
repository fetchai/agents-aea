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

"""This test module contains the tests for the `aea gui` sub-commands."""

import json
from unittest.mock import patch

from tests.test_cli.tools_for_testing import raise_click_exception
from tests.test_cli_gui.test_base import create_app


@patch("aea.cli_gui.cli_fetch_agent")
def test_fetch_agent(*mocks):
    """Test fetch an agent."""
    app = create_app()

    agent_name = "test_agent_name"
    agent_id = "author/{}:0.1.0".format(agent_name)

    # Ensure there is now one agent
    resp = app.post(
        "api/fetch-agent", content_type="application/json", data=json.dumps(agent_id),
    )
    assert resp.status_code == 201
    data = json.loads(resp.get_data(as_text=True))
    assert data == agent_name


@patch("aea.cli_gui.cli_fetch_agent", raise_click_exception)
def test_fetch_agent_fail(*mocks):
    """Test fetch agent fail."""
    app = create_app()

    agent_name = "test_agent_name"
    agent_id = "author/{}:0.1.0".format(agent_name)

    resp = app.post(
        "api/fetch-agent", content_type="application/json", data=json.dumps(agent_id),
    )
    assert resp.status_code == 400
    data = json.loads(resp.get_data(as_text=True))
    assert data["detail"] == "Failed to fetch an agent {}. {}".format(
        agent_id, "Message"
    )
