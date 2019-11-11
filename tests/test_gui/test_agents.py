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

from .test_base import TestBase


class TestHomePageExits(TestBase):
    """Test that the gui home page exits and has the correct title."""

    def test_home_page_exits(self):
        """Test that the home-page exits."""
        # sends HTTP GET request to the application
        # on the specified path
        result = self.app.get('/')

        # assert the status code of the response
        assert result.status_code == 200
        assert "Fetch.AI AEA CLI REST API" in str(result.data)


class TestCreateAndList(TestBase):
    """Test that we can create an agent and get list of agents."""

    def test_agents_create_and_list(self):
        """Test that we can create an agent and get list of agents."""
        agent_name = "test_agent"

        # Make sure there are no agents in the directory
        response_list = self.app.get(
            'api/agent',
            data=None,
            content_type='application/json',
        )
        data = json.loads(response_list.get_data(as_text=True))
        assert len(data) == 0
        assert response_list.status_code == 200

        # Make an agent
        assert self.create_agent(agent_name).status_code == 201

        # Ensure there is now one agent
        response_list = self.app.get(
            'api/agent',
            data=None,
            content_type='application/json',
        )
        data = json.loads(response_list.get_data(as_text=True))
        assert response_list.status_code == 200
        assert len(data) == 1
        assert data[0]['id'] == agent_name

        # Delete the agent
        response_delete = self.app.delete(
            'api/agent/' + agent_name,
            data=None,
            content_type='application/json',
        )
        assert response_delete.status_code == 200

        # Ensure there are now agents
        response_list = self.app.get(
            'api/agent',
            data=None,
            content_type='application/json',
        )
        data = json.loads(response_list.get_data(as_text=True))
        assert response_list.status_code == 200
        assert len(data) == 0


class TestDuplicateAgentError(TestBase):
    """Test that if you try and create two agents of the same name we get an error."""

    def test_duplicate_agent_error(self):
        """Test that if you try and create two agents of the same name we get an error."""
        response_list = self.app.get(
            'api/agent',
            data=None,
            content_type='application/json',
        )
        data = json.loads(response_list.get_data(as_text=True))
        assert len(data) == 0
        assert response_list.status_code == 200

        # Make an agent
        assert self.create_agent("test_agent").status_code == 201

        # Attempt tp make the same agent again
        assert self.create_agent("test_agent").status_code == 400
