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

import copy
import datetime
from collections import defaultdict, deque
from typing import Deque, Dict, List, Tuple, cast

from aea.common import Address
from aea.decision_maker.default import OwnershipState
from aea.exceptions import enforce
from aea.helpers.search.models import Description
from aea.helpers.transaction.base import RawMessage, Terms
from aea.protocols.dialogue.base import DialogueLabel
from aea.protocols.signing.message import SigningMessage
from aea.skills.base import Model

from packages.fetchai.skills.tac_negotiation.dialogues import (
    FipaDialogue,
    SigningDialogue,
    SigningDialogues,
)

MessageId = int


class Transactions(Model):
    """Class to handle pending transaction proposals/acceptances and locked transactions."""

    def __init__(self, **kwargs) -> None:
        """Initialize the transactions."""
        self._pending_transaction_timeout = kwargs.pop(
            "pending_transaction_timeout", 30
        )
        super().__init__(**kwargs)
        self._pending_proposals = defaultdict(
            lambda: {}
        )  # type: Dict[DialogueLabel, Dict[MessageId, SigningMessage]]
        self._pending_initial_acceptances = defaultdict(
            lambda: {}
        )  # type: Dict[DialogueLabel, Dict[MessageId, SigningMessage]]

        self._locked_txs = {}  # type: Dict[str, SigningMessage]
        self._locked_txs_as_buyer = {}  # type: Dict[str, SigningMessage]
        self._locked_txs_as_seller = {}  # type: Dict[str, SigningMessage]

        self._last_update_for_transactions = (
            deque()
        )  # type: Deque[Tuple[datetime.datetime, str]]
        self._nonce = 0

    @property
    def pending_proposals(
        self,
    ) -> Dict[DialogueLabel, Dict[MessageId, SigningMessage]]:
        """Get the pending proposals."""
        return self._pending_proposals

    @property
    def pending_initial_acceptances(
        self,
    ) -> Dict[DialogueLabel, Dict[MessageId, SigningMessage]]:
        """Get the pending initial acceptances."""
        return self._pending_initial_acceptances

    def get_next_nonce(self) -> str:
        """Get the next nonce."""
        self._nonce += 1
        return str(self._nonce)

    def generate_signing_message(
        self,
        performative: SigningMessage.Performative,
        proposal_description: Description,
        fipa_dialogue: FipaDialogue,
        role: FipaDialogue.Role,
        agent_addr: Address,
    ) -> SigningMessage:
        """
        Generate the transaction message from the description and the dialogue.

        :param proposal_description: the description of the proposal
        :param fipa_dialogue: the fipa dialogue
        :param role: the role of the agent (seller or buyer)
        :param agent_addr: the address of the agent
        :return: a transaction message
        """
        is_seller = role == FipaDialogue.Role.SELLER

        goods_component = copy.copy(proposal_description.values)
        [  # pylint: disable=expression-not-assigned
            goods_component.pop(key)
            for key in ["fee", "price", "currency_id", "nonce", "ledger_id"]
        ]
        # switch signs based on whether seller or buyer role
        amount = (
            proposal_description.values["price"]
            if is_seller
            else -proposal_description.values["price"]
        )
        fee = proposal_description.values["fee"]
        if is_seller:
            for good_id in goods_component.keys():
                goods_component[good_id] = goods_component[good_id] * (-1)
        amount_by_currency_id = {proposal_description.values["currency_id"]: amount}
        fee_by_currency_id = {proposal_description.values["currency_id"]: fee}
        nonce = proposal_description.values["nonce"]
        ledger_id = proposal_description.values["ledger_id"]
        terms = Terms(
            ledger_id=ledger_id,
            sender_address=agent_addr,
            counterparty_address=fipa_dialogue.dialogue_label.dialogue_opponent_addr,
            amount_by_currency_id=amount_by_currency_id,
            is_sender_payable_tx_fee=not is_seller,
            quantities_by_good_id=goods_component,
            nonce=nonce,
            fee_by_currency_id=fee_by_currency_id,
        )
        signing_dialogues = cast(SigningDialogues, self.context.signing_dialogues)
        raw_message = RawMessage(
            ledger_id=ledger_id, body=terms.sender_hash.encode("utf-8")
        )
        signing_msg, signing_dialogue = signing_dialogues.create(
            counterparty="decision_maker",
            performative=performative,
            terms=terms,
            raw_message=raw_message,
        )
        signing_dialogue = cast(SigningDialogue, signing_dialogue)
        signing_dialogue.associated_fipa_dialogue = fipa_dialogue
        return cast(SigningMessage, signing_msg)

    def update_confirmed_transactions(self) -> None:
        """
        Update model wrt to confirmed transactions.

        :return: None
        """
        confirmed_tx_ids = self.context.shared_state.pop(
            "confirmed_tx_ids", []
        )  # type: List[str]
        for transaction_id in confirmed_tx_ids:
            # remove (safely) the associated pending proposal (if present)
            self._locked_txs.pop(transaction_id, None)
            self._locked_txs_as_buyer.pop(transaction_id, None)
            self._locked_txs_as_seller.pop(transaction_id, None)

    def cleanup_pending_transactions(self) -> None:
        """
        Remove all the pending messages (i.e. either proposals or acceptances) that have been stored for an amount of time longer than the timeout.

        :return: None
        """
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
                break
            next_date, next_item = queue[0]

    def add_pending_proposal(
        self,
        dialogue_label: DialogueLabel,
        proposal_id: int,
        signing_msg: SigningMessage,
    ) -> None:
        """
        Add a proposal (in the form of a transaction) to the pending list.

        :param dialogue_label: the dialogue label associated with the proposal
        :param proposal_id: the message id of the proposal
        :param signing_msg: the transaction message
        :raise AEAEnforceError: if the pending proposal is already present.

        :return: None
        """
        enforce(
            dialogue_label not in self._pending_proposals
            and proposal_id not in self._pending_proposals[dialogue_label],
            "Proposal is already in the list of pending proposals.",
        )
        self._pending_proposals[dialogue_label][proposal_id] = signing_msg

    def pop_pending_proposal(
        self, dialogue_label: DialogueLabel, proposal_id: int
    ) -> SigningMessage:
        """
        Remove a proposal (in the form of a transaction) from the pending list.

        :param dialogue_label: the dialogue label associated with the proposal
        :param proposal_id: the message id of the proposal
        :raise AEAEnforceError: if the pending proposal is not present.

        :return: the transaction message
        """
        enforce(
            dialogue_label in self._pending_proposals
            and proposal_id in self._pending_proposals[dialogue_label],
            "Cannot find the proposal in the list of pending proposals.",
        )
        signing_msg = self._pending_proposals[dialogue_label].pop(proposal_id)
        return signing_msg

    def add_pending_initial_acceptance(
        self,
        dialogue_label: DialogueLabel,
        proposal_id: int,
        signing_msg: SigningMessage,
    ) -> None:
        """
        Add an acceptance (in the form of a transaction) to the pending list.

        :param dialogue_label: the dialogue label associated with the proposal
        :param proposal_id: the message id of the proposal
        :param signing_msg: the transaction message
        :raise AEAEnforceError: if the pending acceptance is already present.

        :return: None
        """
        enforce(
            dialogue_label not in self._pending_initial_acceptances
            and proposal_id not in self._pending_initial_acceptances[dialogue_label],
            "Initial acceptance is already in the list of pending initial acceptances.",
        )
        self._pending_initial_acceptances[dialogue_label][proposal_id] = signing_msg

    def pop_pending_initial_acceptance(
        self, dialogue_label: DialogueLabel, proposal_id: int
    ) -> SigningMessage:
        """
        Remove an acceptance (in the form of a transaction) from the pending list.

        :param dialogue_label: the dialogue label associated with the proposal
        :param proposal_id: the message id of the proposal
        :raise AEAEnforceError: if the pending acceptance is not present.

        :return: the transaction message
        """
        enforce(
            dialogue_label in self._pending_initial_acceptances
            and proposal_id in self._pending_initial_acceptances[dialogue_label],
            "Cannot find the initial acceptance in the list of pending initial acceptances.",
        )
        signing_msg = self._pending_initial_acceptances[dialogue_label].pop(proposal_id)
        return signing_msg

    def _register_transaction_with_time(self, transaction_id: str) -> None:
        """
        Register a transaction with a creation datetime.

        :param transaction_id: the transaction id

        :return: None
        """
        now = datetime.datetime.now()
        self._last_update_for_transactions.append((now, transaction_id))

    def add_locked_tx(
        self, signing_msg: SigningMessage, role: FipaDialogue.Role
    ) -> None:
        """
        Add a lock (in the form of a transaction).

        :param signing_msg: the transaction message
        :param role: the role of the agent (seller or buyer)
        :raise AEAEnforceError: if the transaction is already present.

        :return: None
        """
        as_seller = role == FipaDialogue.Role.SELLER

        transaction_id = signing_msg.terms.id
        enforce(
            transaction_id not in self._locked_txs,
            "This transaction is already a locked transaction.",
        )
        self._register_transaction_with_time(transaction_id)
        self._locked_txs[transaction_id] = signing_msg
        if as_seller:
            self._locked_txs_as_seller[transaction_id] = signing_msg
        else:
            self._locked_txs_as_buyer[transaction_id] = signing_msg

    def pop_locked_tx(self, signing_msg: SigningMessage) -> SigningMessage:
        """
        Remove a lock (in the form of a transaction).

        :param signing_msg: the transaction message
        :raise AEAEnforceError: if the transaction with the given transaction id has not been found.

        :return: the transaction
        """
        transaction_id = signing_msg.terms.id
        enforce(
            transaction_id in self._locked_txs,
            "Cannot find this transaction in the list of locked transactions.",
        )
        signing_msg = self._locked_txs.pop(transaction_id)
        self._locked_txs_as_buyer.pop(transaction_id, None)
        self._locked_txs_as_seller.pop(transaction_id, None)
        return signing_msg

    def ownership_state_after_locks(self, is_seller: bool) -> OwnershipState:
        """
        Apply all the locks to the current ownership state of the agent.

        This assumes, that all the locked transactions will be successful.

        :param is_seller: Boolean indicating the role of the agent.

        :return: the agent state with the locks applied to current state
        """
        signing_msgs = (
            list(self._locked_txs_as_seller.values())
            if is_seller
            else list(self._locked_txs_as_buyer.values())
        )
        terms = [signing_msg.terms for signing_msg in signing_msgs]
        ownership_state = cast(
            OwnershipState, self.context.decision_maker_handler_context.ownership_state
        )
        ownership_state_after_locks = ownership_state.apply_transactions(terms)
        return ownership_state_after_locks
