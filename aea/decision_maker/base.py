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

import copy
import math
from queue import Queue
from typing import Dict, List, Optional

from aea.mail.base import OutBox, Envelope
from aea.protocols.base import Message
from aea.protocols.transaction import TransactionMessage
from aea.protocols.state_update import StateUpdateMessage

CurrencyEndowment = Dict[str, float]  # a map from identifier to quantity
GoodEndowment = Dict[str, int]   # a map from identifier to quantity
UtilityParams = Dict[str, float]   # a map from identifier to quantity
ExchangeParams = Dict[str, float]   # a map from identifier to quantity

QUANTITY_SHIFT = 100


class Preferences:
    """Class to represent the preferences."""

    def __init__(self, utility_params: UtilityParams, exchange_params: ExchangeParams):
        """
        Instantiate an agent preference object.

        :param utility_params: the utility params for every asset.
        """
        self._utility_params = utility_params
        self._exchange_params = exchange_params
        self._quantity_shift = QUANTITY_SHIFT

    @property
    def utility_params(self) -> UtilityParams:
        """Get utility parameter for each good."""
        return self._utility_params

    @property
    def exchange_params(self) -> ExchangeParams:
        """Get exchange parameter for each currency."""
        return self._exchange_params

    @property
    def quantity_shift(self) -> int:
        """Get utility parameter for each good."""
        return self._quantity_shift

    def logarithmic_utility(self, good_bundle: Dict[str, int]) -> float:
        """
        Compute agent's utility given her utility function params and a good bundle.

        :param good_bundle: a bundle of goods (dictionary) with the identifier (key) and quantity (value) for each good
        :return: utility value
        """
        goodwise_utility = [self.utility_params[good_pbk] * math.log(quantity + self.quantity_shift) if quantity + self.quantity_shift > 0 else -10000
                            for good_pbk, quantity in good_bundle.items()]
        return sum(goodwise_utility)

    def linear_utility(self, currency_bundle: Dict[str, int]) -> float:
        """
        Compute agent's utility given her utility function params and a currency bundle.

        :param currency_bundle: a bundle of currencies (dictionary) with the identifier (key) and quantity (value) for each good
        :return: utility value
        """
        currencywise_utility = [self.exchange_params[currency_pbk] for currency_pbk, quantity in currency_bundle.items()]
        return sum(currencywise_utility)

    def get_score(self, good_bundle: Dict[str, int], currency_bundle: Dict[str, float]) -> float:
        """
        Compute the score of the current state.

        The score is computed as the sum of all the utilities for the good holdings
        with positive quantity plus the money left.
        :return: the score.
        """
        goods_score = self.logarithmic_utility(good_bundle)
        currency_score = self.linear_utility(currency_bundle)
        score = goods_score + currency_score
        return score


