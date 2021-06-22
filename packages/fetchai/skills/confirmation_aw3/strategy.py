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

import datetime
import json
import random
from typing import Any, Dict, List, Optional, Tuple, cast

from aea.helpers.search.models import Location

from packages.fetchai.connections.http_client.connection import (
    PUBLIC_ID as HTTP_CLIENT_PUBLIC_ID,
)
from packages.fetchai.protocols.http.message import HttpMessage
from packages.fetchai.skills.confirmation_aw3.dialogues import HttpDialogues
from packages.fetchai.skills.confirmation_aw3.registration_db import RegistrationDB
from packages.fetchai.skills.generic_buyer.strategy import GenericStrategy


class Strategy(GenericStrategy):
    """Strategy class extending Generic Strategy."""

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize the strategy of the agent.

        :param kwargs: keyword arguments
        """
        aw1_aea: Optional[str] = kwargs.pop("aw1_aea", None)
        if aw1_aea is None:
            raise ValueError("aw1_aea must be provided!")
        self.aw1_aea = aw1_aea
        self._locations = kwargs.pop("locations", {})
        if len(self._locations) == 0:
            raise ValueError("locations must have at least one entry")
        _, location = next(iter(self._locations.items()))
        kwargs["location"] = location
        self._search_queries = kwargs.pop("search_queries", {})
        if len(self._search_queries) == 0:
            raise ValueError("search_queries must have at least one entry")
        _, search_query = next(iter(self._search_queries.items()))
        kwargs["search_query"] = search_query
        kwargs["service_id"] = search_query["search_value"]
        leaderboard_url = kwargs.pop("leaderboard_url", None)
        if leaderboard_url is None:
            raise ValueError("No leader board url provided!")
        self.leaderboard_url = f"{leaderboard_url}/insert"
        leaderboard_token = kwargs.pop("leaderboard_token")
        if leaderboard_token is None:
            raise ValueError("No leader board token provided!")
        self.leaderboard_token = leaderboard_token
        super().__init__(**kwargs)

    def get_acceptable_counterparties(
        self, counterparties: Tuple[str, ...]
    ) -> Tuple[str, ...]:
        """
        Process counterparties and drop unacceptable ones.

        :param counterparties: tuple of counterparties
        :return: list of counterparties
        """
        valid_counterparties: List[str] = []
        for counterparty in counterparties:
            if self.is_valid_counterparty(counterparty):
                valid_counterparties.append(counterparty)
        return tuple(valid_counterparties)

    def is_valid_counterparty(self, counterparty: str) -> bool:
        """
        Check if the counterparty is valid.

        :param counterparty: the counterparty
        :return: bool indicating validity
        """
        registration_db = cast(RegistrationDB, self.context.registration_db)
        if not registration_db.is_registered(counterparty):
            self.context.logger.info(
                f"Invalid counterparty={counterparty}, not registered!"
            )
            return False
        return True

    def successful_trade_with_counterparty(
        self, counterparty: str, data: Dict[str, str]
    ) -> None:
        """
        Do something on successful trade.

        :param counterparty: the counterparty address
        :param data: the data
        """
        registration_db = cast(RegistrationDB, self.context.registration_db)
        registration_db.set_trade(counterparty, datetime.datetime.now(), data)
        self.context.logger.info(f"Successful trade with={counterparty}.")
        developer_handle, nb_trades = registration_db.get_handle_and_trades(
            counterparty
        )
        http_dialogues = cast(HttpDialogues, self.context.http_dialogues)
        request_http_message, _ = http_dialogues.create(
            counterparty=str(HTTP_CLIENT_PUBLIC_ID),
            performative=HttpMessage.Performative.REQUEST,
            method="POST",
            url=self.leaderboard_url,
            headers="Content-Type: application/json; charset=utf-8",
            version="",
            body=json.dumps(
                {
                    "name": developer_handle,
                    "points": nb_trades,
                    "token": self.leaderboard_token,
                }
            ).encode("utf-8"),
        )
        self.context.outbox.put_message(message=request_http_message)
        self.context.logger.info(
            f"Notifying leaderboard: developer_handle={developer_handle}, nb_trades={nb_trades}."
        )

    def register_counterparty(self, counterparty: str, developer_handle: str) -> None:
        """
        Register a counterparty.

        :param counterparty: the counterparty address
        :param developer_handle: the developer handle
        """
        registration_db = cast(RegistrationDB, self.context.registration_db)
        registration_db.set_registered(counterparty, developer_handle)

    def update_search_query_params(self) -> None:
        """Update agent location and query for search."""
        search_query_type, search_query = random.choice(  # nosec
            list(self._search_queries.items())
        )
        self._search_query = search_query
        self._service_id = search_query["search_value"]
        location_name, location = random.choice(list(self._locations.items()))  # nosec
        self._agent_location = Location(
            latitude=location["latitude"], longitude=location["longitude"]
        )
        self.context.logger.info(
            f"New search_type={search_query_type} and location={location_name}."
        )
