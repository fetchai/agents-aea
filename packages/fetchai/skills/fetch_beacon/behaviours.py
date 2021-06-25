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

"""This package contains the behaviour to get the Fetch random beacon."""

from typing import Any, cast

from aea.skills.behaviours import TickerBehaviour

from packages.fetchai.connections.ledger.base import CONNECTION_ID as LEDGER_API_ADDRESS
from packages.fetchai.protocols.ledger_api.custom_types import Kwargs
from packages.fetchai.protocols.ledger_api.message import LedgerApiMessage
from packages.fetchai.skills.fetch_beacon.dialogues import LedgerApiDialogues


class FetchBeaconBehaviour(TickerBehaviour):
    """This class provides a simple beacon fetch behaviour."""

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the beacon fetch behaviour."""

        super().__init__(**kwargs)

    def _get_random_beacon(self) -> None:
        """Request the latest random beacon value by sending a message to the ledger API."""
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
        self.context.logger.info("setting up FetchBeaconBehaviour")

    def act(self) -> None:
        """Implement the act."""

        self.context.logger.info("Fetching random beacon value...")
        self._get_random_beacon()

    def teardown(self) -> None:
        """Implement the task teardown."""
        self.context.logger.info("tearing down FetchBeaconBehaviour")