class OwnershipState:
    """Represent the ownership state of an agent."""

    def __init__(self, currency_endowment: CurrencyEndowment, good_endowment: GoodEndowment):
        """
        Instantiate an ownership state object.

        :param currency_endowment: the currency endowment of the agent in this state.
        :param good_endowment: the good endowment of the agent in this state.
        """
        self._currency_holdings = copy.copy(currency_endowment)
        self._good_holdings = copy.copy(good_endowment)

    @property
    def currency_holdings(self):
        """Get currency holdings in this state."""
        return copy.copy(self._currency_holdings)

    @property
    def good_holdings(self):
        """Get good holdings in this state."""
        return copy.copy(self._good_holdings)

    def check_transaction_is_consistent(self, tx_message: TransactionMessage) -> bool:
        """
        Check if the transaction is consistent.

        E.g. check that the agent state has enough money if it is a buyer
        or enough holdings if it is a seller.
        :return: True if the transaction is legal wrt the current state, false otherwise.
        """
        currency_pbk = tx_message.get("currency_pbk")
        if tx_message.get("is_sender_buyer"):
            # check if we have the money.
            result = self.currency_holdings[currency_pbk] >= tx_message.get("amount") + tx_message.get("fee_buyer")
        else:
            # check if we have the goods.
            result = True
            quantities_by_good_pbk = tx_message.get("quantities_by_good_pbk")
            for good_pbk, quantity in quantities_by_good_pbk.items():
                result = result and (self.current_holdings[good_pbk] >= quantity)
        return result

    def apply(self, transactions: List[TransactionMessage]) -> 'OwnershipState':
        """
        Apply a list of transactions to the current state.

        :param transactions: the sequence of transaction messages.
        :return: the final state.
        """
        new_state = copy.copy(self)
        for tx_message in transactions:
            new_state.update(tx_message)

        return new_state

    def update(self, tx_message: TransactionMessage) -> None:
        """
        Update the agent state from a transaction.

        :param tx: the transaction.
        :param tx_fee: the transaction fee.
        :return: None
        """
        currency_pbk = tx_message.get("currency_pbk")
        if tx_message.get("is_sender_buyer"):
            diff = tx_message.get("amount") + tx_message.get("fee_buyer")
            self._currency_holdings[currency_pbk] -= diff
        else:
            diff = tx_message.get("amount") - tx_message.get("fee_buyer")
            self._currency_holdings[currency_pbk] += diff

        quantities_by_good_pbk = tx_message.get("quantities_by_good_pbk")
        for good_pbk, quantity in quantities_by_good_pbk.items():
            quantity_delta = quantity if tx_message.get("is_sender_buyer") else -quantity
            self._good_holdings[good_pbk] += quantity_delta

    def __copy__(self):
        """Copy the object."""
        return OwnershipState(self.currency_holdings, self.good_holdings)


class DecisionMaker:
    """This class implements the decision maker."""

    def __init__(self, max_reactions: int, outbox: OutBox):
        """
        Initialize the decision maker.

        :param max_reactions: the processing rate of messages per iteration.
        :param outbox: the outbox
        """
        self.max_reactions = max_reactions
        self._outbox = outbox
        self._message_queue = Queue()  # type: Queue
        self._ownership_state = None  # type: Optional[OwnershipState]
        self._preferences = None  # type: Optional[Preferences]

    @property
    def message_queue(self) -> Queue:
        """Get (in) queue."""
        return self._message_queue

    @property
    def outbox(self) -> OutBox:
        """Get outbox."""
        return self._outbox

    @property
    def ownership_state(self) -> OwnershipState:
        """Get ownership state."""
        assert self._ownership_state is not None, "OwnershipState not set!"
        return self._ownership_state

    @property
    def preferences(self) -> Preferences:
        """Get preferences."""
        assert self._preferences is not None, "Preferences not set!"
        return self._preferences

    def execute(self) -> None:
        """
        Execute the decision maker.

        :return: None
        """
        counter = 0
        while not self.message_queue.empty() and counter < self.max_reactions:
            counter += 1
            message = self.message_queue.get_nowait()  # type: Optional[Message]
            if message is not None:
                self.handle(message)

    def handle(self, message: Message) -> None:
        """
        Handle a message.

        :param message: the message
        :return: None
        """
        if type(message) == TransactionMessage:
            self._handle_tx_message(message)
        elif type(message) == StateUpdateMessage:
            self._handle_state_update_message(message)

    def _handle_tx_message(self, tx_message: TransactionMessage) -> None:
        """
        Handle a transaction messae.

        :param tx_message: the transaction message
        :return: None
        """
        score_diff = self._get_score_diff_from_transaction
        if score_diff >= 0:
            envelope = Envelope()
            self.outbox.put(envelope)

    def _get_score_diff_from_transaction(self, tx_message: TransactionMessage) -> float:
        """
        Simulate a transaction and get the resulting score (taking into account the fee).

        :param tx: a transaction object.
        :return: the score.
        """
        current_score = self.get_score(good_bundle=tx_message.good_bundle)
        new_state = self.apply([tx_message])
        new_score = new_state.get_score()
        return new_score - current_score

    def _handle_state_update_message(self, state_update_message: StateUpdateMessage) -> None:
        """
        Handle a transaction messae.

        :param state_update_message: the state update message
        :return: None
        """
        pass
