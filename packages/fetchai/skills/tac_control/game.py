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

"""This package contains a class representing the game."""

import copy
import datetime
import pprint
from enum import Enum
from typing import Dict, List, Optional, cast

from eth_account.messages import encode_defunct

from hexbytes import HexBytes

from web3 import Web3

from aea.helpers.preference_representations.base import (
    linear_utility,
    logarithmic_utility,
)
from aea.mail.base import Address
from aea.skills.base import Model

from packages.fetchai.protocols.tac.message import TacMessage
from packages.fetchai.skills.tac_control.helpers import (
    determine_scaling_factor,
    generate_currency_endowments,
    generate_currency_id_to_name,
    generate_equilibrium_prices_and_holdings,
    generate_exchange_params,
    generate_good_endowments,
    generate_good_id_to_name,
    generate_utility_params,
    tx_hash_from_values,
)
from packages.fetchai.skills.tac_control.parameters import Parameters

GoodId = str
CurrencyId = str
Quantity = int
EquilibriumQuantity = float
Parameter = float
TransactionId = str
CurrencyEndowment = Dict[CurrencyId, Quantity]
ExchangeParams = Dict[CurrencyId, Parameter]
GoodEndowment = Dict[GoodId, Quantity]
UtilityParams = Dict[GoodId, Parameter]
EquilibriumCurrencyHoldings = Dict[CurrencyId, EquilibriumQuantity]
EquilibriumGoodHoldings = Dict[GoodId, EquilibriumQuantity]


class Phase(Enum):
    """This class defines the phases of the game."""

    PRE_GAME = "pre_game"
    GAME_REGISTRATION = "game_registration"
    GAME_SETUP = "game_setup"
    GAME = "game"
    POST_GAME = "post_game"


class Configuration:
    """Class containing the configuration of the game."""

    def __init__(
        self,
        version_id: str,
        tx_fee: int,
        agent_addr_to_name: Dict[Address, str],
        nb_goods: int,
    ):
        """
        Instantiate a game configuration.

        :param version_id: the version of the game.
        :param tx_fee: the fee for a transaction.
        :param agent_addr_to_name: a dictionary mapping agent addresses to agent names (as strings).
        :param nb_goods: the number of goods.
        """
        self._version_id = version_id
        self._tx_fee = tx_fee
        self._agent_addr_to_name = agent_addr_to_name
        self._currency_id_to_name = generate_currency_id_to_name()
        self._good_id_to_name = generate_good_id_to_name(nb_goods)
        self._check_consistency()

    @property
    def version_id(self) -> str:
        """Agent number of a TAC instance."""
        return self._version_id

    @property
    def tx_fee(self) -> int:
        """Transaction fee for the TAC instance."""
        return self._tx_fee

    @property
    def agent_addr_to_name(self) -> Dict[Address, str]:
        """Map agent addresses to names."""
        return self._agent_addr_to_name

    @property
    def currency_id_to_name(self) -> Dict[str, str]:
        """Map currency ids to names."""
        return self._currency_id_to_name

    @property
    def good_id_to_name(self) -> Dict[str, str]:
        """Map good ids to names."""
        return self._good_id_to_name

    def _check_consistency(self):
        """
        Check the consistency of the game configuration.

        :return: None
        :raises: AssertionError: if some constraint is not satisfied.
        """
        assert self.version_id is not None, "A version id must be set."
        assert self.tx_fee >= 0, "Tx fee must be non-negative."
        assert len(self.agent_addr_to_name) >= 2, "Must have at least two agents."
        assert len(self.good_id_to_name) >= 2, "Must have at least two goods."
        assert len(self.currency_id_to_name) == 1, "Must have exactly one currency."


