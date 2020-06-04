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
from typing import Any, Callable, Dict, List, Optional, Sequence, Type, cast

from aea.agent import Agent
from aea.agent_loop import AsyncAgentLoop, BaseAgentLoop, SyncAgentLoop
from aea.configurations.constants import DEFAULT_SKILL
from aea.connections.base import Connection
from aea.context.base import AgentContext
from aea.crypto.ledger_apis import LedgerApis
from aea.crypto.wallet import Wallet
from aea.decision_maker.base import DecisionMaker, DecisionMakerHandler
from aea.decision_maker.default import (
    DecisionMakerHandler as DefaultDecisionMakerHandler,
)
from aea.exceptions import AEAException
from aea.helpers.exception_policy import ExceptionPolicyEnum
from aea.helpers.exec_timeout import ExecTimeoutThreadGuard, TimeoutException
from aea.identity.base import Identity
from aea.mail.base import Envelope
from aea.protocols.base import Message
from aea.protocols.default.message import DefaultMessage
from aea.registries.filter import Filter
from aea.registries.resources import Resources
from aea.skills.base import Behaviour, Handler, SkillComponent
from aea.skills.error.handlers import ErrorHandler
from aea.skills.tasks import TaskManager

logger = logging.getLogger(__name__)


class AEA(Agent):
    """This class implements an autonomous economic agent."""

    RUN_LOOPS: Dict[str, Type[BaseAgentLoop]] = {
        "sync": SyncAgentLoop,
        "async": AsyncAgentLoop,
    }
    DEFAULT_RUN_LOOP: str = "async"

    def __init__(
        self,
        identity: Identity,
        connections: List[Connection],
        wallet: Wallet,
        ledger_apis: LedgerApis,
        resources: Resources,
        loop: Optional[AbstractEventLoop] = None,
        timeout: float = 0.05,
        execution_timeout: float = 0,
        is_debug: bool = False,
        max_reactions: int = 20,
        decision_maker_handler_class: Type[
            DecisionMakerHandler
        ] = DefaultDecisionMakerHandler,
        skill_exception_policy: ExceptionPolicyEnum = ExceptionPolicyEnum.propagate,
        loop_mode: Optional[str] = None,
        runtime_mode: Optional[str] = None,
        **kwargs,
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
        :param exeution_timeout: amount of time to limit single act/handle to execute.
        :param is_debug: if True, run the agent in debug mode (does not connect the multiplexer).
        :param max_reactions: the processing rate of envelopes per tick (i.e. single loop).
        :param decision_maker_handler_class: the class implementing the decision maker handler to be used.
        :param skill_exception_policy: the skill exception policy enum
        :param loop_mode: loop_mode to choose agent run loop.
        :param kwargs: keyword arguments to be attached in the agent context namespace.

        :return: None
        """
        super().__init__(
            identity=identity,
            connections=connections,
            loop=loop,
            timeout=timeout,
            is_debug=is_debug,
            loop_mode=loop_mode,
            runtime_mode=runtime_mode,
        )

        self.max_reactions = max_reactions
        self._task_manager = TaskManager()
        decision_maker_handler = decision_maker_handler_class(
            identity=identity, wallet=wallet, ledger_apis=ledger_apis
        )
        self._decision_maker = DecisionMaker(
            decision_maker_handler=decision_maker_handler
        )
        self._context = AgentContext(
            self.identity,
            ledger_apis,
            self.multiplexer.connection_status,
            self.outbox,
            self.decision_maker.message_in_queue,
            decision_maker_handler.context,
            self.task_manager,
            **kwargs,
        )
        self._execution_timeout = execution_timeout
        self._resources = resources
        self._filter = Filter(self.resources, self.decision_maker.message_out_queue)

        self._skills_exception_policy = skill_exception_policy

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
        ExecTimeoutThreadGuard.start()

    def act(self) -> None:
        """
        Perform actions.

        Calls act() of each active behaviour.

        :return: None
        """
        for behaviour in self._get_active_behaviours():
            self._behaviour_act(behaviour)

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

    def _react_one(self) -> None:
        """
        Get and process one envelop from inbox.

        :return: None
        """
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
            msg.is_incoming = True
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
            self._handle_message_with_handler(msg, handler)

    def _handle_message_with_handler(self, message: Message, handler: Handler) -> None:
        """
        Handle one message with one predefined handler.

        :param message: message to be handled.
        :param handler: handler suitable for this message protocol.
        """
        self._execution_control(handler.handle, handler, [message])

    def _behaviour_act(self, behaviour: Behaviour) -> None:
        """
        Call behaviour's act.

        :param behaviour: behaviour already defined
        :return: None
        """
        self._execution_control(behaviour.act_wrapper, behaviour)

    def _execution_control(
        self,
        fn: Callable,
        component: SkillComponent,
        args: Optional[Sequence] = None,
        kwargs: Optional[Dict] = None,
    ) -> Any:
        """
        Execute skill function in exception handling environment.

        Logs error, stop agent or propagate excepion depends on policy defined.

        :param fn: function to call
        :param component: skill component function belongs to
        :param args: optional sequence of arguments to pass to function on call
        :param kwargs: optional dict of keyword arguments to pass to function on call

        :return: same as function
        """
        # docstyle: ignore
        def log_exception(e, fn, component):
            logger.exception(f"<{e}> raised during `{fn}` call of `{component}`")

        try:
            with ExecTimeoutThreadGuard(self._execution_timeout):
                return fn(*(args or []), **(kwargs or {}))
        except TimeoutException:
            logger.warning(
                "`{}` of `{}` was terminated as its execution exceeded the timeout of {} seconds. Please refactor your code!".format(
                    fn, component, self._execution_timeout
                )
            )
        except Exception as e:
            if self._skills_exception_policy == ExceptionPolicyEnum.propagate:
                raise
            elif self._skills_exception_policy == ExceptionPolicyEnum.just_log:
                log_exception(e, fn, component)
            elif self._skills_exception_policy == ExceptionPolicyEnum.stop_and_exit:
                log_exception(e, fn, component)
                self.stop()
                raise AEAException(
                    f"AEA was terminated cause exception `{e}` in skills {component} {fn}! Please check logs."
                )
            else:
                raise AEAException(
                    f"Unsupported exception policy: {self._skills_exception_policy}"
                )

    def _get_active_behaviours(self) -> List[Behaviour]:
        """Get all active behaviours to use in act."""
        return self._filter.get_active_behaviours()

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
        logger.debug("[{}]: Calling teardown method...".format(self.name))
        self.liveness.stop()
        self.decision_maker.stop()
        self.task_manager.stop()
        self.resources.teardown()
        ExecTimeoutThreadGuard.stop()
