# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2020 Fetch.AI Limited
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

"""This module contains terms related classes."""

from typing import Dict

Address = str


class Terms:
    """Class to represent the terms of a multi-currency & multi-token ledger transaction."""

    def __init__(
        self,
        sender_addr: Address,
        counterparty_addr: Address,
        amount_by_currency_id: Dict[str, int],
        quantities_by_good_id: Dict[str, int],
        is_sender_payable_tx_fee: bool,
        nonce: str,
    ):
        """
        Instantiate terms.

        :param sender_addr: the sender address of the transaction.
        :param counterparty_addr: the counterparty address of the transaction.
        :param amount_by_currency_id: the amount by the currency of the transaction.
        :param quantities_by_good_id: a map from good id to the quantity of that good involved in the transaction.
        :param is_sender_payable_tx_fee: whether the sender or counterparty pays the tx fee.
        :param nonce: nonce to be included in transaction to discriminate otherwise identical transactions
        """
        self._sender_addr = sender_addr
        self._counterparty_addr = counterparty_addr
        self._amount_by_currency_id = amount_by_currency_id
        self._quantities_by_good_id = quantities_by_good_id
        self._is_sender_payable_tx_fee = is_sender_payable_tx_fee
        self._nonce = nonce

    @property
    def sender_addr(self) -> Address:
        """Get the sender address."""
        return self._sender_addr

    @property
    def counterparty_addr(self) -> Address:
        """Get the counterparty address."""
        return self._counterparty_addr

    @property
    def amount_by_currency_id(self) -> Dict[str, int]:
        """Get the amount by currency id."""
        return self._amount_by_currency_id

    @property
    def quantities_by_good_id(self) -> Dict[str, int]:
        """Get the quantities by good id."""
        return self._quantities_by_good_id

    @property
    def is_sender_payable_tx_fee(self) -> bool:
        """Bool indicating whether the tx fee is paid by sender or counterparty."""
        return self._is_sender_payable_tx_fee

    @property
    def nonce(self) -> str:
        """Get the nonce."""
        return self._nonce


class Transfer:
    """Class to represent the terms of simple ledger-based transfer."""

    def __init__(
        self,
        sender_addr: Address,
        counterparty_addr: Address,
        amount_by_currency_id: Dict[str, int],
        nonce: str,
        service_reference: str,
        **kwargs,
    ):
        """
        Instantiate terms.

        :param sender_addr: the sender address of the transaction.
        :param counterparty_addr: the counterparty address of the transaction.
        :param amount_by_currency_id: the amount by the currency of the transaction.
        :param nonce: nonce to be included in transaction to discriminate otherwise identical transactions
        :param service_reference: the service reference
        """
        self._sender_addr = sender_addr
        self._counterparty_addr = counterparty_addr
        self._amount_by_currency_id = amount_by_currency_id
        self._nonce = nonce
        self._service_reference = service_reference

    @property
    def sender_addr(self) -> Address:
        """Get the sender address."""
        return self._sender_addr

    @property
    def counterparty_addr(self) -> Address:
        """Get the counterparty address."""
        return self._counterparty_addr

    @property
    def amount_by_currency_id(self) -> Dict[str, int]:
        """Get the amount by currency id."""
        return self._amount_by_currency_id

    @property
    def nonce(self) -> str:
        """Get the nonce."""
        return self._nonce

    @property
    def service_reference(self) -> str:
        """Get the service reference."""
        return self._service_reference
