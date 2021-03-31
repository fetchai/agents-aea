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

import json
import uuid
from typing import Any, Tuple

import numpy as np

from aea.exceptions import enforce
from aea.helpers.search.generic import (
    AGENT_LOCATION_MODEL,
    AGENT_PERSONALITY_MODEL,
    AGENT_REMOVE_SERVICE_MODEL,
    AGENT_SET_SERVICE_MODEL,
    SIMPLE_DATA_MODEL,
)
from aea.helpers.search.models import Description, Location, Query
from aea.skills.base import Model


DEFAULT_PRICE_PER_DATA_BATCH = 10
DEFAULT_BATCH_SIZE = 32
DEFAULT_SELLER_TX_FEE = 0
DEFAULT_BUYER_TX_FEE = 0
DEFAULT_SERVICE_ID = "data_service"

DEFAULT_LOCATION = {"longitude": 0.1270, "latitude": 51.5194}
DEFAULT_PERSONALITY_DATA = {"piece": "genus", "value": "data"}
DEFAULT_SERVICE_DATA = {"key": "dataset_id", "value": "fmnist"}
DEFAULT_CLASSIFICATION = {"piece": "classification", "value": "seller"}


class NumpyArrayEncoder(json.JSONEncoder):
    """This class defines a custom JSON encoder for numpy ndarray objects."""

    def default(self, obj: Any) -> Any:  # pylint: disable=arguments-differ
        """Encode an object (including a numpy ndarray) into its JSON representation."""
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)  # pragma: nocover


