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

"""This module contains base classes for the ledger API connection."""
import asyncio
from abc import ABC, abstractmethod
from asyncio import Task
from concurrent.futures._base import Executor
from typing import Any, Callable, Dict, Optional

from aea.configurations.base import PublicId
from aea.crypto.registries import Registry
from aea.helpers.dialogue.base import Dialogues
from aea.mail.base import Envelope
from aea.protocols.base import Message


CONNECTION_ID = PublicId.from_str("fetchai/ledger_api:0.1.0")


class RequestDispatcher(ABC):
    """Base class for a request dispatcher."""

    TIMEOUT = 3
    MAX_ATTEMPTS = 120

    def __init__(
        self,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        executor: Optional[Executor] = None,
        api_configs: Optional[Dict[str, Dict[str, str]]] = None,
    ):
        """
        Initialize the request dispatcher.

        :param loop: the asyncio loop.
        :param executor: an executor.
        """
        self.loop = loop if loop is not None else asyncio.get_event_loop()
        self.executor = executor
        self._api_configs = api_configs

    def api_config(self, ledger_id: str) -> Dict[str, str]:
        """Get api config"""
        config = {}  # type: Dict[str, str]
        if self._api_configs is not None and ledger_id in self._api_configs:
            config = self._api_configs[ledger_id]
        return config

    async def run_async(self, func: Callable[[Any], Task], *args):
        """
        Run a function in executor.

        :param func: the function to execute.
        :param args: the arguments to pass to the function.
        :return: the return value of the function.
        """
        try:
            response = await self.loop.run_in_executor(self.executor, func, *args)
            return response
        except Exception as e:  # pylint: disable=broad-except
            return self.get_error_message(e, *args)

    def dispatch(self, envelope: Envelope) -> Task:
        """
        Dispatch the request to the right sender handler.

        :param envelope: the envelope.
        :return: an awaitable.
        """
        message = self.get_message(envelope)
        ledger_id = self.get_ledger_id(message)
        api = self.registry.make(ledger_id, **self.api_config(ledger_id))
        message.is_incoming = True
        dialogue = self.dialogues.update(message)
        assert dialogue is not None, "No dialogue created."
        performative = message.performative
        handler = self.get_handler(performative)
        return self.loop.create_task(self.run_async(handler, api, message, dialogue))

    def get_handler(self, performative: Any) -> Callable[[Any], Task]:
        """
        Get the handler method, given the message performative.

        :param performative: the message performative.
        :return: the method that will send the request.
        """
        handler = getattr(self, performative.value, lambda *args, **kwargs: None)
        if handler is None:
            raise Exception("Performative not recognized.")
        return handler

    @abstractmethod
    def get_error_message(self, *args) -> Message:
        """
        Build an error message.

        :param args: positional arguments.
        :return: an error message response.
        """

    @property
    @abstractmethod
    def dialogues(self) -> Dialogues:
        """Get the dialogues."""

    @property
    @abstractmethod
    def registry(self) -> Registry:
        """Get the registry."""

    @abstractmethod
    def get_message(self, envelope: Envelope) -> Message:
        """Get the message from envelope."""

    @abstractmethod
    def get_ledger_id(self, message: Message) -> str:
        """Extract the ledger id from the message."""
