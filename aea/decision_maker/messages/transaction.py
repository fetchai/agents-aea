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

"""The transaction message module."""

import logging
from enum import Enum
from typing import Any, Dict, Tuple, cast

from aea.configurations.base import PublicId
from aea.decision_maker.messages.base import InternalMessage
from aea.helpers.transaction.base import Terms

logger = logging.getLogger(__name__)

DEFAULT_BODY_SIZE = 3


class TransactionMessage(InternalMessage):
    """A protocol for communication between skills and decision maker."""

    class ErrorCode(Enum):
        """ErrorCodes for the transaction protocol."""

        UNSUCCESSFUL_MESSAGE_SIGNING = "unsuccessful_message_signing"
        UNSUCCESSFUL_TRANSACTION_SIGNING = "unsuccessful_transaction_signing"

        def __str__(self):
            """Get the string representation."""
            return str(self.value)

    class Performative(Enum):
        """Performatives for the transaction protocol."""

        ERROR = "error"
        SIGN_MESSAGE = "sign_message"
        SIGN_TRANSACTION = "sign_transaction"
        SIGNED_MESSAGE = "signed_message"
        SIGNED_TRANSACTION = "signed_transaction"

        def __str__(self):
            """Get the string representation."""
            return str(self.value)

    def __init__(
        self,
        performative: Performative,
        skill_callback_ids: Tuple[PublicId, ...],
        **kwargs,
    ):
        """
        Initialise an instance of TransactionMessage.

        :param performative: the message performative.
        :param skill_callback_ids: the ids of the skills to respond to.
        """
        super().__init__(
            performative=TransactionMessage.Performative(performative),
            skill_callback_ids=skill_callback_ids,
            **kwargs,
        )
        self._performatives = {
            "error",
            "sign_message",
            "sign_transaction",
            "signed_message",
            "signed_transaction",
        }

    @property
    def performative(self) -> Performative:  # type: ignore # noqa: F821
        """Get the performative of the message."""
        assert self.is_set("performative"), "performative is not set."
        return cast(TransactionMessage.Performative, self.get("performative"))

    @property
    def error_code(self) -> ErrorCode:  # type: ignore # noqa: F821
        """Get the 'error_code' content from the message."""
        assert self.is_set("error_code"), "'error_code' content is not set."
        return cast(TransactionMessage.ErrorCode, self.get("error_code"))

    @property
    def message(self) -> bytes:
        """Get the 'message' content from the message."""
        assert self.is_set("message"), "'message' content is not set."
        return cast(bytes, self.get("message"))

    @property
    def signed_message(self) -> str:
        """Get the 'signed_message' content from the message."""
        assert self.is_set("signed_message"), "'signed_message' content is not set."
        return cast(str, self.get("signed_message"))

    @property
    def signed_transaction(self) -> Any:
        """Get the 'signed_transaction' content from the message."""
        assert self.is_set(
            "signed_transaction"
        ), "'signed_transaction' content is not set."
        return cast(Any, self.get("signed_transaction"))

    @property
    def skill_callback_ids(self) -> Tuple[PublicId, ...]:
        """Get the 'skill_callback_ids' content from the message."""
        assert self.is_set(
            "skill_callback_ids"
        ), "'skill_callback_ids' content is not set."
        return cast(Tuple[PublicId, ...], self.get("skill_callback_ids"))

    @property
    def has_skill_callback_info(self) -> bool:
        """Check if skill_callback_info is set."""
        return self.is_set("skill_callback_info")

    @property
    def skill_callback_info(self) -> Dict[str, Any]:
        """Get the 'skill_callback_info' content from the message."""
        assert self.is_set(
            "skill_callback_info"
        ), "'skill_callback_info' content is not set."
        return cast(Dict[str, Any], self.get("skill_callback_info"))

    @property
    def has_terms(self) -> bool:
        """Check if terms are set."""
        return self.is_set("terms")

    @property
    def terms(self) -> Terms:
        """Get the 'terms' content from the message."""
        assert self.is_set("terms"), "'terms' content is not set."
        return cast(Terms, self.get("terms"))

    @property
    def transaction(self) -> Any:
        """Get the 'transaction' content from the message."""
        assert self.is_set("transaction"), "'transaction' content is not set."
        return cast(Any, self.get("transaction"))

    @property
    def is_deprecated_signing_mode(self) -> bool:
        """Get the 'is_deprecated_signing_mode' content from the message."""
        if self.is_set("is_deprecated_signing_mode"):
            return cast(bool, self.get("is_deprecated_signing_mode"))
        else:
            return False

    @property
    def crypto_id(self) -> str:
        """Get the 'crypto_id' content from the message."""
        assert self.is_set("crypto_id"), "'crypto_id' content is not set."
        return cast(str, self.get("crypto_id"))

    @property
    def optional_callback_kwargs(self) -> Dict[str, Dict[str, Any]]:
        """Get the call back kwargs."""
        optional_callback_kwargs = {}  # type: Dict[str, Dict[str, Any]]
        if self.has_skill_callback_info:
            optional_callback_kwargs["skill_callback_info"] = self.skill_callback_info
        return optional_callback_kwargs

    def _is_consistent(self) -> bool:
        """Check that the message follows the transaction protocol."""
        try:
            # Light Protocol Rule 2
            # Check correct performative
            extra = 0
            assert (
                type(self.performative) == TransactionMessage.Performative
            ), "Invalid 'performative'. Expected either of '{}'. Found '{}'.".format(
                [e.value for e in TransactionMessage.Performative], self.performative
            )
            assert (
                type(self.skill_callback_ids) == tuple
            ), "Invalid type for content 'skill_callback_ids'. Expected 'tuple'. Found '{}'.".format(
                type(self.skill_callback_ids)
            )
            assert all(
                type(element) == PublicId for element in self.skill_callback_ids
            ), "Invalid type for tuple elements in content 'skill_callback_ids'. Expected 'PublicId'."
            assert (
                type(self.crypto_id) == str
            ), "Invalid type for content 'crypto_id'. Expected 'str'. Found '{}'.".format(
                type(self.crypto_id)
            )
            if self.has_skill_callback_info:
                extra = 1
                assert (
                    type(self.skill_callback_info) == dict
                ), "Invalid type for content 'skill_callback_info'. Expected 'dict'. Found '{}'.".format(
                    type(self.skill_callback_info)
                )
                for key_of_skill_callback_info in self.skill_callback_info.keys():
                    assert (
                        type(key_of_skill_callback_info) == str
                    ), "Invalid type for dictionary keys in content 'skill_callback_info'. Expected 'str'. Found '{}'.".format(
                        type(key_of_skill_callback_info)
                    )
                    # values can be of any type!

            # Check correct contents
            actual_nb_of_contents = len(self.body) - (DEFAULT_BODY_SIZE + extra)
            expected_nb_of_contents = 0
            if self.performative == TransactionMessage.Performative.SIGN_TRANSACTION:
                expected_nb_of_contents = 1
                if self.has_terms:
                    expected_nb_of_contents += 1
                    assert (
                        type(self.terms) == Terms
                    ), "Invalid type for content 'terms'. Expected 'Terms'. Found '{}'.".format(
                        type(self.terms)
                    )
                assert self.transaction
            elif self.performative == TransactionMessage.Performative.SIGN_MESSAGE:
                expected_nb_of_contents = 1
                if self.has_terms:
                    expected_nb_of_contents += 1
                    assert (
                        type(self.terms) == Terms
                    ), "Invalid type for content 'terms'. Expected 'Terms'. Found '{}'.".format(
                        type(self.terms)
                    )
                if self.is_set("is_deprecated_signing_mode"):
                    expected_nb_of_contents += 1
                    assert (
                        type(self.is_deprecated_signing_mode) == bool
                    ), "Invalid type for content 'is_deprecated_signing_mode'. Expected 'bool'. Found '{}'.".format(
                        type(self.is_deprecated_signing_mode)
                    )
                assert (
                    type(self.message) == bytes
                ), "Invalid type for content 'message'. Expected 'bytes'. Found '{}'.".format(
                    type(self.message)
                )
            elif (
                self.performative == TransactionMessage.Performative.SIGNED_TRANSACTION
            ):
                expected_nb_of_contents = 1
                assert self.signed_transaction
            elif self.performative == TransactionMessage.Performative.SIGNED_MESSAGE:
                expected_nb_of_contents = 1
                assert (
                    type(self.signed_message) == str
                ), "Invalid type for content 'signed_message'. Expected 'str'. Found '{}'.".format(
                    type(self.signed_message)
                )
            elif self.performative == TransactionMessage.Performative.ERROR:
                expected_nb_of_contents = 1
                assert (
                    type(self.error_code) == TransactionMessage.ErrorCode
                ), "Invalid type for content 'error_code'. Expected 'ErrorCode'. Found '{}'.".format(
                    type(self.error_code)
                )

            # Check correct content count
            assert (
                expected_nb_of_contents == actual_nb_of_contents
            ), "Incorrect number of contents. Expected {}. Found {}".format(
                expected_nb_of_contents, actual_nb_of_contents
            )
        except (AssertionError, ValueError, KeyError) as e:
            logger.error(str(e))
            return False

        return True
