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
"""This module contains the tests of the strategy class of the generic buyer skill."""

from pathlib import Path

from aea.configurations.constants import DEFAULT_LEDGER
from aea.helpers.search.models import Constraint, ConstraintType, Description, Query
from aea.helpers.transaction.base import Terms
from aea.test_tools.test_skill import BaseSkillTestCase, COUNTERPARTY_AGENT_ADDRESS

from packages.fetchai.skills.generic_buyer.strategy import (
    GenericStrategy,
    SIMPLE_SERVICE_MODEL,
)

from tests.conftest import ROOT_DIR


class TestGenericStrategy(BaseSkillTestCase):
    """Test GenericStrategy of generic buyer."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "generic_buyer")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.ledger_id = DEFAULT_LEDGER
        cls.is_ledger_tx = True
        cls.currency_id = "some_currency_id"
        cls.max_unit_price = 20
        cls.max_tx_fee = 1
        cls.service_id = "some_service_id"
        cls.search_query = {
            "constraint_type": "==",
            "search_key": "seller_service",
            "search_value": "some_search_value",
        }
        cls.location = {
            "longitude": 0.127,
            "latitude": 51.5194,
        }
        cls.search_radius = 5.0
        cls.max_negotiations = 2
        cls.strategy = GenericStrategy(
            ledger_id=cls.ledger_id,
            is_ledger_tx=cls.is_ledger_tx,
            currency_id=cls.currency_id,
            max_unit_price=cls.max_unit_price,
            max_tx_fee=cls.max_tx_fee,
            service_id=cls.service_id,
            search_query=cls.search_query,
            location=cls.location,
            search_radius=cls.search_radius,
            max_negotiations=cls.max_negotiations,
            name="strategy",
            skill_context=cls._skill.skill_context,
        )

    def test_properties(self):
        """Test the properties of GenericStrategy class."""
        assert self.strategy.ledger_id == self.ledger_id
        assert self.strategy.is_ledger_tx == self.is_ledger_tx
        assert self.strategy.is_searching is False

        self.strategy.is_searching = True
        assert self.strategy.is_searching is True

        assert self.strategy.balance == 0

        self.strategy.balance = 100
        assert self.strategy.balance == 100

        assert self.strategy.max_negotiations is self.max_negotiations

    def test_get_location_and_service_query(self):
        """Test the get_location_and_service_query method of the GenericStrategy class."""
        query = self.strategy.get_location_and_service_query()

        assert type(query) == Query
        assert len(query.constraints) == 2
        assert query.model is None

        location_constraint = Constraint(
            "location",
            ConstraintType(
                "distance", (self.strategy._agent_location, self.search_radius)
            ),
        )
        assert query.constraints[0] == location_constraint

        service_key_constraint = Constraint(
            self.search_query["search_key"],
            ConstraintType(
                self.search_query["constraint_type"], self.search_query["search_value"],
            ),
        )
        assert query.constraints[1] == service_key_constraint

    def test_get_service_query(self):
        """Test the get_service_query method of the GenericStrategy class."""
        query = self.strategy.get_service_query()

        assert type(query) == Query
        assert len(query.constraints) == 1

        assert query.model == SIMPLE_SERVICE_MODEL

        service_key_constraint = Constraint(
            self.search_query["search_key"],
            ConstraintType(
                self.search_query["constraint_type"], self.search_query["search_value"],
            ),
        )
        assert query.constraints[0] == service_key_constraint

    def test_is_acceptable_proposal(self):
        """Test the is_acceptable_proposal method of the GenericStrategy class."""
        acceptable_description = Description(
            {
                "ledger_id": self.ledger_id,
                "price": 150,
                "currency_id": self.currency_id,
                "service_id": self.service_id,
                "quantity": 10,
                "tx_nonce": "some_tx_nonce",
            }
        )
        is_acceptable = self.strategy.is_acceptable_proposal(acceptable_description)
        assert is_acceptable

        unacceptable_description = Description(
            {
                "ledger_id": self.ledger_id,
                "price": 250,
                "currency_id": self.currency_id,
                "service_id": self.service_id,
                "quantity": 10,
                "tx_nonce": "some_tx_nonce",
            }
        )
        is_acceptable = self.strategy.is_acceptable_proposal(unacceptable_description)
        assert not is_acceptable

    def test_is_affordable_proposal(self):
        """Test the is_affordable_proposal method of the GenericStrategy class."""
        description = Description(
            {
                "ledger_id": self.ledger_id,
                "price": 150,
                "currency_id": self.currency_id,
                "service_id": self.service_id,
                "quantity": 10,
                "tx_nonce": "some_tx_nonce",
            }
        )
        self.strategy.balance = 151
        is_affordable = self.strategy.is_affordable_proposal(description)
        assert is_affordable

        self.strategy.balance = 150
        is_affordable = self.strategy.is_affordable_proposal(description)
        assert not is_affordable

        self.strategy._is_ledger_tx = False
        is_affordable = self.strategy.is_affordable_proposal(description)
        assert is_affordable

    def test_terms_from_proposal(self):
        """Test the terms_from_proposal method of the GenericStrategy class."""
        description = Description(
            {
                "ledger_id": self.ledger_id,
                "price": 150,
                "currency_id": self.currency_id,
                "service_id": self.service_id,
                "quantity": 10,
                "tx_nonce": "some_tx_nonce",
            }
        )
        terms = Terms(
            ledger_id=self.ledger_id,
            sender_address=self.skill.skill_context.agent_address,
            counterparty_address=COUNTERPARTY_AGENT_ADDRESS,
            amount_by_currency_id={self.currency_id: -150},
            quantities_by_good_id={self.service_id: 10},
            is_sender_payable_tx_fee=True,
            nonce="some_tx_nonce",
            fee_by_currency_id={self.currency_id: self.max_tx_fee},
        )
        assert (
            self.strategy.terms_from_proposal(description, COUNTERPARTY_AGENT_ADDRESS)
            == terms
        )
