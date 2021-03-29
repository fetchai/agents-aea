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
"""This module contains the tests of the strategy class of the ml_data_provider skill."""

import json
import sys
from pathlib import Path
from unittest.mock import PropertyMock, patch

import numpy as np
import pytest

from aea.configurations.constants import DEFAULT_LEDGER
from aea.helpers.search.models import (
    Constraint,
    ConstraintType,
    Description,
    Location,
    Query,
)
from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.skills.ml_data_provider.strategy import (
    AGENT_LOCATION_MODEL,
    AGENT_PERSONALITY_MODEL,
    AGENT_REMOVE_SERVICE_MODEL,
    AGENT_SET_SERVICE_MODEL,
    DEFAULT_BATCH_SIZE,
    DEFAULT_BUYER_TX_FEE,
    DEFAULT_CLASSIFICATION,
    DEFAULT_LOCATION,
    DEFAULT_PERSONALITY_DATA,
    DEFAULT_PRICE_PER_DATA_BATCH,
    DEFAULT_SELLER_TX_FEE,
    DEFAULT_SERVICE_DATA,
    DEFAULT_SERVICE_ID,
    SIMPLE_DATA_MODEL,
    Strategy,
)

from tests.conftest import ROOT_DIR


@pytest.mark.skipif(
    sys.version_info >= (3, 9),
    reason="These tests use tensorflow which, at the time of writing, does not yet support python version 3.9.",
)
class TestGenericStrategy(BaseSkillTestCase):
    """Test Strategy of ml_data_provider."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "ml_data_provider")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()
        cls.batch_size = DEFAULT_BATCH_SIZE
        cls.price_per_data_batch = DEFAULT_PRICE_PER_DATA_BATCH
        cls.seller_tx_fee = DEFAULT_SELLER_TX_FEE
        cls.buyer_tx_fee = DEFAULT_BUYER_TX_FEE
        cls.currency_id = "some_currency_id"
        cls.ledger_id = DEFAULT_LEDGER
        cls.is_ledger_tx = True
        cls.service_id = DEFAULT_SERVICE_ID
        cls.location = DEFAULT_LOCATION
        cls.personality_data = DEFAULT_PERSONALITY_DATA
        cls.classification = DEFAULT_CLASSIFICATION
        cls.service_data = DEFAULT_SERVICE_DATA
        cls.strategy = Strategy(
            batch_size=cls.batch_size,
            price_per_data_batch=cls.price_per_data_batch,
            seller_tx_fee=cls.seller_tx_fee,
            buyer_tx_fee=cls.buyer_tx_fee,
            ledger_id=cls.ledger_id,
            is_ledger_tx=cls.is_ledger_tx,
            currency_id=cls.currency_id,
            service_id=cls.service_id,
            location=cls.location,
            personality_data=cls.personality_data,
            classification=cls.classification,
            service_data=cls.service_data,
            name="strategy",
            skill_context=cls._skill.skill_context,
        )

    def test_properties(self):
        """Test the properties of Strategy class."""
        assert self.strategy.ledger_id == self.ledger_id
        assert self.strategy.is_ledger_tx == self.is_ledger_tx

    def test_get_location_description(self):
        """Test the get_location_description method of the Strategy class."""
        description = self.strategy.get_location_description()

        assert type(description) == Description
        assert description.data_model is AGENT_LOCATION_MODEL
        assert description.values.get("location", "") == Location(
            latitude=self.location["latitude"], longitude=self.location["longitude"]
        )

    def test_get_register_personality_description(self):
        """Test the get_register_personality_description method of the Strategy class."""
        description = self.strategy.get_register_personality_description()

        assert type(description) == Description
        assert description.data_model is AGENT_PERSONALITY_MODEL
        assert description.values.get("piece", "") == "genus"
        assert description.values.get("value", "") == "data"

    def test_get_register_classification_description(self):
        """Test the get_register_classification_description method of the Strategy class."""
        description = self.strategy.get_register_classification_description()

        assert type(description) == Description
        assert description.data_model is AGENT_PERSONALITY_MODEL
        assert description.values.get("piece", "") == "classification"
        assert description.values.get("value", "") == "seller"

    def test_get_register_service_description(self):
        """Test the get_register_service_description method of the Strategy class."""
        description = self.strategy.get_register_service_description()

        assert type(description) == Description
        assert description.data_model is AGENT_SET_SERVICE_MODEL
        assert description.values.get("key", "") == "dataset_id"
        assert description.values.get("value", "") == "fmnist"

    def test_get_service_description(self):
        """Test the get_service_description method of the Strategy class."""
        description = self.strategy.get_service_description()

        assert type(description) == Description
        assert description.data_model is SIMPLE_DATA_MODEL
        assert description.values.get("dataset_id", "") == "fmnist"

    def test_get_unregister_service_description(self):
        """Test the get_unregister_service_description method of the GenericStrategy class."""
        description = self.strategy.get_unregister_service_description()

        assert type(description) == Description
        assert description.data_model is AGENT_REMOVE_SERVICE_MODEL
        assert description.values.get("key", "") == "dataset_id"

    def test_sample_data(self):
        """Test the sample_data method of the Strategy class."""
        data = self.strategy.sample_data(32)

        assert type(data) == tuple
        assert len(data) == 2
        assert type(data[0]) == np.ndarray
        assert type(data[0]) == np.ndarray

    def test_encode_sample_data(self):
        """Test the encode_sample_data method of the Strategy class."""
        # setup
        data = self.strategy.sample_data(32)

        # operation
        encoded_data = self.strategy.encode_sample_data(data)

        # after
        assert type(encoded_data) == bytes

        # decode it and check identical
        decoded_arrays = json.loads(encoded_data)
        numpy_data_0 = np.asarray(decoded_arrays["data_0"])
        numpy_data_1 = np.asarray(decoded_arrays["data_1"])

        assert (numpy_data_0 == data[0]).all()
        assert (numpy_data_1 == data[1]).all()

    def test_is_matching_supply(self):
        """Test the is_matching_supply method of the Strategy class."""
        acceptable_constraint = Constraint("dataset_id", ConstraintType("==", "fmnist"))
        matching_query = Query([acceptable_constraint])
        is_matching_supply = self.strategy.is_matching_supply(matching_query)
        assert is_matching_supply

        unacceptable_constraint = Constraint(
            "dataset_id", ConstraintType("==", "some_other_service")
        )
        unmatching_query = Query([unacceptable_constraint])
        is_matching_supply = self.strategy.is_matching_supply(unmatching_query)
        assert not is_matching_supply

    def test_generate_terms(self):
        """Test the generate_terms method of the Strategy class."""
        # setup
        mocked_nonce = "some_nonce"
        expected_proposal = Description(
            {
                "batch_size": self.batch_size,
                "price": self.price_per_data_batch,
                "seller_tx_fee": self.seller_tx_fee,
                "buyer_tx_fee": self.buyer_tx_fee,
                "currency_id": self.currency_id,
                "ledger_id": self.ledger_id,
                "address": self.skill.skill_context.agent_address,
                "service_id": self.service_id,
                "nonce": mocked_nonce,
            }
        )

        # operation
        with patch(
            "uuid.UUID.hex", new_callable=PropertyMock, return_value=mocked_nonce
        ) as mocked_uuid:
            proposal = self.strategy.generate_terms()

        # after
        mocked_uuid.assert_called_once()
        assert proposal == expected_proposal

    def test_is_valid_terms_i(self):
        """Test the is_valid_terms method of the Strategy class where terms is VALID."""
        # setup
        valid_proposal = Description(
            {
                "batch_size": self.batch_size,
                "price": self.price_per_data_batch,
                "seller_tx_fee": self.seller_tx_fee,
                "buyer_tx_fee": self.buyer_tx_fee,
                "currency_id": self.currency_id,
                "ledger_id": self.ledger_id,
                "address": self.skill.skill_context.agent_address,
                "service_id": self.service_id,
                "nonce": "some_nonce",
            }
        )

        # operation
        is_valid = self.strategy.is_valid_terms(valid_proposal)

        # after
        assert is_valid is True

    def test_is_valid_terms_ii(self):
        """Test the is_valid_terms method of the Strategy class where terms is INVALID."""
        # setup
        invalid_batch_size = 0
        valid_proposal = Description(
            {
                "batch_size": invalid_batch_size,
                "price": self.price_per_data_batch,
                "seller_tx_fee": self.seller_tx_fee,
                "buyer_tx_fee": self.buyer_tx_fee,
                "currency_id": self.currency_id,
                "ledger_id": self.ledger_id,
                "address": self.skill.skill_context.agent_address,
                "service_id": self.service_id,
                "nonce": "some_nonce",
            }
        )

        # operation
        is_valid = self.strategy.is_valid_terms(valid_proposal)

        # after
        assert is_valid is False
