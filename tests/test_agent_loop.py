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
"""This module contains tests of the implementation of an agent loop using asyncio."""

from queue import Empty
from typing import Any, Callable, Dict, List, Optional, Sequence, Type
from unittest.mock import MagicMock

from aea.agent_loop import AsyncAgentLoop, BaseAgentLoop, SyncAgentLoop
from aea.helpers.async_friendly_queue import AsyncFriendlyQueue
from aea.mail.base import Envelope
from aea.protocols.base import Message
from aea.skills.base import Behaviour, Handler, SkillComponent, SkillContext
from aea.skills.behaviours import TickerBehaviour

from tests.common.utils import run_in_thread, wait_for_condition


class CountHandler(Handler):
    """Simple handler to count how many message it gets."""

    def setup(self) -> None:
        """Set up handler."""
        self.counter = 0

    def handle(self, message: Message) -> None:
        """Process incoming message."""
        self.counter += 1

    def teardown(self) -> None:
        """Clean up handler."""
        pass

    @classmethod
    def make(cls) -> "CountHandler":
        """Construct handler."""
        return cls(name="test", skill_context=SkillContext())


class CountBehaviour(TickerBehaviour):
    """Simple behaviour to count how many acts were called."""

    def setup(self) -> None:
        """Set up behaviour."""
        self.counter = 0

    def act(self) -> None:
        """Make an action."""
        self.counter += 1

    @classmethod
    def make(cls, tick_interval: int = 1) -> "CountBehaviour":
        """Construct behaviour."""
        return cls(
            name="test", skill_context=SkillContext(), tick_interval=tick_interval
        )


class AsyncFakeAgent:
    """Fake agent form testing."""

    name = "fake_agent"

    def __init__(self, handlers=None, behaviours=None):
        """Init agent."""
        self.handlers = handlers or []
        self.behaviours = behaviours or []
        self._inbox = AsyncFriendlyQueue()
        self.inbox = self._inbox
        self.filter = MagicMock()
        self.filter._process_internal_message = MagicMock()
        self.filter._handle_new_behaviours = MagicMock()
        self.decision_maker = MagicMock()

        self.decision_maker.message_out_queue = AsyncFriendlyQueue()
        self.timeout = 0.001

    @property
    def active_behaviours(self) -> List[Behaviour]:
        """Return all behaviours."""
        return self.behaviours

    def _handle(self, envelope: Envelope) -> None:
        """
        Handle an envelope.

        :param envelope: the envelope to handle.
        :return: None
        """
        for handler in self.handlers:
            handler.handle(envelope)

    def put_inbox(self, msg: Any) -> None:
        """Add a message to inbox."""
        self._inbox.put_nowait(msg)

    def put_internal_message(self, msg: Any) -> None:
        """Add a message to internal queue."""
        self.decision_maker.message_out_queue.put_nowait(msg)

    def act(self) -> None:
        """Call all acts of behaviours."""
        for behaviour in self.behaviours:
            behaviour.act_wrapper()

    def react(self) -> None:
        """Process one incoming message."""
        try:
            envelope = self.inbox.get_nowait()  # type: Optional[Envelope]
            if envelope is not None:
                self._handle(envelope)
        except Empty:
            pass

    def update(self) -> None:
        """Call internal messages handle and add behaviours handler."""
        self.filter._process_internal_message()
        self.filter._handle_new_behaviours()

    def _execution_control(
        self,
        fn: Callable,
        component: SkillComponent,
        args: Optional[Sequence] = None,
        kwargs: Optional[Dict] = None,
    ) -> Any:
        """
        Execute skill function in exception handling environment.

        Logs error, stop agent or propagate excepion depends on policy defined.

        :param fn: function to call
        :param component: skill component function belongs to
        :param args: optional sequence of arguments to pass to function on call
        :param kwargs: optional dict of keyword arguments to pass to function on call

        :return: same as function
        """
        return fn(*(args or []), **(kwargs or {}))


class SyncFakeAgent(AsyncFakeAgent):
    """Fake agent for sync loop."""

    def put_inbox(self, msg: Any) -> None:
        """Add a message to inbox."""
        self._inbox.put_nowait(msg)

    def put_internal_message(self, msg: Any) -> None:
        """Add a message to internal queue."""
        self.decision_maker.message_out_queue.put_nowait(msg)


class TestAsyncAgentLoop:
    """Tests for asynchronous loop."""

    AGENT_LOOP_CLASS: Type[BaseAgentLoop] = AsyncAgentLoop
    FAKE_AGENT_CLASS = AsyncFakeAgent

    def test_loop_start_stop(self):
        """Test loop start and stopped properly."""
        agent_loop = self.AGENT_LOOP_CLASS(self.FAKE_AGENT_CLASS())
        with run_in_thread(agent_loop.start):
            wait_for_condition(lambda: agent_loop.is_running, timeout=10)
            agent_loop.stop()

    def test_handle_envelope(self):
        """Test one envelope handling."""
        handler = CountHandler.make()
        agent = self.FAKE_AGENT_CLASS(handlers=[handler])
        agent_loop = self.AGENT_LOOP_CLASS(agent)

        handler.setup()
        with run_in_thread(agent_loop.start, timeout=10):
            wait_for_condition(lambda: agent_loop.is_running, timeout=10)
            agent.put_inbox("msg")
            wait_for_condition(lambda: handler.counter == 1, timeout=2)
            agent_loop.stop()

    def test_behaviour_act(self):
        """Test behaviour act called by schedule."""
        tick_interval = 0.1

        behaviour = CountBehaviour.make(tick_interval=tick_interval)
        behaviour.setup()
        agent = self.FAKE_AGENT_CLASS(behaviours=[behaviour])
        agent_loop = self.AGENT_LOOP_CLASS(agent)

        with run_in_thread(agent_loop.start, timeout=5):
            wait_for_condition(lambda: agent_loop.is_running, timeout=10)

            # test behaviour called
            wait_for_condition(
                lambda: behaviour.counter >= 1, timeout=tick_interval * 2
            )

            agent_loop.stop()

    def test_internal_messages(self):
        """Test internal meesages are processed."""
        agent = self.FAKE_AGENT_CLASS()
        agent_loop = self.AGENT_LOOP_CLASS(agent)

        with run_in_thread(agent_loop.start, timeout=5):
            wait_for_condition(lambda: agent_loop.is_running, timeout=10)
            agent.put_internal_message("msg")
            wait_for_condition(
                lambda: agent.filter._process_internal_message.called is True,
                timeout=5,
            )
            agent_loop.stop()

    def test_new_behaviours(self):
        """Test new behaviours are added."""
        agent = self.FAKE_AGENT_CLASS()
        agent_loop = self.AGENT_LOOP_CLASS(agent)
        agent_loop.NEW_BEHAVIOURS_PROCESS_SLEEP = 0.5

        with run_in_thread(agent_loop.start, timeout=5):
            wait_for_condition(lambda: agent_loop.is_running, timeout=10)
            wait_for_condition(
                lambda: agent.filter._handle_new_behaviours.call_count >= 2,
                timeout=agent_loop.NEW_BEHAVIOURS_PROCESS_SLEEP * 3,
            )
            agent_loop.stop()


class TestSyncAgentLoop(TestAsyncAgentLoop):
    """Tests for synchronous loop."""

    AGENT_LOOP_CLASS = SyncAgentLoop
    FAKE_AGENT_CLASS = SyncFakeAgent
