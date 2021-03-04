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

"""This module contains tests for decision_maker."""

import copy

import pytest
from aea_ledger_ethereum import EthereumCrypto

from aea.decision_maker.gop import OwnershipState, Preferences
from aea.helpers.transaction.base import Terms


def test_preferences_properties():
    """Test the properties of the preferences class."""
    preferences = Preferences()
    with pytest.raises(ValueError):
        preferences.exchange_params_by_currency_id
    with pytest.raises(ValueError):
        preferences.utility_params_by_good_id


def test_preferences_init():
    """Test the preferences init()."""
    utility_params = {"good_id": 20.0}
    exchange_params = {"FET": 10.0}
    preferences = Preferences()
    preferences.set(
        exchange_params_by_currency_id=exchange_params,
        utility_params_by_good_id=utility_params,
    )
    assert preferences.utility_params_by_good_id is not None
    assert preferences.exchange_params_by_currency_id is not None
    assert preferences.is_initialized
    copied_preferences = copy.copy(preferences)
    assert (
        preferences.exchange_params_by_currency_id
        == copied_preferences.exchange_params_by_currency_id
    )
    assert (
        preferences.utility_params_by_good_id
        == copied_preferences.utility_params_by_good_id
    )


def test_logarithmic_utility():
    """Calculate the logarithmic utility and checks that it is not none.."""
    utility_params = {"good_id": 20.0}
    exchange_params = {"FET": 10.0}
    good_holdings = {"good_id": 2}
    preferences = Preferences()
    preferences.set(
        utility_params_by_good_id=utility_params,
        exchange_params_by_currency_id=exchange_params,
    )
    log_utility = preferences.logarithmic_utility(quantities_by_good_id=good_holdings)
    assert log_utility is not None, "Log_utility must not be none."


def test_linear_utility():
    """Calculate the linear_utility and checks that it is not none."""
    currency_holdings = {"FET": 100}
    utility_params = {"good_id": 20.0}
    exchange_params = {"FET": 10.0}
    preferences = Preferences()
    preferences.set(
        utility_params_by_good_id=utility_params,
        exchange_params_by_currency_id=exchange_params,
    )
    linear_utility = preferences.linear_utility(amount_by_currency_id=currency_holdings)
    assert linear_utility is not None, "Linear utility must not be none."


def test_utility():
    """Calculate the score."""
    utility_params = {"good_id": 20.0}
    exchange_params = {"FET": 10.0}
    currency_holdings = {"FET": 100}
    good_holdings = {"good_id": 2}
    preferences = Preferences()
    preferences.set(
        utility_params_by_good_id=utility_params,
        exchange_params_by_currency_id=exchange_params,
    )
    score = preferences.utility(
        quantities_by_good_id=good_holdings, amount_by_currency_id=currency_holdings,
    )
    linear_utility = preferences.linear_utility(amount_by_currency_id=currency_holdings)
    log_utility = preferences.logarithmic_utility(quantities_by_good_id=good_holdings)
    assert (
        score == log_utility + linear_utility
    ), "The score must be equal to the sum of log_utility and linear_utility."


def test_marginal_utility():
    """Test the marginal utility."""
    currency_holdings = {"FET": 100}
    utility_params = {"good_id": 20.0}
    exchange_params = {"FET": 10.0}
    good_holdings = {"good_id": 2}
    preferences = Preferences()
    preferences.set(
        utility_params_by_good_id=utility_params,
        exchange_params_by_currency_id=exchange_params,
    )
    delta_good_holdings = {"good_id": 1}
    delta_currency_holdings = {"FET": -5}
    ownership_state = OwnershipState()
    ownership_state.set(
        amount_by_currency_id=currency_holdings, quantities_by_good_id=good_holdings,
    )
    marginal_utility = preferences.marginal_utility(
        ownership_state=ownership_state,
        delta_quantities_by_good_id=delta_good_holdings,
        delta_amount_by_currency_id=delta_currency_holdings,
    )
    assert marginal_utility is not None, "Marginal utility must not be none."


def test_score_diff_from_transaction():
    """Test the difference between the scores."""
    good_holdings = {"good_id": 2}
    currency_holdings = {"FET": 100}
    utility_params = {"good_id": 20.0}
    exchange_params = {"FET": 10.0}
    ownership_state = OwnershipState()
    ownership_state.set(
        amount_by_currency_id=currency_holdings, quantities_by_good_id=good_holdings
    )
    preferences = Preferences()
    preferences.set(
        utility_params_by_good_id=utility_params,
        exchange_params_by_currency_id=exchange_params,
    )
    terms = Terms(
        ledger_id=EthereumCrypto.identifier,
        sender_address="agent_1",
        counterparty_address="pk",
        amount_by_currency_id={"FET": -20},
        is_sender_payable_tx_fee=True,
        quantities_by_good_id={"good_id": 10},
        nonce="transaction nonce",
    )
    cur_score = preferences.utility(
        quantities_by_good_id=good_holdings, amount_by_currency_id=currency_holdings
    )
    new_state = ownership_state.apply_transactions([terms])
    new_score = preferences.utility(
        quantities_by_good_id=new_state.quantities_by_good_id,
        amount_by_currency_id=new_state.amount_by_currency_id,
    )
    diff_scores = new_score - cur_score
    score_difference = preferences.utility_diff_from_transaction(
        ownership_state=ownership_state, terms=terms
    )
    assert (
        score_difference == diff_scores
    ), "The calculated difference must be equal to the return difference from the function."
    assert not preferences.is_utility_enhancing(
        ownership_state=ownership_state, terms=terms
    ), "Should not enhance utility."


def test_is_utility_enhancing_uninitialized():
    """Test is_utility_enhancing when the states are uninitialized."""
    ownership_state = OwnershipState()
    preferences = Preferences()
    terms = Terms(
        ledger_id=EthereumCrypto.identifier,
        sender_address="agent_1",
        counterparty_address="pk",
        amount_by_currency_id={"FET": -20},
        is_sender_payable_tx_fee=True,
        quantities_by_good_id={"good_id": 10},
        nonce="transaction nonce",
    )
    assert preferences.is_utility_enhancing(
        ownership_state=ownership_state, terms=terms
    ), "Should enhance utility."
