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
"""This module contains test case classes based on pytest for AEA skill testing."""

import asyncio
from pathlib import Path
from queue import Queue
from types import SimpleNamespace
from typing import Optional, Union, cast

from aea.context.base import AgentContext
from aea.identity.base import Identity
from aea.multiplexer import AsyncMultiplexer, Multiplexer, OutBox
from aea.protocols.base import Message
from aea.skills.base import Skill
from aea.skills.tasks import TaskManager


class BaseSkillTestCase:
    """A class to test a skill."""

    path_to_skill: Union[Path, str] = Path(".")
    _skill: Skill
    _multiplexer: AsyncMultiplexer
    _outbox: OutBox

    @property
    def skill(self) -> Skill:
        """Get the skill."""
        try:
            value = self._skill
        except AttributeError:
            raise ValueError("Ensure skill is set during setup_class.")
        return value

    def get_quantity_in_outbox(self) -> int:
        """Get the quantity of envelopes in the outbox."""
        return self._multiplexer.out_queue.qsize()

    def get_message_from_outbox(self) -> Optional[Message]:
        """Get message from outbox."""
        if self._outbox.empty():
            return None
        envelope = self._multiplexer.out_queue.get_nowait()
        return envelope.message

    @classmethod
    def setup(cls) -> None:
        """Set up the skill test case."""
        identity = Identity("test_agent_name", "test_agent_address")

        cls._multiplexer = AsyncMultiplexer()
        cls._multiplexer._out_queue = asyncio.Queue()  # pylint: disable=protected-access
        cls._outbox = OutBox(cast(Multiplexer, cls._multiplexer))

        agent_context = AgentContext(
            identity=identity,
            connection_status=cls._multiplexer.connection_status,
            outbox=cls._outbox,
            decision_maker_message_queue=Queue(),
            decision_maker_handler_context=SimpleNamespace(),
            task_manager=TaskManager(),
            default_connection=None,
            default_routing={},
            search_service_address="dummy_search_service_address",
            decision_maker_address="dummy_decision_maker_address",
        )

        cls._skill = Skill.from_dir(str(cls.path_to_skill), agent_context)
