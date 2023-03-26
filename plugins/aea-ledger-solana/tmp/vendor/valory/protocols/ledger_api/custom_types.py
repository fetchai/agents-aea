# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2020-2023 Valory AG
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

"""This module contains class representations corresponding to every custom type in the protocol specification."""

from typing import Any, List

from aea.common import JSONLike
from aea.exceptions import enforce
from aea.helpers.serializers import DictProtobufStructSerializer
from aea.helpers.transaction.base import RawTransaction as BaseRawTransaction
from aea.helpers.transaction.base import SignedTransaction as BaseSignedTransaction
from aea.helpers.transaction.base import State as BaseState
from aea.helpers.transaction.base import Terms as BaseTerms
from aea.helpers.transaction.base import TransactionDigest as BaseTransactionDigest
from aea.helpers.transaction.base import TransactionReceipt as BaseTransactionReceipt


RawTransaction = BaseRawTransaction
SignedTransaction = BaseSignedTransaction
State = BaseState
Terms = BaseTerms
TransactionDigest = BaseTransactionDigest
TransactionReceipt = BaseTransactionReceipt


class Kwargs:
    """This class represents an instance of Kwargs."""

    __slots__ = ("_body",)

    def __init__(
        self,
        body: JSONLike,
    ):
        """Initialise an instance of RawTransaction."""
        self._body = body
        self._check_consistency()

    def _check_consistency(self) -> None:
        """Check consistency of the object."""
        enforce(
            isinstance(self._body, dict)
            and all([isinstance(key, str) for key in self._body.keys()]),
            "Body must be dict and keys must be str.",
        )

    @property
    def body(self) -> JSONLike:
        """Get the body."""
        return self._body

    @staticmethod
    def encode(kwargs_protobuf_object: Any, kwargs_object: "Kwargs") -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the kwargs_protobuf_object argument is matched with the instance of this class in the 'kwargs_object' argument.

        :param kwargs_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param kwargs_object: an instance of this class to be encoded in the protocol buffer object.
        """
        kwargs_protobuf_object.kwargs = DictProtobufStructSerializer.encode(
            kwargs_object.body
        )

    @classmethod
    def decode(cls, kwargs_protobuf_object: Any) -> "Kwargs":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class is created that matches the protocol buffer object in the 'kwargs_protobuf_object' argument.

        :param kwargs_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'kwargs_protobuf_object' argument.
        """
        kwargs = DictProtobufStructSerializer.decode(kwargs_protobuf_object.kwargs)
        return cls(kwargs)

    def __eq__(self, other: Any) -> bool:
        """Check equality."""
        return isinstance(other, Kwargs) and self.body == other.body

    def __str__(self) -> str:
        """Get string representation."""
        return "Kwargs: body={}".format(self.body)


