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

"""This test module contains the integration test for the echo skill."""

from pathlib import Path

from aea.helpers import http_requests as requests
from aea.test_tools.test_cases import AEATestCaseEmpty

from tests.conftest import ROOT_DIR


API_SPEC_PATH = str(Path(ROOT_DIR, "examples", "http_ex", "petstore.yaml").absolute())


class TestHttpEchoSkill(AEATestCaseEmpty):
    """Test that http echo skill works."""

    capture_log = True

    def test_echo(self):
        """Run the echo skill sequence."""
        self.generate_private_key()
        self.add_private_key()
        self.add_item("connection", "fetchai/http_server:0.22.0")
        self.add_item("skill", "fetchai/http_echo:0.20.0")
        self.set_config("agent.default_connection", "fetchai/http_server:0.22.0")
        self.set_config(
            "vendor.fetchai.connections.http_server.config.target_skill_id",
            "fetchai/http_echo:0.20.0",
        )
        self.set_config(
            "vendor.fetchai.connections.http_server.config.api_spec_path", API_SPEC_PATH
        )
        self.run_install()

        process = self.run_agent()
        is_running = self.is_running(process)
        assert is_running, "AEA not running within timeout!"

        # add sending and receiving envelope from input/output files

        response = requests.get("http://127.0.0.1:8000")
        assert response.status_code == 404, "Failed to receive not found"
        # we receive a not found since the path is not available in the api spec

        response = requests.get("http://127.0.0.1:8000/pets")
        assert response.status_code == 200, "Failed to receive ok"
        assert (
            response.content == b'{"tom": {"type": "cat", "age": 10}}'
        ), "Wrong body on get"

        response = requests.post("http://127.0.0.1:8000/pets")
        assert response.status_code == 200
        assert response.content == b"", "Wrong body on post"

        check_strings = (
            "received http request with method=get, url=http://127.0.0.1:8000/pets and body=b''",
            "received http request with method=post, url=http://127.0.0.1:8000/pets and body=b''",
        )
        missing_strings = self.missing_from_output(process, check_strings)
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in agent output.".format(missing_strings)

        assert (
            self.is_successfully_terminated()
        ), "Http echo agent wasn't successfully terminated."
