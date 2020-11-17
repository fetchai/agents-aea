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

from pathlib import Path
from unittest.mock import patch

import pytest

from aea.exceptions import AEAEnforceError
from aea.helpers.search.models import (
    Constraint,
    ConstraintType,
    Description,
    Location,
    Query,
)
from aea.helpers.transaction.base import Terms
from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.skills.tac_negotiation.dialogues import FipaDialogue
from packages.fetchai.skills.tac_negotiation.strategy import (
    AGENT_LOCATION_MODEL,
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
        super().setup()
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
        description = self.strategy.get_register_service_description()

        assert type(description) == Description
        assert description.data_model is AGENT_SET_SERVICE_MODEL
        assert description.values.get("key", "") == self.service_key
        assert description.values.get("value", "") == self.register_as

    def test_get_unregister_service_description(self):
        """Test the get_unregister_service_description method of the GenericStrategy class."""
        description = self.strategy.get_unregister_service_description()

        assert type(description) == Description
        assert description.data_model is AGENT_REMOVE_SERVICE_MODEL
        assert description.values.get("key", "") == self.service_key

    def test_get_location_and_service_query(self):
        """Test the get_location_and_service_query method of the Strategy class."""
        query = self.strategy.get_location_and_service_query()

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
            self.service_key, ConstraintType("==", self.search_for)
        )
        assert query.constraints[1] == service_key_filter

    def test_get_own_service_description(self):
        """Test the get_own_service_description method of the Strategy class."""
        # ToDo complete
        pytest.skip("not working")
        is_supply = True
        mocked_description = Description({"foo1": 1, "bar1": 2})

        with patch.object(
            self.skill.skill_context.transactions, "ownership_state_after_locks"
        ) as mock_ownership:
            with patch.object(
                self.strategy,
                "build_goods_description",
                return_value=mocked_description,
            ) as mock_build:
                with patch.object(self.strategy, "_supplied_goods") as mock_supplied:
                    self.strategy.get_own_service_description(is_supply)

        mock_ownership.assert_any_call(is_supply)
        mock_supplied.assert_called_once()
        mock_build.assert_called_once()

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

    def test_get_own_services_query(self):
        """Test the get_own_services_query method of the Strategy class."""
        # ToDo complete

    def test__get_proposal_for_query(self):
        """Test the _get_proposal_for_query method of the Strategy class."""
        # ToDo complete

    def test_get_proposal_for_query(self):
        """Test the get_proposal_for_query method of the Strategy class."""
        # ToDo complete

    def test_generate_candidate_proposals(self):
        """Test the _generate_candidate_proposals method of the Strategy class."""
        # ToDo complete

    def test_is_profitable_transaction(self):
        """Test the is_profitable_transaction method of the Strategy class."""
        # ToDo complete

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

    def test_kwargs_from_terms_seller(self):
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
            "from_supplies": [10, 0],
            "to_supplies": [0, 5],
            "value": 0,
            "trade_nonce": 125,
            "signature": self.signature,
        }

        actual_kwargs = self.strategy.kwargs_from_terms(terms, self.signature)

        assert actual_kwargs == expected_kwargs

    def test_kwargs_from_terms_buyer(self):
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
            "from_supplies": [10, 0],
            "to_supplies": [0, 5],
            "value": 0,
            "trade_nonce": 125,
            "signature": self.signature,
        }

        actual_kwargs = self.strategy.kwargs_from_terms(terms, self.signature)

        assert actual_kwargs == expected_kwargs
