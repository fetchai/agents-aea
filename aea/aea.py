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

"""This module contains the implementation of an Autonomous Economic Agent."""
import base64
import logging
from abc import abstractmethod, ABC
from typing import List, Optional, Dict

from aea.agent import Agent
from aea.mail.base import Envelope, ProtocolId
from aea.protocols.base.protocol import Protocol
from aea.protocols.default.message import DefaultMessage
from aea.protocols.default.serialization import DefaultSerializer

logger = logging.getLogger(__name__)

SkillId = str


class Handler(ABC):
    """This class implements an abstract behaviour."""

    @abstractmethod
    def handle_envelope(self, envelope: Envelope) -> None:
        """
        Implement the reaction to an envelope.

        :param envelope: the envelope
        :return: None
        """

    @abstractmethod
    def teardown(self) -> None:
        """
        Implement the handler teardown.

        :return: None
        """


class Registry(ABC):
    """This class implements an abstract registry."""

    @abstractmethod
    def populate(self) -> None:
        """
        Load into the registry as specified in the config and apply consistency checks.

        :return: None
        """

    @abstractmethod
    def teardown(self) -> None:
        """
        Teardown the registry.

        :return: None
        """


class ProtocolRegistry(Registry):
    """This class implements the handlers registry."""

    def __init__(self) -> None:
        """
        Instantiate the registry.

        :return: None
        """
        self._protocols = []  # type: List[Protocol]

    def populate(self) -> None:
        """
        Load the handlers as specified in the config and apply consistency checks.

        :return: None
        """
        pass

    def fetch_protocol(self, envelope: Envelope) -> Optional[Protocol]:
        """
        Fetch the protocol for the envelope.

        :pass envelope: the envelope
        :return: the protocol id or None if the protocol is not registered
        """
        pass

    def teardown(self) -> None:
        """
        Teardown the registry.

        :return: None
        """
        self._protocols = []


class HandlerRegistry(Registry):
    """This class implements the handlers registry."""

    def __init__(self) -> None:
        """
        Instantiate the registry.

        :return: None
        """
        self._behaviours = {}  # type: Dict[SkillId, Handler]

    def populate(self) -> None:
        """
        Load the handlers as specified in the config and apply consistency checks.

        :return: None
        """
        pass

    def fetch_handler(self, protocol_id: ProtocolId) -> Optional[Handler]:
        """
        Fetch the handler for the protocol_id.

        :param protocol_id: the protocol id
        :return: the handler
        """
        pass

    def teardown(self) -> None:
        """
        Teardown the registry.

        :return: None
        """
        for handler in self._handlers:
            handler.teardown()
        self._handlers = {}


class AEA(Agent):
    """This class implements an autonomous economic agent."""

    def __init__(self, name: str,
                 private_key_pem_path: Optional[str] = None,
                 timeout: Optional[float] = 1.0,
                 debug: bool = False,
                 max_reactions: int = 20) -> None:
        """
        Instantiate the agent.

        :param name: the name of the agent
        :param private_key_pem_path: the path to the private key of the agent.
        :param timeout: the time in (fractions of) seconds to time out an agent between act and react
        :param debug: if True, run the agent in debug mode.
        :param max_reactions: the processing rate of messages per iteration.

        :return: None
        """
        super().__init__(name=name, private_key_pem_path=private_key_pem_path, timeout=timeout, debug=debug)

        self.max_reactions = max_reactions
        self._protocol_registry = ProtocolRegistry()
        self._handler_registry = HandlerRegistry()

    @property
    def protocol_registry(self) -> ProtocolRegistry:
        """Get the protocol registry."""
        return self._protocol_registry

    def setup(self) -> None:
        """
        Set up the agent.

        :return: None
        """
        self._protocol_registry.populate()
        self._handler_registry.populate()

    def act(self) -> None:
        """
        Perform actions.

        :return: None
        """
        # for behaviour in self._behaviour_registry.fetch_behaviours():
        #     behaviour.act()

    def react(self) -> None:
        """
        React to incoming events.

        :return: None
        """
        counter = 0
        while not self.inbox.empty() and counter < self.max_reactions:
            counter += 1
            envelope = self.inbox.get_nowait()  # type: Optional[Envelope]
            if envelope is not None:
                self.handle(envelope)

    def handle(self, envelope: Envelope) -> None:
        """Handle an envelope."""
        protocol = self._protocol_registry.fetch_protocol(envelope)

        if protocol is None:
            self.on_unsupported_protocol(envelope)
            return

        try:
            msg = protocol.serializer.decode(envelope.message)
        except Exception:
            self.on_decoding_error(envelope)
            return

        if not protocol.check(msg):
            self.on_invalid_message(envelope)
            return

        handler = self._handler_registry.fetch_handler(protocol.name)
        if handler is None:
            logger.warning("Cannot handle envelope: no handler registered for the protocol '{}'.".format(protocol.name))
            return

        handler.handle_envelope(envelope)

    def on_unsupported_protocol(self, envelope: Envelope):
        """Handle the received envelope in case the protocol is not supported."""
        logger.warning("Unsupported protocol: {}".format(envelope.protocol_id))
        reply = DefaultMessage(type=DefaultMessage.Type.ERROR,
                               error_code=DefaultMessage.ErrorCode.UNSUPPORTED_PROTOCOL,
                               error_msg="Unsupported protocol.",
                               error_data={"protocol_id": envelope.protocol_id})
        self.outbox.put_message(to=envelope.sender, sender=self.name, protocol_id=DefaultMessage.protocol_id,
                                message=DefaultSerializer().encode(reply))

    def on_decoding_error(self, envelope):
        """Handle a decoding error."""
        logger.warning("Decoding error: {}.".format(envelope))
        encoded_envelope = base64.b85encode(envelope.encode()).decode("utf-8")
        reply = DefaultMessage(type=DefaultMessage.Type.ERROR,
                               error_code=DefaultMessage.ErrorCode.DECODING_ERROR,
                               error_msg="Decoding error.",
                               error_data={"envelope": encoded_envelope})
        self.outbox.put_message(to=envelope.sender, sender=self.name, protocol_id=DefaultMessage.protocol_id,
                                message=DefaultSerializer().encode(reply))

    def on_invalid_message(self, envelope):
        """Handle an message that is invalid wrt a protocol.."""
        logger.warning("Invalid message wrt protocol: {}.".format(envelope.protocol_id))
        encoded_envelope = base64.b85encode(envelope.encode()).decode("utf-8")
        reply = DefaultMessage(type=DefaultMessage.Type.ERROR,
                               error_code=DefaultMessage.ErrorCode.INVALID_MESSAGE,
                               error_msg="Invalid message.",
                               error_data={"envelope": encoded_envelope})
        self.outbox.put_message(to=envelope.sender, sender=self.name, protocol_id=DefaultMessage.protocol_id,
                                message=DefaultSerializer().encode(reply))

    def update(self) -> None:
        """Update the current state of the agent.

        :return None
        """
        # for task in self._task_registry.fetch_tasks():
        #     task.execute()

    def teardown(self) -> None:
        """
        Tear down the agent.

        :return: None
        """
        self._protocol_registry.teardown()

