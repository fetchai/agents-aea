# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 Valory AG
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
"""This test module contains AEA/AEABuilder wrapper to make performance tests easy."""

import uuid
from threading import Thread
from typing import Dict, List, Optional, Tuple, Type, Union

from aea.aea import AEA
from aea.aea_builder import AEABuilder
from aea.components.base import Component
from aea.configurations.base import SkillConfig
from aea.configurations.constants import _FETCHAI_IDENTIFIER
from aea.mail.base import Envelope
from aea.protocols.base import Message
from aea.skills.base import Handler, Skill, SkillContext
from benchmark.framework.fake_connection import FakeConnection

from packages.fetchai.protocols.default.message import DefaultMessage
from packages.fetchai.protocols.default.serialization import DefaultSerializer


class AEATestWrapper:
    """A testing wrapper to run and control an agent."""

    def __init__(
        self, name: str = "my_aea", components: Optional[List[Component]] = None
    ):
        """
        Make an agency with optional name and skills.

        :param name: name of the agent
        :param components: dict of components to add to agent
        """
        self.components = components or []
        self.name = name
        self._fake_connection: Optional[FakeConnection] = None

        self.aea = self.make_aea(self.name, self.components)
        self._thread = None  # type: Optional[Thread]

    def make_aea(
        self, name: Optional[str] = None, components: Optional[List[Component]] = None
    ) -> AEA:
        """
        Create AEA from name and already loaded components.

        :param name: name of the agent
        :param components: list of components to add to agent

        :return: AEA
        """
        components = components or []
        builder = AEABuilder()

        builder.set_name(name or self.name)

        builder.add_private_key(_FETCHAI_IDENTIFIER, private_key_path=None)

        for component in components:
            builder.add_component_instance(component)

        aea = builder.build()
        return aea

    @classmethod
    def make_skill(
        cls,
        config: Optional[SkillConfig] = None,
        context: Optional[SkillContext] = None,
        handlers: Optional[Dict[str, Type[Handler]]] = None,
    ) -> Skill:
        """
        Make a skill from optional config, context, handlers dict.

        :param config: SkillConfig
        :param context: SkillContext
        :param handlers: dict of handler types to add to skill

        :return: Skill
        """
        handlers = handlers or {}
        context = context or SkillContext()
        config = config or SkillConfig(
            name="skill_{}".format(uuid.uuid4().hex[0:5]), author="fetchai"
        )

        handlers_instances = {
            name: handler_cls(name=name, skill_context=context)
            for name, handler_cls in handlers.items()
        }

        skill = Skill(
            configuration=config, skill_context=context, handlers=handlers_instances
        )
        return skill

    @classmethod
    def dummy_default_message(
        cls,
        dialogue_reference: Tuple[str, str] = ("", ""),
        message_id: int = 1,
        target: int = 0,
        performative: DefaultMessage.Performative = DefaultMessage.Performative.BYTES,
        content: Union[str, bytes] = "hello world!",
    ) -> Message:
        """
        Construct simple message, all arguments are optional.

        :param dialogue_reference: the dialogue reference.
        :param message_id: the message id.
        :param target: the message target.
        :param performative: the message performative.
        :param content: string or bytes payload.

        :return: Message
        """
        if isinstance(content, str):
            content = content.encode("utf-8")

        return DefaultMessage(
            dialogue_reference=dialogue_reference,
            message_id=message_id,
            target=target,
            performative=performative,
            content=content,
        )

    @classmethod
    def dummy_envelope(
        cls,
        to: str = "test",
        sender: str = "test",
        message: Optional[Message] = None,
    ) -> Envelope:
        """
        Create envelope, if message is not passed use .dummy_message method.

        :param to: the address of the receiver.
        :param sender: the address of the sender.
        :param message: the protocol-specific message.

        :return: Envelope
        """
        message = message or cls.dummy_default_message()
        return Envelope(
            to=to,
            sender=sender,
            protocol_specification_id=DefaultMessage.protocol_specification_id,
            message=DefaultSerializer().encode(message),
        )

    def set_loop_timeout(self, period: float) -> None:
        """
        Set agent's loop timeout.

        :param period: idle sleep timeout for agent's loop
        """
        self.aea._period = period  # pylint: disable=protected-access

    def setup(self) -> None:
        """Set up agent: start multiplexer etc."""
        self.aea.setup()

    def stop(self) -> None:
        """Stop the agent."""
        self.aea.stop()

    def put_inbox(self, envelope: Envelope) -> None:
        """
        Add an envelope to agent's inbox.

        :param envelope: envelope to process by agent
        """
        self.aea.runtime.multiplexer.in_queue.put(envelope)

    def is_inbox_empty(self) -> bool:
        """
        Check there is no messages in inbox.

        :return: boolean indicating whether inbox is empty
        """
        return self.aea.runtime.multiplexer.in_queue.empty()

    def __enter__(self) -> None:
        """Context manager enter."""
        self.start_loop()

    def __exit__(  # type: ignore # pylint: disable=useless-return
        self, exc_type=None, exc=None, traceback=None
    ) -> None:
        """Context manager exit, stop agent."""
        self.stop_loop()
        return None

    def start_loop(self) -> None:
        """Start agents loop in dedicated thread."""
        self._thread = Thread(target=self.aea.start)
        self._thread.start()

    def stop_loop(self) -> None:
        """Stop agents loop in dedicated thread, close thread."""
        if self._thread is None:
            raise ValueError("Thread not set, call start_loop first.")
        self.aea.stop()
        self._thread.join()

    def is_running(self) -> bool:
        """
        Check is agent loop is set as running.

        :return: bool
        """
        return not self.aea.is_running

    def set_fake_connection(
        self, inbox_num: int, envelope: Optional[Envelope] = None
    ) -> None:
        """
        Add fake connection for testing.

        :param inbox_num: number of messages to generate by connection.
        :param envelope: envelope to generate. dummy one created by default.
        """
        if self._fake_connection:
            raise Exception("Fake connection is already set!")

        envelope = envelope or self.dummy_envelope()
        self._fake_connection = FakeConnection(
            envelope, inbox_num, connection_id="fake_connection"
        )
        self.aea.runtime.multiplexer.add_connection(self._fake_connection)

    def is_messages_in_fake_connection(self) -> bool:
        """
        Check fake connection has messages left.

        :return: bool
        """
        if not self._fake_connection:
            raise Exception("Fake connection is not set!")
        return self._fake_connection.num != 0  # type: ignore # cause fake connection is used.
