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
import shutil
import time
from multiprocessing import Event
from pathlib import Path
from threading import Thread
from unittest.mock import patch

import pytest
import yaml

from aea.configurations.base import DEFAULT_AEA_CONFIG_FILE
from aea.launcher import AEADirMultiprocessTask, AEALauncher, _run_agent
from aea.test_tools.test_cases import AEATestCaseMany

from tests.common.utils import wait_for_condition
from tests.conftest import CUR_PATH


class TestThreadLauncherMode(AEATestCaseMany):
    """Test launcher in threaded mode."""

    RUNNER_MODE = "threaded"
    agent_name_1 = "myagent_1"
    agent_name_2 = "myagent_2"
    failing_agent = "failing_agent"

    @classmethod
    def setup_class(cls):
        """Set the test up."""
        super(AEATestCaseMany, cls).setup_class()
        cls.create_agents(cls.agent_name_1, cls.agent_name_2, cls.failing_agent)
        cls.set_agent_context(cls.failing_agent)
        shutil.copytree(
            Path(CUR_PATH, "data", "exception_skill"),
            Path(cls.t, cls.failing_agent, "skills", "exception"),
        )
        config_path = Path(cls.t, cls.failing_agent, DEFAULT_AEA_CONFIG_FILE)
        with open(config_path) as fp:
            config = yaml.safe_load(fp)
        config.setdefault("skills", []).append("fetchai/exception:0.1.0")
        yaml.safe_dump(config, open(config_path, "w"))
        cls.unset_agent_context()

        for agent_name in (cls.agent_name_1, cls.agent_name_2, cls.failing_agent):
            cls.set_agent_context(agent_name)
            cls.generate_private_key()
            cls.add_private_key()
            cls.set_runtime_mode_to_async(agent_name)
            cls.unset_agent_context()

    @classmethod
    def set_runtime_mode_to_async(cls, agent_name: str) -> None:
        """Set runtime mode of the agent to async."""
        config_path = Path(cls.t, agent_name, DEFAULT_AEA_CONFIG_FILE)
        with open(config_path) as fp:
            config = yaml.safe_load(fp)
        config.setdefault("runtime_mode", "async")
        with open(config_path, "w") as fp:
            yaml.safe_dump(config, fp)

    def test_start_stop(self, capfd, caplog) -> None:
        """Test agents started stopped."""
        try:
            runner = AEALauncher(
                [self.agent_name_1, self.agent_name_2],
                self.RUNNER_MODE,
                log_level="DEBUG",
            )
            runner.start(True)
            wait_for_condition(lambda: runner.is_running, timeout=10)

            capfd_out = ""

            def _check():
                nonlocal capfd_out  # to accumulate logs from capfd to chgck all the logs captured.
                capfd_out += capfd.readouterr().out
                log_text = capfd_out + "\n".join(caplog.messages)
                return (
                    f"[{self.agent_name_1}]: Runtime state changed to RuntimeStates.running."
                    in log_text
                    and f"[{self.agent_name_2}]: Runtime state changed to RuntimeStates.running."
                    in log_text
                )

            wait_for_condition(_check, timeout=10, period=0.1)
            assert runner.num_failed == 0
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
        finally:
            runner.stop()

    def test_run_agent_in_thread(self):
        """Test agent started and stopped in thread."""
        stop_event = Event()
        t = Thread(target=_run_agent, args=(self.agent_name_1, stop_event))
        t.start()
        time.sleep(1)
        stop_event.set()
        t.join()


class TestAsyncLauncherMode(TestThreadLauncherMode):
    """Test launcher in async mode."""

    RUNNER_MODE = "async"


class TestProcessLauncherMode(TestThreadLauncherMode):
    """Test launcher in process mode."""

    RUNNER_MODE = "multiprocess"


def test_task_stop():
    """Test AEADirMultiprocessTask.stop when not started."""
    task = AEADirMultiprocessTask("some")
    assert not task.failed
    with patch.object(task._stop_event, "set") as set_mock:
        task.stop()
        set_mock.assert_not_called()
