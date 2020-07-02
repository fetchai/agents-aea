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

import pickle  # nosec
from typing import Any, Dict, Optional

Address = str


class RawTransaction:
    """This class represents an instance of RawTransaction."""

    def __init__(
        self, ledger_id: str, body: Any,
    ):
        """Initialise an instance of RawTransaction."""
        self._ledger_id = ledger_id
        self._body = body
        self._check_consistency()

    def _check_consistency(self) -> None:
        """Check consistency of the object."""
        assert isinstance(self._ledger_id, str), "ledger_id must be str"
        assert self._body is not None, "body must not be None"

    @property
    def ledger_id(self) -> str:
        """Get the id of the ledger on which the terms are to be settled."""
        return self._ledger_id

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
        raw_transaction = pickle.loads(  # nosec
            raw_transaction_protobuf_object.raw_transaction_bytes
        )
        return raw_transaction

    def __eq__(self, other):
        return (
            isinstance(other, RawTransaction)
            and self.ledger_id == other.ledger_id
            and self.body == other.body
        )

    def __str__(self):
        return "RawTransaction: ledger_id={}, body={}".format(
            self.ledger_id, self.body,
        )


class RawMessage:
    """This class represents an instance of RawMessage."""

    def __init__(
        self, ledger_id: str, body: bytes, is_deprecated_mode: bool = False,
    ):
        """Initialise an instance of RawMessage."""
        self._ledger_id = ledger_id
        self._body = body
        self._is_deprecated_mode = is_deprecated_mode
        self._check_consistency()

    def _check_consistency(self) -> None:
        """Check consistency of the object."""
        assert isinstance(self._ledger_id, str), "ledger_id must be str"
        assert self._body is not None, "body must not be None"
        assert isinstance(
            self._is_deprecated_mode, bool
        ), "is_deprecated_mode must be bool"

    @property
    def ledger_id(self) -> str:
        """Get the id of the ledger on which the terms are to be settled."""
        return self._ledger_id

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
        raw_message_protobuf_object.raw_message_bytes = raw_message_bytes

    @classmethod
    def decode(cls, raw_message_protobuf_object) -> "RawMessage":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class must be created that matches the protocol buffer object in the 'raw_message_protobuf_object' argument.

        :param raw_message_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'raw_message_protobuf_object' argument.
        """
        raw_message = pickle.loads(  # nosec
            raw_message_protobuf_object.raw_message_bytes
        )
        return raw_message

    def __eq__(self, other):
        return (
            isinstance(other, RawMessage)
            and self.ledger_id == other.ledger_id
            and self.body == other.body
            and self.is_deprecated_mode == other.is_deprecated_mode
        )

    def __str__(self):
        return "RawMessage: ledger_id={}, body={}, is_deprecated_mode={}".format(
            self.ledger_id, self.body, self.is_deprecated_mode,
        )


class SignedTransaction:
    """This class represents an instance of SignedTransaction."""

    def __init__(
        self, ledger_id: str, body: Any,
    ):
        """Initialise an instance of SignedTransaction."""
        self._ledger_id = ledger_id
        self._body = body
        self._check_consistency()

    def _check_consistency(self) -> None:
        """Check consistency of the object."""
        assert isinstance(self._ledger_id, str), "ledger_id must be str"
        assert self._body is not None, "body must not be None"

    @property
    def ledger_id(self) -> str:
        """Get the id of the ledger on which the terms are to be settled."""
        return self._ledger_id

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
        signed_transaction = pickle.loads(  # nosec
            signed_transaction_protobuf_object.signed_transaction_bytes
        )
        return signed_transaction

    def __eq__(self, other):
        return (
            isinstance(other, SignedTransaction)
            and self.ledger_id == other.ledger_id
            and self.body == other.body
        )

    def __str__(self):
        return "SignedTransaction: ledger_id={}, body={}".format(
            self.ledger_id, self.body,
        )


class SignedMessage:
    """This class represents an instance of RawMessage."""

    def __init__(
        self, ledger_id: str, body: str, is_deprecated_mode: bool = False,
    ):
        """Initialise an instance of SignedMessage."""
        self._ledger_id = ledger_id
        self._body = body
        self._is_deprecated_mode = is_deprecated_mode
        self._check_consistency()

    def _check_consistency(self) -> None:
        """Check consistency of the object."""
        assert isinstance(self._ledger_id, str), "ledger_id must be str"
        assert isinstance(self._body, str), "body must be string"
        assert isinstance(
            self._is_deprecated_mode, bool
        ), "is_deprecated_mode must be bool"

    @property
    def ledger_id(self) -> str:
        """Get the id of the ledger on which the terms are to be settled."""
        return self._ledger_id

    @property
    def body(self):
        """Get the body."""
        return self._body

    @property
    def is_deprecated_mode(self):
        """Get the is_deprecated_mode."""
        return self._is_deprecated_mode

    @staticmethod
    def encode(
        signed_message_protobuf_object, signed_message_object: "SignedMessage"
    ) -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the signed_message_protobuf_object argument must be matched with the instance of this class in the 'signed_message_object' argument.

        :param signed_message_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param signed_message_object: an instance of this class to be encoded in the protocol buffer object.
        :return: None
        """
        signed_message_bytes = pickle.dumps(signed_message_object)  # nosec
        signed_message_protobuf_object.signed_message_bytes = signed_message_bytes

    @classmethod
    def decode(cls, signed_message_protobuf_object) -> "SignedMessage":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class must be created that matches the protocol buffer object in the 'signed_message_protobuf_object' argument.

        :param signed_message_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'signed_message_protobuf_object' argument.
        """
        signed_message = pickle.loads(  # nosec
            signed_message_protobuf_object.signed_message_bytes
        )
        return signed_message

    def __eq__(self, other):
        return (
            isinstance(other, SignedMessage)
            and self.ledger_id == other.ledger_id
            and self.body == other.body
            and self.is_deprecated_mode == other.is_deprecated_mode
        )

    def __str__(self):
        return "SignedMessage: ledger_id={}, body={}, is_deprecated_mode={}".format(
            self.ledger_id, self.body, self.is_deprecated_mode,
        )


class State:
    """This class represents an instance of State."""

    def __init__(self, ledger_id: str, body: bytes):
        """Initialise an instance of State."""
        self._ledger_id = ledger_id
        self._body = body
        self._check_consistency()

    def _check_consistency(self) -> None:
        """Check consistency of the object."""
        assert isinstance(self._ledger_id, str), "ledger_id must be str"
        assert self._body is not None, "body must not be None"

    @property
    def ledger_id(self) -> str:
        """Get the id of the ledger on which the terms are to be settled."""
        return self._ledger_id

    @property
    def body(self):
        """Get the body."""
        return self._body

    @staticmethod
    def encode(state_protobuf_object, state_object: "State") -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the state_protobuf_object argument must be matched with the instance of this class in the 'state_object' argument.

        :param state_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param state_object: an instance of this class to be encoded in the protocol buffer object.
        :return: None
        """
        state_bytes = pickle.dumps(state_object)  # nosec
        state_protobuf_object.state_bytes = state_bytes

    @classmethod
    def decode(cls, state_protobuf_object) -> "State":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class must be created that matches the protocol buffer object in the 'state_protobuf_object' argument.

        :param state_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'state_protobuf_object' argument.
        """
        state = pickle.loads(state_protobuf_object.state_bytes)  # nosec
        return state

    def __eq__(self, other):
        return (
            isinstance(other, State)
            and self.ledger_id == other.ledger_id
            and self.body == other.body
        )

    def __str__(self):
        return "State: ledger_id={}, body={}".format(self.ledger_id, self.body)


class Terms:
    """Class to represent the terms of a multi-currency & multi-token ledger transaction."""

    def __init__(
        self,
        ledger_id: str,
        sender_address: Address,
        counterparty_address: Address,
        amount_by_currency_id: Dict[str, int],
        quantities_by_good_id: Dict[str, int],
        is_sender_payable_tx_fee: bool,
        nonce: str,
        fee_by_currency_id: Optional[Dict[str, int]] = None,
        **kwargs,
    ):
        """
        Instantiate terms.

        :param ledger_id: the ledger on which the terms are to be settled.
        :param sender_address: the sender address of the transaction.
        :param counterparty_address: the counterparty address of the transaction.
        :param amount_by_currency_id: the amount by the currency of the transaction.
        :param quantities_by_good_id: a map from good id to the quantity of that good involved in the transaction.
        :param is_sender_payable_tx_fee: whether the sender or counterparty pays the tx fee.
        :param nonce: nonce to be included in transaction to discriminate otherwise identical transactions.
        :param fee_by_currency_id: the fee associated with the transaction.
        """
        self._ledger_id = ledger_id
        self._sender_address = sender_address
        self._counterparty_address = counterparty_address
        self._amount_by_currency_id = amount_by_currency_id
        self._quantities_by_good_id = quantities_by_good_id
        self._is_sender_payable_tx_fee = is_sender_payable_tx_fee
        self._nonce = nonce
        self._fee_by_currency_id = fee_by_currency_id
        self._kwargs = kwargs if kwargs is not None else {}
        self._check_consistency()

    def _check_consistency(self) -> None:
        """Check consistency of the object."""
        assert isinstance(self._ledger_id, str), "ledger_id must be str"
        assert isinstance(self._sender_address, str), "sender_address must be str"
        assert isinstance(
            self._counterparty_address, str
        ), "counterparty_address must be str"
        assert isinstance(self._amount_by_currency_id, dict) and all(
            [
                isinstance(key, str) and isinstance(value, int)
                for key, value in self._amount_by_currency_id.items()
            ]
        ), "amount_by_currency_id must be a dictionary with str keys and int values."
        assert isinstance(self._quantities_by_good_id, dict) and all(
            [
                isinstance(key, str) and isinstance(value, int)
                for key, value in self._quantities_by_good_id.items()
            ]
        ), "quantities_by_good_id must be a dictionary with str keys and int values."
        pos_amounts = all(
            [amount >= 0 for amount in self._amount_by_currency_id.values()]
        )
        neg_amounts = all(
            [amount <= 0 for amount in self._amount_by_currency_id.values()]
        )
        pos_quantities = all(
            [quantity >= 0 for quantity in self._quantities_by_good_id.values()]
        )
        neg_quantities = all(
            [quantity <= 0 for quantity in self._quantities_by_good_id.values()]
        )
        assert (pos_amounts and neg_quantities) or (
            neg_amounts and pos_quantities
        ), "quantities and amounts do not constitute valid terms."
        assert isinstance(
            self._is_sender_payable_tx_fee, bool
        ), "is_sender_payable_tx_fee must be bool"
        assert isinstance(self._nonce, str), "nonce must be str"
        assert self._fee_by_currency_id is None or (
            isinstance(self._fee_by_currency_id, dict)
            and all(
                [
                    isinstance(key, str) and isinstance(value, int)
                    for key, value in self._fee_by_currency_id.items()
                ]
            )
        ), "fee must be None or Dict[str, int]"

    @property
    def ledger_id(self) -> str:
        """Get the id of the ledger on which the terms are to be settled."""
        return self._ledger_id

    @property
    def sender_address(self) -> Address:
        """Get the sender address."""
        return self._sender_address

    @property
    def counterparty_address(self) -> Address:
        """Get the counterparty address."""
        return self._counterparty_address

    @counterparty_address.setter
    def counterparty_address(self, counterparty_address: Address) -> None:
        """Set the counterparty address."""
        assert isinstance(counterparty_address, str), "counterparty_address must be str"
        self._counterparty_address = counterparty_address

    @property
    def amount_by_currency_id(self) -> Dict[str, int]:
        """Get the amount by currency id."""
        return self._amount_by_currency_id

    @property
    def sender_payable_amount(self) -> int:
        """Get the amount the sender must pay."""
        assert (
            len(self._amount_by_currency_id) == 1
        ), "More than one currency id, cannot get amount."
        return -next(iter(self._amount_by_currency_id.values()))

    @property
    def counterparty_payable_amount(self) -> int:
        """Get the amount the counterparty must pay."""
        assert (
            len(self._amount_by_currency_id) == 1
        ), "More than one currency id, cannot get amount."
        return next(iter(self._amount_by_currency_id.values()))

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

    @property
    def has_fee(self) -> bool:
        """Check if fee is set."""
        return self._fee_by_currency_id is not None

    @property
    def fee(self) -> int:
        """Get the fee."""
        assert self._fee_by_currency_id is not None, "fee_by_currency_id not set."
        assert (
            len(self._fee_by_currency_id) == 1
        ), "More than one currency id, cannot get fee."
        return next(iter(self._fee_by_currency_id.values()))

    @property
    def fee_by_currency_id(self) -> Dict[str, int]:
        """Get fee by currency."""
        assert self._fee_by_currency_id is not None, "fee_by_currency_id not set."
        return self._fee_by_currency_id

    @property
    def kwargs(self) -> Dict[str, Any]:
        """Get the kwargs."""
        return self._kwargs

    @staticmethod
    def encode(terms_protobuf_object, terms_object: "Terms") -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the terms_protobuf_object argument must be matched with the instance of this class in the 'terms_object' argument.

        :param terms_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param terms_object: an instance of this class to be encoded in the protocol buffer object.
        :return: None
        """
        terms_bytes = pickle.dumps(terms_object)  # nosec
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
            and self.ledger_id == other.ledger_id
            and self.sender_address == other.sender_address
            and self.counterparty_address == other.counterparty_address
            and self.amount_by_currency_id == other.amount_by_currency_id
            and self.quantities_by_good_id == other.quantities_by_good_id
            and self.is_sender_payable_tx_fee == other.is_sender_payable_tx_fee
            and self.nonce == other.nonce
            and self.kwargs == other.kwargs
            and self.fee == other.fee
            if (self.has_fee and other.has_fee)
            else self.has_fee == other.has_fee
        )

    def __str__(self):
        return "Terms: ledger_id={}, sender_address={}, counterparty_address={}, amount_by_currency_id={}, quantities_by_good_id={}, is_sender_payable_tx_fee={}, nonce={}, fee_by_currency_id={}, kwargs={}".format(
            self.ledger_id,
            self.sender_address,
            self.counterparty_address,
            self.amount_by_currency_id,
            self.quantities_by_good_id,
            self.is_sender_payable_tx_fee,
            self.nonce,
            self._fee_by_currency_id,
            self.kwargs,
        )


