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
import inspect
from pathlib import Path
from queue import Queue
from types import SimpleNamespace
from typing import Optional, Tuple, Type, Union, cast

from aea.context.base import AgentContext
from aea.identity.base import Identity
from aea.mail.base import Address
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

    @staticmethod
    def message_has_attributes(
        actual_message: Message, message_type: Type[Message], **kwargs,
    ) -> Tuple[bool, str]:
        """
        Evaluates whether a message's attributes match the expected attributes provided.

        :param actual_message: the actual message
        :param message_type: the expected message type
        :param kwargs: other expected message attributes

        :return: boolean result of the evaluation and accompanied message
        """
        if type(actual_message) != message_type:
            return (
                False,
                "The message types do not match. Actual type: {}. Expected type: {}".format(
                    type(actual_message), message_type
                ),
            )

        for attribute_name, expected_value in kwargs.items():
            attribute = getattr(actual_message, attribute_name)
            if callable(attribute):
                if attribute != expected_value:
                    return (
                        False,
                        "The '{}' fields do not match. Actual '{}': {}. Expected '{}': {}".format(
                            attribute_name,
                            attribute_name,
                            attribute,
                            attribute_name,
                            expected_value,
                        ),
                    )

        return True, "The message has the provided expected attributes."

    def build_incoming_message(
        self,
        message_type: Type[Message],
        dialogue_reference: Optional[Tuple[str, str]] = None,
        message_id: Optional[int] = None,
        target: Optional[int] = None,
        performative: Optional[Message.Performative] = None,
        to: Optional[Address] = None,
        sender: Address = "counterparty",
        **kwargs,
    ) -> Message:
        """
        Quickly create an incoming message with the provided attributes.

        For any attribute not provided, the corresponding default value in message is used.

        :param message_type: the type of the message
        :param dialogue_reference: the dialogue_reference
        :param message_id: the message_id
        :param target: the target
        :param performative: the performative
        :param to: the 'to' address
        :param sender: the 'sender' address
        :param kwargs: other attributes

        :return: the created incoming message
        """
        d = dict()
        for arg_name in inspect.getfullargspec(self.build_incoming_message)[0][1:]:
            if (
                arg_name not in {"message_type", "to", "sender"}
                and locals()[arg_name] is not None
            ):
                d[arg_name] = locals()[arg_name]
        d.update(kwargs)

        incoming_message = message_type(**d)
        incoming_message.sender = sender
        incoming_message.to = (
            self.skill.skill_context.agent_address if to is None else to
        )

        return incoming_message

    @classmethod
    def setup(cls) -> None:
        """Set up the skill test case."""
        identity = Identity("test_agent_name", "test_agent_address")

        cls._multiplexer = AsyncMultiplexer()
        cls._multiplexer._out_queue = (  # pylint: disable=protected-access
            asyncio.Queue()
        )
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
