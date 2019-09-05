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
import logging
from pathlib import Path
from typing import Optional

from aea.agent import Agent
from aea.mail.base import Envelope
from aea.skills.base import Resources, Context

logger = logging.getLogger(__name__)


class AEA(Agent):
    """This class implements an autonomous economic agent."""

    def __init__(self, name: str,
                 private_key_pem_path: Optional[str] = None,
                 timeout: Optional[float] = 1.0,  # TODO we might want to set this to 0 for the aea and let the skills take care of slowing things down on a skill level
                 debug: bool = False,
                 max_reactions: int = 20,
                 directory: Optional[str] = None) -> None:
        """
        Instantiate the agent.

        :param name: the name of the agent
        :param private_key_pem_path: the path to the private key of the agent.
        :param timeout: the time in (fractions of) seconds to time out an agent between act and react
        :param debug: if True, run the agent in debug mode.
        :param max_reactions: the processing rate of messages per iteration.
        :param directory: the path to the agent's resource directory.
                        | If None, we assume the directory is in the working directory of the interpreter.

        :return: None
        """
        super().__init__(name=name, private_key_pem_path=private_key_pem_path, timeout=timeout, debug=debug)

        self.max_reactions = max_reactions
        self._directory = directory
        if self._directory is None:
            self._directory = str(Path(".").absolute())

        self.context = Context(self.name, self.outbox)
        self.resources = Resources(self.context)

    def setup(self) -> None:
        """
        Set up the agent.

        :return: None
        """
        self.resources.populate(self._directory)

    def act(self) -> None:
        """
        Perform actions.

        :return: None
        """
        for behaviour in self.resources.behaviour_registry.fetch_behaviours():  # the skill should be able to register things here as active so we hand control fully to the skill and let this just spin through
            behaviour.act()
        # NOTE: we must ensure that these are non-blocking.

    def react(self) -> None:
        """
        React to incoming events (envelopes).

        :return: None
        """
        counter = 0
        while not self.inbox.empty() and counter < self.max_reactions:
            counter += 1
            envelope = self.inbox.get_nowait()  # type: Optional[Envelope]
            if envelope is not None:
                self.handle(envelope)
        # Note: here things are processed sequentially, but on a skill level anything can be done (e.g. wait for several messages/ create templates etc.)
        # NOTE: we must ensure that these are non-blocking.

    def handle(self, envelope: Envelope) -> None:
        """
        Handle an envelope.

        :param envelope: the envelope to handle.
        :return: None
        """
        protocol = self.resources.protocol_registry.fetch_protocol(envelope.protocol_id)

        # fetch the handler of the "default" protocol for error handling. TODO: change with the handler of "error" protocol.
        default_handler = self.resources.handler_registry.fetch_handler("default")

        if protocol is None:
            if default_handler is not None:
                default_handler.send_unsupported_protocol(envelope)
            return

        try:
            msg = protocol.serializer.decode(envelope.message)
        except Exception:
            if default_handler is not None:
                default_handler.send_decoding_error(envelope)
            return

        if not protocol.check(msg):
            if default_handler is not None:
                default_handler.send_invalid_message(envelope)
            return

        handler = self.resources.handler_registry.fetch_handler(protocol.id)
        if handler is None:
            if default_handler is not None:
                default_handler.send_unsupported_skill(envelope, protocol)
            return

        handler.handle_envelope(envelope)

    def update(self) -> None:
        """Update the current state of the agent.

        :return None
        """
        for task in self.resources.task_registry.fetch_tasks():
            task.execute()

    def teardown(self) -> None:
        """
        Tear down the agent.

        :return: None
        """
        self.resources.teardown()
