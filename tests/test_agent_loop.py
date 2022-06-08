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
"""This module contains tests of the implementation of an agent loop using asyncio."""
import asyncio
import datetime
import logging
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple, Type
from unittest.mock import MagicMock, Mock, patch

import pytest

from aea.aea import AEA
from aea.agent_loop import AgentLoopStates, AsyncAgentLoop, BaseAgentLoop, SyncAgentLoop
from aea.exceptions import AEAActException
from aea.helpers.async_friendly_queue import AsyncFriendlyQueue
from aea.helpers.exception_policy import ExceptionPolicyEnum
from aea.mail.base import Envelope, EnvelopeContext
from aea.protocols.base import Message
from aea.registries.filter import Filter
from aea.registries.resources import Resources
from aea.skills.base import Behaviour, Handler, SkillContext
from aea.skills.behaviours import TickerBehaviour

from packages.fetchai.protocols.default.message import DefaultMessage

from tests.common.utils import wait_for_condition, wait_for_condition_async


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


class FailBehaviour(TickerBehaviour):
    """Simple behaviour to raise an exception."""

    def setup(self) -> None:
        """Set up behaviour."""
        pass

    def act(self) -> None:
        """Make an action."""
        raise ValueError("expected!")

    @classmethod
    def make(cls, tick_interval: int = 1) -> "FailBehaviour":
        """Construct behaviour."""
        return cls(name="test", skill_context=Mock(), tick_interval=tick_interval)


