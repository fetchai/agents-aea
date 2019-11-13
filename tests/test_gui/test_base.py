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
import os
import shutil
import json

import tempfile

import aea.cli_gui


class TestBase:
    """Base class for testing gui entry points."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.temp_dir = tempfile.mkdtemp()
        cls.cwd = os.getcwd()
        os.chdir(cls.temp_dir)

        cls.app = aea.cli_gui.run_test()
        cls.app.debug = True
        cls.app.testing = True

    def create_agent(self, name):
        """Create an aea project."""
        return self.app.post(
            'api/agent',
            content_type='application/json',
            data=json.dumps(name))

    @classmethod
    def teardown_class(cls):
        """Teardowm the test."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.temp_dir)
        except (OSError, IOError):
            pass

    def _test_create_and_list(self, item_type, new_item_name):
        agent_name = "test_agent"

        # Make an agent
        assert self.create_agent(agent_name).status_code == 201

        # Get list of items on this agent
        response_list = self.app.get(
            'api/agent/' + agent_name + "/" + item_type,
            data=None,
            content_type='application/json',
        )
        data = json.loads(response_list.get_data(as_text=True))
        assert response_list.status_code == 200
        prev_count = len(data)

        # Get list of items from the package
        response_list = self.app.get(
            'api/' + item_type,
            data=None,
            content_type='application/json',
        )
        data = json.loads(response_list.get_data(as_text=True))
        assert response_list.status_code == 200
        assert len(data) > 0

        # Add a item
        response_create = self.app.post(
            'api/agent/' + agent_name + "/" + item_type,
            content_type='application/json',
            data=json.dumps(new_item_name)
        )
        assert response_create.status_code == 201

        # Get list of items
        response_list = self.app.get(
            'api/agent/' + agent_name + "/" + item_type,
            data=None,
            content_type='application/json',
        )
        data = json.loads(response_list.get_data(as_text=True))
        assert response_list.status_code == 200
        assert len(data) == prev_count + 1
        new_item_exists = False
        for element in data:
            assert element['id'] != ""
            assert element['description'] != ""
            if element['id'] == new_item_name:
                new_item_exists = True
        assert new_item_exists

        # Remove the item
        response_delete = self.app.delete(
            'api/agent/' + agent_name + "/" + item_type + "/" + new_item_name,
            data=None,
            content_type='application/json',
        )
        assert response_delete.status_code == 201

        # Get list of items
        response_list = self.app.get(
            'api/agent/' + agent_name + "/" + item_type,
            data=None,
            content_type='application/json',
        )
        data = json.loads(response_list.get_data(as_text=True))
        assert response_list.status_code == 200
        assert len(data) == prev_count

        # Scaffold item
        scaffold_item_name = "scaffold_item"
        response_create = self.app.post(
            'api/agent/' + agent_name + "/" + item_type + "/scaffold",
            content_type='application/json',
            data=json.dumps(scaffold_item_name)
        )
        assert response_create.status_code == 201

        # Get list of items
        response_list = self.app.get(
            'api/agent/' + agent_name + "/" + item_type,
            data=None,
            content_type='application/json',
        )
        data = json.loads(response_list.get_data(as_text=True))
        assert response_list.status_code == 200
        assert len(data) == prev_count + 1
        new_item_exists = False
        for element in data:
            assert element['id'] != ""
            assert element['description'] != ""
            if element['id'] == scaffold_item_name:
                new_item_exists = True
        assert new_item_exists