class Initialization:
    """Class containing the initialization of the game."""

    def __init__(
        self,
        agent_addr_to_currency_endowments: Dict[Address, CurrencyEndowment],
        agent_addr_to_exchange_params: Dict[Address, ExchangeParams],
        agent_addr_to_good_endowments: Dict[Address, GoodEndowment],
        agent_addr_to_utility_params: Dict[Address, UtilityParams],
        good_id_to_eq_prices: Dict[GoodId, float],
        agent_addr_to_eq_good_holdings: Dict[Address, EquilibriumGoodHoldings],
        agent_addr_to_eq_currency_holdings: Dict[Address, EquilibriumCurrencyHoldings],
    ):
        """
        Instantiate a game initialization.

        :param agent_addr_to_currency_endowments: the currency endowments of the agents. A nested dict where the outer key is the agent id
                            and the inner key is the currency id.
        :param agent_addr_to_exchange_params: the exchange params representing the exchange rate the agetns use between currencies.
        :param agent_addr_to_good_endowments: the good endowments of the agents. A nested dict where the outer key is the agent id
                            and the inner key is the good id.
        :param agent_addr_to_utility_params: the utility params representing the preferences of the agents.
        :param good_id_to_eq_prices: the competitive equilibrium prices of the goods. A list.
        :param agent_addr_to_eq_good_holdings: the competitive equilibrium good holdings of the agents.
        :param agent_addr_to_eq_currency_holdings: the competitive equilibrium money holdings of the agents.
        """
        self._agent_addr_to_currency_endowments = agent_addr_to_currency_endowments
        self._agent_addr_to_exchange_params = agent_addr_to_exchange_params
        self._agent_addr_to_good_endowments = agent_addr_to_good_endowments
        self._agent_addr_to_utility_params = agent_addr_to_utility_params
        self._good_id_to_eq_prices = good_id_to_eq_prices
        self._agent_addr_to_eq_good_holdings = agent_addr_to_eq_good_holdings
        self._agent_addr_to_eq_currency_holdings = agent_addr_to_eq_currency_holdings
        self._check_consistency()

    @property
    def agent_addr_to_currency_endowments(self) -> Dict[Address, CurrencyEndowment]:
        """Get currency endowments of agents."""
        return self._agent_addr_to_currency_endowments

    @property
    def agent_addr_to_exchange_params(self) -> Dict[Address, ExchangeParams]:
        """Get exchange params of agents."""
        return self._agent_addr_to_exchange_params

    @property
    def agent_addr_to_good_endowments(self) -> Dict[Address, GoodEndowment]:
        """Get good endowments of the agents."""
        return self._agent_addr_to_good_endowments

    @property
    def agent_addr_to_utility_params(self) -> Dict[Address, UtilityParams]:
        """Get utility parameters of agents."""
        return self._agent_addr_to_utility_params

    @property
    def good_id_to_eq_prices(self) -> Dict[GoodId, float]:
        """Get theoretical equilibrium prices (a benchmark)."""
        return self._good_id_to_eq_prices

    @property
    def agent_addr_to_eq_good_holdings(self) -> Dict[Address, EquilibriumGoodHoldings]:
        """Get theoretical equilibrium good holdings (a benchmark)."""
        return self._agent_addr_to_eq_good_holdings

    @property
    def agent_addr_to_eq_currency_holdings(
        self,
    ) -> Dict[Address, EquilibriumCurrencyHoldings]:
        """Get theoretical equilibrium currency holdings (a benchmark)."""
        return self._agent_addr_to_eq_currency_holdings

    def _check_consistency(self):
        """
        Check the consistency of the game configuration.

        :return: None
        :raises: AssertionError: if some constraint is not satisfied.
        """
        assert all(
            c_e >= 0
            for currency_endowments in self.agent_addr_to_currency_endowments.values()
            for c_e in currency_endowments.values()
        ), "Currency endowments must be non-negative."
        assert all(
            p > 0
            for params in self.agent_addr_to_exchange_params.values()
            for p in params.values()
        ), "ExchangeParams must be strictly positive."
        assert all(
            g_e > 0
            for good_endowments in self.agent_addr_to_good_endowments.values()
            for g_e in good_endowments.values()
        ), "Good endowments must be strictly positive."
        assert all(
            p > 0
            for params in self.agent_addr_to_utility_params.values()
            for p in params.values()
        ), "UtilityParams must be strictly positive."
        assert len(self.agent_addr_to_good_endowments.keys()) == len(
            self.agent_addr_to_currency_endowments.keys()
        ), "Length of endowments must be the same."
        assert len(self.agent_addr_to_exchange_params.keys()) == len(
            self.agent_addr_to_utility_params.keys()
        ), "Length of params must be the same."
        assert all(
            len(self.good_id_to_eq_prices.values()) == len(eq_good_holdings)
            for eq_good_holdings in self.agent_addr_to_eq_good_holdings.values()
        ), "Length of eq_prices and an element of eq_good_holdings must be the same."
        assert len(self.agent_addr_to_eq_good_holdings.values()) == len(
            self.agent_addr_to_eq_currency_holdings.values()
        ), "Length of eq_good_holdings and eq_currency_holdings must be the same."
        assert all(
            len(self.agent_addr_to_exchange_params[agent_addr]) == len(endowments)
            for agent_addr, endowments in self.agent_addr_to_currency_endowments.items()
        ), "Dimensions for exchange_params and currency_endowments rows must be the same."
        assert all(
            len(self.agent_addr_to_utility_params[agent_addr]) == len(endowments)
            for agent_addr, endowments in self.agent_addr_to_good_endowments.items()
        ), "Dimensions for utility_params and good_endowments rows must be the same."


