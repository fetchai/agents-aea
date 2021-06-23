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
from typing import Any, Dict

from packages.fetchai.skills.generic_seller.strategy import GenericStrategy


class Strategy(GenericStrategy):
    """This class defines a strategy for the agent."""

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize the strategy of the agent.

        :param kwargs: keyword arguments
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
        data = self.context.shared_state.get(self.shared_state_key, b"{}")
        formatted_data = self._format_data(data)
        return formatted_data

    def _format_data(self, data: bytes) -> Dict[str, str]:
        """
        Convert to dict.

        :param data: the bytes data to format
        :return: a dict with key and values as strings
        """
        result: Dict[str, str] = {}
        try:
            loaded = json.loads(data)
            if isinstance(loaded, dict) and all(
                [
                    isinstance(key, str) and isinstance(value, str)
                    for key, value in loaded.items()
                ]
            ):
                result = loaded
            else:
                result = {"data": json.dumps(loaded)}
        except json.decoder.JSONDecodeError as e:
            self.context.logger.warning(f"error when loading json: {e}")
        return result
