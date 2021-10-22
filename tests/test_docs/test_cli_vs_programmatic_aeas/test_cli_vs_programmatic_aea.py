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
import shutil
from pathlib import Path
from random import uniform

import pytest
from aea_ledger_fetchai import FetchAICrypto

from aea.test_tools.test_cases import AEATestCaseManyFlaky

from packages.fetchai.connections.p2p_libp2p.connection import LIBP2P_SUCCESS_MESSAGE

from tests.conftest import (
    CUR_PATH,
    FETCHAI_PRIVATE_KEY_FILE,
    FETCHAI_PRIVATE_KEY_FILE_CONNECTION,
    MAX_FLAKY_RERUNS_INTEGRATION,
    NON_FUNDED_FETCHAI_PRIVATE_KEY_1,
    ROOT_DIR,
    wait_for_localhost_ports_to_close,
)
from tests.test_docs.helper import extract_code_blocks, extract_python_code


MD_FILE = "docs/cli-vs-programmatic-aeas.md"
PY_FILE = "test_docs/test_cli_vs_programmatic_aeas/programmatic_aea.py"
DEST = "programmatic_aea.py"


def test_read_md_file():
    """Compare the extracted code with the python file."""
    doc_path = os.path.join(ROOT_DIR, MD_FILE)
    code_blocks = extract_code_blocks(filepath=doc_path, filter_="python")
    test_code_path = os.path.join(CUR_PATH, PY_FILE)
    python_file = extract_python_code(test_code_path)
    assert code_blocks[-1] == python_file, "Files must be exactly the same."


class TestCliVsProgrammaticAEA(AEATestCaseManyFlaky):
    """This class contains the tests for the code-blocks in the build-aea-programmatically.md file."""

    capture_log: bool = True

    @pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS_INTEGRATION)
    @pytest.mark.integration
    def test_cli_programmatic_communication(self):
        """Test the communication of the two agents."""

        weather_station = "weather_station"
        self.fetch_agent("fetchai/weather_station:0.31.0", weather_station)
        self.set_agent_context(weather_station)
        self.set_config(
            "vendor.fetchai.skills.weather_station.models.strategy.args.is_ledger_tx",
            False,
            "bool",
        )
        self.run_install()

        # add non-funded key
        self.generate_private_key(FetchAICrypto.identifier)
        self.generate_private_key(
            FetchAICrypto.identifier, FETCHAI_PRIVATE_KEY_FILE_CONNECTION
        )
        self.add_private_key(FetchAICrypto.identifier, FETCHAI_PRIVATE_KEY_FILE)
        self.add_private_key(
            FetchAICrypto.identifier,
            FETCHAI_PRIVATE_KEY_FILE_CONNECTION,
            connection=True,
        )
        self.replace_private_key_in_file(
            NON_FUNDED_FETCHAI_PRIVATE_KEY_1, FETCHAI_PRIVATE_KEY_FILE_CONNECTION
        )
        # generate random location
        location = {
            "latitude": round(uniform(-90, 90), 2),  # nosec
            "longitude": round(uniform(-180, 180), 2),  # nosec
        }
        setting_path = (
            "vendor.fetchai.skills.weather_station.models.strategy.args.location"
        )
        self.nested_set_config(setting_path, location)

        self.run_cli_command("build", cwd=self._get_cwd())
        self.run_cli_command("issue-certificates", cwd=self._get_cwd())
        weather_station_process = self.run_agent()

        check_strings = (
            "Starting libp2p node...",
            "Connecting to libp2p node...",
            "Successfully connected to libp2p node!",
            LIBP2P_SUCCESS_MESSAGE,
        )
        missing_strings = self.missing_from_output(
            weather_station_process, check_strings, timeout=30, is_terminating=False
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in weather_station output.".format(missing_strings)

        src_file_path = os.path.join(ROOT_DIR, "tests", PY_FILE)
        dst_file_path = os.path.join(ROOT_DIR, self.t, DEST)
        shutil.copyfile(src_file_path, dst_file_path)
        self._inject_location(location, dst_file_path)
        weather_client_process = self.start_subprocess(DEST, cwd=self.t)

        check_strings = (
            "Starting libp2p node...",
            "Connecting to libp2p node...",
            "Successfully connected to libp2p node!",
            LIBP2P_SUCCESS_MESSAGE,
        )
        missing_strings = self.missing_from_output(
            weather_client_process, check_strings, timeout=30, is_terminating=False,
        )
        assert (
            missing_strings == []
        ), "Strings {} didn't appear in weather_client output.".format(missing_strings)

        check_strings = (
            "registering agent on SOEF.",
            "registering agent's service on the SOEF.",
            "registering agent's personality genus on the SOEF.",
            "registering agent's personality classification on the SOEF.",
            "received CFP from sender=",
            "sending a PROPOSE with proposal=",
            "received ACCEPT from sender=",
            "sending MATCH_ACCEPT_W_INFORM to sender=",
            "received INFORM from sender=",
            "transaction confirmed, sending data=",
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
            "received the following data=",
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
        wait_for_localhost_ports_to_close([9000, 9001])

    def _inject_location(self, location, dst_file_path):
        """Inject location into the weather client strategy."""
        file = Path(dst_file_path)
        lines = file.read_text().splitlines()
        target_line = "    strategy._is_ledger_tx = False"
        line_insertion_position = lines.index(target_line) + 1
        lines.insert(
            line_insertion_position,
            "    from packages.fetchai.skills.generic_buyer.strategy import Location",
        )
        lines.insert(
            line_insertion_position + 1,
            f"    strategy._agent_location = Location(latitude={location['latitude']}, longitude={location['longitude']})",
        )
        file.write_text("\n".join(lines))
