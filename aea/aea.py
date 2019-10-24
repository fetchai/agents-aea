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
from typing import Optional, cast

from aea.agent import Agent
from aea.context.base import AgentContext
from aea.crypto.wallet import Wallet
from aea.decision_maker.base import DecisionMaker
from aea.mail.base import Envelope, MailBox
from aea.registries.base import Resources
from aea.skills.error.handlers import ErrorHandler


logger = logging.getLogger(__name__)


class AEA(Agent):
    """This class implements an autonomous economic agent."""

    def __init__(self, name: str,
                 mailbox: MailBox,
                 wallet: Wallet,
                 timeout: float = 0.0,
                 debug: bool = False,
                 max_reactions: int = 20,
                 directory: str = '') -> None:
        """
        Instantiate the agent.

        :param name: the name of the agent
        :param mailbox: the mailbox of the agent.
        :param wallet: the wallet of the agent.
        :param timeout: the time in (fractions of) seconds to time out an agent between act and react
        :param debug: if True, run the agent in debug mode.
        :param max_reactions: the processing rate of messages per iteration.
        :param directory: the path to the agent's resource directory.
                        | If None, we assume the directory is in the working directory of the interpreter.

        :return: None
        """
        super().__init__(name=name, wallet=wallet, timeout=timeout, debug=debug)

        self.max_reactions = max_reactions
        self._directory = directory if directory else str(Path(".").absolute())

        self.mailbox = mailbox
        self._decision_maker = DecisionMaker(self.max_reactions, self.outbox, self.wallet)
        self._context = AgentContext(self.name,
                                     self.wallet.public_keys,
                                     self.wallet.addresses,
                                     self.outbox,
                                     self.decision_maker.message_queue,
                                     self.decision_maker.ownership_state,
                                     self.decision_maker.preferences,
                                     self.decision_maker.is_ready_to_pursuit_goals)
        self._resources = None  # type: Optional[Resources]

    @property
    def decision_maker(self) -> DecisionMaker:
        """Get decision maker."""
        return self._decision_maker

    @property
    def context(self) -> AgentContext:
        """Get context."""
        return self._context

    @property
    def resources(self) -> Resources:
        """Get resources."""
        assert self._resources is not None, "No resources initialized. Call setup."
        return self._resources

    def setup(self) -> None:
        """
        Set up the agent.

        :return: None
        """
        self._resources = Resources.from_resource_dir(self._directory, self.context)
        assert self._resources is not None, "No resources initialized. Error in setup."
        self._resources.setup()

    def act(self) -> None:
        """
        Perform actions.

        :return: None
        """
        for behaviour in self.resources.behaviour_registry.fetch_all():  # the skill should be able to register things here as active so we hand control fully to the skill and let this just spin through
            behaviour.act()

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

    def handle(self, envelope: Envelope) -> None:
        """
        Handle an envelope.

        :param envelope: the envelope to handle.
        :return: None
        """
        protocol = self.resources.protocol_registry.fetch(envelope.protocol_id)

        error_handler = self.resources.handler_registry.fetch_by_skill("default", "error")
        assert error_handler is not None, "ErrorHandler not initialized"
        error_handler = cast(ErrorHandler, error_handler)

        if protocol is None:
            error_handler.send_unsupported_protocol(envelope)
            return

        try:
            msg = protocol.serializer.decode(envelope.message)
        except Exception:
            error_handler.send_decoding_error(envelope)
            return

        if not protocol.check(msg):                         # pragma: no cover
            error_handler.send_invalid_message(envelope)    # pragma: no cover
            return                                          # pragma: no cover

        handlers = self.resources.handler_registry.fetch(protocol.id)
        if handlers is None:
            if error_handler is not None:
                error_handler.send_unsupported_skill(envelope)
            return

        # TODO: add filter, currently each handler independently acts on the message
        for handler in handlers:
            handler.handle(msg, envelope.sender)

    def update(self) -> None:
        """Update the current state of the agent.

        :return None
        """
        for task in self.resources.task_registry.fetch_all():
            task.execute()
        self.decision_maker.execute()

    def teardown(self) -> None:
        """
        Tear down the agent.

        :return: None
        """
        if self._resources is not None:
            self._resources.teardown()
