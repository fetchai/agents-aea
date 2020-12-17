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

"""This module contains signing's message definition."""

import logging
from typing import Set, Tuple, cast

from aea.configurations.base import PublicId
from aea.exceptions import AEAEnforceError, enforce
from aea.protocols.base import Message

from packages.fetchai.protocols.signing.custom_types import ErrorCode as CustomErrorCode
from packages.fetchai.protocols.signing.custom_types import (
    RawMessage as CustomRawMessage,
)
from packages.fetchai.protocols.signing.custom_types import (
    RawTransaction as CustomRawTransaction,
)
from packages.fetchai.protocols.signing.custom_types import (
    SignedMessage as CustomSignedMessage,
)
from packages.fetchai.protocols.signing.custom_types import (
    SignedTransaction as CustomSignedTransaction,
)
from packages.fetchai.protocols.signing.custom_types import Terms as CustomTerms


_default_logger = logging.getLogger("aea.packages.fetchai.protocols.signing.message")

DEFAULT_BODY_SIZE = 4


class SigningMessage(Message):
    """A protocol for communication between skills and decision maker."""

    protocol_id = PublicId.from_str("fetchai/signing:0.8.0")

    ErrorCode = CustomErrorCode

    RawMessage = CustomRawMessage

    RawTransaction = CustomRawTransaction

    SignedMessage = CustomSignedMessage

    SignedTransaction = CustomSignedTransaction

    Terms = CustomTerms

    class Performative(Message.Performative):
        """Performatives for the signing protocol."""

        ERROR = "error"
        SIGN_MESSAGE = "sign_message"
        SIGN_TRANSACTION = "sign_transaction"
        SIGNED_MESSAGE = "signed_message"
        SIGNED_TRANSACTION = "signed_transaction"

        def __str__(self):
            """Get the string representation."""
            return str(self.value)

    _performatives = {
        "error",
        "sign_message",
        "sign_transaction",
        "signed_message",
        "signed_transaction",
    }
    __slots__: Tuple[str, ...] = tuple()

    class _SlotsCls:
        __slots__ = (
            "dialogue_reference",
            "error_code",
            "message_id",
            "performative",
            "raw_message",
            "raw_transaction",
            "signed_message",
            "signed_transaction",
            "target",
            "terms",
        )

    def __init__(
        self,
        performative: Performative,
        dialogue_reference: Tuple[str, str] = ("", ""),
        message_id: int = 1,
        target: int = 0,
        **kwargs,
    ):
        """
        Initialise an instance of SigningMessage.

        :param message_id: the message id.
        :param dialogue_reference: the dialogue reference.
        :param target: the message target.
        :param performative: the message performative.
        """
        super().__init__(
            dialogue_reference=dialogue_reference,
            message_id=message_id,
            target=target,
            performative=SigningMessage.Performative(performative),
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
        return cast(SigningMessage.Performative, self.get("performative"))

    @property
    def target(self) -> int:
        """Get the target of the message."""
        enforce(self.is_set("target"), "target is not set.")
        return cast(int, self.get("target"))

    @property
    def error_code(self) -> CustomErrorCode:
        """Get the 'error_code' content from the message."""
        enforce(self.is_set("error_code"), "'error_code' content is not set.")
        return cast(CustomErrorCode, self.get("error_code"))

    @property
    def raw_message(self) -> CustomRawMessage:
        """Get the 'raw_message' content from the message."""
        enforce(self.is_set("raw_message"), "'raw_message' content is not set.")
        return cast(CustomRawMessage, self.get("raw_message"))

    @property
    def raw_transaction(self) -> CustomRawTransaction:
        """Get the 'raw_transaction' content from the message."""
        enforce(self.is_set("raw_transaction"), "'raw_transaction' content is not set.")
        return cast(CustomRawTransaction, self.get("raw_transaction"))

    @property
    def signed_message(self) -> CustomSignedMessage:
        """Get the 'signed_message' content from the message."""
        enforce(self.is_set("signed_message"), "'signed_message' content is not set.")
        return cast(CustomSignedMessage, self.get("signed_message"))

    @property
    def signed_transaction(self) -> CustomSignedTransaction:
        """Get the 'signed_transaction' content from the message."""
        enforce(
            self.is_set("signed_transaction"),
            "'signed_transaction' content is not set.",
        )
        return cast(CustomSignedTransaction, self.get("signed_transaction"))

    @property
    def terms(self) -> CustomTerms:
        """Get the 'terms' content from the message."""
        enforce(self.is_set("terms"), "'terms' content is not set.")
        return cast(CustomTerms, self.get("terms"))

    def _is_consistent(self) -> bool:
        """Check that the message follows the signing protocol."""
        try:
            enforce(
                type(self.dialogue_reference) == tuple,
                "Invalid type for 'dialogue_reference'. Expected 'tuple'. Found '{}'.".format(
                    type(self.dialogue_reference)
                ),
            )
            enforce(
                type(self.dialogue_reference[0]) == str,
                "Invalid type for 'dialogue_reference[0]'. Expected 'str'. Found '{}'.".format(
                    type(self.dialogue_reference[0])
                ),
            )
            enforce(
                type(self.dialogue_reference[1]) == str,
                "Invalid type for 'dialogue_reference[1]'. Expected 'str'. Found '{}'.".format(
                    type(self.dialogue_reference[1])
                ),
            )
            enforce(
                type(self.message_id) == int,
                "Invalid type for 'message_id'. Expected 'int'. Found '{}'.".format(
                    type(self.message_id)
                ),
            )
            enforce(
                type(self.target) == int,
                "Invalid type for 'target'. Expected 'int'. Found '{}'.".format(
                    type(self.target)
                ),
            )

            # Light Protocol Rule 2
            # Check correct performative
            enforce(
                type(self.performative) == SigningMessage.Performative,
                "Invalid 'performative'. Expected either of '{}'. Found '{}'.".format(
                    self.valid_performatives, self.performative
                ),
            )

            # Check correct contents
            actual_nb_of_contents = len(self._body) - DEFAULT_BODY_SIZE
            expected_nb_of_contents = 0
            if self.performative == SigningMessage.Performative.SIGN_TRANSACTION:
                expected_nb_of_contents = 2
                enforce(
                    type(self.terms) == CustomTerms,
                    "Invalid type for content 'terms'. Expected 'Terms'. Found '{}'.".format(
                        type(self.terms)
                    ),
                )
                enforce(
                    type(self.raw_transaction) == CustomRawTransaction,
                    "Invalid type for content 'raw_transaction'. Expected 'RawTransaction'. Found '{}'.".format(
                        type(self.raw_transaction)
                    ),
                )
            elif self.performative == SigningMessage.Performative.SIGN_MESSAGE:
                expected_nb_of_contents = 2
                enforce(
                    type(self.terms) == CustomTerms,
                    "Invalid type for content 'terms'. Expected 'Terms'. Found '{}'.".format(
                        type(self.terms)
                    ),
                )
                enforce(
                    type(self.raw_message) == CustomRawMessage,
                    "Invalid type for content 'raw_message'. Expected 'RawMessage'. Found '{}'.".format(
                        type(self.raw_message)
                    ),
                )
            elif self.performative == SigningMessage.Performative.SIGNED_TRANSACTION:
                expected_nb_of_contents = 1
                enforce(
                    type(self.signed_transaction) == CustomSignedTransaction,
                    "Invalid type for content 'signed_transaction'. Expected 'SignedTransaction'. Found '{}'.".format(
                        type(self.signed_transaction)
                    ),
                )
            elif self.performative == SigningMessage.Performative.SIGNED_MESSAGE:
                expected_nb_of_contents = 1
                enforce(
                    type(self.signed_message) == CustomSignedMessage,
                    "Invalid type for content 'signed_message'. Expected 'SignedMessage'. Found '{}'.".format(
                        type(self.signed_message)
                    ),
                )
            elif self.performative == SigningMessage.Performative.ERROR:
                expected_nb_of_contents = 1
                enforce(
                    type(self.error_code) == CustomErrorCode,
                    "Invalid type for content 'error_code'. Expected 'ErrorCode'. Found '{}'.".format(
                        type(self.error_code)
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
            else:
                enforce(
                    0 < self.target < self.message_id,
                    "Invalid 'target'. Expected an integer between 1 and {} inclusive. Found {}.".format(
                        self.message_id - 1, self.target,
                    ),
                )
        except (AEAEnforceError, ValueError, KeyError) as e:
            _default_logger.error(str(e))
            return False

        return True
