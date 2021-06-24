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
from typing import Any, Dict, List, Optional, Tuple, cast

from packages.fetchai.skills.confirmation_aw2.registration_db import RegistrationDB
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
        self.minimum_hours_between_txs = kwargs.pop("mininum_hours_between_txs", 4)
        self.minimum_minutes_since_last_attempt = kwargs.pop(
            "minimum_minutes_since_last_attempt", 2
        )
        super().__init__(**kwargs)
        self.last_attempt: Dict[str, datetime.datetime] = {}

    def get_acceptable_counterparties(
        self, counterparties: Tuple[str, ...]
    ) -> Tuple[str, ...]:
        """
        Process counterparties and drop unacceptable ones.

        :param counterparties: a tuple of counterparties
        :return: list of counterparties
        """
        valid_counterparties: List[str] = []
        for counterparty in counterparties:
            if self.is_valid_counterparty(counterparty):
                valid_counterparties.append(counterparty)
        return tuple(valid_counterparties)

    def is_enough_time_since_last_attempt(self, counterparty: str) -> bool:
        """
        Check if enough time has passed since last attempt for potential previous trade to complete.

        :param counterparty: the counterparty
        :return: bool indicating validity
        """
        last_time = self.last_attempt.get(counterparty, None)
        if last_time is None:
            return True
        result = datetime.datetime.now() > last_time + datetime.timedelta(
            minutes=self.minimum_minutes_since_last_attempt
        )
        return result

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
        if not self.is_enough_time_since_last_attempt(counterparty):
            self.context.logger.debug(
                f"Not enough time since last attempt for counterparty={counterparty}!"
            )
            return False
        self.last_attempt[counterparty] = datetime.datetime.now()
        if not registration_db.is_allowed_to_trade(
            counterparty, self.minimum_hours_between_txs
        ):
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
        self.context.logger.info(
            f"Successful trade with={counterparty}. Data acquired={data}!"
        )

    def register_counterparty(self, counterparty: str, developer_handle: str) -> None:
        """
        Register a counterparty.

        :param counterparty: the counterparty address
        :param developer_handle: the developer handle
        """
        registration_db = cast(RegistrationDB, self.context.registration_db)
        registration_db.set_registered(counterparty, developer_handle)
