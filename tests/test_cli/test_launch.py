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
"""This test module contains the tests for the `aea launch` sub-command."""

import logging
import os
import shutil
import sys
import tempfile
import unittest
from contextlib import contextmanager
from pathlib import Path
from typing import Generator, List, Optional

from pexpect.exceptions import EOF  # type: ignore

import pytest

import yaml

from aea.cli import cli
from aea.configurations.base import DEFAULT_AEA_CONFIG_FILE

from tests.common.pexpect_popen import PexpectWrapper
from tests.conftest import AUTHOR, CLI_LOG_OPTION, CUR_PATH, CliRunner, MAX_FLAKY_RERUNS

logger = logging.getLogger(__name__)


class BaseLaunchTestCase:
    """Base Test case for launch tests."""

    @contextmanager
    def _cli_launch(
        self, agents: List[str], options: Optional[List[str]] = None
    ) -> Generator:
        """
        Run aea.cli wrapped with Pexpect.

        :param agents: list of agent names to run
        :param options: list of string options to pass to aea launch.

        :return: PexpectWrapper
        """
        proc = PexpectWrapper(  # nosec
            [
                sys.executable,
                "-m",
                "aea.cli",
                "-v",
                "DEBUG",
                "launch",
                *(options or []),
                *(agents or []),
            ],
            env=os.environ,
            maxread=10000,
            encoding="utf-8",
            logfile=sys.stdout,
        )
        try:
            yield proc
        finally:
            proc.wait_to_complete(10)

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        if cls is BaseLaunchTestCase:
            raise unittest.SkipTest("Skip BaseTest tests, it's a base class")

        cls.runner = CliRunner()
        cls.agent_name_1 = "myagent_1"
        cls.agent_name_2 = "myagent_2"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)
        result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR]
        )
        assert result.exit_code == 0
        result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "create", "--local", cls.agent_name_1]
        )
        assert result.exit_code == 0
        result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "create", "--local", cls.agent_name_2]
        )
        assert result.exit_code == 0

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            shutil.rmtree(cls.t)
        except (OSError, IOError):
            pass


class TestLaunch(BaseLaunchTestCase):
    """Test that the command 'aea launch <agent_name>' works as expected."""

    def test_exit_code_equal_to_zero(self):
        """Assert that the exit code is equal to zero (i.e. success)."""
        with self._cli_launch([self.agent_name_1, self.agent_name_2]) as process_launch:
            process_launch.expect_all(
                [
                    f"[{self.agent_name_1}] Start processing messages...",
                    f"[{self.agent_name_2}] Start processing messages...",
                ],
                timeout=20,
            )
            process_launch.control_c()
            process_launch.expect_all(
                ["Exit cli. code: 0"], timeout=20,
            )


@pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
class TestLaunchWithOneFailingAgent(BaseLaunchTestCase):
    """Test aea launch when there is a failing agent.."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        super().setup_class()
        # add the exception skill to agent 2
        os.chdir(cls.agent_name_2)
        shutil.copytree(
            Path(CUR_PATH, "data", "exception_skill"),
            Path(cls.t, cls.agent_name_2, "skills", "exception"),
        )
        config_path = Path(cls.t, cls.agent_name_2, DEFAULT_AEA_CONFIG_FILE)
        config = yaml.safe_load(open(config_path))
        config.setdefault("skills", []).append("fetchai/exception:0.1.0")
        yaml.safe_dump(config, open(config_path, "w"))
        os.chdir(cls.t)

    def test_exit_code_equal_to_one(self):
        """Assert that the exit code is equal to one (i.e. generic failure)."""
        with self._cli_launch([self.agent_name_1, self.agent_name_2]) as process_launch:
            process_launch.expect_all(
                [
                    f"[{self.agent_name_1}] Start processing messages...",
                    "Expected exception!",
                    "Receiving loop terminated",  # cause race condition in close/interrupt agent 2, so wait it closed by exception before call ctrl+c
                ],
                timeout=20,
            )
            process_launch.control_c()
            process_launch.expect_all(
                [
                    f"Agent {self.agent_name_1} terminated with exit code 0",
                    f"Agent {self.agent_name_2} terminated with exit code ",
                ],
                timeout=20,
            )
            process_launch.expect(
                EOF, timeout=20,
            )
            process_launch.wait_to_complete(10)
            assert process_launch.returncode == 1


class TestLaunchWithWrongArguments(BaseLaunchTestCase):
    """Test aea launch when some agent directory does not exist."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        os.chdir(cls.t)

        cls.result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "launch", "this_agent_does_not_exist"],
            standalone_mode=True,
        )

    def test_exit_code_equal_to_one(self):
        """Assert that the exit code is equal to 1."""
        assert self.result.exit_code == 1


class TestLaunchMultithreaded(BaseLaunchTestCase):
    """Test that the command 'aea launch <agent_names> --multithreaded' works as expected."""

    def test_exit_code_equal_to_zero(self):
        """Assert that the exit code is equal to zero (i.e. success)."""
        with self._cli_launch(
            [self.agent_name_1, self.agent_name_2], ["--multithreaded"]
        ) as process_launch:
            process_launch.expect_all(
                [
                    f"[{self.agent_name_1}] Start processing messages",
                    f"[{self.agent_name_2}] Start processing messages",
                ],
                timeout=20,
            )
            process_launch.control_c()
            process_launch.expect_all(
                ["Exit cli. code: 0"], timeout=20,
            )


class TestLaunchOneAgent(BaseLaunchTestCase):
    """Test that the command 'aea launch <agent_name>' works as expected."""

    def test_exit_code_equal_to_zero(self):
        """Assert that the exit code is equal to zero (i.e. success)."""
        with self._cli_launch([self.agent_name_1]) as process_launch:
            process_launch.expect_all(
                [f"[{self.agent_name_1}] Start processing messages..."], timeout=20
            )
            process_launch.control_c()
            process_launch.expect_all(
                [f"Agent {self.agent_name_1} terminated with exit code 0"], timeout=20
            )
            process_launch.wait_to_complete(10)

            assert process_launch.returncode == 0
