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
"""This module contains the tests of the strategy class of the tac negotiation skill."""

import re
from pathlib import Path
from unittest.mock import patch

import pytest

from aea.decision_maker.gop import GoalPursuitReadiness, OwnershipState, Preferences
from aea.exceptions import AEAEnforceError
from aea.helpers.search.models import (
    Attribute,
    Constraint,
    ConstraintType,
    DataModel,
    Description,
    Location,
    Query,
)
from aea.helpers.transaction.base import Terms
from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.skills.tac_negotiation.dialogues import FipaDialogue
from packages.fetchai.skills.tac_negotiation.helpers import (
    build_goods_description,
    build_goods_query,
)
from packages.fetchai.skills.tac_negotiation.strategy import (
    AGENT_LOCATION_MODEL,
    AGENT_PERSONALITY_MODEL,
    AGENT_REMOVE_SERVICE_MODEL,
    AGENT_SET_SERVICE_MODEL,
    CONTRACT_ID,
    Strategy,
)

from tests.conftest import ROOT_DIR


class TestStrategy(BaseSkillTestCase):
    """Test Strategy of tac negotiation."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "tac_negotiation")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        tac_dm_context_kwargs = {
            "goal_pursuit_readiness": GoalPursuitReadiness(),
            "ownership_state": OwnershipState(),
            "preferences": Preferences(),
        }
        super().setup(dm_context_kwargs=tac_dm_context_kwargs)
        cls.register_as = "both"
        cls.search_for = "both"
        cls.is_contract_tx = False
        cls.ledger_id = "some_ledger_id"
        cls.location = {"longitude": 0.1270, "latitude": 51.5194}
        cls.search_radius = 5.0
        cls.service_key = "tac_service"

        cls.strategy = Strategy(
            register_as=cls.register_as,
            search_for=cls.search_for,
            is_contract_tx=cls.is_contract_tx,
            ledger_id=cls.ledger_id,
            location=cls.location,
            service_key=cls.service_key,
            search_radius=cls.search_radius,
            name="strategy",
            skill_context=cls._skill.skill_context,
        )

        cls.nonce = "125"
        cls.sender = "some_sender_address"
        cls.counterparty = "some_counterparty_address"
        cls.signature = "some_signature"
        cls.sender_pk = "some_sender_public_key"
        cls.counterparty_pk = "some_counterparty_public_key"

        cls.mocked_currency_id = "12"
        cls.mocked_currency_amount = 2000000
        cls.mocked_amount_by_currency_id = {
            cls.mocked_currency_id: cls.mocked_currency_amount
        }
        cls.mocked_good_ids = ["13", "14", "15", "16", "17", "18", "19", "20", "21"]
        cls.mocked_good_quantities = [5, 7, 4, 3, 5, 4, 3, 5, 6]
        cls.mocked_quantities_by_good_id = dict(
            zip(cls.mocked_good_ids, cls.mocked_good_quantities)
        )
        cls.mocked_ownership_state = (
            cls._skill.skill_context.decision_maker_handler_context.ownership_state
        )
        cls.mocked_ownership_state.set(
            cls.mocked_amount_by_currency_id, cls.mocked_quantities_by_good_id
        )

        cls.exchange_params_by_currency_id = {cls.mocked_currency_id: 1.0}
        cls.utility_params_by_good_id = {
            "13": 48300.0,
            "14": 43700.0,
            "15": 163200.0,
            "16": 59800.0,
            "17": 114900.0,
            "18": 128700.00000000001,
            "19": 126400.00000000001,
            "20": 211500.0,
            "21": 103500.0,
        }
        cls.mocked_preferences = (
            cls._skill.skill_context.decision_maker_handler_context.preferences
        )
        cls.mocked_preferences.set(
            exchange_params_by_currency_id=cls.exchange_params_by_currency_id,
            utility_params_by_good_id=cls.utility_params_by_good_id,
        )

    def test_properties(self):
        """Test the properties of Strategy class."""
        assert self.strategy.registering_as == "buyer and seller"

        assert self.strategy.searching_for == "buyer and seller"

        assert self.strategy.searching_for_types == [
            (True, "sellers"),
            (False, "buyers"),
        ]

        assert self.strategy.is_contract_tx == self.is_contract_tx

        assert self.strategy.ledger_id == self.ledger_id

        assert self.strategy.contract_id == str(CONTRACT_ID)

        with pytest.raises(AEAEnforceError, match="ERC1155Contract address not set!"):
            assert self.strategy.contract_address
        self.skill.skill_context._agent_context._shared_state = {
            "erc1155_contract_address": "some_address"
        }
        assert self.strategy.contract_address == "some_address"

    def test_get_location_description(self):
        """Test the get_location_description method of the Strategy class."""
        description = self.strategy.get_location_description()

        assert type(description) == Description
        assert description.data_model is AGENT_LOCATION_MODEL
        assert description.values.get("location", "") == Location(
            latitude=self.location["latitude"], longitude=self.location["longitude"]
        )

    def test_get_register_service_description(self):
        """Test the get_register_service_description method of the GenericStrategy class."""
        # setup
        self.strategy.tac_version_id = "some_tac_id"

        # operation
        description = self.strategy.get_register_service_description()

        # after
        assert type(description) == Description
        assert description.data_model is AGENT_SET_SERVICE_MODEL
        assert (
            description.values.get("key", "")
            == f"{self.service_key}_{self.strategy.tac_version_id}"
        )
        assert description.values.get("value", "") == self.register_as

    def test_get_register_personality_description(self):
        """Test the get_register_personality_description method of the GenericStrategy class."""
        description = self.strategy.get_register_personality_description()

        assert type(description) == Description
        assert description.data_model is AGENT_PERSONALITY_MODEL
        assert description.values.get("piece", "") == "genus"
        assert description.values.get("value", "") == "data"

    def test_get_register_classification_description(self):
        """Test the get_register_classification_description method of the GenericStrategy class."""
        description = self.strategy.get_register_classification_description()

        assert type(description) == Description
        assert description.data_model is AGENT_PERSONALITY_MODEL
        assert description.values.get("piece", "") == "classification"
        assert description.values.get("value", "") == "tac.participant"

    def test_get_unregister_service_description(self):
        """Test the get_unregister_service_description method of the GenericStrategy class."""
        description = self.strategy.get_unregister_service_description()

        assert type(description) == Description
        assert description.data_model is AGENT_REMOVE_SERVICE_MODEL
        assert description.values.get("key", "") == self.service_key

    def test_get_location_and_service_query(self):
        """Test the get_location_and_service_query method of the Strategy class."""
        # setup
        self.strategy.tac_version_id = "some_tac_id"

        # operation
        query = self.strategy.get_location_and_service_query()

        # after
        assert type(query) == Query
        assert len(query.constraints) == 2
        assert query.model is None

        location_constraint = Constraint(
            "location",
            ConstraintType(
                "distance",
                (
                    Location(
                        latitude=self.location["latitude"],
                        longitude=self.location["longitude"],
                    ),
                    self.search_radius,
                ),
            ),
        )
        assert query.constraints[0] == location_constraint

        service_key_filter = Constraint(
            f"{self.service_key}_{self.strategy.tac_version_id}",
            ConstraintType("==", self.search_for),
        )
        assert query.constraints[1] == service_key_filter

    def test_get_own_service_description_is_supply(self):
        """Test the get_own_service_description method of the Strategy class where is_supply is True."""
        # setup
        is_supply = True
        mocked_supplied_quantities_by_good_id = {
            good_id: quantity - 1
            for good_id, quantity in self.mocked_quantities_by_good_id.items()
        }
        expected_description = build_goods_description(
            mocked_supplied_quantities_by_good_id,
            self.mocked_currency_id,
            self.ledger_id,
            is_supply,
        )

        # operation
        with patch.object(
            self.skill.skill_context.transactions,
            "ownership_state_after_locks",
            return_value=self.mocked_ownership_state,
        ) as mock_ownership:
            actual_description = self.strategy.get_own_service_description(is_supply)

        # after
        mock_ownership.assert_any_call(is_seller=is_supply)
        assert actual_description == expected_description

    def test_get_own_service_description_not_is_supply(self):
        """Test the get_own_service_description method of the Strategy class where is_supply is False."""
        # setup
        is_supply = False
        mocked_demanded_quantities_by_good_id = {
            good_id: 1 for good_id in self.mocked_quantities_by_good_id.keys()
        }
        expected_description = build_goods_description(
            mocked_demanded_quantities_by_good_id,
            self.mocked_currency_id,
            self.ledger_id,
            is_supply,
        )

        # operation
        with patch.object(
            self.skill.skill_context.transactions,
            "ownership_state_after_locks",
            return_value=self.mocked_ownership_state,
        ) as mock_ownership:
            actual_description = self.strategy.get_own_service_description(is_supply)

        # after
        mock_ownership.assert_any_call(is_seller=is_supply)
        assert actual_description == expected_description

    def test_supplied_goods(self):
        """Test the _supplied_goods method of the Strategy class."""
        good_holdings = {"1": 1, "2": 5, "3": 10, "4": 1, "5": 0}
        actual_supply = self.strategy._supplied_goods(good_holdings)

        expected_supply = {"1": 0, "2": 4, "3": 9, "4": 0, "5": 0}
        assert actual_supply == expected_supply

    def test_demanded_goods(self):
        """Test the _demanded_goods method of the Strategy class."""
        good_holdings = {"1": 1, "2": 5, "3": 10, "4": 1, "5": 0}
        actual_demand = self.strategy._demanded_goods(good_holdings)

        expected_demand = {"1": 1, "2": 1, "3": 1, "4": 1, "5": 1}
        assert actual_demand == expected_demand

    def test_get_own_services_query_searching_seller(self):
        """Test the get_own_services_query method of the Strategy class where is_searching_for_sellers is True."""
        # setup
        is_searching_for_sellers = True
        expected_query = build_goods_query(
            list(self.mocked_quantities_by_good_id.keys()),
            self.mocked_currency_id,
            self.ledger_id,
            is_searching_for_sellers,
        )

        # operation
        with patch.object(
            self.skill.skill_context.transactions,
            "ownership_state_after_locks",
            return_value=self.mocked_ownership_state,
        ) as mock_ownership:
            actual_query = self.strategy.get_own_services_query(
                is_searching_for_sellers
            )

        # after
        mock_ownership.assert_any_call(is_seller=not is_searching_for_sellers)
        assert actual_query == expected_query

    def test_get_own_services_query_searching_buyers(self):
        """Test the get_own_services_query method of the Strategy class where is_searching_for_sellers is False (same as above)."""
        # setup
        is_searching_for_sellers = False
        expected_query = build_goods_query(
            list(self.mocked_quantities_by_good_id.keys()),
            self.mocked_currency_id,
            self.ledger_id,
            is_searching_for_sellers,
        )

        # operation
        with patch.object(
            self.skill.skill_context.transactions,
            "ownership_state_after_locks",
            return_value=self.mocked_ownership_state,
        ) as mock_ownership:
            actual_query = self.strategy.get_own_services_query(
                is_searching_for_sellers
            )

        # after
        mock_ownership.assert_any_call(is_seller=not is_searching_for_sellers)
        assert actual_query == expected_query

    def test__get_proposal_for_query(self):
        """Test the _get_proposal_for_query method of the Strategy class."""
        # setup
        is_seller = True
        mocked_query = Query(
            [Constraint("some_attribute_name", ConstraintType("==", "some_value"))],
            DataModel(
                "some_data_model_name",
                [
                    Attribute(
                        "some_attribute_name",
                        str,
                        False,
                        "Some attribute descriptions.",
                    )
                ],
            ),
        )

        proposal_1 = Description(
            {
                "some_attribute_name": "some_value",
                "ledger_id": self.ledger_id,
                "price": 100,
                "currency_id": "1",
                "fee": 1,
                "nonce": self.nonce,
            }
        )
        proposal_2 = Description(
            {
                "some_attribute_name": "some_value",
                "ledger_id": self.ledger_id,
                "price": -100,
                "currency_id": "1",
                "fee": 2,
                "nonce": self.nonce,
            }
        )
        mocked_candidate_proposals = [proposal_1, proposal_2]

        # operation
        with patch.object(
            self.strategy,
            "_generate_candidate_proposals",
            return_value=mocked_candidate_proposals,
        ) as mock_candid:
            actual_query = self.strategy._get_proposal_for_query(
                mocked_query, is_seller
            )

        # after
        mock_candid.assert_any_call(is_seller)
        assert actual_query in mocked_candidate_proposals

    def test_get_proposal_for_query(self):
        """Test the get_proposal_for_query method of the Strategy class."""
        # setup
        role = FipaDialogue.Role.SELLER
        is_seller = True

        mocked_query = Query(
            [Constraint("some_attribute_name", ConstraintType("==", "some_value"))],
            DataModel(
                "some_data_model_name",
                [
                    Attribute(
                        "some_attribute_name",
                        str,
                        False,
                        "Some attribute descriptions.",
                    )
                ],
            ),
        )
        own_description = Description(
            {
                "some_attribute_name": "some_value",
                "ledger_id": self.ledger_id,
                "price": 100,
                "currency_id": "1",
                "fee": 1,
                "nonce": self.nonce,
            }
        )

        expected_proposal = own_description

        # operation
        with patch.object(
            self.strategy, "get_own_service_description", return_value=own_description
        ) as mock_own:
            with patch.object(
                self.strategy, "_get_proposal_for_query", return_value=expected_proposal
            ) as mock_get_proposal:
                actual_proposal = self.strategy.get_proposal_for_query(
                    mocked_query, role
                )

        # after
        mock_own.assert_any_call(is_supply=is_seller)
        mock_get_proposal.assert_any_call(mocked_query, is_seller=is_seller)
        assert actual_proposal == expected_proposal

    def test_generate_candidate_proposals_i(self):
        """Test the _generate_candidate_proposals method of the Strategy class where role is seller."""
        # setup
        is_searching_for_sellers = True
        expected_proposed_prices = [463, 411, 1578, 584, 1101, 1244, 1234, 2025, 982]

        # operation
        with patch.object(
            self.skill.skill_context.transactions,
            "ownership_state_after_locks",
            return_value=self.mocked_ownership_state,
        ) as mock_ownership:
            actual_proposals = self.strategy._generate_candidate_proposals(
                is_searching_for_sellers
            )

        # after
        mock_ownership.assert_any_call(is_seller=is_searching_for_sellers)

        assert type(actual_proposals) == list
        assert len(actual_proposals) == 9

        for index in range(9):
            assert type(actual_proposals[index]) == Description
            assert actual_proposals[index].values[self.mocked_good_ids[index]] == 1
            for good_id_index in range(9):
                if index != good_id_index:
                    assert (
                        actual_proposals[index].values[
                            self.mocked_good_ids[good_id_index]
                        ]
                        == 0
                    )
            assert (
                actual_proposals[index].values["currency_id"] == self.mocked_currency_id
            )
            assert actual_proposals[index].values["ledger_id"] == self.ledger_id
            assert (
                actual_proposals[index].values["price"]
                == expected_proposed_prices[index]
            )
            assert actual_proposals[index].values["fee"] == 0
            assert actual_proposals[index].values["nonce"] == str(index + 1)

    def test_generate_candidate_proposals_ii(self):
        """Test the _generate_candidate_proposals method of the Strategy class where role is buyer."""
        # setup
        expected_proposed_prices = [457, 406, 1561, 577, 1088, 1231, 1220, 2004, 971]
        is_searching_for_sellers = False

        # operation
        with patch.object(
            self.skill.skill_context.transactions,
            "ownership_state_after_locks",
            return_value=self.mocked_ownership_state,
        ) as mock_ownership:
            actual_proposals = self.strategy._generate_candidate_proposals(
                is_searching_for_sellers
            )

        # after
        mock_ownership.assert_any_call(is_seller=is_searching_for_sellers)

        assert type(actual_proposals) == list
        assert len(actual_proposals) == len(self.mocked_good_ids)

        for index in range(9):
            assert type(actual_proposals[index]) == Description
            assert actual_proposals[index].values[self.mocked_good_ids[index]] == 1
            for good_id_index in range(9):
                if index != good_id_index:
                    assert (
                        actual_proposals[index].values[
                            self.mocked_good_ids[good_id_index]
                        ]
                        == 0
                    )
            assert (
                actual_proposals[index].values["currency_id"] == self.mocked_currency_id
            )
            assert actual_proposals[index].values["ledger_id"] == self.ledger_id
            assert (
                actual_proposals[index].values["price"]
                == expected_proposed_prices[index]
            )
            assert actual_proposals[index].values["fee"] == 0
            assert actual_proposals[index].values["nonce"] == str(index + 1)

    def test_generate_candidate_proposals_iii(self):
        """Test the _generate_candidate_proposals method of the Strategy class where is_seller and quantity is 0."""
        # setup
        is_searching_for_sellers = True
        expected_proposed_price = 982

        mocked_good_quantities = [1, 0, 0, 1, 0, 1, 0, 1, 6]
        mocked_quantities_by_good_id = dict(
            zip(self.mocked_good_ids, mocked_good_quantities)
        )
        self.mocked_ownership_state._amount_by_currency_id = None
        self.mocked_ownership_state._quantities_by_good_id = None
        self.mocked_ownership_state.set(
            self.mocked_amount_by_currency_id, mocked_quantities_by_good_id
        )

        # operation
        with patch.object(
            self.skill.skill_context.transactions,
            "ownership_state_after_locks",
            return_value=self.mocked_ownership_state,
        ) as mock_ownership:
            actual_proposals = self.strategy._generate_candidate_proposals(
                is_searching_for_sellers
            )

        # after
        mock_ownership.assert_any_call(is_seller=is_searching_for_sellers)

        assert type(actual_proposals) == list
        assert len(actual_proposals) == 1
        actual_proposal = actual_proposals[0]

        assert type(actual_proposal) == Description
        assert actual_proposal.values[self.mocked_good_ids[8]] == 1
        for good_id_index in range(8):
            assert actual_proposal.values[self.mocked_good_ids[good_id_index]] == 0
        assert actual_proposal.values["currency_id"] == self.mocked_currency_id
        assert actual_proposal.values["ledger_id"] == self.ledger_id
        assert actual_proposal.values["price"] == expected_proposed_price
        assert actual_proposal.values["fee"] == 0
        assert actual_proposal.values["nonce"] == "1"

    def test_generate_candidate_proposals_iv(self):
        """Test the _generate_candidate_proposals method of the Strategy class where proposed price is 0."""
        # setup
        is_searching_for_sellers = True

        mocked_good_quantities = [2, 0, 0, 1, 0, 1, 0, 1, 0]
        mocked_quantities_by_good_id = dict(
            zip(self.mocked_good_ids, mocked_good_quantities)
        )
        self.mocked_ownership_state._amount_by_currency_id = None
        self.mocked_ownership_state._quantities_by_good_id = None
        self.mocked_ownership_state.set(
            self.mocked_amount_by_currency_id, mocked_quantities_by_good_id
        )

        utility_params_by_good_id = {
            "13": -100.0,
            "14": 43700.0,
            "15": 163200.0,
            "16": 59800.0,
            "17": 114900.0,
            "18": 128700.00000000001,
            "19": 126400.00000000001,
            "20": 211500.0,
            "21": 103500.0,
        }
        self.mocked_preferences._exchange_params_by_currency_id = None
        self.mocked_preferences._utility_params_by_good_id = None
        self.mocked_preferences.set(
            exchange_params_by_currency_id=self.exchange_params_by_currency_id,
            utility_params_by_good_id=utility_params_by_good_id,
        )

        # operation
        with patch.object(
            self.skill.skill_context.transactions,
            "ownership_state_after_locks",
            return_value=self.mocked_ownership_state,
        ) as mock_ownership:
            actual_proposals = self.strategy._generate_candidate_proposals(
                is_searching_for_sellers
            )

        # after
        mock_ownership.assert_any_call(is_seller=is_searching_for_sellers)
        assert actual_proposals == []

    def test_is_profitable_transaction_not_affordable(self):
        """Test the is_profitable_transaction method of the Strategy class where is_affordable_transaction is False."""
        is_searching_for_sellers = False
        role = FipaDialogue.Role.BUYER
        proposal = Description(
            {
                "13": 1,
                "14": 0,
                "15": 0,
                "16": 0,
                "17": 0,
                "18": 0,
                "19": 0,
                "20": 0,
                "21": 0,
                "ledger_id": self.ledger_id,
                "price": 10000000,
                "currency_id": self.mocked_currency_id,
                "fee": 0,
                "nonce": self.nonce,
            }
        )
        terms = self.strategy.terms_from_proposal(
            proposal, self.sender, self.counterparty, role
        )

        # operation
        with patch.object(
            self.skill.skill_context.transactions,
            "ownership_state_after_locks",
            return_value=self.mocked_ownership_state,
        ) as mock_ownership:
            with patch.object(
                self.mocked_ownership_state,
                "is_affordable_transaction",
                return_value=False,
            ) as mock_is_affordable:
                is_profitable = self.strategy.is_profitable_transaction(terms, role)

        # after
        mock_ownership.assert_any_call(is_searching_for_sellers)
        mock_is_affordable.assert_any_call(terms)

        assert not is_profitable

    def test_is_profitable_transaction_is_affordable(self):
        """Test the is_profitable_transaction method of the Strategy class where is_affordable_transaction is True."""
        is_searching_for_sellers = True
        role = FipaDialogue.Role.SELLER
        proposal = Description(
            {
                "13": 1,
                "14": 0,
                "15": 0,
                "16": 0,
                "17": 0,
                "18": 0,
                "19": 0,
                "20": 0,
                "21": 0,
                "ledger_id": self.ledger_id,
                "price": 463,
                "currency_id": self.mocked_currency_id,
                "fee": 0,
                "nonce": self.nonce,
            }
        )
        terms = self.strategy.terms_from_proposal(
            proposal, self.sender, self.counterparty, role
        )

        # operation
        with patch.object(
            self.skill.skill_context.transactions,
            "ownership_state_after_locks",
            return_value=self.mocked_ownership_state,
        ) as mock_ownership:
            with patch.object(
                self.mocked_ownership_state,
                "is_affordable_transaction",
                return_value=True,
            ) as mock_is_affordable:
                is_profitable = self.strategy.is_profitable_transaction(terms, role)

        # after
        mock_ownership.assert_any_call(is_searching_for_sellers)
        mock_is_affordable.assert_any_call(terms)

        assert is_profitable

    def test_terms_from_proposal_seller(self):
        """Test the terms_from_proposal method of the Strategy class where is_seller is True."""
        proposal = Description(
            {
                "2": 5,
                "ledger_id": self.ledger_id,
                "price": 100,
                "currency_id": "FET",
                "fee": 1,
                "nonce": self.nonce,
            }
        )
        role = FipaDialogue.Role.SELLER
        is_seller = True

        expected_terms = Terms(
            ledger_id=self.ledger_id,
            sender_address=self.sender,
            counterparty_address=self.counterparty,
            amount_by_currency_id={
                proposal.values["currency_id"]: proposal.values["price"]
            },
            quantities_by_good_id={"2": -5},
            is_sender_payable_tx_fee=not is_seller,
            nonce=self.nonce,
            fee_by_currency_id={proposal.values["currency_id"]: proposal.values["fee"]},
        )

        actual_terms = self.strategy.terms_from_proposal(
            proposal, self.sender, self.counterparty, role
        )

        assert actual_terms == expected_terms

    def test_terms_from_proposal_buyer(self):
        """Test the terms_from_proposal method of the Strategy class where is_seller is False."""
        proposal = Description(
            {
                "2": 5,
                "ledger_id": self.ledger_id,
                "price": 100,
                "currency_id": "FET",
                "fee": 1,
                "nonce": self.nonce,
            }
        )
        role = FipaDialogue.Role.BUYER
        is_seller = False

        expected_terms = Terms(
            ledger_id=self.ledger_id,
            sender_address=self.sender,
            counterparty_address=self.counterparty,
            amount_by_currency_id={
                proposal.values["currency_id"]: -proposal.values["price"]
            },
            quantities_by_good_id={"2": 5},
            is_sender_payable_tx_fee=not is_seller,
            nonce=self.nonce,
            fee_by_currency_id={proposal.values["currency_id"]: proposal.values["fee"]},
        )

        actual_terms = self.strategy.terms_from_proposal(
            proposal, self.sender, self.counterparty, role
        )

        assert actual_terms == expected_terms

    def test_kwargs_from_terms_seller_ethereum(self):
        """Test the kwargs_from_terms method of the Strategy class where is_seller is True."""
        is_seller = True
        terms = Terms(
            ledger_id=self.ledger_id,
            sender_address=self.sender,
            counterparty_address=self.counterparty,
            amount_by_currency_id={"1": 10},
            quantities_by_good_id={"2": -5},
            is_sender_payable_tx_fee=not is_seller,
            nonce=self.nonce,
            fee_by_currency_id={"1": 1},
        )

        expected_kwargs = {
            "from_address": self.sender,
            "to_address": self.counterparty,
            "token_ids": [1, 2],
            "from_supplies": [0, 5],
            "to_supplies": [10, 0],
            "value": 0,
            "trade_nonce": 125,
            "signature": self.signature,
        }

        actual_kwargs = self.strategy.kwargs_from_terms(
            terms, self.signature, is_from_terms_sender=True
        )

        assert actual_kwargs == expected_kwargs

        expected_kwargs = {
            "from_address": self.counterparty,
            "to_address": self.sender,
            "token_ids": [1, 2],
            "from_supplies": [10, 0],
            "to_supplies": [0, 5],
            "value": 0,
            "trade_nonce": 125,
            "signature": self.signature,
        }
        actual_kwargs = self.strategy.kwargs_from_terms(
            terms, self.signature, is_from_terms_sender=False
        )

        assert actual_kwargs == expected_kwargs

    def test_kwargs_from_terms_buyer_fetchai(self):
        """Test the kwargs_from_terms method of the Strategy class where is_seller is False (no difference with seller)."""
        is_seller = False
        terms = Terms(
            ledger_id=self.ledger_id,
            sender_address=self.sender,
            counterparty_address=self.counterparty,
            amount_by_currency_id={"1": 10},
            quantities_by_good_id={"2": -5},
            is_sender_payable_tx_fee=not is_seller,
            nonce=self.nonce,
            fee_by_currency_id={"1": 1},
        )

        expected_kwargs = {
            "from_address": self.sender,
            "to_address": self.counterparty,
            "token_ids": [1, 2],
            "from_supplies": [0, 5],
            "to_supplies": [10, 0],
            "value": 1,
            "trade_nonce": 125,
            "from_pubkey": self.sender_pk,
            "to_pubkey": self.counterparty_pk,
        }

        actual_kwargs = self.strategy.kwargs_from_terms(
            terms,
            sender_public_key=self.sender_pk,
            counterparty_public_key=self.counterparty_pk,
        )

        assert actual_kwargs == expected_kwargs

    def test_kwargs_from_terms_i(self):
        """Test the kwargs_from_terms method of the Strategy class where sender's IS and counterparty's public key is NOT provided."""
        is_seller = True
        terms = Terms(
            ledger_id=self.ledger_id,
            sender_address=self.sender,
            counterparty_address=self.counterparty,
            amount_by_currency_id={"1": 10},
            quantities_by_good_id={"2": -5},
            is_sender_payable_tx_fee=not is_seller,
            nonce=self.nonce,
            fee_by_currency_id={"1": 1},
        )

        with pytest.raises(
            AEAEnforceError,
            match="Either provide both sender's and counterparty's public-keys or neither's.",
        ):
            self.strategy.kwargs_from_terms(
                terms,
                self.signature,
                is_from_terms_sender=True,
                sender_public_key="some_public_key",
            )

    def test_kwargs_from_terms_ii(self):
        """Test the kwargs_from_terms method of the Strategy class where sender's is NOT and counterparty's public key IS provided."""
        is_seller = True
        terms = Terms(
            ledger_id=self.ledger_id,
            sender_address=self.sender,
            counterparty_address=self.counterparty,
            amount_by_currency_id={"1": 10},
            quantities_by_good_id={"2": -5},
            is_sender_payable_tx_fee=not is_seller,
            nonce=self.nonce,
            fee_by_currency_id={"1": 1},
        )

        with pytest.raises(
            AEAEnforceError,
            match="Either provide both sender's and counterparty's public-keys or neither's.",
        ):
            self.strategy.kwargs_from_terms(
                terms,
                self.signature,
                is_from_terms_sender=True,
                counterparty_public_key="some_public_key",
            )

    def test_kwargs_from_terms_iii(self):
        """Test the kwargs_from_terms method of the Strategy class where signature IS and a public_key is NOT provided."""
        is_seller = True
        terms = Terms(
            ledger_id=self.ledger_id,
            sender_address=self.sender,
            counterparty_address=self.counterparty,
            amount_by_currency_id={"1": 10},
            quantities_by_good_id={"2": -5},
            is_sender_payable_tx_fee=not is_seller,
            nonce=self.nonce,
            fee_by_currency_id={"1": 1},
        )

        with pytest.raises(
            AEAEnforceError,
            match=re.escape(
                "Either provide signature (for Ethereum-based TAC) or sender and counterparty's public keys (for Fetchai-based TAC), or neither (for and non-contract-based Tac)"
            ),
        ):
            self.strategy.kwargs_from_terms(
                terms,
                self.signature,
                is_from_terms_sender=True,
                sender_public_key="some_public_key",
                counterparty_public_key="some_other_public_key",
            )
