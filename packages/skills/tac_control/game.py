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
import sys
from typing import cast, Dict, List, Optional, TYPE_CHECKING

from aea.helpers.preference_representations.base import logarithmic_utility, linear_utility
from aea.mail.base import Address
from aea.skills.base import SharedClass

if TYPE_CHECKING or "pytest" in sys.modules:
    from packages.protocols.tac.message import TACMessage
    from packages.skills.tac_control.helpers import generate_good_id_to_name, determine_scaling_factor, \
        generate_money_endowments, generate_good_endowments, generate_utility_params, generate_equilibrium_prices_and_holdings
    from packages.skills.tac_control.parameters import Parameters
else:
    from tac_protocol.message import TACMessage
    from tac_control_skill.helpers import generate_good_id_to_name, determine_scaling_factor, \
        generate_money_endowments, generate_good_endowments, generate_utility_params, generate_equilibrium_prices_and_holdings
    from tac_control_skill.parameters import Parameters

GoodId = str
CurrencyId = str
Amount = int
Quantity = int
EquilibriumQuantity = float
Parameter = float
TransactionId = str
Endowment = Dict[GoodId, Quantity]
UtilityParams = Dict[GoodId, Parameter]
EquilibriumHoldings = Dict[GoodId, EquilibriumQuantity]

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
                 tx_fee: int,
                 agent_addr_to_name: Dict[Address, str],
                 good_id_to_name: Dict[GoodId, str]):
        """
        Instantiate a game configuration.

        :param version_id: the version of the game.
        :param tx_fee: the fee for a transaction.
        :param agent_addr_to_name: a dictionary mapping agent addresses to agent names (as strings).
        :param good_id_to_name: a dictionary mapping good ids to good names (as strings).
        """
        self._version_id = version_id
        self._tx_fee = tx_fee
        self._agent_addr_to_name = agent_addr_to_name
        self._good_id_to_name = good_id_to_name

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
    def good_id_to_name(self) -> Dict[str, str]:
        """Map good ids to names and uids (the external good identifiers)."""
        return self._good_id_to_name

    def _check_consistency(self):
        """
        Check the consistency of the game configuration.

        :return: None
        :raises: AssertionError: if some constraint is not satisfied.
        """
        assert self.version_id is not None, "A version id must be set."
        assert self.tx_fee >= 0, "Tx fee must be non-negative."
        assert len(self.agent_addr_to_name) > 1, "Must have at least two agents."
        assert len(self.agent_addr_to_name) > 1, "Must have at least two goods."


