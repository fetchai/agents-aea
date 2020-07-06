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
from unittest.mock import patch

from tests.test_cli.tools_for_testing import raise_click_exception
from tests.test_cli_gui.test_base import create_app


@patch("aea.cli_gui.cli_delete_aea")
def test_delete_agent(*mocks):
    """Test creating an agent."""
    app = create_app()
    agent_name = "test_agent_id"

    # Ensure there is now one agent
    response_delete = app.delete(
        "api/agent/" + agent_name, data=None, content_type="application/json"
    )
    assert response_delete.status_code == 200
    data = json.loads(response_delete.get_data(as_text=True))
    assert data == "Agent {} deleted".format(agent_name)


@patch("aea.cli_gui.cli_delete_aea", raise_click_exception)
def test_delete_agent_fail(*mocks):
    """Test creating an agent and failing."""
    app = create_app()
    agent_name = "test_agent_id"

    response_delete = app.delete(
        "api/agent/" + agent_name, data=None, content_type="application/json"
    )
    assert response_delete.status_code == 400
    data = json.loads(response_delete.get_data(as_text=True))
    assert data["detail"] == "Failed to delete Agent {} - it may not exist".format(
        agent_name
    )