class Transaction:
    """Convenience representation of a transaction."""

    def __init__(
        self,
        transaction_id: TransactionId,
        sender_addr: Address,
        counterparty_addr: Address,
        amount_by_currency_id: Dict[str, int],
        sender_fee: int,
        counterparty_fee: int,
        quantities_by_good_id: Dict[str, int],
        nonce: int,
        sender_signature: str,
        counterparty_signature: str,
    ) -> None:
        """
        Instantiate transaction request.

        :param transaction_id: the id of the transaction.
        :param sender_addr: the sender of the transaction.
        :param tx_counterparty_addr: the counterparty of the transaction.
        :param amount_by_currency_id: the currency used.
        :param sender_fee: the transaction fee covered by the sender.
        :param counterparty_fee: the transaction fee covered by the counterparty.
        :param quantities_by_good_id: a map from good pbk to the quantity of that good involved in the transaction.
        :param nonce: the nonce of the transaction
        :param sender_signature: the signature of the transaction sender
        :param counterparty_signature: the signature of the transaction counterparty
        :return: None
        """
        self._id = transaction_id
        self._sender_addr = sender_addr
        self._counterparty_addr = counterparty_addr
        self._amount_by_currency_id = amount_by_currency_id
        self._sender_fee = sender_fee
        self._counterparty_fee = counterparty_fee
        self._quantities_by_good_id = quantities_by_good_id
        self._nonce = nonce
        self._sender_signature = sender_signature
        self._counterparty_signature = counterparty_signature
        self._check_consistency()

    @property
    def id(self) -> str:
        """Get the transaction id."""
        return self._id

    @property
    def sender_addr(self) -> Address:
        """Get the sender address."""
        return self._sender_addr

    @property
    def counterparty_addr(self) -> Address:
        """Get the counterparty address."""
        return self._counterparty_addr

    @property
    def amount_by_currency_id(self) -> Dict[CurrencyId, Quantity]:
        """Get the amount for each currency."""
        return copy.copy(self._amount_by_currency_id)

    @property
    def sender_fee(self) -> int:
        """Get the sender fee."""
        return self._sender_fee

    @property
    def counterparty_fee(self) -> int:
        """Get the counterparty fee."""
        return self._counterparty_fee

    @property
    def quantities_by_good_id(self) -> Dict[GoodId, Quantity]:
        """Get the quantities by good_id."""
        return copy.copy(self._quantities_by_good_id)

    @property
    def nonce(self) -> int:
        """Get the nonce of the transaction."""
        return self._nonce

    @property
    def sender_signature(self) -> str:
        """Get the sender signature."""
        return self._sender_signature

    @property
    def counterparty_signature(self) -> str:
        """Get the counterparty signature."""
        return self._counterparty_signature

    @property
    def is_sender_buyer(self) -> bool:
        """Get the sender is buyer status."""
        return all(value <= 0 for value in self.amount_by_currency_id.values())

    @property
    def buyer_addr(self) -> Address:
        """Get the buyer address."""
        return self._sender_addr if self.is_sender_buyer else self._counterparty_addr

    @property
    def sender_hash(self) -> bytes:
        """Get the sender hash."""
        return tx_hash_from_values(
            tx_sender_addr=self.sender_addr,
            tx_counterparty_addr=self.counterparty_addr,
            tx_quantities_by_good_id=self.quantities_by_good_id,
            tx_amount_by_currency_id=self.amount_by_currency_id,
            tx_nonce=self.nonce,
        )

    @property
    def counterparty_hash(self) -> bytes:
        """Get the sender hash."""
        return tx_hash_from_values(
            tx_sender_addr=self.counterparty_addr,
            tx_counterparty_addr=self.sender_addr,
            tx_quantities_by_good_id={
                good_id: -quantity
                for good_id, quantity in self.quantities_by_good_id.items()
            },
            tx_amount_by_currency_id={
                currency_id: -amount
                for currency_id, amount in self.amount_by_currency_id.items()
            },
            tx_nonce=self.nonce,
        )

    @property
    def amount(self) -> int:
        """Get the amount."""
        return list(self.amount_by_currency_id.values())[0]

    @property
    def currency_id(self) -> str:
        """Get the currency id."""
        return list(self.amount_by_currency_id.keys())[0]

    @property
    def sender_amount(self) -> int:
        """Get the amount the sender gets/pays."""
        return self.amount - self.sender_fee

    @property
    def counterparty_amount(self) -> int:
        """Get the amount the counterparty gets/pays."""
        return -self.amount - self.counterparty_fee

    def _check_consistency(self) -> None:
        """
        Check the consistency of the transaction parameters.

        :return: None
        :raises AssertionError if some constraint is not satisfied.
        """
        assert self.sender_addr != self.counterparty_addr
        assert (
            len(self.amount_by_currency_id.keys()) == 1
        )  # For now we restrict to one currency per transaction.
        assert self.sender_fee >= 0
        assert self.counterparty_fee >= 0
        assert (
            self.amount >= 0
            and all(quantity <= 0 for quantity in self.quantities_by_good_id.values())
        ) or (
            self.amount <= 0
            and all(quantity >= 0 for quantity in self.quantities_by_good_id.values())
        )
        assert isinstance(self.sender_signature, str) and isinstance(
            self.counterparty_signature, str
        )
        if self.amount >= 0:
            assert (
                self.sender_amount >= 0
            ), "Sender_amount must be positive when the sender is the payment receiver."
        else:
            assert (
                self.counterparty_amount >= 0
            ), "Counterparty_amount must be positive when the counterpary is the payment receiver."

    def has_matching_signatures(self) -> bool:
        """
        Check that the signatures match the terms of trade.

        :return: True if the transaction has been signed by both parties
        """
        w3 = Web3()
        singable_message = encode_defunct(primitive=self.sender_hash)
        result = (
            w3.eth.account.recover_message(  # pylint: disable=no-member
                signable_message=singable_message,
                signature=HexBytes(self.sender_signature),
            )
            == self.sender_addr
        )
        counterparty_signable_message = encode_defunct(primitive=self.counterparty_hash)
        result = (
            result
            and w3.eth.account.recover_message(  # pylint: disable=no-member
                signable_message=counterparty_signable_message,
                signature=HexBytes(self.counterparty_signature),
            )
            == self.counterparty_addr
        )
        return result

    @classmethod
    def from_message(cls, message: TacMessage) -> "Transaction":
        """
        Create a transaction from a proposal.

        :param message: the message
        :return: Transaction
        """
        assert message.performative == TacMessage.Performative.TRANSACTION
        return Transaction(
            message.tx_id,
            message.tx_sender_addr,
            message.tx_counterparty_addr,
            message.amount_by_currency_id,
            message.tx_sender_fee,
            message.tx_counterparty_fee,
            message.quantities_by_good_id,
            message.tx_nonce,
            message.tx_sender_signature,
            message.tx_counterparty_signature,
        )

    def __eq__(self, other):
        """Compare to another object."""
        return (
            isinstance(other, Transaction)
            and self.id == other.id
            and self.sender_addr == other.sender_addr
            and self.counterparty_addr == other.counterparty_addr
            and self.amount_by_currency_id == other.amount_by_currency_id
            and self.sender_fee == other.sender_fee
            and self.counterparty_fee == other.counterparty_fee
            and self.quantities_by_good_id == other.quantities_by_good_id
            and self.nonce == other.nonce
            and self.sender_signature == other.sender_signature
            and self.counterparty_signature == other.counterparty_signature
        )


