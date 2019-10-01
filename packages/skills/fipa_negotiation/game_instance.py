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

"""This class manages the state and some services related to the TAC for an agent."""

import datetime
import random
from typing import Any, List, Optional, Set, Tuple, Dict, Union, Sequence, cast

from aea.channels.oef.connection import MailStats
from aea.mail.base import Address
from aea.protocols.oef.models import Description, Query

from tac.agents.participant.v1.base.dialogues import Dialogues, Dialogue
from tac.agents.participant.v1.base.helpers import build_dict, build_query, get_goods_quantities_description
from tac.agents.participant.v1.base.states import AgentState, WorldState
from tac.agents.participant.v1.base.stats_manager import StatsManager
from tac.agents.participant.v1.base.strategy import Strategy
from tac.agents.participant.v1.base.transaction_manager import TransactionManager
from tac.gui.dashboards.agent import AgentDashboard
from tac.platform.game.base import GamePhase, GameConfiguration
from tac.platform.game.base import GameData, Transaction
from tac.platform.protocols.tac.message import TACMessage


class Search:
    """This class deals with the search state."""

    def __init__(self):
        """Instantiate the search class."""
        self._id = 0
        self.ids_for_tac = set()  # type: Set[int]
        self.ids_for_sellers = set()  # type: Set[int]
        self.ids_for_buyers = set()  # type: Set[int]

    @property
    def id(self) -> int:
        """Get the search id."""
        return self._id

    def get_next_id(self) -> int:
        """
        Generate the next search id and stores it.

        :return: a search id
        """
        self._id += 1
        return self._id


