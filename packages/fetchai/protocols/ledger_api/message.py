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
from typing import Dict, Set, Tuple, cast

from aea.configurations.base import ProtocolId
from aea.protocols.base import Message

logger = logging.getLogger("aea.packages.fetchai.protocols.ledger_api.message")

DEFAULT_BODY_SIZE = 4


class LedgerApiMessage(Message):
    """A protocol for ledger APIs requests and responses."""

    protocol_id = ProtocolId("fetchai", "ledger_api", "0.1.0")

    class Performative(Enum):
        """Performatives for the ledger_api protocol."""

        BALANCE = "balance"
        GENERATE_TX_NONCE = "generate_tx_nonce"
        GET_BALANCE = "get_balance"
        GET_TRANSACTION_RECEIPT = "get_transaction_receipt"
        IS_TRANSACTION_SETTLED = "is_transaction_settled"
        IS_TRANSACTION_VALID = "is_transaction_valid"
        TRANSFER = "transfer"
        TX_DIGEST = "tx_digest"

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
            "generate_tx_nonce",
            "get_balance",
            "get_transaction_receipt",
            "is_transaction_settled",
            "is_transaction_valid",
            "transfer",
            "tx_digest",
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
    def performative(self) -> Performative:  # noqa: F821
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
    def data(self) -> Dict[str, str]:
        """Get the 'data' content from the message."""
        assert self.is_set("data"), "'data' content is not set."
        return cast(Dict[str, str], self.get("data"))

    @property
    def destination_address(self) -> str:
        """Get the 'destination_address' content from the message."""
        assert self.is_set(
            "destination_address"
        ), "'destination_address' content is not set."
        return cast(str, self.get("destination_address"))

    @property
    def ledger_id(self) -> str:
        """Get the 'ledger_id' content from the message."""
        assert self.is_set("ledger_id"), "'ledger_id' content is not set."
        return cast(str, self.get("ledger_id"))

    @property
    def tx_digest(self) -> str:
        """Get the 'tx_digest' content from the message."""
        assert self.is_set("tx_digest"), "'tx_digest' content is not set."
        return cast(str, self.get("tx_digest"))

    @property
    def tx_fee(self) -> int:
        """Get the 'tx_fee' content from the message."""
        assert self.is_set("tx_fee"), "'tx_fee' content is not set."
        return cast(int, self.get("tx_fee"))

    @property
    def tx_nonce(self) -> int:
        """Get the 'tx_nonce' content from the message."""
        assert self.is_set("tx_nonce"), "'tx_nonce' content is not set."
        return cast(int, self.get("tx_nonce"))

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
            elif self.performative == LedgerApiMessage.Performative.TRANSFER:
                expected_nb_of_contents = 6
                assert (
                    type(self.ledger_id) == str
                ), "Invalid type for content 'ledger_id'. Expected 'str'. Found '{}'.".format(
                    type(self.ledger_id)
                )
                assert (
                    type(self.destination_address) == str
                ), "Invalid type for content 'destination_address'. Expected 'str'. Found '{}'.".format(
                    type(self.destination_address)
                )
                assert (
                    type(self.amount) == int
                ), "Invalid type for content 'amount'. Expected 'int'. Found '{}'.".format(
                    type(self.amount)
                )
                assert (
                    type(self.tx_fee) == int
                ), "Invalid type for content 'tx_fee'. Expected 'int'. Found '{}'.".format(
                    type(self.tx_fee)
                )
                assert (
                    type(self.tx_nonce) == int
                ), "Invalid type for content 'tx_nonce'. Expected 'int'. Found '{}'.".format(
                    type(self.tx_nonce)
                )
                assert (
                    type(self.data) == dict
                ), "Invalid type for content 'data'. Expected 'dict'. Found '{}'.".format(
                    type(self.data)
                )
                for key_of_data, value_of_data in self.data.items():
                    assert (
                        type(key_of_data) == str
                    ), "Invalid type for dictionary keys in content 'data'. Expected 'str'. Found '{}'.".format(
                        type(key_of_data)
                    )
                    assert (
                        type(value_of_data) == str
                    ), "Invalid type for dictionary values in content 'data'. Expected 'str'. Found '{}'.".format(
                        type(value_of_data)
                    )
            elif (
                self.performative
                == LedgerApiMessage.Performative.IS_TRANSACTION_SETTLED
            ):
                expected_nb_of_contents = 2
                assert (
                    type(self.ledger_id) == str
                ), "Invalid type for content 'ledger_id'. Expected 'str'. Found '{}'.".format(
                    type(self.ledger_id)
                )
                assert (
                    type(self.tx_digest) == str
                ), "Invalid type for content 'tx_digest'. Expected 'str'. Found '{}'.".format(
                    type(self.tx_digest)
                )
            elif (
                self.performative == LedgerApiMessage.Performative.IS_TRANSACTION_VALID
            ):
                expected_nb_of_contents = 2
                assert (
                    type(self.ledger_id) == str
                ), "Invalid type for content 'ledger_id'. Expected 'str'. Found '{}'.".format(
                    type(self.ledger_id)
                )
                assert (
                    type(self.tx_digest) == str
                ), "Invalid type for content 'tx_digest'. Expected 'str'. Found '{}'.".format(
                    type(self.tx_digest)
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
                    type(self.tx_digest) == str
                ), "Invalid type for content 'tx_digest'. Expected 'str'. Found '{}'.".format(
                    type(self.tx_digest)
                )
            elif self.performative == LedgerApiMessage.Performative.GENERATE_TX_NONCE:
                expected_nb_of_contents = 1
                assert (
                    type(self.ledger_id) == str
                ), "Invalid type for content 'ledger_id'. Expected 'str'. Found '{}'.".format(
                    type(self.ledger_id)
                )
            elif self.performative == LedgerApiMessage.Performative.BALANCE:
                expected_nb_of_contents = 1
                assert (
                    type(self.ledger_id) == str
                ), "Invalid type for content 'ledger_id'. Expected 'str'. Found '{}'.".format(
                    type(self.ledger_id)
                )
            elif self.performative == LedgerApiMessage.Performative.TX_DIGEST:
                expected_nb_of_contents = 0

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
