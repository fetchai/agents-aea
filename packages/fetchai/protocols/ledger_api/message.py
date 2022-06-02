# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2022 fetchai
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

"""This module contains ledger_api's message definition."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,too-many-branches,not-an-iterable,unidiomatic-typecheck,unsubscriptable-object
import logging
from typing import Any, Optional, Set, Tuple, cast

from aea.configurations.base import PublicId
from aea.exceptions import AEAEnforceError, enforce
from aea.protocols.base import Message

from packages.fetchai.protocols.ledger_api.custom_types import Kwargs as CustomKwargs
from packages.fetchai.protocols.ledger_api.custom_types import (
    RawTransaction as CustomRawTransaction,
)
from packages.fetchai.protocols.ledger_api.custom_types import (
    SignedTransaction as CustomSignedTransaction,
)
from packages.fetchai.protocols.ledger_api.custom_types import State as CustomState
from packages.fetchai.protocols.ledger_api.custom_types import Terms as CustomTerms
from packages.fetchai.protocols.ledger_api.custom_types import (
    TransactionDigest as CustomTransactionDigest,
)
from packages.fetchai.protocols.ledger_api.custom_types import (
    TransactionReceipt as CustomTransactionReceipt,
)


_default_logger = logging.getLogger("aea.packages.fetchai.protocols.ledger_api.message")

DEFAULT_BODY_SIZE = 4


class LedgerApiMessage(Message):
    """A protocol for ledger APIs requests and responses."""

    protocol_id = PublicId.from_str("fetchai/ledger_api:1.0.0")
    protocol_specification_id = PublicId.from_str("fetchai/ledger_api:1.0.0")

    Kwargs = CustomKwargs

    RawTransaction = CustomRawTransaction

    SignedTransaction = CustomSignedTransaction

    State = CustomState

    Terms = CustomTerms

    TransactionDigest = CustomTransactionDigest

    TransactionReceipt = CustomTransactionReceipt

    class Performative(Message.Performative):
        """Performatives for the ledger_api protocol."""

        BALANCE = "balance"
        ERROR = "error"
        GET_BALANCE = "get_balance"
        GET_RAW_TRANSACTION = "get_raw_transaction"
        GET_STATE = "get_state"
        GET_TRANSACTION_RECEIPT = "get_transaction_receipt"
        RAW_TRANSACTION = "raw_transaction"
        SEND_SIGNED_TRANSACTION = "send_signed_transaction"
        STATE = "state"
        TRANSACTION_DIGEST = "transaction_digest"
        TRANSACTION_RECEIPT = "transaction_receipt"

        def __str__(self) -> str:
            """Get the string representation."""
            return str(self.value)

    _performatives = {
        "balance",
        "error",
        "get_balance",
        "get_raw_transaction",
        "get_state",
        "get_transaction_receipt",
        "raw_transaction",
        "send_signed_transaction",
        "state",
        "transaction_digest",
        "transaction_receipt",
    }
    __slots__: Tuple[str, ...] = tuple()

    class _SlotsCls:
        __slots__ = (
            "address",
            "args",
            "balance",
            "callable",
            "code",
            "data",
            "dialogue_reference",
            "kwargs",
            "ledger_id",
            "message",
            "message_id",
            "performative",
            "raw_transaction",
            "signed_transaction",
            "state",
            "target",
            "terms",
            "transaction_digest",
            "transaction_receipt",
        )

    def __init__(
        self,
        performative: Performative,
        dialogue_reference: Tuple[str, str] = ("", ""),
        message_id: int = 1,
        target: int = 0,
        **kwargs: Any,
    ):
        """
        Initialise an instance of LedgerApiMessage.

        :param message_id: the message id.
        :param dialogue_reference: the dialogue reference.
        :param target: the message target.
        :param performative: the message performative.
        :param **kwargs: extra options.
        """
        super().__init__(
            dialogue_reference=dialogue_reference,
            message_id=message_id,
            target=target,
            performative=LedgerApiMessage.Performative(performative),
            **kwargs,
        )

    @property
    def valid_performatives(self) -> Set[str]:
        """Get valid performatives."""
        return self._performatives

    @property
    def dialogue_reference(self) -> Tuple[str, str]:
        """Get the dialogue_reference of the message."""
        enforce(self.is_set("dialogue_reference"), "dialogue_reference is not set.")
        return cast(Tuple[str, str], self.get("dialogue_reference"))

    @property
    def message_id(self) -> int:
        """Get the message_id of the message."""
        enforce(self.is_set("message_id"), "message_id is not set.")
        return cast(int, self.get("message_id"))

    @property
    def performative(self) -> Performative:  # type: ignore # noqa: F821
        """Get the performative of the message."""
        enforce(self.is_set("performative"), "performative is not set.")
        return cast(LedgerApiMessage.Performative, self.get("performative"))

    @property
    def target(self) -> int:
        """Get the target of the message."""
        enforce(self.is_set("target"), "target is not set.")
        return cast(int, self.get("target"))

    @property
    def address(self) -> str:
        """Get the 'address' content from the message."""
        enforce(self.is_set("address"), "'address' content is not set.")
        return cast(str, self.get("address"))

    @property
    def args(self) -> Tuple[str, ...]:
        """Get the 'args' content from the message."""
        enforce(self.is_set("args"), "'args' content is not set.")
        return cast(Tuple[str, ...], self.get("args"))

    @property
    def balance(self) -> int:
        """Get the 'balance' content from the message."""
        enforce(self.is_set("balance"), "'balance' content is not set.")
        return cast(int, self.get("balance"))

    @property
    def callable(self) -> str:
        """Get the 'callable' content from the message."""
        enforce(self.is_set("callable"), "'callable' content is not set.")
        return cast(str, self.get("callable"))

    @property
    def code(self) -> int:
        """Get the 'code' content from the message."""
        enforce(self.is_set("code"), "'code' content is not set.")
        return cast(int, self.get("code"))

    @property
    def data(self) -> Optional[bytes]:
        """Get the 'data' content from the message."""
        return cast(Optional[bytes], self.get("data"))

    @property
    def kwargs(self) -> CustomKwargs:
        """Get the 'kwargs' content from the message."""
        enforce(self.is_set("kwargs"), "'kwargs' content is not set.")
        return cast(CustomKwargs, self.get("kwargs"))

    @property
    def ledger_id(self) -> str:
        """Get the 'ledger_id' content from the message."""
        enforce(self.is_set("ledger_id"), "'ledger_id' content is not set.")
        return cast(str, self.get("ledger_id"))

    @property
    def message(self) -> Optional[str]:
        """Get the 'message' content from the message."""
        return cast(Optional[str], self.get("message"))

    @property
    def raw_transaction(self) -> CustomRawTransaction:
        """Get the 'raw_transaction' content from the message."""
        enforce(self.is_set("raw_transaction"), "'raw_transaction' content is not set.")
        return cast(CustomRawTransaction, self.get("raw_transaction"))

    @property
    def signed_transaction(self) -> CustomSignedTransaction:
        """Get the 'signed_transaction' content from the message."""
        enforce(
            self.is_set("signed_transaction"),
            "'signed_transaction' content is not set.",
        )
        return cast(CustomSignedTransaction, self.get("signed_transaction"))

    @property
    def state(self) -> CustomState:
        """Get the 'state' content from the message."""
        enforce(self.is_set("state"), "'state' content is not set.")
        return cast(CustomState, self.get("state"))

    @property
    def terms(self) -> CustomTerms:
        """Get the 'terms' content from the message."""
        enforce(self.is_set("terms"), "'terms' content is not set.")
        return cast(CustomTerms, self.get("terms"))

    @property
    def transaction_digest(self) -> CustomTransactionDigest:
        """Get the 'transaction_digest' content from the message."""
        enforce(
            self.is_set("transaction_digest"),
            "'transaction_digest' content is not set.",
        )
        return cast(CustomTransactionDigest, self.get("transaction_digest"))

    @property
    def transaction_receipt(self) -> CustomTransactionReceipt:
        """Get the 'transaction_receipt' content from the message."""
        enforce(
            self.is_set("transaction_receipt"),
            "'transaction_receipt' content is not set.",
        )
        return cast(CustomTransactionReceipt, self.get("transaction_receipt"))

    def _is_consistent(self) -> bool:
        """Check that the message follows the ledger_api protocol."""
        try:
            enforce(
                isinstance(self.dialogue_reference, tuple),
                "Invalid type for 'dialogue_reference'. Expected 'tuple'. Found '{}'.".format(
                    type(self.dialogue_reference)
                ),
            )
            enforce(
                isinstance(self.dialogue_reference[0], str),
                "Invalid type for 'dialogue_reference[0]'. Expected 'str'. Found '{}'.".format(
                    type(self.dialogue_reference[0])
                ),
            )
            enforce(
                isinstance(self.dialogue_reference[1], str),
                "Invalid type for 'dialogue_reference[1]'. Expected 'str'. Found '{}'.".format(
                    type(self.dialogue_reference[1])
                ),
            )
            enforce(
                type(self.message_id) is int,
                "Invalid type for 'message_id'. Expected 'int'. Found '{}'.".format(
                    type(self.message_id)
                ),
            )
            enforce(
                type(self.target) is int,
                "Invalid type for 'target'. Expected 'int'. Found '{}'.".format(
                    type(self.target)
                ),
            )

            # Light Protocol Rule 2
            # Check correct performative
            enforce(
                isinstance(self.performative, LedgerApiMessage.Performative),
                "Invalid 'performative'. Expected either of '{}'. Found '{}'.".format(
                    self.valid_performatives, self.performative
                ),
            )

            # Check correct contents
            actual_nb_of_contents = len(self._body) - DEFAULT_BODY_SIZE
            expected_nb_of_contents = 0
            if self.performative == LedgerApiMessage.Performative.GET_BALANCE:
                expected_nb_of_contents = 2
                enforce(
                    isinstance(self.ledger_id, str),
                    "Invalid type for content 'ledger_id'. Expected 'str'. Found '{}'.".format(
                        type(self.ledger_id)
                    ),
                )
                enforce(
                    isinstance(self.address, str),
                    "Invalid type for content 'address'. Expected 'str'. Found '{}'.".format(
                        type(self.address)
                    ),
                )
            elif self.performative == LedgerApiMessage.Performative.GET_RAW_TRANSACTION:
                expected_nb_of_contents = 1
                enforce(
                    isinstance(self.terms, CustomTerms),
                    "Invalid type for content 'terms'. Expected 'Terms'. Found '{}'.".format(
                        type(self.terms)
                    ),
                )
            elif (
                self.performative
                == LedgerApiMessage.Performative.SEND_SIGNED_TRANSACTION
            ):
                expected_nb_of_contents = 1
                enforce(
                    isinstance(self.signed_transaction, CustomSignedTransaction),
                    "Invalid type for content 'signed_transaction'. Expected 'SignedTransaction'. Found '{}'.".format(
                        type(self.signed_transaction)
                    ),
                )
            elif (
                self.performative
                == LedgerApiMessage.Performative.GET_TRANSACTION_RECEIPT
            ):
                expected_nb_of_contents = 1
                enforce(
                    isinstance(self.transaction_digest, CustomTransactionDigest),
                    "Invalid type for content 'transaction_digest'. Expected 'TransactionDigest'. Found '{}'.".format(
                        type(self.transaction_digest)
                    ),
                )
            elif self.performative == LedgerApiMessage.Performative.BALANCE:
                expected_nb_of_contents = 2
                enforce(
                    isinstance(self.ledger_id, str),
                    "Invalid type for content 'ledger_id'. Expected 'str'. Found '{}'.".format(
                        type(self.ledger_id)
                    ),
                )
                enforce(
                    type(self.balance) is int,
                    "Invalid type for content 'balance'. Expected 'int'. Found '{}'.".format(
                        type(self.balance)
                    ),
                )
            elif self.performative == LedgerApiMessage.Performative.RAW_TRANSACTION:
                expected_nb_of_contents = 1
                enforce(
                    isinstance(self.raw_transaction, CustomRawTransaction),
                    "Invalid type for content 'raw_transaction'. Expected 'RawTransaction'. Found '{}'.".format(
                        type(self.raw_transaction)
                    ),
                )
            elif self.performative == LedgerApiMessage.Performative.TRANSACTION_DIGEST:
                expected_nb_of_contents = 1
                enforce(
                    isinstance(self.transaction_digest, CustomTransactionDigest),
                    "Invalid type for content 'transaction_digest'. Expected 'TransactionDigest'. Found '{}'.".format(
                        type(self.transaction_digest)
                    ),
                )
            elif self.performative == LedgerApiMessage.Performative.TRANSACTION_RECEIPT:
                expected_nb_of_contents = 1
                enforce(
                    isinstance(self.transaction_receipt, CustomTransactionReceipt),
                    "Invalid type for content 'transaction_receipt'. Expected 'TransactionReceipt'. Found '{}'.".format(
                        type(self.transaction_receipt)
                    ),
                )
            elif self.performative == LedgerApiMessage.Performative.GET_STATE:
                expected_nb_of_contents = 4
                enforce(
                    isinstance(self.ledger_id, str),
                    "Invalid type for content 'ledger_id'. Expected 'str'. Found '{}'.".format(
                        type(self.ledger_id)
                    ),
                )
                enforce(
                    isinstance(self.callable, str),
                    "Invalid type for content 'callable'. Expected 'str'. Found '{}'.".format(
                        type(self.callable)
                    ),
                )
                enforce(
                    isinstance(self.args, tuple),
                    "Invalid type for content 'args'. Expected 'tuple'. Found '{}'.".format(
                        type(self.args)
                    ),
                )
                enforce(
                    all(isinstance(element, str) for element in self.args),
                    "Invalid type for tuple elements in content 'args'. Expected 'str'.",
                )
                enforce(
                    isinstance(self.kwargs, CustomKwargs),
                    "Invalid type for content 'kwargs'. Expected 'Kwargs'. Found '{}'.".format(
                        type(self.kwargs)
                    ),
                )
            elif self.performative == LedgerApiMessage.Performative.STATE:
                expected_nb_of_contents = 2
                enforce(
                    isinstance(self.ledger_id, str),
                    "Invalid type for content 'ledger_id'. Expected 'str'. Found '{}'.".format(
                        type(self.ledger_id)
                    ),
                )
                enforce(
                    isinstance(self.state, CustomState),
                    "Invalid type for content 'state'. Expected 'State'. Found '{}'.".format(
                        type(self.state)
                    ),
                )
            elif self.performative == LedgerApiMessage.Performative.ERROR:
                expected_nb_of_contents = 1
                enforce(
                    type(self.code) is int,
                    "Invalid type for content 'code'. Expected 'int'. Found '{}'.".format(
                        type(self.code)
                    ),
                )
                if self.is_set("message"):
                    expected_nb_of_contents += 1
                    message = cast(str, self.message)
                    enforce(
                        isinstance(message, str),
                        "Invalid type for content 'message'. Expected 'str'. Found '{}'.".format(
                            type(message)
                        ),
                    )
                if self.is_set("data"):
                    expected_nb_of_contents += 1
                    data = cast(bytes, self.data)
                    enforce(
                        isinstance(data, bytes),
                        "Invalid type for content 'data'. Expected 'bytes'. Found '{}'.".format(
                            type(data)
                        ),
                    )

            # Check correct content count
            enforce(
                expected_nb_of_contents == actual_nb_of_contents,
                "Incorrect number of contents. Expected {}. Found {}".format(
                    expected_nb_of_contents, actual_nb_of_contents
                ),
            )

            # Light Protocol Rule 3
            if self.message_id == 1:
                enforce(
                    self.target == 0,
                    "Invalid 'target'. Expected 0 (because 'message_id' is 1). Found {}.".format(
                        self.target
                    ),
                )
        except (AEAEnforceError, ValueError, KeyError) as e:
            _default_logger.error(str(e))
            return False

        return True
