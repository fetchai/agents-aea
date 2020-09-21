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

import unittest.mock

from flask import Flask

import aea.cli_gui

from tests.common.mocks import ctx_mock_Popen
from tests.test_cli_gui.test_base import create_app


def test_home_page_exits():
    """Test that the home-page exits."""
    app = create_app()

    # sends HTTP GET request to the application
    # on the specified path
    result = app.get("/")

    # assert the status code of the response
    assert result.status_code == 200
    assert "AEA GUI" in str(result.data)


def test_icon():
    """Test that the home-page exits."""
    app = create_app()

    # sends HTTP GET request to the application
    # on the specified path
    result = app.get("/favicon.ico")

    # assert the status code of the response
    assert result.status_code == 200


def test_js():
    """Test that the home-page exits."""
    app = create_app()

    # sends HTTP GET request to the application
    # on the specified path
    result = app.get("/static/js/home.js")

    # assert the status code of the response
    assert result.status_code == 200


def test_run_app():
    """Test that running the app in non-test mode works."""
    with ctx_mock_Popen():
        with unittest.mock.patch.object(Flask, "run", return_value=None):
            aea.cli_gui.run(8080)
