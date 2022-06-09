# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 Valory AG
#   Copyright 2018-2021 Fetch.AI Limited
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

import collections
import copy
from typing import Any, Dict, List, Optional, Tuple

from aea.common import JSONLike
from aea.crypto.ledger_apis import LedgerApis
from aea.exceptions import enforce
from aea.helpers.serializers import DictProtobufStructSerializer


Address = str


class RawTransaction:
    """This class represents an instance of RawTransaction."""

    __slots__ = ("_ledger_id", "_body")

    def __init__(
        self,
        ledger_id: str,
        body: JSONLike,
    ) -> None:
        """Initialise an instance of RawTransaction."""
        self._ledger_id = ledger_id
        self._body = body
        self._check_consistency()

    def _check_consistency(self) -> None:
        """Check consistency of the object."""
        enforce(isinstance(self._ledger_id, str), "ledger_id must be str")
        enforce(isinstance(self._body, dict), "body must not be JSONLike")

    @property
    def ledger_id(self) -> str:
        """Get the id of the ledger on which the terms are to be settled."""
        return self._ledger_id

    @property
    def body(self) -> JSONLike:
        """Get the body."""
        return self._body

    @staticmethod
    def encode(
        raw_transaction_protobuf_object: Any, raw_transaction_object: "RawTransaction"
    ) -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the raw_transaction_protobuf_object argument must be matched with the instance of this class in the 'raw_transaction_object' argument.

        :param raw_transaction_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param raw_transaction_object: an instance of this class to be encoded in the protocol buffer object.
        """

        raw_transaction_dict = {
            "ledger_id": raw_transaction_object.ledger_id,
            "body": raw_transaction_object.body,
        }

        raw_transaction_protobuf_object.raw_transaction = (
            DictProtobufStructSerializer.encode(raw_transaction_dict)
        )

    @classmethod
    def decode(cls, raw_transaction_protobuf_object: Any) -> "RawTransaction":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class must be created that matches the protocol buffer object in the 'raw_transaction_protobuf_object' argument.

        :param raw_transaction_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'raw_transaction_protobuf_object' argument.
        """
        raw_transaction_dict = DictProtobufStructSerializer.decode(
            raw_transaction_protobuf_object.raw_transaction
        )
        return cls(raw_transaction_dict["ledger_id"], raw_transaction_dict["body"])

    def __eq__(self, other: Any) -> bool:
        """Check equality."""
        return (
            isinstance(other, RawTransaction)
            and self.ledger_id == other.ledger_id
            and self.body == other.body
        )

    def __str__(self) -> str:
        """Get string representation."""
        return "RawTransaction: ledger_id={}, body={}".format(
            self.ledger_id,
            self.body,
        )


class RawMessage:
    """This class represents an instance of RawMessage."""

    __slots__ = ("_ledger_id", "_body", "_is_deprecated_mode")

    def __init__(
        self,
        ledger_id: str,
        body: bytes,
        is_deprecated_mode: bool = False,
    ) -> None:
        """Initialise an instance of RawMessage."""
        self._ledger_id = ledger_id
        self._body = body
        self._is_deprecated_mode = is_deprecated_mode
        self._check_consistency()

    def _check_consistency(self) -> None:
        """Check consistency of the object."""
        enforce(isinstance(self._ledger_id, str), "ledger_id must be str")
        enforce(isinstance(self._body, bytes), "body must not be bytes")
        enforce(
            isinstance(self._is_deprecated_mode, bool),
            "is_deprecated_mode must be bool",
        )

    @property
    def ledger_id(self) -> str:
        """Get the id of the ledger on which the terms are to be settled."""
        return self._ledger_id

    @property
    def body(self) -> bytes:
        """Get the body."""
        return self._body

    @property
    def is_deprecated_mode(self) -> bool:
        """Get the is_deprecated_mode."""
        return self._is_deprecated_mode

    @staticmethod
    def encode(
        raw_message_protobuf_object: Any, raw_message_object: "RawMessage"
    ) -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the raw_message_protobuf_object argument must be matched with the instance of this class in the 'raw_message_object' argument.

        :param raw_message_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param raw_message_object: an instance of this class to be encoded in the protocol buffer object.
        """
        raw_message_dict = {
            "ledger_id": raw_message_object.ledger_id,
            "body": raw_message_object.body,
            "is_deprecated_mode": raw_message_object.is_deprecated_mode,
        }

        raw_message_protobuf_object.raw_message = DictProtobufStructSerializer.encode(
            raw_message_dict
        )

    @classmethod
    def decode(cls, raw_message_protobuf_object: Any) -> "RawMessage":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class must be created that matches the protocol buffer object in the 'raw_message_protobuf_object' argument.

        :param raw_message_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'raw_message_protobuf_object' argument.
        """
        raw_message_dict = DictProtobufStructSerializer.decode(
            raw_message_protobuf_object.raw_message
        )
        return cls(
            raw_message_dict["ledger_id"],
            raw_message_dict["body"],
            raw_message_dict["is_deprecated_mode"],
        )

    def __eq__(self, other: Any) -> bool:
        """Check equality."""
        return (
            isinstance(other, RawMessage)
            and self.ledger_id == other.ledger_id
            and self.body == other.body
            and self.is_deprecated_mode == other.is_deprecated_mode
        )

    def __str__(self) -> str:
        """Get string representation."""
        return "RawMessage: ledger_id={}, body={!r}, is_deprecated_mode={}".format(
            self.ledger_id,
            self.body,
            self.is_deprecated_mode,
        )


