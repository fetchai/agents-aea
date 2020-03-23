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
from typing import Set, cast

from aea.skills.base import Model

DEFAULT_SEARCH_INTERVAL = 30


class Search(Model):
    """This class deals with the search state."""

    def __init__(self, **kwargs):
        """Instantiate the search class."""
        self._search_interval = (
            cast(float, kwargs.pop("search_interval"))
            if "search_interval" in kwargs.keys()
            else DEFAULT_SEARCH_INTERVAL
        )
        super().__init__(**kwargs)
        self._id = 0
        self.ids_for_tac = set()  # type: Set[int]
        self._last_search_time = datetime.datetime.now()

    @property
    def id(self) -> int:
        """Get the search id."""
        return self._id

    def get_next_id(self) -> int:
        """
        Generate the next search id and stores it.

        :return: a search id
        """
        self._id += 1
        self.ids_for_tac.add(self._id)
        return self._id

    def is_time_to_search(self) -> bool:
        """
        Check whether it is time to search.

        :return: whether it is time to search
        """
        now = datetime.datetime.now()
        diff = now - self._last_search_time
        result = diff.total_seconds() > self._search_interval
        if result:
            self._last_search_time = now
        return result
