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
import sys
import unittest.mock

from .test_base import DummyPID, create_app

dummy_output = """------------------------------
Public ID: fetchai/default:0.2.0
Name: default
Description: The default item allows for any byte logic.
Version: 0.1.0
------------------------------
------------------------------
Public ID: fetchai/oef_search:0.2.0
Name: oef_search
Description: The oef item implements the OEF specific logic.
Version: 0.1.0
------------------------------

"""

dummy_error = """dummy error"""


def _test_list_items(item_type: str):
    """Test for listing generic items supported by an agent."""
    app = create_app()
    pid = DummyPID(0, dummy_output, "")
    agent_name = "test_agent_id"

    def _dummy_call_aea_async(param_list, dir_arg):
        assert param_list[0] == sys.executable
        assert param_list[1] == "-m"
        assert param_list[2] == "aea.cli"
        assert param_list[3] == "list"
        assert param_list[4] == item_type + "s"
        assert agent_name in dir_arg
        return pid

    # Test for actual agent
    with unittest.mock.patch("aea.cli_gui._call_aea_async", _dummy_call_aea_async):
        response_list = app.get(
            "api/agent/" + agent_name + "/" + item_type,
            data=None,
            content_type="application/json",
        )
    data = json.loads(response_list.get_data(as_text=True))
    assert response_list.status_code == 200
    assert len(data) == 2
    assert data[0]["id"] == "fetchai/default:0.2.0"
    assert data[0]["description"] == "The default item allows for any byte logic."
    assert data[1]["id"] == "fetchai/oef_search:0.2.0"
    assert data[1]["description"] == "The oef item implements the OEF specific logic."


def _test_list_items_none(item_type: str):
    """Test for listing generic items supported by an "NONE" - should be empty."""
    app = create_app()
    pid = DummyPID(0, dummy_output, "")
    agent_name = "NONE"

    def _dummy_call_aea_async(param_list, dir_arg):
        assert param_list[0] == sys.executable
        assert param_list[1] == "-m"
        assert param_list[2] == "aea.cli"
        assert param_list[3] == "list"
        assert param_list[4] == item_type + "s"
        return pid

    with unittest.mock.patch("aea.cli_gui._call_aea_async", _dummy_call_aea_async):
        response_list = app.get(
            "api/agent/" + agent_name + "/" + item_type,
            data=None,
            content_type="application/json",
        )
    assert response_list.status_code == 200
    data = json.loads(response_list.get_data(as_text=True))
    assert len(data) == 0


def _test_list_items_fail(item_type: str):
    """Test listing of generic items supported by an agent."""
    app = create_app()
    pid = DummyPID(1, "", dummy_error)
    agent_name = "test_agent_id"

    def _dummy_call_aea_async(param_list, dir_arg):
        assert param_list[0] == sys.executable
        assert param_list[1] == "-m"
        assert param_list[2] == "aea.cli"
        assert param_list[3] == "list"
        assert param_list[4] == item_type + "s"
        assert agent_name in dir_arg
        return pid

    # Test for actual agent
    with unittest.mock.patch("aea.cli_gui._call_aea_async", _dummy_call_aea_async):
        response_list = app.get(
            "api/agent/" + agent_name + "/" + item_type,
            data=None,
            content_type="application/json",
        )
    assert response_list.status_code == 400
    data = json.loads(response_list.get_data(as_text=True))

    assert data["detail"] == dummy_error + "\n"


def test_list_protocols():
    """Test for listing protocols supported by an agent."""
    _test_list_items("protocol")
    _test_list_items_none("protocol")
    _test_list_items_fail("protocol")


def test_list_connections():
    """Test for listing connections supported by an agent."""
    _test_list_items("connection")
    _test_list_items_none("connection")
    _test_list_items_fail("connection")


def test_list_skills():
    """Test for listing connections supported by an agent."""
    _test_list_items("skill")
    _test_list_items_none("skill")
    _test_list_items_fail("skill")