class SignedTransaction:
    """This class represents an instance of SignedTransaction."""

    __slots__ = ("_ledger_id", "_body")

    def __init__(
        self,
        ledger_id: str,
        body: JSONLike,
    ) -> None:
        """Initialise an instance of SignedTransaction."""
        self._ledger_id = ledger_id
        self._body = body
        self._check_consistency()

    def _check_consistency(self) -> None:
        """Check consistency of the object."""
        enforce(isinstance(self._ledger_id, str), "ledger_id must be str")
        enforce(isinstance(self._body, dict), "body must not JSONLike")

    @property
    def ledger_id(self) -> str:
        """Get the id of the ledger on which the terms are to be settled."""
        return self._ledger_id

    @property
    def body(self) -> JSONLike:
        """Get the body."""
        return self._body

    @staticmethod
    def encode(
        signed_transaction_protobuf_object: Any,
        signed_transaction_object: "SignedTransaction",
    ) -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the signed_transaction_protobuf_object argument must be matched with the instance of this class in the 'signed_transaction_object' argument.

        :param signed_transaction_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param signed_transaction_object: an instance of this class to be encoded in the protocol buffer object.
        """
        signed_transaction_dict = {
            "ledger_id": signed_transaction_object.ledger_id,
            "body": signed_transaction_object.body,
        }

        signed_transaction_protobuf_object.signed_transaction = (
            DictProtobufStructSerializer.encode(signed_transaction_dict)
        )

    @classmethod
    def decode(cls, signed_transaction_protobuf_object: Any) -> "SignedTransaction":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class must be created that matches the protocol buffer object in the 'signed_transaction_protobuf_object' argument.

        :param signed_transaction_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'signed_transaction_protobuf_object' argument.
        """
        signed_transaction_dict = DictProtobufStructSerializer.decode(
            signed_transaction_protobuf_object.signed_transaction
        )
        return cls(
            signed_transaction_dict["ledger_id"], signed_transaction_dict["body"]
        )

    def __eq__(self, other: Any) -> bool:
        """Check equality."""
        return (
            isinstance(other, SignedTransaction)
            and self.ledger_id == other.ledger_id
            and self.body == other.body
        )

    def __str__(self) -> str:
        """Get string representation."""
        return "SignedTransaction: ledger_id={}, body={}".format(
            self.ledger_id,
            self.body,
        )


