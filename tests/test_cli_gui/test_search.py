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

from tests.common.utils import run_in_root_dir

from .test_base import DummyPID, create_app

dummy_output = """Available items:
------------------------------
Public ID: fetchai/default:0.1.0
Name: default
Description: The default item allows for any byte logic.
Version: 0.1.0
------------------------------
------------------------------
Public ID: fetchai/oef_search:0.1.0
Name: oef_search
Description: The oef item implements the OEF specific logic.
Version: 0.1.0
------------------------------

"""

dummy_error = """dummy error"""


def _test_search_items_with_query(item_type: str, query: str):
    """Test searching of generic items in registry."""
    app = create_app()

    pid = DummyPID(0, dummy_output, "")

    # Test for actual agent
    with unittest.mock.patch("aea.cli_gui._call_aea_async", return_value=pid):
        response_list = app.get(
            "api/" + item_type + "/" + query,
            data=None,
            content_type="application/json",
        )
    assert response_list.status_code == 200
    data = json.loads(response_list.get_data(as_text=True))
    assert len(data["search_result"]) == 2
    assert data["search_result"][0]["id"] == "fetchai/default:0.1.0"
    assert (
        data["search_result"][0]["description"]
        == "The default item allows for any byte logic."
    )
    assert data["search_result"][1]["id"] == "fetchai/oef_search:0.1.0"
    assert (
        data["search_result"][1]["description"]
        == "The oef item implements the OEF specific logic."
    )
    assert data["item_type"] == item_type
    assert data["search_term"] == "test"


def _test_search_items(item_type: str):
    """Test searching of generic items in registry."""
    app = create_app()

    pid = DummyPID(0, dummy_output, "")

    # Test for actual agent
    with unittest.mock.patch("aea.cli_gui._call_aea_async", return_value=pid):
        response_list = app.get(
            "api/" + item_type, data=None, content_type="application/json",
        )
    assert response_list.status_code == 200
    data = json.loads(response_list.get_data(as_text=True))
    assert len(data) == 2
    assert data[0]["id"] == "fetchai/default:0.1.0"
    assert data[0]["description"] == "The default item allows for any byte logic."
    assert data[1]["id"] == "fetchai/oef_search:0.1.0"
    assert data[1]["description"] == "The oef item implements the OEF specific logic."


def _test_search_items_fail(item_type: str):
    """Test searching of generic items in registry failing."""
    app = create_app()

    pid = DummyPID(1, "", dummy_error)

    with unittest.mock.patch("aea.cli_gui._call_aea_async", return_value=pid):
        response_list = app.get(
            "api/" + item_type, data=None, content_type="application/json",
        )
    assert response_list.status_code == 400
    data = json.loads(response_list.get_data(as_text=True))

    assert data["detail"] == dummy_error + "\n"


def test_search_protocols():
    """Test for listing protocols supported by an agent."""
    _test_search_items("protocol")
    _test_search_items_fail("protocol")
    _test_search_items_with_query("protocol", "test")


def test_search_connections():
    """Test for listing connections supported by an agent."""
    _test_search_items("connection")
    _test_search_items_fail("connection")
    _test_search_items_with_query("connection", "test")


def test_list_skills():
    """Test for listing connections supported by an agent."""
    _test_search_items("skill")
    _test_search_items_fail("skill")
    _test_search_items_with_query("skill", "test")


@run_in_root_dir
def test_real_search():
    """Call at least one function that actually calls call_aea_async."""
    app = create_app()
    # Test for actual agent
    response_list = app.get(
        "api/connection", data=None, content_type="application/json",
    )
    assert response_list.status_code == 200
    data = json.loads(response_list.get_data(as_text=True))

    assert len(data) == 13, data
    i = 0

    assert data[i]["id"] == "fetchai/gym:0.1.0"
    assert data[i]["description"] == "The gym connection wraps an OpenAI gym."
    i += 1
    assert data[i]["id"] == "fetchai/http_client:0.2.0"
    assert (
        data[i]["description"]
        == "The HTTP_client connection that wraps a web-based client connecting to a RESTful API specification."
    )
    i += 1
    assert data[i]["id"] == "fetchai/http_server:0.2.0"
    assert (
        data[i]["description"]
        == "The HTTP server connection that wraps http server implementing a RESTful API specification."
    )
    i += 1
    assert data[i]["id"] == "fetchai/local:0.1.0"
    assert (
        data[i]["description"]
        == "The local connection provides a stub for an OEF node."
    )
    i += 1
    assert data[i]["id"] == "fetchai/oef:0.3.0"
    assert (
        data[i]["description"]
        == "The oef connection provides a wrapper around the OEF SDK for connection with the OEF search and communication node."
    )
    i += 1
    assert data[i]["id"] == "fetchai/p2p_client:0.1.0"
    assert (
        data[i]["description"]
        == "The p2p_client connection provides a connection with the fetch.ai mail provider."
    )
    i += 1
    assert data[i]["id"] == "fetchai/p2p_libp2p:0.2.0"
    assert (
        data[i]["description"]
        == "The p2p libp2p connection implements an interface to standalone golang go-libp2p node that can exchange aea envelopes with other agents connected to the same DHT."
    )
    i += 1
    assert data[i]["id"] == "fetchai/p2p_noise:0.2.0"
    assert (
        data[i]["description"]
        == "The p2p noise connection implements an interface to standalone golang noise node that can exchange aea envelopes with other agents participating in the same p2p network."
    )
    i += 1
    assert data[i]["id"] == "fetchai/p2p_stub:0.1.0"
    assert (
        data[i]["description"]
        == "The stub p2p connection implements a local p2p connection allowing agents to communicate with each other through files created in the namespace directory."
    )
    i += 1
    assert data[i]["id"] == "fetchai/soef:0.1.0"
    assert (
        data[i]["description"]
        == "The soef connection provides a connection api to the simple OEF."
    )
    i += 1
    assert data[i]["id"] == "fetchai/stub:0.4.0"
    assert (
        data[i]["description"]
        == "The stub connection implements a connection stub which reads/writes messages from/to file."
    )
    i += 1
    assert data[i]["id"] == "fetchai/tcp:0.1.0"
    assert (
        data[i]["description"]
        == "The tcp connection implements a tcp server and client."
    )
    i += 1
    assert data[i]["id"] == "fetchai/webhook:0.1.0"
    assert (
        data[i]["description"]
        == "The webhook connection that wraps a webhook functionality."
    )
