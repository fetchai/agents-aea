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
"""This module contains the tests for aea exception policies."""
import time
from threading import Thread
from unittest.mock import patch

import pytest

from aea.aea import logger
from aea.aea_builder import AEABuilder
from aea.configurations.constants import DEFAULT_LEDGER
from aea.exceptions import AEAException
from aea.helpers.exception_policy import ExceptionPolicyEnum
from aea.skills.base import Skill, SkillConfig, SkillContext

from tests.common.utils import (
    AeaTool,
    make_behaviour_cls_from_funcion,
    make_handler_cls_from_funcion,
)
from tests.conftest import COSMOS_PRIVATE_KEY_PATH


class ExpectedExcepton(Exception):
    """Exception for testing."""


class TestAeaExceptionPolicy:
    """Tests for exception policies."""

    @staticmethod
    def raise_exception(*args, **kwargs) -> None:
        """Raise exception for tests."""
        raise ExpectedExcepton("we wait it!")

    def setup(self) -> None:
        """Set test cae instance."""
        agent_name = "MyAgent"

        builder = AEABuilder()
        builder.set_name(agent_name)
        builder.add_private_key(DEFAULT_LEDGER, COSMOS_PRIVATE_KEY_PATH)

        self.handler_called = 0

        def handler_func(*args, **kwargs):
            self.handler_called += 1

        skill_context = SkillContext()
        handler_cls = make_handler_cls_from_funcion(handler_func)
        behaviour_cls = make_behaviour_cls_from_funcion(handler_func)

        self.handler = handler_cls(name="handler1", skill_context=skill_context)
        self.behaviour = behaviour_cls(name="behaviour1", skill_context=skill_context)

        test_skill = Skill(
            SkillConfig(name="test_skill", author="fetchai"),
            skill_context=skill_context,
            handlers={"handler": self.handler},
            behaviours={"behaviour": self.behaviour},
        )
        skill_context._skill = test_skill  # weird hack

        builder.add_component_instance(test_skill)
        self.aea = builder.build()
        self.aea_tool = AeaTool(self.aea)

    def test_no_exceptions(self) -> None:
        """Test act and handle works if no exception raised."""
        t = Thread(target=self.aea.start)
        t.start()

        self.aea_tool.put_inbox(self.aea_tool.dummy_envelope())
        time.sleep(1)
        assert self.handler_called >= 2

    def test_handle_propagate(self) -> None:
        """Test propagate policy on message handle."""
        self.aea._skills_exception_policy = ExceptionPolicyEnum.propagate
        self.handler.handle = self.raise_exception  # type: ignore # cause error: Cannot assign to a method
        self.aea_tool.put_inbox(self.aea_tool.dummy_envelope())

        with pytest.raises(ExpectedExcepton):
            self.aea.start()

        assert not self.aea.is_running

    def test_handle_stop_and_exit(self) -> None:
        """Test stop and exit policy on message handle."""
        self.aea._skills_exception_policy = ExceptionPolicyEnum.stop_and_exit
        self.handler.handle = self.raise_exception  # type: ignore # cause error: Cannot assign to a method
        self.aea_tool.put_inbox(self.aea_tool.dummy_envelope())

        with pytest.raises(
            AEAException, match=r"AEA was terminated cause exception .*"
        ):
            self.aea.start()

        assert not self.aea.is_running

    def test_handle_just_log(self) -> None:
        """Test just log policy on message handle."""
        self.aea._skills_exception_policy = ExceptionPolicyEnum.just_log
        self.handler.handle = self.raise_exception  # type: ignore # cause error: Cannot assign to a method

        with patch.object(logger, "exception") as patched:
            t = Thread(target=self.aea.start)
            t.start()

            self.aea_tool.put_inbox(self.aea_tool.dummy_envelope())
            self.aea_tool.put_inbox(self.aea_tool.dummy_envelope())
            time.sleep(1)
        assert self.aea.is_running
        assert patched.call_count == 2

    def test_act_propagate(self) -> None:
        """Test propagate policy on behaviour act."""
        self.aea._skills_exception_policy = ExceptionPolicyEnum.propagate
        self.behaviour.act = self.raise_exception  # type: ignore # cause error: Cannot assign to a method

        with pytest.raises(ExpectedExcepton):
            self.aea.start()

        assert not self.aea.is_running

    def test_act_stop_and_exit(self) -> None:
        """Test stop and exit policy on behaviour act."""
        self.aea._skills_exception_policy = ExceptionPolicyEnum.stop_and_exit
        self.behaviour.act = self.raise_exception  # type: ignore # cause error: Cannot assign to a method

        with pytest.raises(
            AEAException, match=r"AEA was terminated cause exception .*"
        ):
            self.aea.start()

        assert not self.aea.is_running

    def test_act_just_log(self) -> None:
        """Test just log policy on behaviour act."""
        self.aea._skills_exception_policy = ExceptionPolicyEnum.just_log
        self.behaviour.act = self.raise_exception  # type: ignore # cause error: Cannot assign to a method

        with patch.object(logger, "exception") as patched:
            t = Thread(target=self.aea.start)
            t.start()

            time.sleep(1)
        assert self.aea.is_running
        assert patched.call_count > 1

    def test_act_bad_policy(self) -> None:
        """Test propagate policy on behaviour act."""
        self.aea._skills_exception_policy = "non exists policy"  # type: ignore
        self.behaviour.act = self.raise_exception  # type: ignore # cause error: Cannot assign to a method

        with pytest.raises(AEAException, match=r"Unsupported exception policy.*"):
            self.aea.start()

        assert not self.aea.is_running

    def teardown(self) -> None:
        """Stop AEA if not stopped."""
        self.aea.stop()
