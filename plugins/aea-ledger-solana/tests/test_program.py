"""Tests for the solana program."""
from dataclasses import dataclass


class SolanaAccount():
    """Class to represent a solana account."""
    def __init__(self, address, entity):
        self.address = address
        self.entity = entity

