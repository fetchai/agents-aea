
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

import unittest.mock

from .test_base import create_app


def test_create_agent():
    """Test creating an agent."""
    app = create_app()
    agent_name = "test_agent_id"

    def _dummy_call_aea(param_list, dir):
        assert param_list[0] == "aea"
        assert param_list[1] == "create"
        assert param_list[2] == agent_name
        return 0

    with unittest.mock.patch("aea.cli_gui._call_aea", _dummy_call_aea):
        # Ensure there is now one agent
        response_create = app.post(
            'api/agent',
            content_type='application/json',
            data=json.dumps(agent_name))
    assert response_create.status_code == 201
    data = json.loads(response_create.get_data(as_text=True))
    assert data == agent_name


def test_create_agent_fail():
    """Test creating an agent and failing."""
    app = create_app()
    agent_name = "test_agent_id"

    def _dummy_call_aea(param_list, dir):
        assert param_list[0] == "aea"
        assert param_list[1] == "create"
        assert param_list[2] == agent_name
        return 1

    with unittest.mock.patch("aea.cli_gui._call_aea", _dummy_call_aea):
        # Ensure there is now one agent
        response_create = app.post(
            'api/agent',
            content_type='application/json',
            data=json.dumps(agent_name))
    assert response_create.status_code == 400
    data = json.loads(response_create.get_data(as_text=True))
    assert data['detail'] == 'Failed to create Agent {} - a folder of this name may exist already'.format(agent_name)