class AgentState:
    """Represent the state of an agent during the game."""

    def __init__(
        self,
        agent_address: Address,
        amount_by_currency_id: Dict[CurrencyId, Quantity],
        exchange_params_by_currency_id: Dict[CurrencyId, Parameter],
        quantities_by_good_id: Dict[GoodId, Quantity],
        utility_params_by_good_id: Dict[GoodId, Parameter],
    ):
        """
        Instantiate an agent state object.

        :param agent_address: the agent address
        :param amount_by_currency_id: the amount for each currency
        :param exchange_params_by_currency_id: the exchange parameters of the different currencies
        :param quantities_by_good_id: the quantities for each good.
        :param utility_params_by_good_id: the utility params for every good.
        """
        assert len(amount_by_currency_id.keys()) == len(
            exchange_params_by_currency_id.keys()
        )
        assert len(quantities_by_good_id.keys()) == len(
            utility_params_by_good_id.keys()
        )
        self._agent_address = agent_address
        self._amount_by_currency_id = copy.copy(amount_by_currency_id)
        self._exchange_params_by_currency_id = copy.copy(exchange_params_by_currency_id)
        self._quantities_by_good_id = quantities_by_good_id
        self._utility_params_by_good_id = copy.copy(utility_params_by_good_id)

    @property
    def agent_address(self) -> str:
        """Get address of the agent which state that is."""
        return self._agent_address

    @property
    def amount_by_currency_id(self) -> Dict[CurrencyId, Quantity]:
        """Get the amount for each currency."""
        return copy.copy(self._amount_by_currency_id)

    @property
    def exchange_params_by_currency_id(self) -> Dict[CurrencyId, Parameter]:
        """Get the exchange parameters for each currency."""
        return copy.copy(self._exchange_params_by_currency_id)

    @property
    def quantities_by_good_id(self) -> Dict[GoodId, Quantity]:
        """Get holding of each good."""
        return copy.copy(self._quantities_by_good_id)

    @property
    def utility_params_by_good_id(self) -> Dict[GoodId, Parameter]:
        """Get utility parameter for each good."""
        return copy.copy(self._utility_params_by_good_id)

    def get_score(self) -> float:
        """
        Compute the score of the current state.

        The score is computed as the sum of all the utilities for the good holdings
        with positive quantity plus the money left.
        :return: the score.
        """
        goods_score = logarithmic_utility(
            self.utility_params_by_good_id, self.quantities_by_good_id
        )
        money_score = linear_utility(
            self.exchange_params_by_currency_id, self.amount_by_currency_id
        )
        score = goods_score + money_score
        return score

    def is_consistent_transaction(self, tx: Transaction) -> bool:
        """
        Check if the transaction is consistent.

        E.g. check that the agent state has enough money if it is a buyer
        or enough holdings if it is a seller.
        :return: True if the transaction is legal wrt the current state, False otherwise.
        """
        result = self.agent_address in [tx.sender_addr, tx.counterparty_addr]
        if tx.amount == 0 and all(
            quantity == 0 for quantity in tx.quantities_by_good_id.values()
        ):
            # reject the transaction when there is no wealth exchange
            result = False
        elif tx.amount <= 0 and all(
            quantity >= 0 for quantity in tx.quantities_by_good_id.values()
        ):
            # sender is buyer, counterparty is seller
            if self.agent_address == tx.sender_addr:
                # check this sender state has enough money
                result = result and (
                    self.amount_by_currency_id[tx.currency_id] >= tx.sender_amount
                )
            elif self.agent_address == tx.counterparty_addr:
                # check this counterparty state has enough goods
                result = result and all(
                    self.quantities_by_good_id[good_id] >= quantity
                    for good_id, quantity in tx.quantities_by_good_id.items()
                )
        elif tx.amount >= 0 and all(
            quantity <= 0 for quantity in tx.quantities_by_good_id.values()
        ):
            # sender is seller, counterparty is buyer
            # Note, on a ledger, this atomic swap would only be possible for amount == 0!
            if self.agent_address == tx.sender_addr:
                # check this sender state has enough goods
                result = result and all(
                    self.quantities_by_good_id[good_id] >= -quantity
                    for good_id, quantity in tx.quantities_by_good_id.items()
                )
            elif self.agent_address == tx.counterparty_addr:
                # check this counterparty state has enough money
                result = result and (
                    self.amount_by_currency_id[tx.currency_id] >= tx.counterparty_amount
                )
        else:
            result = False
        return result

    def apply(self, transactions: List[Transaction]) -> "AgentState":
        """
        Apply a list of transactions to the current state.

        :param transactions: the sequence of transaction.
        :return: the final state.
        """
        new_state = copy.copy(self)
        for tx in transactions:
            new_state.update(tx)

        return new_state

    def update(self, tx: Transaction) -> None:
        """
        Update the agent state from a transaction.

        :param tx: the transaction.
        :return: None
        """
        assert self.is_consistent_transaction(tx), "Inconsistent transaction."

        new_amount_by_currency_id = self.amount_by_currency_id
        if self.agent_address == tx.sender_addr:
            # settling the transaction for the sender
            new_amount_by_currency_id[tx.currency_id] += tx.sender_amount
        elif self.agent_address == tx.counterparty_addr:
            # settling the transaction for the counterparty
            new_amount_by_currency_id[tx.currency_id] += tx.counterparty_amount

        self._amount_by_currency_id = new_amount_by_currency_id

        new_quantities_by_good_id = self.quantities_by_good_id
        for good_id, quantity in tx.quantities_by_good_id.items():
            if self.agent_address == tx.sender_addr:
                new_quantities_by_good_id[good_id] += quantity
            elif self.agent_address == tx.counterparty_addr:
                new_quantities_by_good_id[good_id] -= quantity
        self._quantities_by_good_id = new_quantities_by_good_id

    def __copy__(self):
        """Copy the object."""
        return AgentState(
            self.agent_address,
            self.amount_by_currency_id,
            self.exchange_params_by_currency_id,
            self.quantities_by_good_id,
            self.utility_params_by_good_id,
        )

    def __str__(self):
        """From object to string."""
        return "AgentState{}".format(
            pprint.pformat(
                {
                    "agent_address": self.agent_address,
                    "amount_by_currency_id": self.amount_by_currency_id,
                    "exchange_params_by_currency_id": self.exchange_params_by_currency_id,
                    "quantities_by_good_id": self.quantities_by_good_id,
                    "utility_params_by_good_id": self.utility_params_by_good_id,
                }
            )
        )

    def __eq__(self, other) -> bool:
        """Compare equality of two instances of the class."""
        return (
            isinstance(other, AgentState)
            and self.agent_address == other.agent_address
            and self.amount_by_currency_id == other.amount_by_currency_id
            and self.exchange_params_by_currency_id
            == other.exchange_params_by_currency_id
            and self.quantities_by_good_id == other.quantities_by_good_id
            and self.utility_params_by_good_id == other.utility_params_by_good_id
        )


