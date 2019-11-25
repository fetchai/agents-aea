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

from collections import defaultdict
import copy
from enum import Enum
import pprint
from typing import cast, Dict, List, Optional, TYPE_CHECKING

from aea.helpers.preference_representations.base import logarithmic_utility, linear_utility
from aea.skills.base import SharedClass

if TYPE_CHECKING:
    from packages.protocols.tac.message import TACMessage
    from packages.skills.tac_control.helpers import generate_good_pbk_to_name, determine_scaling_factor, \
        generate_money_endowments, generate_good_endowments, generate_utility_params, generate_equilibrium_prices_and_holdings
    from packages.skills.tac_control.parameters import Parameters
else:
    from tac_protocol.message import TACMessage
    from tac_control_skill.helpers import generate_good_pbk_to_name, determine_scaling_factor, \
        generate_money_endowments, generate_good_endowments, generate_utility_params, generate_equilibrium_prices_and_holdings
    from tac_control_skill.parameters import Parameters

Address = str
TransactionId = str
Endowment = List[int]  # an element e_j is the endowment of good j.
UtilityParams = List[float]  # an element u_j is the utility value of good j.

DEFAULT_CURRENCY = 'FET'
DEFAULT_CURRENCY_EXCHANGE_RATE = 1.0


class Phase(Enum):
    """This class defines the phases of the game."""

    PRE_GAME = 'pre_game'
    GAME_REGISTRATION = 'game_registration'
    GAME_SETUP = 'game_setup'
    GAME = 'game'
    POST_GAME = 'post_game'


class Configuration:
    """Class containing the configuration of the game."""

    def __init__(self,
                 version_id: str,
                 nb_agents: int,
                 nb_goods: int,
                 tx_fee: int,
                 agent_pbk_to_name: Dict[Address, str],
                 good_pbk_to_name: Dict[Address, str]):
        """
        Instantiate a game configuration.

        :param version_id: the version of the game.
        :param nb_agents: the number of agents.
        :param nb_goods: the number of goods.
        :param tx_fee: the fee for a transaction.
        :param agent_pbk_to_name: a dictionary mapping agent public keys to agent names (as strings).
        :param good_pbk_to_name: a dictionary mapping good public keys to good names (as strings).
        """
        self._version_id = version_id
        self._nb_agents = nb_agents
        self._nb_goods = nb_goods
        self._tx_fee = tx_fee
        self._agent_pbk_to_name = agent_pbk_to_name
        self._good_pbk_to_name = good_pbk_to_name

        self._check_consistency()

    @property
    def version_id(self) -> str:
        """Agent number of a TAC instance."""
        return self._version_id

    @property
    def nb_agents(self) -> int:
        """Agent number of a TAC instance."""
        return self._nb_agents

    @property
    def nb_goods(self) -> int:
        """Good number of a TAC instance."""
        return self._nb_goods

    @property
    def tx_fee(self) -> int:
        """Transaction fee for the TAC instance."""
        return self._tx_fee

    @property
    def agent_pbk_to_name(self) -> Dict[Address, str]:
        """Map agent public keys to names."""
        return self._agent_pbk_to_name

    @property
    def good_pbk_to_name(self) -> Dict[Address, str]:
        """Map good public keys to names."""
        return self._good_pbk_to_name

    @property
    def agent_pbks(self) -> List[Address]:
        """List of agent public keys."""
        return list(self._agent_pbk_to_name.keys())

    @property
    def agent_names(self):
        """List of agent names."""
        return list(self._agent_pbk_to_name.values())

    @property
    def good_pbks(self) -> List[Address]:
        """List of good public keys."""
        return list(self._good_pbk_to_name.keys())

    @property
    def good_names(self) -> List[str]:
        """List of good names."""
        return list(self._good_pbk_to_name.values())

    def _check_consistency(self):
        """
        Check the consistency of the game configuration.

        :return: None
        :raises: AssertionError: if some constraint is not satisfied.
        """
        assert self.version_id is not None, "A version id must be set."
        assert self.tx_fee >= 0, "Tx fee must be non-negative."
        assert self.nb_agents > 1, "Must have at least two agents."
        assert self.nb_goods > 1, "Must have at least two goods."
        assert len(self.agent_pbks) == self.nb_agents, "There must be one public key for each agent."
        assert len(set(self.agent_names)) == self.nb_agents, "Agents' names must be unique."
        assert len(self.good_pbks) == self.nb_goods, "There must be one public key for each good."
        assert len(set(self.good_names)) == self.nb_goods, "Goods' names must be unique."


