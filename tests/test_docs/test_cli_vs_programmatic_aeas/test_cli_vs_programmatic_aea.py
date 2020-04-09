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
import signal
import subprocess  # nosec
import sys
import tempfile
import time
from threading import Thread

import pytest

from aea.cli import cli
from aea.test_tools.click_testing import CliRunner

from .programmatic_aea import run
from ..helper import extract_code_blocks, extract_python_code
from ...conftest import (
    CLI_LOG_OPTION,
    CUR_PATH,
    ROOT_DIR,
)

MD_FILE = "docs/cli-vs-programmatic-aeas.md"
PY_FILE = "test_docs/test_cli_vs_programmatic_aeas/programmatic_aea.py"


# TODO this test does not work properly...
class TestCliVsProgrammaticAEA:
    """This class contains the tests for the code-blocks in the build-aea-programmatically.md file."""

    @classmethod
    def setup_class(cls):
        """Setup the test class."""
        cls.path = os.path.join(ROOT_DIR, MD_FILE)
        cls.code_blocks = extract_code_blocks(filepath=cls.path, filter="python")
        path = os.path.join(CUR_PATH, PY_FILE)
        cls.python_file = extract_python_code(path)
        cls.runner = CliRunner()
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

    @pytest.fixture(autouse=True)
    def _start_oef_node(self, network_node):
        """Start an oef node."""

    def test_read_md_file(self):
        """Compare the extracted code with the python file."""
        assert (
            self.code_blocks[-1] == self.python_file
        ), "Files must be exactly the same."

    def test_cli_programmatic_communication(self, pytestconfig):
        """Test the communication of the two agents."""

        if pytestconfig.getoption("ci"):
            pytest.skip("Skipping the test since it doesn't work in CI.")

        packages_src = os.path.join(self.cwd, "packages")
        packages_dst = os.path.join(os.getcwd(), "packages")
        shutil.copytree(packages_src, packages_dst)

        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "fetch", "--local", "fetchai/weather_station:0.1.0"],
            standalone_mode=False,
        )
        assert result.exit_code == 0

        path = os.path.join(os.getcwd(), "weather_station")
        os.chdir(path)
        result = self.runner.invoke(
            cli,
            [
                *CLI_LOG_OPTION,
                "config",
                "set",
                "vendor.fetchai.skills.weather_station.models.strategy.args.is_ledger_tx",
                "False",
                "--type",
                "bool",
            ],
            standalone_mode=False,
        )
        assert result.exit_code == 0

        process_one = subprocess.Popen(  # nosec
            [
                sys.executable,
                "-m",
                "aea.cli",
                "--skip-consistency-check",
                "run",
                "--connections",
                "fetchai/oef:0.1.0",
            ],
            env=os.environ.copy(),
        )

        time.sleep(5.0)
        process_one.send_signal(signal.SIGINT)
        process_one.wait(timeout=20)

        assert process_one.returncode == 0

        client_thread = Thread(target=run)
        client_thread.start()
        poll_one = process_one.poll()
        if poll_one is None:
            process_one.terminate()
            process_one.wait(2)

        client_thread.join()

    @classmethod
    def teardown_class(cls):
        """Teardowm the test."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass
