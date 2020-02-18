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

import io
import logging
import os
import signal
import subprocess  # nosec
import sys
import time
from pathlib import Path
from threading import Thread
from unittest import mock

import pytest

from aea.cli import cli

from .programmatic_aea import run, logger
from ..helper import extract_code_blocks
from ...common.click_testing import CliRunner
from ...conftest import (
    CLI_LOG_OPTION,
    CUR_PATH,
    ROOT_DIR,
)

MD_FILE = "docs/cli-vs-programmatic-aeas.md"
PY_FILE = "test_docs/test_cli_vs_programmatic_aeas/programmatic_aea.py"


def _read_tty(pid: subprocess.Popen):
    for line in io.TextIOWrapper(pid.stdout, encoding="utf-8"):
        print("stdout: " + line.replace("\n", ""))


def _read_error(pid: subprocess.Popen):
    for line in io.TextIOWrapper(pid.stderr, encoding="utf-8"):
        print("stderr: " + line.replace("\n", ""))


class TestProgrammaticAEA:
    """This class contains the tests for the code-blocks in the build-aea-programmatically.md file."""

    @classmethod
    def _patch_logger(cls):
        cls.patch_logger_warning = mock.patch.object(
            logger, "warning"
        )
        cls.mocked_logger_warning = cls.patch_logger_warning.__enter__()

    @classmethod
    def _unpatch_logger(cls):
        cls.mocked_logger_warning.__exit__()

    @classmethod
    def setup_class(cls):
        """Setup the test class."""
        cls.path = os.path.join(ROOT_DIR, MD_FILE)
        cls.code_blocks = extract_code_blocks(file=cls.path, filter="python")
        path = os.path.join(CUR_PATH, PY_FILE)
        with open(path, "r") as python_file:
            cls.read_python_file = python_file.read()
        cls.runner = CliRunner()
        cls._patch_logger()



    @pytest.fixture(autouse=True)
    def _start_oef_node(self, network_node):
        """Start an oef node."""

    def test_read_md_file(self):
        """Compare the extracted code with the python file."""
        assert (
            self.code_blocks[-1] == self.read_python_file
        ), "Files must be exactly the same."

    def test_cli_programmatic_communication(self):
        """Test the communication of the two agents."""

        patch_logger_info = mock.patch.object(logger, "info")
        mocked_logger_info = patch_logger_info.__enter__()

        result = self.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "fetch", "fetchai/weather_station:0.1.0"],
            standalone_mode=False,
        )
        assert result.exit_code == 0

        path = Path(os.getcwd(), "weather_station")
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
                "run",
                "--connections",
                "fetchai/oef:0.1.0",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=os.environ.copy(),
        )

        time.sleep(5.0)
        process_one.send_signal(signal.SIGINT)
        weather_station_thread = Thread(target=_read_tty, args=(process_one,))
        weather_station_thread.start()
        client_thread = Thread(target=_read_tty, args=(run,))
        client_thread.start()

        process_one.send_signal(signal.SIGINT)
        process_one.wait(timeout=60)

        assert process_one.returncode == 0
        poll_one = process_one.poll()
        if poll_one is None:
            process_one.terminate()
            process_one.wait(2)

        weather_station_thread.join()
        client_thread.join()

        mocked_logger_info.assert_called_with(
            "[weather_station]: received the following weather data={}"
        )

    @classmethod
    def teardown(cls):
        path = Path(ROOT_DIR, "weather_station")
        if os.path.exists(path):
            path = Path(ROOT_DIR)
            os.chdir(path)
            result = cls.runner.invoke(
                cli,
                [*CLI_LOG_OPTION, "delete", "weather_station"],
                standalone_mode=False,
            )
            assert result.exit_code == 0
        path = Path(ROOT_DIR, "fet_private_key.txt")
        if os.path.exists(path):
            os.remove(path)
