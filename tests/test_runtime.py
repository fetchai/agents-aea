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
"""This module contains tests for aea runtime."""
import os
from pathlib import Path
from typing import Type
from unittest.mock import patch

import pytest

from aea.aea_builder import AEABuilder
from aea.configurations.constants import DEFAULT_LEDGER, DEFAULT_PRIVATE_KEY_FILE
from aea.runtime import AsyncRuntime, BaseRuntime, RuntimeStates, ThreadedRuntime


from tests.common.utils import run_in_thread, wait_for_condition
from tests.conftest import CUR_PATH


class TestAsyncRuntime:
    """Test async runtime."""

    RUNTIME: Type[BaseRuntime] = AsyncRuntime

    def setup(self):
        """Set up case."""
        agent_name = "MyAgent"
        private_key_path = os.path.join(CUR_PATH, "data", DEFAULT_PRIVATE_KEY_FILE)
        builder = AEABuilder()
        builder.set_name(agent_name)
        builder.add_private_key(DEFAULT_LEDGER, private_key_path)
        builder.add_skill(Path(CUR_PATH, "data", "dummy_skill"))
        self.agent = builder.build()
        self.runtime = self.RUNTIME(self.agent)

    def test_start_stop(self):
        """Test runtime tart/stop."""
        with run_in_thread(self.runtime.start, timeout=20):
            wait_for_condition(lambda: self.runtime.is_running, timeout=20)
            self.runtime.stop()
            wait_for_condition(lambda: not self.runtime.is_running, timeout=20)

    def test_double_start(self):
        """Test runtime double start do nothing."""
        with patch.object(self.runtime, "_start", side_effect=ValueError("oops")):
            with pytest.raises(ValueError, match="oops"):
                self.runtime.start()

            self.runtime._state.set(RuntimeStates.running)
            self.runtime.start()

    def test_double_stop(self):
        """Test runtime double stop do nothing."""
        with patch.object(self.runtime, "_stop", side_effect=ValueError("oops")):
            self.runtime._state.set(RuntimeStates.running)
            with pytest.raises(ValueError, match="oops"):
                self.runtime.stop()

            self.runtime._state.set(RuntimeStates.stopped)
            self.runtime.stop()

    def test_error_state(self):
        """Test runtime fails on start."""
        with patch.object(
            self.runtime, "_start_agent_loop", side_effect=ValueError("oops")
        ):
            with pytest.raises(ValueError, match="oops"):
                self.runtime.start()

        assert self.runtime.state == RuntimeStates.error


class TestThreadedRuntime(TestAsyncRuntime):
    """Test threaded runtime."""

    RUNTIME = ThreadedRuntime

    def test_error_state(self):
        """Test runtime fails on start."""
        with patch.object(
            self.runtime.main_loop, "start", side_effect=ValueError("oops")
        ):
            with pytest.raises(ValueError, match="oops"):
                self.runtime.start()

        assert self.runtime.state == RuntimeStates.error

        self.runtime._stop()
