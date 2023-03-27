"""Solana transaction."""
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
