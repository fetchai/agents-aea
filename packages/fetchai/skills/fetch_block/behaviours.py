# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2022 Fetch.AI Limited
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

"""This package contains the behaviour to get the latest block from the Fetch ledger."""

from typing import Any, cast

from aea.skills.behaviours import TickerBehaviour

from packages.fetchai.connections.ledger.base import CONNECTION_ID as LEDGER_API_ADDRESS
from packages.fetchai.protocols.ledger_api.custom_types import Kwargs
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.skills.fetch_block.dialogues import LedgerApiDialogues


class FetchBlockBehaviour(TickerBehaviour):
    """This class provides a behaviour to get the latest block from the Fetch ledger."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the fetch block behaviour."""

        super().__init__(**kwargs)

    def _get_block(self) -> None:
        """Request the latest block by sending a message to the ledger API."""
        ledger_api_dialogues = cast(
            LedgerApiDialogues, self.context.ledger_api_dialogues
        )
        ledger_api_msg, _ = ledger_api_dialogues.create(
            counterparty=str(LEDGER_API_ADDRESS),
            performative=LedgerApiMessage.Performative.GET_STATE,
            ledger_id=self.context.default_ledger_id,
            callable="blocks",
            args=("latest",),
            kwargs=Kwargs({}),
        )
        self.context.outbox.put_message(message=ledger_api_msg)

    def setup(self) -> None:
        """Implement the setup."""
        self.context.logger.info("setting up FetchBlockBehaviour")

    def act(self) -> None:
        """Implement the act."""

        self.context.logger.info("Fetching latest block...")
        self._get_block()

    def teardown(self) -> None:
        """Implement the task teardown."""
        self.context.logger.info("tearing down FetchBlockBehaviour")
