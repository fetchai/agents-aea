# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021-2022 Valory AG
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
"""This module contains base classes for the ledger API connection."""
import asyncio
import inspect
from abc import ABC, abstractmethod
from asyncio import Task
from concurrent.futures._base import Executor
from logging import Logger
from typing import Any, Callable, Dict, Optional, Union

from aea.crypto.base import LedgerApi
from aea.crypto.registries import Registry, ledger_apis_registry
from aea.exceptions import enforce
from aea.helpers.async_utils import AsyncState
from aea.mail.base import Envelope
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue, Dialogues


class RequestDispatcher(ABC):
    """Base class for a request dispatcher."""

    def __init__(  # pylint: disable=too-many-arguments
        self,
        logger: Logger,
        connection_state: AsyncState,
        retry_attempts: int = 120,
        retry_timeout: int = 3,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        executor: Optional[Executor] = None,
        api_configs: Optional[Dict[str, Dict[str, str]]] = None,
    ):
        """
        Initialize the request dispatcher.

        :param retry_attempts: the retry attempts for any api used.
        :param retry_timeout: the retry timeout of any api used.
        :param logger: the logger.
        :param connection_state: connection state.
        :param loop: the asyncio loop.
        :param executor: an executor.
        :param api_configs: api configs.
        """
        self.connection_state = connection_state
        self.loop = loop if loop is not None else asyncio.get_event_loop()
        self.executor = executor
        self._api_configs = api_configs
        self.logger = logger
        self.retry_attempts = retry_attempts
        self.retry_timeout = retry_timeout

    def api_config(self, ledger_id: str) -> Dict[str, str]:
        """Get api config."""
        config = {}  # type: Dict[str, str]
        if self._api_configs is not None and ledger_id in self._api_configs:
            config = self._api_configs[ledger_id]
        return config

    async def run_async(
        self,
        func: Callable[[Any], Task],
        api: LedgerApi,
        message: Message,
        dialogue: Dialogue,
    ) -> Union[Message, Task]:
        """
        Run a function in executor.

        :param func: the function to execute.
        :param api: the ledger api.
        :param message: a Ledger API message.
        :param dialogue: a Ledger API dialogue.
        :return: the return value of the function.
        """
        try:
            if inspect.iscoroutinefunction(func):
                # If it is a coroutine, no need to run it in an executor
                # This can happen if the handler is async.
                task = func(api, message, dialogue)  # type: ignore
            else:
                task = self.loop.run_in_executor(  # type: ignore
                    self.executor, func, api, message, dialogue
                )
            response = await task
            return response
        except Exception as exception:  # pylint: disable=broad-except
            return self.get_error_message(exception, api, message, dialogue)

    async def wait_for(
        self, func: Callable, *args: Any, timeout: Optional[float] = None
    ) -> Any:
        """
        Runs a non-coroutine callable async while enforcing a timeout.

        Warning: This function can be used with non-coroutine callables ONLY!
        If you want the same functionality with coroutine callables, use asyncio.wait_for().

        :param func: the callable (function) to run.
        :param args: the function params.
        :param timeout: for how long to run the function before cancelling it and raising TimeoutError.
        :return: the return value of "func" if it finishes in "timeout", raises a TimeoutError otherwise.
        """
        enforce(
            not inspect.iscoroutinefunction(func),
            'A coroutine was passed to "RequestDispatcher.wait_for()", '
            '"RequestDispatcher.wait_for()" only works with non-coroutine callables. '
            'Hint: Look at "asyncio.wait_for()". ',
        )

        # we run the passed function using the default executor
        running_func = self.loop.run_in_executor(self.executor, func, *args)

        # func_result will carry the value the function returns
        func_result = await asyncio.wait_for(running_func, timeout=timeout)
        return func_result

    def dispatch(self, envelope: Envelope) -> Task:
        """
        Dispatch the request to the right sender handler.

        :param envelope: the envelope.
        :return: an awaitable.
        """
        if not isinstance(envelope.message, Message):  # pragma: nocover
            raise ValueError("Ledger connection expects non-serialized messages.")
        message = envelope.message
        ledger_id = self.get_ledger_id(message)
        api = self.ledger_api_registry.make(ledger_id, **self.api_config(ledger_id))
        dialogue = self.dialogues.update(message)
        if dialogue is None:
            raise ValueError(  # pragma: nocover
                f"No dialogue created. Message={message} not valid."
            )
        performative = message.performative
        handler = self.get_handler(performative)
        return self.loop.create_task(self.run_async(handler, api, message, dialogue))

    def get_handler(self, performative: Any) -> Callable[[Any], Task]:
        """
        Get the handler method, given the message performative.

        :param performative: the message performative.
        :return: the method that will send the request.
        """
        handler = getattr(self, performative.value, None)
        if handler is None:
            raise Exception("Performative not recognized.")  # pragma: nocover
        return handler

    @abstractmethod
    def get_error_message(
        self,
        exception: Exception,
        api: LedgerApi,
        message: Message,
        dialogue: Dialogue,
    ) -> Message:
        """
        Build an error message.

        :param exception: the exception
        :param api: the ledger api
        :param message: the received message.
        :param dialogue: the dialogue.
        :return: an error message response.
        """

    @property
    @abstractmethod
    def dialogues(self) -> Dialogues:
        """Get the dialogues."""

    @property
    def ledger_api_registry(self) -> Registry:
        """Get the registry."""
        return ledger_apis_registry

    @abstractmethod
    def get_ledger_id(self, message: Message) -> str:
        """Extract the ledger id from the message."""
