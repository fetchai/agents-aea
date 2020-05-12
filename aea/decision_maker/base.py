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

"""This module contains the decision maker class."""

import hashlib
import logging
import threading
import uuid
from abc import ABC, abstractmethod
from enum import Enum
from queue import Queue
from threading import Thread
from typing import List, Optional

from aea.crypto.wallet import Wallet
from aea.decision_maker.messages.base import InternalMessage
from aea.decision_maker.messages.state_update import StateUpdateMessage
from aea.decision_maker.messages.transaction import TransactionMessage
from aea.identity.base import Identity

logger = logging.getLogger(__name__)


def _hash(access_code: str) -> str:
    """
    Get the hash of the access code.

    :param access_code: the access code
    :return: the hash
    """
    result = hashlib.sha224(access_code.encode("utf-8")).hexdigest()
    return result


class GoalPursuitReadiness:
    """The goal pursuit readiness."""

    class Status(Enum):
        """
        The enum of the readiness status.

        In particular, it can be one of the following:

        - Status.READY: when the agent is ready to pursuit its goal
        - Status.NOT_READY: when the agent is not ready to pursuit its goal
        """

        READY = "ready"
        NOT_READY = "not_ready"

    def __init__(self):
        """Instantiate the goal pursuit readiness."""
        self._status = GoalPursuitReadiness.Status.NOT_READY

    @property
    def is_ready(self) -> bool:
        """Get the readiness."""
        return self._status.value == GoalPursuitReadiness.Status.READY.value

    def update(self, new_status: Status) -> None:
        """
        Update the goal pursuit readiness.

        :param new_status: the new status
        :return: None
        """
        self._status = new_status


class OwnershipState(ABC):
    """Represent the ownership state of an agent."""

    @abstractmethod
    def set(self, **kwargs) -> None:
        """
        Set values on the ownership state.

        :param kwargs: the relevant keyword arguments
        :return: None
        """

    @abstractmethod
    def apply_delta(self, **kwargs) -> None:
        """
        Apply a state update to the ownership state.

        This method is used to apply a raw state update without a transaction.

        :param kwargs: the relevant keyword arguments
        :return: None
        """

    @property
    @abstractmethod
    def is_initialized(self) -> bool:
        """Get the initialization status."""

    @abstractmethod
    def is_affordable_transaction(self, tx_message: TransactionMessage) -> bool:
        """
        Check if the transaction is affordable (and consistent).

        :param tx_message: the transaction message
        :return: True if the transaction is legal wrt the current state, false otherwise.
        """

    @abstractmethod
    def apply_transactions(
        self, transactions: List[TransactionMessage]
    ) -> "OwnershipState":
        """
        Apply a list of transactions to (a copy of) the current state.

        :param transactions: the sequence of transaction messages.
        :return: the final state.
        """

    @abstractmethod
    def __copy__(self) -> "OwnershipState":
        """Copy the object."""


class LedgerStateProxy:
    """Class to represent a proxy to a ledger state."""

    @property
    @abstractmethod
    def is_initialized(self) -> bool:
        """Get the initialization status."""

    @abstractmethod
    def is_affordable_transaction(self, tx_message: TransactionMessage) -> bool:
        """
        Check if the transaction is affordable on the default ledger.

        :param tx_message: the transaction message
        :return: whether the transaction is affordable on the ledger
        """


class Preferences:
    """Class to represent the preferences."""

    @abstractmethod
    def set(self, **kwargs,) -> None:
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
    def marginal_utility(self, ownership_state: OwnershipState, **kwargs,) -> float:
        """
        Compute the marginal utility.

        :param ownership_state: the ownership state against which to compute the marginal utility.
        :param kwargs: optional keyword argyments
        :return: the marginal utility score
        """

    @abstractmethod
    def utility_diff_from_transaction(
        self, ownership_state: OwnershipState, tx_message: TransactionMessage
    ) -> float:
        """
        Simulate a transaction and get the resulting utility difference (taking into account the fee).

        :param ownership_state: the ownership state against which to apply the transaction.
        :param tx_message: a transaction message.
        :return: the score.
        """

    @abstractmethod
    def __copy__(self) -> "Preferences":
        """Copy the object."""


