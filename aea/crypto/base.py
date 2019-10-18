# -*- coding: utf-8 -*-

# ------------------------------------------------------------------------------
#
#   Copyright 2018-2019 Fetch.AI Limited
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""Abstract module wrapping the public and private key cryptography and ledger api."""

from abc import ABC, abstractmethod


class Crypto(ABC):
    """Base class for a crypto object."""

    @abstractmethod
    def public_key(self) -> str:
        """
        Return a public key.

        :return: a public key string
        """

    @abstractmethod
    def address(self) -> str:
        """
        Return the address.

        :return: an address string
        """

    @abstractmethod
    def token_balance(self) -> float:
        """
        Return the token balance.

        :return: the token balance
        """

    @abstractmethod
    def transfer(self, destination_address: str, amount: float, tx_fee: float) -> None:
        """
        Transfer from self to destination.

        :param destination_address: the address of the receive
        :param amount: the amount
        :param tx_fee: the tx fee
        """
