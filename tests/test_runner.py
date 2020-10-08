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
"""This module contains tests for aea runner."""
import time
from unittest.mock import call, patch

import pytest

from aea.aea_builder import AEABuilder
from aea.configurations.base import SkillConfig
from aea.configurations.constants import DEFAULT_LEDGER
from aea.helpers.multiple_executor import ExecutorExceptionPolicies
from aea.helpers.multiple_executor import _default_logger as executor_logger
from aea.runner import AEARunner
from aea.skills.base import Skill, SkillContext

from tests.common.utils import make_behaviour_cls_from_funcion, wait_for_condition
from tests.conftest import FETCHAI_PRIVATE_KEY_PATH


class TestThreadedRunner:
    """Test runner in threaded mode."""

    RUNNER_MODE = "threaded"

    def _builder(self, agent_name="agent1", act_func=None) -> AEABuilder:
        """Build an aea instance."""
        builder = AEABuilder()
        builder.set_name(agent_name)
        builder.add_private_key(DEFAULT_LEDGER, FETCHAI_PRIVATE_KEY_PATH)

        skill_context = SkillContext()
        act_func = act_func or (lambda self: self)
        behaviour_cls = make_behaviour_cls_from_funcion(act_func)

        behaviour = behaviour_cls(name="behaviour", skill_context=skill_context)
        test_skill = Skill(
            SkillConfig(name="test_skill", author="fetchai"),
            skill_context=skill_context,
            behaviours={"behaviour": behaviour},
        )
        skill_context._skill = test_skill  # weird hack
        builder.add_component_instance(test_skill)
        builder.set_runtime_mode("async")
        return builder

    def setup(self):
        """Set up aea instances."""
        self.aea1 = self._builder("agent1").build()
        self.aea2 = self._builder("agent2").build()
        self.failing_aea = self._builder(
            "failing_agent", act_func=self.raise_exception
        ).build()
        self.agents = [self.aea1, self.aea2]

    def raise_exception(self, *args, **kwargs):
        """Raise a test exception."""
        raise Exception("expected!")

    def test_start_stop(self):
        """Test agents started stopped."""
        runner = AEARunner([self.aea1, self.aea2], self.RUNNER_MODE)
        runner.start(True)
        wait_for_condition(lambda: runner.is_running, timeout=5)
        time.sleep(1)
        runner.stop()
        assert not runner.is_running

    def test_one_fails_propagate_policy(self) -> None:
        """Test agents started, one agent failed, exception is raised."""
        runner = AEARunner(
            [self.aea1, self.aea2, self.failing_aea],
            self.RUNNER_MODE,
            fail_policy=ExecutorExceptionPolicies.propagate,
        )

        with pytest.raises(Exception, match="expected!"):
            runner.start()
        runner.stop()

    def test_one_fails_log_only_policy(self) -> None:
        """Test agents started, one agent failed, exception is raised."""
        runner = AEARunner(
            [self.aea1, self.aea2, self.failing_aea],
            self.RUNNER_MODE,
            fail_policy=ExecutorExceptionPolicies.log_only,
        )
        with patch.object(executor_logger, "exception") as mock:
            runner.start(threaded=True)
            time.sleep(1)
        mock.assert_called_with(
            f"Exception raised during {self.failing_aea.name} running."
        )
        assert runner.is_running
        runner.stop()

    def test_one_fails_stop_policy(self) -> None:
        """Test agents started, one agent failed, exception is raised."""
        runner = AEARunner(
            [self.aea1, self.aea2, self.failing_aea],
            self.RUNNER_MODE,
            fail_policy=ExecutorExceptionPolicies.stop_all,
        )
        with patch.object(executor_logger, "exception") as mock:
            runner.start(threaded=True)
            time.sleep(1)
        mock.assert_has_calls(
            [call(f"Exception raised during {self.failing_aea.name} running.")]
        )
        assert not runner.is_running
        runner.stop()


class TestAsyncRunner(TestThreadedRunner):
    """Test runner in async mode."""

    RUNNER_MODE = "async"
