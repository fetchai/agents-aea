# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021 Valory AG
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

import pytest

from aea.configurations.constants import DEFAULT_LEDGER, _FETCHAI_IDENTIFIER
from aea.exceptions import AEAEnforceError
from aea.helpers.transaction.base import (
    RawMessage,
    RawTransaction,
    SignedMessage,
    SignedTransaction,
    State,
    Terms,
    TransactionDigest,
    TransactionReceipt,
)


def test_init_terms():
    """Test the terms object initialization."""
    ledger_id = _FETCHAI_IDENTIFIER
    sender_addr = "SenderAddress"
    counterparty_addr = "CounterpartyAddress"
    amount_by_currency_id = {"FET": -10}
    quantities_by_good_id = {"good_1": 20}
    is_sender_payable_tx_fee = True
    nonce = "somestring"
    kwargs = {"key": "value"}
    fee_by_currency_id = {}
    terms = Terms(
        ledger_id=ledger_id,
        sender_address=sender_addr,
        counterparty_address=counterparty_addr,
        amount_by_currency_id=amount_by_currency_id,
        quantities_by_good_id=quantities_by_good_id,
        is_sender_payable_tx_fee=is_sender_payable_tx_fee,
        nonce=nonce,
        **kwargs,
    )
    sender_hash = "9af02c24bdb18b73aad129291dc9eee008f9bcf62f5a6e91b5cb7427f146ca3b"
    counterparty_hash = (
        "174c1321c0eb4a49bf99d783b56f4fc30d0ee558106454c56d1c0fad295ccc79"
    )
    assert terms.ledger_id == ledger_id
    assert terms.sender_address == sender_addr
    assert terms.counterparty_address == counterparty_addr
    assert terms.amount_by_currency_id == amount_by_currency_id
    assert terms.quantities_by_good_id == quantities_by_good_id
    assert terms.is_sender_payable_tx_fee == is_sender_payable_tx_fee
    assert terms.nonce == nonce
    assert terms.kwargs == kwargs
    assert terms.fee_by_currency_id == fee_by_currency_id
    assert terms.id == sender_hash
    assert terms.sender_hash == sender_hash
    assert terms.counterparty_hash == counterparty_hash
    assert terms.currency_id == next(iter(amount_by_currency_id.keys()))
    assert str(
        terms
    ) == "Terms: ledger_id={}, sender_address={}, counterparty_address={}, amount_by_currency_id={}, quantities_by_good_id={}, is_sender_payable_tx_fee={}, nonce={}, fee_by_currency_id={}, kwargs={}".format(
        ledger_id,
        sender_addr,
        counterparty_addr,
        amount_by_currency_id,
        quantities_by_good_id,
        is_sender_payable_tx_fee,
        nonce,
        fee_by_currency_id,
        kwargs,
    )
    assert terms == terms
    with pytest.raises(AEAEnforceError):
        terms.fee


def test_init_terms_w_fee():
    """Test the terms object initialization with fee."""
    ledger_id = _FETCHAI_IDENTIFIER
    sender_addr = "SenderAddress"
    counterparty_addr = "CounterpartyAddress"
    amount_by_currency_id = {"FET": -10}
    quantities_by_good_id = {"good_1": 20}
    is_sender_payable_tx_fee = True
    nonce = "somestring"
    fee_by_currency_id = {"FET": 1}
    terms = Terms(
        ledger_id=ledger_id,
        sender_address=sender_addr,
        counterparty_address=counterparty_addr,
        amount_by_currency_id=amount_by_currency_id,
        quantities_by_good_id=quantities_by_good_id,
        is_sender_payable_tx_fee=is_sender_payable_tx_fee,
        nonce=nonce,
        fee_by_currency_id=fee_by_currency_id,
    )
    new_counterparty_address = "CounterpartyAddressNew"
    terms.counterparty_address = new_counterparty_address
    assert terms.counterparty_address == new_counterparty_address
    assert terms.fee == next(iter(fee_by_currency_id.values()))
    assert terms.fee_by_currency_id == fee_by_currency_id
    assert terms.counterparty_payable_amount == 0
    assert terms.sender_payable_amount == -next(iter(amount_by_currency_id.values()))
    assert terms.sender_payable_amount_incl_fee == -next(
        iter(amount_by_currency_id.values())
    ) + next(iter(fee_by_currency_id.values()))
    assert terms.sender_fee == next(iter(fee_by_currency_id.values()))
    assert terms.counterparty_fee == 0


