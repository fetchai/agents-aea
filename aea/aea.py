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
from asyncio import AbstractEventLoop
from concurrent.futures import Executor
from typing import Optional, cast, List

from aea.agent import Agent
from aea.connections.base import Connection
from aea.context.base import AgentContext
from aea.crypto.ledger_apis import LedgerApis
from aea.crypto.wallet import Wallet
from aea.decision_maker.base import DecisionMaker
from aea.mail.base import Envelope
from aea.registries.base import Filter, Resources
from aea.skills.error.handlers import ErrorHandler
from aea.skills.tasks import TaskManager

logger = logging.getLogger(__name__)


class AEA(Agent):
    """This class implements an autonomous economic agent."""

    def __init__(self, name: str,
                 connections: List[Connection],
                 wallet: Wallet,
                 ledger_apis: LedgerApis,
                 resources: Resources,
                 loop: Optional[AbstractEventLoop] = None,
                 timeout: float = 0.0,
                 debug: bool = False,
                 programmatic: bool = False,
                 max_reactions: int = 20,
                 executor: Optional[Executor] = None) -> None:
        """
        Instantiate the agent.

        :param name: the name of the agent
        :param connections: the list of connections of the agent.
        :param loop: the event loop to run the connections.
        :param wallet: the wallet of the agent.
        :param ledger_apis: the ledger apis of the agent.
        :param resources: the resources of the agent.
        :param timeout: the time in (fractions of) seconds to time out an agent between act and react
        :param debug: if True, run the agent in debug mode.
        :param programmatic: if True, run the agent in programmatic mode (skips loading of resources from directory).
        :param max_reactions: the processing rate of messages per iteration.
        :param executor: executor for asynchronous execution of tasks.

        :return: None
        """
        super().__init__(name=name, wallet=wallet, connections=connections, loop=loop, timeout=timeout, debug=debug, programmatic=programmatic)

        self.max_reactions = max_reactions
        self._task_manager = TaskManager(executor)
        self._decision_maker = DecisionMaker(self.name,
                                             self.max_reactions,
                                             self.outbox,
                                             self.wallet,
                                             ledger_apis)
        self._context = AgentContext(self.name,
                                     self.wallet.public_keys,
                                     self.wallet.addresses,
                                     ledger_apis,
                                     self.multiplexer.connection_status,
                                     self.outbox,
                                     self.decision_maker.message_in_queue,
                                     self.decision_maker.ownership_state,
                                     self.decision_maker.preferences,
                                     self.decision_maker.goal_pursuit_readiness,
                                     self.task_manager.task_queue)
        self._resources = resources
        self._filter = Filter(self.resources, self.decision_maker.message_out_queue)

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
        return self._resources

    @resources.setter
    def resources(self, resources: 'Resources'):
        """Set resources."""
        self._resources = resources

    @property
    def filter(self) -> Filter:
        """Get filter."""
        return self._filter

    @property
    def task_manager(self) -> TaskManager:
        """Get the task manager."""
        return self._task_manager

    def setup(self) -> None:
        """
        Set up the agent.

        :return: None
        """
        if not self.programmatic:
            self.resources.load(self.context)
        self.resources.setup()
        self.task_manager.start()

    def act(self) -> None:
        """
        Perform actions.

        :return: None
        """
        for behaviour in self.filter.get_active_behaviours():
            behaviour.act_wrapper()

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
                self._handle(envelope)

    def _handle(self, envelope: Envelope) -> None:
        """
        Handle an envelope.

        :param envelope: the envelope to handle.
        :return: None
        """
        logger.debug("Handling envelope: {}".format(envelope))
        protocol = self.resources.protocol_registry.fetch(envelope.protocol_id)

        error_handler = self.resources.handler_registry.fetch_by_skill("default", "error")
        assert error_handler is not None, "ErrorHandler not initialized"
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

        if not protocol.check(msg):                         # pragma: no cover
            error_handler.send_invalid_message(envelope)    # pragma: no cover
            return                                          # pragma: no cover

        handlers = self.filter.get_active_handlers(protocol.id)
        if handlers is None:
            if error_handler is not None:
                error_handler.send_unsupported_skill(envelope)
            return

        for handler in handlers:
            handler.handle(msg)

    def update(self) -> None:
        """
        Update the current state of the agent.

        :return None
        """
        # TODO: task should be submitted by the behaviours and handlers
        for task in self.filter.get_active_tasks():
            task.execute()
        self.decision_maker.execute()
        self.filter.handle_internal_messages()

    def teardown(self) -> None:
        """
        Tear down the agent.

        :return: None
        """
        self.task_manager.stop()
        if self._resources is not None:
            self._resources.teardown()