class SignedTransactions:
    """This class represents an instance of SignedTransactions."""

    __slots__ = (
        "_ledger_id",
        "_signed_transactions",
    )

    def __init__(
        self,
        ledger_id: str,
        signed_transactions: List[JSONLike],
    ):
        """Initialise an instance of SignedTransactions."""
        self._ledger_id = ledger_id
        self._signed_transactions = signed_transactions
        self._check_consistency()

    def _check_consistency(self) -> None:
        """Check consistency of the object."""
        enforce(isinstance(self._ledger_id, str), "ledger_id must be str.")
        enforce(
            isinstance(self._signed_transactions, list),
            "signed_transactions must be list.",
        )

    @property
    def ledger_id(self) -> str:
        """Get the body."""
        return self._ledger_id

    @property
    def signed_transactions(self) -> List[JSONLike]:
        """Get the body."""
        return self._signed_transactions

    @staticmethod
    def encode(
        signed_transactions_protobuf_object: Any,
        signed_transactions_object: "SignedTransactions",
    ) -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the signed_transactions_protobuf_object argument is matched with the instance of this class in the 'signed_transactions_object' argument.

        :param signed_transactions_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param signed_transactions_object: an instance of this class to be encoded in the protocol buffer object.
        """
        encoded_transactions = [
            DictProtobufStructSerializer.encode(tx)
            for tx in signed_transactions_object.signed_transactions
        ]
        signed_transactions_protobuf_object.signed_transactions.extend(
            encoded_transactions
        )
        signed_transactions_protobuf_object.ledger_id = (
            signed_transactions_object.ledger_id
        )

    @classmethod
    def decode(cls, signed_transactions_protobuf_object: Any) -> "SignedTransactions":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class is created that matches the protocol buffer object in the 'signed_transactions_protobuf_object' argument.

        :param signed_transactions_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'signed_transactions_protobuf_object' argument.
        """
        decoded_transactions = [
            DictProtobufStructSerializer.decode(tx)
            for tx in signed_transactions_protobuf_object.signed_transactions
        ]
        return cls(
            ledger_id=signed_transactions_protobuf_object.ledger_id,
            signed_transactions=decoded_transactions,
        )

    def __eq__(self, other: Any) -> bool:
        """Check equality."""
        return (
            isinstance(other, SignedTransactions)
            and self.ledger_id == other.ledger_id
            and self.signed_transactions == other.signed_transactions
        )

    def __str__(self) -> str:
        """Get string representation."""
        return "SignedTransactions: ledger_id={} signed_transactions={}".format(
            self.ledger_id, self.signed_transactions
        )


class TransactionDigests:
    """This class represents an instance of TransactionDigests."""

    __slots__ = (
        "_ledger_id",
        "_transaction_digests",
    )

    def __init__(
        self,
        ledger_id: str,
        transaction_digests: List[str],
    ):
        """Initialise an instance of TransactionDigests."""
        self._ledger_id = ledger_id
        self._transaction_digests = transaction_digests
        self._check_consistency()

    def _check_consistency(self) -> None:
        """Check consistency of the object."""
        enforce(isinstance(self._ledger_id, str), "ledger_id must be str.")
        enforce(
            isinstance(self._transaction_digests, list),
            "transaction_digests must be list.",
        )

    @property
    def ledger_id(self) -> str:
        """Get the body."""
        return self._ledger_id

    @property
    def transaction_digests(self) -> List[str]:
        """Get the body."""
        return self._transaction_digests

    @staticmethod
    def encode(
        transaction_digests_protobuf_object: Any,
        transaction_digests_object: "TransactionDigests",
    ) -> None:
        """
        Encode an instance of this class into the protocol buffer object.

        The protocol buffer object in the transaction_digests_protobuf_object argument is matched with the instance of this class in the 'transaction_digests_object' argument.

        :param transaction_digests_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :param transaction_digests_object: an instance of this class to be encoded in the protocol buffer object.
        """
        transaction_digests_protobuf_object.transaction_digests.extend(
            transaction_digests_object.transaction_digests
        )
        transaction_digests_protobuf_object.ledger_id = (
            transaction_digests_object.ledger_id
        )

    @classmethod
    def decode(cls, transaction_digests_protobuf_object: Any) -> "TransactionDigests":
        """
        Decode a protocol buffer object that corresponds with this class into an instance of this class.

        A new instance of this class is created that matches the protocol buffer object in the 'transaction_digests_protobuf_object' argument.

        :param transaction_digests_protobuf_object: the protocol buffer object whose type corresponds with this class.
        :return: A new instance of this class that matches the protocol buffer object in the 'transaction_digests_protobuf_object' argument.
        """
        return cls(
            ledger_id=transaction_digests_protobuf_object.ledger_id,
            transaction_digests=list(
                transaction_digests_protobuf_object.transaction_digests
            ),
        )

    def __eq__(self, other: Any) -> bool:
        """Check equality."""
        return (
            isinstance(other, TransactionDigests)
            and self.ledger_id == other.ledger_id
            and self.transaction_digests == other.transaction_digests
        )

    def __str__(self) -> str:
        """Get string representation."""
        return "TransactionDigests: ledger_id={} transaction_digests={}".format(
            self.ledger_id, self.transaction_digests
        )
