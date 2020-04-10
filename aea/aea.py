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

"""This module contains the implementation of an autonomous economic agent (AEA)."""

import logging
from asyncio import AbstractEventLoop
from typing import List, Optional, cast

from aea.agent import Agent
from aea.configurations.constants import DEFAULT_SKILL
from aea.connections.base import Connection
from aea.context.base import AgentContext
from aea.crypto.ledger_apis import LedgerApis
from aea.crypto.wallet import Wallet
from aea.decision_maker.base import DecisionMaker
from aea.identity.base import Identity
from aea.mail.base import Envelope
from aea.protocols.default.message import DefaultMessage
from aea.registries.filter import Filter
from aea.registries.resources import Resources
from aea.skills.error.handlers import ErrorHandler
from aea.skills.tasks import TaskManager

logger = logging.getLogger(__name__)


class AEA(Agent):
    """This class implements an autonomous economic agent."""

    def __init__(
        self,
        identity: Identity,
        connections: List[Connection],
        wallet: Wallet,
        ledger_apis: LedgerApis,
        resources: Resources,
        loop: Optional[AbstractEventLoop] = None,
        timeout: float = 0.0,
        is_debug: bool = False,
        max_reactions: int = 20,
    ) -> None:
        """
        Instantiate the agent.

        :param identity: the identity of the agent
        :param connections: the list of connections of the agent.
        :param wallet: the wallet of the agent.
        :param ledger_apis: the APIs the agent will use to connect to ledgers.
        :param resources: the resources (protocols and skills) of the agent.
        :param loop: the event loop to run the connections.
        :param timeout: the time in (fractions of) seconds to time out an agent between act and react
        :param is_debug: if True, run the agent in debug mode (does not connect the multiplexer).
        :param max_reactions: the processing rate of envelopes per tick (i.e. single loop).

        :return: None
        """
        super().__init__(
            identity=identity,
            connections=connections,
            loop=loop,
            timeout=timeout,
            is_debug=is_debug,
        )

        self.max_reactions = max_reactions
        self._task_manager = TaskManager()
        self._decision_maker = DecisionMaker(identity, wallet, ledger_apis)
        self._context = AgentContext(
            self.identity,
            ledger_apis,
            self.multiplexer.connection_status,
            self.outbox,
            self.decision_maker.message_in_queue,
            self.decision_maker.ownership_state,
            self.decision_maker.preferences,
            self.decision_maker.goal_pursuit_readiness,
            self.task_manager,
        )
        self._resources = resources
        self._filter = Filter(self.resources, self.decision_maker.message_out_queue)

    @property
    def decision_maker(self) -> DecisionMaker:
        """Get decision maker."""
        return self._decision_maker

    @property
    def context(self) -> AgentContext:
        """Get (agent) context."""
        return self._context

    @property
    def resources(self) -> Resources:
        """Get resources."""
        return self._resources

    @resources.setter
    def resources(self, resources: "Resources") -> None:
        """Set resources."""
        self._resources = resources

    @property
    def task_manager(self) -> TaskManager:
        """Get the task manager."""
        return self._task_manager

    def setup(self) -> None:
        """
        Set up the agent.

        Performs the following:

        - loads the resources (unless in programmatic mode)
        - starts the task manager
        - starts the decision maker
        - calls setup() on the resources

        :return: None
        """
        self.task_manager.start()
        self.decision_maker.start()
        self.resources.setup()

    def act(self) -> None:
        """
        Perform actions.

        Calls act() of each active behaviour.

        :return: None
        """
        for behaviour in self._filter.get_active_behaviours():
            behaviour.act_wrapper()

    def react(self) -> None:
        """
        React to incoming envelopes.

        Gets up to max_reactions number of envelopes from the inbox and
        handles each envelope, which entailes:

        - fetching the protocol referenced by the envelope, and
        - returning an envelope to sender if the protocol is unsupported, using the error handler, or
        - returning an envelope to sender if there is a decoding error, using the error handler, or
        - returning an envelope to sender if no active handler is available for the specified protocol, using the error handler, or
        - handling the message recovered from the envelope with all active handlers for the specified protocol.

        :return: None
        """
        counter = 0
        while not self.inbox.empty() and counter < self.max_reactions:
            counter += 1
            self._react_one()

    def _react_one(self):
        """ get and process one envelop from inbox """
        envelope = self.inbox.get_nowait()  # type: Optional[Envelope]
        if envelope is not None:
            self._handle(envelope)

    def _handle(self, envelope: Envelope) -> None:
        """
        Handle an envelope.

        :param envelope: the envelope to handle.
        :return: None
        """
        logger.debug("Handling envelope: {}".format(envelope))
        protocol = self.resources.get_protocol(envelope.protocol_id)

        # TODO specify error handler in config and make this work for different skill/protocol versions.
        error_handler = self.resources.get_handler(
            DefaultMessage.protocol_id, DEFAULT_SKILL
        )

        if error_handler is None:
            logger.warning("ErrorHandler not initialized. Stopping AEA!")
            self.stop()
            return
        error_handler = cast(ErrorHandler, error_handler)

        if protocol is None:
            error_handler.send_unsupported_protocol(envelope)
            return

        try:
            msg = protocol.serializer.decode(envelope.message)
            msg.counterparty = envelope.sender
        except Exception as e:
            error_handler.send_decoding_error(envelope)
            logger.warning("Decoding error. Exception: {}".format(str(e)))
            return

        handlers = self._filter.get_active_handlers(
            protocol.public_id, envelope.skill_id
        )
        if len(handlers) == 0:
            error_handler.send_unsupported_skill(envelope)
            return

        for handler in handlers:
            handler.handle(msg)

    def update(self) -> None:
        """
        Update the current state of the agent.

        Handles the internal messages from the skills to the decision maker.

        :return None
        """
        self._filter.handle_internal_messages()

    def teardown(self) -> None:
        """
        Tear down the agent.

        Performs the following:

        - stops the decision maker
        - stops the task manager
        - tears down the resources.

        :return: None
        """
        self.decision_maker.stop()
        self.task_manager.stop()
        self.resources.teardown()