class Transactions:
    """Class managing the transactions."""

    def __init__(self):
        """Instantiate the transaction class."""
        self._confirmed = {}  # type: Dict[datetime.datetime, Transaction]
        self._confirmed_per_agent = (
            {}
        )  # type: Dict[Address, Dict[datetime.datetime, Transaction]]

    @property
    def confirmed(self) -> Dict[datetime.datetime, Transaction]:
        """Get the confirmed transactions."""
        return self._confirmed

    @property
    def confirmed_per_agent(
        self,
    ) -> Dict[Address, Dict[datetime.datetime, Transaction]]:
        """Get the confirmed transactions by agent."""
        return self._confirmed_per_agent

    def add(self, transaction: Transaction) -> None:
        """
        Add a confirmed transaction.

        :param transaction: the transaction
        :return: None
        """
        now = datetime.datetime.now()
        self._confirmed[now] = transaction
        if self._confirmed_per_agent.get(transaction.sender_addr) is None:
            self._confirmed_per_agent[transaction.sender_addr] = {}
        self._confirmed_per_agent[transaction.sender_addr][now] = transaction
        if self._confirmed_per_agent.get(transaction.counterparty_addr) is None:
            self._confirmed_per_agent[transaction.counterparty_addr] = {}
        self._confirmed_per_agent[transaction.counterparty_addr][now] = transaction


