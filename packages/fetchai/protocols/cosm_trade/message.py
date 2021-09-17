# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2021 fetchai
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

"""This module contains cosm_trade's message definition."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,too-many-branches,not-an-iterable,unidiomatic-typecheck,unsubscriptable-object
import logging
from typing import Any, Optional, Set, Tuple, cast

from aea.configurations.base import PublicId
from aea.exceptions import AEAEnforceError, enforce
from aea.protocols.base import Message

from packages.fetchai.protocols.cosm_trade.custom_types import (
    SignedTransaction as CustomSignedTransaction,
)


_default_logger = logging.getLogger("aea.packages.fetchai.protocols.cosm_trade.message")

DEFAULT_BODY_SIZE = 4


class CosmTradeMessage(Message):
    """A protocol for preparing an atomic swap bilateral transaction for cosmos-based ledgers, including fetchai's."""

    protocol_id = PublicId.from_str("fetchai/cosm_trade:0.1.0")
    protocol_specification_id = PublicId.from_str("fetchai/cosm_trade:1.0.0")

    SignedTransaction = CustomSignedTransaction

    class Performative(Message.Performative):
        """Performatives for the cosm_trade protocol."""

        END = "end"
        ERROR = "error"
        INFORM_PUBLIC_KEY = "inform_public_key"
        INFORM_SIGNED_TRANSACTION = "inform_signed_transaction"

        def __str__(self) -> str:
            """Get the string representation."""
            return str(self.value)

    _performatives = {"end", "error", "inform_public_key", "inform_signed_transaction"}
    __slots__: Tuple[str, ...] = tuple()

    class _SlotsCls:
        __slots__ = (
            "code",
            "data",
            "dialogue_reference",
            "fipa_dialogue_id",
            "message",
            "message_id",
            "performative",
            "public_key",
            "signed_transaction",
            "target",
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
        Initialise an instance of CosmTradeMessage.

        :param message_id: the message id.
        :param dialogue_reference: the dialogue reference.
        :param target: the message target.
        :param performative: the message performative.
        """
        super().__init__(
            dialogue_reference=dialogue_reference,
            message_id=message_id,
            target=target,
            performative=CosmTradeMessage.Performative(performative),
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
        return cast(CosmTradeMessage.Performative, self.get("performative"))

    @property
    def target(self) -> int:
        """Get the target of the message."""
        enforce(self.is_set("target"), "target is not set.")
        return cast(int, self.get("target"))

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
    def fipa_dialogue_id(self) -> Optional[Tuple[str, ...]]:
        """Get the 'fipa_dialogue_id' content from the message."""
        return cast(Optional[Tuple[str, ...]], self.get("fipa_dialogue_id"))

    @property
    def message(self) -> Optional[str]:
        """Get the 'message' content from the message."""
        return cast(Optional[str], self.get("message"))

    @property
    def public_key(self) -> str:
        """Get the 'public_key' content from the message."""
        enforce(self.is_set("public_key"), "'public_key' content is not set.")
        return cast(str, self.get("public_key"))

    @property
    def signed_transaction(self) -> CustomSignedTransaction:
        """Get the 'signed_transaction' content from the message."""
        enforce(
            self.is_set("signed_transaction"),
            "'signed_transaction' content is not set.",
        )
        return cast(CustomSignedTransaction, self.get("signed_transaction"))

    def _is_consistent(self) -> bool:
        """Check that the message follows the cosm_trade protocol."""
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
                isinstance(self.performative, CosmTradeMessage.Performative),
                "Invalid 'performative'. Expected either of '{}'. Found '{}'.".format(
                    self.valid_performatives, self.performative
                ),
            )

            # Check correct contents
            actual_nb_of_contents = len(self._body) - DEFAULT_BODY_SIZE
            expected_nb_of_contents = 0
            if self.performative == CosmTradeMessage.Performative.INFORM_PUBLIC_KEY:
                expected_nb_of_contents = 1
                enforce(
                    isinstance(self.public_key, str),
                    "Invalid type for content 'public_key'. Expected 'str'. Found '{}'.".format(
                        type(self.public_key)
                    ),
                )
            elif (
                self.performative
                == CosmTradeMessage.Performative.INFORM_SIGNED_TRANSACTION
            ):
                expected_nb_of_contents = 1
                enforce(
                    isinstance(self.signed_transaction, CustomSignedTransaction),
                    "Invalid type for content 'signed_transaction'. Expected 'SignedTransaction'. Found '{}'.".format(
                        type(self.signed_transaction)
                    ),
                )
                if self.is_set("fipa_dialogue_id"):
                    expected_nb_of_contents += 1
                    fipa_dialogue_id = cast(Tuple[str, ...], self.fipa_dialogue_id)
                    enforce(
                        isinstance(fipa_dialogue_id, tuple),
                        "Invalid type for content 'fipa_dialogue_id'. Expected 'tuple'. Found '{}'.".format(
                            type(fipa_dialogue_id)
                        ),
                    )
                    enforce(
                        all(isinstance(element, str) for element in fipa_dialogue_id),
                        "Invalid type for tuple elements in content 'fipa_dialogue_id'. Expected 'str'.",
                    )
            elif self.performative == CosmTradeMessage.Performative.ERROR:
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
            elif self.performative == CosmTradeMessage.Performative.END:
                expected_nb_of_contents = 0

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