def test_init_terms_w_fee_counterparty():
    """Test the terms object initialization with fee."""
    ledger_id = _FETCHAI_IDENTIFIER
    sender_addr = "SenderAddress"
    counterparty_addr = "CounterpartyAddress"
    amount_by_currency_id = {"FET": 10}
    quantities_by_good_id = {"good_1": -20}
    is_sender_payable_tx_fee = False
    nonce = "somestring"
    fee_by_currency_id = {"FET": 1}
    terms = Terms(
        ledger_id=ledger_id,
        sender_address=sender_addr,
        counterparty_address=counterparty_addr,
        amount_by_currency_id=amount_by_currency_id,
        quantities_by_good_id=quantities_by_good_id,
        is_sender_payable_tx_fee=is_sender_payable_tx_fee,
        nonce=nonce,
        fee_by_currency_id=fee_by_currency_id,
    )
    new_counterparty_address = "CounterpartyAddressNew"
    terms.counterparty_address = new_counterparty_address
    assert terms.counterparty_address == new_counterparty_address
    assert terms.fee == next(iter(fee_by_currency_id.values()))
    assert terms.fee_by_currency_id == fee_by_currency_id
    assert terms.counterparty_payable_amount == next(
        iter(amount_by_currency_id.values())
    )
    assert terms.counterparty_payable_amount_incl_fee == next(
        iter(amount_by_currency_id.values())
    ) + next(iter(fee_by_currency_id.values()))
    assert terms.sender_payable_amount == 0
    assert terms.sender_fee == 0
    assert terms.counterparty_fee == next(iter(fee_by_currency_id.values()))


def test_init_terms_strict_positive():
    """Test the terms object initialization in strict mode."""
    ledger_id = _FETCHAI_IDENTIFIER
    sender_addr = "SenderAddress"
    counterparty_addr = "CounterpartyAddress"
    amount_by_currency_id = {"FET": -10}
    quantities_by_good_id = {"good_1": 20}
    is_sender_payable_tx_fee = True
    nonce = "somestring"
    assert Terms(
        ledger_id=ledger_id,
        sender_address=sender_addr,
        counterparty_address=counterparty_addr,
        amount_by_currency_id=amount_by_currency_id,
        quantities_by_good_id=quantities_by_good_id,
        is_sender_payable_tx_fee=is_sender_payable_tx_fee,
        nonce=nonce,
        is_strict=True,
    )


def test_init_terms_strict_negative():
    """Test the terms object initialization in strict mode."""
    ledger_id = _FETCHAI_IDENTIFIER
    sender_addr = "SenderAddress"
    counterparty_addr = "CounterpartyAddress"
    amount_by_currency_id = {"FET": 10}
    quantities_by_good_id = {"good_1": 20}
    is_sender_payable_tx_fee = True
    nonce = "somestring"
    with pytest.raises(AEAEnforceError):
        Terms(
            ledger_id=ledger_id,
            sender_address=sender_addr,
            counterparty_address=counterparty_addr,
            amount_by_currency_id=amount_by_currency_id,
            quantities_by_good_id=quantities_by_good_id,
            is_sender_payable_tx_fee=is_sender_payable_tx_fee,
            nonce=nonce,
            is_strict=True,
        )


def test_init_terms_multiple_goods():
    """Test the terms object initialization with multiple goods."""
    ledger_id = _FETCHAI_IDENTIFIER
    sender_addr = "SenderAddress"
    counterparty_addr = "CounterpartyAddress"
    amount_by_currency_id = {"FET": -10}
    quantities_by_good_id = {"good_1": 20, "good_2": -10}
    is_sender_payable_tx_fee = True
    nonce = "somestring"
    terms = Terms(
        ledger_id=ledger_id,
        sender_address=sender_addr,
        counterparty_address=counterparty_addr,
        amount_by_currency_id=amount_by_currency_id,
        quantities_by_good_id=quantities_by_good_id,
        is_sender_payable_tx_fee=is_sender_payable_tx_fee,
        nonce=nonce,
    )
    assert (
        terms.id == "f81812773f5242d0cb52cfa82bc08bdba8d17b1e56e2cf02b3056749184e198c"
    )


