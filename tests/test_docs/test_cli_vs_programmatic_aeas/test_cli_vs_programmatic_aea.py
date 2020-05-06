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

from aea.test_tools.decorators import skip_test_ci
from aea.test_tools.test_cases import AEATestCaseMany, UseOef

from .programmatic_aea import run
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

    @skip_test_ci
    def test_cli_programmatic_communication(self, pytestconfig):
        """Test the communication of the two agents."""

        weather_station = "weather_station"
        self.fetch_agent("fetchai/weather_station:0.3.0", weather_station)
        self.set_agent_context(weather_station)
        self.set_config(
            "vendor.fetchai.skills.weather_station.models.strategy.args.is_ledger_tx",
            False,
            "bool",
        )

        weather_station_process = self.run_agent("--connections", "fetchai/oef:0.2.0")

        self.start_thread(target=run)

        check_strings = (
            "updating weather station services on OEF service directory.",
            "received CFP from sender=",
            "sending a PROPOSE with proposal=",
            "received ACCEPT from sender=",
            "sending MATCH_ACCEPT_W_INFORM to sender=",
            "received INFORM from sender=",
            "unregistering weather station services from OEF service directory.",
        )
        missing_strings = self.missing_from_output(
            weather_station_process, check_strings
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in weather_station output.".format(missing_strings)

        assert (
            self.is_successfully_terminated()
        ), "Agents weren't successfully terminated."
