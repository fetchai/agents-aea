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
from typing import cast

from aea.protocols.oef.models import Description, Query, Constraint, ConstraintType
from aea.skills.base import SharedClass

DEFAULT_COUNTRY = 'UK'
SEARCH_TERM = 'country'
DEFAULT_SEARCH_INTERVAL = 5.0
DEFAULT_MAX_PRICE = 0.2


class Strategy(SharedClass):
    """This class defines a strategy for the agent."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize the strategy of the agent.

        :return: None
        """
        self._country = kwargs.pop('country') if 'country' in kwargs.keys() else DEFAULT_COUNTRY
        self._search_interval = cast(float, kwargs.pop('search_interval')) if 'search_interval' in kwargs.keys() else DEFAULT_SEARCH_INTERVAL
        self._max_price = kwargs.pop('max_price') if 'max_price' in kwargs.keys() else DEFAULT_MAX_PRICE
        super().__init__(**kwargs)
        self.is_searching = True
        self.last_search_time = datetime.datetime.now()

    def get_service_query(self) -> Query:
        """
        Get the service query of the agent.

        :return: the query
        """
        query = Query([Constraint(SEARCH_TERM, ConstraintType("==", self._country))], model=None)
        return query

    def is_time_to_search(self) -> bool:
        """
        Check whether it is time to search.

        :return: whether it is time to search
        """
        now = datetime.datetime.now()
        diff = now - self.last_search_time
        result = diff.total_seconds() > self._search_interval
        return result

    def is_acceptable_proposal(self, proposal: Description) -> bool:
        """
        Check whether it is an acceptable proposal.

        :return: whether it is acceptable
        """
        result = True if proposal.values["price"] < self._max_price * proposal.values['rows'] else False
        return result