def test_init_terms_no_amount_and_quantity():
    """Test the terms object initialization with no amount."""
    ledger_id = DEFAULT_LEDGER
    sender_addr = "SenderAddress"
    counterparty_addr = "CounterpartyAddress"
    amount_by_currency_id = {}
    quantities_by_good_id = {}
    nonce = "somestring"
    terms = Terms(
        ledger_id=ledger_id,
        sender_address=sender_addr,
        counterparty_address=counterparty_addr,
        amount_by_currency_id=amount_by_currency_id,
        quantities_by_good_id=quantities_by_good_id,
        nonce=nonce,
    )
    new_counterparty_address = "CounterpartyAddressNew"
    terms.counterparty_address = new_counterparty_address
    assert terms.counterparty_address == new_counterparty_address
    assert not terms.has_fee
    assert terms.counterparty_payable_amount == 0
    assert terms.counterparty_payable_amount_incl_fee == 0
    assert terms.sender_payable_amount == 0
    assert terms.sender_payable_amount_incl_fee == 0


def test_terms_encode_decode():
    """Test encoding and decoding of terms."""

    class TermsProtobufObject:
        terms_bytes = b""

    ledger_id = DEFAULT_LEDGER
    sender_addr = "SenderAddress"
    counterparty_addr = "CounterpartyAddress"
    amount_by_currency_id = {"FET": -10}
    quantities_by_good_id = {"good_1": 20}
    is_sender_payable_tx_fee = True
    nonce = "somestring"
    terms = Terms(
        ledger_id=ledger_id,
        sender_address=sender_addr,
        counterparty_address=counterparty_addr,
        amount_by_currency_id=amount_by_currency_id,
        quantities_by_good_id=quantities_by_good_id,
        is_sender_payable_tx_fee=is_sender_payable_tx_fee,
        nonce=nonce,
        is_strict=True,
    )
    Terms.encode(TermsProtobufObject, terms)
    recovered_terms = Terms.decode(TermsProtobufObject)
    assert terms == recovered_terms


def test_init_raw_transaction():
    """Test the raw_transaction object initialization."""
    ledger_id = "some_ledger"
    body = {"body": "value"}
    rt = RawTransaction(ledger_id, body)
    assert rt.ledger_id == ledger_id
    assert rt.body == body
    assert str(rt) == "RawTransaction: ledger_id=some_ledger, body={'body': 'value'}"
    assert rt == rt


def test_raw_transaction_encode_decode():
    """Test encoding and decoding of terms."""

    class RawTransactionProtobufObject:
        raw_transaction_bytes = b""

    ledger_id = "some_ledger"
    body = {"body": "value"}
    rt = RawTransaction(ledger_id, body)
    RawTransaction.encode(RawTransactionProtobufObject, rt)
    recovered_rt = RawTransaction.decode(RawTransactionProtobufObject)
    assert rt == recovered_rt


def test_init_raw_message():
    """Test the raw_message object initialization."""
    ledger_id = "some_ledger"
    body = b"body"
    rm = RawMessage(ledger_id, body)
    assert rm.ledger_id == ledger_id
    assert rm.body == body
    assert not rm.is_deprecated_mode
    assert (
        str(rm)
        == f"RawMessage: ledger_id=some_ledger, body={body}, is_deprecated_mode=False"
    )
    assert rm == rm


def test_raw_message_encode_decode():
    """Test encoding and decoding of raw_message."""

    class RawMessageProtobufObject:
        raw_message_bytes = b""

    ledger_id = "some_ledger"
    body = b"body"
    rm = RawMessage(ledger_id, body)
    RawMessage.encode(RawMessageProtobufObject, rm)
    recovered_rm = RawMessage.decode(RawMessageProtobufObject)
    assert rm == recovered_rm


def test_init_signed_transaction():
    """Test the signed_transaction object initialization."""
    ledger_id = "some_ledger"
    body = {"key": "value"}
    st = SignedTransaction(ledger_id, body)
    assert st.ledger_id == ledger_id
    assert st.body == body
    assert str(st) == "SignedTransaction: ledger_id=some_ledger, body={'key': 'value'}"
    assert st == st


