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
"""This module contains the tests of the strategy class of the generic seller skill."""

from pathlib import Path

import pytest

from aea.configurations.constants import DEFAULT_LEDGER
from aea.crypto.ledger_apis import LedgerApis
from aea.helpers.search.models import (
    Constraint,
    ConstraintType,
    Description,
    Location,
    Query,
)
from aea.helpers.transaction.base import Terms
from aea.test_tools.test_skill import BaseSkillTestCase, COUNTERPARTY_AGENT_ADDRESS

from packages.fetchai.skills.generic_seller.strategy import (
    AGENT_LOCATION_MODEL,
    AGENT_PERSONALITY_MODEL,
    AGENT_REMOVE_SERVICE_MODEL,
    AGENT_SET_SERVICE_MODEL,
    GenericStrategy,
    SIMPLE_SERVICE_MODEL,
)

from tests.conftest import ROOT_DIR


class TestGenericStrategy(BaseSkillTestCase):
    """Test GenericStrategy of generic seller."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "generic_seller")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.ledger_id = DEFAULT_LEDGER
        cls.is_ledger_tx = True
        cls.currency_id = "some_currency_id"
        cls.unit_price = 20
        cls.service_id = "some_service_id"
        cls.location = {
            "longitude": 0.127,
            "latitude": 51.5194,
        }
        cls.service_data = {"key": "seller_service", "value": "some_service"}
        cls.has_data_source = False
        cls.data_for_sale = {"some_data_type": "some_data"}
        cls.strategy = GenericStrategy(
            ledger_id=cls.ledger_id,
            is_ledger_tx=cls.is_ledger_tx,
            currency_id=cls.currency_id,
            unit_price=cls.unit_price,
            service_id=cls.service_id,
            location=cls.location,
            service_data=cls.service_data,
            has_data_source=cls.has_data_source,
            data_for_sale=cls.data_for_sale,
            name="strategy",
            skill_context=cls._skill.skill_context,
        )

    def test_properties(self):
        """Test the properties of GenericStrategy class."""
        assert self.strategy.ledger_id == self.ledger_id
        assert self.strategy.is_ledger_tx == self.is_ledger_tx

    def test_get_location_description(self):
        """Test the get_location_description method of the GenericStrategy class."""
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
        assert description.values.get("key", "") == "seller_service"
        assert description.values.get("value", "") == "some_service"

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
        assert description.values.get("value", "") == "seller"

    def test_get_service_description(self):
        """Test the get_service_description method of the GenericStrategy class."""
        description = self.strategy.get_service_description()

        assert type(description) == Description
        assert description.data_model is SIMPLE_SERVICE_MODEL
        assert description.values.get("seller_service", "") == "some_service"

    def test_get_unregister_service_description(self):
        """Test the get_unregister_service_description method of the GenericStrategy class."""
        description = self.strategy.get_unregister_service_description()

        assert type(description) == Description
        assert description.data_model is AGENT_REMOVE_SERVICE_MODEL
        assert description.values.get("key", "") == "seller_service"

    def test_is_matching_supply(self):
        """Test the is_matching_supply method of the GenericStrategy class."""
        acceptable_constraint = Constraint(
            "seller_service", ConstraintType("==", "some_service")
        )
        matching_query = Query([acceptable_constraint])
        is_matching_supply = self.strategy.is_matching_supply(matching_query)
        assert is_matching_supply

        unacceptable_constraint = Constraint(
            "seller_service", ConstraintType("==", "some_other_service")
        )
        unmatching_query = Query([unacceptable_constraint])
        is_matching_supply = self.strategy.is_matching_supply(unmatching_query)
        assert not is_matching_supply

    def test_generate_proposal_terms_and_data(self):
        """Test the generate_proposal_terms_and_data method of the GenericStrategy class."""
        # setup
        seller = self.skill.skill_context.agent_address
        total_price = len(self.data_for_sale) * self.unit_price
        sale_quantity = len(self.data_for_sale)
        tx_nonce = LedgerApis.generate_tx_nonce(
            identifier=self.ledger_id, seller=seller, client=COUNTERPARTY_AGENT_ADDRESS,
        )
        query = Query(
            [Constraint("seller_service", ConstraintType("==", "some_service"))]
        )

        # expected returned values
        expected_proposal = Description(
            {
                "ledger_id": self.ledger_id,
                "price": total_price,
                "currency_id": self.currency_id,
                "service_id": self.service_id,
                "quantity": sale_quantity,
                "tx_nonce": tx_nonce,
            }
        )
        expected_terms = Terms(
            ledger_id=self.ledger_id,
            sender_address=seller,
            counterparty_address=COUNTERPARTY_AGENT_ADDRESS,
            amount_by_currency_id={self.currency_id: total_price},
            quantities_by_good_id={self.service_id: -sale_quantity},
            is_sender_payable_tx_fee=False,
            nonce=tx_nonce,
            fee_by_currency_id={self.currency_id: 0},
        )

        # operation
        proposal, terms, data = self.strategy.generate_proposal_terms_and_data(
            query, COUNTERPARTY_AGENT_ADDRESS
        )

        # after
        assert proposal == expected_proposal
        assert terms == expected_terms
        assert data == self.data_for_sale

    def test_collect_from_data_source(self):
        """Test the collect_from_data_source method of the GenericStrategy class."""
        with pytest.raises(NotImplementedError):
            self.strategy.collect_from_data_source()