class Registration:
    """Class managing the registration of the game."""

    def __init__(self):
        """Instantiate the registration class."""
        self._agent_addr_to_name = {}  # type: Dict[str, str]

    @property
    def agent_addr_to_name(self) -> Dict[str, str]:
        """Get the registered agent addresses and their names."""
        return self._agent_addr_to_name

    @property
    def nb_agents(self) -> int:
        """Get the number of registered agents."""
        return len(self._agent_addr_to_name)

    def register_agent(self, agent_addr: Address, agent_name: str) -> None:
        """
        Register an agent.

        :param agent_addr: the Address of the agent
        :param agent_name: the name of the agent
        :return: None
        """
        self._agent_addr_to_name[agent_addr] = agent_name

    def unregister_agent(self, agent_addr: Address) -> None:
        """
        Register an agent.

        :param agent_addr: the Address of the agent
        :return: None
        """
        self._agent_addr_to_name.pop(agent_addr)


class Game(Model):
    """A class to manage a TAC instance."""

    def __init__(self, **kwargs):
        """Instantiate the search class."""
        super().__init__(**kwargs)
        self._phase = Phase.PRE_GAME
        self._registration = Registration()
        self._conf = None  # type: Optional[Configuration]
        self._initialization = None  # type: Optional[Initialization]
        self._initial_agent_states = None  # type: Optional[Dict[str, AgentState]]
        self._current_agent_states = None  # type: Optional[Dict[str, AgentState]]
        self._transactions = Transactions()

    @property
    def phase(self) -> Phase:
        """Get the game phase."""
        return self._phase

    @phase.setter
    def phase(self, phase: Phase) -> None:
        """Set the game phase."""
        self._phase = phase

    @property
    def registration(self) -> Registration:
        """Get the registration."""
        return self._registration

    @property
    def conf(self) -> Configuration:
        """Get game configuration."""
        assert self._conf is not None, "Call create before calling configuration."
        return self._conf

    @property
    def initialization(self) -> Initialization:
        """Get game initialization."""
        assert (
            self._initialization is not None
        ), "Call create before calling initialization."
        return self._initialization

    @property
    def initial_agent_states(self) -> Dict[str, AgentState]:
        """Get initial state of each agent."""
        assert (
            self._initial_agent_states is not None
        ), "Call create before calling initial_agent_states."
        return self._initial_agent_states

    @property
    def current_agent_states(self) -> Dict[str, AgentState]:
        """Get current state of each agent."""
        assert (
            self._current_agent_states is not None
        ), "Call create before calling current_agent_states."
        return self._current_agent_states

    @property
    def transactions(self) -> Transactions:
        """Get the transactions."""
        return self._transactions

    def create(self):
        """Create a game."""
        assert not self.phase == Phase.GAME
        self._phase = Phase.GAME_SETUP
        self._generate()

    def _generate(self):
        """Generate a TAC game."""
        parameters = cast(Parameters, self.context.parameters)

        self._conf = Configuration(
            parameters.version_id,
            parameters.tx_fee,
            self.registration.agent_addr_to_name,
            parameters.nb_goods,
        )

        scaling_factor = determine_scaling_factor(parameters.money_endowment)

        agent_addr_to_currency_endowments = generate_currency_endowments(
            list(self.conf.agent_addr_to_name.keys()),
            list(self.conf.currency_id_to_name.keys()),
            parameters.money_endowment,
        )

        agent_addr_to_exchange_params = generate_exchange_params(
            list(self.conf.agent_addr_to_name.keys()),
            list(self.conf.currency_id_to_name.keys()),
        )

        agent_addr_to_good_endowments = generate_good_endowments(
            list(self.conf.agent_addr_to_name.keys()),
            list(self.conf.good_id_to_name.keys()),
            parameters.base_good_endowment,
            parameters.lower_bound_factor,
            parameters.upper_bound_factor,
        )

        agent_addr_to_utility_params = generate_utility_params(
            list(self.conf.agent_addr_to_name.keys()),
            list(self.conf.good_id_to_name.keys()),
            scaling_factor,
        )

        (
            good_id_to_eq_prices,
            agent_addr_to_eq_good_holdings,
            agent_addr_to_eq_currency_holdings,
        ) = generate_equilibrium_prices_and_holdings(
            agent_addr_to_good_endowments,
            agent_addr_to_utility_params,
            agent_addr_to_currency_endowments,
            agent_addr_to_exchange_params,
            scaling_factor,
        )

        self._initialization = Initialization(
            agent_addr_to_currency_endowments,
            agent_addr_to_exchange_params,
            agent_addr_to_good_endowments,
            agent_addr_to_utility_params,
            good_id_to_eq_prices,
            agent_addr_to_eq_good_holdings,
            agent_addr_to_eq_currency_holdings,
        )

        self._initial_agent_states = dict(
            (
                agent_addr,
                AgentState(
                    agent_addr,
                    self.initialization.agent_addr_to_currency_endowments[agent_addr],
                    self.initialization.agent_addr_to_exchange_params[agent_addr],
                    self.initialization.agent_addr_to_good_endowments[agent_addr],
                    self.initialization.agent_addr_to_utility_params[agent_addr],
                ),
            )
            for agent_addr in self.conf.agent_addr_to_name.keys()
        )

        self._current_agent_states = dict(
            (
                agent_addr,
                AgentState(
                    agent_addr,
                    self.initialization.agent_addr_to_currency_endowments[agent_addr],
                    self.initialization.agent_addr_to_exchange_params[agent_addr],
                    self.initialization.agent_addr_to_good_endowments[agent_addr],
                    self.initialization.agent_addr_to_utility_params[agent_addr],
                ),
            )
            for agent_addr in self.conf.agent_addr_to_name.keys()
        )

    @property
    def holdings_summary(self) -> str:
        """Get holdings summary (a string representing the holdings for every agent)."""
        result = "\n" + "Current good & money allocation & score: \n"
        for agent_addr, agent_state in self.current_agent_states.items():
            result = (
                result + "- " + self.conf.agent_addr_to_name[agent_addr] + ":" + "\n"
            )
            for good_id, quantity in agent_state.quantities_by_good_id.items():
                result += (
                    "    "
                    + self.conf.good_id_to_name[good_id]
                    + ": "
                    + str(quantity)
                    + "\n"
                )
            for currency_id, amount in agent_state.amount_by_currency_id.items():
                result += (
                    "    "
                    + self.conf.currency_id_to_name[currency_id]
                    + ": "
                    + str(amount)
                    + "\n"
                )
            result += "    score: " + str(round(agent_state.get_score(), 2)) + "\n"
        result = result + "\n"
        return result

    @property
    def equilibrium_summary(self) -> str:
        """Get equilibrium summary."""
        result = "\n" + "Equilibrium prices: \n"
        for good_id, eq_price in self.initialization.good_id_to_eq_prices.items():
            result = (
                result + self.conf.good_id_to_name[good_id] + " " + str(eq_price) + "\n"
            )
        result = result + "\n"
        result = result + "Equilibrium good allocation: \n"
        for (
            agent_addr,
            eq_allocations,
        ) in self.initialization.agent_addr_to_eq_good_holdings.items():
            result = result + "- " + self.conf.agent_addr_to_name[agent_addr] + ":\n"
            for good_id, quantity in eq_allocations.items():
                result = (
                    result
                    + "    "
                    + self.conf.good_id_to_name[good_id]
                    + ": "
                    + str(quantity)
                    + "\n"
                )
        result = result + "\n"
        result = result + "Equilibrium money allocation: \n"
        for (
            agent_addr,
            eq_allocation,
        ) in self.initialization.agent_addr_to_eq_currency_holdings.items():
            result = (
                result
                + self.conf.agent_addr_to_name[agent_addr]
                + " "
                + str(eq_allocation)
                + "\n"
            )
        result = result + "\n"
        return result

    def is_transaction_valid(self, tx: Transaction) -> bool:
        """
        Check whether the transaction is signed correctly and valid given the state of the game.

        :param tx: the transaction.
        :return: True if the transaction is valid, False otherwise.
        :raises: AssertionError: if the data in the transaction are not allowed (e.g. negative amount).
        """
        sender_state = self.current_agent_states[tx.sender_addr]
        counterparty_state = self.current_agent_states[tx.counterparty_addr]
        result = tx.has_matching_signatures()
        result = result and sender_state.is_consistent_transaction(tx)
        result = result and counterparty_state.is_consistent_transaction(tx)
        return result

    def settle_transaction(self, tx: Transaction) -> None:
        """
        Settle a valid transaction.

        :param tx: the game transaction.
        :return: None
        :raises: AssertionError if the transaction is not valid.
        """
        assert (
            self._current_agent_states is not None
        ), "Call create before calling current_agent_states."
        assert self.is_transaction_valid(tx), "Transaction is not valid."
        sender_state = self.current_agent_states[tx.sender_addr]
        counterparty_state = self.current_agent_states[tx.counterparty_addr]

        new_sender_state = sender_state.apply([tx])
        new_counterparty_state = counterparty_state.apply([tx])

        self.transactions.add(tx)
        self._current_agent_states.update({tx.sender_addr: new_sender_state})
        self._current_agent_states.update(
            {tx.counterparty_addr: new_counterparty_state}
        )