class TransactionDigest:
    """This class represents an instance of TransactionDigest."""

    def __init__(self, ledger_id: str, body: Any):
        """Initialise an instance of TransactionDigest."""
        self._ledger_id = ledger_id
        self._body = body
        self._check_consistency()

    def _check_consistency(self) -> None:
        """Check consistency of the object."""
        assert isinstance(self._ledger_id, str), "ledger_id must be str"
        assert self._body is not None, "body must not be None"

    @property
    def ledger_id(self) -> str:
        """Get the id of the ledger on which the terms are to be settled."""
        return self._ledger_id

    @property
    def body(self) -> Any:
        """Get the receipt."""
        return self._body

    @staticmethod
    def encode(
        transaction_digest_protobuf_object,
        transaction_digest_object: "TransactionDigest",
    ) -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the transaction_digest_protobuf_object argument must be matched with the instance of this class in the 'transaction_digest_object' argument.

        :param transaction_digest_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param transaction_digest_object: an instance of this class to be encoded in the protocol buffer object.
        :return: None
        """
        transaction_digest_bytes = pickle.dumps(transaction_digest_object)  # nosec
        transaction_digest_protobuf_object.transaction_digest_bytes = (
            transaction_digest_bytes
        )

    @classmethod
    def decode(cls, transaction_digest_protobuf_object) -> "TransactionDigest":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class must be created that matches the protocol buffer object in the 'transaction_digest_protobuf_object' argument.

        :param transaction_digest_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'transaction_digest_protobuf_object' argument.
        """
        transaction_digest = pickle.loads(  # nosec
            transaction_digest_protobuf_object.transaction_digest_bytes
        )
        return transaction_digest

    def __eq__(self, other):
        return (
            isinstance(other, TransactionDigest)
            and self.ledger_id == other.ledger_id
            and self.body == other.body
        )

    def __str__(self):
        return "TransactionDigest: ledger_id={}, body={}".format(
            self.ledger_id, self.body
        )


