# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2020 fetchai
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

import logging
from enum import Enum
from typing import Optional, Set, Tuple, cast

from aea.configurations.base import ProtocolId
from aea.protocols.base import Message

from packages.fetchai.protocols.ledger_api.custom_types import (
    AnyObject as CustomAnyObject,
)

logger = logging.getLogger("aea.packages.fetchai.protocols.ledger_api.message")

DEFAULT_BODY_SIZE = 4


class LedgerApiMessage(Message):
    """A protocol for ledger APIs requests and responses."""

    protocol_id = ProtocolId("fetchai", "ledger_api", "0.1.0")

    AnyObject = CustomAnyObject

    class Performative(Enum):
        """Performatives for the ledger_api protocol."""

        BALANCE = "balance"
        ERROR = "error"
        GET_BALANCE = "get_balance"
        GET_TRANSACTION_RECEIPT = "get_transaction_receipt"
        GET_TRANSFER_TRANSACTION = "get_transfer_transaction"
        SEND_SIGNED_TRANSACTION = "send_signed_transaction"
        TRANSACTION = "transaction"
        TRANSACTION_DIGEST = "transaction_digest"
        TRANSACTION_RECEIPT = "transaction_receipt"

        def __str__(self):
            """Get the string representation."""
            return str(self.value)

    def __init__(
        self,
        performative: Performative,
        dialogue_reference: Tuple[str, str] = ("", ""),
        message_id: int = 1,
        target: int = 0,
        **kwargs,
    ):
        """
        Initialise an instance of LedgerApiMessage.

        :param message_id: the message id.
        :param dialogue_reference: the dialogue reference.
        :param target: the message target.
        :param performative: the message performative.
        """
        super().__init__(
            dialogue_reference=dialogue_reference,
            message_id=message_id,
            target=target,
            performative=LedgerApiMessage.Performative(performative),
            **kwargs,
        )
        self._performatives = {
            "balance",
            "error",
            "get_balance",
            "get_transaction_receipt",
            "get_transfer_transaction",
            "send_signed_transaction",
            "transaction",
            "transaction_digest",
            "transaction_receipt",
        }

    @property
    def valid_performatives(self) -> Set[str]:
        """Get valid performatives."""
        return self._performatives

    @property
    def dialogue_reference(self) -> Tuple[str, str]:
        """Get the dialogue_reference of the message."""
        assert self.is_set("dialogue_reference"), "dialogue_reference is not set."
        return cast(Tuple[str, str], self.get("dialogue_reference"))

    @property
    def message_id(self) -> int:
        """Get the message_id of the message."""
        assert self.is_set("message_id"), "message_id is not set."
        return cast(int, self.get("message_id"))

    @property
    def performative(self) -> Performative:  # type: ignore # noqa: F821
        """Get the performative of the message."""
        assert self.is_set("performative"), "performative is not set."
        return cast(LedgerApiMessage.Performative, self.get("performative"))

    @property
    def target(self) -> int:
        """Get the target of the message."""
        assert self.is_set("target"), "target is not set."
        return cast(int, self.get("target"))

    @property
    def address(self) -> str:
        """Get the 'address' content from the message."""
        assert self.is_set("address"), "'address' content is not set."
        return cast(str, self.get("address"))

    @property
    def amount(self) -> int:
        """Get the 'amount' content from the message."""
        assert self.is_set("amount"), "'amount' content is not set."
        return cast(int, self.get("amount"))

    @property
    def code(self) -> Optional[int]:
        """Get the 'code' content from the message."""
        return cast(Optional[int], self.get("code"))

    @property
    def data(self) -> CustomAnyObject:
        """Get the 'data' content from the message."""
        assert self.is_set("data"), "'data' content is not set."
        return cast(CustomAnyObject, self.get("data"))

    @property
    def ledger_id(self) -> str:
        """Get the 'ledger_id' content from the message."""
        assert self.is_set("ledger_id"), "'ledger_id' content is not set."
        return cast(str, self.get("ledger_id"))

    @property
    def message(self) -> Optional[str]:
        """Get the 'message' content from the message."""
        return cast(Optional[str], self.get("message"))

    @property
    def signed_transaction(self) -> CustomAnyObject:
        """Get the 'signed_transaction' content from the message."""
        assert self.is_set(
            "signed_transaction"
        ), "'signed_transaction' content is not set."
        return cast(CustomAnyObject, self.get("signed_transaction"))

    @property
    def transaction(self) -> CustomAnyObject:
        """Get the 'transaction' content from the message."""
        assert self.is_set("transaction"), "'transaction' content is not set."
        return cast(CustomAnyObject, self.get("transaction"))

    @property
    def transaction_digest(self) -> str:
        """Get the 'transaction_digest' content from the message."""
        assert self.is_set(
            "transaction_digest"
        ), "'transaction_digest' content is not set."
        return cast(str, self.get("transaction_digest"))

    @property
    def transaction_receipt(self) -> CustomAnyObject:
        """Get the 'transaction_receipt' content from the message."""
        assert self.is_set(
            "transaction_receipt"
        ), "'transaction_receipt' content is not set."
        return cast(CustomAnyObject, self.get("transaction_receipt"))

    @property
    def transfer(self) -> CustomAnyObject:
        """Get the 'transfer' content from the message."""
        assert self.is_set("transfer"), "'transfer' content is not set."
        return cast(CustomAnyObject, self.get("transfer"))

    def _is_consistent(self) -> bool:
        """Check that the message follows the ledger_api protocol."""
        try:
            assert (
                type(self.dialogue_reference) == tuple
            ), "Invalid type for 'dialogue_reference'. Expected 'tuple'. Found '{}'.".format(
                type(self.dialogue_reference)
            )
            assert (
                type(self.dialogue_reference[0]) == str
            ), "Invalid type for 'dialogue_reference[0]'. Expected 'str'. Found '{}'.".format(
                type(self.dialogue_reference[0])
            )
            assert (
                type(self.dialogue_reference[1]) == str
            ), "Invalid type for 'dialogue_reference[1]'. Expected 'str'. Found '{}'.".format(
                type(self.dialogue_reference[1])
            )
            assert (
                type(self.message_id) == int
            ), "Invalid type for 'message_id'. Expected 'int'. Found '{}'.".format(
                type(self.message_id)
            )
            assert (
                type(self.target) == int
            ), "Invalid type for 'target'. Expected 'int'. Found '{}'.".format(
                type(self.target)
            )

            # Light Protocol Rule 2
            # Check correct performative
            assert (
                type(self.performative) == LedgerApiMessage.Performative
            ), "Invalid 'performative'. Expected either of '{}'. Found '{}'.".format(
                self.valid_performatives, self.performative
            )

            # Check correct contents
            actual_nb_of_contents = len(self.body) - DEFAULT_BODY_SIZE
            expected_nb_of_contents = 0
            if self.performative == LedgerApiMessage.Performative.GET_BALANCE:
                expected_nb_of_contents = 2
                assert (
                    type(self.ledger_id) == str
                ), "Invalid type for content 'ledger_id'. Expected 'str'. Found '{}'.".format(
                    type(self.ledger_id)
                )
                assert (
                    type(self.address) == str
                ), "Invalid type for content 'address'. Expected 'str'. Found '{}'.".format(
                    type(self.address)
                )
            elif (
                self.performative
                == LedgerApiMessage.Performative.GET_TRANSFER_TRANSACTION
            ):
                expected_nb_of_contents = 2
                assert (
                    type(self.ledger_id) == str
                ), "Invalid type for content 'ledger_id'. Expected 'str'. Found '{}'.".format(
                    type(self.ledger_id)
                )
                assert (
                    type(self.transfer) == CustomAnyObject
                ), "Invalid type for content 'transfer'. Expected 'AnyObject'. Found '{}'.".format(
                    type(self.transfer)
                )
            elif (
                self.performative
                == LedgerApiMessage.Performative.SEND_SIGNED_TRANSACTION
            ):
                expected_nb_of_contents = 2
                assert (
                    type(self.ledger_id) == str
                ), "Invalid type for content 'ledger_id'. Expected 'str'. Found '{}'.".format(
                    type(self.ledger_id)
                )
                assert (
                    type(self.signed_transaction) == CustomAnyObject
                ), "Invalid type for content 'signed_transaction'. Expected 'AnyObject'. Found '{}'.".format(
                    type(self.signed_transaction)
                )
            elif (
                self.performative
                == LedgerApiMessage.Performative.GET_TRANSACTION_RECEIPT
            ):
                expected_nb_of_contents = 2
                assert (
                    type(self.ledger_id) == str
                ), "Invalid type for content 'ledger_id'. Expected 'str'. Found '{}'.".format(
                    type(self.ledger_id)
                )
                assert (
                    type(self.transaction_digest) == str
                ), "Invalid type for content 'transaction_digest'. Expected 'str'. Found '{}'.".format(
                    type(self.transaction_digest)
                )
            elif self.performative == LedgerApiMessage.Performative.BALANCE:
                expected_nb_of_contents = 1
                assert (
                    type(self.amount) == int
                ), "Invalid type for content 'amount'. Expected 'int'. Found '{}'.".format(
                    type(self.amount)
                )
            elif self.performative == LedgerApiMessage.Performative.TRANSACTION:
                expected_nb_of_contents = 1
                assert (
                    type(self.transaction) == CustomAnyObject
                ), "Invalid type for content 'transaction'. Expected 'AnyObject'. Found '{}'.".format(
                    type(self.transaction)
                )
            elif self.performative == LedgerApiMessage.Performative.TRANSACTION_DIGEST:
                expected_nb_of_contents = 1
                assert (
                    type(self.transaction_digest) == str
                ), "Invalid type for content 'transaction_digest'. Expected 'str'. Found '{}'.".format(
                    type(self.transaction_digest)
                )
            elif self.performative == LedgerApiMessage.Performative.TRANSACTION_RECEIPT:
                expected_nb_of_contents = 1
                assert (
                    type(self.transaction_receipt) == CustomAnyObject
                ), "Invalid type for content 'transaction_receipt'. Expected 'AnyObject'. Found '{}'.".format(
                    type(self.transaction_receipt)
                )
            elif self.performative == LedgerApiMessage.Performative.ERROR:
                expected_nb_of_contents = 1
                if self.is_set("code"):
                    expected_nb_of_contents += 1
                    code = cast(int, self.code)
                    assert (
                        type(code) == int
                    ), "Invalid type for content 'code'. Expected 'int'. Found '{}'.".format(
                        type(code)
                    )
                if self.is_set("message"):
                    expected_nb_of_contents += 1
                    message = cast(str, self.message)
                    assert (
                        type(message) == str
                    ), "Invalid type for content 'message'. Expected 'str'. Found '{}'.".format(
                        type(message)
                    )
                assert (
                    type(self.data) == CustomAnyObject
                ), "Invalid type for content 'data'. Expected 'AnyObject'. Found '{}'.".format(
                    type(self.data)
                )

            # Check correct content count
            assert (
                expected_nb_of_contents == actual_nb_of_contents
            ), "Incorrect number of contents. Expected {}. Found {}".format(
                expected_nb_of_contents, actual_nb_of_contents
            )

            # Light Protocol Rule 3
            if self.message_id == 1:
                assert (
                    self.target == 0
                ), "Invalid 'target'. Expected 0 (because 'message_id' is 1). Found {}.".format(
                    self.target
                )
            else:
                assert (
                    0 < self.target < self.message_id
                ), "Invalid 'target'. Expected an integer between 1 and {} inclusive. Found {}.".format(
                    self.message_id - 1, self.target,
                )
        except (AssertionError, ValueError, KeyError) as e:
            logger.error(str(e))
            return False

        return True
