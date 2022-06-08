# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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

import pytest
import yaml
from aea_ledger_fetchai import FetchAICrypto
from pexpect.exceptions import EOF  # type: ignore

from aea.cli import cli
from aea.configurations.base import DEFAULT_AEA_CONFIG_FILE

from tests.common.pexpect_popen import PexpectWrapper
from tests.conftest import (
    AUTHOR,
    CLI_LOG_OPTION,
    CUR_PATH,
    CliRunner,
    MAX_FLAKY_RERUNS,
    MAX_FLAKY_RERUNS_ETH,
    ROOT_DIR,
)


logger = logging.getLogger(__name__)

DEFAULT_EXPECT_TIMEOUT = 40


class BaseLaunchTestCase:
    """Base Test case for launch tests."""

    PASSWORD: Optional[str] = None  # nosec

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
        password_options = self.get_password_args(self.PASSWORD)
        proc = PexpectWrapper(  # nosec
            [
                sys.executable,
                "-m",
                "aea.cli",
                "-v",
                "DEBUG",
                "launch",
                *password_options,
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

        method_list = [
            func
            for func in dir(cls)
            if callable(getattr(cls, func))
            and not func.startswith("__")
            and func.startswith("test_")
        ]
        if len(method_list) > 1:
            raise ValueError(f"{cls.__name__} can only contain one test method!")

        cls.runner = CliRunner()
        cls.agent_name_1 = "myagent_1"
        cls.agent_name_2 = "myagent_2"
        cls.cwd = os.getcwd()
        cls.t = tempfile.mkdtemp()
        dir_path = Path("packages")
        tmp_dir = cls.t / dir_path
        src_dir = cls.cwd / Path(ROOT_DIR, dir_path)
        shutil.copytree(str(src_dir), str(tmp_dir))
        os.chdir(cls.t)
        password_option = cls.get_password_args(cls.PASSWORD)
        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "init", "--local", "--author", AUTHOR],
        )
        assert result.exit_code == 0
        result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "create", "--local", cls.agent_name_1]
        )
        assert result.exit_code == 0
        os.chdir(cls.agent_name_1)
        result = cls.runner.invoke(
            cli,
            [
                *CLI_LOG_OPTION,
                "generate-key",
                FetchAICrypto.identifier,
                *password_option,
            ],
        )
        assert result.exit_code == 0

        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "add-key", FetchAICrypto.identifier, *password_option],
        )
        assert result.exit_code == 0
        os.chdir(cls.t)
        result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "create", "--local", cls.agent_name_2]
        )
        assert result.exit_code == 0
        os.chdir(cls.agent_name_2)
        result = cls.runner.invoke(
            cli,
            [
                *CLI_LOG_OPTION,
                "generate-key",
                FetchAICrypto.identifier,
                *password_option,
            ],
        )
        assert result.exit_code == 0

        result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "add-key", FetchAICrypto.identifier, *password_option],
        )
        assert result.exit_code == 0
        os.chdir(cls.t)

    @classmethod
    def get_password_args(cls, password: Optional[str]) -> List[str]:
        """Get password arguments."""
        return [] if password is None else ["--password", password]

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

    @pytest.mark.skip  # wrong ledger_id
    @pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS_ETH)
    def test_exit_code_equal_to_zero(self):
        """Assert that the exit code is equal to zero (i.e. success)."""
        with self._cli_launch([self.agent_name_1, self.agent_name_2]) as process_launch:
            process_launch.expect_all(
                [
                    f"[{self.agent_name_1}] Start processing messages...",
                    f"[{self.agent_name_2}] Start processing messages...",
                ],
                timeout=DEFAULT_EXPECT_TIMEOUT,
            )
            process_launch.control_c()
            process_launch.expect_all(
                ["Exit cli. code: 0"],
                timeout=DEFAULT_EXPECT_TIMEOUT,
            )


@pytest.mark.skip  # wrong ledger_id
class TestLaunchWithPassword(TestLaunch):
    """Test that the command 'aea launch <agent_name> --password <password>' works as expected."""

    PASSWORD = "fake-password"  # nosec


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

    @pytest.mark.skip  # wrong ledger_id
    @pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
    def test_exit_code_equal_to_one(self):
        """Assert that the exit code is equal to one (i.e. generic failure)."""
        with self._cli_launch([self.agent_name_1, self.agent_name_2]) as process_launch:
            process_launch.expect_all(
                [
                    f"[{self.agent_name_1}] Start processing messages...",
                    "Expected exception!",
                    "Receiving loop terminated",  # cause race condition in close/interrupt agent 2, so wait it closed by exception before call ctrl+c
                ],
                timeout=DEFAULT_EXPECT_TIMEOUT,
            )
            process_launch.control_c()
            process_launch.expect_all(
                [
                    f"Agent {self.agent_name_1} terminated with exit code 0",
                    f"Agent {self.agent_name_2} terminated with exit code ",
                ],
                timeout=DEFAULT_EXPECT_TIMEOUT,
            )
            process_launch.expect(
                EOF,
                timeout=DEFAULT_EXPECT_TIMEOUT,
            )
            process_launch.wait_to_complete(10)
            assert process_launch.returncode == 1


class TestLaunchWithWrongArguments(BaseLaunchTestCase):
    """Test aea launch when some agent directory does not exist."""

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        super().setup_class()
        cls.temp_agent = tempfile.mkdtemp()
        os.chdir(cls.temp_agent)

        cls.result = cls.runner.invoke(
            cli,
            [*CLI_LOG_OPTION, "launch", "this_agent_does_not_exist"],
            standalone_mode=True,
        )

    def test_exit_code_equal_to_one(self):
        """Assert that the exit code is equal to 1."""
        assert self.result.exit_code == 1

    @classmethod
    def teardown_class(cls):
        """Set the test up."""
        os.chdir(cls.t)
        try:
            shutil.rmtree(cls.temp_agent)
        except (OSError, IOError):
            pass
        super().teardown_class()


class TestLaunchMultithreaded(BaseLaunchTestCase):
    """Test that the command 'aea launch <agent_names> --multithreaded' works as expected."""

    @pytest.mark.skip  # wrong ledger_id
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
                timeout=DEFAULT_EXPECT_TIMEOUT,
            )
            process_launch.control_c()
            process_launch.expect_all(
                ["Exit cli. code: 0"],
                timeout=DEFAULT_EXPECT_TIMEOUT,
            )


class TestLaunchOneAgent(BaseLaunchTestCase):
    """Test that the command 'aea launch <agent_name>' works as expected."""

    @pytest.mark.skip  # wrong ledger_id
    def test_exit_code_equal_to_zero(self):
        """Assert that the exit code is equal to zero (i.e. success)."""
        with self._cli_launch([self.agent_name_1]) as process_launch:
            process_launch.expect_all(
                [f"[{self.agent_name_1}] Start processing messages..."],
                timeout=DEFAULT_EXPECT_TIMEOUT,
            )
            process_launch.control_c()
            process_launch.expect_all(
                [f"Agent {self.agent_name_1} terminated with exit code 0"],
                timeout=DEFAULT_EXPECT_TIMEOUT,
            )
            process_launch.wait_to_complete(10)

            assert process_launch.returncode == 0
