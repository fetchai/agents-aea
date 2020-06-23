# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2018-2019 Fetch.AI Limited
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

"""This module contains the tests for the base module."""

from aea.helpers.transaction.base import Terms, Transfer


def test_init_terms():
    """Test the terms object initialization."""
    sender_addr = "SenderAddress"
    counterparty_addr = "CounterpartyAddress"
    amount_by_currency_id = {"FET": 10}
    quantities_by_good_id = {"good_1": 20}
    is_sender_payable_tx_fee = True
    nonce = "somestring"
    terms = Terms(
        sender_addr=sender_addr,
        counterparty_addr=counterparty_addr,
        amount_by_currency_id=amount_by_currency_id,
        quantities_by_good_id=quantities_by_good_id,
        is_sender_payable_tx_fee=is_sender_payable_tx_fee,
        nonce=nonce,
    )
    assert terms.sender_addr == sender_addr
    assert terms.counterparty_addr == counterparty_addr
    assert terms.amount_by_currency_id == amount_by_currency_id
    assert terms.quantities_by_good_id == quantities_by_good_id
    assert terms.is_sender_payable_tx_fee == is_sender_payable_tx_fee
    assert terms.nonce == nonce


def test_init_transfer():
    """Test the transfer object initialization."""
    sender_addr = "SenderAddress"
    counterparty_addr = "CounterpartyAddress"
    amount_by_currency_id = {"FET": 10}
    service_reference = "someservice"
    nonce = "somestring"
    transfer = Transfer(
        sender_addr=sender_addr,
        counterparty_addr=counterparty_addr,
        amount_by_currency_id=amount_by_currency_id,
        service_reference=service_reference,
        nonce=nonce,
    )
    assert transfer.sender_addr == sender_addr
    assert transfer.counterparty_addr == counterparty_addr
    assert transfer.amount_by_currency_id == amount_by_currency_id
    assert transfer.service_reference == service_reference
    assert transfer.nonce == nonce
