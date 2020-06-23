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


@patch("aea.cli_gui.cli_remove_item")
@patch("aea.cli_gui.try_to_load_agent_config")
def test_remove_item(*mocks):
    """Test remove a skill/connection/protocol.

    Actually we just do connection as code coverage is the same.
    """
    app = create_app()

    agent_name = "test_agent_id"
    connection_name = "fetchai/test_connection:0.1.0"

    response_remove = app.post(
        "api/agent/" + agent_name + "/connection/remove",
        content_type="application/json",
        data=json.dumps(connection_name),
    )
    assert response_remove.status_code == 201
    data = json.loads(response_remove.get_data(as_text=True))
    assert data == agent_name


@patch("aea.cli_gui.cli_remove_item", raise_click_exception)
def test_remove_item_fail(*mocks):
    """Test remove a skill/connection/protocol when it fails.

    Actually we just do connection as code coverage is the same.
    """
    app = create_app()

    agent_name = "test_agent_id"
    connection_name = "fetchai/test_connection:0.1.0"

    response_remove = app.post(
        "api/agent/" + agent_name + "/connection/remove",
        content_type="application/json",
        data=json.dumps(connection_name),
    )
    assert response_remove.status_code == 400
    data = json.loads(response_remove.get_data(as_text=True))
    assert data["detail"] == "Failed to remove connection {} from agent {}".format(
        connection_name, agent_name
    )
