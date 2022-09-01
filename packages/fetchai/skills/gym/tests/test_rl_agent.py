# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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
"""This module contains the tests for the rl_agent module of the gym skill."""
# pylint: skip-file

import copy
from unittest.mock import patch

from packages.fetchai.skills.gym.helpers import ProxyEnv
from packages.fetchai.skills.gym.rl_agent import GoodPriceModel
from packages.fetchai.skills.gym.tests.intermediate_class import GymTestCase


class TestPriceBandit(GymTestCase):
    """Test PriceBandit of gym."""

    def test_sample(self):
        """Test the sample method of PriceBandit class."""
        sample = self.price_bandit.sample()
        assert type(sample) == int

    def test_update(self):
        """Test the update method of the PriceBandit class."""
        # before
        assert self.price_bandit.beta_a == self.mocked_beta_a
        assert self.price_bandit.beta_b == self.mocked_beta_b

        # operation
        self.price_bandit.update(True)

        # after & before
        assert self.price_bandit.beta_a == self.mocked_beta_a + 1
        assert self.price_bandit.beta_b == self.mocked_beta_b

        # operation
        self.price_bandit.update(False)

        # after
        assert self.price_bandit.beta_a == self.mocked_beta_a + 1
        assert self.price_bandit.beta_b == self.mocked_beta_b + 1


class TestGoodPriceModel(GymTestCase):
    """Test GoodPriceModel of gym."""

    def test_update_i(self):
        """Test the update method of the GoodPriceModel class where outcome is True."""
        # setup
        outcome = True
        mocked_price = 46
        before_prices = copy.deepcopy(self.good_price_model.price_bandits)

        # operation
        self.good_price_model.update(outcome, mocked_price)

        # after
        assert (
            self.good_price_model.price_bandits[mocked_price].beta_a
            != before_prices[mocked_price].beta_a
            and self.good_price_model.price_bandits[mocked_price].beta_b
            == before_prices[mocked_price].beta_b
        )
        for price in range(self.mocked_bound + 1):
            if price != mocked_price:
                assert (
                    self.good_price_model.price_bandits[price].beta_a
                    == before_prices[price].beta_a
                    and self.good_price_model.price_bandits[price].beta_b
                    == before_prices[price].beta_b
                )

    def test_update_ii(self):
        """Test the update method of the GoodPriceModel class where outcome is False."""
        # setup
        outcome = False
        mocked_price = 12
        before_prices = copy.deepcopy(self.good_price_model.price_bandits)

        # operation
        self.good_price_model.update(outcome, mocked_price)

        # after
        assert (
            self.good_price_model.price_bandits[mocked_price].beta_a
            == before_prices[mocked_price].beta_a
            and self.good_price_model.price_bandits[mocked_price].beta_b
            != before_prices[mocked_price].beta_b
        )
        for price in range(self.mocked_bound + 1):
            if price != mocked_price:
                assert (
                    self.good_price_model.price_bandits[price].beta_a
                    == before_prices[price].beta_a
                    and self.good_price_model.price_bandits[price].beta_b
                    == before_prices[price].beta_b
                )

    def test_get_price_expectation(self):
        """Test the get_price_expectation method of GoodPriceModel class."""
        expectation = self.good_price_model.get_price_expectation()
        assert type(expectation) == int


class TestMyRLAgent(GymTestCase):
    """Test MyRLAgent of gym."""

    def test_fit(self):
        """Test the fit method of the MyRLAgent class."""
        # setup
        step_result = ("obs", "reward", "done", "info")

        # operation
        with patch.object(ProxyEnv, "reset") as mocked_reset:
            with patch.object(
                ProxyEnv, "step", return_value=step_result
            ) as mocked_step:
                with patch.object(ProxyEnv, "close") as mocked_close:
                    with patch.object(
                        GoodPriceModel, "get_price_expectation"
                    ) as mocked_price_exp:
                        with patch.object(GoodPriceModel, "update") as mocked_update:
                            with patch.object(self.logger, "log") as mock_logger:
                                self.my_rl_agent.fit(self.proxy_env, self.nb_steps)

        # after
        # fit
        mocked_reset.assert_called_once()

        # _pick_an_action
        mocked_price_exp.assert_called()
        assert mocked_price_exp.call_count == self.nb_steps

        # fit
        mocked_step.assert_called()
        assert mocked_step.call_count == self.nb_steps

        # _update_model
        mocked_update.assert_called()
        assert mocked_update.call_count == self.nb_steps

        # fit
        mock_logger.assert_called()
        mocked_close.assert_called()
