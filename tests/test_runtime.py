# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021 Valory AG
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
import asyncio
import os
from pathlib import Path
from typing import Type
from unittest.mock import patch

import pytest

from aea.aea_builder import AEABuilder
from aea.configurations.base import ComponentType
from aea.configurations.constants import DEFAULT_LEDGER, DEFAULT_PRIVATE_KEY_FILE
from aea.exceptions import _StopRuntime
from aea.runtime import AsyncRuntime, BaseRuntime, RuntimeStates, ThreadedRuntime

from tests.common.utils import wait_for_condition
from tests.conftest import CUR_PATH, MAX_FLAKY_RERUNS, ROOT_DIR
from tests.data.dummy_skill import PUBLIC_ID as DUMMY_SKILL_PUBLIC_ID


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
        protocol = os.path.join(ROOT_DIR, "packages", "fetchai", "protocols", "default")
        builder.add_component(ComponentType.PROTOCOL, protocol)
        protocol = os.path.join(
            ROOT_DIR, "packages", "fetchai", "protocols", "state_update"
        )
        builder.add_component(ComponentType.PROTOCOL, protocol)
        builder.add_skill(Path(CUR_PATH, "data", "dummy_skill"))
        builder.set_storage_uri("sqlite://:memory:")
        self.agent = builder.build()

        self.runtime = self.RUNTIME(
            self.agent,
            threaded=True,
            multiplexer_options={
                "connections": self.agent.runtime.multiplexer.connections
            },
        )
        self.agent._runtime = self.runtime

    def teardown(self):
        """Tear down."""
        self.runtime.stop()
        self.runtime.wait_completed(sync=True)

    def test_start_stop(self):
        """Test runtime tart/stop."""
        self.runtime.start()
        wait_for_condition(lambda: self.runtime.is_running, timeout=20)
        self.runtime.stop()
        self.runtime.wait_completed(sync=True)

    @pytest.mark.flaky(reruns=MAX_FLAKY_RERUNS)
    @pytest.mark.asyncio
    async def test_stop_with_stopped_exception(self):
        """Test runtime stopped by stopruntime exception."""
        behaviour = self.agent.resources.get_behaviour(DUMMY_SKILL_PUBLIC_ID, "dummy")
        with patch.object(
            behaviour, "act", side_effect=_StopRuntime(reraise=ValueError("expected"))
        ):
            self.runtime.start()
            with pytest.raises(ValueError, match="expected"):
                self.runtime.wait_completed(timeout=20, sync=True)

    def test_double_start(self):
        """Test runtime double start do nothing."""
        assert self.runtime.start()
        assert not self.runtime.start()
        wait_for_condition(lambda: self.runtime.is_running, timeout=20)

    def test_set_loop(self):
        """Test set loop method."""
        loop = asyncio.new_event_loop()
        self.runtime.set_loop(loop)
        assert self.runtime.loop is loop

    def test_double_stop(self):
        """Test runtime double stop do nothing."""
        self.runtime.start()
        wait_for_condition(lambda: self.runtime.is_running, timeout=20)
        self.runtime.stop()
        self.runtime.wait_completed(sync=True)
        assert self.runtime.is_stopped

        self.runtime.stop()
        self.runtime.wait_completed(sync=True)
        assert self.runtime.is_stopped

    def test_error_state(self):
        """Test runtime fails on start."""

        async def error(*args, **kwargs):
            raise ValueError("oops")

        with patch.object(self.runtime, "_start_agent_loop", error):
            with pytest.raises(ValueError, match="oops"):
                self.runtime.start_and_wait_completed(sync=True)

        assert self.runtime.state == RuntimeStates.error, self.runtime.state


class TestThreadedRuntime(TestAsyncRuntime):
    """Test threaded runtime."""

    RUNTIME = ThreadedRuntime

    def test_error_state(self):
        """Test runtime fails on start."""
        with patch.object(
            self.runtime.agent_loop, "start", side_effect=ValueError("oops")
        ):
            with pytest.raises(ValueError, match="oops"):
                self.runtime.start_and_wait_completed(sync=True)

        assert self.runtime.state == RuntimeStates.error, self.runtime.state
