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
"""This module contains tests for aea launcher."""
import os
import shutil
import tempfile
import time
from multiprocessing import Event
from pathlib import Path
from threading import Thread


import pytest

import yaml

from aea.cli.core import cli
from aea.configurations.base import DEFAULT_AEA_CONFIG_FILE
from aea.helpers.base import cd
from aea.launcher import AEALauncher, _run_agent
from aea.test_tools.test_cases import CLI_LOG_OPTION


from tests.common.utils import wait_for_condition
from tests.conftest import AUTHOR, CUR_PATH, CliRunner


class TestThreadLauncherMode:
    """Test launcher in threaded mode."""

    RUNNER_MODE = "threaded"
    t: str = ""
    agent_name_1 = "myagent_1"
    agent_name_2 = "myagent_2"
    failing_agent = "failing_agent"

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        cls.runner = CliRunner()
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

        result = cls.runner.invoke(
            cli, [*CLI_LOG_OPTION, "create", "--local", cls.failing_agent]
        )
        assert result.exit_code == 0

        os.chdir(cls.failing_agent)
        shutil.copytree(
            Path(CUR_PATH, "data", "exception_skill"),
            Path(cls.t, cls.failing_agent, "skills", "exception"),
        )
        config_path = Path(cls.t, cls.failing_agent, DEFAULT_AEA_CONFIG_FILE)
        config = yaml.safe_load(open(config_path))
        config.setdefault("skills", []).append("fetchai/exception:0.1.0")
        yaml.safe_dump(config, open(config_path, "w"))
        os.chdir(cls.t)

        for agent_name in (cls.agent_name_1, cls.agent_name_2, cls.failing_agent):
            cls.set_runtime_mode_to_async(agent_name)

    @classmethod
    def set_runtime_mode_to_async(cls, agent_name: str) -> None:
        """Set runtime mode of the agent to async."""
        with cd(agent_name):
            config_path = Path(cls.t, agent_name, DEFAULT_AEA_CONFIG_FILE)
            config = yaml.safe_load(open(config_path))
            config.setdefault("runtime_mode", "async")
            yaml.safe_dump(config, open(config_path, "w"))

    @classmethod
    def teardown_class(cls):
        """Tear the test down."""
        os.chdir(cls.cwd)
        try:
            # shutil.rmtree(cls.t)
            pass
        except (OSError, IOError):
            pass

    def test_start_stop(self) -> None:
        """Test agents started stopped."""
        try:
            runner = AEALauncher(
                [self.agent_name_1, self.agent_name_2], self.RUNNER_MODE
            )
            runner.start(True)
            wait_for_condition(lambda: runner.is_running, timeout=5)
            assert runner.num_failed == 0
            time.sleep(1)
        finally:
            runner.stop()
            assert not runner.is_running
            assert runner.num_failed == 0

    def test_one_fails(self) -> None:
        """Test agents started, one agent failed, exception is raised."""
        try:
            runner = AEALauncher(
                [self.agent_name_1, self.agent_name_2, self.failing_agent],
                self.RUNNER_MODE,
            )

            with pytest.raises(Exception, match="Expected exception!"):
                runner.start()
            time.sleep(1)
        finally:
            runner.stop()

    def test_run_agent_in_thread(self):
        """Test agent started ans stopped in thread."""
        stop_event = Event()
        t = Thread(target=_run_agent, args=(self.agent_name_1, stop_event))
        t.start()
        stop_event.set()
        t.join(10)


class TestAsyncLauncherMode(TestThreadLauncherMode):
    """Test launcher in async mode."""

    RUNNER_MODE = "async"


class TestProcessLauncherMode(TestThreadLauncherMode):
    """Test launcher in process mode."""

    RUNNER_MODE = "multiprocess"