class Strategy(Model):
    """This class defines a strategy for the agent."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the strategy of the agent."""
        self.price_per_data_batch = kwargs.pop(
            "price_per_data_batch", DEFAULT_PRICE_PER_DATA_BATCH
        )
        self.batch_size = kwargs.pop("batch_size", DEFAULT_BATCH_SIZE)
        self.seller_tx_fee = kwargs.pop("seller_tx_fee", DEFAULT_SELLER_TX_FEE)
        self.buyer_tx_fee = kwargs.pop("buyer_tx_fee", DEFAULT_BUYER_TX_FEE)
        currency_id = kwargs.pop("currency_id", None)
        ledger_id = kwargs.pop("ledger_id", None)
        self._is_ledger_tx = kwargs.pop("is_ledger_tx", False)
        self._service_id = kwargs.pop("service_id", DEFAULT_SERVICE_ID)

        location = kwargs.pop("location", DEFAULT_LOCATION)
        self._agent_location = {
            "location": Location(
                latitude=location["latitude"], longitude=location["longitude"]
            )
        }
        self._set_personality_data = kwargs.pop(
            "personality_data", DEFAULT_PERSONALITY_DATA
        )
        enforce(
            len(self._set_personality_data) == 2
            and "piece" in self._set_personality_data
            and "value" in self._set_personality_data,
            "personality_data must contain keys `key` and `value`",
        )
        self._set_classification = kwargs.pop("classification", DEFAULT_CLASSIFICATION)
        enforce(
            len(self._set_classification) == 2
            and "piece" in self._set_classification
            and "value" in self._set_classification,
            "classification must contain keys `key` and `value`",
        )
        self._set_service_data = kwargs.pop("service_data", DEFAULT_SERVICE_DATA)
        enforce(
            len(self._set_service_data) == 2
            and "key" in self._set_service_data
            and "value" in self._set_service_data,
            "service_data must contain keys `key` and `value`",
        )
        self._remove_service_data = {"key": self._set_service_data["key"]}
        self._simple_service_data = {
            self._set_service_data["key"]: self._set_service_data["value"]
        }

        super().__init__(**kwargs)
        self._ledger_id = (
            ledger_id if ledger_id is not None else self.context.default_ledger_id
        )
        if currency_id is None:
            currency_id = self.context.currency_denominations.get(self._ledger_id, None)
            enforce(
                currency_id is not None,
                f"Currency denomination for ledger_id={self._ledger_id} not specified.",
            )
        self._currency_id = currency_id
        # loading ML dataset
        # (this could be parametrized)
        from tensorflow import keras  # pylint: disable=import-outside-toplevel

        (
            (self.train_x, self.train_y),
            (self.test_x, self.test_y),
        ) = keras.datasets.fashion_mnist.load_data()

    @property
    def ledger_id(self) -> str:
        """Get the ledger id."""
        return self._ledger_id

    @property
    def is_ledger_tx(self) -> str:
        """Get the is_ledger_tx."""
        return self._is_ledger_tx

    def get_location_description(self) -> Description:
        """
        Get the location description.

        :return: a description of the agent's location
        """
        description = Description(
            self._agent_location, data_model=AGENT_LOCATION_MODEL,
        )
        return description

    def get_register_personality_description(self) -> Description:
        """
        Get the register personality description.

        :return: a description of the personality
        """
        description = Description(
            self._set_personality_data, data_model=AGENT_PERSONALITY_MODEL,
        )
        return description

    def get_register_classification_description(self) -> Description:
        """
        Get the register classification description.

        :return: a description of the classification
        """
        description = Description(
            self._set_classification, data_model=AGENT_PERSONALITY_MODEL,
        )
        return description

    def get_register_service_description(self) -> Description:
        """
        Get the register service description.

        :return: a description of the offered services
        """
        description = Description(
            self._set_service_data, data_model=AGENT_SET_SERVICE_MODEL,
        )
        return description

    def get_service_description(self) -> Description:
        """
        Get the simple service description.

        :return: a description of the offered services
        """
        description = Description(
            self._simple_service_data, data_model=SIMPLE_DATA_MODEL,
        )
        return description

    def get_unregister_service_description(self) -> Description:
        """
        Get the unregister service description.

        :return: a description of the to be removed service
        """
        description = Description(
            self._remove_service_data, data_model=AGENT_REMOVE_SERVICE_MODEL,
        )
        return description

    def sample_data(self, n: int) -> Tuple:
        """Sample N rows from data."""
        idx = np.arange(self.train_x.shape[0])
        mask = np.zeros_like(idx, dtype=bool)

        selected = np.random.choice(idx, n, replace=False)
        mask[selected] = True

        x_sample = self.train_x[mask]
        y_sample = self.train_y[mask]
        return x_sample, y_sample

    @staticmethod
    def encode_sample_data(data: Tuple) -> bytes:
        """Serialize data (a tuple of two numpy ndarrays) into bytes."""
        data_dict = {
            "data_0": data[0],
            "data_1": data[1],
        }
        return json.dumps(data_dict, cls=NumpyArrayEncoder).encode("utf-8")

    def is_matching_supply(self, query: Query) -> bool:
        """
        Check if the query matches the supply.

        :param query: the query
        :return: bool indicating whether matches or not
        """
        service_desc = self.get_service_description()
        return query.check(service_desc)

    def generate_terms(self) -> Description:
        """
        Generate a proposal.

        :return: a tuple of proposal and the weather data
        """
        address = self.context.agent_addresses[self.ledger_id]
        proposal = Description(
            {
                "batch_size": self.batch_size,
                "price": self.price_per_data_batch,
                "seller_tx_fee": self.seller_tx_fee,
                "buyer_tx_fee": self.buyer_tx_fee,
                "currency_id": self._currency_id,
                "ledger_id": self.ledger_id,
                "address": address,
                "service_id": self._service_id,
                "nonce": uuid.uuid4().hex,
            }
        )
        return proposal

    def is_valid_terms(self, terms: Description) -> bool:
        """
        Check the terms are valid.

        :param terms: the terms
        :return: boolean
        """
        generated_terms = self.generate_terms()
        return all(
            [
                terms.values[key] == generated_terms.values[key]
                for key in [
                    "batch_size",
                    "price",
                    "seller_tx_fee",
                    "buyer_tx_fee",
                    "currency_id",
                    "ledger_id",
                    "address",
                    "service_id",
                ]
            ]
        )