class Initialization:
    """Class containing the initialization of the game."""

    def __init__(self,
                 initial_money_amounts: List[int],
                 endowments: List[Endowment],
                 utility_params: List[UtilityParams],
                 eq_prices: List[float],
                 eq_good_holdings: List[List[float]],
                 eq_money_holdings: List[float]):
        """
        Instantiate a game initialization.

        :param initial_money_amounts: the initial amount of money of every agent.
        :param endowments: the endowments of the agents. A matrix where the first index is the agent id
                            and the second index is the good id. A generic element e_ij at row i and column j is
                            an integer that denotes the endowment of good j for agent i.
        :param utility_params: the utility params representing the preferences of the agents. A matrix where the first
                            index is the agent id and the second index is the good id. A generic element e_ij
                            at row i and column j is an integer that denotes the utility of good j for agent i.
        :param eq_prices: the competitive equilibrium prices of the goods. A list.
        :param eq_good_holdings: the competitive equilibrium good holdings of the agents. A matrix where the first index is the agent id
                            and the second index is the good id. A generic element g_ij at row i and column j is
                            a float that denotes the (divisible) amount of good j for agent i.
        :param eq_money_holdings: the competitive equilibrium money holdings of the agents. A list.
        """
        self._initial_money_amounts = initial_money_amounts
        self._endowments = endowments
        self._utility_params = utility_params
        self._eq_prices = eq_prices
        self._eq_good_holdings = eq_good_holdings
        self._eq_money_holdings = eq_money_holdings

        self._check_consistency()

    @property
    def initial_money_amounts(self) -> List[int]:
        """Get list of the initial amount of money of every agent."""
        return self._initial_money_amounts

    @property
    def endowments(self) -> List[Endowment]:
        """Get endowments of the agents."""
        return self._endowments

    @property
    def utility_params(self) -> List[UtilityParams]:
        """Get utility parameter list of the agents."""
        return self._utility_params

    @property
    def eq_prices(self) -> List[float]:
        """Get theoretical equilibrium prices (a benchmark)."""
        return self._eq_prices

    @property
    def eq_good_holdings(self) -> List[List[float]]:
        """Get theoretical equilibrium good holdings (a benchmark)."""
        return self._eq_good_holdings

    @property
    def eq_money_holdings(self) -> List[float]:
        """Get theoretical equilibrium money holdings (a benchmark)."""
        return self._eq_money_holdings

    def _check_consistency(self):
        """
        Check the consistency of the game configuration.

        :return: None
        :raises: AssertionError: if some constraint is not satisfied.
        """
        assert all(money >= 0 for money in self.initial_money_amounts), "Money must be non-negative."
        assert all(e > 0 for row in self.endowments for e in row), "Endowments must be strictly positive."
        assert all(e > 0 for row in self.utility_params for e in row), "UtilityParams must be strictly positive."

        assert len(self.endowments) == len(self.initial_money_amounts), "Length of endowments and initial_money_amounts must be the same."
        assert len(self.endowments) == len(self.utility_params), "Length of endowments and utility_params must be the same."

        assert len(self.eq_prices) == len(self.eq_good_holdings[0]), "Length of eq_prices and an element of eq_good_holdings must be the same."
        assert len(self.eq_good_holdings) == len(self.eq_money_holdings), "Length of eq_good_holdings and eq_good_holdings must be the same."

        assert all(len(row_e) == len(row_u) for row_e, row_u in zip(self.endowments, self.utility_params)), "Dimensions for utility_params and endowments rows must be the same."


class GoodState:
    """Represent the state of a good during the game."""

    def __init__(self, price: float = 0.0) -> None:
        """
        Instantiate an agent state object.

        :param price: price of the good in this state.
        :return: None
        """
        self.price = price

        self._check_consistency()

    def _check_consistency(self) -> None:
        """
        Check the consistency of the good state.

        :return: None
        :raises: AssertionError: if some constraint is not satisfied.
        """
        assert self.price >= 0.0, "The price must be non-negative."


