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

"""This module contains the tests for the code-blocks in the build-aea-programmatically.md file."""

import os

from aea.test_tools.test_cases import AEATestCaseMany, UseOef

from ..helper import extract_code_blocks, extract_python_code
from ...conftest import (
    CUR_PATH,
    ROOT_DIR,
)

MD_FILE = "docs/cli-vs-programmatic-aeas.md"
PY_FILE = "test_docs/test_cli_vs_programmatic_aeas/programmatic_aea.py"


class TestCliVsProgrammaticAEA(AEATestCaseMany, UseOef):
    """This class contains the tests for the code-blocks in the build-aea-programmatically.md file."""

    def test_read_md_file(self):
        """Compare the extracted code with the python file."""
        doc_path = os.path.join(ROOT_DIR, MD_FILE)
        code_blocks = extract_code_blocks(filepath=doc_path, filter="python")
        test_code_path = os.path.join(CUR_PATH, PY_FILE)
        python_file = extract_python_code(test_code_path)
        assert code_blocks[-1] == python_file, "Files must be exactly the same."

    def test_cli_programmatic_communication(self):
        """Test the communication of the two agents."""

        weather_station = "weather_station"
        self.fetch_agent("fetchai/weather_station:0.4.0", weather_station)
        self.set_agent_context(weather_station)
        self.set_config(
            "vendor.fetchai.skills.weather_station.models.strategy.args.is_ledger_tx",
            False,
            "bool",
        )
        self.run_install()
        weather_station_process = self.run_agent("--connections", "fetchai/oef:0.2.0")

        file_path = os.path.join("tests", PY_FILE)
        weather_client_process = self.start_subprocess(file_path, cwd=ROOT_DIR)

        check_strings = (
            "updating weather station services on OEF service directory.",
            "unregistering weather station services from OEF service directory.",
            "received CFP from sender=",
            "sending a PROPOSE with proposal=",
            "received ACCEPT from sender=",
            "sending MATCH_ACCEPT_W_INFORM to sender=",
            "received INFORM from sender=",
        )
        missing_strings = self.missing_from_output(
            weather_station_process, check_strings, timeout=120, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in weather_station output.".format(missing_strings)

        check_strings = (
            "found agents=",
            "sending CFP to agent=",
            "received proposal=",
            "accepting the proposal from sender=",
            "informing counterparty=",
            "received INFORM from sender=",
            "received the following weather data=",
        )
        missing_strings = self.missing_from_output(
            weather_client_process, check_strings, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in weather_client output.".format(missing_strings)

        self.terminate_agents(weather_client_process, weather_station_process)
        assert (
            self.is_successfully_terminated()
        ), "Agents weren't successfully terminated."