class GameInstance:
    """The GameInstance maintains state of the game from the agent's perspective."""

    def __init__(self, agent_name: str,
                 strategy: Strategy,
                 mail_stats: MailStats,
                 expected_version_id: str,
                 services_interval: int = 10,
                 pending_transaction_timeout: int = 10,
                 dashboard: Optional[AgentDashboard] = None) -> None:
        """
        Instantiate a game instance.

        :param agent_name: the name of the agent.
        :param strategy: the strategy of the agent.
        :param mail_stats: the mail stats of the mailbox.
        :param expected_version_id: the expected version of the TAC.
        :param services_interval: the interval at which services are updated.
        :param pending_transaction_timeout: the timeout after which transactions are removed from the lock manager.
        :param dashboard: the agent dashboard.

        :return: None
        """
        self.agent_name = agent_name
        self.controller_pbk = None  # type: Optional[str]

        self._strategy = strategy

        self._search = Search()
        self._dialogues = Dialogues()

        self._game_phase = GamePhase.PRE_GAME

        self._expected_version_id = expected_version_id
        self._game_configuration = None  # type: Optional[GameConfiguration]
        self._initial_agent_state = None  # type: Optional[AgentState]
        self._agent_state = None  # type: Optional[AgentState]
        self._world_state = None  # type: Optional[WorldState]

        self._services_interval = datetime.timedelta(0, services_interval)
        self._last_update_time = datetime.datetime.now() - self._services_interval
        self._last_search_time = datetime.datetime.now() - datetime.timedelta(0, round(services_interval / 2.0))

        self.goods_supplied_description = None
        self.goods_demanded_description = None

        self.transaction_manager = TransactionManager(agent_name, pending_transaction_timeout=pending_transaction_timeout)

        self.stats_manager = StatsManager(mail_stats, dashboard)

        self.dashboard = dashboard
        if self.dashboard is not None:
            self.dashboard.start()
            self.stats_manager.start()

    def init(self, game_data: GameData, agent_pbk: Address) -> None:
        """
        Populate data structures with the game data.

        :param game_data: the game instance data
        :param agent_pbk: the public key of the agent

        :return: None
        """
        # TODO: extend TAC messages to include reference to version id; then replace below with assert
        game_data.version_id = self.expected_version_id
        self._game_configuration = GameConfiguration(game_data.version_id, game_data.nb_agents, game_data.nb_goods, game_data.tx_fee,
                                                     game_data.agent_pbk_to_name, game_data.good_pbk_to_name)
        self._initial_agent_state = AgentState(game_data.money, game_data.endowment, game_data.utility_params)
        self._agent_state = AgentState(game_data.money, game_data.endowment, game_data.utility_params)
        if self.strategy.is_world_modeling:
            opponent_pbks = self.game_configuration.agent_pbks
            opponent_pbks.remove(agent_pbk)
            self._world_state = WorldState(opponent_pbks, self.game_configuration.good_pbks, self.initial_agent_state)

    def on_state_update(self, message: TACMessage, agent_pbk: Address) -> None:
        """
        Update the game instance with a State Update from the controller.

        :param state_update: the state update
        :param agent_pbk: the public key of the agent

        :return: None
        """
        self.init(message.get("initial_state"), agent_pbk)
        self._game_phase = GamePhase.GAME
        for tx in message.get("transactions"):
            self.agent_state.update(tx, message.get("initial_state").get("tx_fee"))

    @property
    def expected_version_id(self) -> str:
        """Get the expected version id of the TAC."""
        return self._expected_version_id

    @property
    def strategy(self) -> Strategy:
        """Get the strategy."""
        return self._strategy

    @property
    def search(self) -> Search:
        """Get the search."""
        return self._search

    @property
    def dialogues(self) -> Dialogues:
        """Get the dialogues."""
        return self._dialogues

    @property
    def game_phase(self) -> GamePhase:
        """Get the game phase."""
        return self._game_phase

    @property
    def game_configuration(self) -> GameConfiguration:
        """Get the game configuration."""
        assert self._game_configuration is not None, "Game configuration not assigned!"
        return self._game_configuration

    @property
    def initial_agent_state(self) -> AgentState:
        """Get the initial agent state."""
        assert self._initial_agent_state is not None, "Initial agent state not assigned!"
        return self._initial_agent_state

    @property
    def agent_state(self) -> AgentState:
        """Get the agent state."""
        assert self._agent_state is not None, "Agent state not assigned!"
        return self._agent_state

    @property
    def world_state(self) -> WorldState:
        """Get the world state."""
        assert self._world_state is not None, "World state not assigned!"
        return self._world_state

    @property
    def services_interval(self) -> datetime.timedelta:
        """Get the services interval."""
        return self._services_interval

    @property
    def last_update_time(self) -> datetime.datetime:
        """Get the last services update time."""
        return self._last_update_time

    @property
    def last_search_time(self) -> datetime.datetime:
        """Get the last services search time."""
        return self._last_search_time

    def is_time_to_update_services(self) -> bool:
        """
        Check if the agent should update the service directory.

        :return: bool indicating the action
        """
        now = datetime.datetime.now()
        result = now - self.last_update_time > self.services_interval
        if result:
            self._last_update_time = now
        return result

    def is_time_to_search_services(self) -> bool:
        """
        Check if the agent should search the service directory.

        :return: bool indicating the action
        """
        now = datetime.datetime.now()
        result = now - self.last_search_time > self.services_interval
        if result:
            self._last_search_time = now
        return result

    def is_profitable_transaction(self, transaction: Transaction, dialogue: Dialogue) -> Tuple[bool, str]:
        """
        Check if a transaction is profitable.

        Is it a profitable transaction?
        - apply all the locks for role.
        - check if the transaction is consistent with the locks (enough money/holdings)
        - check that we gain score.

        :param transaction: the transaction
        :param dialogue: the dialogue

        :return: True if the transaction is good (as stated above), False otherwise.
        """
        state_after_locks = self.state_after_locks(dialogue.is_seller)

        if not state_after_locks.check_transaction_is_consistent(transaction, self.game_configuration.tx_fee):
            message = "[{}]: the proposed transaction is not consistent with the state after locks.".format(self.agent_name)
            return False, message
        proposal_delta_score = state_after_locks.get_score_diff_from_transaction(transaction, self.game_configuration.tx_fee)

        result = self.strategy.is_acceptable_proposal(proposal_delta_score)
        message = "[{}]: is good proposal for {}? {}: tx_id={}, delta_score={}, amount={}".format(self.agent_name, dialogue.role, result, transaction.transaction_id, proposal_delta_score, transaction.amount)
        return result, message

    def get_service_description(self, is_supply: bool) -> Description:
        """
        Get the description of the supplied goods (as a seller), or the demanded goods (as a buyer).

        :param is_supply: Boolean indicating whether it is supply or demand.

        :return: the description (to advertise on the Service Directory).
        """
        desc = get_goods_quantities_description(self.game_configuration.good_pbks,
                                                self.get_goods_quantities(is_supply),
                                                is_supply=is_supply)
        return desc

    def build_services_query(self, is_searching_for_sellers: bool) -> Optional[Query]:
        """
        Build a query to search for services.

        In particular, build the query to look for agents
            - which supply the agent's demanded goods (i.e. sellers), or
            - which demand the agent's supplied goods (i.e. buyers).

        :param is_searching_for_sellers: Boolean indicating whether the search is for sellers or buyers.

        :return: the Query, or None.
        """
        good_pbks = self.get_goods_pbks(is_supply=not is_searching_for_sellers)

        res = None if len(good_pbks) == 0 else build_query(good_pbks, is_searching_for_sellers)
        return res

    def build_services_dict(self, is_supply: bool) -> Optional[Dict[str, Sequence[str]]]:
        """
        Build a dictionary containing the services demanded/supplied.

        :param is_supply: Boolean indicating whether the services are demanded or supplied.

        :return: a Dict.
        """
        good_pbks = self.get_goods_pbks(is_supply=is_supply)

        res = None if len(good_pbks) == 0 else build_dict(good_pbks, is_supply)
        return res

    def is_matching(self, cfp_services: Dict[str, Union[bool, List[Any]]], goods_description: Description) -> bool:
        """
        Check for a match between the CFP services and the goods description.

        :param cfp_services: the services associated with the cfp.
        :param goods_description: a description of the goods.

        :return: Bool
        """
        services = cfp_services['services']
        services = cast(List[Any], services)
        if cfp_services['description'] is goods_description.data_model.name:
            # The call for proposal description and the goods model name cannot be the same for trading agent pairs.
            return False
        for good_pbk in goods_description.data_model.attributes_by_name.keys():
            if good_pbk not in services: continue
            return True
        return False

    def get_goods_pbks(self, is_supply: bool) -> Set[str]:
        """
        Wrap the function which determines supplied and demanded good public keys.

        :param is_supply: Boolean indicating whether it is referencing the supplied or demanded public keys.

        :return: a list of good public keys
        """
        state_after_locks = self.state_after_locks(is_seller=is_supply)
        good_pbks = self.strategy.supplied_good_pbks(self.game_configuration.good_pbks, state_after_locks.current_holdings) if is_supply else self.strategy.demanded_good_pbks(self.game_configuration.good_pbks, state_after_locks.current_holdings)
        return good_pbks

    def get_goods_quantities(self, is_supply: bool) -> List[int]:
        """
        Wrap the function which determines supplied and demanded good quantities.

        :param is_supply: Boolean indicating whether it is referencing the supplied or demanded quantities.

        :return: the vector of good quantities offered/requested.
        """
        state_after_locks = self.state_after_locks(is_seller=is_supply)
        quantities = self.strategy.supplied_good_quantities(state_after_locks.current_holdings) if is_supply else self.strategy.demanded_good_quantities(state_after_locks.current_holdings)
        return quantities

    def state_after_locks(self, is_seller: bool) -> AgentState:
        """
        Apply all the locks to the current state of the agent.

        This assumes, that all the locked transactions will be successful.

        :param is_seller: Boolean indicating the role of the agent.

        :return: the agent state with the locks applied to current state
        """
        assert self._agent_state is not None, "Agent state not assigned!"
        transactions = list(self.transaction_manager.locked_txs_as_seller.values()) if is_seller \
            else list(self.transaction_manager.locked_txs_as_buyer.values())
        state_after_locks = self._agent_state.apply(transactions, self.game_configuration.tx_fee)
        return state_after_locks

    def generate_proposal(self, cfp_services: Dict[str, Union[bool, List[Any]]], is_seller: bool) -> Optional[Description]:
        """
        Wrap the function which generates proposals from a seller or buyer.

        If there are locks as seller, it applies them.

        :param cfp_services: the query associated with the cfp.
        :param is_seller: Boolean indicating the role of the agent.

        :return: a list of descriptions
        """
        state_after_locks = self.state_after_locks(is_seller=is_seller)
        candidate_proposals = self.strategy.get_proposals(self.game_configuration.good_pbks, state_after_locks.current_holdings, state_after_locks.utility_params, self.game_configuration.tx_fee, is_seller, self._world_state)
        proposals = []
        for proposal in candidate_proposals:
            if not self.is_matching(cfp_services, proposal): continue
            if not proposal.values["price"] > 0: continue
            proposals.append(proposal)
        if not proposals:
            return None
        else:
            return random.choice(proposals)

    def stop(self):
        """Stop the services attached to the game instance."""
        self.stats_manager.stop()
