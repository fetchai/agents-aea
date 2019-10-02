
      self._world_state = None  # type: Optional[WorldState]

get_own_service_description(is_supply=dialogue.is_seller)
generate_proposal(cfp_services, dialogue.is_seller)
    @property
    def world_state(self) -> WorldState:
        """Get the world state."""
        assert self._world_state is not None, "World state not assigned!"
        return self._world_state

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