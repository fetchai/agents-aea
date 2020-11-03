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

from typing import Dict

from packages.fetchai.skills.generic_seller.strategy import GenericStrategy


class Strategy(GenericStrategy):
    """This class defines a strategy for the agent."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize the strategy of the agent.

        :param register_as: determines whether the agent registers as seller, buyer or both
        :param search_for: determines whether the agent searches for sellers, buyers or both

        :return: None
        """
        self.shared_state_key = kwargs.pop("shared_state_key", None)
        if self.shared_state_key is None:
            raise ValueError("No shared_state_key provided!")
        super().__init__(**kwargs)

    def collect_from_data_source(self) -> Dict[str, str]:
        """
        Build the data payload.

        :param fetched_data: the fetched data
        :return: a tuple of the data and the rows
        """
        data = self.context.shared_state.get(self.shared_state_key, {})
        return data
