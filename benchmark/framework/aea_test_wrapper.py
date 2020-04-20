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
"""This test module contains AEA/AEABuilder wrapper to make performance tests easy."""
from threading import Thread
from typing import Dict, List, Optional, Tuple, Type, Union

from benchmark.framework.fake_connection import FakeConnection

from aea.aea import AEA
from aea.aea_builder import AEABuilder
from aea.configurations.base import ProtocolId, SkillConfig
from aea.configurations.components import Component
from aea.crypto.fetchai import FETCHAI
from aea.mail.base import Envelope
from aea.protocols.base import Message
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer
from aea.skills.base import Handler, Skill, SkillContext


class AEATestWrapper:
    """A testing wrapper to run and control an agent."""

    def __init__(self, name: str = "my_aea", skills: List[dict] = None):
        """Make an agency with optional name and skills."""
        self.skills = skills or []
        self.name = name

        self.aea = self.make_aea(
            self.name, [self.make_skill(**skill) for skill in self.skills]
        )

    def make_aea(self, name: str = "my_eae", components: List[Component] = None) -> AEA:
        """
        Create AEA from name and already loaded components.

        :return: AEA
        """
        components = components or []
        builder = AEABuilder()

        builder.set_name(self.name)
        builder.add_private_key(FETCHAI, "")

        for component in components:
            builder._resources.add_component(component)

        aea = builder.build()
        return aea

    def make_skill(
        self,
        config: SkillConfig = None,
        context: SkillContext = None,
        handlers: Optional[Dict[str, Type[Handler]]] = None,
    ) -> Skill:
        """
        Make a skill from optional config, context, handlers dict.

        :return: Skill
        """
        handlers = handlers or {}
        context = context or SkillContext()
        config = config or SkillConfig()

        handlers_instances = {
            name: cls(name=name, skill_context=context)
            for name, cls in handlers.items()
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
        protocol_id: ProtocolId = DefaultMessage.protocol_id,
        message: Message = None,
    ) -> Envelope:
        """
        Create envelope, if message is not passed use .dummy_message method.

        :return: Envelope
        """
        message = message or cls.dummy_default_message()
        return Envelope(
            to=to,
            sender=sender,
            protocol_id=protocol_id,
            message=DefaultSerializer().encode(message),
        )

    def set_loop_timeout(self, timeout: float) -> None:
        """Set agent's loop timeout."""
        self.aea._timeout = timeout

    def setup(self) -> None:
        """Set up agent: start multiplexer etc."""
        self.aea._start_setup()

    def stop(self) -> None:
        """Stop the agent."""
        self.aea.stop()

    def put_inbox(self, envelope: Envelope) -> None:
        """Add an envelope to agent's inbox."""
        self.aea._multiplexer.in_queue.put(envelope)

    def is_inbox_empty(self) -> bool:
        """Check there is no messages in inbox."""
        return self.aea._multiplexer.in_queue.empty()

    def react(self) -> None:
        """One time process of react for incoming message."""
        self.aea.react()

    def spin_main_loop(self) -> None:
        """One time process agent's main loop."""
        self.aea._spin_main_loop()

    def __enter__(self) -> None:
        """Contenxt manager enter."""
        self.start_loop()

    def __exit__(self, exc_type=None, exc=None, traceback=None) -> None:
        """Context manager exit, stop agent."""
        self.stop_loop()
        return None

    def start_loop(self) -> None:
        """Start agents loop in dedicated thread."""
        self._thread = Thread(target=self.aea.start)
        self._thread.start()

    def stop_loop(self) -> None:
        """Stop agents loop in dedicated thread, close thread."""
        self.aea.stop()
        self._thread.join()

    def is_running(self) -> bool:
        """
        Check is agent loop is set as running.

        :return: bool
        """
        return not self.aea.liveness.is_stopped

    def set_fake_connection(self, inbox_num: int, envelope: Optional[Envelope] = None):
        """
        Replace first conenction with fake one.

        :param inbox_num: number of messages to generate by connection.
        :param envelope: envelope to generate. dummy one created by default.
        """
        envelope = envelope or self.dummy_envelope()
        self.aea._connections.clear()
        self.aea._connections.append(
            FakeConnection(envelope, inbox_num, connection_id="12")
        )

    def is_messages_in_fake_connection(self):
        """Check fake connection has messages left."""
        return self.aea._connections[0].num != 0
