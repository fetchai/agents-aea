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

"""This module contains a class to manage transactions."""

import datetime
from collections import defaultdict, deque
from typing import Any, Deque, Dict, List, Tuple, cast

from aea.decision_maker.gop import OwnershipState
from aea.exceptions import enforce
from aea.helpers.transaction.base import Terms
from aea.protocols.dialogue.base import DialogueLabel
from aea.skills.base import Model

from packages.fetchai.skills.tac_negotiation.dialogues import FipaDialogue


MessageId = int


class Transactions(Model):
    """Class to handle pending transaction proposals/acceptances and locked transactions."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the transactions."""
        self._pending_transaction_timeout = kwargs.pop(
            "pending_transaction_timeout", 30
        )
        super().__init__(**kwargs)
        self._pending_proposals = defaultdict(
            lambda: {}
        )  # type: Dict[DialogueLabel, Dict[MessageId, Terms]]
        self._pending_initial_acceptances = defaultdict(
            lambda: {}
        )  # type: Dict[DialogueLabel, Dict[MessageId, Terms]]

        self._locked_txs = {}  # type: Dict[str, Terms]
        self._locked_txs_as_buyer = {}  # type: Dict[str, Terms]
        self._locked_txs_as_seller = {}  # type: Dict[str, Terms]

        self._last_update_for_transactions = (
            deque()
        )  # type: Deque[Tuple[datetime.datetime, str]]
        self._nonce = 0

    @property
    def pending_proposals(self,) -> Dict[DialogueLabel, Dict[MessageId, Terms]]:
        """Get the pending proposals."""
        return self._pending_proposals

    @property
    def pending_initial_acceptances(
        self,
    ) -> Dict[DialogueLabel, Dict[MessageId, Terms]]:
        """Get the pending initial acceptances."""
        return self._pending_initial_acceptances

    def get_next_nonce(self) -> str:
        """Get the next nonce."""
        self._nonce += 1
        return str(self._nonce)

    def update_confirmed_transactions(self) -> None:
        """Update model wrt to confirmed transactions."""
        confirmed_tx_ids = self.context.shared_state.pop(
            "confirmed_tx_ids", []
        )  # type: List[str]
        for transaction_id in confirmed_tx_ids:
            # remove (safely) the associated pending proposal (if present)
            self._locked_txs.pop(transaction_id, None)
            self._locked_txs_as_buyer.pop(transaction_id, None)
            self._locked_txs_as_seller.pop(transaction_id, None)

    def cleanup_pending_transactions(self) -> None:
        """Remove all the pending messages (i.e. either proposals or acceptances) that have been stored for an amount of time longer than the timeout."""
        queue = self._last_update_for_transactions
        timeout = datetime.timedelta(0, self._pending_transaction_timeout)

        if len(queue) == 0:
            return

        next_date, next_item = queue[0]

        while datetime.datetime.now() - next_date > timeout:

            # remove the element from the queue
            queue.popleft()

            # extract dialogue label and message id
            transaction_id = next_item
            self.context.logger.debug(
                "removing transaction from pending list: {}".format(transaction_id)
            )

            # remove (safely) the associated pending proposal (if present)
            self._locked_txs.pop(transaction_id, None)
            self._locked_txs_as_buyer.pop(transaction_id, None)
            self._locked_txs_as_seller.pop(transaction_id, None)

            # check the next transaction, if present
            if len(queue) == 0:
                break  # pragma: no cover
            next_date, next_item = queue[0]  # pragma: no cover

    def add_pending_proposal(
        self, dialogue_label: DialogueLabel, proposal_id: int, terms: Terms,
    ) -> None:
        """
        Add a proposal (in the form of a transaction) to the pending list.

        :param dialogue_label: the dialogue label associated with the proposal
        :param proposal_id: the message id of the proposal
        :param terms: the terms
        """
        enforce(
            dialogue_label not in self._pending_proposals
            and proposal_id not in self._pending_proposals[dialogue_label],
            "Proposal is already in the list of pending proposals.",
        )
        self._pending_proposals[dialogue_label][proposal_id] = terms

    def pop_pending_proposal(
        self, dialogue_label: DialogueLabel, proposal_id: int
    ) -> Terms:
        """
        Remove a proposal (in the form of a transaction) from the pending list.

        :param dialogue_label: the dialogue label associated with the proposal
        :param proposal_id: the message id of the proposal
        :return: terms
        """
        enforce(
            dialogue_label in self._pending_proposals
            and proposal_id in self._pending_proposals[dialogue_label],
            "Cannot find the proposal in the list of pending proposals.",
        )
        terms = self._pending_proposals[dialogue_label].pop(proposal_id)
        return terms

    def add_pending_initial_acceptance(
        self, dialogue_label: DialogueLabel, proposal_id: int, terms: Terms,
    ) -> None:
        """
        Add an acceptance (in the form of a transaction) to the pending list.

        :param dialogue_label: the dialogue label associated with the proposal
        :param proposal_id: the message id of the proposal
        :param terms: the terms
        """
        enforce(
            dialogue_label not in self._pending_initial_acceptances
            and proposal_id not in self._pending_initial_acceptances[dialogue_label],
            "Initial acceptance is already in the list of pending initial acceptances.",
        )
        self._pending_initial_acceptances[dialogue_label][proposal_id] = terms

    def pop_pending_initial_acceptance(
        self, dialogue_label: DialogueLabel, proposal_id: int
    ) -> Terms:
        """
        Remove an acceptance (in the form of a transaction) from the pending list.

        :param dialogue_label: the dialogue label associated with the proposal
        :param proposal_id: the message id of the proposal
        :return: the transaction message
        """
        enforce(
            dialogue_label in self._pending_initial_acceptances
            and proposal_id in self._pending_initial_acceptances[dialogue_label],
            "Cannot find the initial acceptance in the list of pending initial acceptances.",
        )
        terms = self._pending_initial_acceptances[dialogue_label].pop(proposal_id)
        return terms

    def _register_transaction_with_time(self, transaction_id: str) -> None:
        """
        Register a transaction with a creation datetime.

        :param transaction_id: the transaction id
        """
        now = datetime.datetime.now()
        self._last_update_for_transactions.append((now, transaction_id))

    def add_locked_tx(self, terms: Terms, role: FipaDialogue.Role) -> None:
        """
        Add a lock (in the form of a transaction).

        :param terms: the terms
        :param role: the role of the agent (seller or buyer)
        """
        as_seller = role == FipaDialogue.Role.SELLER

        transaction_id = terms.id
        enforce(
            transaction_id not in self._locked_txs,
            "This transaction is already a locked transaction.",
        )
        self._register_transaction_with_time(transaction_id)
        self._locked_txs[transaction_id] = terms
        if as_seller:
            self._locked_txs_as_seller[transaction_id] = terms
        else:
            self._locked_txs_as_buyer[transaction_id] = terms

    def pop_locked_tx(self, terms: Terms) -> Terms:
        """
        Remove a lock (in the form of a transaction).

        :param terms: the terms
        :return: the transaction
        """
        transaction_id = terms.id
        enforce(
            transaction_id in self._locked_txs,
            "Cannot find this transaction in the list of locked transactions.",
        )
        terms = self._locked_txs.pop(transaction_id)
        self._locked_txs_as_buyer.pop(transaction_id, None)
        self._locked_txs_as_seller.pop(transaction_id, None)
        return terms

    def ownership_state_after_locks(self, is_seller: bool) -> OwnershipState:
        """
        Apply all the locks to the current ownership state of the agent.

        This assumes, that all the locked transactions will be successful.

        :param is_seller: Boolean indicating the role of the agent.
        :return: the agent state with the locks applied to current state
        """
        all_terms = (
            list(self._locked_txs_as_seller.values())
            if is_seller
            else list(self._locked_txs_as_buyer.values())
        )
        ownership_state = cast(
            OwnershipState, self.context.decision_maker_handler_context.ownership_state
        )
        ownership_state_after_locks = ownership_state.apply_transactions(all_terms)
        return ownership_state_after_locks