class Transaction:
    """Convenience representation of a transaction."""

    def __init__(self,
                 transaction_id: TransactionId,
                 sender: Address,
                 counterparty: Address,
                 amount_by_currency: Dict[str, int],
                 sender_tx_fee: int,
                 counterparty_tx_fee: int,
                 quantities_by_good_pbk: Dict[str, int]) -> None:
        """
        Instantiate transaction request.

        :param transaction_id: the id of the transaction.
        :param sender: the sender of the transaction.
        :param counterparty: the counterparty of the transaction.
        :param amount_by_currency: the currency used.
        :param sender_tx_fee: the transaction fee covered by the sender.
        :param counterparty_tx_fee: the transaction fee covered by the counterparty.
        :param quantities_by_good_pbk: a map from good pbk to the quantity of that good involved in the transaction.
        :return: None
        """
        self.transaction_id = transaction_id
        self.sender = sender
        self.counterparty = counterparty
        self.is_sender_buyer = any(value <= 0 for value in amount_by_currency.values())
        self.amount_by_currency = amount_by_currency
        self.sender_tx_fee = sender_tx_fee
        self.counterparty_tx_fee = counterparty_tx_fee
        self.quantities_by_good_pbk = quantities_by_good_pbk
        self._check_consistency()

    @property
    def buyer_pbk(self) -> Address:
        """Get the public key of the buyer."""
        result = self.sender if self.is_sender_buyer else self.counterparty
        return result

    @property
    def seller_pbk(self) -> Address:
        """Get the public key of the seller."""
        result = self.counterparty if self.is_sender_buyer else self.sender
        return result

    @property
    def buyer_tx_fee(self) -> int:
        """Get the tx fee of the buyer."""
        result = self.sender_tx_fee if self.is_sender_buyer else self.counterparty_tx_fee
        return result

    @property
    def seller_tx_fee(self) -> int:
        """Get the tx fee of the seller."""
        result = self.counterparty_tx_fee if self.is_sender_buyer else self.sender_tx_fee
        return result

    @property
    def amount(self) -> int:
        """Get the amount."""
        assert len(self.amount_by_currency) == 1
        return list(self.amount_by_currency.values())[0]

    @property
    def currency(self) -> str:
        """Get the currency."""
        assert len(self.amount_by_currency) == 1
        return list(self.amount_by_currency.keys())[0]

    def _check_consistency(self) -> None:
        """
        Check the consistency of the transaction parameters.

        :return: None
        :raises AssertionError if some constraint is not satisfied.
        """
        assert self.sender != self.counterparty
        assert len(self.amount_by_currency.keys()) == 1  # For now we restrict to one currency per transaction.
        assert self.sender_tx_fee >= 0
        assert self.counterparty_tx_fee >= 0
        assert len(self.quantities_by_good_pbk.keys()) == len(set(self.quantities_by_good_pbk.keys()))

    @classmethod
    def from_message(cls, message: TACMessage, sender: Address) -> 'Transaction':
        """
        Create a transaction from a proposal.

        :param message: the message
        :return: Transaction
        """
        assert message.get('type') == TACMessage.Type.TRANSACTION
        return Transaction(cast(str, message.get("transaction_id")),
                           sender,
                           cast(str, message.get("counterparty")),
                           cast(Dict[str, int], message.get("amount_by_currency")),
                           cast(int, message.get("sender_tx_fee")),
                           cast(int, message.get("counterparty_tx_fee")),
                           cast(Dict[str, int], message.get("quantities_by_good_pbk")))

    def matches(self, other: 'Transaction') -> bool:
        """
        Check if the transaction matches with another (mirroring) transaction.

        Two transaction requests do match if:
        - the transaction id is the same;
        - one of them is from a buyer and the other one is from a seller
        - the counterparty and the origin field are consistent.
        - the amount and the quantities are equal.

        :param other: the other transaction to match.
        :return: True if the two
        """
        return self.transaction_id == other.transaction_id \
            and self.sender == other.counterparty \
            and self.counterparty == other.sender \
            and self.is_sender_buyer != other.is_sender_buyer \
            and self.amount_by_currency == {x: y * -1 for x, y in other.amount_by_currency.items()} \
            and self.sender_tx_fee == other.counterparty_tx_fee \
            and self.counterparty_tx_fee == other.sender_tx_fee \
            and self.quantities_by_good_pbk == {x: y * -1 for x, y in other.quantities_by_good_pbk.items()}

    def __eq__(self, other):
        """Compare to another object."""
        return isinstance(other, Transaction) \
            and self.transaction_id == other.transaction_id \
            and self.sender == other.sender \
            and self.counterparty == other.counterparty \
            and self.is_sender_buyer == other.is_sender_buyer \
            and self.amount_by_currency == other.amount_by_currency \
            and self.sender_tx_fee == other.sender_tx_fee \
            and self.counterparty_tx_fee == other.counterparty_tx_fee \
            and self.quantities_by_good_pbk == other.quantities_by_good_pbk


