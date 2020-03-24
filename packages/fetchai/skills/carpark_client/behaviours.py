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

from aea.crypto.ethereum import ETHEREUM
from aea.crypto.fetchai import FETCHAI
from aea.skills.behaviours import TickerBehaviour

from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.protocols.oef_search.serialization import OefSearchSerializer
from packages.fetchai.skills.carpark_client.strategy import Strategy


class MySearchBehaviour(TickerBehaviour):
    """This class scaffolds a behaviour."""

    def __init__(self, **kwargs):
        """Initialise the class."""
        super().__init__(**kwargs)
        self._search_id = 0

    def setup(self) -> None:
        """Implement the setup for the behaviour."""
        if self.context.ledger_apis.has_fetchai:
            fet_balance = self.context.ledger_apis.token_balance(
                FETCHAI, cast(str, self.context.agent_addresses.get(FETCHAI))
            )
            if fet_balance > 0:
                self.context.logger.info(
                    "[{}]: starting balance on fetchai ledger={}.".format(
                        self.context.agent_name, fet_balance
                    )
                )
            else:
                self.context.logger.warning(
                    "[{}]: you have no starting balance on fetchai ledger!".format(
                        self.context.agent_name
                    )
                )

        if self.context.ledger_apis.has_ethereum:
            eth_balance = self.context.ledger_apis.token_balance(
                ETHEREUM, cast(str, self.context.agent_addresses.get(ETHEREUM))
            )
            if eth_balance > 0:
                self.context.logger.info(
                    "[{}]: starting balance on ethereum ledger={}.".format(
                        self.context.agent_name, eth_balance
                    )
                )
            else:
                self.context.logger.warning(
                    "[{}]: you have no starting balance on ethereum ledger!".format(
                        self.context.agent_name
                    )
                )

        # TODO: deregister skill from filter

    def act(self) -> None:
        """
        Implement the act.

        :return: None
        """
        strategy = cast(Strategy, self.context.strategy)
        if strategy.is_searching:
            strategy.on_submit_search()
            self._search_id += 1
            query = strategy.get_service_query()
            search_request = OefSearchMessage(
                performative=OefSearchMessage.Performative.SEARCH_SERVICES,
                dialogue_reference=(str(self._search_id), ""),
                query=query,
            )
            self.context.outbox.put_message(
                to=self.context.search_service_address,
                sender=self.context.agent_address,
                protocol_id=OefSearchMessage.protocol_id,
                message=OefSearchSerializer().encode(search_request),
            )

    def teardown(self) -> None:
        """
        Implement the task teardown.

        :return: None
        """
        if self.context.ledger_apis.has_fetchai:
            balance = self.context.ledger_apis.token_balance(
                FETCHAI, cast(str, self.context.agent_addresses.get(FETCHAI))
            )
            self.context.logger.info(
                "[{}]: ending balance on fetchai ledger={}.".format(
                    self.context.agent_name, balance
                )
            )

        if self.context.ledger_apis.has_ethereum:
            balance = self.context.ledger_apis.token_balance(
                ETHEREUM, cast(str, self.context.agent_addresses.get(ETHEREUM))
            )
            self.context.logger.info(
                "[{}]: ending balance on ethereum ledger={}.".format(
                    self.context.agent_name, balance
                )
            )
