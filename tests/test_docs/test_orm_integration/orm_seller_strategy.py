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
import random
import time
from typing import Any, Dict, List, Optional, Tuple

import sqlalchemy as db

from aea.helpers.search.generic import GenericDataModel
from aea.helpers.search.models import Description, Query
from aea.mail.base import Address
from aea.skills.base import Model

DEFAULT_SELLER_TX_FEE = 0
DEFAULT_TOTAL_PRICE = 10
DEFAULT_CURRENCY_PBK = "FET"
DEFAULT_LEDGER_ID = "fetchai"
DEFAULT_HAS_DATA_SOURCE = False
DEFAULT_DATA_FOR_SALE = {}  # type: Optional[Dict[str, Any]]
DEFAULT_IS_LEDGER_TX = True
DEFAULT_DATA_MODEL_NAME = "location"
DEFAULT_DATA_MODEL = {
    "attribute_one": {"name": "country", "type": "str", "is_required": True},
    "attribute_two": {"name": "city", "type": "str", "is_required": True},
}  # type: Optional[Dict[str, Any]]
DEFAULT_SERVICE_DATA = {"country": "UK", "city": "Cambridge"}


class Strategy(Model):
    """This class defines a strategy for the agent."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize the strategy of the agent.

        :param register_as: determines whether the agent registers as seller, buyer or both
        :param search_for: determines whether the agent searches for sellers, buyers or both

        :return: None
        """
        self._seller_tx_fee = kwargs.pop("seller_tx_fee", DEFAULT_SELLER_TX_FEE)
        self._currency_id = kwargs.pop("currency_id", DEFAULT_CURRENCY_PBK)
        self._ledger_id = kwargs.pop("ledger_id", DEFAULT_LEDGER_ID)
        self.is_ledger_tx = kwargs.pop("is_ledger_tx", DEFAULT_IS_LEDGER_TX)
        self._total_price = kwargs.pop("total_price", DEFAULT_TOTAL_PRICE)
        self._has_data_source = kwargs.pop("has_data_source", DEFAULT_HAS_DATA_SOURCE)
        self._service_data = kwargs.pop("service_data", DEFAULT_SERVICE_DATA)
        self._data_model = kwargs.pop("data_model", DEFAULT_DATA_MODEL)
        self._data_model_name = kwargs.pop("data_model_name", DEFAULT_DATA_MODEL_NAME)
        data_for_sale = kwargs.pop("data_for_sale", DEFAULT_DATA_FOR_SALE)

        super().__init__(**kwargs)

        self._oef_msg_id = 0
        self._db_engine = db.create_engine("sqlite:///genericdb.db")
        self._tbl = self.create_database_and_table()
        self.insert_data()

        # Read the data from the sensor if the bool is set to True.
        # Enables us to let the user implement his data collection logic without major changes.
        if self._has_data_source:
            self._data_for_sale = self.collect_from_data_source()
        else:
            self._data_for_sale = data_for_sale

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
        desc = Description(
            self._service_data,
            data_model=GenericDataModel(self._data_model_name, self._data_model),
        )
        return desc

    def is_matching_supply(self, query: Query) -> bool:
        """
        Check if the query matches the supply.

        :param query: the query
        :return: bool indiciating whether matches or not
        """
        # TODO, this is a stub
        return True

    def generate_proposal_and_data(
        self, query: Query, counterparty: Address
    ) -> Tuple[Description, Dict[str, List[Dict[str, Any]]]]:
        """
        Generate a proposal matching the query.

        :param counterparty: the counterparty of the proposal.
        :param query: the query
        :return: a tuple of proposal and the weather data
        """
        tx_nonce = self.context.ledger_apis.generate_tx_nonce(
            identifier=self._ledger_id,
            seller=self.context.agent_addresses[self._ledger_id],
            client=counterparty,
        )
        assert (
            self._total_price - self._seller_tx_fee > 0
        ), "This sale would generate a loss, change the configs!"
        proposal = Description(
            {
                "price": self._total_price,
                "seller_tx_fee": self._seller_tx_fee,
                "currency_id": self._currency_id,
                "ledger_id": self._ledger_id,
                "tx_nonce": tx_nonce if tx_nonce is not None else "",
            }
        )
        return proposal, self._data_for_sale

    def collect_from_data_source(self) -> Dict[str, Any]:
        """Implement the logic to collect data."""
        connection = self._db_engine.connect()
        query = db.select([self._tbl])
        result_proxy = connection.execute(query)
        data_points = result_proxy.fetchall()
        return {"data": json.dumps(list(map(tuple, data_points)))}

    def create_database_and_table(self):
        """Creates a database and a table to store the data if not exists."""
        metadata = db.MetaData()

        tbl = db.Table(
            "data",
            metadata,
            db.Column("timestamp", db.Integer()),
            db.Column("temprature", db.String(255), nullable=False),
        )
        metadata.create_all(self._db_engine)
        return tbl

    def insert_data(self):
        """Insert data in the database."""
        connection = self._db_engine.connect()
        self.context.logger.info("Populating the database...")
        for _ in range(10):
            query = db.insert(self._tbl).values(  # nosec
                timestamp=time.time(), temprature=str(random.randrange(10, 25))
            )
            connection.execute(query)
