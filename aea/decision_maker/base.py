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
"""This module contains the decision maker class."""

import hashlib
import threading
from abc import ABC, abstractmethod
from queue import Queue
from threading import Thread
from types import SimpleNamespace
from typing import Any, Dict, List, Optional
from uuid import uuid4

from aea.crypto.wallet import Wallet
from aea.helpers.async_friendly_queue import AsyncFriendlyQueue
from aea.helpers.logging import WithLogger, get_logger
from aea.helpers.transaction.base import Terms
from aea.identity.base import Identity
from aea.protocols.base import Message


def _hash(access_code: str) -> str:
    """
    Get the hash of the access code.

    :param access_code: the access code
    :return: the hash
    """
    result = hashlib.sha224(access_code.encode("utf-8")).hexdigest()
    return result


class OwnershipState(ABC):
    """Represent the ownership state of an agent (can proxy a ledger)."""

    @abstractmethod
    def set(self, **kwargs: Any) -> None:
        """
        Set values on the ownership state.

        :param kwargs: the relevant keyword arguments
        """

    @abstractmethod
    def apply_delta(self, **kwargs: Any) -> None:
        """
        Apply a state update to the ownership state.

        This method is used to apply a raw state update without a transaction.

        :param kwargs: the relevant keyword arguments
        """

    @property
    @abstractmethod
    def is_initialized(self) -> bool:
        """Get the initialization status."""

    @abstractmethod
    def is_affordable_transaction(self, terms: Terms) -> bool:
        """
        Check if the transaction is affordable (and consistent).

        :param terms: the transaction terms
        :return: True if the transaction is legal wrt the current state, false otherwise.
        """

    @abstractmethod
    def apply_transactions(self, list_of_terms: List[Terms]) -> "OwnershipState":
        """
        Apply a list of transactions to (a copy of) the current state.

        :param list_of_terms: the sequence of transaction terms.
        :return: the final state.
        """

    @abstractmethod
    def __copy__(self) -> "OwnershipState":
        """Copy the object."""


class Preferences(ABC):
    """Class to represent the preferences."""

    @abstractmethod
    def set(self, **kwargs: Any) -> None:
        """
        Set values on the preferences.

        :param kwargs: the relevant key word arguments
        """

    @property
    @abstractmethod
    def is_initialized(self) -> bool:
        """
        Get the initialization status.

        Returns True if exchange_params_by_currency_id and utility_params_by_good_id are not None.
        """

    @abstractmethod
    def marginal_utility(self, ownership_state: OwnershipState, **kwargs: Any) -> float:
        """
        Compute the marginal utility.

        :param ownership_state: the ownership state against which to compute the marginal utility.
        :param kwargs: optional keyword arguments
        :return: the marginal utility score
        """

    @abstractmethod
    def utility_diff_from_transaction(
        self, ownership_state: OwnershipState, terms: Terms
    ) -> float:
        """
        Simulate a transaction and get the resulting utility difference (taking into account the fee).

        :param ownership_state: the ownership state against which to apply the transaction.
        :param terms: the transaction terms.
        :return: the score.
        """

    @abstractmethod
    def __copy__(self) -> "Preferences":
        """Copy the object."""


class ProtectedQueue(Queue):
    """A wrapper of a queue to protect which object can read from it."""

    def __init__(self, access_code: str) -> None:
        """
        Initialize the protected queue.

        :param access_code: the access code to read from the queue
        """
        super().__init__()
        self._access_code_hash = _hash(access_code)

    def put(  # pylint: disable=arguments-differ
        self,
        internal_message: Optional[Message],
        block: bool = True,
        timeout: Optional[float] = None,
    ) -> None:
        """
        Put an internal message on the queue.

        If optional args block is true and timeout is None (the default),
        block if necessary until a free slot is available. If timeout is
        a positive number, it blocks at most timeout seconds and raises
        the Full exception if no free slot was available within that time.
        Otherwise (block is false), put an item on the queue if a free slot
        is immediately available, else raise the Full exception (timeout is
        ignored in that case).

        :param internal_message: the internal message to put on the queue
        :param block: whether to block or not
        :param timeout: timeout on block
        :raises: ValueError, if the item is not an internal message
        """
        if not (isinstance(internal_message, Message) or internal_message is None):
            raise ValueError("Only messages are allowed!")
        super().put(internal_message, block=True, timeout=None)

    def put_nowait(  # pylint: disable=arguments-differ
        self, internal_message: Optional[Message]
    ) -> None:
        """
        Put an internal message on the queue.

        Equivalent to put(item, False).

        :param internal_message: the internal message to put on the queue
        :raises: ValueError, if the item is not an internal message
        """
        if not (isinstance(internal_message, Message) or internal_message is None):
            raise ValueError("Only messages are allowed!")
        super().put_nowait(internal_message)

    def get(self, block: bool = True, timeout: Optional[float] = None) -> None:
        """
        Inaccessible get method.

        :param block: whether to block or not
        :param timeout: timeout on block
        :raises: ValueError, access not permitted.
        """
        raise ValueError("Access not permitted!")

    def get_nowait(self) -> None:
        """
        Inaccessible get_nowait method.

        :raises: ValueError, access not permitted.
        """
        raise ValueError("Access not permitted!")

    def protected_get(
        self, access_code: str, block: bool = True, timeout: Optional[float] = None
    ) -> Optional[Message]:
        """
        Access protected get method.

        :param access_code: the access code
        :param block: If optional args block is true and timeout is None (the default), block if necessary until an item is available.
        :param timeout: If timeout is a positive number, it blocks at most timeout seconds and raises the Empty exception if no item was available within that time.
        :raises: ValueError, if caller is not permitted
        :return: internal message
        """
        if self._access_code_hash != _hash(access_code):
            raise ValueError("Wrong code, access not permitted!")
        internal_message = super().get(
            block=block, timeout=timeout
        )  # type: Optional[Message]
        return internal_message


