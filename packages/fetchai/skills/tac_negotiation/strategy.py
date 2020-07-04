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

"""This module contains the abstract class defining an agent's strategy for the TAC."""

import copy
import random
from enum import Enum
from typing import Dict, Optional, cast

from aea.helpers.search.models import Description, Query
from aea.protocols.signing.message import SigningMessage
from aea.skills.base import Model

from packages.fetchai.skills.tac_negotiation.dialogues import Dialogue
from packages.fetchai.skills.tac_negotiation.helpers import (
    build_goods_description,
    build_goods_query,
)
from packages.fetchai.skills.tac_negotiation.transactions import Transactions


ROUNDING_ADJUSTMENT = 1


class Strategy(Model):
    """This class defines an abstract strategy for the agent."""

    class RegisterAs(Enum):
        """This class defines the service registration options."""

        SELLER = "seller"
        BUYER = "buyer"
        BOTH = "both"

    class SearchFor(Enum):
        """This class defines the service search options."""

        SELLERS = "sellers"
        BUYERS = "buyers"
        BOTH = "both"

    def __init__(self, **kwargs) -> None:
        """
        Initialize the strategy of the agent.

        :param register_as: determines whether the agent registers as seller, buyer or both
        :param search_for: determines whether the agent searches for sellers, buyers or both

        :return: None
        """
        self._register_as = Strategy.RegisterAs(kwargs.pop("register_as", "both"))
        self._search_for = Strategy.SearchFor(kwargs.pop("search_for", "both"))
        self._is_contract_tx = kwargs.pop("is_contract_tx", False)
        self._ledger_id = kwargs.pop("ledger_id", "ethereum")
        super().__init__(**kwargs)

    @property
    def is_registering_as_seller(self) -> bool:
        """Check if the agent registers as a seller on the OEF service directory."""
        return (
            self._register_as == Strategy.RegisterAs.SELLER
            or self._register_as == Strategy.RegisterAs.BUYER
        )

    @property
    def is_searching_for_sellers(self) -> bool:
        """Check if the agent searches for sellers on the OEF service directory."""
        return (
            self._search_for == Strategy.SearchFor.SELLERS
            or self._search_for == Strategy.SearchFor.BOTH
        )

    @property
    def is_registering_as_buyer(self) -> bool:
        """Check if the agent registers as a buyer on the OEF service directory."""
        return (
            self._register_as == Strategy.RegisterAs.BUYER
            or self._register_as == Strategy.RegisterAs.BOTH
        )

    @property
    def is_searching_for_buyers(self) -> bool:
        """Check if the agent searches for buyers on the OEF service directory."""
        return (
            self._search_for == Strategy.SearchFor.BUYERS
            or self._search_for == Strategy.SearchFor.BOTH
        )

    @property
    def is_contract_tx(self) -> bool:
        """Check if tx are made against the ERC1155 or not."""
        return self._is_contract_tx

    @property
    def ledger_id(self) -> str:
        """Get the ledger id."""
        return self._ledger_id

    def get_own_service_description(
        self, is_supply: bool, is_search_description: bool
    ) -> Description:
        """
        Get the description of the supplied goods (as a seller), or the demanded goods (as a buyer).

        :param is_supply: Boolean indicating whether it is supply or demand.
        :param is_search_description: whether or not the description is for search.

        :return: the description (to advertise on the Service Directory).
        """
        transactions = cast(Transactions, self.context.transactions)
        ownership_state_after_locks = transactions.ownership_state_after_locks(
            is_seller=is_supply
        )
        good_id_to_quantities = (
            self._supplied_goods(ownership_state_after_locks.quantities_by_good_id)
            if is_supply
            else self._demanded_goods(ownership_state_after_locks.quantities_by_good_id)
        )
        currency_id = list(ownership_state_after_locks.amount_by_currency_id.keys())[0]
        desc = build_goods_description(
            good_id_to_quantities=good_id_to_quantities,
            currency_id=currency_id,
            is_supply=is_supply,
            is_search_description=is_search_description,
        )
        return desc

    @staticmethod
    def _supplied_goods(good_holdings: Dict[str, int]) -> Dict[str, int]:
        """
        Generate a dictionary of quantities which are supplied.

        :param good_holdings: a dictionary of current good holdings
        :return: a dictionary of quantities supplied
        """
        supply = {}  # type: Dict[str, int]
        for good_id, quantity in good_holdings.items():
            supply[good_id] = quantity - 1 if quantity > 1 else 0
        return supply

    @staticmethod
    def _demanded_goods(good_holdings: Dict[str, int]) -> Dict[str, int]:
        """
        Generate a dictionary of quantities which are demanded.

        :param good_holdings: a dictionary of current good holdings
        :return: a dictionary of quantities supplied
        """
        demand = {}  # type: Dict[str, int]
        for good_id in good_holdings.keys():
            demand[good_id] = 1
        return demand

    def get_own_services_query(
        self, is_searching_for_sellers: bool, is_search_query: bool
    ) -> Query:
        """
        Build a query.

        In particular, build the query to look for agents
            - which supply the agent's demanded goods (i.e. sellers), or
            - which demand the agent's supplied goods (i.e. buyers).

        :param is_searching_for_sellers: Boolean indicating whether the search is for sellers or buyers.
        :param is_search_query: whether or not the query is used for search on OEF

        :return: the Query, or None.
        """
        transactions = cast(Transactions, self.context.transactions)
        ownership_state_after_locks = transactions.ownership_state_after_locks(
            is_seller=not is_searching_for_sellers
        )
        good_id_to_quantities = (
            self._demanded_goods(ownership_state_after_locks.quantities_by_good_id)
            if is_searching_for_sellers
            else self._supplied_goods(ownership_state_after_locks.quantities_by_good_id)
        )
        currency_id = list(ownership_state_after_locks.amount_by_currency_id.keys())[0]
        query = build_goods_query(
            good_ids=list(good_id_to_quantities.keys()),
            currency_id=currency_id,
            is_searching_for_sellers=is_searching_for_sellers,
            is_search_query=is_search_query,
        )
        return query

    def _get_proposal_for_query(
        self, query: Query, is_seller: bool
    ) -> Optional[Description]:
        """
        Generate proposal (in the form of a description) which matches the query.

        :param query: the query for which to build the proposal
        :is_seller: whether the agent making the proposal is a seller or not

        :return: a description
        """
        candidate_proposals = self._generate_candidate_proposals(is_seller)
        proposals = []
        for proposal in candidate_proposals:
            if not query.check(proposal):
                continue
            proposals.append(proposal)
        if not proposals:
            return None
        else:
            return random.choice(proposals)  # nosec

    def get_proposal_for_query(
        self, query: Query, role: Dialogue.Role
    ) -> Optional[Description]:
        """
        Generate proposal (in the form of a description) which matches the query.

        :param query: the query for which to build the proposal
        :param role: the role of the agent making the proposal (seller or buyer)

        :return: a description
        """
        is_seller = role == Dialogue.Role.SELLER

        own_service_description = self.get_own_service_description(
            is_supply=is_seller, is_search_description=False
        )
        if not query.check(own_service_description):
            self.context.logger.debug(
                "[{}]: Current holdings do not satisfy CFP query.".format(
                    self.context.agent_name
                )
            )
            return None
        else:
            proposal_description = self._get_proposal_for_query(
                query, is_seller=is_seller
            )
            if proposal_description is None:
                self.context.logger.debug(
                    "[{}]: Current strategy does not generate proposal that satisfies CFP query.".format(
                        self.context.agent_name
                    )
                )
            return proposal_description

    def _generate_candidate_proposals(self, is_seller: bool):
        """
        Generate proposals from the agent in the role of seller/buyer.

        :param is_seller: the bool indicating whether the agent is a seller.

        :return: a list of proposals in Description form
        """
        transactions = cast(Transactions, self.context.transactions)
        ownership_state_after_locks = transactions.ownership_state_after_locks(
            is_seller=is_seller
        )
        good_id_to_quantities = (
            self._supplied_goods(ownership_state_after_locks.quantities_by_good_id)
            if is_seller
            else self._demanded_goods(ownership_state_after_locks.quantities_by_good_id)
        )
        nil_proposal_dict = {
            good_id: 0 for good_id in good_id_to_quantities.keys()
        }  # type: Dict[str, int]
        proposals = []
        seller_tx_fee = (
            self.context.decision_maker_handler_context.preferences.seller_transaction_fee
        )
        buyer_tx_fee = (
            self.context.decision_maker_handler_context.preferences.buyer_transaction_fee
        )
        currency_id = list(
            self.context.decision_maker_handler_context.ownership_state.amount_by_currency_id.keys()
        )[0]
        for good_id, quantity in good_id_to_quantities.items():
            if is_seller and quantity == 0:
                continue
            proposal_dict = copy.copy(nil_proposal_dict)
            proposal_dict[good_id] = 1
            proposal = build_goods_description(
                good_id_to_quantities=proposal_dict,
                currency_id=currency_id,
                is_supply=is_seller,
                is_search_description=False,
            )
            if is_seller:
                delta_quantities_by_good_id = {
                    good_id: quantity * -1
                    for good_id, quantity in proposal_dict.items()
                }  # type: Dict[str, int]
            else:
                delta_quantities_by_good_id = proposal_dict
            marginal_utility_from_delta_good_holdings = self.context.decision_maker_handler_context.preferences.marginal_utility(
                ownership_state=ownership_state_after_locks,
                delta_quantities_by_good_id=delta_quantities_by_good_id,
            )
            switch = -1 if is_seller else 1
            breakeven_price_rounded = (
                round(marginal_utility_from_delta_good_holdings) * switch
            )
            if is_seller:
                proposal.values["price"] = (
                    breakeven_price_rounded + seller_tx_fee + ROUNDING_ADJUSTMENT
                )
            else:
                proposal.values["price"] = (
                    breakeven_price_rounded - buyer_tx_fee - ROUNDING_ADJUSTMENT
                )
            proposal.values["seller_tx_fee"] = seller_tx_fee
            proposal.values["buyer_tx_fee"] = buyer_tx_fee
            if not proposal.values["price"] > 0:
                continue
            tx_nonce = transactions.get_next_tx_nonce()
            proposal.values["tx_nonce"] = tx_nonce
            proposals.append(proposal)
        return proposals

    def is_profitable_transaction(
        self, transaction_msg: SigningMessage, role: Dialogue.Role
    ) -> bool:
        """
        Check if a transaction is profitable.

        Is it a profitable transaction?
        - apply all the locks for role.
        - check if the transaction is consistent with the locks (enough money/holdings)
        - check that we gain score.

        :param transaction_msg: the transaction_msg
        :param role: the role of the agent (seller or buyer)

        :return: True if the transaction is good (as stated above), False otherwise.
        """
        is_seller = role == Dialogue.Role.SELLER

        transactions = cast(Transactions, self.context.transactions)
        ownership_state_after_locks = transactions.ownership_state_after_locks(
            is_seller
        )
        if not ownership_state_after_locks.is_affordable_transaction(
            transaction_msg.terms
        ):
            return False
        proposal_delta_score = self.context.decision_maker_handler_context.preferences.utility_diff_from_transaction(
            ownership_state_after_locks, transaction_msg
        )
        if proposal_delta_score >= 0:
            return True
        else:
            return False
