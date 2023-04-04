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
"""This module contains the TransactionInstruction of the solana module."""

from typing import List, NamedTuple

from aea_ledger_solana.account import AccountMeta
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
    def from_solders(cls, ixn: instruction.Instruction) -> "TransactionInstruction":
        """
        Convert from a `solders` instruction.

        :param ixn: The `solders` instruction.
        :param The `solana-py` instruction.
        :return: The `solders` instruction.
        """
        keys = [AccountMeta.from_solders(am) for am in ixn.accounts]
        program_id = PublicKey.from_bytes(bytes(ixn.program_id))
        return cls(keys=keys, program_id=program_id, data=ixn.data)

    def to_solders(self) -> instruction.Instruction:
        """
        Convert to a `solders` instruction.

        :return: The `solders` instruction.
        """
        accounts = [key for key in self.keys]
        return instruction.Instruction(
            program_id=self.program_id, data=self.data, accounts=accounts
        )
