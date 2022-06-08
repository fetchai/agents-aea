# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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
import datetime
from asyncio import AbstractEventLoop
from logging import Logger
from multiprocessing.pool import AsyncResult
from typing import (
    Any,
    Callable,
    Collection,
    Dict,
    List,
    Optional,
    Sequence,
    Tuple,
    Type,
    cast,
)

from aea.agent import Agent
from aea.agent_loop import AsyncAgentLoop, BaseAgentLoop, SyncAgentLoop
from aea.configurations.base import PublicId
from aea.configurations.constants import (
    DEFAULT_BUILD_DIR_NAME,
    DEFAULT_SEARCH_SERVICE_ADDRESS,
)
from aea.context.base import AgentContext
from aea.crypto.ledger_apis import DEFAULT_CURRENCY_DENOMINATIONS
from aea.crypto.wallet import Wallet
from aea.decision_maker.base import DecisionMakerHandler
from aea.error_handler.base import AbstractErrorHandler
from aea.error_handler.default import ErrorHandler as DefaultErrorHandler
from aea.exceptions import AEAException, _StopRuntime
from aea.helpers.exception_policy import ExceptionPolicyEnum
from aea.helpers.logging import AgentLoggerAdapter, WithLogger, get_logger
from aea.identity.base import Identity
from aea.mail.base import Envelope
from aea.protocols.base import Message, Protocol
from aea.registries.filter import Filter
from aea.registries.resources import Resources
from aea.skills.base import Behaviour, Handler


