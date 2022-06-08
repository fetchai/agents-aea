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
"""This module contains base classes for the ledger API connection."""
import asyncio
from abc import ABC, abstractmethod
from asyncio import Task
from concurrent.futures._base import Executor
from logging import Logger
from typing import Any, Callable, Dict, Optional, Union

from aea.configurations.base import PublicId
from aea.crypto.base import LedgerApi
from aea.crypto.registries import Registry, ledger_apis_registry
from aea.helpers.async_utils import AsyncState
from aea.mail.base import Envelope
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue, Dialogues


CONNECTION_ID = PublicId.from_str("fetchai/ledger:0.19.0")


class RequestDispatcher(ABC):
    """Base class for a request dispatcher."""

    TIMEOUT = 3
    MAX_ATTEMPTS = 120

    def __init__(
        self,
        logger: Logger,
        connection_state: AsyncState,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        executor: Optional[Executor] = None,
        api_configs: Optional[Dict[str, Dict[str, str]]] = None,
    ):
        """
        Initialize the request dispatcher.

        :param logger: the logger.
        :param connection_state: the connection state.
        :param loop: the asyncio loop.
        :param executor: an executor.
        :param api_configs: the configurations of the api.
        """
        self.connection_state = connection_state
        self.loop = loop if loop is not None else asyncio.get_event_loop()
        self.executor = executor
        self._api_configs = api_configs
        self.logger = logger

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
        :param message: the message.
        :param dialogue: the dialogue.
        :return: the return value of the function.
        """
        try:
            response = await self.loop.run_in_executor(
                self.executor, func, api, message, dialogue
            )
            return response
        except Exception as e:  # pylint: disable=broad-except
            return self.get_error_message(e, api, message, dialogue)

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
                "No dialogue created. Message={} not valid.".format(message)
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
            raise Exception("Performative not recognized.")
        return handler

    @abstractmethod
    def get_error_message(
        self,
        e: Exception,
        api: LedgerApi,
        message: Message,
        dialogue: Dialogue,
    ) -> Message:
        """
        Build an error message.

        :param e: the exception
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