class SignedMessage:
    """This class represents an instance of RawMessage."""

    __slots__ = ("_ledger_id", "_body", "_is_deprecated_mode")

    def __init__(
        self,
        ledger_id: str,
        body: str,
        is_deprecated_mode: bool = False,
    ) -> None:
        """Initialise an instance of SignedMessage."""
        self._ledger_id = ledger_id
        self._body = body
        self._is_deprecated_mode = is_deprecated_mode
        self._check_consistency()

    def _check_consistency(self) -> None:
        """Check consistency of the object."""
        enforce(isinstance(self._ledger_id, str), "ledger_id must be str")
        enforce(isinstance(self._body, str), "body must be string")
        enforce(
            isinstance(self._is_deprecated_mode, bool),
            "is_deprecated_mode must be bool",
        )

    @property
    def ledger_id(self) -> str:
        """Get the id of the ledger on which the terms are to be settled."""
        return self._ledger_id

    @property
    def body(self) -> str:
        """Get the body."""
        return self._body

    @property
    def is_deprecated_mode(self) -> bool:
        """Get the is_deprecated_mode."""
        return self._is_deprecated_mode

    @staticmethod
    def encode(
        signed_message_protobuf_object: Any, signed_message_object: "SignedMessage"
    ) -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the signed_message_protobuf_object argument must be matched with the instance of this class in the 'signed_message_object' argument.

        :param signed_message_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param signed_message_object: an instance of this class to be encoded in the protocol buffer object.
        """
        signed_message_dict = {
            "ledger_id": signed_message_object.ledger_id,
            "body": signed_message_object.body,
            "is_deprecated_mode": signed_message_object.is_deprecated_mode,
        }

        signed_message_protobuf_object.signed_message = (
            DictProtobufStructSerializer.encode(signed_message_dict)
        )

    @classmethod
    def decode(cls, signed_message_protobuf_object: Any) -> "SignedMessage":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class must be created that matches the protocol buffer object in the 'signed_message_protobuf_object' argument.

        :param signed_message_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'signed_message_protobuf_object' argument.
        """
        signed_message_dict = DictProtobufStructSerializer.decode(
            signed_message_protobuf_object.signed_message
        )
        return cls(
            signed_message_dict["ledger_id"],
            signed_message_dict["body"],
            signed_message_dict["is_deprecated_mode"],
        )

    def __eq__(self, other: Any) -> bool:
        """Check equality."""
        return (
            isinstance(other, SignedMessage)
            and self.ledger_id == other.ledger_id
            and self.body == other.body
            and self.is_deprecated_mode == other.is_deprecated_mode
        )

    def __str__(self) -> str:
        """Get string representation."""
        return "SignedMessage: ledger_id={}, body={}, is_deprecated_mode={}".format(
            self.ledger_id,
            self.body,
            self.is_deprecated_mode,
        )


class State:
    """This class represents an instance of State."""

    __slots__ = ("_ledger_id", "_body")

    def __init__(self, ledger_id: str, body: JSONLike) -> None:
        """Initialise an instance of State."""
        self._ledger_id = ledger_id
        self._body = body
        self._check_consistency()

    def _check_consistency(self) -> None:
        """Check consistency of the object."""
        enforce(isinstance(self._ledger_id, str), "ledger_id must be str")
        enforce(isinstance(self._body, dict), "body must be dict")

    @property
    def ledger_id(self) -> str:
        """Get the id of the ledger on which the terms are to be settled."""
        return self._ledger_id

    @property
    def body(self) -> JSONLike:
        """Get the body."""
        return self._body

    @staticmethod
    def encode(state_protobuf_object: Any, state_object: "State") -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the state_protobuf_object argument must be matched with the instance of this class in the 'state_object' argument.

        :param state_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param state_object: an instance of this class to be encoded in the protocol buffer object.
        """
        state_dict = {
            "ledger_id": state_object.ledger_id,
            "body": state_object.body,
        }

        state_protobuf_object.state = DictProtobufStructSerializer.encode(state_dict)

    @classmethod
    def decode(cls, state_protobuf_object: Any) -> "State":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class must be created that matches the protocol buffer object in the 'state_protobuf_object' argument.

        :param state_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'state_protobuf_object' argument.
        """
        state_dict = DictProtobufStructSerializer.decode(state_protobuf_object.state)
        return cls(state_dict["ledger_id"], state_dict["body"])

    def __eq__(self, other: Any) -> bool:
        """Check equality."""
        return (
            isinstance(other, State)
            and self.ledger_id == other.ledger_id
            and self.body == other.body
        )

    def __str__(self) -> str:
        """Get string representation."""
        return "State: ledger_id={}, body={}".format(self.ledger_id, self.body)


