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
import logging
import math
from queue import Queue
from typing import Dict, List, Optional, cast

from aea.decision_maker.messages.transaction import TransactionMessage
from aea.decision_maker.messages.state_update import StateUpdateMessage
from aea.mail.base import OutBox  # , Envelope
from aea.protocols.base import Message

CurrencyEndowment = Dict[str, float]  # a map from identifier to quantity
CurrencyHoldings = Dict[str, float]
GoodEndowment = Dict[str, int]   # a map from identifier to quantity
GoodHoldings = Dict[str, int]
UtilityParams = Dict[str, float]   # a map from identifier to quantity
ExchangeParams = Dict[str, float]   # a map from identifier to quantity

QUANTITY_SHIFT = 100

logger = logging.getLogger(__name__)


class OwnershipState:
    """Represent the ownership state of an agent."""

    def __init__(self):
        """Instantiate an ownership state object."""
        self._currency_holdings = None  # type: CurrencyHoldings
        self._good_holdings = None  # type: GoodHoldings

    def init(self, currency_endowment: CurrencyEndowment, good_endowment: GoodEndowment):
        """
        Instantiate an ownership state object.

        :param currency_endowment: the currency endowment of the agent in this state.
        :param good_endowment: the good endowment of the agent in this state.
        """
        logger.warning("Careful! OwnershipState is being updated!")
        self._currency_holdings = copy.copy(currency_endowment)
        self._good_holdings = copy.copy(good_endowment)

    @property
    def currency_holdings(self) -> CurrencyHoldings:
        """Get currency holdings in this state."""
        assert self._currency_holdings is not None, "CurrencyHoldings not set!"
        return copy.copy(self._currency_holdings)

    @property
    def good_holdings(self) -> GoodHoldings:
        """Get good holdings in this state."""
        assert self._good_holdings is not None, "GoodHoldings not set!"
        return copy.copy(self._good_holdings)

    def check_transaction_is_consistent(self, tx_message: TransactionMessage) -> bool:
        """
        Check if the transaction is consistent.

        E.g. check that the agent state has enough money if it is a buyer
        or enough holdings if it is a seller.
        :return: True if the transaction is legal wrt the current state, false otherwise.
        """
        import pdb; pdb.set_trace()
        currency_pbk = tx_message.get("currency")
        currency_pbk = cast(str, currency_pbk)
        if tx_message.get("is_sender_buyer"):
            # check if we have the money to cover amount and tx fee.
            result = self.currency_holdings[currency_pbk] >= cast(float, tx_message.get("amount")) + cast(float, tx_message.get("sender_tx_fee"))
        else:
            # check if we have the goods.
            result = True
            quantities_by_good_pbk = tx_message.get("quantities_by_good_pbk")
            quantities_by_good_pbk = cast(Dict[str, int], quantities_by_good_pbk)
            for good_pbk, quantity in quantities_by_good_pbk.items():
                result = result and (self.currency_holdings[good_pbk] >= quantity)
            # check if we have the money to cover tx fee.
            result = self.currency_holdings[currency_pbk] + cast(float, tx_message.get("amount")) >= cast(float, tx_message.get("sender_tx_fee"))
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
        currency_pbk = tx_message.get("currency")
        currency_pbk = cast(str, currency_pbk)
        if tx_message.get("is_sender_buyer"):
            diff = cast(float, tx_message.get("amount")) + cast(float, tx_message.get("sender_tx_fee"))
            self._currency_holdings[currency_pbk] -= diff
        else:
            diff = cast(float, tx_message.get("amount")) - cast(float, tx_message.get("sender_tx_fee"))
            self._currency_holdings[currency_pbk] += diff

        quantities_by_good_pbk = tx_message.get("quantities_by_good_pbk")
        quantities_by_good_pbk = cast(Dict[str, int], quantities_by_good_pbk)
        for good_pbk, quantity in quantities_by_good_pbk.items():
            quantity_delta = quantity if tx_message.get("is_sender_buyer") else -quantity
            self._good_holdings[good_pbk] += quantity_delta

    def __copy__(self):
        """Copy the object."""
        return OwnershipState(self.currency_holdings, self.good_holdings)


