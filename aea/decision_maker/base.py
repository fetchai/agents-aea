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
from enum import Enum
import math
import logging
from queue import Queue
from typing import Dict, List, Optional, cast

from aea.crypto.wallet import Wallet
from aea.crypto.ledger_apis import LedgerApis
from aea.decision_maker.messages.transaction import TransactionMessage
from aea.decision_maker.messages.state_update import StateUpdateMessage
from aea.helpers.preference_representations.base import logarithmic_utility, linear_utility
from aea.mail.base import OutBox  # , Envelope
from aea.protocols.base import Message

CurrencyEndowment = Dict[str, int]  # a map from identifier to quantity
CurrencyHoldings = Dict[str, int]
GoodEndowment = Dict[str, int]   # a map from identifier to quantity
GoodHoldings = Dict[str, int]
UtilityParams = Dict[str, float]   # a map from identifier to quantity
ExchangeParams = Dict[str, float]   # a map from identifier to quantity

SENDER_TX_SHARE = 0.5
QUANTITY_SHIFT = 100
INTERNAL_PROTOCOL_ID = 'internal'

logger = logging.getLogger(__name__)


class GoalPursuitReadiness:
    """The goal pursuit readiness."""

    class Status(Enum):
        """The enum of status."""

        READY = 'ready'
        NOT_READY = 'not_ready'

    def __init__(self):
        """Instantiate an ownership state object."""
        self._status = GoalPursuitReadiness.Status.NOT_READY

    @property
    def is_ready(self) -> bool:
        """Get the readiness."""
        return self._status.value == GoalPursuitReadiness.Status.READY.value

    def update(self, new_status: Status) -> None:
        """Update the goal pursuit readiness."""
        self._status = new_status


