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
import time
import unittest.mock

from .test_base import DummyPID, create_app


def test_create_and_run_oef():
    """Test for running oef, reading TTY and errors."""
    app = create_app()

    pid = DummyPID(None, "A thing of beauty is a joy forever\n", "Testing Error\n")

    def _dummy_call_aea_async(param_list, dir_arg):
        assert param_list[0] == sys.executable
        assert "launch.py" in param_list[1]
        return pid

    with unittest.mock.patch("subprocess.call", return_value=None):
        with unittest.mock.patch("aea.cli_gui._call_aea_async", _dummy_call_aea_async):
            response_start = app.post(
                "api/oef", data=None, content_type="application/json",
            )
    assert response_start.status_code == 200

    # Wait for key message to appear
    start_time = time.time()
    # wait for a bit to ensure polling
    oef_startup_timeout = 60
    oef_started = False
    while time.time() - start_time < oef_startup_timeout and not oef_started:
        response_status = app.get(
            "api/oef", data=None, content_type="application/json",
        )
        assert response_status.status_code == 200
        data = json.loads(response_status.get_data(as_text=True))
        assert "RUNNING" in data["status"]
        if "A thing of beauty is a joy forever" in data["tty"]:
            assert "Testing Error" in data["error"]
            oef_started = True

    assert oef_started

    # get the status if failed
    pid.return_code = 1
    with unittest.mock.patch("aea.cli_gui._call_aea_async", _dummy_call_aea_async):
        response_status = app.get(
            "api/oef", data=None, content_type="application/json",
        )
    assert response_status.status_code == 200
    data = json.loads(response_status.get_data(as_text=True))
    assert "FAILED" in data["status"]

    # get the status if finished
    pid.return_code = 0
    with unittest.mock.patch("aea.cli_gui._call_aea_async", _dummy_call_aea_async):
        response_status = app.get(
            "api/oef", data=None, content_type="application/json",
        )
    assert response_status.status_code == 200
    data = json.loads(response_status.get_data(as_text=True))
    assert "FINISHED" in data["status"]

    # Stop the OEF Node
    with unittest.mock.patch("subprocess.call", return_value=None):
        response_stop = app.delete(
            "api/oef", data=None, content_type="application/json",
        )
    assert response_stop.status_code == 200

    # get the status
    pid.return_code = 0
    with unittest.mock.patch("aea.cli_gui._call_aea_async", _dummy_call_aea_async):
        response_status = app.get(
            "api/oef", data=None, content_type="application/json",
        )
    assert response_status.status_code == 200
    data = json.loads(response_status.get_data(as_text=True))
    assert "NOT_STARTED" in data["status"]


def test_create_and_run_oef_fail():
    """Test for running oef, reading TTY and errors."""
    app = create_app()

    def _dummy_call_aea_async(param_list, dir_arg):
        assert param_list[0] == sys.executable
        assert "launch.py" in param_list[1]
        return None

    with unittest.mock.patch("subprocess.call", return_value=None):
        with unittest.mock.patch("aea.cli_gui._call_aea_async", _dummy_call_aea_async):
            response_start = app.post(
                "api/oef", data=None, content_type="application/json",
            )
    assert response_start.status_code == 400
