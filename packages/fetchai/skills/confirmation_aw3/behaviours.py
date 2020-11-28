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

"""This package contains the behaviours of the agent."""

from typing import cast

from packages.fetchai.skills.confirmation_aw3.strategy import Strategy
from packages.fetchai.skills.generic_buyer.behaviours import (
    GenericSearchBehaviour,
    GenericTransactionBehaviour,
)


TransactionBehaviour = GenericTransactionBehaviour


class SearchBehaviour(GenericSearchBehaviour):
    """Search behaviour extension."""

    def act(self) -> None:
        """
        Implement the act.

        :return: None
        """
        strategy = cast(Strategy, self.context.strategy)
        strategy.update_search_query_params()
        super().act()
