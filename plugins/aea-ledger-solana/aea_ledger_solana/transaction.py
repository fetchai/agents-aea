# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 Valory AG
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
"""This module contains the transaction helper for the solana module."""
import json

from solana.transaction import Transaction
from solders.transaction import Transaction as SoldersTransaction


class SolanaTransaction(Transaction):
    """Class to represent a solana ledger transaction."""

    @classmethod
    def from_json(cls, json_data: dict) -> "SolanaTransaction":
        """Convert from a json."""
        string_value = json.dumps(json_data)
        solders_tx = SoldersTransaction.from_json(string_value)
        return cls.from_solders(solders_tx)

    def to_json(self) -> dict:
        """Convert to json."""
        return json.loads(self._solders.to_json())
