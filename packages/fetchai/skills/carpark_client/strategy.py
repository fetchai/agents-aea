# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2023 Fetch.AI Limited
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

from typing import List

from packages.fetchai.skills.generic_buyer.strategy import GenericStrategy


class Strategy(GenericStrategy):
    """This class defines a strategy for the agent."""

    def get_cheapest_proposal(self, agents: List) -> dict:
        """
        Get the cheapest proposal from a given list.

        e.g. agents = [
                {'sender': 'agent_1', 'message': {'price': 10, ...}},
                {'sender': 'agent_2', 'message': {'price': 5, ...}}
            ]
        """
        return sorted(
            agents,
            key=lambda agent: agent["message"].proposal.values["price"],
            reverse=False,
        )[0]
