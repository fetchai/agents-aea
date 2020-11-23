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
"""This module contains the tests of the helpers module of the tac control contract skill."""

from pathlib import Path
from unittest.mock import patch

import pytest

from aea.exceptions import AEAEnforceError
from aea.test_tools.test_skill import BaseSkillTestCase

from packages.fetchai.skills.tac_control_contract.helpers import (
    ERC1155Contract,
    _sample_good_instances,
    determine_scaling_factor,
    generate_currency_endowments,
    generate_currency_id_to_name,
    generate_currency_ids,
    generate_equilibrium_prices_and_holdings,
    generate_exchange_params,
    generate_good_endowments,
    generate_good_id_to_name,
    generate_good_ids,
    generate_utility_params,
)

from tests.conftest import ROOT_DIR


class TestHelpers(BaseSkillTestCase):
    """Test Helper module methods of tac control."""

    path_to_skill = Path(ROOT_DIR, "packages", "fetchai", "skills", "tac_control")

    @classmethod
    def setup(cls):
        """Setup the test class."""
        super().setup()

    def test_generate_good_ids_succeeds(self):
        """Test the generate_good_ids of Helpers module which succeeds."""
        expected_list = [1, 2, 3, 4, 5]
        with patch.object(
            ERC1155Contract, "generate_token_ids", return_value=expected_list
        ):
            good_ids = generate_good_ids(5)
        assert good_ids == expected_list

    def test_generate_good_ids_fails(self):
        """Test the generate_good_ids of Helpers module which fails because generate_token_ids generates wrong good ids."""
        expected_list = [1, 2, 3, 4, 5, 6]
        with patch.object(
            ERC1155Contract, "generate_token_ids", return_value=expected_list
        ):
            with pytest.raises(
                AEAEnforceError,
                match="Length of good ids and number of goods must match.",
            ):
                assert generate_good_ids(5)

    def test_generate_currency_ids_succeeds(self):
        """Test the generate_good_ids of Helpers module which succeeds."""
        expected_list = [1, 2, 3, 4, 5]
        with patch.object(
            ERC1155Contract, "generate_token_ids", return_value=expected_list
        ):
            currency_ids = generate_currency_ids(5)
        assert currency_ids == expected_list

    def test_generate_currency_ids_fails(self):
        """Test the generate_good_ids of Helpers module which fails because generate_token_ids generates wrong currency ids."""
        expected_list = [1, 2, 3, 4, 5, 6]
        with patch.object(
            ERC1155Contract, "generate_token_ids", return_value=expected_list
        ):
            with pytest.raises(
                AEAEnforceError,
                match="Length of currency ids and number of currencies must match.",
            ):
                assert generate_currency_ids(5)

    def test_generate_currency_id_to_name(self):
        """Test the generate_currency_id_to_name of Helpers module."""
        expected_currency_id_to_name = {
            "1": "FT_1",
            "3": "FT_3",
            "5": "FT_5",
            "7": "FT_7",
            "9": "FT_9",
        }
        currency_id_to_name = generate_currency_id_to_name([1, 3, 5, 7, 9])
        assert currency_id_to_name == expected_currency_id_to_name

    def test_generate_good_id_to_name(self):
        """Test the generate_good_id_to_name of Helpers module."""
        expected_good_id_to_name = {
            "1": "FT_1",
            "3": "FT_3",
            "5": "FT_5",
            "7": "FT_7",
            "9": "FT_9",
        }
        good_id_to_name = generate_good_id_to_name([1, 3, 5, 7, 9])
        assert good_id_to_name == expected_good_id_to_name

    def test_determine_scaling_factor(self):
        """Test the determine_scaling_factor of Helpers module."""
        money_endowment = 53730411
        scaling_factor = determine_scaling_factor(money_endowment)
        assert scaling_factor == 10000000.0

    def test_generate_good_endowments(self):
        """Test the generate_good_endowments of Helpers module."""
        endowments = generate_good_endowments(
            ["ag_1_add", "ag_2_add"], ["good_id_1", "good_id_2"], 2, 1, 1
        )
        assert "good_id_1" in endowments["ag_1_add"]
        assert "good_id_2" in endowments["ag_1_add"]
        assert "good_id_1" in endowments["ag_2_add"]
        assert "good_id_2" in endowments["ag_2_add"]

    def test_generate_utility_params(self):
        """Test the generate_utility_params of Helpers module."""
        utility_function_params = generate_utility_params(
            ["ag_1_add", "ag_2_add"], ["good_id_1", "good_id_2"], 1000.0
        )
        assert "good_id_1" in utility_function_params["ag_1_add"].keys()
        assert "good_id_2" in utility_function_params["ag_1_add"].keys()
        assert "good_id_1" in utility_function_params["ag_2_add"].keys()
        assert "good_id_2" in utility_function_params["ag_2_add"].keys()

    def test_sample_good_instances(self):
        """Test the _sample_good_instances of Helpers module."""
        nb_instances = _sample_good_instances(2, ["good_id_1", "good_id_2"], 2, 1, 1)
        assert type(nb_instances["good_id_1"]) == int
        assert type(nb_instances["good_id_2"]) == int

    def test_generate_currency_endowments(self):
        """Test the generate_currency_endowments of Helpers module."""
        currency_endowments = generate_currency_endowments(
            ["ag_1_add", "ag_2_add"], ["currency_id_1", "currency_id_2"], 10
        )
        assert "currency_id_1" in currency_endowments["ag_1_add"].keys()
        assert "currency_id_2" in currency_endowments["ag_2_add"].keys()
        assert currency_endowments["ag_1_add"]["currency_id_1"] == 10
        assert currency_endowments["ag_1_add"]["currency_id_2"] == 10

        assert currency_endowments["ag_2_add"]["currency_id_1"] == 10
        assert currency_endowments["ag_2_add"]["currency_id_2"] == 10

    def test_generate_exchange_params(self):
        """Test the generate_exchange_params of Helpers module."""
        currency_endowments = generate_exchange_params(
            ["ag_1_add", "ag_2_add"], ["currency_id_1", "currency_id_2"]
        )
        assert "currency_id_1" in currency_endowments["ag_1_add"].keys()
        assert "currency_id_2" in currency_endowments["ag_2_add"].keys()
        assert currency_endowments["ag_1_add"]["currency_id_1"] == 1.0
        assert currency_endowments["ag_1_add"]["currency_id_2"] == 1.0

        assert currency_endowments["ag_2_add"]["currency_id_1"] == 1.0
        assert currency_endowments["ag_2_add"]["currency_id_2"] == 1.0

    def test_generate_equilibrium_prices_and_holdings(self):
        """Test the generate_equilibrium_prices_and_holdings of Helpers module."""
        (
            eq_prices_dict,
            eq_good_holdings_dict,
            eq_currency_holdings_dict,
        ) = generate_equilibrium_prices_and_holdings(
            {"ag_1": {"good_1": 1}},
            {"ag_1": {"good_1": 1.0}},
            {"ag_1": {"currency_1": 10}},
            {"ag_1": {"currency_1": 1.0}},
            2.0,
        )

        assert len(eq_prices_dict) == 1
        assert type(eq_prices_dict["good_1"]) == float

        assert len(eq_good_holdings_dict) == 1
        assert len(eq_good_holdings_dict["ag_1"]) == 1
        assert type(eq_good_holdings_dict["ag_1"]["good_1"]) == float

        assert len(eq_currency_holdings_dict) == 1
        assert type(eq_currency_holdings_dict["ag_1"]) == float