class AgentState:
    """Represent the state of an agent during the game."""

    def __init__(self, amount_by_currency: Dict[str, int],
                 exchange_params_by_currency: Dict[str, float],
                 quantities_by_good_pbk: Dict[str, int],
                 utility_params_by_good_pbk: Dict[str, float]):
        """
        Instantiate an agent state object.

        :param amount_by_currency: the amount for each currency
        :param exchange_params_by_currency: the exchange parameters of the different currencies
        :param quantities_by_good_pbk: the quantities for each good.
        :param utility_params_by_good_pbk: the utility params for every good.
        """
        assert len(amount_by_currency.keys()) == len(exchange_params_by_currency.keys())
        assert len(quantities_by_good_pbk.keys()) == len(utility_params_by_good_pbk.keys())
        self._balance_by_currency = copy.copy(amount_by_currency)
        self._exchange_params_by_currency = copy.copy(exchange_params_by_currency)
        self._quantities_by_good_pbk = quantities_by_good_pbk
        self._utility_params_by_good_pbk = copy.copy(utility_params_by_good_pbk)

    @property
    def balance_by_currency(self) -> Dict[str, int]:
        """Get the balance for each currency."""
        return copy.copy(self._balance_by_currency)

    @property
    def exchange_params_by_currency(self) -> Dict[str, float]:
        """Get the exchange parameters for each currency."""
        return copy.copy(self._exchange_params_by_currency)

    @property
    def quantities_by_good_pbk(self) -> Dict[str, int]:
        """Get holding of each good."""
        return copy.copy(self._quantities_by_good_pbk)

    @property
    def utility_params_by_good_pbk(self) -> Dict[str, float]:
        """Get utility parameter for each good."""
        return copy.copy(self._utility_params_by_good_pbk)

    def get_score(self) -> float:
        """
        Compute the score of the current state.

        The score is computed as the sum of all the utilities for the good holdings
        with positive quantity plus the money left.
        :return: the score.
        """
        goods_score = logarithmic_utility(self.utility_params_by_good_pbk, self.quantities_by_good_pbk)
        money_score = linear_utility(self.exchange_params_by_currency, self.balance_by_currency)
        score = goods_score + money_score
        return score

    def get_score_diff_from_transaction(self, tx: Transaction) -> float:
        """
        Simulate a transaction and get the resulting score (taking into account the fee).

        :param tx: a transaction object.
        :return: the score.
        """
        current_score = self.get_score()
        new_state = self.apply([tx])
        new_score = new_state.get_score()
        return new_score - current_score

    def check_transaction_is_consistent(self, tx: Transaction) -> bool:
        """
        Check if the transaction is consistent.

        E.g. check that the agent state has enough money if it is a buyer
        or enough holdings if it is a seller.
        :return: True if the transaction is legal wrt the current state, false otherwise.
        """
        if tx.is_sender_buyer:
            # check if we have the money as the buyer.
            result = self.balance_by_currency[tx.currency] >= tx.amount + tx.buyer_tx_fee
        else:
            # check if we have the diff and the goods as the seller.
            result = self.balance_by_currency[tx.currency] + tx.amount >= tx.seller_tx_fee
            for good_pbk, quantity in tx.quantities_by_good_pbk.items():
                result = result and (self.quantities_by_good_pbk[good_pbk] >= quantity)
        return result

    def apply(self, transactions: List[Transaction]) -> 'AgentState':
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
        new_balance_by_currency = self.balance_by_currency
        if tx.is_sender_buyer:
            total = tx.amount + tx.buyer_tx_fee
            new_balance_by_currency[tx.currency] -= total
        else:
            diff = tx.amount - tx.seller_tx_fee
            new_balance_by_currency[tx.currency] += diff
        self._balance_by_currency = new_balance_by_currency

        new_quantities_by_good_pbk = self.quantities_by_good_pbk
        for good_pbk, quantity in tx.quantities_by_good_pbk.items():
            quantity_delta = quantity if tx.is_sender_buyer else -quantity
            new_quantities_by_good_pbk[good_pbk] += quantity_delta
        self._quantities_by_good_pbk = new_quantities_by_good_pbk

    def __copy__(self):
        """Copy the object."""
        return AgentState(self.balance_by_currency,
                          self.exchange_params_by_currency,
                          self.quantities_by_good_pbk,
                          self.utility_params_by_good_pbk)

    def __str__(self):
        """From object to string."""
        return "AgentState{}".format(pprint.pformat({
            "balance_by_currency": self.balance_by_currency,
            "exchange_params_by_currency": self.exchange_params_by_currency,
            "quantities_by_good_pbk": self.quantities_by_good_pbk,
            "utility_params_by_good_pbk": self.utility_params_by_good_pbk
        }))

    def __eq__(self, other) -> bool:
        """Compare equality of two instances of the class."""
        return isinstance(other, AgentState) and \
            self.balance_by_currency == other.balance_by_currency and \
            self.exchange_params_by_currency == other.exchange_params_by_currency and \
            self.quantities_by_good_pbk == other.quantities_by_good_pbk and \
            self.utility_params_by_good_pbk == other.utility_params_by_good_pbk


