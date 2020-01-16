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

from .test_base import DummyPID, create_app

dummy_output = """Available items:
------------------------------
Name: default
Description: The default item allows for any byte logic.
Version: 0.1.0
------------------------------
------------------------------
Name: oef
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
            'api/' + item_type + "/" + query,
            data=None,
            content_type='application/json',
        )
    assert response_list.status_code == 200
    data = json.loads(response_list.get_data(as_text=True))
    assert len(data["search_result"]) == 2
    assert data["search_result"][0]['id'] == 'default'
    assert data["search_result"][0]['description'] == 'The default item allows for any byte logic.'
    assert data["search_result"][1]['id'] == 'oef'
    assert data["search_result"][1]['description'] == 'The oef item implements the OEF specific logic.'
    assert data["item_type"] == item_type
    assert data["search_term"] == 'test'


def _test_search_items(item_type: str):
    """Test searching of generic items in registry."""
    app = create_app()

    pid = DummyPID(0, dummy_output, "")

    # Test for actual agent
    with unittest.mock.patch("aea.cli_gui._call_aea_async", return_value=pid):
        response_list = app.get(
            'api/' + item_type,
            data=None,
            content_type='application/json',
        )
    assert response_list.status_code == 200
    data = json.loads(response_list.get_data(as_text=True))
    assert len(data) == 2
    assert data[0]['id'] == 'default'
    assert data[0]['description'] == 'The default item allows for any byte logic.'
    assert data[1]['id'] == 'oef'
    assert data[1]['description'] == 'The oef item implements the OEF specific logic.'


def _test_search_items_fail(item_type: str):
    """Test searching of generic items in registry failing."""
    app = create_app()

    pid = DummyPID(1, "", dummy_error)

    with unittest.mock.patch("aea.cli_gui._call_aea_async", return_value=pid):
        response_list = app.get(
            'api/' + item_type,
            data=None,
            content_type='application/json',
        )
    assert response_list.status_code == 400
    data = json.loads(response_list.get_data(as_text=True))

    assert data['detail'] == dummy_error + '\n'


def test_search_protocols():
    """Test for listing protocols supported by an agent."""
    _test_search_items('protocol')
    _test_search_items_fail('protocol')
    _test_search_items_with_query('protocol', 'test')


def test_search_connections():
    """Test for listing connections supported by an agent."""
    _test_search_items('connection')
    _test_search_items_fail('connection')
    _test_search_items_with_query('connection', 'test')


def test_list_skills():
    """Test for listing connections supported by an agent."""
    _test_search_items('skill')
    _test_search_items_fail('skill')
    _test_search_items_with_query('skill', 'test')


def test_real_search():
    """Call at least one function that actually calls call_aea_async."""
    app = create_app()

    # Test for actual agent
    response_list = app.get(
        'api/connection',
        data=None,
        content_type='application/json',
    )
    assert response_list.status_code == 200
    data = json.loads(response_list.get_data(as_text=True))
    assert len(data) == 6
    i = 0

    assert data[i]['id'] == 'gym'
    assert data[i]['description'] == 'The gym connection wraps an OpenAI gym.'
    i += 1
    assert data[i]['id'] == 'local'
    assert data[i]['description'] == 'The local connection provides a stub for an OEF node.'
    i += 1
    assert data[i]['id'] == 'oef'
    assert data[i]['description'] == 'The oef connection provides a wrapper around the OEF sdk.'
    i += 1
    assert data[i]['id'] == 'p2p'
    assert data[i]['description'] == 'The p2p connection provides a connection with the fetch.ai mail provider.'
    i += 1
    assert data[i]['id'] == 'stub'
    assert data[i]['description'] == 'The stub connection implements a connection stub which reads/writes messages from/to file.'
    i += 1
    assert data[i]['id'] == 'tcp'
    assert data[i]['description'] == 'The tcp connection implements a tcp server and client.'
