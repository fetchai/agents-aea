# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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
"""This module contains the tests for subprocess task manager/tasl_test_skill."""
from aea.test_tools.test_cases import AEATestCaseEmpty


class TestTaskTestSkill(AEATestCaseEmpty):
    """Test task manager subprocess run a simple task."""

    capture_log = True

    @classmethod
    def setup_class(cls) -> None:
        """Init the test case."""
        super(TestTaskTestSkill, cls).setup_class()
        cls.add_item("skill", "fetchai/task_test_skill:0.1.0", local=True)
        cls.generate_private_key()
        cls.add_private_key()
        cls.set_config("agent.task_manager_mode", "multiprocess", "str")

    def test_task_run_in_a_subprocess(self):
        """Test task run in a subporocess."""
        process = self.run_agent()
        try:
            is_running = self.is_running(process)
            assert is_running, "AEA not running within timeout!"
            assert not self.missing_from_output(
                process, ["Task id is"], 10, is_terminating=False
            )
            assert not self.missing_from_output(
                process, ["result is"], 10, is_terminating=False
            )
        finally:
            process.terminate()
            process.wait(10)
            print(self.stdout[process.pid])
            print(self.stderr[process.pid])
