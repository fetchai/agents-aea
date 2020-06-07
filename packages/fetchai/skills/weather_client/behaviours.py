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

"""This package contains a scaffold of a behaviour."""

from typing import cast

from aea.skills.behaviours import TickerBehaviour

from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.weather_client.strategy import Strategy

DEFAULT_SEARCH_INTERVAL = 5.0


class MySearchBehaviour(TickerBehaviour):
    """This class implements a search behaviour."""

    def __init__(self, **kwargs):
        """Initialize the search behaviour."""
        search_interval = cast(
            float, kwargs.pop("search_interval", DEFAULT_SEARCH_INTERVAL)
        )
        super().__init__(tick_interval=search_interval, **kwargs)

    def setup(self) -> None:
        """Implement the setup for the behaviour."""
        strategy = cast(Strategy, self.context.strategy)
        if self.context.ledger_apis.has_ledger(strategy.ledger_id):
            balance = self.context.ledger_apis.token_balance(
                strategy.ledger_id,
                cast(str, self.context.agent_addresses.get(strategy.ledger_id)),
            )
            if balance > 0:
                self.context.logger.info(
                    "[{}]: starting balance on {} ledger={}.".format(
                        self.context.agent_name, strategy.ledger_id, balance
                    )
                )
            else:
                self.context.logger.warning(
                    "[{}]: you have no starting balance on {} ledger!".format(
                        self.context.agent_name, strategy.ledger_id
                    )
                )
                self.context.is_active = False

    def act(self) -> None:
        """
        Implement the act.

        :return: None
        """
        strategy = cast(Strategy, self.context.strategy)
        if strategy.is_searching:
            query = strategy.get_service_query()
            search_id = strategy.get_next_search_id()
            oef_msg = OefSearchMessage(
                performative=OefSearchMessage.Performative.SEARCH_SERVICES,
                dialogue_reference=(str(search_id), ""),
                query=query,
            )
            oef_msg.counterparty = self.context.search_service_address
            self.context.outbox.put_message(message=oef_msg)

    def teardown(self) -> None:
        """
        Implement the task teardown.

        :return: None
        """
        strategy = cast(Strategy, self.context.strategy)
        if self.context.ledger_apis.has_ledger(strategy.ledger_id):
            balance = self.context.ledger_apis.token_balance(
                strategy.ledger_id,
                cast(str, self.context.agent_addresses.get(strategy.ledger_id)),
            )
            self.context.logger.info(
                "[{}]: ending balance on {} ledger={}.".format(
                    self.context.agent_name, strategy.ledger_id, balance
                )
            )