class ProtectedQueue(Queue):
    """A wrapper of a queue to protect which object can read from it."""

    def __init__(self, access_code: str):
        """
        Initialize the protected queue.

        :param access_code: the access code to read from the queue
        """
        super().__init__()
        self._access_code_hash = _hash(access_code)

    def put(
        self, internal_message: Optional[InternalMessage], block=True, timeout=None
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
        :raises: ValueError, if the item is not an internal message
        :return: None
        """
        if not (
            type(internal_message)
            in {InternalMessage, TransactionMessage, StateUpdateMessage}
            or internal_message is None
        ):
            raise ValueError("Only internal messages are allowed!")
        super().put(internal_message, block=True, timeout=None)

    def put_nowait(self, internal_message: Optional[InternalMessage]) -> None:
        """
        Put an internal message on the queue.

        Equivalent to put(item, False).

        :param internal_message: the internal message to put on the queue
        :raises: ValueError, if the item is not an internal message
        :return: None
        """
        if not (
            type(internal_message)
            in {InternalMessage, TransactionMessage, StateUpdateMessage}
            or internal_message is None
        ):
            raise ValueError("Only internal messages are allowed!")
        super().put_nowait(internal_message)

    def get(self, block=True, timeout=None) -> None:
        """
        Inaccessible get method.

        :raises: ValueError, access not permitted.
        :return: None
        """
        raise ValueError("Access not permitted!")

    def get_nowait(self) -> None:
        """
        Inaccessible get_nowait method.

        :raises: ValueError, access not permitted.
        :return: None
        """
        raise ValueError("Access not permitted!")

    def protected_get(
        self, access_code: str, block=True, timeout=None
    ) -> Optional[InternalMessage]:
        """
        Access protected get method.

        :param access_code: the access code
        :param block: If optional args block is true and timeout is None (the default), block if necessary until an item is available.
        :param timeout: If timeout is a positive number, it blocks at most timeout seconds and raises the Empty exception if no item was available within that time.
        :raises: ValueError, if caller is not permitted
        :return: internal message
        """
        if not self._access_code_hash == _hash(access_code):
            raise ValueError("Wrong code, access not permitted!")
        internal_message = super().get(
            block=block, timeout=timeout
        )  # type: Optional[InternalMessage]
        return internal_message


class DecisionMaker:
    """This class implements the decision maker."""

    def __init__(
        self,
        identity: Identity,
        wallet: Wallet,
        ownership_state: OwnershipState,
        ledger_state_proxy: LedgerStateProxy,
        preferences: Preferences,
        **kwargs,
    ):
        """
        Initialize the decision maker.

        :param identity: the identity
        :param wallet: the wallet
        :param ledger_apis: the ledger apis
        """
        self._kwargs = kwargs
        self._agent_name = identity.name
        self._wallet = wallet
        self._queue_access_code = uuid.uuid4().hex
        self._message_in_queue = ProtectedQueue(
            self._queue_access_code
        )  # type: ProtectedQueue
        self._message_out_queue = Queue()  # type: Queue
        self._ownership_state = ownership_state
        self._ledger_state_proxy = ledger_state_proxy
        self._preferences = preferences
        self._goal_pursuit_readiness = GoalPursuitReadiness()
        self._thread = None  # type: Optional[Thread]
        self._lock = threading.Lock()
        self._stopped = True

    @property
    def message_in_queue(self) -> ProtectedQueue:
        """Get (in) queue."""
        return self._message_in_queue

    @property
    def message_out_queue(self) -> Queue:
        """Get (out) queue."""
        return self._message_out_queue

    @property
    def wallet(self) -> Wallet:
        """Get wallet."""
        return self._wallet

    @property
    def ownership_state(self) -> OwnershipState:
        """Get ownership state."""
        return self._ownership_state

    @property
    def ledger_state_proxy(self) -> LedgerStateProxy:
        """Get ledger state proxy."""
        return self._ledger_state_proxy

    @property
    def preferences(self) -> Preferences:
        """Get preferences."""
        return self._preferences

    @property
    def goal_pursuit_readiness(self) -> GoalPursuitReadiness:
        """Get readiness of agent to pursuit its goals."""
        return self._goal_pursuit_readiness

    def start(self) -> None:
        """Start the decision maker."""
        with self._lock:
            if not self._stopped:  # pragma: no cover
                logger.debug(
                    "[{}]: Decision maker already started.".format(self._agent_name)
                )
                return

            self._stopped = False
            self._thread = Thread(target=self.execute)
            self._thread.start()

    def stop(self) -> None:
        """Stop the decision maker."""
        with self._lock:
            self._stopped = True
            self.message_in_queue.put(None)
            if self._thread is not None:
                self._thread.join()
            logger.debug("[{}]: Decision Maker stopped.".format(self._agent_name))
            self._thread = None

    def execute(self) -> None:
        """
        Execute the decision maker.

        Performs the following while not stopped:

        - gets internal messages from the in queue and calls handle() on them

        :return: None
        """
        while not self._stopped:
            message = self.message_in_queue.protected_get(
                self._queue_access_code, block=True
            )  # type: Optional[InternalMessage]

            if message is None:
                logger.debug(
                    "[{}]: Received empty message. Quitting the processing loop...".format(
                        self._agent_name
                    )
                )
                continue

            if message.protocol_id == InternalMessage.protocol_id:
                self.handle(message)
            else:
                logger.warning(
                    "[{}]: Message received by the decision maker is not of protocol_id=internal.".format(
                        self._agent_name
                    )
                )

    @abstractmethod
    def handle(self, message: InternalMessage) -> None:
        """
        Handle an internal message from the skills.

        :param message: the internal message
        :return: None
        """
