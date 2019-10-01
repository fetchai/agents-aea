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

"""This module contains a class to manage transactions the agent has committed to at varying degrees."""

import datetime
import logging
from collections import defaultdict, deque
from typing import Dict, Tuple, Deque

from tac.agents.participant.v1.base.dialogues import DialogueLabel
from tac.platform.game.base import Transaction, TransactionId

logger = logging.getLogger(__name__)

MESSAGE_ID = int
TRANSACTION_ID = str


class TransactionManager(object):
    """Class to handle pending transaction proposals/acceptances and locked transactions."""

    def __init__(self) -> None:
        """Initialize a TransactionManager."""

        self.pending_proposals = defaultdict(lambda: {})  # type: Dict[DialogueLabel, Dict[MESSAGE_ID, Transaction]]
        self.pending_initial_acceptances = defaultdict(lambda: {})  # type: Dict[DialogueLabel, Dict[MESSAGE_ID, Transaction]]

        self.locked_txs = {}  # type: Dict[TRANSACTION_ID, Transaction]
        self.locked_txs_as_buyer = {}  # type: Dict[TRANSACTION_ID, Transaction]
        self.locked_txs_as_seller = {}  # type: Dict[TRANSACTION_ID, Transaction]

        self._last_update_for_transactions = deque()  # type: Deque[Tuple[datetime.datetime, TRANSACTION_ID]]

    def cleanup_pending_transactions(self) -> None:
        """
        Remove all the pending messages (i.e. either proposals or acceptances) that have been stored for an amount of time longer than the timeout.

        :return: None
        """
        queue = self._last_update_for_transactions
        timeout = datetime.timedelta(0, self.pending_transaction_timeout)

        if len(queue) == 0:
            return

        next_date, next_item = queue[0]

        while datetime.datetime.now() - next_date > timeout:

            # remove the element from the queue
            queue.popleft()

            # extract dialogue label and message id
            transaction_id = next_item
            logger.debug("[{}]: Removing transaction: {}".format(self.agent_name, transaction_id))

            # remove (safely) the associated pending proposal (if present)
            self.locked_txs.pop(transaction_id, None)
            self.locked_txs_as_buyer.pop(transaction_id, None)
            self.locked_txs_as_seller.pop(transaction_id, None)

            # check the next transaction, if present
            if len(queue) == 0:
                break
            next_date, next_item = queue[0]

    def _register_transaction_with_time(self, transaction_id: TransactionId) -> None:
        """
        Register a transaction with a creation datetime.

        :param transaction_id: the transaction id

        :return: None
        """
        now = datetime.datetime.now()
        self._last_update_for_transactions.append((now, transaction_id))

    def add_pending_proposal(self, dialogue_label: DialogueLabel, proposal_id: int, transaction: Transaction) -> None:
        """
        Add a proposal (in the form of a transaction) to the pending list.

        :param dialogue_label: the dialogue label associated with the proposal
        :param proposal_id: the message id of the proposal
        :param transaction: the transaction
        :raise AssertionError: if the pending proposal is already present.

        :return: None
        """
        assert dialogue_label not in self.pending_proposals and proposal_id not in self.pending_proposals[dialogue_label]
        self.pending_proposals[dialogue_label][proposal_id] = transaction

    def pop_pending_proposal(self, dialogue_label: DialogueLabel, proposal_id: int) -> Transaction:
        """
        Remove a proposal (in the form of a transaction) from the pending list.

        :param dialogue_label: the dialogue label associated with the proposal
        :param proposal_id: the message id of the proposal
        :raise AssertionError: if the pending proposal is not present.

        :return: the transaction
        """
        assert dialogue_label in self.pending_proposals and proposal_id in self.pending_proposals[dialogue_label]
        transaction = self.pending_proposals[dialogue_label].pop(proposal_id)
        return transaction

    def add_pending_initial_acceptance(self, dialogue_label: DialogueLabel, proposal_id: int, transaction: Transaction) -> None:
        """
        Add an acceptance (in the form of a transaction) to the pending list.

        :param dialogue_label: the dialogue label associated with the proposal
        :param proposal_id: the message id of the proposal
        :param transaction: the transaction
        :raise AssertionError: if the pending acceptance is already present.

        :return: None
        """
        assert dialogue_label not in self.pending_initial_acceptances and proposal_id not in self.pending_initial_acceptances[dialogue_label]
        self.pending_initial_acceptances[dialogue_label][proposal_id] = transaction

    def pop_pending_initial_acceptance(self, dialogue_label: DialogueLabel, proposal_id: int) -> Transaction:
        """
        Remove an acceptance (in the form of a transaction) from the pending list.

        :param dialogue_label: the dialogue label associated with the proposal
        :param proposal_id: the message id of the proposal
        :raise AssertionError: if the pending acceptance is not present.

        :return: the transaction
        """
        assert dialogue_label in self.pending_initial_acceptances and proposal_id in self.pending_initial_acceptances[dialogue_label]
        transaction = self.pending_initial_acceptances[dialogue_label].pop(proposal_id)
        return transaction

    def add_locked_tx(self, transaction: Transaction, as_seller: bool) -> None:
        """
        Add a lock (in the form of a transaction).

        :param transaction: the transaction
        :param as_seller: whether the agent is a seller or not
        :raise AssertionError: if the transaction is already present.

        :return: None
        """
        transaction_id = transaction.transaction_id
        assert transaction_id not in self.locked_txs
        self._register_transaction_with_time(transaction_id)
        self.locked_txs[transaction_id] = transaction
        if as_seller:
            self.locked_txs_as_seller[transaction_id] = transaction
        else:
            self.locked_txs_as_buyer[transaction_id] = transaction

    def pop_locked_tx(self, transaction_id: TransactionId) -> Transaction:
        """
        Remove a lock (in the form of a transaction).

        :param transaction_id: the transaction id
        :raise AssertionError: if the transaction with the given transaction id has not been found.

        :return: the transaction
        """
        assert transaction_id in self.locked_txs
        transaction = self.locked_txs.pop(transaction_id)
        self.locked_txs_as_buyer.pop(transaction_id, None)
        self.locked_txs_as_seller.pop(transaction_id, None)
        return transaction
