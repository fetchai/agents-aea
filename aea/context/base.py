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


"""This module contains the agent context class."""

from queue import Queue
from types import SimpleNamespace
from typing import Any, Callable, Dict, Optional

from aea.common import Address
from aea.configurations.base import PublicId
from aea.helpers.storage.generic_storage import Storage
from aea.identity.base import Identity
from aea.multiplexer import MultiplexerStatus, OutBox
from aea.skills.tasks import TaskManager


class AgentContext:
    """Provide read access to relevant objects of the agent for the skills."""

    def __init__(
        self,
        identity: Identity,
        connection_status: MultiplexerStatus,
        outbox: OutBox,
        decision_maker_message_queue: Queue,
        decision_maker_handler_context: SimpleNamespace,
        task_manager: TaskManager,
        default_ledger_id: str,
        currency_denominations: Dict[str, str],
        default_connection: Optional[PublicId],
        default_routing: Dict[PublicId, PublicId],
        search_service_address: Address,
        decision_maker_address: Address,
        storage_callable: Callable[[], Optional[Storage]] = lambda: None,
        **kwargs
    ):
        """
        Initialize an agent context.

        :param identity: the identity object
        :param connection_status: the connection status of the multiplexer
        :param outbox: the outbox
        :param decision_maker_message_queue: the (in) queue of the decision maker
        :param decision_maker_handler_context: the decision maker's name space
        :param task_manager: the task manager
        :param default_ledger_id: the default ledger id
        :param ledger_it_to_currency_denom: mapping from ledger ids to currency denominations
        :param default_connection: the default connection
        :param default_routing: the default routing
        :param search_service_address: the address of the search service
        :param decision_maker_address: the address of the decision maker
        :param storage_callable: function that returns optional storage attached to agent.
        :param kwargs: keyword arguments to be attached in the agent context namespace.
        """
        self._shared_state = {}  # type: Dict[str, Any]
        self._identity = identity
        self._connection_status = connection_status
        self._outbox = outbox
        self._decision_maker_message_queue = decision_maker_message_queue
        self._decision_maker_handler_context = decision_maker_handler_context
        self._task_manager = task_manager
        self._search_service_address = search_service_address
        self._decision_maker_address = decision_maker_address
        self._default_ledger_id = default_ledger_id
        self._currency_denominations = currency_denominations
        self._default_connection = default_connection
        self._default_routing = default_routing
        self._storage_callable = storage_callable
        self._namespace = SimpleNamespace(**kwargs)

    @property
    def storage(self) -> Optional[Storage]:
        """Return storage instance if enabled in AEA."""
        return self._storage_callable()

    @property
    def shared_state(self) -> Dict[str, Any]:
        """
        Get the shared state dictionary.

        The shared state is the only object which skills can use
        to exchange state directly. It is accessible (read and write) from
        all skills.
        """
        return self._shared_state

    @property
    def identity(self) -> Identity:
        """Get the identity."""
        return self._identity

    @property
    def agent_name(self) -> str:
        """Get agent name."""
        return self.identity.name

    @property
    def addresses(self) -> Dict[str, Address]:
        """Get addresses."""
        return self.identity.addresses

    @property
    def address(self) -> Address:
        """Get the default address."""
        return self.identity.address

    @property
    def connection_status(self) -> MultiplexerStatus:
        """Get connection status of the multiplexer."""
        return self._connection_status

    @property
    def outbox(self) -> OutBox:
        """Get outbox."""
        return self._outbox

    @property
    def decision_maker_message_queue(self) -> Queue:
        """Get decision maker queue."""
        return self._decision_maker_message_queue

    @property
    def decision_maker_handler_context(self) -> SimpleNamespace:
        """Get the decision maker handler context."""
        return self._decision_maker_handler_context

    @property
    def task_manager(self) -> TaskManager:
        """Get the task manager."""
        return self._task_manager

    @property
    def search_service_address(self) -> Address:
        """Get the address of the search service."""
        return self._search_service_address

    @property
    def decision_maker_address(self) -> Address:
        """Get the address of the decision maker."""
        return self._decision_maker_address

    @property
    def default_ledger_id(self) -> str:
        """Get the default ledger id."""
        return self._default_ledger_id

    @property
    def currency_denominations(self) -> Dict[str, str]:
        """Get a dictionary mapping ledger ids to currency denominations."""
        return self._currency_denominations

    @property
    def default_connection(self) -> Optional[PublicId]:
        """Get the default connection."""
        return self._default_connection

    @property
    def default_routing(self) -> Dict[PublicId, PublicId]:
        """Get the default routing."""
        return self._default_routing

    @property
    def namespace(self) -> SimpleNamespace:
        """Get the agent context namespace."""
        return self._namespace
