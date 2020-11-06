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

"""This module contains the strategy class (extended from the generic_seller skill)."""

import json
from typing import Dict

from packages.fetchai.skills.generic_seller.strategy import GenericStrategy


class Strategy(GenericStrategy):
    """This class defines a strategy for the agent."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize the strategy of the agent.

        :return: None
        """
        self.shared_state_key = kwargs.pop("shared_state_key", None)
        if self.shared_state_key is None:
            raise ValueError("No shared_state_key provided!")
        super().__init__(**kwargs)

    def collect_from_data_source(self) -> Dict[str, str]:
        """
        Build the data payload.

        :return: a dict of the data found in the shared state.
        """
        data = self.context.shared_state.get(self.shared_state_key, "{}")
        result: Dict[str, str] = {}
        try:
            loaded = json.load(data)
            if not isinstance(loaded, dict) or not all(
                [
                    isinstance(key, str) and isinstance(value, str)
                    for key, value in loaded.items()
                ]
            ):
                raise ValueError("Invalid data, must be Dict[str, str]")
            result = loaded
        except (TypeError, ValueError) as e:
            self.context.logger.warning(f"error when loading json: {e}")
        return result
