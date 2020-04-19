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

"""This package contains a class representing the search state."""

import datetime
from typing import Set

from aea.skills.base import Model


class Search(Model):
    """This class deals with the services search state."""

    def __init__(self, **kwargs):
        """Instantiate the search class."""
        self._search_interval = kwargs.pop("search_interval", 5)  # type: int
        super().__init__(**kwargs)
        self._id = 0
        self._ids_for_sellers = set()  # type: Set[int]
        self._ids_for_buyers = set()  # type: Set[int]
        self._last_search_time = datetime.datetime.now()  # type: datetime.datetime

    @property
    def id(self) -> int:
        """Get the search id."""
        return self._id

    @property
    def ids_for_sellers(self) -> Set[int]:
        """Get search ids for the sellers."""
        return self._ids_for_sellers

    @property
    def ids_for_buyers(self) -> Set[int]:
        """Get search ids for the buyers."""
        return self._ids_for_buyers

    def get_next_id(self, is_searching_for_sellers: bool) -> int:
        """
        Generate the next search id and stores it.

        :param is_searching_for_sellers: whether it is a seller search
        :return: a search id
        """
        self._id += 1
        if is_searching_for_sellers:
            self._ids_for_sellers.add(self.id)
        else:
            self._ids_for_buyers.add(self.id)
        return self.id

    def is_time_to_search_services(self) -> bool:
        """
        Check if the agent should search the service directory.

        :return: bool indicating the action
        """
        now = datetime.datetime.now()
        diff = now - self._last_search_time
        result = diff.total_seconds() > self._search_interval
        if result:
            self._last_search_time = now
        return result
