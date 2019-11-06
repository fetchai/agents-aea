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
from typing import Optional, cast

from aea.agent import Agent
from aea.context.base import AgentContext
from aea.crypto.ledger_apis import LedgerApis
from aea.crypto.wallet import Wallet
from aea.decision_maker.base import DecisionMaker
from aea.mail.base import Envelope, MailBox
from aea.registries.base import Filter, Resources
from aea.skills.error.handlers import ErrorHandler

logger = logging.getLogger(__name__)


class AEA(Agent):
    """This class implements an autonomous economic agent."""

    def __init__(self, name: str,
                 mailbox: MailBox,
                 wallet: Wallet,
                 ledger_apis: LedgerApis,
                 resources: Resources,
                 timeout: float = 0.0,
                 debug: bool = False,
                 max_reactions: int = 20) -> None:
        """
        Instantiate the agent.

        :param name: the name of the agent
        :param mailbox: the mailbox of the agent.
        :param wallet: the wallet of the agent.
        :param ledger_apis: the ledger apis of the agent.
        :param resources: the resources of the agent.
        :param timeout: the time in (fractions of) seconds to time out an agent between act and react
        :param debug: if True, run the agent in debug mode.
        :param max_reactions: the processing rate of messages per iteration.

        :return: None
        """
        super().__init__(name=name, wallet=wallet, timeout=timeout, debug=debug)

        self.max_reactions = max_reactions

        self.mailbox = mailbox
        self._decision_maker = DecisionMaker(self.name,
                                             self.max_reactions,
                                             self.outbox,
                                             self.wallet,
                                             ledger_apis)
        self._context = AgentContext(self.name,
                                     self.wallet.public_keys,
                                     self.wallet.addresses,
                                     ledger_apis,
                                     self.outbox,
                                     self.decision_maker.message_in_queue,
                                     self.decision_maker.ownership_state,
                                     self.decision_maker.preferences,
                                     self.decision_maker.is_ready_to_pursuit_goals)
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

    def setup(self) -> None:
        """
        Set up the agent.

        :return: None
        """
        self.resources.load(self.context)
        self.resources.setup()

    def act(self) -> None:
        """
        Perform actions.

        :return: None
        """
        for behaviour in self.filter.get_active_behaviours():
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
        except Exception:
            error_handler.send_decoding_error(envelope)
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
            handler.handle(msg, envelope.sender)

    def update(self) -> None:
        """
        Update the current state of the agent.

        :return None
        """
        for task in self.filter.get_active_tasks():
            task.execute()
        self.decision_maker.execute()
        self.filter.handle_internal_messages()

    def teardown(self) -> None:
        """
        Tear down the agent.

        :return: None
        """
        if self._resources is not None:
            self._resources.teardown()
