"""Solana account implementation."""
from dataclasses import dataclass

from solders import instruction
from solders.pubkey import Pubkey as PublicKey


@dataclass
class AccountMeta:
    """Account metadata dataclass."""

    pubkey: PublicKey
    """An account's public key."""
    is_signer: bool
    """True if an instruction requires a transaction signature matching `pubkey`"""
    is_writable: bool
    """True if the `pubkey` can be loaded as a read-write account."""

    @classmethod
    def from_solders(cls, meta: instruction.AccountMeta):
        """
        Convert from a `solders` AccountMeta.

        Args:
            meta: The `solders` AccountMeta.
        Returns:
            The `solana-py` AccountMeta.
        """
        return cls(
            pubkey=PublicKey.from_bytes(bytes(meta.pubkey)),
            is_signer=meta.is_signer,
            is_writable=meta.is_writable,
        )

    def to_solders(self) -> instruction.AccountMeta:
        """
        Convert to a `solders` AccountMeta.

        Returns:
            The `solders` AccountMeta.
        """
        return instruction.AccountMeta(
            pubkey=self.pubkey, is_signer=self.is_signer, is_writable=self.is_writable
        )
