# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2020 Fetch.AI Limited
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

"""This module contains the tests for the preference representations helper module."""

from aea.helpers.preference_representations.base import (
    linear_utility,
    logarithmic_utility,
)


def test_logarithmic_utility():
    """Test logarithmic utlity."""
    assert (
        logarithmic_utility(
            utility_params_by_good_id={"good_1": 0.2, "good_2": 0.8},
            quantities_by_good_id={"good_1": 2, "good_2": 1},
        )
        > 0
    ), "Utility should be positive."


def test_linear_utility():
    """Test logarithmic utlity."""
    assert (
        linear_utility(
            exchange_params_by_currency_id={"cur_1": 0.2, "cur_2": 0.8},
            balance_by_currency_id={"cur_1": 20, "cur_2": 100},
        )
        > 0
    ), "Utility should be positive."
