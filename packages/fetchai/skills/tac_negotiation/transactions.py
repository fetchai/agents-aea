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
from typing import Deque, Dict, Tuple

from aea.configurations.base import PublicId
from aea.decision_maker.default import OwnershipState
from aea.helpers.dialogue.base import DialogueLabel
from aea.helpers.search.models import Description
from aea.helpers.transaction.base import Terms
from aea.mail.base import Address
from aea.protocols.signing.message import SigningMessage
from aea.skills.base import Model

from packages.fetchai.skills.tac_negotiation.dialogues import Dialogue
from packages.fetchai.skills.tac_negotiation.helpers import tx_hash_from_values

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
        self._tx_nonce = 0
        self._tx_id = 0

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

    def get_next_tx_nonce(self) -> int:
        """Get the next nonce."""
        self._tx_nonce += 1
        return self._tx_nonce

    def get_internal_tx_id(self) -> str:
        """Get an id for internal reference of the tx."""
        self._tx_id += 1
        return str(self._tx_id)

    def generate_transaction_message(  # pylint: disable=no-self-use
        self,
        performative: SigningMessage.Performative,
        proposal_description: Description,
        dialogue_label: DialogueLabel,
        role: Dialogue.Role,
        agent_addr: Address,
    ) -> SigningMessage:
        """
        Generate the transaction message from the description and the dialogue.

        :param proposal_description: the description of the proposal
        :param dialogue_label: the dialogue label
        :param role: the role of the agent (seller or buyer)
        :param agent_addr: the address of the agent
        :return: a transaction message
        """
        is_seller = role == Dialogue.Role.SELLER

        # sender_tx_fee = (
        #     proposal_description.values["seller_tx_fee"]
        #     if is_seller
        #     else proposal_description.values["buyer_tx_fee"]
        # )
        # counterparty_tx_fee = (
        #     proposal_description.values["buyer_tx_fee"]
        #     if is_seller
        #     else proposal_description.values["seller_tx_fee"]
        # )
        goods_component = copy.copy(proposal_description.values)
        [  # pylint: disable=expression-not-assigned
            goods_component.pop(key)
            for key in [
                "seller_tx_fee",
                "buyer_tx_fee",
                "price",
                "currency_id",
                "tx_nonce",
            ]
        ]
        # switch signs based on whether seller or buyer role
        amount = (
            proposal_description.values["price"]
            if is_seller
            else -proposal_description.values["price"]
        )
        if is_seller:
            for good_id in goods_component.keys():
                goods_component[good_id] = goods_component[good_id] * (-1)
        tx_amount_by_currency_id = {proposal_description.values["currency_id"]: amount}
        tx_fee_by_currency_id = {proposal_description.values["currency_id"]: 1}
        tx_nonce = proposal_description.values["tx_nonce"]
        # need to hash positive.negative side separately
        tx_hash = tx_hash_from_values(
            tx_sender_addr=agent_addr,
            tx_counterparty_addr=dialogue_label.dialogue_opponent_addr,
            tx_quantities_by_good_id=goods_component,
            tx_amount_by_currency_id=tx_amount_by_currency_id,
            tx_nonce=tx_nonce,
        )
        skill_callback_ids = (
            (PublicId.from_str("fetchai/tac_participation:0.4.0"),)
            if performative == SigningMessage.Performative.SIGN_MESSAGE
            else (PublicId.from_str("fetchai/tac_negotiation:0.5.0"),)
        )
        transaction_msg = SigningMessage(
            performative=performative,
            skill_callback_ids=skill_callback_ids,
            # tx_id=self.get_internal_tx_id(),
            terms=Terms(
                ledger_id="ethereum",
                sender_address=agent_addr,
                counterparty_address=dialogue_label.dialogue_opponent_addr,
                amount_by_currency_id=tx_amount_by_currency_id,
                is_sender_payable_tx_fee=True,  # TODO: check!
                quantities_by_good_id=goods_component,
                nonce=tx_nonce,
                fee_by_currency_id=tx_fee_by_currency_id,
            ),
            skill_callback_info={"dialogue_label": dialogue_label.json},
            message=tx_hash,
        )
        return transaction_msg

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
                "[{}]: Removing transaction from pending list: {}".format(
                    self.context.agent_name, transaction_id
                )
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
        transaction_msg: SigningMessage,
    ) -> None:
        """
        Add a proposal (in the form of a transaction) to the pending list.

        :param dialogue_label: the dialogue label associated with the proposal
        :param proposal_id: the message id of the proposal
        :param transaction_msg: the transaction message
        :raise AssertionError: if the pending proposal is already present.

        :return: None
        """
        assert (
            dialogue_label not in self._pending_proposals
            and proposal_id not in self._pending_proposals[dialogue_label]
        )
        self._pending_proposals[dialogue_label][proposal_id] = transaction_msg

    def pop_pending_proposal(
        self, dialogue_label: DialogueLabel, proposal_id: int
    ) -> SigningMessage:
        """
        Remove a proposal (in the form of a transaction) from the pending list.

        :param dialogue_label: the dialogue label associated with the proposal
        :param proposal_id: the message id of the proposal
        :raise AssertionError: if the pending proposal is not present.

        :return: the transaction message
        """
        assert (
            dialogue_label in self._pending_proposals
            and proposal_id in self._pending_proposals[dialogue_label]
        )
        transaction_msg = self._pending_proposals[dialogue_label].pop(proposal_id)
        return transaction_msg

    def add_pending_initial_acceptance(
        self,
        dialogue_label: DialogueLabel,
        proposal_id: int,
        transaction_msg: SigningMessage,
    ) -> None:
        """
        Add an acceptance (in the form of a transaction) to the pending list.

        :param dialogue_label: the dialogue label associated with the proposal
        :param proposal_id: the message id of the proposal
        :param transaction_msg: the transaction message
        :raise AssertionError: if the pending acceptance is already present.

        :return: None
        """
        assert (
            dialogue_label not in self._pending_initial_acceptances
            and proposal_id not in self._pending_initial_acceptances[dialogue_label]
        )
        self._pending_initial_acceptances[dialogue_label][proposal_id] = transaction_msg

    def pop_pending_initial_acceptance(
        self, dialogue_label: DialogueLabel, proposal_id: int
    ) -> SigningMessage:
        """
        Remove an acceptance (in the form of a transaction) from the pending list.

        :param dialogue_label: the dialogue label associated with the proposal
        :param proposal_id: the message id of the proposal
        :raise AssertionError: if the pending acceptance is not present.

        :return: the transaction message
        """
        assert (
            dialogue_label in self._pending_initial_acceptances
            and proposal_id in self._pending_initial_acceptances[dialogue_label]
        )
        transaction_msg = self._pending_initial_acceptances[dialogue_label].pop(
            proposal_id
        )
        return transaction_msg

    def _register_transaction_with_time(self, transaction_id: str) -> None:
        """
        Register a transaction with a creation datetime.

        :param transaction_id: the transaction id

        :return: None
        """
        now = datetime.datetime.now()
        self._last_update_for_transactions.append((now, transaction_id))

    def add_locked_tx(
        self, transaction_msg: SigningMessage, role: Dialogue.Role
    ) -> None:
        """
        Add a lock (in the form of a transaction).

        :param transaction_msg: the transaction message
        :param role: the role of the agent (seller or buyer)
        :raise AssertionError: if the transaction is already present.

        :return: None
        """
        as_seller = role == Dialogue.Role.SELLER

        transaction_id = transaction_msg.dialogue_reference[0]  # TODO: fix
        assert transaction_id not in self._locked_txs
        self._register_transaction_with_time(transaction_id)
        self._locked_txs[transaction_id] = transaction_msg
        if as_seller:
            self._locked_txs_as_seller[transaction_id] = transaction_msg
        else:
            self._locked_txs_as_buyer[transaction_id] = transaction_msg

    def pop_locked_tx(self, transaction_msg: SigningMessage) -> SigningMessage:
        """
        Remove a lock (in the form of a transaction).

        :param transaction_msg: the transaction message
        :raise AssertionError: if the transaction with the given transaction id has not been found.

        :return: the transaction
        """
        transaction_id = transaction_msg.dialogue_reference[0]  # TODO: fix
        assert transaction_id in self._locked_txs
        transaction_msg = self._locked_txs.pop(transaction_id)
        self._locked_txs_as_buyer.pop(transaction_id, None)
        self._locked_txs_as_seller.pop(transaction_id, None)
        return transaction_msg

    def ownership_state_after_locks(self, is_seller: bool) -> OwnershipState:
        """
        Apply all the locks to the current ownership state of the agent.

        This assumes, that all the locked transactions will be successful.

        :param is_seller: Boolean indicating the role of the agent.

        :return: the agent state with the locks applied to current state
        """
        transaction_msgs = (
            list(self._locked_txs_as_seller.values())
            if is_seller
            else list(self._locked_txs_as_buyer.values())
        )
        ownership_state_after_locks = self.context.decision_maker_handler_context.ownership_state.apply_transactions(
            transaction_msgs
        )
        return ownership_state_after_locks