def test_signed_transaction_encode_decode():
    """Test encoding and decoding of signed_transaction."""

    class SignedTransactionProtobufObject:
        signed_transaction_bytes = b""

    ledger_id = "some_ledger"
    body = {"key": "value"}
    st = SignedTransaction(ledger_id, body)
    SignedTransaction.encode(SignedTransactionProtobufObject, st)
    recovered_st = SignedTransaction.decode(SignedTransactionProtobufObject)
    assert st == recovered_st


def test_init_signed_message():
    """Test the signed_message object initialization."""
    ledger_id = "some_ledger"
    body = "body"
    sm = SignedMessage(ledger_id, body)
    assert sm.ledger_id == ledger_id
    assert sm.body == body
    assert not sm.is_deprecated_mode
    assert (
        str(sm)
        == "SignedMessage: ledger_id=some_ledger, body=body, is_deprecated_mode=False"
    )
    assert sm == sm


def test_signed_message_encode_decode():
    """Test encoding and decoding of signed_message."""

    class SignedMessageProtobufObject:
        signed_message_bytes = b""

    ledger_id = "some_ledger"
    body = "body"
    sm = SignedMessage(ledger_id, body)
    SignedMessage.encode(SignedMessageProtobufObject, sm)
    recovered_sm = SignedMessage.decode(SignedMessageProtobufObject)
    assert sm == recovered_sm


def test_init_transaction_receipt():
    """Test the transaction_receipt object initialization."""
    ledger_id = "some_ledger"
    receipt = {"receipt": "v"}
    transaction = {"transaction": "v"}
    tr = TransactionReceipt(ledger_id, receipt, transaction)
    assert tr.ledger_id == ledger_id
    assert tr.receipt == receipt
    assert tr.transaction == transaction
    assert (
        str(tr)
        == f"TransactionReceipt: ledger_id={ledger_id}, receipt={receipt}, transaction={transaction}"
    )
    assert tr == tr


def test_transaction_receipt_encode_decode():
    """Test encoding and decoding of transaction_receipt."""

    class TransactionReceiptProtobufObject:
        transaction_receipt_bytes = b""

    ledger_id = "some_ledger"
    receipt = {"receipt": "v"}
    transaction = {"transaction": "v"}
    tr = TransactionReceipt(ledger_id, receipt, transaction)
    TransactionReceipt.encode(TransactionReceiptProtobufObject, tr)
    recovered_tr = TransactionReceipt.decode(TransactionReceiptProtobufObject)
    assert tr == recovered_tr


def test_init_state():
    """Test the state object initialization."""
    ledger_id = "some_ledger"
    body = {"state": "v"}
    state = State(ledger_id, body)
    assert state.ledger_id == ledger_id
    assert state.body == body
    assert str(state) == f"State: ledger_id={ledger_id}, body={body}"
    assert state == state


def test_state_encode_decode():
    """Test encoding and decoding of state."""

    class StateProtobufObject:
        state_bytes = b""

    ledger_id = "some_ledger"
    body = {"state": "v"}
    state = State(ledger_id, body)
    State.encode(StateProtobufObject, state)
    recovered_state = State.decode(StateProtobufObject)
    assert state == recovered_state


def test_init_transaction_digest():
    """Test the transaction_digest object initialization."""
    ledger_id = "some_ledger"
    body = "digest"
    td = TransactionDigest(ledger_id, body)
    assert td.ledger_id == ledger_id
    assert td.body == body
    assert str(td) == "TransactionDigest: ledger_id={}, body={}".format(ledger_id, body)
    assert td == td


def test_transaction_digest_encode_decode():
    """Test encoding and decoding of transaction_digest."""

    class TransactionDigestProtobufObject:
        transaction_digest_bytes = b""

    ledger_id = "some_ledger"
    body = "digest"
    td = TransactionDigest(ledger_id, body)
    TransactionDigest.encode(TransactionDigestProtobufObject, td)
    recovered_td = TransactionDigest.decode(TransactionDigestProtobufObject)
    assert td == recovered_td