class Transactions:
    """Class managing the transactions."""

    def __init__(self):
        """Instantiate the transaction class."""
        self._pending = defaultdict(lambda: [])  # type: Dict[TransactionId, Transaction]
        self._confirmed = []  # type: List[Transaction]
        self._confirmed_per_agent = defaultdict(lambda: [])  # type: Dict[Address, List[Transaction]]

    @property
    def pending(self) -> Dict[TransactionId, Transaction]:
        """Get the pending transactions."""
        return self._pending

    @property
    def confirmed(self) -> List[Transaction]:
        """Get the confirmed transactions."""
        return self._confirmed

    @property
    def confirmed_per_agent(self) -> Dict[Address, List[Transaction]]:
        """Get the confirmed transactions by agent."""
        return self._confirmed_per_agent

    def add_pending(self, transaction: Transaction) -> None:
        """
        Add a pending transaction.

        :param transaction: the transaction
        :return: None
        """
        self._pending[transaction.transaction_id] = transaction

    def pop_pending(self, transaction_id: TransactionId) -> Transaction:
        """
        Pop a pending transaction.

        :param transaction_id: the transaction id
        :return: None
        """
        return self._pending.pop(transaction_id)

    def add_confirmed(self, transaction: Transaction) -> None:
        """
        Add a confirmed transaction.

        :param transaction: the transaction
        :return: None
        """
        self._confirmed.append(transaction)
        self._confirmed_per_agent[transaction.sender].append(transaction)
        self._confirmed_per_agent[transaction.counterparty].append(transaction)


class Registration:
    """Class managing the registration of the game."""

    def __init__(self):
        """Instantiate the registration class."""
        self._agent_pbk_to_name = defaultdict()  # type: Dict[str, str]

    @property
    def agent_pbk_to_name(self) -> Dict[str, str]:
        """Get the registered agent public keys and their names."""
        return self._agent_pbk_to_name

    @property
    def nb_agents(self) -> int:
        """Get the number of registered agents."""
        return len(self._agent_pbk_to_name)

    def register_agent(self, agent_pbk: str, agent_name: str) -> None:
        """
        Register an agent.

        :param agent_pbk: the public key of the agent
        :param agent_name: the name of the agent
        :return: None
        """
        self._agent_pbk_to_name[agent_pbk] = agent_name

    def unregister_agent(self, agent_pbk: str) -> None:
        """
        Register an agent.

        :param agent_pbk: the public key of the agent
        :return: None
        """
        self._agent_pbk_to_name.pop(agent_pbk)


