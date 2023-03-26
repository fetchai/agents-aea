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

"""This package contains a scaffold of a model."""
from typing import Optional
from aea.helpers.transaction.base import Terms

from aea.skills.base import Model


class SolanaDemoStrategy(Model):
    """This class scaffolds a model."""
    _ledger_id: str
    _in_flight: bool
    _balance: 0
    _has_transferred: bool = False

    @property
    def ledger_id(self) -> str:
        """Get the ledger id."""
        return self._ledger_id

    @property
    def balance(self) -> int:
        """Get the balance."""
        return self._balance

    @balance.setter
    def balance(self, value: int):
        """Set the balance."""
        self._balance = value

    @property
    def in_flight(self) -> bool:
        """Get the in_flight."""
        return self._in_flight

    @in_flight.setter
    def in_flight(self, value: bool):
        """Set the in_flight."""
        self._in_flight = value

    @property
    def has_transferred_lamports(self) -> bool:
        """Get the has_transferred_lamports."""
        return self._has_transferred

    @has_transferred_lamports.setter
    def has_transferred_lamports(self, value: bool):
        """Set the has_transferred_lamports."""
        self._has_transferred = value




    def __init__(self, **kwargs):
        """Initialize the strategy of the agent."""
        super().__init__(**kwargs)
        self._ledger_id = self.context.default_ledger_id
        self._in_flight = False
        self._balance = None
        self.context.logger.info(f"SolanaDemoStrategy: Running on ledger {self.ledger_id}")
        self.failed_txs = 0

    def get_transfer_terms(self) -> Terms:
        """
        Get deploy terms of deployment.
        :return: terms
        """
        terms = Terms(
            ledger_id=self.ledger_id,
            sender_address=self.context.agent_address,
            counterparty_address=self.context.agent_address,
            amount_by_currency_id={
                "lamports": 1000000000,
            },
            quantities_by_good_id={
                "lamports": 1000000000,
            },

            fee_by_currency_id={
                "lamports": 1000000000,
            },
            nonce="",
        )
        return terms