class TransactionReceipt:
    """This class represents an instance of TransactionReceipt."""

    def __init__(self, ledger_id: str, receipt: Any, transaction: Any):
        """Initialise an instance of TransactionReceipt."""
        self._ledger_id = ledger_id
        self._receipt = receipt
        self._transaction = transaction
        self._check_consistency()

    def _check_consistency(self) -> None:
        """Check consistency of the object."""
        assert isinstance(self._ledger_id, str), "ledger_id must be str"
        assert self._receipt is not None, "receipt must not be None"
        assert self._transaction is not None, "transaction must not be None"

    @property
    def ledger_id(self) -> str:
        """Get the id of the ledger on which the terms are to be settled."""
        return self._ledger_id

    @property
    def receipt(self) -> Any:
        """Get the receipt."""
        return self._receipt

    @property
    def transaction(self) -> Any:
        """Get the transaction."""
        return self._transaction

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
        transaction_receipt = pickle.loads(  # nosec
            transaction_receipt_protobuf_object.transaction_receipt_bytes
        )
        return transaction_receipt

    def __eq__(self, other):
        return (
            isinstance(other, TransactionReceipt)
            and self.ledger_id == other.ledger_id
            and self.receipt == other.receipt
            and self.transaction == other.transaction
        )

    def __str__(self):
        return "TransactionReceipt: ledger_id={}, receipt={}, transaction={}".format(
            self.ledger_id, self.receipt, self.transaction
        )
