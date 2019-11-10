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
from typing import Any, cast, Dict, List, Optional, TYPE_CHECKING

from aea.skills.base import SharedClass

if TYPE_CHECKING:
    from packages.protocols.tac.message import TACMessage
    from packages.skills.tac_control.helpers import generate_good_pbk_to_name, determine_scaling_factor, \
        generate_money_endowments, generate_good_endowments, generate_utility_params, generate_equilibrium_prices_and_holdings, \
        logarithmic_utility
    from packages.skills.tac_control.parameters import Parameters
else:
    from tac_protocol.message import TACMessage
    from tac_control_skill.helpers import generate_good_pbk_to_name, determine_scaling_factor, \
        generate_money_endowments, generate_good_endowments, generate_utility_params, generate_equilibrium_prices_and_holdings, \
        logarithmic_utility
    from tac_control_skill.parameters import Parameters

Address = str
TransactionId = str
Endowment = List[int]  # an element e_j is the endowment of good j.
UtilityParams = List[float]  # an element u_j is the utility value of good j.


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
                 tx_fee: float,
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
    def tx_fee(self) -> float:
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
                 initial_money_amounts: List[float],
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
    def initial_money_amounts(self) -> List[float]:
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

    def __init__(self, price: float) -> None:
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
        assert self.price >= 0, "The price must be non-negative."