class Terms:
    """Class to represent the terms of a multi-currency & multi-token ledger transaction."""

    __slots__ = (
        "_ledger_id",
        "_sender_address",
        "_counterparty_address",
        "_amount_by_currency_id",
        "_quantities_by_good_id",
        "_is_sender_payable_tx_fee",
        "_nonce",
        "_fee_by_currency_id",
        "_is_strict",
        "_kwargs",
        "_good_ids",
        "_sender_supplied_quantities",
        "_counterparty_supplied_quantities",
        "_sender_hash",
        "_counterparty_hash",
    )

    def __init__(
        self,
        ledger_id: str,
        sender_address: Address,
        counterparty_address: Address,
        amount_by_currency_id: Dict[str, int],
        quantities_by_good_id: Dict[str, int],
        nonce: str,
        is_sender_payable_tx_fee: bool = True,
        fee_by_currency_id: Optional[Dict[str, int]] = None,
        is_strict: bool = False,
        **kwargs: Any,
    ) -> None:
        """
        Instantiate terms of a transaction.

        :param ledger_id: the ledger on which the terms are to be settled.
        :param sender_address: the sender address of the transaction.
        :param counterparty_address: the counterparty address of the transaction.
        :param amount_by_currency_id: the amount by the currency of the transaction.
        :param quantities_by_good_id: a map from good id to the quantity of that good involved in the transaction.
        :param nonce: nonce to be included in transaction to discriminate otherwise identical transactions.
        :param is_sender_payable_tx_fee: whether the sender or counterparty pays the tx fee.
        :param fee_by_currency_id: the fee associated with the transaction.
        :param is_strict: whether or not terms must have quantities and amounts of opposite signs.
        :param kwargs: keyword arguments
        """
        self._ledger_id = ledger_id
        self._sender_address = sender_address
        self._counterparty_address = counterparty_address
        self._amount_by_currency_id = amount_by_currency_id
        self._quantities_by_good_id = quantities_by_good_id
        self._is_sender_payable_tx_fee = is_sender_payable_tx_fee
        self._nonce = nonce
        self._fee_by_currency_id = (
            fee_by_currency_id if fee_by_currency_id is not None else {}
        )
        self._is_strict = is_strict
        self._kwargs = kwargs if kwargs is not None else {}
        self._check_consistency()
        (
            good_ids,
            sender_supplied_quantities,
            counterparty_supplied_quantities,
        ) = self._get_lists()
        self._good_ids = good_ids
        self._sender_supplied_quantities = sender_supplied_quantities
        self._counterparty_supplied_quantities = counterparty_supplied_quantities
        self._sender_hash = self.get_hash(
            self.ledger_id,
            sender_address=self.sender_address,
            counterparty_address=self.counterparty_address,
            good_ids=self.good_ids,
            sender_supplied_quantities=self.sender_supplied_quantities,
            counterparty_supplied_quantities=self.counterparty_supplied_quantities,
            sender_payable_amount=self.sender_payable_amount,
            counterparty_payable_amount=self.counterparty_payable_amount,
            nonce=self.nonce,
        )
        self._counterparty_hash = self.get_hash(
            self.ledger_id,
            sender_address=self.counterparty_address,
            counterparty_address=self.sender_address,
            good_ids=self.good_ids,
            sender_supplied_quantities=self.counterparty_supplied_quantities,
            counterparty_supplied_quantities=self.sender_supplied_quantities,
            sender_payable_amount=self.counterparty_payable_amount,
            counterparty_payable_amount=self.sender_payable_amount,
            nonce=self.nonce,
        )

    def _check_consistency(self) -> None:
        """Check consistency of the object."""
        enforce(isinstance(self._ledger_id, str), "ledger_id must be str")
        enforce(isinstance(self._sender_address, str), "sender_address must be str")
        enforce(
            isinstance(self._counterparty_address, str),
            "counterparty_address must be str",
        )
        enforce(
            isinstance(self._amount_by_currency_id, dict)
            and all(
                [
                    isinstance(key, str) and isinstance(value, int)
                    for key, value in self._amount_by_currency_id.items()
                ]
            ),
            "amount_by_currency_id must be a dictionary with str keys and int values.",
        )
        enforce(
            isinstance(self._quantities_by_good_id, dict)
            and all(
                [
                    isinstance(key, str) and isinstance(value, int)
                    for key, value in self._quantities_by_good_id.items()
                ]
            ),
            "quantities_by_good_id must be a dictionary with str keys and int values.",
        )
        enforce(
            isinstance(self._is_sender_payable_tx_fee, bool),
            "is_sender_payable_tx_fee must be bool",
        )
        enforce(isinstance(self._nonce, str), "nonce must be str")
        enforce(
            self._fee_by_currency_id is None
            or (
                isinstance(self._fee_by_currency_id, dict)
                and all(
                    [
                        isinstance(key, str) and isinstance(value, int) and value >= 0
                        for key, value in self._fee_by_currency_id.items()
                    ]
                )
            ),
            "fee must be None or Dict[str, int] with positive fees only.",
        )
        enforce(
            all(
                [
                    key in self._amount_by_currency_id
                    for key in self._fee_by_currency_id.keys()
                ]
            ),
            "Fee dictionary has keys which are not present in amount dictionary.",
        )
        if self._is_strict:
            is_pos_amounts = all(
                [amount >= 0 for amount in self._amount_by_currency_id.values()]
            )
            is_neg_amounts = all(
                [amount <= 0 for amount in self._amount_by_currency_id.values()]
            )
            is_pos_quantities = all(
                [quantity >= 0 for quantity in self._quantities_by_good_id.values()]
            )
            is_neg_quantities = all(
                [quantity <= 0 for quantity in self._quantities_by_good_id.values()]
            )
            enforce(
                (is_pos_amounts and is_neg_quantities)
                or (is_neg_amounts and is_pos_quantities),
                "quantities and amounts do not constitute valid terms. All quantities must be of same sign. All amounts must be of same sign. Quantities and amounts must be of different sign.",
            )

    @property
    def id(self) -> str:
        """Get hash of the terms."""
        return self.sender_hash

    @property
    def sender_hash(self) -> str:
        """Get the sender hash."""
        return self._sender_hash

    @property
    def counterparty_hash(self) -> str:
        """Get the sender hash."""
        return self._counterparty_hash

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
        enforce(
            isinstance(counterparty_address, str), "counterparty_address must be str"
        )
        self._counterparty_address = counterparty_address

    @property
    def amount_by_currency_id(self) -> Dict[str, int]:
        """Get the amount by currency id."""
        return copy.copy(self._amount_by_currency_id)

    @property
    def is_sender_payable_tx_fee(self) -> bool:
        """Bool indicating whether the tx fee is paid by sender or counterparty."""
        return self._is_sender_payable_tx_fee

    @property
    def is_single_currency(self) -> bool:
        """Check whether a single currency is used for payment."""
        return (
            len(self._amount_by_currency_id) == 1 and len(self._fee_by_currency_id) <= 1
        )

    @property
    def is_empty_currency(self) -> bool:
        """Check whether a single currency is used for payment."""
        return len(self._amount_by_currency_id) == 0

    @property
    def currency_id(self) -> str:
        """Get the amount the sender must pay."""
        enforce(self.is_single_currency, "More than one currency id, cannot get id.")
        value = next(iter(self._amount_by_currency_id.keys()))
        return value

    @property
    def sender_payable_amount(self) -> int:
        """Get the amount the sender must pay."""
        enforce(
            self.is_single_currency or self.is_empty_currency,
            "More than one currency id, cannot get amount.",
        )
        value = (
            next(iter(self._amount_by_currency_id.values()))
            if not self.is_empty_currency
            else 0
        )
        payable = -value if value <= 0 else 0
        return payable

    @property
    def sender_payable_amount_incl_fee(self) -> int:
        """Get the amount the sender must pay inclusive fee."""
        enforce(
            self.is_single_currency or self.is_empty_currency,
            "More than one currency id, cannot get amount.",
        )
        payable = self.sender_payable_amount
        if self.is_sender_payable_tx_fee and len(self._fee_by_currency_id) == 1:
            payable += next(iter(self._fee_by_currency_id.values()))
        return payable

    @property
    def counterparty_payable_amount(self) -> int:
        """Get the amount the counterparty must pay."""
        enforce(
            self.is_single_currency or self.is_empty_currency,
            "More than one currency id, cannot get amount.",
        )
        value = (
            next(iter(self._amount_by_currency_id.values()))
            if not self.is_empty_currency
            else 0
        )
        payable = value if value >= 0 else 0
        return payable

    @property
    def counterparty_payable_amount_incl_fee(self) -> int:
        """Get the amount the counterparty must pay."""
        enforce(
            self.is_single_currency or self.is_empty_currency,
            "More than one currency id, cannot get amount.",
        )
        payable = self.counterparty_payable_amount
        if not self.is_sender_payable_tx_fee and len(self._fee_by_currency_id) == 1:
            payable += next(iter(self._fee_by_currency_id.values()))
        return payable

    @property
    def quantities_by_good_id(self) -> Dict[str, int]:
        """Get the quantities by good id."""
        return copy.copy(self._quantities_by_good_id)

    @property
    def good_ids(self) -> List[str]:
        """Get the (ordered) good ids."""
        return self._good_ids

    @property
    def sender_supplied_quantities(self) -> List[int]:
        """Get the (ordered) quantities supplied by the sender."""
        return self._sender_supplied_quantities

    @property
    def counterparty_supplied_quantities(self) -> List[int]:
        """Get the (ordered) quantities supplied by the counterparty."""
        return self._counterparty_supplied_quantities

    @property
    def nonce(self) -> str:
        """Get the nonce."""
        return self._nonce

    @property
    def has_fee(self) -> bool:
        """Check if fee is set."""
        return self.fee_by_currency_id != {}

    @property
    def fee(self) -> int:
        """Get the fee."""
        enforce(self.has_fee, "fee_by_currency_id not set.")
        enforce(
            len(self.fee_by_currency_id) == 1,
            "More than one currency id, cannot get fee.",
        )
        return next(iter(self._fee_by_currency_id.values()))

    @property
    def sender_fee(self) -> int:
        """Get the sender fee."""
        value = self.fee if self.is_sender_payable_tx_fee else 0
        return value

    @property
    def counterparty_fee(self) -> int:
        """Get the counterparty fee."""
        value = 0 if self.is_sender_payable_tx_fee else self.fee
        return value

    @property
    def fee_by_currency_id(self) -> Dict[str, int]:
        """Get fee by currency."""
        return copy.copy(self._fee_by_currency_id)

    @property
    def kwargs(self) -> JSONLike:
        """Get the kwargs."""
        return self._kwargs

    @property
    def is_strict(self) -> bool:
        """Get is_strict."""
        return self._is_strict

    def _get_lists(self) -> Tuple[List[str], List[int], List[int]]:
        ordered = collections.OrderedDict(sorted(self.quantities_by_good_id.items()))
        good_ids = []  # type: List[str]
        sender_supplied_quantities = []  # type: List[int]
        counterparty_supplied_quantities = []  # type: List[int]
        for good_id, quantity in ordered.items():
            good_ids.append(good_id)
            if quantity >= 0:
                sender_supplied_quantities.append(quantity)
                counterparty_supplied_quantities.append(0)
            else:
                sender_supplied_quantities.append(0)
                counterparty_supplied_quantities.append(-quantity)
        return good_ids, sender_supplied_quantities, counterparty_supplied_quantities

    @staticmethod
    def get_hash(
        ledger_id: str,
        sender_address: str,
        counterparty_address: str,
        good_ids: List[str],
        sender_supplied_quantities: List[int],
        counterparty_supplied_quantities: List[int],
        sender_payable_amount: int,
        counterparty_payable_amount: int,
        nonce: str,
    ) -> str:
        """
        Generate a hash from transaction information.

        :param ledger_id: the ledger id
        :param sender_address: the sender address
        :param counterparty_address: the counterparty address
        :param good_ids: the list of good ids
        :param sender_supplied_quantities: the quantities supplied by the sender (must all be positive)
        :param counterparty_supplied_quantities: the quantities supplied by the counterparty (must all be positive)
        :param sender_payable_amount: the amount payable by the sender
        :param counterparty_payable_amount: the amount payable by the counterparty
        :param nonce: the nonce of the transaction
        :return: the hash
        """
        if len(good_ids) == 0:
            aggregate_hash = LedgerApis.get_hash(ledger_id, b"")
        else:
            aggregate_hash = LedgerApis.get_hash(
                ledger_id,
                b"".join(
                    [
                        good_ids[0].encode("utf-8"),
                        sender_supplied_quantities[0].to_bytes(32, "big"),
                        counterparty_supplied_quantities[0].to_bytes(32, "big"),
                    ]
                ),
            )
        for idx, good_id in enumerate(good_ids):
            if idx == 0:
                continue
            aggregate_hash = LedgerApis.get_hash(
                ledger_id,
                b"".join(
                    [
                        aggregate_hash.encode("utf-8"),
                        good_id.encode("utf-8"),
                        sender_supplied_quantities[idx].to_bytes(32, "big"),
                        counterparty_supplied_quantities[idx].to_bytes(32, "big"),
                    ]
                ),
            )

        m_list = []  # type: List[bytes]
        m_list.append(sender_address.encode("utf-8"))
        m_list.append(counterparty_address.encode("utf-8"))
        m_list.append(aggregate_hash.encode("utf-8"))
        m_list.append(sender_payable_amount.to_bytes(32, "big"))
        m_list.append(counterparty_payable_amount.to_bytes(32, "big"))
        m_list.append(nonce.encode("utf-8"))
        digest = LedgerApis.get_hash(ledger_id, b"".join(m_list))
        return digest

    @staticmethod
    def encode(terms_protobuf_object: Any, terms_object: "Terms") -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the terms_protobuf_object argument must be matched with the instance of this class in the 'terms_object' argument.

        :param terms_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param terms_object: an instance of this class to be encoded in the protocol buffer object.
        """
        terms_dict = {
            "ledger_id": terms_object.ledger_id,
            "sender_address": terms_object.sender_address,
            "counterparty_address": terms_object.counterparty_address,
            "amount_by_currency_id": terms_object.amount_by_currency_id,
            "quantities_by_good_id": terms_object.quantities_by_good_id,
            "nonce": terms_object.nonce,
            "is_sender_payable_tx_fee": terms_object.is_sender_payable_tx_fee,
            "fee_by_currency_id": terms_object.fee_by_currency_id,
            "is_strict": terms_object.is_strict,
            "kwargs": terms_object.kwargs,
        }
        terms_protobuf_object.terms = DictProtobufStructSerializer.encode(terms_dict)

    @classmethod
    def decode(cls, terms_protobuf_object: Any) -> "Terms":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class must be created that matches the protocol buffer object in the 'terms_protobuf_object' argument.

        :param terms_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'terms_protobuf_object' argument.
        """
        terms_dict = DictProtobufStructSerializer.decode(terms_protobuf_object.terms)

        return cls(
            terms_dict["ledger_id"],
            terms_dict["sender_address"],
            terms_dict["counterparty_address"],
            terms_dict["amount_by_currency_id"],
            terms_dict["quantities_by_good_id"],
            terms_dict["nonce"],
            terms_dict["is_sender_payable_tx_fee"],
            dict(terms_dict["fee_by_currency_id"]),
            terms_dict["is_strict"],
            **dict(terms_dict["kwargs"]),
        )

    def __eq__(self, other: Any) -> bool:
        """Check equality."""
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

    def __str__(self) -> str:
        """Get string representation."""
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

    __slots__ = ("_ledger_id", "_body")

    def __init__(self, ledger_id: str, body: str) -> None:
        """Initialise an instance of TransactionDigest."""
        self._ledger_id = ledger_id
        self._body = body
        self._check_consistency()

    def _check_consistency(self) -> None:
        """Check consistency of the object."""
        enforce(isinstance(self._ledger_id, str), "ledger_id must be str")
        enforce(isinstance(self._body, str), "body must not be None")

    @property
    def ledger_id(self) -> str:
        """Get the id of the ledger on which the terms are to be settled."""
        return self._ledger_id

    @property
    def body(self) -> str:
        """Get the receipt."""
        return self._body

    @staticmethod
    def encode(
        transaction_digest_protobuf_object: Any,
        transaction_digest_object: "TransactionDigest",
    ) -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the transaction_digest_protobuf_object argument must be matched with the instance of this class in the 'transaction_digest_object' argument.

        :param transaction_digest_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param transaction_digest_object: an instance of this class to be encoded in the protocol buffer object.
        """
        transaction_digest_dict = {
            "ledger_id": transaction_digest_object.ledger_id,
            "body": transaction_digest_object.body,
        }

        transaction_digest_protobuf_object.transaction_digest = (
            DictProtobufStructSerializer.encode(transaction_digest_dict)
        )

    @classmethod
    def decode(cls, transaction_digest_protobuf_object: Any) -> "TransactionDigest":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class must be created that matches the protocol buffer object in the 'transaction_digest_protobuf_object' argument.

        :param transaction_digest_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'transaction_digest_protobuf_object' argument.
        """
        transaction_digest_dict = DictProtobufStructSerializer.decode(
            transaction_digest_protobuf_object.transaction_digest
        )

        return cls(
            transaction_digest_dict["ledger_id"], transaction_digest_dict["body"]
        )

    def __eq__(self, other: Any) -> bool:
        """Check equality."""
        return (
            isinstance(other, TransactionDigest)
            and self.ledger_id == other.ledger_id
            and self.body == other.body
        )

    def __str__(self) -> str:
        """Get string representation."""
        return "TransactionDigest: ledger_id={}, body={}".format(
            self.ledger_id, self.body
        )


