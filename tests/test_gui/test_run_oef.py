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
# import json
# import time
from .test_base import create_app


def test_create_and_run_oef():
    """Test for running oef, reading TTY and errors."""
    pass
    # """Test for running oef, reading TTY and errors."""
    #
    # response_start = self.app.post(
    #     'api/oef',
    #     data=None,
    #     content_type='application/json',
    # )
    # assert response_start.status_code == 200
    #
    # # Wait for key message to appear
    # start_time = time.time()
    # oef_startup_timeout = 60
    # oef_started = False
    # while time.time() - start_time < oef_startup_timeout and not oef_started:
    #     response_status = self.app.get(
    #         'api/oef',
    #         data=None,
    #         content_type='application/json',
    #     )
    #     assert response_status.status_code == 200
    #     data = json.loads(response_status.get_data(as_text=True))
    #     assert "RUNNING" in data["status"]
    #     if "A thing of beauty is a joy forever" in data["tty"]:
    #         oef_started = True
    #     time.sleep(2)
    #
    # assert oef_started
