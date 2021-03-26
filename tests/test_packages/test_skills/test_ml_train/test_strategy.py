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
"""This module contains the tests of the strategy class of the ml_train skill."""

import json
import sys
from pathlib import Path

import numpy as np
import pytest

from aea.exceptions import AEAEnforceError
from aea.helpers.search.models import Constraint, ConstraintType, Description, Query
from aea.helpers.transaction.base import Terms
from aea.test_tools.test_skill import BaseSkillTestCase, COUNTERPARTY_AGENT_ADDRESS

from packages.fetchai.skills.ml_data_provider.strategy import (
    Strategy as DataProviderStrategy,
)
from packages.fetchai.skills.ml_train.strategy import (
    DEFAULT_LOCATION,
    DEFAULT_MAX_NEGOTIATIONS,
    DEFAULT_MAX_ROW_PRICE,
    DEFAULT_MAX_TX_FEE,
    DEFAULT_SEARCH_QUERY,
    DEFAULT_SEARCH_RADIUS,
    DEFAULT_SERVICE_ID,
    SIMPLE_DATA_MODEL,
    Strategy,
)

from tests.conftest import ROOT_DIR
from tests.test_packages.test_skills.test_ml_train.helpers import produce_data


class TestStrategy(BaseSkillTestCase):
    """Test Strategy of ml_train."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "ml_train")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.max_unit_price = DEFAULT_MAX_ROW_PRICE
        cls.max_buyer_tx_fee = DEFAULT_MAX_TX_FEE
        cls.currency_id = "FET"
        cls.ledger_id = "fetchai"
        cls.is_ledger_tx = False
        cls.max_negotiations = DEFAULT_MAX_NEGOTIATIONS
        cls.service_id = DEFAULT_SERVICE_ID
        cls.search_query = DEFAULT_SEARCH_QUERY
        cls.location = DEFAULT_LOCATION
        cls.search_radius = DEFAULT_SEARCH_RADIUS

        cls.strategy = Strategy(
            max_unit_price=cls.max_unit_price,
            max_buyer_tx_fee=cls.max_buyer_tx_fee,
            currency_id=cls.currency_id,
            ledger_id=cls.ledger_id,
            is_ledger_tx=cls.is_ledger_tx,
            max_negotiations=cls.max_negotiations,
            service_id=cls.service_id,
            search_query=cls.search_query,
            location=cls.location,
            search_radius=cls.search_radius,
            name="strategy",
            skill_context=cls._skill.skill_context,
        )

    def test_properties(self):
        """Test the properties of Strategy class."""
        assert self.strategy.ledger_id == self.ledger_id
        assert self.strategy.is_ledger_tx == self.is_ledger_tx
        assert self.strategy.max_negotiations == self.max_negotiations

        assert self.strategy.is_searching is False
        self.strategy.is_searching = True
        assert self.strategy.is_searching is True
        with pytest.raises(AEAEnforceError, match="Can only set bool on is_searching!"):
            self.strategy.is_searching = "True"

        assert self.strategy.balance == 0
        self.strategy.balance = 5
        assert self.strategy.balance == 5

        assert self.strategy.current_task_id is None
        self.strategy.current_task_id = 2
        assert self.strategy.current_task_id == 2

        assert self.strategy.weights is None
        self.strategy.weights = []
        assert self.strategy.weights == []

        assert self.strategy.data == []

    def test_get_next_transaction_id(self):
        """Test the get_next_transaction_id method of the Strategy class."""
        tx_id = self.strategy.get_next_transaction_id()
        assert tx_id == f"transaction_{self.strategy._tx_id}"

    def test_get_location_and_service_query(self):
        """Test the get_location_and_service_query method of the Strategy class."""
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
        """Test the get_service_query method of the Strategy class."""
        query = self.strategy.get_service_query()

        assert type(query) == Query
        assert len(query.constraints) == 1

        assert query.model == SIMPLE_DATA_MODEL

        service_key_constraint = Constraint(
            self.search_query["search_key"],
            ConstraintType(
                self.search_query["constraint_type"], self.search_query["search_value"],
            ),
        )
        assert query.constraints[0] == service_key_constraint

    def test_is_acceptable_proposal(self):
        """Test the is_acceptable_proposal method of the Strategy class."""
        acceptable_description = Description(
            {
                "ledger_id": self.ledger_id,
                "price": 20,
                "currency_id": self.currency_id,
                "service_id": self.service_id,
                "quantity": 10,
                "tx_nonce": "some_tx_nonce",
                "seller_tx_fee": 0,
                "buyer_tx_fee": 0,
                "batch_size": 5,
            }
        )
        is_acceptable = self.strategy.is_acceptable_terms(acceptable_description)
        assert is_acceptable

        unacceptable_description = Description(
            {
                "ledger_id": self.ledger_id,
                "price": 250,
                "currency_id": self.currency_id,
                "service_id": self.service_id,
                "quantity": 10,
                "tx_nonce": "some_tx_nonce",
                "seller_tx_fee": 0,
                "buyer_tx_fee": 0,
                "batch_size": 5,
            }
        )
        is_acceptable = self.strategy.is_acceptable_terms(unacceptable_description)
        assert not is_acceptable

    def test_is_affordable_proposal(self):
        """Test the is_affordable_proposal method of the Strategy class."""
        self.strategy._is_ledger_tx = True
        description = Description(
            {
                "ledger_id": self.ledger_id,
                "price": 20,
                "currency_id": self.currency_id,
                "service_id": self.service_id,
                "quantity": 10,
                "tx_nonce": "some_tx_nonce",
                "seller_tx_fee": 0,
                "buyer_tx_fee": 0,
                "batch_size": 5,
            }
        )
        self.strategy.balance = 20
        is_affordable = self.strategy.is_affordable_terms(description)
        assert is_affordable

        self.strategy.balance = 19
        is_affordable = self.strategy.is_affordable_terms(description)
        assert not is_affordable

        self.strategy._is_ledger_tx = False
        is_affordable = self.strategy.is_affordable_terms(description)
        assert is_affordable

    def test_terms_from_proposal(self):
        """Test the terms_from_proposal method of the Strategy class."""
        description = Description(
            {
                "ledger_id": self.ledger_id,
                "price": 150,
                "address": COUNTERPARTY_AGENT_ADDRESS,
                "currency_id": self.currency_id,
                "service_id": self.service_id,
                "quantity": 10,
                "tx_nonce": "some_tx_nonce",
                "seller_tx_fee": 0,
                "buyer_tx_fee": 0,
                "batch_size": 5,
                "nonce": "some_tx_nonce",
            }
        )
        terms = Terms(
            ledger_id=self.ledger_id,
            sender_address=self.skill.skill_context.agent_address,
            counterparty_address=COUNTERPARTY_AGENT_ADDRESS,
            amount_by_currency_id={self.currency_id: -150},
            quantities_by_good_id={self.service_id: 5},
            is_sender_payable_tx_fee=True,
            nonce="some_tx_nonce",
            fee_by_currency_id={self.currency_id: self.max_buyer_tx_fee},
        )
        assert self.strategy.terms_from_proposal(description) == terms

    @pytest.mark.skipif(
        sys.version_info >= (3, 9),
        reason="This test uses tensorflow which, at the time of writing, does not yet support python version 3.9.",
    )
    def test_decode_sample_data_i(self):
        """Test the decode_sample_data method of the Strategy class where data is NOT None."""
        # setup
        data = produce_data(batch_size=32)
        encoded_data = DataProviderStrategy.encode_sample_data(data)

        # operation
        decoded_data = self.strategy.decode_sample_data(encoded_data)

        # after
        assert type(decoded_data) == tuple

        numpy_data_0 = decoded_data[0]
        numpy_data_1 = decoded_data[1]

        assert type(numpy_data_0) == type(numpy_data_1) == np.ndarray
        assert (numpy_data_0 == data[0]).all()
        assert (numpy_data_1 == data[1]).all()

    def test_decode_sample_data_ii(self):
        """Test the decode_sample_data method of the Strategy class where data IS None."""
        # setup
        data = None
        encoded_data = json.dumps(data).encode("utf-8")

        # operation
        decoded_data = self.strategy.decode_sample_data(encoded_data)

        # after
        assert decoded_data is None