class AsyncFakeAgent(AEA):
    """Fake agent form testing."""

    name = "fake_agent"
    _skills_exception_policy = ExceptionPolicyEnum.just_log

    def __init__(self, handlers=None, behaviours=None):
        """Init agent."""
        self.handlers = handlers or []
        self.behaviours = behaviours or []
        self._runtime = MagicMock()
        self.runtime.decision_maker.message_out_queue = AsyncFriendlyQueue()
        self._inbox = AsyncFriendlyQueue()
        self._runtime.agent_loop.skill2skill_queue = asyncio.Queue()
        self._filter = Filter(
            Resources(), self.runtime.decision_maker.message_out_queue
        )
        self._logger = logging.getLogger("fake agent")
        self._period = 0.001
        self.filter.handle_internal_message = MagicMock()
        self.filter.handle_new_handlers_and_behaviours = MagicMock()

    def _get_behaviours_tasks(
        self,
    ) -> Dict[Callable, Tuple[float, Optional[datetime.datetime]]]:
        tasks = {}
        for behaviour in self.active_behaviours:
            tasks[behaviour.act_wrapper] = (behaviour.tick_interval, behaviour.start_at)
        return tasks

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
        self._inbox.put_nowait(msg)  # type: ignore

    def put_internal_message(self, msg: Any) -> None:
        """Add a message to internal queue."""
        self.runtime.decision_maker.message_out_queue.put_nowait(msg)

    def _get_msg_and_handlers_for_envelope(
        self, envelope: Envelope
    ) -> Tuple[Optional[Message], List[Handler]]:
        return envelope, self.handlers  # type: ignore

    def _execution_control(
        self,
        fn: Callable,
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

    def _handle_envelope(self, envelope: Envelope) -> None:
        for handler in self.handlers:
            handler.handle(envelope)


class SyncFakeAgent(AsyncFakeAgent):
    """Fake agent for sync loop."""

    def put_inbox(self, msg: Any) -> None:
        """Add a message to inbox."""
        self._inbox.put_nowait(msg)  # type: ignore

    def put_internal_message(self, msg: Any) -> None:
        """Add a message to internal queue."""
        self.runtime.decision_maker.message_out_queue.put_nowait(msg)


class TestAsyncAgentLoop:
    """Tests for asynchronous loop."""

    AGENT_LOOP_CLASS: Type[BaseAgentLoop] = AsyncAgentLoop
    FAKE_AGENT_CLASS = AsyncFakeAgent

    def test_loop_start_stop(self):
        """Test loop start and stopped properly."""
        agent = self.FAKE_AGENT_CLASS()
        agent_loop = self.AGENT_LOOP_CLASS(agent, threaded=True)
        agent.runtime.agent_loop = agent_loop
        agent_loop.start()
        wait_for_condition(lambda: agent_loop.is_running, timeout=10)
        agent_loop.stop()
        agent_loop.wait_completed(sync=True)
        assert not agent_loop.is_running, agent_loop.state

    def test_set_loop(self):
        """Test set loop."""
        agent_loop = self.AGENT_LOOP_CLASS(self.FAKE_AGENT_CLASS())

        loop = asyncio.new_event_loop()
        agent_loop.set_loop(loop=loop)
        assert agent_loop._loop == loop

    @pytest.mark.asyncio
    async def test_state_property(self):
        """Test state property."""
        agent_loop = self.AGENT_LOOP_CLASS(self.FAKE_AGENT_CLASS())

        assert agent_loop.state == AgentLoopStates.initial
        await asyncio.wait_for(
            agent_loop.wait_state(AgentLoopStates.initial), timeout=2
        )

    def test_handle_envelope(self):
        """Test one envelope handling."""
        handler = CountHandler.make()
        agent = self.FAKE_AGENT_CLASS(handlers=[handler])
        agent_loop = self.AGENT_LOOP_CLASS(agent, threaded=True)
        agent.runtime.agent_loop = agent_loop
        handler.setup()
        agent_loop.start()
        wait_for_condition(lambda: agent_loop.is_running, timeout=10)
        agent.put_inbox("msg")
        wait_for_condition(lambda: handler.counter == 1, timeout=2)
        agent_loop.stop()
        agent_loop.wait_completed(sync=True)

    def test_behaviour_act(self):
        """Test behaviour act called by schedule."""
        tick_interval = 0.1

        behaviour = CountBehaviour.make(tick_interval=tick_interval)
        behaviour.setup()
        agent = self.FAKE_AGENT_CLASS(behaviours=[behaviour])
        agent_loop = self.AGENT_LOOP_CLASS(agent, threaded=True)
        agent.runtime.agent_loop = agent_loop
        agent_loop.start()
        wait_for_condition(lambda: agent_loop.is_running, timeout=10)

        wait_for_condition(lambda: behaviour.counter >= 1, timeout=tick_interval * 2)
        agent_loop.stop()
        agent_loop.wait_completed(sync=True)

    @pytest.mark.asyncio
    async def test_internal_messages(self):
        """Test internal meesages are processed."""
        agent = self.FAKE_AGENT_CLASS()
        agent_loop = self.AGENT_LOOP_CLASS(agent)
        agent.runtime.agent_loop = agent_loop
        agent_loop.start()
        await asyncio.wait_for(
            agent_loop.wait_state(AgentLoopStates.started), timeout=10
        )
        agent.put_internal_message("msg")
        await wait_for_condition_async(
            lambda: agent.filter.handle_internal_message.called is True,
            timeout=5,
        )
        agent_loop.stop()
        await agent_loop.wait_completed()

    def test_new_behaviours(self):
        """Test new behaviours are added."""
        agent = self.FAKE_AGENT_CLASS()
        agent_loop = self.AGENT_LOOP_CLASS(agent, threaded=True)
        agent_loop.NEW_BEHAVIOURS_PROCESS_SLEEP = 0.5
        agent.runtime.agent_loop = agent_loop

        agent_loop.start()
        wait_for_condition(lambda: agent_loop.is_running, timeout=10)
        wait_for_condition(
            lambda: agent.filter.handle_new_handlers_and_behaviours.call_count >= 2,
            timeout=agent_loop.NEW_BEHAVIOURS_PROCESS_SLEEP * 3,
        )
        agent_loop.stop()
        agent_loop.wait_completed(sync=True)

    @pytest.mark.asyncio
    async def test_behaviour_exception(self):
        """Test behaviour exception reraised properly."""
        tick_interval = 0.1
        behaviour = FailBehaviour.make(tick_interval)
        agent = self.FAKE_AGENT_CLASS(behaviours=[behaviour])
        agent_loop = self.AGENT_LOOP_CLASS(agent, threaded=True)
        agent.runtime.agent_loop = agent_loop
        agent._skills_exception_policy = ExceptionPolicyEnum.propagate

        with pytest.raises(AEAActException):
            with pytest.raises(ValueError, match="expected!"):
                agent_loop.start()
                await agent_loop.wait_completed()

        agent_loop.stop()
        agent_loop.wait_completed(sync=True)

    @pytest.mark.asyncio
    async def test_stop(self):
        """Test loop stoped."""
        agent = self.FAKE_AGENT_CLASS()
        agent_loop = self.AGENT_LOOP_CLASS(agent)
        agent_loop.start()
        await asyncio.wait_for(
            agent_loop._state.wait(AgentLoopStates.started), timeout=10
        )
        agent_loop.stop()
        await asyncio.wait_for(
            agent_loop._state.wait(AgentLoopStates.stopped), timeout=10
        )

    @pytest.mark.asyncio
    async def test_send_to_skill(self):
        """Test loop stoped."""
        agent = self.FAKE_AGENT_CLASS()
        agent_loop = self.AGENT_LOOP_CLASS(agent)
        agent_loop.start()
        await asyncio.wait_for(
            agent_loop._state.wait(AgentLoopStates.started), timeout=10
        )

        msg = DefaultMessage(performative=DefaultMessage.Performative.BYTES)
        msg.to = "to"
        msg.sender = "sender"
        envelope = Envelope(
            to=msg.to,
            sender=msg.sender,
            message=msg,
            context=EnvelopeContext(connection_id="some_con"),
        )
        try:
            with pytest.raises(
                ValueError, match="Unsupported message or envelope type:"
            ):
                agent_loop.send_to_skill("something")

            with patch.object(agent_loop, "_skill2skill_message_queue"):
                agent_loop.send_to_skill(msg)
                agent_loop.send_to_skill(envelope)
        finally:
            agent_loop.stop()
            await asyncio.wait_for(
                agent_loop._state.wait(AgentLoopStates.stopped), timeout=10
            )


class TestSyncAgentLoop:
    """Tests for synchronous loop."""

    AGENT_LOOP_CLASS: Type[BaseAgentLoop] = SyncAgentLoop
    FAKE_AGENT_CLASS = SyncFakeAgent