class Initialization:
    """Class containing the initialization of the game."""

    def __init__(self,
                 agent_addr_to_initial_money_amounts: Dict[Address, Amount],
                 agent_addr_to_endowments: Dict[Address, Endowment],
                 agent_addr_to_utility_params: Dict[Address, UtilityParams],
                 good_id_to_eq_prices: Dict[GoodId, float],
                 agent_addr_to_eq_good_holdings: Dict[Address, EquilibriumHoldings],
                 agent_addr_to_eq_money_holdings: Dict[Address, float]):
        """
        Instantiate a game initialization.

        :param agent_addr_to_initial_money_amounts: the initial amount of money of every agent.
        :param agent_addr_to_endowments: the endowments of the agents. A matrix where the first index is the agent id
                            and the second index is the good id. A generic element e_ij at row i and column j is
                            an integer that denotes the endowment of good j for agent i.
        :param agent_addr_to_utility_params: the utility params representing the preferences of the agents. A matrix where the first
                            index is the agent id and the second index is the good id. A generic element e_ij
                            at row i and column j is an integer that denotes the utility of good j for agent i.
        :param good_id_to_eq_prices: the competitive equilibrium prices of the goods. A list.
        :param agent_addr_to_eq_good_holdings: the competitive equilibrium good holdings of the agents. A matrix where the first index is the agent id
                            and the second index is the good id. A generic element g_ij at row i and column j is
                            a float that denotes the (divisible) amount of good j for agent i.
        :param agent_addr_to_eq_money_holdings: the competitive equilibrium money holdings of the agents. A list.
        """
        self._agent_addr_to_initial_money_amounts = agent_addr_to_initial_money_amounts
        self._agent_addr_to_endowments = agent_addr_to_endowments
        self._agent_addr_to_utility_params = agent_addr_to_utility_params
        self._good_id_to_eq_prices = good_id_to_eq_prices
        self._agent_addr_to_eq_good_holdings = agent_addr_to_eq_good_holdings
        self._agent_addr_to_eq_money_holdings = agent_addr_to_eq_money_holdings

        self._check_consistency()

    @property
    def agent_addr_to_initial_money_amounts(self) -> Dict[Address, Amount]:
        """Get list of the initial amount of money of every agent."""
        return self._agent_addr_to_initial_money_amounts

    @property
    def agent_addr_to_endowments(self) -> Dict[Address, Endowment]:
        """Get endowments of the agents."""
        return self._agent_addr_to_endowments

    @property
    def agent_addr_to_utility_params(self) -> Dict[Address, UtilityParams]:
        """Get utility parameter list of the agents."""
        return self._agent_addr_to_utility_params

    @property
    def good_id_to_eq_prices(self) -> Dict[Address, float]:
        """Get theoretical equilibrium prices (a benchmark)."""
        return self._good_id_to_eq_prices

    @property
    def agent_addr_to_eq_good_holdings(self) -> Dict[Address, EquilibriumHoldings]:
        """Get theoretical equilibrium good holdings (a benchmark)."""
        return self._agent_addr_to_eq_good_holdings

    @property
    def agent_addr_to_eq_money_holdings(self) -> Dict[Address, float]:
        """Get theoretical equilibrium money holdings (a benchmark)."""
        return self._agent_addr_to_eq_money_holdings

    def _check_consistency(self):
        """
        Check the consistency of the game configuration.

        :return: None
        :raises: AssertionError: if some constraint is not satisfied.
        """
        assert all(initial_money_amount >= 0 for initial_money_amount in self.agent_addr_to_initial_money_amounts.values()), "Initial money amount must be non-negative."
        assert all(e > 0 for endowments in self.agent_addr_to_endowments.values() for e in endowments.values()), "Endowments must be strictly positive."
        assert all(p > 0 for params in self.agent_addr_to_utility_params.values() for p in params.values()), "UtilityParams must be strictly positive."

        assert len(self.agent_addr_to_endowments.values()) == len(self.agent_addr_to_initial_money_amounts.values()), "Length of endowments and initial_money_amounts must be the same."
        assert len(self.agent_addr_to_endowments.values()) == len(self.agent_addr_to_utility_params.values()), "Length of endowments and utility_params must be the same."

        assert all(len(self.good_id_to_eq_prices.values()) == len(eq_good_holdings) for eq_good_holdings in self.agent_addr_to_eq_good_holdings.values()), "Length of eq_prices and an element of eq_good_holdings must be the same."
        assert len(self.agent_addr_to_eq_good_holdings.values()) == len(self.agent_addr_to_eq_money_holdings.values()), "Length of eq_good_holdings and eq_money_holdings must be the same."

        assert all(len(self.agent_addr_to_utility_params[agent_addr]) == len(endowments) for agent_addr, endowments in self.agent_addr_to_endowments.items()), "Dimensions for utility_params and endowments rows must be the same."


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
                 id: TransactionId,
                 sender_addr: Address,
                 counterparty_addr: Address,
                 amount_by_currency_id: Dict[str, int],
                 sender_fee: int,
                 counterparty_fee: int,
                 quantities_by_good_id: Dict[str, int],
                 nonce: int,
                 sender_signature: bytes,
                 counterparty_signature: bytes) -> None:
        """
        Instantiate transaction request.

        :param id: the id of the transaction.
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
        self.id = id
        self.sender_addr = sender_addr
        self.counterparty_addr = counterparty_addr
        self.amount_by_currency_id = amount_by_currency_id
        self.sender_fee = sender_fee
        self.counterparty_fee = counterparty_fee
        self.quantities_by_good_id = quantities_by_good_id
        self.nonce = nonce
        self.sender_signature = sender_signature
        self.counterparty_signature = counterparty_signature
        self._check_consistency()
        self.is_sender_buyer = all(value <= 0 for value in amount_by_currency_id.values())

    @property
    def buyer_addr(self) -> Address:
        """Get the address of the buyer."""
        result = self.sender_addr if self.is_sender_buyer else self.counterparty_addr
        return result

    @property
    def seller_addr(self) -> Address:
        """Get the address of the seller."""
        result = self.counterparty_addr if self.is_sender_buyer else self.sender_addr
        return result

    @property
    def buyer_tx_fee(self) -> int:
        """Get the tx fee of the buyer."""
        result = self.sender_fee if self.is_sender_buyer else self.counterparty_fee
        return result

    @property
    def seller_tx_fee(self) -> int:
        """Get the tx fee of the seller."""
        result = self.counterparty_fee if self.is_sender_buyer else self.sender_fee
        return result

    @property
    def amount(self) -> int:
        """Get the amount."""
        assert len(self.amount_by_currency_id) == 1
        return list(self.amount_by_currency_id.values())[0]

    @property
    def currency_id(self) -> str:
        """Get the currency."""
        assert len(self.amount_by_currency_id) == 1
        return list(self.amount_by_currency_id.keys())[0]

    def _check_consistency(self) -> None:
        """
        Check the consistency of the transaction parameters.

        :return: None
        :raises AssertionError if some constraint is not satisfied.
        """
        assert self.sender_addr != self.counterparty_addr
        assert len(self.amount_by_currency_id.keys()) == 1  # For now we restrict to one currency per transaction.
        assert self.sender_fee >= 0
        assert self.counterparty_fee >= 0
        assert len(self.quantities_by_good_id.keys()) == len(set(self.quantities_by_good_id.keys()))
        assert (all(amount >= 0 for amount in self.amount_by_currency_id.values()) and all(quantity <= 0 for quantity in self.quantities_by_good_id.values())) or \
            (all(amount <= 0 for amount in self.amount_by_currency_id.values()) and all(quantity >= 0 for quantity in self.quantities_by_good_id.values()))

    @classmethod
    def from_message(cls, message: TACMessage) -> 'Transaction':
        """
        Create a transaction from a proposal.

        :param message: the message
        :return: Transaction
        """
        assert message.type == TACMessage.Type.TRANSACTION
        return Transaction(message.tx_id,
                           message.tx_sender_addr,
                           message.tx_counterparty_addr,
                           message.amount_by_currency_id,
                           message.tx_sender_fee,
                           message.tx_counterparty_fee,
                           message.quantities_by_good_id,
                           message.tx_nonce,
                           message.tx_sender_signature,
                           message.tx_counterparty_signature)

    def __eq__(self, other):
        """Compare to another object."""
        return isinstance(other, Transaction) \
            and self.id == other.id \
            and self.sender_addr == other.sender_addr \
            and self.counterparty_addr == other.counterparty_addr \
            and self.amount_by_currency_id == other.amount_by_currency_id \
            and self.sender_fee == other.sender_fee \
            and self.counterparty_fee == other.counterparty_fee \
            and self.quantities_by_good_id == other.quantities_by_good_id \
            and self.sender_signature == other.sender_signature \
            and self.counterparty_signature == other.counterparty_signature


class AgentState:
    """Represent the state of an agent during the game."""

    def __init__(self, amount_by_currency_id: Dict[CurrencyId, Amount],
                 exchange_params_by_currency_id: Dict[CurrencyId, Parameter],
                 quantities_by_good_id: Dict[GoodId, Quantity],
                 utility_params_by_good_id: Dict[GoodId, Parameter]):
        """
        Instantiate an agent state object.

        :param amount_by_currency_id: the amount for each currency
        :param exchange_params_by_currency_id: the exchange parameters of the different currencies
        :param quantities_by_good_id: the quantities for each good.
        :param utility_params_by_good_id: the utility params for every good.
        """
        assert len(amount_by_currency_id.keys()) == len(exchange_params_by_currency_id.keys())
        assert len(quantities_by_good_id.keys()) == len(utility_params_by_good_id.keys())
        self._amount_by_currency_id = copy.copy(amount_by_currency_id)
        self._exchange_params_by_currency_id = copy.copy(exchange_params_by_currency_id)
        self._quantities_by_good_id = quantities_by_good_id
        self._utility_params_by_good_id = copy.copy(utility_params_by_good_id)

    @property
    def amount_by_currency_id(self) -> Dict[CurrencyId, Amount]:
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
        goods_score = logarithmic_utility(self.utility_params_by_good_id, self.quantities_by_good_id)
        money_score = linear_utility(self.exchange_params_by_currency_id, self.amount_by_currency_id)
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
            result = self.amount_by_currency_id[tx.currency_id] >= tx.amount + tx.buyer_tx_fee
        else:
            # check if we have the diff and the goods as the seller.
            result = self.amount_by_currency_id[tx.currency_id] + tx.amount >= tx.seller_tx_fee
            for good_id, quantity in tx.quantities_by_good_id.items():
                result = result and (self.quantities_by_good_id[good_id] >= quantity)
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
        new_amount_by_currency_id = self.amount_by_currency_id
        if tx.is_sender_buyer:
            total = tx.amount + tx.buyer_tx_fee
            new_amount_by_currency_id[tx.currency_id] -= total
        else:
            diff = tx.amount - tx.seller_tx_fee
            new_amount_by_currency_id[tx.currency_id] += diff
        self._amount_by_currency_id = new_amount_by_currency_id

        new_quantities_by_good_id = self.quantities_by_good_id
        for good_id, quantity in tx.quantities_by_good_id.items():
            quantity_delta = quantity if tx.is_sender_buyer else -quantity
            new_quantities_by_good_id[good_id] += quantity_delta
        self._quantities_by_good_id = new_quantities_by_good_id

    def __copy__(self):
        """Copy the object."""
        return AgentState(self.amount_by_currency_id,
                          self.exchange_params_by_currency_id,
                          self.quantities_by_good_id,
                          self.utility_params_by_good_id)

    def __str__(self):
        """From object to string."""
        return "AgentState{}".format(pprint.pformat({
            "amount_by_currency_id": self.amount_by_currency_id,
            "exchange_params_by_currency_id": self.exchange_params_by_currency_id,
            "quantities_by_good_id": self.quantities_by_good_id,
            "utility_params_by_good_id": self.utility_params_by_good_id
        }))

    def __eq__(self, other) -> bool:
        """Compare equality of two instances of the class."""
        return isinstance(other, AgentState) and \
            self.amount_by_currency_id == other.amount_by_currency_id and \
            self.exchange_params_by_currency_id == other.exchange_params_by_currency_id and \
            self.quantities_by_good_id == other.quantities_by_good_id and \
            self.utility_params_by_good_id == other.utility_params_by_good_id


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
        self._pending[transaction.id] = transaction

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
        self._confirmed_per_agent[transaction.sender_addr].append(transaction)
        self._confirmed_per_agent[transaction.counterparty_addr].append(transaction)


class Registration:
    """Class managing the registration of the game."""

    def __init__(self):
        """Instantiate the registration class."""
        self._agent_addr_to_name = defaultdict()  # type: Dict[str, str]

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

        good_id_to_name = generate_good_id_to_name(parameters.nb_goods)
        self._configuration = Configuration(parameters.version_id, parameters.tx_fee, self.registration.agent_addr_to_name, good_id_to_name)

        scaling_factor = determine_scaling_factor(parameters.money_endowment)
        agent_addr_to_money_endowments = generate_money_endowments(list(self.configuration.agent_addr_to_name.keys()), parameters.money_endowment)
        agent_addr_to_good_endowments = generate_good_endowments(list(self.configuration.agent_addr_to_name.keys()), list(self.configuration.good_id_to_name.keys()), parameters.base_good_endowment, parameters.lower_bound_factor, parameters.upper_bound_factor)
        agent_addr_to_utility_params = generate_utility_params(list(self.configuration.agent_addr_to_name.keys()), list(self.configuration.good_id_to_name.keys()), scaling_factor)
        good_id_to_eq_prices, agent_addr_to_eq_good_holdings, agent_addr_to_eq_money_holdings = generate_equilibrium_prices_and_holdings(agent_addr_to_good_endowments, agent_addr_to_utility_params, agent_addr_to_money_endowments, scaling_factor)
        self._initialization = Initialization(agent_addr_to_money_endowments, agent_addr_to_good_endowments, agent_addr_to_utility_params, good_id_to_eq_prices, agent_addr_to_eq_good_holdings, agent_addr_to_eq_money_holdings)

        self._initial_agent_states = dict(
            (agent_addr,
                AgentState(
                    {DEFAULT_CURRENCY: self.initialization.agent_addr_to_initial_money_amounts[agent_addr]},
                    {DEFAULT_CURRENCY: DEFAULT_CURRENCY_EXCHANGE_RATE},
                    self.initialization.agent_addr_to_endowments[agent_addr],
                    self.initialization.agent_addr_to_utility_params[agent_addr]
                ))
            for agent_addr in self.configuration.agent_addr_to_name.keys())

        self._current_agent_states = dict(
            (agent_addr,
                AgentState(
                    {DEFAULT_CURRENCY: self.initialization.agent_addr_to_initial_money_amounts[agent_addr]},
                    {DEFAULT_CURRENCY: DEFAULT_CURRENCY_EXCHANGE_RATE},
                    self.initialization.agent_addr_to_endowments[agent_addr],
                    self.initialization.agent_addr_to_utility_params[agent_addr]
                ))
            for agent_addr in self.configuration.agent_addr_to_name.keys())

        self._current_good_states = dict(
            (good_id,
                GoodState())
            for good_id in self.configuration.good_id_to_name.keys())

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
        return {agent_addr: agent_state.get_score() for agent_addr, agent_state in self.initial_agent_states.items()}

    @property
    def current_agent_scores(self) -> Dict[str, float]:
        """Get the current scores for every agent."""
        return {agent_addr: agent_state.get_score() for agent_addr, agent_state in self.current_agent_states.items()}

    @property
    def holdings_matrix(self) -> List[List[Quantity]]:
        """
        Get the holdings matrix of shape (nb_agents, nb_goods).

        :return: the holdings matrix.
        """
        result = list(map(lambda state: list(state.quantities_by_good_id.values()), self.current_agent_states.values()))
        return result

    @property
    def agent_amounts(self) -> Dict[str, int]:
        """Get the current agent amounts."""
        result = {agent_addr: agent_state.amount_by_currency_id[DEFAULT_CURRENCY] for agent_addr, agent_state in self.current_agent_states.items()}
        return result

    @property
    def good_prices(self) -> List[float]:
        """Get the current good prices."""
        result = list(map(lambda state: state.price, self.current_good_states.values()))
        return result

    @property
    def holdings_summary(self) -> str:
        """Get holdings summary (a string representing the holdings for every agent)."""
        result = "\n" + "Current good allocation: \n"
        for agent_addr, agent_state in self.current_agent_states.items():
            result = result + "- " + self.configuration.agent_addr_to_name[agent_addr] + ":" + "\n"
            for good_id, quantity in agent_state.quantities_by_good_id.items():
                result += "    " + good_id + ": " + str(quantity) + "\n"
        result = result + "\n"
        return result

    @property
    def equilibrium_summary(self) -> str:
        """Get equilibrium summary."""
        result = "\n" + "Equilibrium prices: \n"
        for good_id, eq_price in self.initialization.good_id_to_eq_prices.items():
            result = result + good_id + " " + str(eq_price) + "\n"
        result = result + "\n"
        result = result + "Equilibrium good allocation: \n"
        for agent_addr, eq_allocations in self.initialization.agent_addr_to_eq_good_holdings.items():
            result = result + "- " + self.configuration.agent_addr_to_name[agent_addr] + ":\n"
            for good_id, quantity in eq_allocations.items():
                result = result + "    " + good_id + ": " + str(quantity) + "\n"
        result = result + "\n"
        result = result + "Equilibrium money allocation: \n"
        for agent_addr, eq_allocation in self.initialization.agent_addr_to_eq_money_holdings.items():
            result = result + self.configuration.agent_addr_to_name[agent_addr] + " " + str(eq_allocation) + "\n"
        result = result + "\n"
        return result

    def is_transaction_valid(self, tx: Transaction) -> bool:
        """
        Check whether the transaction is valid given the state of the game.

        :param tx: the transaction.
        :return: True if the transaction is valid, False otherwise.
        :raises: AssertionError: if the data in the transaction are not allowed (e.g. negative amount).
        """
        buyer_state = self.current_agent_states[tx.buyer_addr]
        seller_state = self.current_agent_states[tx.seller_addr]
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
        buyer_state = self.current_agent_states[tx.buyer_addr]
        seller_state = self.current_agent_states[tx.seller_addr]

        buyer_state.update(tx)
        seller_state.update(tx)

        self._current_agent_states.update({tx.buyer_addr: buyer_state})
        self._current_agent_states.update({tx.seller_addr: seller_state})