class Game(SharedClass):
    """A class to manage a TAC instance."""

    def __init__(self, **kwargs):
        """Instantiate the search class."""
        super().__init__(**kwargs)
        self._phase = Phase.PRE_GAME
        self._registration = Registration()
        self._configuration = None  # type: Optional[Configuration]
        self._initialization = None  # type: Optional[Initialization]
        self._initial_agent_states = None  # type: Optional[Dict[str, AgentState]]
        self._current_agent_states = None  # type: Optional[Dict[str, AgentState]]
        self._current_good_states = None  # type: Optional[Dict[str, GoodState]]
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
    def configuration(self) -> Configuration:
        """Get game configuration."""
        assert self._configuration is not None, "Call create before calling configuration."
        return self._configuration

    @property
    def initialization(self) -> Initialization:
        """Get game initialization."""
        assert self._initialization is not None, "Call create before calling initialization."
        return self._initialization

    @property
    def initial_agent_states(self) -> Dict[str, AgentState]:
        """Get initial state of each agent."""
        assert self._initial_agent_states is not None, "Call create before calling initial_agent_states."
        return self._initial_agent_states

    @property
    def current_agent_states(self) -> Dict[str, AgentState]:
        """Get current state of each agent."""
        assert self._current_agent_states is not None, "Call create before calling current_agent_states."
        return self._current_agent_states

    @property
    def current_good_states(self) -> Dict[str, GoodState]:
        """Get current state of each good."""
        assert self._current_good_states is not None, "Call create before calling current_good_states."
        return self._current_good_states

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

        good_pbk_to_name = generate_good_pbk_to_name(parameters.nb_goods)
        self._configuration = Configuration(parameters.version_id, self.registration.nb_agents, parameters.nb_goods, parameters.tx_fee, self.registration.agent_pbk_to_name, good_pbk_to_name)

        scaling_factor = determine_scaling_factor(parameters.money_endowment)
        money_endowments = generate_money_endowments(self.registration.nb_agents, parameters.money_endowment)
        good_endowments = generate_good_endowments(parameters.nb_goods, self.registration.nb_agents, parameters.base_good_endowment, parameters.lower_bound_factor, parameters.upper_bound_factor)
        utility_params = generate_utility_params(self.registration.nb_agents, parameters.nb_goods, scaling_factor)
        eq_prices, eq_good_holdings, eq_money_holdings = generate_equilibrium_prices_and_holdings(good_endowments, utility_params, money_endowments, scaling_factor)
        self._initialization = Initialization(money_endowments, good_endowments, utility_params, eq_prices, eq_good_holdings, eq_money_holdings)

        self._initial_agent_states = dict(
            (agent_pbk,
                AgentState(
                    {DEFAULT_CURRENCY: self.initialization.initial_money_amounts[i]},
                    {DEFAULT_CURRENCY: DEFAULT_CURRENCY_EXCHANGE_RATE},
                    {good_pbk: endowment for good_pbk, endowment in zip(list(good_pbk_to_name.keys()), self.initialization.endowments[i])},
                    {good_pbk: utility_param for good_pbk, utility_param in zip(list(good_pbk_to_name.keys()), self.initialization.utility_params[i])}
                ))
            for agent_pbk, i in zip(self.configuration.agent_pbks, range(self.configuration.nb_agents)))

        self._current_agent_states = dict(
            (agent_pbk,
                AgentState(
                    {DEFAULT_CURRENCY: self.initialization.initial_money_amounts[i]},
                    {DEFAULT_CURRENCY: DEFAULT_CURRENCY_EXCHANGE_RATE},
                    {good_pbk: endowment for good_pbk, endowment in zip(list(good_pbk_to_name.keys()), self.initialization.endowments[i])},
                    {good_pbk: utility_param for good_pbk, utility_param in zip(list(good_pbk_to_name.keys()), self.initialization.utility_params[i])}
                ))
            for agent_pbk, i in zip(self.configuration.agent_pbks, range(self.configuration.nb_agents)))

        self._current_good_states = dict(
            (good_pbk,
                GoodState())
            for good_pbk in self.configuration.good_pbks)

    def reset(self) -> None:
        """Reset the game."""
        self._phase = Phase.PRE_GAME
        self._registration = Registration()
        self._configuration = None
        self._initialization = None
        self._initial_agent_states = None
        self._current_agent_states = None
        self._current_good_states = None
        self._transactions = Transactions()

    @property
    def initial_agent_scores(self) -> Dict[str, float]:
        """Get the initial scores for every agent."""
        return {agent_pbk: agent_state.get_score() for agent_pbk, agent_state in self.initial_agent_states.items()}

    @property
    def current_agent_scores(self) -> Dict[str, float]:
        """Get the current scores for every agent."""
        return {agent_pbk: agent_state.get_score() for agent_pbk, agent_state in self.current_agent_states.items()}

    @property
    def holdings_matrix(self) -> List[Endowment]:
        """
        Get the holdings matrix of shape (nb_agents, nb_goods).

        :return: the holdings matrix.
        """
        result = list(map(lambda state: list(state.quantities_by_good_pbk.values()), self.current_agent_states.values()))
        return result

    @property
    def agent_balances(self) -> Dict[str, int]:
        """Get the current agent balances."""
        result = {agent_pbk: agent_state.balance_by_currency[DEFAULT_CURRENCY] for agent_pbk, agent_state in self.current_agent_states.items()}
        return result

    @property
    def good_prices(self) -> List[float]:
        """Get the current good prices."""
        result = list(map(lambda state: state.price, self.current_good_states.values()))
        return result

    @property
    def holdings_summary(self) -> str:
        """Get holdings summary (a string representing the holdings for every agent)."""
        result = ""
        for agent_pbk, agent_state in self.current_agent_states.items():
            result = result + self.configuration.agent_pbk_to_name[agent_pbk] + " " + str(agent_state.quantities_by_good_pbk) + "\n"
        return result

    @property
    def equilibrium_summary(self) -> str:
        """Get equilibrium summary."""
        result = "Equilibrium prices: \n"
        for good_pbk, eq_price in zip(self.configuration.good_pbks, self.initialization.eq_prices):
            result = result + good_pbk + " " + str(eq_price) + "\n"
        result = result + "\n"
        result = result + "Equilibrium good allocation: \n"
        for agent_name, eq_allocations in zip(self.configuration.agent_names, self.initialization.eq_good_holdings):
            result = result + agent_name + " " + str(eq_allocations) + "\n"
        result = result + "\n"
        result = result + "Equilibrium money allocation: \n"
        for agent_name, eq_allocation in zip(self.configuration.agent_names, self.initialization.eq_money_holdings):
            result = result + agent_name + " " + str(eq_allocation) + "\n"
        return result

    def is_transaction_valid(self, tx: Transaction) -> bool:
        """
        Check whether the transaction is valid given the state of the game.

        :param tx: the transaction.
        :return: True if the transaction is valid, False otherwise.
        :raises: AssertionError: if the data in the transaction are not allowed (e.g. negative amount).
        """
        buyer_state = self.current_agent_states[tx.buyer_pbk]
        seller_state = self.current_agent_states[tx.seller_pbk]
        result = buyer_state.check_transaction_is_consistent(tx) and \
            seller_state.check_transaction_is_consistent(tx)
        return result

    def settle_transaction(self, tx: Transaction) -> None:
        """
        Settle a valid transaction.

        :param tx: the game transaction.
        :return: None
        :raises: AssertionError if the transaction is not valid.
        """
        # assert self.is_transaction_valid(tx)
        # self._transactions.append(tx)
        assert self._current_agent_states is not None, "Call create before calling current_agent_states."
        buyer_state = self.current_agent_states[tx.buyer_pbk]
        seller_state = self.current_agent_states[tx.seller_pbk]

        buyer_state.update(tx)
        seller_state.update(tx)

        self._current_agent_states.update({tx.buyer_pbk: buyer_state})
        self._current_agent_states.update({tx.seller_pbk: seller_state})