class OwnershipState:
    """Represent the ownership state of an agent."""

    def __init__(self):
        """Instantiate an ownership state object."""
        self._amount_by_currency = None  # type: CurrencyHoldings
        self._quantities_by_good_pbk = None  # type: GoodHoldings

    def init(self, amount_by_currency: CurrencyEndowment, quantities_by_good_pbk: GoodEndowment, agent_name: str = ''):
        """
        Instantiate an ownership state object.

        :param amount_by_currency: the currency endowment of the agent in this state.
        :param quantities_by_good_pbk: the good endowment of the agent in this state.
        :param agent_name: the agent name
        """
        logger.warning("[{}]: Careful! OwnershipState are being initialized!".format(agent_name))
        self._amount_by_currency = copy.copy(amount_by_currency)
        self._quantities_by_good_pbk = copy.copy(quantities_by_good_pbk)

    @property
    def is_initialized(self) -> bool:
        """Get the initialization status."""
        return self._amount_by_currency is not None and self._quantities_by_good_pbk is not None

    @property
    def amount_by_currency(self) -> CurrencyHoldings:
        """Get currency holdings in this state."""
        assert self._amount_by_currency is not None, "CurrencyHoldings not set!"
        return copy.copy(self._amount_by_currency)

    @property
    def quantities_by_good_pbk(self) -> GoodHoldings:
        """Get good holdings in this state."""
        assert self._quantities_by_good_pbk is not None, "GoodHoldings not set!"
        return copy.copy(self._quantities_by_good_pbk)

    def check_transaction_is_consistent(self, tx_message: TransactionMessage) -> bool:
        """
        Check if the transaction is consistent.

        E.g. check that the agent state has enough money if it is a buyer
        or enough holdings if it is a seller.
        :return: True if the transaction is legal wrt the current state, false otherwise.
        """
        currency_pbk = cast(str, tx_message.get("currency_pbk"))
        if tx_message.get("is_sender_buyer"):
            # check if we have the money to cover amount and tx fee.
            result = self.amount_by_currency[currency_pbk] >= cast(int, tx_message.get("amount")) + cast(int, tx_message.get("sender_tx_fee"))
        else:
            # check if we have the goods.
            result = True
            quantities_by_good_pbk = cast(Dict[str, int], tx_message.get("quantities_by_good_pbk"))
            for good_pbk, quantity in quantities_by_good_pbk.items():
                result = result and (self.quantities_by_good_pbk[good_pbk] >= quantity)
            # check if we have the money to cover tx fee.
            result = self.amount_by_currency[currency_pbk] + cast(int, tx_message.get("amount")) >= cast(int, tx_message.get("sender_tx_fee"))
        return result

    def apply_state_update(self, amount_deltas_by_currency: Dict[str, int], quantity_deltas_by_good_pbk: Dict[str, int]) -> 'OwnershipState':
        """
        Apply a list of transactions to the current state.

        :param amount_deltas_by_currency: the delta in the currency amounts
        :param quantity_deltas_by_good_pbk: the delta in the quantities by good
        :return: the final state.
        """
        new_state = copy.copy(self)

        for currency, amount_delta in amount_deltas_by_currency.items():
            new_state._amount_by_currency[currency] += amount_delta

        for good_pbk, quantity_delta in quantity_deltas_by_good_pbk.items():
            new_state._quantities_by_good_pbk[good_pbk] += quantity_delta

        return new_state

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

        :param tx_message:
        :return: None
        """
        currency_pbk = cast(str, tx_message.get("currency_pbk"))
        if tx_message.get("is_sender_buyer"):
            diff = cast(int, tx_message.get("amount")) + cast(int, tx_message.get("sender_tx_fee"))
            self._amount_by_currency[currency_pbk] -= diff
        else:
            diff = cast(int, tx_message.get("amount")) - cast(int, tx_message.get("sender_tx_fee"))
            self._amount_by_currency[currency_pbk] += diff

        quantities_by_good_pbk = cast(Dict[str, int], tx_message.get("quantities_by_good_pbk"))
        for good_pbk, quantity in quantities_by_good_pbk.items():
            quantity_delta = quantity if tx_message.get("is_sender_buyer") else -quantity
            self._quantities_by_good_pbk[good_pbk] += quantity_delta

    def __copy__(self):
        """Copy the object."""
        state = OwnershipState()
        if self.amount_by_currency is not None and self.quantities_by_good_pbk is not None:
            state._amount_by_currency = self.amount_by_currency
            state._quantities_by_good_pbk = self.quantities_by_good_pbk
        return state


class Preferences:
    """Class to represent the preferences."""

    def __init__(self):
        """Instantiate an agent preference object."""
        self._exchange_params_by_currency = None  # type: ExchangeParams
        self._utility_params_by_good_pbk = None  # type: UtilityParams
        self._transaction_fees = None  # type: Dict[str, int]
        self._quantity_shift = QUANTITY_SHIFT

    def init(self, exchange_params_by_currency: ExchangeParams, utility_params_by_good_pbk: UtilityParams, tx_fee: int, agent_name: str = ''):
        """
        Instantiate an agent preference object.

        :param exchange_params_by_currency: the exchange params.
        :param utility_params_by_good_pbk: the utility params for every asset.
        :param agent_name: the agent name
        """
        logger.warning("[{}]: Careful! Preferences are being initialized!".format(agent_name))
        self._exchange_params_by_currency = exchange_params_by_currency
        self._utility_params_by_good_pbk = utility_params_by_good_pbk
        self._transaction_fees = self._split_tx_fees(tx_fee)

    @property
    def is_initialized(self) -> bool:
        """Get the initialization status."""
        return (self._exchange_params_by_currency is not None) and \
            (self._utility_params_by_good_pbk is not None) and \
            (self._transaction_fees is not None)

    @property
    def exchange_params_by_currency(self) -> ExchangeParams:
        """Get exchange parameter for each currency."""
        assert self._exchange_params_by_currency is not None, "ExchangeParams not set!"
        return self._exchange_params_by_currency

    @property
    def utility_params_by_good_pbk(self) -> UtilityParams:
        """Get utility parameter for each good."""
        assert self._utility_params_by_good_pbk is not None, "UtilityParams not set!"
        return self._utility_params_by_good_pbk

    @property
    def transaction_fees(self) -> Dict[str, int]:
        """Get the transaction fee."""
        assert self._transaction_fees is not None, "Transaction fee not set!"
        return self._transaction_fees

    def logarithmic_utility(self, quantities_by_good_pbk: GoodHoldings) -> float:
        """
        Compute agent's utility given her utility function params and a good bundle.

        :param quantities_by_good_pbk: the good holdings (dictionary) with the identifier (key) and quantity (value) for each good
        :return: utility value
        """
        result = logarithmic_utility(self.utility_params_by_good_pbk, quantities_by_good_pbk, self._quantity_shift)
        return result

    def linear_utility(self, amount_by_currency: CurrencyHoldings) -> float:
        """
        Compute agent's utility given her utility function params and a currency bundle.

        :param amount_by_currency: the currency holdings (dictionary) with the identifier (key) and quantity (value) for each currency
        :return: utility value
        """
        result = linear_utility(self.exchange_params_by_currency, amount_by_currency)
        return result

    def get_score(self, quantities_by_good_pbk: GoodHoldings, amount_by_currency: CurrencyHoldings) -> float:
        """
        Compute the score given the good and currency holdings.

        :param quantities_by_good_pbk: the good holdings
        :param currency_holdings: the currency holdings
        :return: the score.
        """
        goods_score = self.logarithmic_utility(quantities_by_good_pbk)
        currency_score = self.linear_utility(amount_by_currency)
        score = goods_score + currency_score
        return score

    def marginal_utility(self, ownership_state: OwnershipState, delta_good_holdings: Optional[GoodHoldings] = None, delta_currency_holdings: Optional[CurrencyHoldings] = None) -> float:
        """
        Compute the marginal utility.

        :param ownership_state: the current ownership state
        :param delta_good_holdings: the change in good holdings
        :param delta_currency_holdings: the change in money holdings
        :return: the marginal utility score
        """
        current_goods_score = self.logarithmic_utility(ownership_state.quantities_by_good_pbk)
        current_currency_score = self.linear_utility(ownership_state.amount_by_currency)
        new_goods_score = current_goods_score
        new_currency_score = current_currency_score
        if delta_good_holdings is not None:
            new_quantities_by_good_pbk = {good_pbk: quantity + delta_good_holdings[good_pbk] for good_pbk, quantity in ownership_state.quantities_by_good_pbk.items()}
            new_goods_score = self.logarithmic_utility(new_quantities_by_good_pbk)
        if delta_currency_holdings is not None:
            new_amount_by_currency = {currency: amount + delta_currency_holdings[currency] for currency, amount in ownership_state.amount_by_currency.items()}
            new_currency_score = self.linear_utility(new_amount_by_currency)
        return new_goods_score + new_currency_score - current_goods_score - current_currency_score

    def get_score_diff_from_transaction(self, ownership_state: OwnershipState, tx_message: TransactionMessage) -> float:
        """
        Simulate a transaction and get the resulting score (taking into account the fee).

        :param tx_message: a transaction object.
        :return: the score.
        """
        current_score = self.get_score(quantities_by_good_pbk=ownership_state.quantities_by_good_pbk,
                                       amount_by_currency=ownership_state.amount_by_currency)
        new_ownership_state = ownership_state.apply([tx_message])
        new_score = self.get_score(quantities_by_good_pbk=new_ownership_state.quantities_by_good_pbk,
                                   amount_by_currency=new_ownership_state.amount_by_currency)
        return new_score - current_score

    def _split_tx_fees(self, tx_fee: int) -> Dict[str, int]:
        """
        Split the transaction fee.

        :param tx_fee: the tx fee
        :return: the split into buyer and seller part
        """
        buyer_part = math.ceil(tx_fee * SENDER_TX_SHARE)
        seller_part = math.ceil(tx_fee * (1 - SENDER_TX_SHARE))
        if buyer_part + seller_part > tx_fee:
            seller_part -= 1
        return {'seller_tx_fee': seller_part, 'buyer_tx_fee': buyer_part}


class DecisionMaker:
    """This class implements the decision maker."""

    def __init__(self, agent_name: str, max_reactions: int, outbox: OutBox, wallet: Wallet, ledger_apis: LedgerApis):
        """
        Initialize the decision maker.

        :param agent_name: the name of the agent
        :param max_reactions: the processing rate of messages per iteration.
        :param outbox: the outbox
        :param wallet: the wallet
        :param ledger_apis: the ledger apis
        """
        self._max_reactions = max_reactions
        self._agent_name = agent_name
        self._outbox = outbox
        self._wallet = wallet
        self._ledger_apis = ledger_apis
        self._message_in_queue = Queue()  # type: Queue
        self._message_out_queue = Queue()  # type: Queue
        self._ownership_state = OwnershipState()
        self._preferences = Preferences()
        self._goal_pursuit_readiness = GoalPursuitReadiness()

    @property
    def message_in_queue(self) -> Queue:
        """Get (in) queue."""
        return self._message_in_queue

    @property
    def message_out_queue(self) -> Queue:
        """Get (out) queue."""
        return self._message_out_queue

    @property
    def ledger_apis(self) -> LedgerApis:
        """Get outbox."""
        return self._ledger_apis

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
    def goal_pursuit_readiness(self) -> GoalPursuitReadiness:
        """Get readiness of agent to pursuit its goals."""
        return self._goal_pursuit_readiness

    def execute(self) -> None:
        """
        Execute the decision maker.

        :return: None
        """
        while not self.message_in_queue.empty():
            message = self.message_in_queue.get_nowait()  # type: Optional[Message]
            if message is not None:
                if message.protocol_id == INTERNAL_PROTOCOL_ID:
                    self.handle(message)
                else:
                    logger.warning("[{}]: Message received by the decision maker is not of protocol_id=internal.".format(self._agent_name))

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
        if not self.goal_pursuit_readiness.is_ready:
            logger.warning("[{}]: Preferences and ownership state not initialized. Refusing to process transaction!".format(self._agent_name))
            return

        # check if the transaction is acceptable and process it accordingly
        if self._is_acceptable_tx(tx_message):
            tx_digest = self._settle_tx(tx_message)
            if tx_digest is not None:
                tx_message_response = TransactionMessage.respond_with(tx_message,
                                                                      performative=TransactionMessage.Performative.ACCEPT,
                                                                      transaction_digest=tx_digest)
            else:
                tx_message_response = TransactionMessage.respond_with(tx_message,
                                                                      performative=TransactionMessage.Performative.REJECT)
        else:
            tx_message_response = TransactionMessage.respond_with(tx_message,
                                                                  performative=TransactionMessage.Performative.REJECT)
        self.message_out_queue.put(tx_message_response)

    def _is_acceptable_tx(self, tx_message: TransactionMessage) -> bool:
        """
        Check if the tx is acceptable.

        :param tx_message: the transaction message
        :return: whether the transaction is acceptable or not
        """
        if tx_message.get("ledger_id") is not None:
            amount = cast(int, tx_message.get("amount"))
            counterparty_tx_fee = cast(int, tx_message.get("counterparty_tx_fee"))
            sender_tx_fee = cast(int, tx_message.get("sender_tx_fee"))
            # adjust payment amount to reflect transaction fee split
            amount -= counterparty_tx_fee
            tx_fee = counterparty_tx_fee + sender_tx_fee
            payable = amount + tx_fee
            is_correct_format = isinstance(payable, int)
            crypto_object = self._wallet.crypto_objects.get(tx_message.get("ledger_id"))
            balance = self.ledger_apis.token_balance(crypto_object.identifier, cast(str, crypto_object.address))
            is_affordable = payable <= balance
            # TODO check against preferences and other constraints
            is_acceptable = is_correct_format and is_affordable
        else:
            is_acceptable = self.preferences.get_score_diff_from_transaction(self.ownership_state, tx_message) >= 0.0
        return is_acceptable

    def _settle_tx(self, tx_message: TransactionMessage) -> Optional[str]:
        """
        Settle the tx.

        :param tx_message: the transaction message
        :return: the transaction digest
        """
        logger.info("[{}]: Settling transaction!".format(self._agent_name))
        if tx_message.get("ledger_id") is not None:
            amount = cast(int, tx_message.get("amount"))
            counterparty_tx_fee = cast(int, tx_message.get("counterparty_tx_fee"))
            sender_tx_fee = cast(int, tx_message.get("sender_tx_fee"))
            counterparty_address = cast(str, tx_message.get("counterparty"))
            # adjust payment amount to reflect transaction fee split
            amount -= counterparty_tx_fee
            tx_fee = counterparty_tx_fee + sender_tx_fee
            crypto_object = self._wallet.crypto_objects.get(tx_message.get("ledger_id"))
            tx_digest = self.ledger_apis.transfer(crypto_object.identifier, crypto_object, counterparty_address, amount, tx_fee)
        else:
            tx_digest = cast(str, tx_message.get("transaction_id"))
        return tx_digest

    def _handle_state_update_message(self, state_update_message: StateUpdateMessage) -> None:
        """
        Handle a state update message.

        :param state_update_message: the state update message
        :return: None
        """
        performative = state_update_message.get("performative")
        if performative == StateUpdateMessage.Performative.INITIALIZE:
            amount_by_currency = cast(Dict[str, int], state_update_message.get("amount_by_currency"))
            quantities_by_good_pbk = cast(Dict[str, int], state_update_message.get("quantities_by_good_pbk"))
            self.ownership_state.init(amount_by_currency=amount_by_currency, quantities_by_good_pbk=quantities_by_good_pbk, agent_name=self._agent_name)
            exchange_params_by_currency = cast(Dict[str, float], state_update_message.get("exchange_params_by_currency"))
            utility_params_by_good_pbk = cast(Dict[str, float], state_update_message.get("utility_params_by_good_pbk"))
            tx_fee = cast(int, state_update_message.get("tx_fee"))
            self.preferences.init(exchange_params_by_currency=exchange_params_by_currency, utility_params_by_good_pbk=utility_params_by_good_pbk, tx_fee=tx_fee, agent_name=self._agent_name)
            self.goal_pursuit_readiness.update(GoalPursuitReadiness.Status.READY)
        elif performative == StateUpdateMessage.Performative.APPLY:
            amount_by_currency = cast(Dict[str, int], state_update_message.get("amount_by_currency"))
            quantities_by_good_pbk = cast(Dict[str, int], state_update_message.get("quantities_by_good_pbk"))
            new_ownership_state = self.ownership_state.apply_state_update(amount_deltas_by_currency=amount_by_currency, quantity_deltas_by_good_pbk=quantities_by_good_pbk)
            self._ownership_state = new_ownership_state