class TransactionReceipt:
    """This class represents an instance of TransactionReceipt."""

    __slots__ = ("_ledger_id", "_receipt", "_transaction")

    def __init__(
        self, ledger_id: str, receipt: JSONLike, transaction: JSONLike
    ) -> None:
        """Initialise an instance of TransactionReceipt."""
        self._ledger_id = ledger_id
        self._receipt = receipt
        self._transaction = transaction
        self._check_consistency()

    def _check_consistency(self) -> None:
        """Check consistency of the object."""
        enforce(isinstance(self._ledger_id, str), "ledger_id must be str")
        enforce(isinstance(self._receipt, dict), "receipt must be dict")
        enforce(isinstance(self._transaction, dict), "transaction must be dict")

    @property
    def ledger_id(self) -> str:
        """Get the id of the ledger on which the terms are to be settled."""
        return self._ledger_id

    @property
    def receipt(self) -> JSONLike:
        """Get the receipt."""
        return self._receipt

    @property
    def transaction(self) -> JSONLike:
        """Get the transaction."""
        return self._transaction

    @staticmethod
    def encode(
        transaction_receipt_protobuf_object: Any,
        transaction_receipt_object: "TransactionReceipt",
    ) -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the transaction_receipt_protobuf_object argument must be matched with the instance of this class in the 'transaction_receipt_object' argument.

        :param transaction_receipt_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param transaction_receipt_object: an instance of this class to be encoded in the protocol buffer object.
        """
        transaction_receipt_dict = {
            "ledger_id": transaction_receipt_object.ledger_id,
            "receipt": transaction_receipt_object.receipt,
            "transaction": transaction_receipt_object.transaction,
        }

        transaction_receipt_protobuf_object.transaction_receipt = (
            DictProtobufStructSerializer.encode(transaction_receipt_dict)
        )

    @classmethod
    def decode(cls, transaction_receipt_protobuf_object: Any) -> "TransactionReceipt":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class must be created that matches the protocol buffer object in the 'transaction_receipt_protobuf_object' argument.

        :param transaction_receipt_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'transaction_receipt_protobuf_object' argument.
        """
        transaction_receipt_dict = DictProtobufStructSerializer.decode(
            transaction_receipt_protobuf_object.transaction_receipt
        )
        return cls(
            transaction_receipt_dict["ledger_id"],
            transaction_receipt_dict["receipt"],
            transaction_receipt_dict["transaction"],
        )

    def __eq__(self, other: Any) -> bool:
        """Check equality."""
        return (
            isinstance(other, TransactionReceipt)
            and self.ledger_id == other.ledger_id
            and self.receipt == other.receipt
            and self.transaction == other.transaction
        )

    def __str__(self) -> str:
        """Get string representation."""
        return "TransactionReceipt: ledger_id={}, receipt={}, transaction={}".format(
            self.ledger_id, self.receipt, self.transaction
        )