class DecisionMakerHandler(WithLogger, ABC):
    """This class implements the decision maker."""

    __slots__ = ("_identity", "_wallet", "_config", "_context", "_message_out_queue")

    self_address: str = "decision_maker"

    def __init__(
        self, identity: Identity, wallet: Wallet, config: Dict[str, Any], **kwargs: Any
    ) -> None:
        """
        Initialize the decision maker handler.

        :param identity: the identity
        :param wallet: the wallet
        :param config: the user defined configuration of the handler
        :param kwargs: the key word arguments
        """
        logger = get_logger(__name__, identity.name)
        WithLogger.__init__(self, logger=logger)
        self._identity = identity
        self._wallet = wallet
        self._config = config
        self._context = SimpleNamespace(**kwargs)
        self._message_out_queue = AsyncFriendlyQueue()  # type: AsyncFriendlyQueue

    @property
    def agent_name(self) -> str:
        """Get the agent name."""
        return self.identity.name

    @property
    def identity(self) -> Identity:
        """Get identity of the agent."""
        return self._identity

    @property
    def wallet(self) -> Wallet:
        """Get wallet of the agent."""
        return self._wallet

    @property
    def config(self) -> Dict[str, Any]:
        """Get user defined configuration"""
        return self._config

    @property
    def context(self) -> SimpleNamespace:
        """Get the context."""
        return self._context

    @property
    def message_out_queue(self) -> AsyncFriendlyQueue:
        """Get (out) queue."""
        return self._message_out_queue

    @abstractmethod
    def handle(self, message: Message) -> None:
        """
        Handle an internal message from the skills.

        :param message: the internal message
        """


class DecisionMaker(WithLogger):
    """This class implements the decision maker."""

    __slots__ = (
        "_queue_access_code",
        "_message_in_queue",
        "_decision_maker_handler",
        "_thread",
        "_lock",
        "_message_out_queue",
        "_stopped",
    )

    def __init__(
        self,
        decision_maker_handler: DecisionMakerHandler,
    ) -> None:
        """
        Initialize the decision maker.

        :param decision_maker_handler: the decision maker handler
        """
        WithLogger.__init__(self, logger=decision_maker_handler.logger)
        self._queue_access_code = uuid4().hex
        self._message_in_queue = ProtectedQueue(
            self._queue_access_code
        )  # type: ProtectedQueue
        self._decision_maker_handler = decision_maker_handler
        self._thread = None  # type: Optional[Thread]
        self._lock = threading.Lock()
        self._message_out_queue = decision_maker_handler.message_out_queue
        self._stopped = True

    @property
    def agent_name(self) -> str:
        """Get the agent name."""
        return self.decision_maker_handler.identity.name

    @property
    def message_in_queue(self) -> ProtectedQueue:
        """Get (in) queue."""
        return self._message_in_queue

    @property
    def message_out_queue(self) -> AsyncFriendlyQueue:
        """Get (out) queue."""
        return self._message_out_queue

    @property
    def decision_maker_handler(self) -> DecisionMakerHandler:
        """Get the decision maker handler."""
        return self._decision_maker_handler

    def start(self) -> None:
        """Start the decision maker."""
        with self._lock:
            if not self._stopped:  # pragma: no cover
                self.logger.debug(
                    "[{}]: Decision maker already started.".format(self.agent_name)
                )
                return

            self._stopped = False
            self._thread = Thread(target=self.execute, name=self.__class__.__name__)
            self._thread.start()

    def stop(self) -> None:
        """Stop the decision maker."""
        with self._lock:
            self._stopped = True
            self.message_in_queue.put(None)
            if self._thread is not None:
                self._thread.join()
            self.logger.debug("[{}]: Decision Maker stopped.".format(self.agent_name))
            self._thread = None

    def execute(self) -> None:
        """
        Execute the decision maker.

        Performs the following while not stopped:

        - gets internal messages from the in queue and calls handle() on them
        """
        while not self._stopped:
            message = self.message_in_queue.protected_get(
                self._queue_access_code, block=True
            )  # type: Optional[Message]

            if message is None:
                self.logger.debug(
                    "[{}]: Received empty message. Quitting the processing loop...".format(
                        self.agent_name
                    )
                )
                continue

            self.handle(message)

    def handle(self, message: Message) -> None:
        """
        Handle an internal message from the skills.

        :param message: the internal message
        """
        self.decision_maker_handler.handle(message)
