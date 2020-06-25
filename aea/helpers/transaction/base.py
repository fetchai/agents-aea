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

import pickle  #  nosec
from typing import Any, Dict

Address = str


class RawTransaction:
    """This class represents an instance of RawTransaction."""

    def __init__(
        self, body: Any,
    ):
        """Initialise an instance of RawTransaction."""
        self._body = body

    @property
    def body(self):
        """Get the body."""
        return self._body

    @staticmethod
    def encode(
        raw_transaction_protobuf_object, raw_transaction_object: "RawTransaction"
    ) -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the raw_transaction_protobuf_object argument must be matched with the instance of this class in the 'raw_transaction_object' argument.

        :param raw_transaction_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param raw_transaction_object: an instance of this class to be encoded in the protocol buffer object.
        :return: None
        """
        raw_transaction_bytes = pickle.dumps(raw_transaction_object)  # nosec
        raw_transaction_protobuf_object.raw_transaction_bytes = raw_transaction_bytes

    @classmethod
    def decode(cls, raw_transaction_protobuf_object) -> "RawTransaction":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class must be created that matches the protocol buffer object in the 'raw_transaction_protobuf_object' argument.

        :param raw_transaction_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'raw_transaction_protobuf_object' argument.
        """
        raw_transaction = pickle.loads(
            raw_transaction_protobuf_object.raw_transaction_bytes
        )  # nosec
        return raw_transaction

    def __eq__(self, other):
        return isinstance(other, RawTransaction) and self.body == other.body


class RawMessage:
    """This class represents an instance of RawMessage."""

    def __init__(
        self, body: bytes, is_deprecated_mode: bool = False,
    ):
        """Initialise an instance of RawMessage."""
        self._body = body
        self._is_deprecated_mode = is_deprecated_mode

    @property
    def body(self):
        """Get the body."""
        return self._body

    @property
    def is_deprecated_mode(self):
        """Get the is_deprecated_mode."""
        return self._is_deprecated_mode

    @staticmethod
    def encode(raw_message_protobuf_object, raw_message_object: "RawMessage") -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the raw_message_protobuf_object argument must be matched with the instance of this class in the 'raw_message_object' argument.

        :param raw_message_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param raw_message_object: an instance of this class to be encoded in the protocol buffer object.
        :return: None
        """
        raw_message_bytes = pickle.dumps(raw_message_object)  # nosec
        raw_message_protobuf_object.raw_tmessage_bytes = raw_message_bytes

    @classmethod
    def decode(cls, raw_message_protobuf_object) -> "RawMessage":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class must be created that matches the protocol buffer object in the 'raw_message_protobuf_object' argument.

        :param raw_message_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'raw_message_protobuf_object' argument.
        """
        raw_message = pickle.loads(
            raw_message_protobuf_object.raw_message_bytes
        )  # nosec
        return raw_message

    def __eq__(self, other):
        return (
            isinstance(other, RawMessage)
            and self.body == other.body
            and self.is_deprecated_mode == other.is_deprecated_mode
        )


class SignedTransaction:
    """This class represents an instance of SignedTransaction."""

    def __init__(
        self, body: Any,
    ):
        """Initialise an instance of SignedTransaction."""
        self._body = body

    @property
    def body(self):
        """Get the body."""
        return self._body

    @staticmethod
    def encode(
        signed_transaction_protobuf_object,
        signed_transaction_object: "SignedTransaction",
    ) -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the signed_transaction_protobuf_object argument must be matched with the instance of this class in the 'signed_transaction_object' argument.

        :param signed_transaction_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param signed_transaction_object: an instance of this class to be encoded in the protocol buffer object.
        :return: None
        """
        signed_transaction_bytes = pickle.dumps(signed_transaction_object)  # nosec
        signed_transaction_protobuf_object.signed_transaction_bytes = (
            signed_transaction_bytes
        )

    @classmethod
    def decode(cls, signed_transaction_protobuf_object) -> "SignedTransaction":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class must be created that matches the protocol buffer object in the 'signed_transaction_protobuf_object' argument.

        :param signed_transaction_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'signed_transaction_protobuf_object' argument.
        """
        signed_transaction = pickle.loads(
            signed_transaction_protobuf_object.signed_transaction_bytes
        )  # nosec
        return signed_transaction

    def __eq__(self, other):
        return isinstance(other, SignedTransaction) and self.body == other.body


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

    @staticmethod
    def encode(terms_protobuf_object, terms_object: "Terms") -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the terms_protobuf_object argument must be matched with the instance of this class in the 'terms_object' argument.

        :param terms_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param terms_object: an instance of this class to be encoded in the protocol buffer object.
        :return: None
        """
        terms_bytes = pickle.dumps(terms_protobuf_object)  # nosec
        terms_protobuf_object.terms_bytes = terms_bytes

    @classmethod
    def decode(cls, terms_protobuf_object) -> "Terms":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class must be created that matches the protocol buffer object in the 'terms_protobuf_object' argument.

        :param terms_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'terms_protobuf_object' argument.
        """
        terms = pickle.loads(terms_protobuf_object.terms_bytes)  # nosec
        return terms

    def __eq__(self, other):
        return (
            isinstance(other, Terms)
            and self.sender_addr == other.sender_addr
            and self.counterparty_addr == other.counterparty_addr
            and self.amount_by_currency_id == other.amount_by_currency_id
            and self.quantities_by_good_id == other.quantities_by_good_id
            and self.is_sender_payable_tx_fee == other.is_sender_payable_tx_fee
            and self.nonce == other.nonce
        )


class TransactionReceipt:
    """This class represents an instance of TransactionReceipt."""

    def __init__(
        self, body: Any,
    ):
        """Initialise an instance of TransactionReceipt."""
        self._body = body

    @property
    def body(self):
        """Get the body."""
        return self._body

    @staticmethod
    def encode(
        transaction_receipt_protobuf_object,
        transaction_receipt_object: "TransactionReceipt",
    ) -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the transaction_receipt_protobuf_object argument must be matched with the instance of this class in the 'transaction_receipt_object' argument.

        :param transaction_receipt_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param transaction_receipt_object: an instance of this class to be encoded in the protocol buffer object.
        :return: None
        """
        transaction_receipt_bytes = pickle.dumps(transaction_receipt_object)  # nosec
        transaction_receipt_protobuf_object.transaction_receipt_bytes = (
            transaction_receipt_bytes
        )

    @classmethod
    def decode(cls, transaction_receipt_protobuf_object) -> "TransactionReceipt":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class must be created that matches the protocol buffer object in the 'transaction_receipt_protobuf_object' argument.

        :param transaction_receipt_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'transaction_receipt_protobuf_object' argument.
        """
        transaction_receipt = pickle.loads(
            transaction_receipt_protobuf_object.transaction_receipt_bytes
        )  # nosec
        return transaction_receipt

    def __eq__(self, other):
        return isinstance(other, TransactionReceipt) and self.body == other.body