class Transaction:
    """Convenience representation of a transaction."""

    def __init__(self, transaction_id: TransactionId, is_sender_buyer: bool, counterparty: Address,
                 amount: float, quantities_by_good_pbk: Dict[str, int], sender: Address) -> None:
        """
        Instantiate transaction request.

        :param transaction_id: the id of the transaction.
        :param is_sender_buyer: whether the transaction is sent by a buyer.
        :param counterparty: the counterparty of the transaction.
        :param amount: the amount of money involved.
        :param quantities_by_good_pbk: a map from good pbk to the quantity of that good involved in the transaction.
        :param sender: the sender of the transaction.

        :return: None
        """
        self.transaction_id = transaction_id
        self.is_sender_buyer = is_sender_buyer
        self.counterparty = counterparty
        self.amount = amount
        self.quantities_by_good_pbk = quantities_by_good_pbk
        self.sender = sender

        self._check_consistency()

    @property
    def buyer_pbk(self) -> Address:
        """Get the publick key of the buyer."""
        result = self.sender if self.is_sender_buyer else self.counterparty
        return result

    @property
    def seller_pbk(self) -> Address:
        """Get the publick key of the seller."""
        result = self.counterparty if self.is_sender_buyer else self.sender
        return result

    def _check_consistency(self) -> None:
        """
        Check the consistency of the transaction parameters.

        :return: None
        :raises AssertionError if some constraint is not satisfied.
        """
        assert self.sender != self.counterparty
        assert self.amount >= 0
        assert len(self.quantities_by_good_pbk.keys()) == len(set(self.quantities_by_good_pbk.keys()))
        assert all(quantity >= 0 for quantity in self.quantities_by_good_pbk.values())

    def to_dict(self) -> Dict[str, Any]:
        """From object to dictionary."""
        return {
            "transaction_id": self.transaction_id,
            "is_sender_buyer": self.is_sender_buyer,
            "counterparty": self.counterparty,
            "amount": self.amount,
            "quantities_by_good_pbk": self.quantities_by_good_pbk,
            "sender": self.sender
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'Transaction':
        """Return a class instance from a dictionary."""
        return cls(
            transaction_id=d["transaction_id"],
            is_sender_buyer=d["is_sender_buyer"],
            counterparty=d["counterparty"],
            amount=d["amount"],
            quantities_by_good_pbk=d["quantities_by_good_pbk"],
            sender=d["sender"]
        )

    def from_message(cls, message: TACMessage, sender: Address) -> 'Transaction':
        """
        Create a transaction from a proposal.

        :param message: the message
        :return: Transaction
        """
        assert message.get('type') == TACMessage.Type.TRANSACTION
        return Transaction(message.get("transaction_id"), message.get("is_sender_buyer"), message.get("counterparty"), message.get("amount"), message.get("quantities_by_good_pbk"), sender)

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
        result = True
        result = result and self.transaction_id == other.transaction_id
        result = result and self.is_sender_buyer != other.is_sender_buyer
        result = result and self.counterparty == other.sender
        result = result and other.counterparty == self.sender
        result = result and self.amount == other.amount
        result = result and self.quantities_by_good_pbk == other.quantities_by_good_pbk

        return result

    def __eq__(self, other):
        """Compare to another object."""
        return isinstance(other, Transaction) \
            and self.transaction_id == other.transaction_id \
            and self.is_sender_buyer == other.is_sender_buyer \
            and self.counterparty == other.counterparty \
            and self.amount == other.amount \
            and self.quantities_by_good_pbk == other.quantities_by_good_pbk \
            and self.sender == other.sender \
            and self.buyer_pbk == other.buyer_pbk \
            and self.seller_pbk == other.seller_pbk


class AgentState:
    """Represent the state of an agent during the game."""

    def __init__(self, money: float, endowment: Endowment, utility_params: UtilityParams):
        """
        Instantiate an agent state object.

        :param money: the money of the agent in this state.
        :param endowment: the endowment for every good.
        :param utility_params: the utility params for every good.
        """
        assert len(endowment) == len(utility_params)
        self._balance = money
        self._utility_params = copy.copy(utility_params)
        self._good_holdings = copy.copy(endowment)

    @property
    def balance(self) -> int:
        """Get the money balance."""
        return self._balance

    @property
    def good_holdings(self) -> Endowment:
        """Get holding of each good."""
        return copy.copy(self._current_holdings)

    @property
    def utility_params(self) -> UtilityParams:
        """Get utility parameter for each good."""
        return copy.copy(self._utility_params)

    def get_score(self) -> float:
        """
        Compute the score of the current state.

        The score is computed as the sum of all the utilities for the good holdings
        with positive quantity plus the money left.
        :return: the score.
        """
        goods_score = logarithmic_utility(self.utility_params, self.good_holdings)
        money_score = self.balance
        score = goods_score + money_score
        return score

    def get_score_diff_from_transaction(self, tx: Transaction, tx_fee: float) -> float:
        """
        Simulate a transaction and get the resulting score (taking into account the fee).

        :param tx: a transaction object.
        :return: the score.
        """
        current_score = self.get_score()
        new_state = self.apply([tx], tx_fee)
        new_score = new_state.get_score()
        return new_score - current_score

    def check_transaction_is_consistent(self, tx: Transaction, tx_fee: float) -> bool:
        """
        Check if the transaction is consistent.

        E.g. check that the agent state has enough money if it is a buyer
        or enough holdings if it is a seller.
        :return: True if the transaction is legal wrt the current state, false otherwise.
        """
        share_of_tx_fee = round(tx_fee / 2.0, 2)
        if tx.is_sender_buyer:
            # check if we have the money.
            result = self.balance >= tx.amount + share_of_tx_fee
        else:
            # check if we have the goods.
            result = True
            for good_id, quantity in enumerate(tx.quantities_by_good_pbk.values()):
                result = result and (self._current_holdings[good_id] >= quantity)
        return result

    def apply(self, transactions: List[Transaction], tx_fee: float) -> 'AgentState':
        """
        Apply a list of transactions to the current state.

        :param transactions: the sequence of transaction.
        :return: the final state.
        """
        new_state = copy.copy(self)
        for tx in transactions:
            new_state.update(tx, tx_fee)

        return new_state

    def update(self, tx: Transaction, tx_fee: float) -> None:
        """
        Update the agent state from a transaction.

        :param tx: the transaction.
        :param tx_fee: the transaction fee.
        :return: None
        """
        share_of_tx_fee = round(tx_fee / 2.0, 2)
        if tx.is_sender_buyer:
            diff = tx.amount + share_of_tx_fee
            self.balance -= diff
        else:
            diff = tx.amount - share_of_tx_fee
            self.balance += diff

        for good_id, quantity in enumerate(tx.quantities_by_good_pbk.values()):
            quantity_delta = quantity if tx.is_sender_buyer else -quantity
            self._current_holdings[good_id] += quantity_delta

    def __copy__(self):
        """Copy the object."""
        return AgentState(self.balance, self.current_holdings, self.utility_params)

    def __str__(self):
        """From object to string."""
        return "AgentState{}".format(pprint.pformat({
            "money": self.balance,
            "utility_params": self.utility_params,
            "current_holdings": self._current_holdings
        }))

    def __eq__(self, other) -> bool:
        """Compare equality of two instances of the class."""
        return isinstance(other, AgentState) and \
            self.balance == other.balance and \
            self.utility_params == other.utility_params and \
            self._current_holdings == other._current_holdings


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
        self._confirmed.add(transaction)
        self._confirmed_per_agent[transaction.sender].add(transaction)
        self._confirmed_per_agent[transaction.counterparty].add(transaction)


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
    def configuration(self) -> Configuration:
        """Get game configuration."""
        assert self._configuration is not None, "Call create before calling initialization."
        return self._configuration

    @property
    def initialization(self) -> Initialization:
        """Get game initialization."""
        assert self._initialization is not None, "Call create before calling initialization."
        return self._initialization

    @property
    def initial_agent_states(self) -> Dict[str, 'AgentState']:
        """Get initial state of each agent."""
        return self._initial_agent_states

    @property
    def phase(self) -> Phase:
        """Get the game phase."""
        return self._phase

    @phase.is_setter
    def phase(self, phase: Phase) -> None:
        """Set the game phase."""
        self._phase = phase

    @property
    def is_running(self) -> bool:
        """Check if the game is running."""
        return self.phase == Phase.GAME

    def create(self):
        """Create a game."""
        assert not self.is_running
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
                    self.initialization.initial_money_amounts[i],
                    self.initialization.endowments[i],
                    self.initialization.utility_params[i]
                ))
            for agent_pbk, i in zip(self.configuration.agent_pbks, range(self.configuration.nb_agents)))

        self._current_agent_states = dict(
            (agent_pbk,
                AgentState(
                    self.initialization.initial_money_amounts[i],
                    self.initialization.endowments[i],
                    self.initialization.utility_params[i]
                ))
            for agent_pbk, i in zip(self.configuration.agent_pbks, range(self.configuration.nb_agents)))

        self._current_good_states = dict(
            (good_pbk,
                GoodState())
            for good_pbk in self.configuration.good_pbks)

    def reset(self) -> None:
        """Reset the game."""
        self._configuration = None  # type: Optional[Configuration]
        self._initialization = None  # type: Optional[Initialization]
        self._initial_agent_states = None  # type: Optional[Dict[str, AgentState]]
        self._current_agent_states = None  # type: Optional[Dict[str, AgentState]]
        self._current_good_states = None  # type: Optional[Dict[str, GoodState]]
        self._transactions = Transactions()

    @property
    def initial_agent_scores(self) -> Dict[str, float]:
        """Get the initial scores for every agent."""
        return {agent_pbk: agent_state.get_score() for agent_pbk, agent_state in self._initial_agent_states.items()}

    @property
    def current_agent_scores(self) -> Dict[str, float]:
        """Get the current scores for every agent."""
        return {agent_pbk: agent_state.get_score() for agent_pbk, agent_state in self._current_agent_states.items()}

    @property
    def holdings_matrix(self) -> List[Endowment]:
        """
        Get the holdings matrix of shape (nb_agents, nb_goods).

        :return: the holdings matrix.
        """
        result = list(map(lambda state: state.current_holdings, self.agent_states.values()))
        return result

    @property
    def agent_balances(self) -> Dict[str, float]:
        """Get the current agent balances."""
        result = {agent_pbk: agent_state.balance for agent_pbk, agent_state in self.agent_states.items()}
        return result

    @property
    def good_prices(self) -> List[float]:
        """Get the current good prices."""
        result = list(map(lambda state: state.price, self.good_states.values()))
        return result

    @property
    def holdings_summary(self) -> str:
        """Get holdings summary (a string representing the holdings for every agent)."""
        result = ""
        for agent_pbk, agent_state in self.agent_states.items():
            result = result + self.configuration.agent_pbk_to_name[agent_pbk] + " " + str(agent_state._current_holdings) + "\n"
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

    def get_agent_state_from_agent_pbk(self, agent_pbk: Address) -> 'AgentState':
        """
        Get agent state from agent pbk.

        :param agent_pbk: the agent's pbk.
        :return: the agent state of the agent.
        """
        return self.agent_states[agent_pbk]

    def is_transaction_valid(self, tx: Transaction) -> bool:
        """
        Check whether the transaction is valid given the state of the game.

        :param tx: the transaction.
        :return: True if the transaction is valid, False otherwise.
        :raises: AssertionError: if the data in the transaction are not allowed (e.g. negative amount).
        """
        # check if the buyer has enough balance to pay the transaction.
        share_of_tx_fee = round(self.configuration.tx_fee / 2.0, 2)
        if self.agent_states[tx.buyer_pbk].balance < tx.amount + share_of_tx_fee:
            return False

        # check if we have enough instances of goods, for every good involved in the transaction.
        seller_holdings = self.agent_states[tx.seller_pbk].current_holdings
        for good_id, bought_quantity in enumerate(tx.quantities_by_good_pbk.values()):
            if seller_holdings[good_id] < bought_quantity:
                return False

        return True

    def settle_transaction(self, tx: Transaction) -> None:
        """
        Settle a valid transaction.

        :param tx: the game transaction.
        :return: None
        :raises: AssertionError if the transaction is not valid.
        """
        assert self.is_transaction_valid(tx)
        self.transactions.append(tx)
        buyer_state = self.agent_states[tx.buyer_pbk]
        seller_state = self.agent_states[tx.seller_pbk]

        nb_instances_traded = sum(tx.quantities_by_good_pbk.values())

        # update holdings and prices
        for good_id, (good_pbk, quantity) in enumerate(tx.quantities_by_good_pbk.items()):
            buyer_state._current_holdings[good_id] += quantity
            seller_state._current_holdings[good_id] -= quantity
            if quantity > 0:
                # for now the price is simply the amount proportional to the share in the bundle
                price = tx.amount / nb_instances_traded
                good_state = self.good_states[good_pbk]
                good_state.price = price

        share_of_tx_fee = round(self.configuration.tx_fee / 2.0, 2)
        # update balances and charge share of fee to buyer and seller
        buyer_state.balance -= tx.amount + share_of_tx_fee
        seller_state.balance += tx.amount - share_of_tx_fee
