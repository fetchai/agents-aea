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
"""Code execution timeout tests."""
import os
import time
import unittest
from typing import Callable
from unittest.case import TestCase

import pytest

from aea.aea_builder import AEABuilder
from aea.configurations.base import SkillConfig
from aea.configurations.constants import DEFAULT_LEDGER
from aea.skills.base import Skill, SkillContext


from tests.common.utils import (
    AeaTool,
    make_behaviour_cls_from_funcion,
    make_handler_cls_from_funcion,
    timeit_context,
)

from .conftest import COSMOS_PRIVATE_KEY_PATH

if os.name == "nt":
    pytest.skip("signal.settimer non available on Windows.", allow_module_level=True)


def sleep_a_bit(sleep_time: float = 0.1, num_of_sleeps: int = 1) -> None:
    """Sleep num_of_sleeps time for sleep_time.

    :param sleep_time: time to sleep.
    :param  num_of_sleeps: how many time sleep for sleep_time.

    :return: None
    """
    for _ in range(num_of_sleeps):
        time.sleep(sleep_time)


class BaseTimeExecutionCase(TestCase):
    """Base Test case for code execute timeout."""

    BASE_TIMEOUT = 0.35

    @classmethod
    def setUpClass(cls) -> None:
        """Set up."""
        if cls is BaseTimeExecutionCase:
            raise unittest.SkipTest("Skip BaseTest tests, it's a base class")

    def tearDown(self) -> None:
        """Tear down."""
        self.aea_tool.stop()

    def prepare(self, function: Callable) -> None:
        """Prepare aea_tool for testing.

        :param function: function be called on react handle or/and Behaviour.act
        :return: None
        """
        agent_name = "MyAgent"

        builder = AEABuilder()
        builder.set_name(agent_name)
        builder.add_private_key(DEFAULT_LEDGER, COSMOS_PRIVATE_KEY_PATH)

        self.function_finished = False

        def handler_func(*args, **kwargs):
            function()
            self.function_finished = True

        skill_context = SkillContext()
        handler_cls = make_handler_cls_from_funcion(handler_func)

        behaviour_cls = make_behaviour_cls_from_funcion(handler_func)

        test_skill = Skill(
            SkillConfig(name="test_skill", author="fetchai"),
            skill_context=skill_context,
            handlers={
                "handler1": handler_cls(name="handler1", skill_context=skill_context)
            },
            behaviours={
                "behaviour1": behaviour_cls(
                    name="behaviour1", skill_context=skill_context
                )
            },
        )
        skill_context._skill = test_skill  # weird hack

        builder.add_component_instance(test_skill)
        aea = builder.build()

        self.aea_tool = AeaTool(aea)
        self.aea_tool.put_inbox(AeaTool.dummy_envelope())

    def test_long_handler_cancelled_by_timeout(self):
        """Test long function terminated by timeout."""
        num_sleeps = 10
        sleep_time = self.BASE_TIMEOUT
        function_sleep_time = num_sleeps * sleep_time
        execution_timeout = self.BASE_TIMEOUT * 2
        assert execution_timeout < function_sleep_time

        self.prepare(lambda: sleep_a_bit(sleep_time, num_sleeps))
        self.aea_tool.set_execution_timeout(execution_timeout)
        self.aea_tool.setup()

        with timeit_context() as timeit:
            self.aea_action()

        assert execution_timeout <= timeit.time_passed <= function_sleep_time
        assert not self.function_finished
        self.aea_tool.stop()

    def test_short_handler_not_cancelled_by_timeout(self):
        """Test short function NOTterminated by timeout."""
        num_sleeps = 1
        sleep_time = self.BASE_TIMEOUT
        function_sleep_time = num_sleeps * sleep_time
        execution_timeout = self.BASE_TIMEOUT * 2

        assert function_sleep_time <= execution_timeout

        self.prepare(lambda: sleep_a_bit(sleep_time, num_sleeps))
        self.aea_tool.set_execution_timeout(execution_timeout)
        self.aea_tool.setup()

        with timeit_context() as timeit:
            self.aea_action()

        assert function_sleep_time <= timeit.time_passed <= execution_timeout
        assert self.function_finished
        self.aea_tool.stop()

    def test_no_timeout(self):
        """Test function NOT terminated by timeout cause timeout == 0."""
        num_sleeps = 1
        sleep_time = self.BASE_TIMEOUT
        function_sleep_time = num_sleeps * sleep_time
        execution_timeout = 0

        self.prepare(lambda: sleep_a_bit(sleep_time, num_sleeps))
        self.aea_tool.set_execution_timeout(execution_timeout)
        self.aea_tool.setup()

        with timeit_context() as timeit:
            self.aea_action()

        assert function_sleep_time <= timeit.time_passed
        assert self.function_finished
        self.aea_tool.stop()


class HandleTimeoutExecutionCase(BaseTimeExecutionCase):
    """Test react timeout."""

    def aea_action(self):
        """Spin react on AEA."""
        self.aea_tool.react_one()


class ActTimeoutExecutionCase(BaseTimeExecutionCase):
    """Test act timeout."""

    def aea_action(self):
        """Spin act on AEA."""
        self.aea_tool.act_one()
