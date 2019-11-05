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

class Game(SharedClass):
    """A class to manage a TAC instance."""

    def __init__(self, agent_name: str, crypto: Crypto, mailbox: MailBox, monitor: Monitor, tac_parameters: TACParameters) -> None:
        """
        Instantiate a Game.

        :param agent_name: the name of the agent.
        :param crypto: the crypto module of the agent.
        :param mailbox: the mailbox.
        :param monitor: the monitor.
        :param tac_parameters: the tac parameters.
        :return: None
        """
        self.agent_name = agent_name
        self.crypto = crypto
        self.mailbox = mailbox
        self.tac_parameters = tac_parameters
        self.competition_start = None  # type: Optional[datetime.datetime]
        self._game_phase = GamePhase.PRE_GAME

        self.registered_agents = set()  # type: Set[str]
        self.agent_pbk_to_name = defaultdict()  # type: Dict[str, str]
        self.good_pbk_to_name = generate_good_pbk_to_name(self.tac_parameters.nb_goods)  # type: Dict[str, str]
        self._current_game = None  # type: Optional[Game]
        self.inactivity_timeout_timedelta = datetime.timedelta(seconds=tac_parameters.inactivity_timeout) \
            if tac_parameters.inactivity_timeout is not None else datetime.timedelta(seconds=15)

        self.game_data_per_participant = {}  # type: Dict[str, GameData]
        self.confirmed_transaction_per_participant = defaultdict(lambda: [])  # type: Dict[str, List[Transaction]]

        self.monitor = monitor
        self.monitor.start(None)
        self.monitor.update()

    def reset(self) -> None:
        """Reset the game."""
        self._current_game = None
        self.registered_agents = set()
        self.agent_pbk_to_name = defaultdict()
        self.good_pbk_to_name = defaultdict()

    @property
    def game_phase(self) -> GamePhase:
        """Get the game phase."""
        return self._game_phase

    @property
    def current_game(self) -> Game:
        """Get the game phase."""
        assert self._current_game is not None, "No current_game assigned!"
        return self._current_game

    @property
    def is_game_running(self) -> bool:
        """
        Check if an instance of a game is already set up.

        :return: Return True if there is a game running, False otherwise.
        """
        return self._current_game is not None

    def start_competition(self):
        """Create a game and send the game setting to every registered agent."""
        # assert that there is no competition running.
        assert not self.is_game_running
        self._current_game = self._create_game()

        try:
            self.monitor.set_gamestats(GameStats(self.current_game))
            self.monitor.update()
        except Exception as e:
            logger.exception(e)

        self._send_game_data_to_agents()

        self._game_phase = GamePhase.GAME
        # log messages
        logger.debug("[{}]: Started competition:\n{}".format(self.agent_name, self.current_game.get_holdings_summary()))
        logger.debug("[{}]: Computed equilibrium:\n{}".format(self.agent_name, self.current_game.get_equilibrium_summary()))

    def _create_game(self) -> Game:
        """
        Create a TAC game.

        :return: a Game instance.
        """
        nb_agents = len(self.registered_agents)

        game = Game.generate_game(self.tac_parameters.version_id,
                                  nb_agents,
                                  self.tac_parameters.nb_goods,
                                  self.tac_parameters.tx_fee,
                                  self.tac_parameters.money_endowment,
                                  self.tac_parameters.base_good_endowment,
                                  self.tac_parameters.lower_bound_factor,
                                  self.tac_parameters.upper_bound_factor,
                                  self.agent_pbk_to_name,
                                  self.good_pbk_to_name)

        return game

    def _send_game_data_to_agents(self) -> None:
        """
        Send the data of every agent about the game (e.g. endowments, preferences, scores).

        Assuming that the agent labels are public keys of the OEF Agents.

        :return: None.
        """
        for public_key in self.current_game.configuration.agent_pbks:
            agent_state = self.current_game.get_agent_state_from_agent_pbk(public_key)
            game_data_response = GameData(
                public_key,
                agent_state.balance,
                agent_state.current_holdings,
                agent_state.utility_params,
                self.current_game.configuration.nb_agents,
                self.current_game.configuration.nb_goods,
                self.current_game.configuration.tx_fee,
                self.current_game.configuration.agent_pbk_to_name,
                self.current_game.configuration.good_pbk_to_name,
                self.current_game.configuration.version_id
            )
            logger.debug("[{}]: sending GameData to '{}': {}"
                         .format(self.agent_name, public_key, str(game_data_response)))
            self.game_data_per_participant[public_key] = game_data_response

            msg = TACMessage(tac_type=TACMessage.Type.GAME_DATA,
                             money=agent_state.balance,
                             endowment=agent_state.current_holdings,
                             utility_params=agent_state.utility_params,
                             nb_agents=self.current_game.configuration.nb_agents,
                             nb_goods=self.current_game.configuration.nb_goods,
                             tx_fee=self.current_game.configuration.tx_fee,
                             agent_pbk_to_name=self.current_game.configuration.agent_pbk_to_name,
                             good_pbk_to_name=self.current_game.configuration.good_pbk_to_name,
                             version_id=self.current_game.configuration.version_id
                             )
            tac_bytes = TACSerializer().encode(msg)
            self.mailbox.outbox.put_message(to=public_key, sender=self.crypto.public_key, protocol_id=TACMessage.protocol_id, message=tac_bytes)

    def notify_competition_cancelled(self):
        """Notify agents that the TAC is cancelled."""
        logger.debug("[{}]: Notifying agents that TAC is cancelled.".format(self.agent_name))
        for agent_pbk in self.registered_agents:
            tac_msg = TACMessage(tac_type=TACMessage.Type.CANCELLED)
            tac_bytes = TACSerializer().encode(tac_msg)
            self.mailbox.outbox.put_message(to=agent_pbk, sender=self.crypto.public_key, protocol_id=TACMessage.protocol_id, message=tac_bytes)
        # wait some time to make sure the connection delivers the messages
        time.sleep(2.0)
        self._game_phase = GamePhase.POST_GAME

    def simulation_dump(self) -> None:
        """
        Dump the details of the simulation.

        :return: None.
        """
        version_dir = self.tac_parameters.data_output_dir + "/" + self.tac_parameters.version_id

        if not self.is_game_running:
            logger.warning("[{}]: Game not present. Using empty dictionary.".format(self.agent_name))
            game_dict = {}  # type: Dict[str, Any]
        else:
            game_dict = self.current_game.to_dict()

        os.makedirs(version_dir, exist_ok=True)
        with open(os.path.join(version_dir, "game.json"), "w") as f:
            json.dump(game_dict, f)

    """
    Class representing a game instance of TAC.

    >>> version_id = '1'
    >>> nb_agents = 3
    >>> nb_goods = 3
    >>> tx_fee = 1.0
    >>> agent_pbk_to_name = {'tac_agent_0_pbk': 'tac_agent_0', 'tac_agent_1_pbk': 'tac_agent_1', 'tac_agent_2_pbk': 'tac_agent_2'}
    >>> good_pbk_to_name = {'tac_good_0': 'Good 0', 'tac_good_1': 'Good 1', 'tac_good_2': 'Good 2'}
    >>> money_amounts = [20, 20, 20]
    >>> endowments = [
    ... [1, 1, 1],
    ... [2, 1, 1],
    ... [1, 1, 2]]
    >>> utility_params = [
    ... [20.0, 40.0, 40.0],
    ... [10.0, 50.0, 40.0],
    ... [40.0, 30.0, 30.0]]
    >>> eq_prices = [1.0, 2.0, 2.0]
    >>> eq_good_holdings = [
    ... [1.0, 1.0, 1.0],
    ... [2.0, 1.0, 1.0],
    ... [1.0, 1.0, 2.0]]
    >>> eq_money_holdings = [20.0, 20.0, 20.0]
    >>> game_configuration = GameConfiguration(
    ...     version_id,
    ...     nb_agents,
    ...     nb_goods,
    ...     tx_fee,
    ...     agent_pbk_to_name,
    ...     good_pbk_to_name
    ... )
    >>> game_initialization = GameInitialization(
    ...     money_amounts,
    ...     endowments,
    ...     utility_params,
    ...     eq_prices,
    ...     eq_good_holdings,
    ...     eq_money_holdings
    ... )
    >>> game = Game(game_configuration, game_initialization)

    Get the scores:
    >>> game.get_scores()
    {'tac_agent_0_pbk': 89.31471805599453, 'tac_agent_1_pbk': 93.36936913707618, 'tac_agent_2_pbk': 101.47867129923947}
    """

    def __init__(self, configuration: GameConfiguration, initialization: GameInitialization):
        """
        Initialize a game.

        :param configuration: the game configuration.
        :param initialization: the game initialization.
        """
        self._configuration = configuration  # type GameConfiguration
        self._initialization = initialization  # type: GameInitialization
        self.transactions = []  # type: List[Transaction]

        self._initial_agent_states = dict(
            (agent_pbk,
                AgentState(
                    initialization.initial_money_amounts[i],
                    initialization.endowments[i],
                    initialization.utility_params[i]
                ))
            for agent_pbk, i in zip(configuration.agent_pbks, range(configuration.nb_agents)))  # type: Dict[str, AgentState]

        self.agent_states = dict(
            (agent_pbk,
                AgentState(
                    initialization.initial_money_amounts[i],
                    initialization.endowments[i],
                    initialization.utility_params[i]
                ))
            for agent_pbk, i in zip(configuration.agent_pbks, range(configuration.nb_agents)))  # type: Dict[str, AgentState]

        self.good_states = dict(
            (good_pbk,
                GoodState(
                    DEFAULT_PRICE
                ))
            for good_pbk in configuration.good_pbks)  # type: Dict[str, GoodState]

    @property
    def initialization(self) -> GameInitialization:
        """Get game initialization."""
        return self._initialization

    @property
    def configuration(self) -> GameConfiguration:
        """Get game configuration."""
        return self._configuration

    @property
    def initial_agent_states(self) -> Dict[str, 'AgentState']:
        """Get initial state of each agent."""
        return self._initial_agent_states

    @staticmethod
    def generate_game(version_id: str,
                      nb_agents: int,
                      nb_goods: int,
                      tx_fee: float,
                      money_endowment: int,
                      base_good_endowment: int,
                      lower_bound_factor: int,
                      upper_bound_factor: int,
                      agent_pbk_to_name: Dict[str, str],
                      good_pbk_to_name: Dict[str, str]) -> 'Game':
        """
        Generate a game, the endowments and the utilites.

        :param version_id: the version of the game.
        :param nb_agents: the number of agents.
        :param nb_goods: the number of goods.
        :param tx_fee: the fee to pay per transaction.
        :param money_endowment: the initial amount of money for every agent.
        :param base_good_endowment: the base amount of instances per good.
        :param lower_bound_factor: the lower bound of a uniform distribution.
        :param upper_bound_factor: the upper bound of a uniform distribution
        :param agent_pbk_to_name: the mapping of the public keys for the agents to their names.
        :param good_pbk_to_name: the mapping of the public keys for the goods to their names.
        :return: a game.
        """
        game_configuration = GameConfiguration(version_id, nb_agents, nb_goods, tx_fee, agent_pbk_to_name, good_pbk_to_name)

        scaling_factor = determine_scaling_factor(money_endowment)
        money_endowments = generate_money_endowments(nb_agents, money_endowment)
        good_endowments = generate_good_endowments(nb_goods, nb_agents, base_good_endowment, lower_bound_factor, upper_bound_factor)
        utility_params = generate_utility_params(nb_agents, nb_goods, scaling_factor)
        eq_prices, eq_good_holdings, eq_money_holdings = generate_equilibrium_prices_and_holdings(good_endowments, utility_params, money_endowment, scaling_factor)
        game_initialization = GameInitialization(money_endowments, good_endowments, utility_params, eq_prices, eq_good_holdings, eq_money_holdings)

        return Game(game_configuration, game_initialization)

    def get_initial_scores(self) -> List[float]:
        """Get the initial scores for every agent."""
        return [agent_state.get_score() for agent_state in self.initial_agent_states.values()]

    def get_scores(self) -> Dict[str, float]:
        """Get the current scores for every agent."""
        return {agent_pbk: agent_state.get_score() for agent_pbk, agent_state in self.agent_states.items()}

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

        >>> version_id = '1'
        >>> nb_agents = 3
        >>> nb_goods = 3
        >>> tx_fee = 1.0
        >>> agent_pbk_to_name = {'tac_agent_0_pbk': 'tac_agent_0', 'tac_agent_1_pbk': 'tac_agent_1', 'tac_agent_2_pbk': 'tac_agent_2'}
        >>> good_pbk_to_name = {'tac_good_0': 'Good 0', 'tac_good_1': 'Good 1', 'tac_good_2': 'Good 2'}
        >>> money_amounts = [20, 20, 20]
        >>> endowments = [
        ... [1, 1, 1],
        ... [2, 1, 1],
        ... [1, 1, 2]]
        >>> utility_params = [
        ... [20.0, 40.0, 40.0],
        ... [10.0, 50.0, 40.0],
        ... [40.0, 30.0, 30.0]]
        >>> eq_prices = [1.0, 2.0, 2.0]
        >>> eq_good_holdings = [
        ... [1.0, 1.0, 1.0],
        ... [2.0, 1.0, 1.0],
        ... [1.0, 1.0, 2.0]]
        >>> eq_money_holdings = [20.0, 20.0, 20.0]
        >>> game_configuration = GameConfiguration(
        ...     version_id,
        ...     nb_agents,
        ...     nb_goods,
        ...     tx_fee,
        ...     agent_pbk_to_name,
        ...     good_pbk_to_name,
        ... )
        >>> game_initialization = GameInitialization(
        ...     money_amounts,
        ...     endowments,
        ...     utility_params,
        ...     eq_prices,
        ...     eq_good_holdings,
        ...     eq_money_holdings
        ... )
        >>> game = Game(game_configuration, game_initialization)
        >>> agent_state_0 = game.agent_states['tac_agent_0_pbk'] # agent state of tac_agent_0
        >>> agent_state_1 = game.agent_states['tac_agent_1_pbk'] # agent state of tac_agent_1
        >>> agent_state_2 = game.agent_states['tac_agent_2_pbk'] # agent state of tac_agent_2
        >>> agent_state_0.balance, agent_state_0.current_holdings
        (20, [1, 1, 1])
        >>> agent_state_1.balance, agent_state_1.current_holdings
        (20, [2, 1, 1])
        >>> agent_state_2.balance, agent_state_2.current_holdings
        (20, [1, 1, 2])
        >>> tx = Transaction('some_tx_id', True, 'tac_agent_1_pbk', 15, {'tac_good_0': 1, 'tac_good_1': 0, 'tac_good_2': 0}, 'tac_agent_0_pbk')
        >>> game.settle_transaction(tx)
        >>> agent_state_0.balance, agent_state_0.current_holdings
        (4.5, [2, 1, 1])
        >>> agent_state_1.balance, agent_state_1.current_holdings
        (34.5, [1, 1, 1])

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

    def get_holdings_matrix(self) -> List[Endowment]:
        """
        Get the holdings matrix of shape (nb_agents, nb_goods).

        :return: the holdings matrix.
        """
        result = list(map(lambda state: state.current_holdings, self.agent_states.values()))
        return result

    def get_balances(self) -> Dict[str, float]:
        """Get the current balances."""
        result = {agent_pbk: agent_state.balance for agent_pbk, agent_state in self.agent_states.items()}
        return result

    def get_prices(self) -> List[float]:
        """Get the current prices."""
        result = list(map(lambda state: state.price, self.good_states.values()))
        return result

    def get_holdings_summary(self) -> str:
        """
        Get holdings summary.

        >>> version_id = '1'
        >>> nb_agents = 3
        >>> nb_goods = 3
        >>> tx_fee = 1.0
        >>> agent_pbk_to_name = {'tac_agent_0_pbk': 'tac_agent_0', 'tac_agent_1_pbk': 'tac_agent_1', 'tac_agent_2_pbk': 'tac_agent_2'}
        >>> good_pbk_to_name = {'tac_good_0': 'Good 0', 'tac_good_1': 'Good 1', 'tac_good_2': 'Good 2'}
        >>> money_amounts = [20, 20, 20]
        >>> endowments = [
        ... [1, 1, 1],
        ... [2, 1, 1],
        ... [1, 1, 2]]
        >>> utility_params = [
        ... [20.0, 40.0, 40.0],
        ... [10.0, 50.0, 40.0],
        ... [40.0, 30.0, 30.0]]
        >>> eq_prices = [1.0, 2.0, 2.0]
        >>> eq_good_holdings = [
        ... [1.0, 1.0, 1.0],
        ... [2.0, 1.0, 1.0],
        ... [1.0, 1.0, 2.0]]
        >>> eq_money_holdings = [20.0, 20.0, 20.0]
        >>> game_configuration = GameConfiguration(
        ...     version_id,
        ...     nb_agents,
        ...     nb_goods,
        ...     tx_fee,
        ...     agent_pbk_to_name,
        ...     good_pbk_to_name
        ... )
        >>> game_initialization = GameInitialization(
        ...     money_amounts,
        ...     endowments,
        ...     utility_params,
        ...     eq_prices,
        ...     eq_good_holdings,
        ...     eq_money_holdings
        ... )
        >>> game = Game(game_configuration, game_initialization)
        >>> print(game.get_holdings_summary(), end="")
        tac_agent_0 [1, 1, 1]
        tac_agent_1 [2, 1, 1]
        tac_agent_2 [1, 1, 2]

        :return: a string representing the holdings for every agent.
        """
        result = ""
        for agent_pbk, agent_state in self.agent_states.items():
            result = result + self.configuration.agent_pbk_to_name[agent_pbk] + " " + str(agent_state._current_holdings) + "\n"
        return result

    def get_equilibrium_summary(self) -> str:
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

    def to_dict(self) -> Dict[str, Any]:
        """Get a dictionary from the object."""
        return {
            "configuration": self.configuration.to_dict(),
            "initialization": self.initialization.to_dict(),
            "transactions": [t.to_dict() for t in self.transactions]
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'Game':
        """Get class instance from dictionary."""
        configuration = GameConfiguration.from_dict(d["configuration"])
        initialization = GameInitialization.from_dict(d["initialization"])

        game = Game(configuration, initialization)
        for tx_dict in d["transactions"]:
            tx = Transaction.from_dict(tx_dict)
            game.settle_transaction(tx)

        return game

    def __eq__(self, other):
        """Compare equality of two instances from class."""
        return isinstance(other, Game) and \
            self.configuration == other.configuration and \
            self.transactions == other.transactions

class GameHandler:
    """A class to manage a TAC instance."""

    def __init__(self, agent_name: str, crypto: Crypto, mailbox: MailBox, monitor: Monitor, tac_parameters: TACParameters) -> None:
        """
        Instantiate a GameHandler.

        :param agent_name: the name of the agent.
        :param crypto: the crypto module of the agent.
        :param mailbox: the mailbox.
        :param monitor: the monitor.
        :param tac_parameters: the tac parameters.
        :return: None
        """
        self.agent_name = agent_name
        self.crypto = crypto
        self.mailbox = mailbox
        self.tac_parameters = tac_parameters
        self.competition_start = None  # type: Optional[datetime.datetime]
        self._game_phase = GamePhase.PRE_GAME

        self.registered_agents = set()  # type: Set[str]
        self.agent_pbk_to_name = defaultdict()  # type: Dict[str, str]
        self.good_pbk_to_name = generate_good_pbk_to_name(self.tac_parameters.nb_goods)  # type: Dict[str, str]
        self._current_game = None  # type: Optional[Game]
        self.inactivity_timeout_timedelta = datetime.timedelta(seconds=tac_parameters.inactivity_timeout) \
            if tac_parameters.inactivity_timeout is not None else datetime.timedelta(seconds=15)

        self.game_data_per_participant = {}  # type: Dict[str, GameData]
        self.confirmed_transaction_per_participant = defaultdict(lambda: [])  # type: Dict[str, List[Transaction]]

        self.monitor = monitor
        self.monitor.start(None)
        self.monitor.update()

    def reset(self) -> None:
        """Reset the game."""
        self._current_game = None
        self.registered_agents = set()
        self.agent_pbk_to_name = defaultdict()
        self.good_pbk_to_name = defaultdict()

    @property
    def game_phase(self) -> GamePhase:
        """Get the game phase."""
        return self._game_phase

    @property
    def current_game(self) -> Game:
        """Get the game phase."""
        assert self._current_game is not None, "No current_game assigned!"
        return self._current_game

    @property
    def is_game_running(self) -> bool:
        """
        Check if an instance of a game is already set up.

        :return: Return True if there is a game running, False otherwise.
        """
        return self._current_game is not None

    def start_competition(self):
        """Create a game and send the game setting to every registered agent."""
        # assert that there is no competition running.
        assert not self.is_game_running
        self._current_game = self._create_game()

        try:
            self.monitor.set_gamestats(GameStats(self.current_game))
            self.monitor.update()
        except Exception as e:
            logger.exception(e)

        self._send_game_data_to_agents()

        self._game_phase = GamePhase.GAME
        # log messages
        logger.debug("[{}]: Started competition:\n{}".format(self.agent_name, self.current_game.get_holdings_summary()))
        logger.debug("[{}]: Computed equilibrium:\n{}".format(self.agent_name, self.current_game.get_equilibrium_summary()))

    def _create_game(self) -> Game:
        """
        Create a TAC game.

        :return: a Game instance.
        """
        nb_agents = len(self.registered_agents)

        game = Game.generate_game(self.tac_parameters.version_id,
                                  nb_agents,
                                  self.tac_parameters.nb_goods,
                                  self.tac_parameters.tx_fee,
                                  self.tac_parameters.money_endowment,
                                  self.tac_parameters.base_good_endowment,
                                  self.tac_parameters.lower_bound_factor,
                                  self.tac_parameters.upper_bound_factor,
                                  self.agent_pbk_to_name,
                                  self.good_pbk_to_name)

        return game

    def _send_game_data_to_agents(self) -> None:
        """
        Send the data of every agent about the game (e.g. endowments, preferences, scores).

        Assuming that the agent labels are public keys of the OEF Agents.

        :return: None.
        """
        for public_key in self.current_game.configuration.agent_pbks:
            agent_state = self.current_game.get_agent_state_from_agent_pbk(public_key)
            game_data_response = GameData(
                public_key,
                agent_state.balance,
                agent_state.current_holdings,
                agent_state.utility_params,
                self.current_game.configuration.nb_agents,
                self.current_game.configuration.nb_goods,
                self.current_game.configuration.tx_fee,
                self.current_game.configuration.agent_pbk_to_name,
                self.current_game.configuration.good_pbk_to_name,
                self.current_game.configuration.version_id
            )
            logger.debug("[{}]: sending GameData to '{}': {}"
                         .format(self.agent_name, public_key, str(game_data_response)))
            self.game_data_per_participant[public_key] = game_data_response

            msg = TACMessage(tac_type=TACMessage.Type.GAME_DATA,
                             money=agent_state.balance,
                             endowment=agent_state.current_holdings,
                             utility_params=agent_state.utility_params,
                             nb_agents=self.current_game.configuration.nb_agents,
                             nb_goods=self.current_game.configuration.nb_goods,
                             tx_fee=self.current_game.configuration.tx_fee,
                             agent_pbk_to_name=self.current_game.configuration.agent_pbk_to_name,
                             good_pbk_to_name=self.current_game.configuration.good_pbk_to_name,
                             version_id=self.current_game.configuration.version_id
                             )
            tac_bytes = TACSerializer().encode(msg)
            self.mailbox.outbox.put_message(to=public_key, sender=self.crypto.public_key, protocol_id=TACMessage.protocol_id, message=tac_bytes)

    def notify_competition_cancelled(self):
        """Notify agents that the TAC is cancelled."""
        logger.debug("[{}]: Notifying agents that TAC is cancelled.".format(self.agent_name))
        for agent_pbk in self.registered_agents:
            tac_msg = TACMessage(tac_type=TACMessage.Type.CANCELLED)
            tac_bytes = TACSerializer().encode(tac_msg)
            self.mailbox.outbox.put_message(to=agent_pbk, sender=self.crypto.public_key, protocol_id=TACMessage.protocol_id, message=tac_bytes)
        # wait some time to make sure the connection delivers the messages
        time.sleep(2.0)
        self._game_phase = GamePhase.POST_GAME

    def simulation_dump(self) -> None:
        """
        Dump the details of the simulation.

        :return: None.
        """
        version_dir = self.tac_parameters.data_output_dir + "/" + self.tac_parameters.version_id

        if not self.is_game_running:
            logger.warning("[{}]: Game not present. Using empty dictionary.".format(self.agent_name))
            game_dict = {}  # type: Dict[str, Any]
        else:
            game_dict = self.current_game.to_dict()

        os.makedirs(version_dir, exist_ok=True)
        with open(os.path.join(version_dir, "game.json"), "w") as f:
            json.dump(game_dict, f)