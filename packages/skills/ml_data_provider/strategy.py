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

"""This module contains the strategy class."""

import numpy as np
from tensorflow import keras

from aea.cli import cli
from aea.protocols.oef.models import Attribute, DataModel, Description, Query
from aea.skills.base import SharedClass
from tests.common.click_testing import CliRunner

DEFAULT_PRICE_PER_DATA_BATCH = 10
DEFAULT_DATASET_ID = "fmnist"
DEFAULT_BATCH_SIZE = 32
DEFAULT_SELLER_TX_FEE = 0
DEFAULT_BUYER_TX_FEE = 0
DEFAULT_CURRENCY_PBK = 'FET'
DEFAULT_LEDGER_ID = 'fetchai'

CLI_LOG_OPTION = ["-v", "OFF"]


class Strategy(SharedClass):
    """This class defines a strategy for the agent."""

    def __init__(self, **kwargs) -> None:
        """Initialize the strategy of the agent."""
        self.runner = CliRunner()

        self.runner.invoke(cli, [*CLI_LOG_OPTION, "config", "set",
                                 "skills.ml_data_provider.shared_classes.strategy.args.price_per_data_batch",
                                 DEFAULT_PRICE_PER_DATA_BATCH], standalone_mode=False)

        self.runner.invoke(cli, [*CLI_LOG_OPTION, "config", "set",
                                 "skills.ml_data_provider.shared_classes.strategy.args.batch_size",
                                 DEFAULT_BATCH_SIZE], standalone_mode=False)

        self.runner.invoke(cli, [*CLI_LOG_OPTION, "config", "set",
                                 "skills.ml_data_provider.shared_classes.strategy.args.dataset_id",
                                 DEFAULT_DATASET_ID], standalone_mode=False)

        self.runner.invoke(cli, [*CLI_LOG_OPTION, "config", "set",
                                 "skills.ml_data_provider.shared_classes.strategy.args.seller_tx_fee",
                                 DEFAULT_SELLER_TX_FEE], standalone_mode=False)

        self.runner.invoke(cli, [*CLI_LOG_OPTION, "config", "set",
                                 "skills.ml_data_provider.shared_classes.strategy.args.buyer_tx_fee",
                                 DEFAULT_BUYER_TX_FEE], standalone_mode=False)

        self.runner.invoke(cli, [*CLI_LOG_OPTION, "config", "set",
                                 "skills.ml_data_provider.shared_classes.strategy.args.currency_id",
                                 DEFAULT_CURRENCY_PBK], standalone_mode=False)

        self.runner.invoke(cli, [*CLI_LOG_OPTION, "config", "set",
                                 "skills.ml_data_provider.shared_classes.strategy.args.ledger_id",
                                 DEFAULT_LEDGER_ID], standalone_mode=False)

        super().__init__(**kwargs)
        self._oef_msg_id = 0

        # loading ML dataset
        # TODO this should be parametrized
        (self.train_x, self.train_y), (self.test_x, self.test_y) = keras.datasets.fashion_mnist.load_data()

    def get_next_oef_msg_id(self) -> int:
        """
        Get the next oef msg id.

        :return: the next oef msg id
        """
        self._oef_msg_id += 1
        return self._oef_msg_id

    def get_service_description(self) -> Description:
        """
        Get the service description.

        :return: a description of the offered services
        """
        dm = DataModel("ml_datamodel", [Attribute("dataset_id", str, True)])
        desc = Description({'dataset_id': DEFAULT_DATASET_ID}, data_model=dm)
        return desc

    def sample_data(self, n: int):
        """Sample N rows from data."""
        idx = np.arange(self.train_x.shape[0])
        mask = np.zeros_like(idx, dtype=bool)

        selected = np.random.choice(idx, n, replace=False)
        mask[selected] = True

        x_sample = self.train_x[mask]
        y_sample = self.train_y[mask]
        return x_sample, y_sample

    def is_matching_supply(self, query: Query) -> bool:
        """
        Check if the query matches the supply.

        :param query: the query
        :return: bool indiciating whether matches or not
        """
        service_desc = self.get_service_description()
        return query.check(service_desc)

    def generate_terms(self) -> Description:
        """
        Generate a proposal.

        :return: a tuple of proposal and the weather data
        """
        address = self.context.agent_addresses[DEFAULT_LEDGER_ID]
        proposal = Description({"batch_size": DEFAULT_BATCH_SIZE,
                                "price": DEFAULT_PRICE_PER_DATA_BATCH,
                                "seller_tx_fee": DEFAULT_SELLER_TX_FEE,
                                "buyer_tx_fee": DEFAULT_BUYER_TX_FEE,
                                "currency_id": DEFAULT_CURRENCY_PBK,
                                "ledger_id": DEFAULT_LEDGER_ID,
                                "address": address})
        return proposal

    def is_valid_terms(self, terms: Description) -> bool:
        """
        Check the terms are valid.

        :param terms: the terms
        :return: boolean
        """
        return terms == self.generate_terms()
