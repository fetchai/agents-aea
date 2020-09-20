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
"""Test module for get registered items with CLI GUI."""

import json
from unittest import TestCase, mock

from tests.test_cli.tools_for_testing import raise_click_exception
from tests.test_cli_gui.test_base import create_app


class GetRegisteredItemsTestCase(TestCase):
    """Test case for get_registered_items API."""

    def setUp(self):
        """Set up test case."""
        self.app = create_app()

    @mock.patch("aea.cli_gui.cli_setup_search_ctx")
    @mock.patch(
        "aea.cli_gui.cli_search_items", return_value=([{"name": "some-connection"}], 1)
    )
    def test_get_registered_items_positive(
        self, cli_setup_search_ctx_mock, cli_search_items_mock
    ):
        """Test case for get_registered_items API positive response."""
        response = self.app.get("api/connection")
        self.assertEqual(response.status_code, 200)

        result = json.loads(response.get_data(as_text=True))
        expected_result = [{"name": "some-connection"}]
        self.assertEqual(result, expected_result)

        cli_setup_search_ctx_mock.assert_called_once()
        cli_search_items_mock.assert_called_once()

    @mock.patch("aea.cli_gui.cli_setup_search_ctx", raise_click_exception)
    def test_get_registered_items_negative(self, *mocks):
        """Test case for get_registered_items API negative response."""
        response = self.app.get("api/connection")
        self.assertEqual(response.status_code, 400)

        result = json.loads(response.get_data(as_text=True))
        expected_result = "Failed to search items."
        self.assertEqual(result["detail"], expected_result)


class GetLocalItemsTestCase(TestCase):
    """Test case for get_local_items API."""

    def setUp(self):
        """Set up test case."""
        self.app = create_app()

    @mock.patch("aea.cli_gui.try_to_load_agent_config")
    @mock.patch(
        "aea.cli_gui.cli_list_agent_items", return_value=[{"name": "some-connection"}]
    )
    def test_get_local_items_positive(self, *mocks):
        """Test case for get_local_items API positive response."""
        response = self.app.get("api/agent/NONE/connection")
        self.assertEqual(response.status_code, 200)
        result = json.loads(response.get_data(as_text=True))
        self.assertEqual(result, [])

        response = self.app.get("api/agent/agent_id/connection")
        self.assertEqual(response.status_code, 200)

        result = json.loads(response.get_data(as_text=True))
        expected_result = [{"name": "some-connection"}]
        self.assertEqual(result, expected_result)

    @mock.patch("aea.cli_gui.try_to_load_agent_config", raise_click_exception)
    def test_get_local_items_negative(self, *mocks):
        """Test case for get_local_items API negative response."""
        response = self.app.get("api/agent/agent_id/connection")
        self.assertEqual(response.status_code, 400)

        result = json.loads(response.get_data(as_text=True))
        expected_result = "Failed to list agent items."
        self.assertEqual(result[0]["detail"], expected_result)
