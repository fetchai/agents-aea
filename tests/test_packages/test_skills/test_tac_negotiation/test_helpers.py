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
"""This module contains the tests of the helpers module of the tac negotiation."""

from pathlib import Path

from aea.helpers.search.models import (
    Attribute,
    Constraint,
    ConstraintType,
    DataModel,
    Description,
)
from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.skills.tac_negotiation.helpers import (
    DEMAND_DATAMODEL_NAME,
    SUPPLY_DATAMODEL_NAME,
    _build_goods_datamodel,
    build_goods_description,
    build_goods_query,
)

from tests.conftest import ROOT_DIR


class TestHelpers(BaseSkillTestCase):
    """Test Helper module methods of tac control."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "tac_negotiation")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()

    def test_build_goods_datamodel_supply(self):
        """Test the _build_goods_datamodel of Helpers module for a supply."""
        good_ids = ["1", "2"]
        is_supply = True
        attributes = [
            Attribute("1", int, True, "A good on offer."),
            Attribute("2", int, True, "A good on offer."),
            Attribute("ledger_id", str, True, "The ledger for transacting."),
            Attribute(
                "currency_id",
                str,
                True,
                "The currency for pricing and transacting the goods.",
            ),
            Attribute("price", int, False, "The price of the goods in the currency."),
            Attribute(
                "fee",
                int,
                False,
                "The transaction fee payable by the buyer in the currency.",
            ),
            Attribute(
                "nonce", str, False, "The nonce to distinguish identical descriptions."
            ),
        ]
        expected_data_model = DataModel(SUPPLY_DATAMODEL_NAME, attributes)
        actual_data_model = _build_goods_datamodel(good_ids, is_supply)
        assert actual_data_model == expected_data_model

    def test_build_goods_datamodel_demand(self):
        """Test the _build_goods_datamodel of Helpers module for a demand."""
        good_ids = ["1", "2"]
        is_supply = False
        attributes = [
            Attribute("1", int, True, "A good on offer."),
            Attribute("2", int, True, "A good on offer."),
            Attribute("ledger_id", str, True, "The ledger for transacting."),
            Attribute(
                "currency_id",
                str,
                True,
                "The currency for pricing and transacting the goods.",
            ),
            Attribute("price", int, False, "The price of the goods in the currency."),
            Attribute(
                "fee",
                int,
                False,
                "The transaction fee payable by the buyer in the currency.",
            ),
            Attribute(
                "nonce", str, False, "The nonce to distinguish identical descriptions."
            ),
        ]
        expected_data_model = DataModel(DEMAND_DATAMODEL_NAME, attributes)
        actual_data_model = _build_goods_datamodel(good_ids, is_supply)
        assert actual_data_model == expected_data_model

    def test_build_goods_description_supply(self):
        """Test the build_goods_description of Helpers module for supply."""
        quantities_by_good_id = {"2": 5, "3": 10}
        currency_id = "1"
        ledger_id = "some_ledger_id"
        is_supply = True

        attributes = [
            Attribute("2", int, True, "A good on offer."),
            Attribute("3", int, True, "A good on offer."),
            Attribute("ledger_id", str, True, "The ledger for transacting."),
            Attribute(
                "currency_id",
                str,
                True,
                "The currency for pricing and transacting the goods.",
            ),
            Attribute("price", int, False, "The price of the goods in the currency."),
            Attribute(
                "fee",
                int,
                False,
                "The transaction fee payable by the buyer in the currency.",
            ),
            Attribute(
                "nonce", str, False, "The nonce to distinguish identical descriptions."
            ),
        ]
        expected_data_model = DataModel(SUPPLY_DATAMODEL_NAME, attributes)
        expected_values = {"currency_id": currency_id, "ledger_id": ledger_id}
        expected_values.update(quantities_by_good_id)
        expected_description = Description(expected_values, expected_data_model)

        actual_description = build_goods_description(
            quantities_by_good_id, currency_id, ledger_id, is_supply
        )
        assert actual_description == expected_description

    def test_build_goods_description_demand(self):
        """Test the build_goods_description of Helpers module for demand (same as above)."""
        quantities_by_good_id = {"2": 5, "3": 10}
        currency_id = "1"
        ledger_id = "some_ledger_id"
        is_supply = False

        attributes = [
            Attribute("2", int, True, "A good on offer."),
            Attribute("3", int, True, "A good on offer."),
            Attribute("ledger_id", str, True, "The ledger for transacting."),
            Attribute(
                "currency_id",
                str,
                True,
                "The currency for pricing and transacting the goods.",
            ),
            Attribute("price", int, False, "The price of the goods in the currency."),
            Attribute(
                "fee",
                int,
                False,
                "The transaction fee payable by the buyer in the currency.",
            ),
            Attribute(
                "nonce", str, False, "The nonce to distinguish identical descriptions."
            ),
        ]
        expected_data_model = DataModel(DEMAND_DATAMODEL_NAME, attributes)
        expected_values = {"currency_id": currency_id, "ledger_id": ledger_id}
        expected_values.update(quantities_by_good_id)
        expected_description = Description(expected_values, expected_data_model)

        actual_description = build_goods_description(
            quantities_by_good_id, currency_id, ledger_id, is_supply
        )
        assert actual_description == expected_description

    def test_build_goods_query(self):
        """Test the build_goods_query of Helpers module."""
        good_ids = ["2", "3"]
        currency_id = "1"
        ledger_id = "some_ledger_id"
        is_searching_for_sellers = True

        attributes = [
            Attribute("2", int, True, "A good on offer."),
            Attribute("3", int, True, "A good on offer."),
            Attribute("ledger_id", str, True, "The ledger for transacting."),
            Attribute(
                "currency_id",
                str,
                True,
                "The currency for pricing and transacting the goods.",
            ),
            Attribute("price", int, False, "The price of the goods in the currency."),
            Attribute(
                "fee",
                int,
                False,
                "The transaction fee payable by the buyer in the currency.",
            ),
            Attribute(
                "nonce", str, False, "The nonce to distinguish identical descriptions."
            ),
        ]
        expected_data_model = DataModel(SUPPLY_DATAMODEL_NAME, attributes)

        expected_constraints = [
            Constraint("2", ConstraintType(">=", 1)),
            Constraint("3", ConstraintType(">=", 1)),
            Constraint("ledger_id", ConstraintType("==", ledger_id)),
            Constraint("currency_id", ConstraintType("==", currency_id)),
        ]

        actual_query = build_goods_query(
            good_ids, currency_id, ledger_id, is_searching_for_sellers
        )

        constraints = [
            (c.constraint_type.type, c.constraint_type.value)
            for c in actual_query.constraints[0].constraints
        ]
        for constraint in expected_constraints:
            assert (
                constraint.constraint_type.type,
                constraint.constraint_type.value,
            ) in constraints
        assert actual_query.model == expected_data_model

    def test_build_goods_query_1_good(self):
        """Test the build_goods_query of Helpers module where there is 1 good."""
        good_ids = ["2"]
        currency_id = "1"
        ledger_id = "some_ledger_id"
        is_searching_for_sellers = True

        attributes = [
            Attribute("2", int, True, "A good on offer."),
            Attribute("ledger_id", str, True, "The ledger for transacting."),
            Attribute(
                "currency_id",
                str,
                True,
                "The currency for pricing and transacting the goods.",
            ),
            Attribute("price", int, False, "The price of the goods in the currency."),
            Attribute(
                "fee",
                int,
                False,
                "The transaction fee payable by the buyer in the currency.",
            ),
            Attribute(
                "nonce", str, False, "The nonce to distinguish identical descriptions."
            ),
        ]
        expected_data_model = DataModel(SUPPLY_DATAMODEL_NAME, attributes)

        expected_constraints = [
            Constraint("2", ConstraintType(">=", 1)),
            Constraint("ledger_id", ConstraintType("==", ledger_id)),
            Constraint("currency_id", ConstraintType("==", currency_id)),
        ]

        actual_query = build_goods_query(
            good_ids, currency_id, ledger_id, is_searching_for_sellers
        )

        for constraint in expected_constraints:
            assert constraint in actual_query.constraints
        assert actual_query.model == expected_data_model
