"""Transaction Instruction class."""

from typing import List, NamedTuple
from .account import AccountMeta
from solders import instruction
from solders.pubkey import Pubkey as PublicKey


class TransactionInstruction(NamedTuple):
    """Transaction Instruction class."""

    keys: List[AccountMeta]
    """Public keys to include in this transaction Boolean represents whether this
    pubkey needs to sign the transaction.
    """
    program_id: PublicKey
    """Program Id to execute."""
    data: bytes = bytes(0)
    """Program input."""

    @classmethod
    def from_solders(cls, ixn: instruction.Instruction):
        """Convert from a `solders` instruction.
        Args:
            ixn: The `solders` instruction.
        Returns:
            The `solana-py` instruction.
        """
        keys = [AccountMeta.from_solders(am) for am in ixn.accounts]
        program_id = PublicKey.from_bytes(bytes(ixn.program_id))
        return cls(keys=keys, program_id=program_id, data=ixn.data)

    def to_solders(self) -> instruction.Instruction:
        """Convert to a `solders` instruction.
        Returns:
            The `solders` instruction.
        """
        accounts = [key for key in self.keys]
        return instruction.Instruction(program_id=self.program_id, data=self.data, accounts=accounts)

