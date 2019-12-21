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
import logging
import sys
from typing import cast, TYPE_CHECKING

from aea.crypto.ethereum import ETHEREUM
from aea.crypto.fetchai import FETCHAI
from aea.skills.behaviours import TickerBehaviour

if TYPE_CHECKING or "pytest" in sys.modules:
    from packages.protocols.oef.message import OEFMessage
    from packages.protocols.oef.serialization import DEFAULT_OEF, OEFSerializer
    from packages.skills.weather_client_ledger.strategy import Strategy
else:
    from oef_protocol.message import OEFMessage
    from oef_protocol.serialization import DEFAULT_OEF, OEFSerializer
    from weather_client_ledger_skill.strategy import Strategy

logger = logging.getLogger("aea.weather_client_ledger_skill")

DEFAULT_SEARCH_INTERVAL = 5.0


class MySearchBehaviour(TickerBehaviour):
    """This class implements a search behaviour."""

    def __init__(self, **kwargs):
        """Initialize the search behaviour."""
        search_interval = cast(float, kwargs.pop('search_interval')) if 'search_interval' in kwargs.keys() else DEFAULT_SEARCH_INTERVAL
        super().__init__(tick_interval=search_interval, **kwargs)

    def setup(self) -> None:
        """Implement the setup for the behaviour."""
        if self.context.ledger_apis.has_fetchai:
            fet_balance = self.context.ledger_apis.token_balance(FETCHAI, cast(str, self.context.agent_addresses.get(FETCHAI)))
            if fet_balance > 0:
                logger.info("[{}]: starting balance on fetchai ledger={}.".format(self.context.agent_name, fet_balance))
            else:
                logger.warning("[{}]: you have no starting balance on fetchai ledger!".format(self.context.agent_name))
                # TODO: deregister skill from filter

        if self.context.ledger_apis.has_ethereum:
            eth_balance = self.context.ledger_apis.token_balance(ETHEREUM, cast(str, self.context.agent_addresses.get(ETHEREUM)))
            if eth_balance > 0:
                logger.info("[{}]: starting balance on ethereum ledger={}.".format(self.context.agent_name, eth_balance))
            else:
                logger.warning("[{}]: you have no starting balance on ethereum ledger!".format(self.context.agent_name))
                # TODO: deregister skill from filter

    def act(self) -> None:
        """
        Implement the act.

        :return: None
        """
        strategy = cast(Strategy, self.context.strategy)
        if strategy.is_searching:
            query = strategy.get_service_query()
            search_id = strategy.get_next_search_id()
            oef_msg = OEFMessage(type=OEFMessage.Type.SEARCH_SERVICES,
                                 id=search_id,
                                 query=query)
            self.context.outbox.put_message(to=DEFAULT_OEF,
                                            sender=self.context.agent_address,
                                            protocol_id=OEFMessage.protocol_id,
                                            message=OEFSerializer().encode(oef_msg))

    def teardown(self) -> None:
        """
        Implement the task teardown.

        :return: None
        """
        if self.context.ledger_apis.has_fetchai:
            balance = self.context.ledger_apis.token_balance(FETCHAI, cast(str, self.context.agent_addresses.get(FETCHAI)))
            logger.info("[{}]: ending balance on fetchai ledger={}.".format(self.context.agent_name, balance))

        if self.context.ledger_apis.has_ethereum:
            balance = self.context.ledger_apis.token_balance(ETHEREUM, cast(str, self.context.agent_addresses.get(ETHEREUM)))
            logger.info("[{}]: ending balance on ethereum ledger={}.".format(self.context.agent_name, balance))
