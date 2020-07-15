# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2020 Fetch.AI Limited
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

"""This package contains the behaviour for the erc-1155 client skill."""

from typing import cast

from aea.skills.behaviours import TickerBehaviour

from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.protocols.oef_search.message import OefSearchMessage
from packages.fetchai.skills.erc1155_client.dialogues import (
    LedgerApiDialogues,
    OefSearchDialogues,
)
from packages.fetchai.skills.erc1155_client.strategy import Strategy

DEFAULT_SEARCH_INTERVAL = 5.0
LEDGER_API_ADDRESS = "fetchai/ledger:0.2.0"


class SearchBehaviour(TickerBehaviour):
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
        ledger_api_dialogues = cast(
            LedgerApiDialogues, self.context.ledger_api_dialogues
        )
        ledger_api_msg = LedgerApiMessage(
            performative=LedgerApiMessage.Performative.GET_BALANCE,
            dialogue_reference=ledger_api_dialogues.new_self_initiated_dialogue_reference(),
            ledger_id=strategy.ledger_id,
            address=cast(str, self.context.agent_addresses.get(strategy.ledger_id)),
        )
        ledger_api_msg.counterparty = LEDGER_API_ADDRESS
        ledger_api_dialogues.update(ledger_api_msg)
        self.context.outbox.put_message(message=ledger_api_msg)

    def act(self) -> None:
        """
        Implement the act.

        :return: None
        """
        strategy = cast(Strategy, self.context.strategy)
        if strategy.is_searching:
            query = strategy.get_service_query()
            oef_search_dialogues = cast(
                OefSearchDialogues, self.context.oef_search_dialogues
            )
            oef_search_msg = OefSearchMessage(
                performative=OefSearchMessage.Performative.SEARCH_SERVICES,
                dialogue_reference=oef_search_dialogues.new_self_initiated_dialogue_reference(),
                query=query,
            )
            oef_search_msg.counterparty = self.context.search_service_address
            oef_search_dialogues.update(oef_search_msg)
            self.context.outbox.put_message(message=oef_search_msg)

    def teardown(self) -> None:
        """
        Implement the task teardown.

        :return: None
        """
        pass
