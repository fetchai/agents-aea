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

from tests.test_cli_gui.test_base import create_app


@patch("aea.cli_gui.cli_list_agent_items", return_value=[{"name": "some-connection"}])
@patch("aea.cli_gui.try_to_load_agent_config")
def test_list_connections(*mocks):
    """Test list localConnections."""
    app = create_app()

    response = app.get("api/agent/agent_name/connection")
    assert response.status_code == 200

    result = json.loads(response.get_data(as_text=True))
    expected_result = [{"name": "some-connection"}]
    assert result == expected_result