class Preferences:
    """Class to represent the preferences."""

    def __init__(self):
        """Instantiate an agent preference object."""
        self._utility_params = None  # type: UtilityParams
        self._exchange_params = None  # type: ExchangeParams
        self._quantity_shift = QUANTITY_SHIFT

    def init(self, utility_params: UtilityParams, exchange_params: ExchangeParams):
        """
        Instantiate an agent preference object.

        :param utility_params: the utility params for every asset.
        :param exchange_params: the exchange params.
        """
        logger.warning("Careful! Preferences are being updated!")
        self._utility_params = utility_params
        self._exchange_params = exchange_params

    @property
    def utility_params(self) -> UtilityParams:
        """Get utility parameter for each good."""
        assert self._utility_params is not None, "UtilityParams not set!"
        return self._utility_params

    @property
    def exchange_params(self) -> ExchangeParams:
        """Get exchange parameter for each currency."""
        assert self._exchange_params is not None, "ExchangeParams not set!"
        return self._exchange_params

    def logarithmic_utility(self, good_holdings: GoodHoldings) -> float:
        """
        Compute agent's utility given her utility function params and a good bundle.

        :param good_holdings: the good holdings (dictionary) with the identifier (key) and quantity (value) for each good
        :return: utility value
        """
        goodwise_utility = [self.utility_params[good_pbk] * math.log(quantity + self._quantity_shift) if quantity + self._quantity_shift > 0 else -10000
                            for good_pbk, quantity in good_holdings.items()]
        return sum(goodwise_utility)

    def linear_utility(self, currency_holdings: CurrencyHoldings) -> float:
        """
        Compute agent's utility given her utility function params and a currency bundle.

        :param currency_holdings: the currency holdings (dictionary) with the identifier (key) and quantity (value) for each currency
        :return: utility value
        """
        currencywise_utility = [self.exchange_params[currency_pbk] for currency_pbk, quantity in currency_holdings.items()]
        return sum(currencywise_utility)

    def get_score(self, good_holdings: GoodHoldings, currency_holdings: CurrencyHoldings) -> float:
        """
        Compute the score given the good and currency holdings.

        :param good_holdings: the good holdings
        :param currency_holdings: the currency holdings
        :return: the score.
        """
        goods_score = self.logarithmic_utility(good_holdings)
        currency_score = self.linear_utility(currency_holdings)
        score = goods_score + currency_score
        return score

    def marginal_utility(self, ownership_state: OwnershipState, delta_good_holdings: GoodHoldings) -> float:
        """
        Compute the marginal utility.

        :return: the marginal utility score
        """
        pass

    def get_score_diff_from_transaction(self, ownership_state: OwnershipState, tx_message: TransactionMessage) -> float:
        """
        Simulate a transaction and get the resulting score (taking into account the fee).

        :param tx_message: a transaction object.
        :return: the score.
        """
        current_score = self.get_score(good_holdings=ownership_state.good_holdings,
                                       currency_holdings=ownership_state.currency_holdings)
        new_ownership_state = ownership_state.apply([tx_message])
        new_score = self.get_score(good_holdings=new_ownership_state.good_holdings,
                                   currency_holdings=new_ownership_state.currency_holdings)
        return new_score - current_score


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
        self._ownership_state = OwnershipState()
        self._preferences = Preferences()
        self._is_ready_to_pursuit_goals = False

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
        return self._ownership_state

    @property
    def preferences(self) -> Preferences:
        """Get preferences."""
        return self._preferences

    @property
    def is_ready_to_pursuit_goals(self) -> bool:
        """Get readiness of agent to pursuit its goals."""
        return self._is_ready_to_pursuit_goals

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
        if isinstance(message, TransactionMessage):
            self._handle_tx_message(message)
        elif isinstance(message, StateUpdateMessage):
            self._handle_state_update_message(message)

    def _handle_tx_message(self, tx_message: TransactionMessage) -> None:
        """
        Handle a transaction message.

        :param tx_message: the transaction message
        :return: None
        """
        score_diff = self.preferences.get_score_diff_from_transaction(self.ownership_state, tx_message)
        if score_diff >= 0.0:
            pass  # TODO: implement tx flow
            # envelope = Envelope()
            # self.outbox.put(envelope)

    def _handle_state_update_message(self, state_update_message: StateUpdateMessage) -> None:
        """
        Handle a state update message.

        :param state_update_message: the state update message
        :return: None
        """
        assert self._ownership_state is None, "OwnershipState already initialized."
        assert self._preferences is None, "Preferences already initialized."
        currency_endowment = cast(CurrencyEndowment, state_update_message.get("currency_endowment"))
        good_endowment = cast(GoodEndowment, state_update_message.get("good_endowment"))
        self.ownership_state.init(currency_endowment=currency_endowment, good_endowment=good_endowment)
        utility_params = cast(UtilityParams, state_update_message.get("utility_params"))
        exchange_params = cast(ExchangeParams, state_update_message.get("exchange_params"))
        self.preferences.init(exchange_params=exchange_params, utility_params=utility_params)
