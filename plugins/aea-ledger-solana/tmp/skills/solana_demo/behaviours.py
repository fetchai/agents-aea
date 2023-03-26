# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 valory
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
from packages.valory.connections.ledger.connection import (
    PUBLIC_ID as LEDGER_CONNECTION_PUBLIC_ID,
)
from packages.valory.protocols.ledger_api.dialogues import (
    LedgerApiDialogues,
)
from packages.valory.protocols.ledger_api.message import LedgerApiMessage

from packages.eightballer.skills.solana_demo.strategy import SolanaDemoStrategy

from aea_ledger_solana import SolanaApi, SolanaFaucetApi
LEDGER_API_ADDRESS = str(LEDGER_CONNECTION_PUBLIC_ID)


class SolanaDemoBehaviour(TickerBehaviour):
    """This class scaffolds a behaviour."""

    def setup(self) -> None:
        """Implement the setup."""
        self.context.logger.info("SolanaDemo: setup method called. Checking Balance...")

        # we submit a message to request the balance of the account.
        # we use the 'ledger_api' protocol to interact with the ledger.
        self._check_balance()

    def act(self) -> None:
        """Implement the act."""
        # self.context.logger.info("SolanaDemo: act method called.")
        strategy = cast(SolanaDemoStrategy, self.context.strategy)
        if strategy.in_flight:
            return
        if strategy.balance == 0:
            self.context.logger.info("SolanaDemo: Requesting from faucet...")
            self._submit_wealth_request()

        if strategy.balance and not strategy.has_transferred_lamports:
            self.context.logger.info("SolanaDemo: Sending Transaction...")
            strategy.in_flight = True
            return self._send_transfer()
        self._check_balance()

    def teardown(self) -> None:
        """Implement the task teardown."""
        self.context.logger.info("SolanaDemo: teardown method called.")

    def _check_balance(self):
        strategy = cast(SolanaDemoStrategy, self.context.strategy)
        ledger_api_dialogues = cast(
            LedgerApiDialogues, self.context.ledger_api_dialogues
        )
        ledger_api_msg, _ = ledger_api_dialogues.create(
            counterparty=LEDGER_API_ADDRESS,
            performative=LedgerApiMessage.Performative.GET_BALANCE,
            ledger_id=strategy.ledger_id,
            address=cast(str, self.context.agent_addresses.get(
                strategy.ledger_id)),
        )
        self.context.outbox.put_message(message=ledger_api_msg)

    def _submit_wealth_request(self):
        """Use the faucet to request wealth. Note this is not a good way to do this and is only for devnet."""
        solana_api = SolanaApi()
        solana_faucet = SolanaFaucetApi()
        solana_faucet.generate_wealth_if_needed(solana_api, self.context.agent_address, 1000000000000000000)

    def _send_transfer(self):
        """We send a transfer request to a known address"""
        strategy = cast(SolanaDemoStrategy, self.context.strategy)
        ledger_api_dialogues = cast(
            LedgerApiDialogues, self.context.ledger_api_dialogues
        )
        terms = strategy.get_transfer_terms()
        ledger_api_msg, _ = ledger_api_dialogues.create(
            counterparty=LEDGER_API_ADDRESS,
            performative=LedgerApiMessage.Performative.GET_RAW_TRANSACTION,
            terms=terms,
        )
        self.context.outbox.put_message(message=ledger_api_msg)