class AEA(Agent):
    """This class implements an autonomous economic agent."""

    RUN_LOOPS: Dict[str, Type[BaseAgentLoop]] = {
        "async": AsyncAgentLoop,
        "sync": SyncAgentLoop,
    }
    DEFAULT_RUN_LOOP: str = "async"

    DEFAULT_BUILD_DIR_NAME = DEFAULT_BUILD_DIR_NAME

    def __init__(
        self,
        identity: Identity,
        wallet: Wallet,
        resources: Resources,
        data_dir: str,
        loop: Optional[AbstractEventLoop] = None,
        period: float = 0.05,
        execution_timeout: float = 0,
        max_reactions: int = 20,
        error_handler_class: Optional[Type[AbstractErrorHandler]] = None,
        error_handler_config: Optional[Dict[str, Any]] = None,
        decision_maker_handler_class: Optional[Type[DecisionMakerHandler]] = None,
        decision_maker_handler_config: Optional[Dict[str, Any]] = None,
        skill_exception_policy: ExceptionPolicyEnum = ExceptionPolicyEnum.propagate,
        connection_exception_policy: ExceptionPolicyEnum = ExceptionPolicyEnum.propagate,
        loop_mode: Optional[str] = None,
        runtime_mode: Optional[str] = None,
        default_ledger: Optional[str] = None,
        currency_denominations: Optional[Dict[str, str]] = None,
        default_connection: Optional[PublicId] = None,
        default_routing: Optional[Dict[PublicId, PublicId]] = None,
        connection_ids: Optional[Collection[PublicId]] = None,
        search_service_address: str = DEFAULT_SEARCH_SERVICE_ADDRESS,
        storage_uri: Optional[str] = None,
        task_manager_mode: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """
        Instantiate the agent.

        :param identity: the identity of the agent
        :param wallet: the wallet of the agent.
        :param resources: the resources (protocols and skills) of the agent.
        :param data_dir: directory where to put local files.
        :param loop: the event loop to run the connections.
        :param period: period to call agent's act
        :param execution_timeout: amount of time to limit single act/handle to execute.
        :param max_reactions: the processing rate of envelopes per tick (i.e. single loop).
        :param error_handler_class: the class implementing the error handler
        :param error_handler_config: the configuration of the error handler
        :param decision_maker_handler_class: the class implementing the decision maker handler to be used.
        :param decision_maker_handler_config: the configuration of the decision maker handler
        :param skill_exception_policy: the skill exception policy enum
        :param connection_exception_policy: the connection exception policy enum
        :param loop_mode: loop_mode to choose agent run loop.
        :param runtime_mode: runtime mode (async, threaded) to run AEA in.
        :param default_ledger: default ledger id
        :param currency_denominations: mapping from ledger id to currency denomination
        :param default_connection: public id to the default connection
        :param default_routing: dictionary for default routing.
        :param connection_ids: active connection ids. Default: consider all the ones in the resources.
        :param search_service_address: the address of the search service used.
        :param storage_uri: optional uri to set generic storage
        :param task_manager_mode: task manager mode (threaded) to run tasks with.
        :param kwargs: keyword arguments to be attached in the agent context namespace.
        """

        self._skills_exception_policy = skill_exception_policy
        self._connection_exception_policy = connection_exception_policy

        aea_logger = AgentLoggerAdapter(
            logger=get_logger(__name__, identity.name),
            agent_name=identity.name,
        )

        self._resources = resources
        super().__init__(
            identity=identity,
            connections=[],
            loop=loop,
            period=period,
            loop_mode=loop_mode,
            runtime_mode=runtime_mode,
            storage_uri=storage_uri,
            logger=cast(Logger, aea_logger),
            task_manager_mode=task_manager_mode,
        )

        default_routing = default_routing if default_routing is not None else {}
        connection_ids = connection_ids or []
        connections = [
            c
            for c in self.resources.get_all_connections()
            if (not connection_ids) or (c.connection_id in connection_ids)
        ]

        if not bool(self.resources.get_all_connections()):
            self.logger.warning(
                "Resource's connections list is empty! Instantiating AEA without connections..."
            )
        elif bool(self.resources.get_all_connections()) and not bool(connections):
            self.logger.warning(  # pragma: nocover
                "No connection left after filtering! Instantiating AEA without connections..."
            )

        self._set_runtime_and_mail_boxes(
            runtime_class=self._get_runtime_class(),
            loop_mode=loop_mode,
            loop=loop,
            multiplexer_options=dict(
                connections=connections,
                default_routing=default_routing,
                default_connection=default_connection,
                protocols=self.resources.get_all_protocols(),
            ),
        )

        self.max_reactions = max_reactions

        if decision_maker_handler_class is None:
            from aea.decision_maker.default import (  # isort:skip  # pylint: disable=import-outside-toplevel
                DecisionMakerHandler as DefaultDecisionMakerHandler,
            )

            decision_maker_handler_class = DefaultDecisionMakerHandler
        if decision_maker_handler_config is None:
            decision_maker_handler_config = {}
        decision_maker_handler = decision_maker_handler_class(
            identity=identity, wallet=wallet, config=decision_maker_handler_config
        )
        self.runtime.set_decision_maker(decision_maker_handler)

        if error_handler_class is None:
            error_handler_class = DefaultErrorHandler
        if error_handler_config is None:
            error_handler_config = {}
        self._error_handler = error_handler_class(**error_handler_config)
        default_ledger_id = (
            default_ledger
            if default_ledger is not None
            else identity.default_address_key
        )
        currency_denominations = (
            currency_denominations
            if currency_denominations is not None
            else DEFAULT_CURRENCY_DENOMINATIONS
        )
        self._context = AgentContext(
            self.identity,
            self.runtime.multiplexer.connection_status,
            self.outbox,
            self.runtime.decision_maker.message_in_queue,
            decision_maker_handler.context,
            self.runtime.task_manager,
            default_ledger_id,
            currency_denominations,
            default_connection,
            default_routing,
            search_service_address,
            decision_maker_handler.self_address,
            data_dir,
            storage_callable=lambda: self.runtime.storage,
            build_dir=self.get_build_dir(),
            send_to_skill=self.runtime.agent_loop.send_to_skill,
            **kwargs,
        )
        self._execution_timeout = execution_timeout
        self._filter = Filter(
            self.resources, self.runtime.decision_maker.message_out_queue
        )

        self._setup_loggers()

    @classmethod
    def get_build_dir(cls) -> str:
        """Get agent build directory."""
        return cls.DEFAULT_BUILD_DIR_NAME

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
    def filter(self) -> Filter:
        """Get the filter."""
        return self._filter

    @property
    def active_behaviours(self) -> List[Behaviour]:
        """Get all active behaviours to use in act."""
        return self.filter.get_active_behaviours()

    def setup(self) -> None:
        """
        Set up the agent.

        Calls setup() on the resources.
        """
        self.resources.setup()

    def act(self) -> None:
        """
        Perform actions.

        Adds new handlers and behaviours for use/execution by the runtime.
        """
        self.filter.handle_new_handlers_and_behaviours()

    def _get_error_handler(self) -> AbstractErrorHandler:
        """Get error handler."""
        return self._error_handler

    def _get_msg_and_handlers_for_envelope(
        self, envelope: Envelope
    ) -> Tuple[Optional[Message], List[Handler]]:
        """Get the msg and its handlers."""
        protocol = self.resources.get_protocol_by_specification_id(
            envelope.protocol_specification_id
        )

        error_handler = self._get_error_handler()

        if protocol is None:
            error_handler.send_unsupported_protocol(envelope, self.logger)
            return None, []

        msg, handlers = self._handle_decoding(envelope, protocol, error_handler)

        return msg, handlers

    def _handle_decoding(
        self,
        envelope: Envelope,
        protocol: Protocol,
        error_handler: AbstractErrorHandler,
    ) -> Tuple[Optional[Message], List[Handler]]:

        handlers = self.filter.get_active_handlers(
            protocol.public_id, envelope.to_as_public_id
        )

        if len(handlers) == 0:
            reason = (
                f"no active handler for protocol={protocol.public_id} in skill={envelope.to_as_public_id}"
                if envelope.is_component_to_component_message
                else f"no active handler for protocol={protocol.public_id}"
            )
            error_handler.send_no_active_handler(envelope, reason, self.logger)
            return None, []

        if isinstance(envelope.message, Message):
            msg = envelope.message
            return msg, handlers
        try:
            msg = protocol.serializer.decode(envelope.message)
            msg.sender = envelope.sender
            msg.to = envelope.to
            return msg, handlers
        except Exception as e:  # pylint: disable=broad-except  # thats ok, because we send the decoding error back
            error_handler.send_decoding_error(envelope, e, self.logger)
            return None, []

    def handle_envelope(self, envelope: Envelope) -> None:
        """
        Handle an envelope.

        Performs the following:

        - fetching the protocol referenced by the envelope, and
        - handling if the protocol is unsupported, using the error handler, or
        - handling if there is a decoding error, using the error handler, or
        - handling if no active handler is available for the specified protocol, using the error handler, or
        - handling the message recovered from the envelope with all active handlers for the specified protocol.

        :param envelope: the envelope to handle.
        :return: None
        """
        self.logger.debug("Handling envelope: {}".format(envelope))
        msg, handlers = self._get_msg_and_handlers_for_envelope(envelope)

        if msg is None:
            return

        for handler in handlers:
            handler.handle_wrapper(msg)

    def _setup_loggers(self) -> None:
        """Set up logger with agent name."""
        for element in [
            self.runtime.agent_loop,
            self.runtime.multiplexer,
            self.runtime.task_manager,
            self.resources.component_registry,
            self.resources.behaviour_registry,
            self.resources.handler_registry,
            self.resources.model_registry,
        ]:
            element = cast(WithLogger, element)
            element.logger = cast(
                Logger,
                AgentLoggerAdapter(element.logger, agent_name=self._identity.name),
            )

    def get_periodic_tasks(
        self,
    ) -> Dict[Callable, Tuple[float, Optional[datetime.datetime]]]:
        """
        Get all periodic tasks for agent.

        :return: dict of callable with period specified
        """
        tasks = super().get_periodic_tasks()
        tasks.update(self._get_behaviours_tasks())
        return tasks

    def _get_behaviours_tasks(
        self,
    ) -> Dict[Callable, Tuple[float, Optional[datetime.datetime]]]:
        """
        Get all periodic tasks for AEA behaviours.

        :return: dict of callable with period specified
        """
        tasks = {}

        for behaviour in self.active_behaviours:
            tasks[behaviour.act_wrapper] = (behaviour.tick_interval, behaviour.start_at)

        return tasks

    def get_message_handlers(self) -> List[Tuple[Callable[[Any], None], Callable]]:
        """
        Get handlers with message getters.

        :return: List of tuples of callables: handler and coroutine to get a message
        """
        return super().get_message_handlers() + [
            (
                self.filter.handle_internal_message,
                self.filter.get_internal_message,
            ),
            (self.handle_envelope, self.runtime.agent_loop.skill2skill_queue.get),
        ]

    def exception_handler(self, exception: Exception, function: Callable) -> bool:
        """
        Handle exception raised during agent main loop execution.

        :param exception: exception raised
        :param function: a callable exception raised in.

        :return: bool, propagate exception if True otherwise skip it.
        """
        # docstyle: ignore # noqa: E800
        def log_exception(e: Exception, fn: Callable, is_debug: bool = False) -> None:
            if is_debug:
                self.logger.debug(f"<{e}> raised during `{fn}`")
            else:
                self.logger.exception(f"<{e}> raised during `{fn}`")

        if self._skills_exception_policy == ExceptionPolicyEnum.propagate:
            log_exception(exception, function, is_debug=True)
            return True

        if self._skills_exception_policy == ExceptionPolicyEnum.stop_and_exit:
            log_exception(exception, function)
            raise _StopRuntime(
                AEAException(
                    f"AEA was terminated cause exception `{exception}` in skills {function}! Please check logs."
                )
            )

        if self._skills_exception_policy == ExceptionPolicyEnum.just_log:
            log_exception(exception, function)
            return False

        raise AEAException(
            f"Unsupported exception policy: {self._skills_exception_policy}"
        )

    def teardown(self) -> None:
        """
        Tear down the agent.

        Performs the following:

        - tears down the resources.
        """
        self.resources.teardown()

    def get_task_result(self, task_id: int) -> AsyncResult:
        """
        Get the result from a task.

        :param task_id: the id of the task
        :return: async result for task_id
        """
        return self.runtime.task_manager.get_task_result(task_id)

    def enqueue_task(
        self,
        func: Callable,
        args: Sequence = (),
        kwargs: Optional[Dict[str, Any]] = None,
    ) -> int:
        """
        Enqueue a task with the task manager.

        :param func: the callable instance to be enqueued
        :param args: the positional arguments to be passed to the function.
        :param kwargs: the keyword arguments to be passed to the function.
        :return: the task id to get the the result.
        """
        return self.runtime.task_manager.enqueue_task(func, args, kwargs)
