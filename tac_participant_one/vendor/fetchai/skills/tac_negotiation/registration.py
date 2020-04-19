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

"""This package contains a class representing the registration state."""

import datetime
from typing import Optional

from aea.helpers.search.models import Description
from aea.skills.base import Model


class Registration(Model):
    """This class deals with the services registration state."""

    def __init__(self, **kwargs):
        """Instantiate the search class."""
        self._update_interval = kwargs.pop("update_interval", 5)  # type: int
        super().__init__(**kwargs)
        self._id = 0
        self.registered_goods_demanded_description = None  # type: Optional[Description]
        self.registered_goods_supplied_description = None  # type: Optional[Description]
        self._last_update_time = datetime.datetime.now()  # type: datetime.datetime

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
        return self.id

    def is_time_to_update_services(self) -> bool:
        """
        Check if the agent should update the service directory.

        :return: bool indicating the action
        """
        now = datetime.datetime.now()
        diff = now - self._last_update_time
        result = diff.total_seconds() > self._update_interval
        if result:
            self._last_update_time = now
        return result
