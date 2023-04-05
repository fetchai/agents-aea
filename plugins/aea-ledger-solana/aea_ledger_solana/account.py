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
        """Convert from a `solders` AccountMeta."""
        return cls(
            pubkey=PublicKey.from_bytes(bytes(meta.pubkey)),
            is_signer=meta.is_signer,
            is_writable=meta.is_writable,
        )

    def to_solders(self) -> instruction.AccountMeta:
        """Convert to a `solders` AccountMeta."""
        return instruction.AccountMeta(
            pubkey=self.pubkey, is_signer=self.is_signer, is_writable=self.is_writable
        )
