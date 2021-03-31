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

"""This module contains tac's message definition."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,too-many-branches,not-an-iterable,unidiomatic-typecheck,unsubscriptable-object
import logging
from typing import Any, Dict, Optional, Set, Tuple, cast

from aea.configurations.base import PublicId
from aea.exceptions import AEAEnforceError, enforce
from aea.protocols.base import Message

from packages.fetchai.protocols.tac.custom_types import ErrorCode as CustomErrorCode


_default_logger = logging.getLogger("aea.packages.fetchai.protocols.tac.message")

DEFAULT_BODY_SIZE = 4


class TacMessage(Message):
    """The tac protocol implements the messages an AEA needs to participate in the TAC."""

    protocol_id = PublicId.from_str("fetchai/tac:1.0.0")
    protocol_specification_id = PublicId.from_str("fetchai/tac:1.0.0")

    ErrorCode = CustomErrorCode

    class Performative(Message.Performative):
        """Performatives for the tac protocol."""

        CANCELLED = "cancelled"
        GAME_DATA = "game_data"
        REGISTER = "register"
        TAC_ERROR = "tac_error"
        TRANSACTION = "transaction"
        TRANSACTION_CONFIRMATION = "transaction_confirmation"
        UNREGISTER = "unregister"

        def __str__(self) -> str:
            """Get the string representation."""
            return str(self.value)

    _performatives = {
        "cancelled",
        "game_data",
        "register",
        "tac_error",
        "transaction",
        "transaction_confirmation",
        "unregister",
    }
    __slots__: Tuple[str, ...] = tuple()

    class _SlotsCls:
        __slots__ = (
            "agent_addr_to_name",
            "agent_name",
            "amount_by_currency_id",
            "counterparty_address",
            "counterparty_signature",
            "currency_id_to_name",
            "dialogue_reference",
            "error_code",
            "exchange_params_by_currency_id",
            "fee_by_currency_id",
            "good_id_to_name",
            "info",
            "ledger_id",
            "message_id",
            "nonce",
            "performative",
            "quantities_by_good_id",
            "sender_address",
            "sender_signature",
            "target",
            "transaction_id",
            "utility_params_by_good_id",
            "version_id",
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
        Initialise an instance of TacMessage.

        :param message_id: the message id.
        :param dialogue_reference: the dialogue reference.
        :param target: the message target.
        :param performative: the message performative.
        """
        super().__init__(
            dialogue_reference=dialogue_reference,
            message_id=message_id,
            target=target,
            performative=TacMessage.Performative(performative),
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
        return cast(TacMessage.Performative, self.get("performative"))

    @property
    def target(self) -> int:
        """Get the target of the message."""
        enforce(self.is_set("target"), "target is not set.")
        return cast(int, self.get("target"))

    @property
    def agent_addr_to_name(self) -> Dict[str, str]:
        """Get the 'agent_addr_to_name' content from the message."""
        enforce(
            self.is_set("agent_addr_to_name"),
            "'agent_addr_to_name' content is not set.",
        )
        return cast(Dict[str, str], self.get("agent_addr_to_name"))

    @property
    def agent_name(self) -> str:
        """Get the 'agent_name' content from the message."""
        enforce(self.is_set("agent_name"), "'agent_name' content is not set.")
        return cast(str, self.get("agent_name"))

    @property
    def amount_by_currency_id(self) -> Dict[str, int]:
        """Get the 'amount_by_currency_id' content from the message."""
        enforce(
            self.is_set("amount_by_currency_id"),
            "'amount_by_currency_id' content is not set.",
        )
        return cast(Dict[str, int], self.get("amount_by_currency_id"))

    @property
    def counterparty_address(self) -> str:
        """Get the 'counterparty_address' content from the message."""
        enforce(
            self.is_set("counterparty_address"),
            "'counterparty_address' content is not set.",
        )
        return cast(str, self.get("counterparty_address"))

    @property
    def counterparty_signature(self) -> str:
        """Get the 'counterparty_signature' content from the message."""
        enforce(
            self.is_set("counterparty_signature"),
            "'counterparty_signature' content is not set.",
        )
        return cast(str, self.get("counterparty_signature"))

    @property
    def currency_id_to_name(self) -> Dict[str, str]:
        """Get the 'currency_id_to_name' content from the message."""
        enforce(
            self.is_set("currency_id_to_name"),
            "'currency_id_to_name' content is not set.",
        )
        return cast(Dict[str, str], self.get("currency_id_to_name"))

    @property
    def error_code(self) -> CustomErrorCode:
        """Get the 'error_code' content from the message."""
        enforce(self.is_set("error_code"), "'error_code' content is not set.")
        return cast(CustomErrorCode, self.get("error_code"))

    @property
    def exchange_params_by_currency_id(self) -> Dict[str, float]:
        """Get the 'exchange_params_by_currency_id' content from the message."""
        enforce(
            self.is_set("exchange_params_by_currency_id"),
            "'exchange_params_by_currency_id' content is not set.",
        )
        return cast(Dict[str, float], self.get("exchange_params_by_currency_id"))

    @property
    def fee_by_currency_id(self) -> Dict[str, int]:
        """Get the 'fee_by_currency_id' content from the message."""
        enforce(
            self.is_set("fee_by_currency_id"),
            "'fee_by_currency_id' content is not set.",
        )
        return cast(Dict[str, int], self.get("fee_by_currency_id"))

    @property
    def good_id_to_name(self) -> Dict[str, str]:
        """Get the 'good_id_to_name' content from the message."""
        enforce(self.is_set("good_id_to_name"), "'good_id_to_name' content is not set.")
        return cast(Dict[str, str], self.get("good_id_to_name"))

    @property
    def info(self) -> Optional[Dict[str, str]]:
        """Get the 'info' content from the message."""
        return cast(Optional[Dict[str, str]], self.get("info"))

    @property
    def ledger_id(self) -> str:
        """Get the 'ledger_id' content from the message."""
        enforce(self.is_set("ledger_id"), "'ledger_id' content is not set.")
        return cast(str, self.get("ledger_id"))

    @property
    def nonce(self) -> str:
        """Get the 'nonce' content from the message."""
        enforce(self.is_set("nonce"), "'nonce' content is not set.")
        return cast(str, self.get("nonce"))

    @property
    def quantities_by_good_id(self) -> Dict[str, int]:
        """Get the 'quantities_by_good_id' content from the message."""
        enforce(
            self.is_set("quantities_by_good_id"),
            "'quantities_by_good_id' content is not set.",
        )
        return cast(Dict[str, int], self.get("quantities_by_good_id"))

    @property
    def sender_address(self) -> str:
        """Get the 'sender_address' content from the message."""
        enforce(self.is_set("sender_address"), "'sender_address' content is not set.")
        return cast(str, self.get("sender_address"))

    @property
    def sender_signature(self) -> str:
        """Get the 'sender_signature' content from the message."""
        enforce(
            self.is_set("sender_signature"), "'sender_signature' content is not set."
        )
        return cast(str, self.get("sender_signature"))

    @property
    def transaction_id(self) -> str:
        """Get the 'transaction_id' content from the message."""
        enforce(self.is_set("transaction_id"), "'transaction_id' content is not set.")
        return cast(str, self.get("transaction_id"))

    @property
    def utility_params_by_good_id(self) -> Dict[str, float]:
        """Get the 'utility_params_by_good_id' content from the message."""
        enforce(
            self.is_set("utility_params_by_good_id"),
            "'utility_params_by_good_id' content is not set.",
        )
        return cast(Dict[str, float], self.get("utility_params_by_good_id"))

    @property
    def version_id(self) -> str:
        """Get the 'version_id' content from the message."""
        enforce(self.is_set("version_id"), "'version_id' content is not set.")
        return cast(str, self.get("version_id"))

    def _is_consistent(self) -> bool:
        """Check that the message follows the tac protocol."""
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
                isinstance(self.performative, TacMessage.Performative),
                "Invalid 'performative'. Expected either of '{}'. Found '{}'.".format(
                    self.valid_performatives, self.performative
                ),
            )

            # Check correct contents
            actual_nb_of_contents = len(self._body) - DEFAULT_BODY_SIZE
            expected_nb_of_contents = 0
            if self.performative == TacMessage.Performative.REGISTER:
                expected_nb_of_contents = 1
                enforce(
                    isinstance(self.agent_name, str),
                    "Invalid type for content 'agent_name'. Expected 'str'. Found '{}'.".format(
                        type(self.agent_name)
                    ),
                )
            elif self.performative == TacMessage.Performative.UNREGISTER:
                expected_nb_of_contents = 0
            elif self.performative == TacMessage.Performative.TRANSACTION:
                expected_nb_of_contents = 10
                enforce(
                    isinstance(self.transaction_id, str),
                    "Invalid type for content 'transaction_id'. Expected 'str'. Found '{}'.".format(
                        type(self.transaction_id)
                    ),
                )
                enforce(
                    isinstance(self.ledger_id, str),
                    "Invalid type for content 'ledger_id'. Expected 'str'. Found '{}'.".format(
                        type(self.ledger_id)
                    ),
                )
                enforce(
                    isinstance(self.sender_address, str),
                    "Invalid type for content 'sender_address'. Expected 'str'. Found '{}'.".format(
                        type(self.sender_address)
                    ),
                )
                enforce(
                    isinstance(self.counterparty_address, str),
                    "Invalid type for content 'counterparty_address'. Expected 'str'. Found '{}'.".format(
                        type(self.counterparty_address)
                    ),
                )
                enforce(
                    isinstance(self.amount_by_currency_id, dict),
                    "Invalid type for content 'amount_by_currency_id'. Expected 'dict'. Found '{}'.".format(
                        type(self.amount_by_currency_id)
                    ),
                )
                for (
                    key_of_amount_by_currency_id,
                    value_of_amount_by_currency_id,
                ) in self.amount_by_currency_id.items():
                    enforce(
                        isinstance(key_of_amount_by_currency_id, str),
                        "Invalid type for dictionary keys in content 'amount_by_currency_id'. Expected 'str'. Found '{}'.".format(
                            type(key_of_amount_by_currency_id)
                        ),
                    )
                    enforce(
                        type(value_of_amount_by_currency_id) is int,
                        "Invalid type for dictionary values in content 'amount_by_currency_id'. Expected 'int'. Found '{}'.".format(
                            type(value_of_amount_by_currency_id)
                        ),
                    )
                enforce(
                    isinstance(self.fee_by_currency_id, dict),
                    "Invalid type for content 'fee_by_currency_id'. Expected 'dict'. Found '{}'.".format(
                        type(self.fee_by_currency_id)
                    ),
                )
                for (
                    key_of_fee_by_currency_id,
                    value_of_fee_by_currency_id,
                ) in self.fee_by_currency_id.items():
                    enforce(
                        isinstance(key_of_fee_by_currency_id, str),
                        "Invalid type for dictionary keys in content 'fee_by_currency_id'. Expected 'str'. Found '{}'.".format(
                            type(key_of_fee_by_currency_id)
                        ),
                    )
                    enforce(
                        type(value_of_fee_by_currency_id) is int,
                        "Invalid type for dictionary values in content 'fee_by_currency_id'. Expected 'int'. Found '{}'.".format(
                            type(value_of_fee_by_currency_id)
                        ),
                    )
                enforce(
                    isinstance(self.quantities_by_good_id, dict),
                    "Invalid type for content 'quantities_by_good_id'. Expected 'dict'. Found '{}'.".format(
                        type(self.quantities_by_good_id)
                    ),
                )
                for (
                    key_of_quantities_by_good_id,
                    value_of_quantities_by_good_id,
                ) in self.quantities_by_good_id.items():
                    enforce(
                        isinstance(key_of_quantities_by_good_id, str),
                        "Invalid type for dictionary keys in content 'quantities_by_good_id'. Expected 'str'. Found '{}'.".format(
                            type(key_of_quantities_by_good_id)
                        ),
                    )
                    enforce(
                        type(value_of_quantities_by_good_id) is int,
                        "Invalid type for dictionary values in content 'quantities_by_good_id'. Expected 'int'. Found '{}'.".format(
                            type(value_of_quantities_by_good_id)
                        ),
                    )
                enforce(
                    isinstance(self.nonce, str),
                    "Invalid type for content 'nonce'. Expected 'str'. Found '{}'.".format(
                        type(self.nonce)
                    ),
                )
                enforce(
                    isinstance(self.sender_signature, str),
                    "Invalid type for content 'sender_signature'. Expected 'str'. Found '{}'.".format(
                        type(self.sender_signature)
                    ),
                )
                enforce(
                    isinstance(self.counterparty_signature, str),
                    "Invalid type for content 'counterparty_signature'. Expected 'str'. Found '{}'.".format(
                        type(self.counterparty_signature)
                    ),
                )
            elif self.performative == TacMessage.Performative.CANCELLED:
                expected_nb_of_contents = 0
            elif self.performative == TacMessage.Performative.GAME_DATA:
                expected_nb_of_contents = 9
                enforce(
                    isinstance(self.amount_by_currency_id, dict),
                    "Invalid type for content 'amount_by_currency_id'. Expected 'dict'. Found '{}'.".format(
                        type(self.amount_by_currency_id)
                    ),
                )
                for (
                    key_of_amount_by_currency_id,
                    value_of_amount_by_currency_id,
                ) in self.amount_by_currency_id.items():
                    enforce(
                        isinstance(key_of_amount_by_currency_id, str),
                        "Invalid type for dictionary keys in content 'amount_by_currency_id'. Expected 'str'. Found '{}'.".format(
                            type(key_of_amount_by_currency_id)
                        ),
                    )
                    enforce(
                        type(value_of_amount_by_currency_id) is int,
                        "Invalid type for dictionary values in content 'amount_by_currency_id'. Expected 'int'. Found '{}'.".format(
                            type(value_of_amount_by_currency_id)
                        ),
                    )
                enforce(
                    isinstance(self.exchange_params_by_currency_id, dict),
                    "Invalid type for content 'exchange_params_by_currency_id'. Expected 'dict'. Found '{}'.".format(
                        type(self.exchange_params_by_currency_id)
                    ),
                )
                for (
                    key_of_exchange_params_by_currency_id,
                    value_of_exchange_params_by_currency_id,
                ) in self.exchange_params_by_currency_id.items():
                    enforce(
                        isinstance(key_of_exchange_params_by_currency_id, str),
                        "Invalid type for dictionary keys in content 'exchange_params_by_currency_id'. Expected 'str'. Found '{}'.".format(
                            type(key_of_exchange_params_by_currency_id)
                        ),
                    )
                    enforce(
                        isinstance(value_of_exchange_params_by_currency_id, float),
                        "Invalid type for dictionary values in content 'exchange_params_by_currency_id'. Expected 'float'. Found '{}'.".format(
                            type(value_of_exchange_params_by_currency_id)
                        ),
                    )
                enforce(
                    isinstance(self.quantities_by_good_id, dict),
                    "Invalid type for content 'quantities_by_good_id'. Expected 'dict'. Found '{}'.".format(
                        type(self.quantities_by_good_id)
                    ),
                )
                for (
                    key_of_quantities_by_good_id,
                    value_of_quantities_by_good_id,
                ) in self.quantities_by_good_id.items():
                    enforce(
                        isinstance(key_of_quantities_by_good_id, str),
                        "Invalid type for dictionary keys in content 'quantities_by_good_id'. Expected 'str'. Found '{}'.".format(
                            type(key_of_quantities_by_good_id)
                        ),
                    )
                    enforce(
                        type(value_of_quantities_by_good_id) is int,
                        "Invalid type for dictionary values in content 'quantities_by_good_id'. Expected 'int'. Found '{}'.".format(
                            type(value_of_quantities_by_good_id)
                        ),
                    )
                enforce(
                    isinstance(self.utility_params_by_good_id, dict),
                    "Invalid type for content 'utility_params_by_good_id'. Expected 'dict'. Found '{}'.".format(
                        type(self.utility_params_by_good_id)
                    ),
                )
                for (
                    key_of_utility_params_by_good_id,
                    value_of_utility_params_by_good_id,
                ) in self.utility_params_by_good_id.items():
                    enforce(
                        isinstance(key_of_utility_params_by_good_id, str),
                        "Invalid type for dictionary keys in content 'utility_params_by_good_id'. Expected 'str'. Found '{}'.".format(
                            type(key_of_utility_params_by_good_id)
                        ),
                    )
                    enforce(
                        isinstance(value_of_utility_params_by_good_id, float),
                        "Invalid type for dictionary values in content 'utility_params_by_good_id'. Expected 'float'. Found '{}'.".format(
                            type(value_of_utility_params_by_good_id)
                        ),
                    )
                enforce(
                    isinstance(self.fee_by_currency_id, dict),
                    "Invalid type for content 'fee_by_currency_id'. Expected 'dict'. Found '{}'.".format(
                        type(self.fee_by_currency_id)
                    ),
                )
                for (
                    key_of_fee_by_currency_id,
                    value_of_fee_by_currency_id,
                ) in self.fee_by_currency_id.items():
                    enforce(
                        isinstance(key_of_fee_by_currency_id, str),
                        "Invalid type for dictionary keys in content 'fee_by_currency_id'. Expected 'str'. Found '{}'.".format(
                            type(key_of_fee_by_currency_id)
                        ),
                    )
                    enforce(
                        type(value_of_fee_by_currency_id) is int,
                        "Invalid type for dictionary values in content 'fee_by_currency_id'. Expected 'int'. Found '{}'.".format(
                            type(value_of_fee_by_currency_id)
                        ),
                    )
                enforce(
                    isinstance(self.agent_addr_to_name, dict),
                    "Invalid type for content 'agent_addr_to_name'. Expected 'dict'. Found '{}'.".format(
                        type(self.agent_addr_to_name)
                    ),
                )
                for (
                    key_of_agent_addr_to_name,
                    value_of_agent_addr_to_name,
                ) in self.agent_addr_to_name.items():
                    enforce(
                        isinstance(key_of_agent_addr_to_name, str),
                        "Invalid type for dictionary keys in content 'agent_addr_to_name'. Expected 'str'. Found '{}'.".format(
                            type(key_of_agent_addr_to_name)
                        ),
                    )
                    enforce(
                        isinstance(value_of_agent_addr_to_name, str),
                        "Invalid type for dictionary values in content 'agent_addr_to_name'. Expected 'str'. Found '{}'.".format(
                            type(value_of_agent_addr_to_name)
                        ),
                    )
                enforce(
                    isinstance(self.currency_id_to_name, dict),
                    "Invalid type for content 'currency_id_to_name'. Expected 'dict'. Found '{}'.".format(
                        type(self.currency_id_to_name)
                    ),
                )
                for (
                    key_of_currency_id_to_name,
                    value_of_currency_id_to_name,
                ) in self.currency_id_to_name.items():
                    enforce(
                        isinstance(key_of_currency_id_to_name, str),
                        "Invalid type for dictionary keys in content 'currency_id_to_name'. Expected 'str'. Found '{}'.".format(
                            type(key_of_currency_id_to_name)
                        ),
                    )
                    enforce(
                        isinstance(value_of_currency_id_to_name, str),
                        "Invalid type for dictionary values in content 'currency_id_to_name'. Expected 'str'. Found '{}'.".format(
                            type(value_of_currency_id_to_name)
                        ),
                    )
                enforce(
                    isinstance(self.good_id_to_name, dict),
                    "Invalid type for content 'good_id_to_name'. Expected 'dict'. Found '{}'.".format(
                        type(self.good_id_to_name)
                    ),
                )
                for (
                    key_of_good_id_to_name,
                    value_of_good_id_to_name,
                ) in self.good_id_to_name.items():
                    enforce(
                        isinstance(key_of_good_id_to_name, str),
                        "Invalid type for dictionary keys in content 'good_id_to_name'. Expected 'str'. Found '{}'.".format(
                            type(key_of_good_id_to_name)
                        ),
                    )
                    enforce(
                        isinstance(value_of_good_id_to_name, str),
                        "Invalid type for dictionary values in content 'good_id_to_name'. Expected 'str'. Found '{}'.".format(
                            type(value_of_good_id_to_name)
                        ),
                    )
                enforce(
                    isinstance(self.version_id, str),
                    "Invalid type for content 'version_id'. Expected 'str'. Found '{}'.".format(
                        type(self.version_id)
                    ),
                )
                if self.is_set("info"):
                    expected_nb_of_contents += 1
                    info = cast(Dict[str, str], self.info)
                    enforce(
                        isinstance(info, dict),
                        "Invalid type for content 'info'. Expected 'dict'. Found '{}'.".format(
                            type(info)
                        ),
                    )
                    for key_of_info, value_of_info in info.items():
                        enforce(
                            isinstance(key_of_info, str),
                            "Invalid type for dictionary keys in content 'info'. Expected 'str'. Found '{}'.".format(
                                type(key_of_info)
                            ),
                        )
                        enforce(
                            isinstance(value_of_info, str),
                            "Invalid type for dictionary values in content 'info'. Expected 'str'. Found '{}'.".format(
                                type(value_of_info)
                            ),
                        )
            elif self.performative == TacMessage.Performative.TRANSACTION_CONFIRMATION:
                expected_nb_of_contents = 3
                enforce(
                    isinstance(self.transaction_id, str),
                    "Invalid type for content 'transaction_id'. Expected 'str'. Found '{}'.".format(
                        type(self.transaction_id)
                    ),
                )
                enforce(
                    isinstance(self.amount_by_currency_id, dict),
                    "Invalid type for content 'amount_by_currency_id'. Expected 'dict'. Found '{}'.".format(
                        type(self.amount_by_currency_id)
                    ),
                )
                for (
                    key_of_amount_by_currency_id,
                    value_of_amount_by_currency_id,
                ) in self.amount_by_currency_id.items():
                    enforce(
                        isinstance(key_of_amount_by_currency_id, str),
                        "Invalid type for dictionary keys in content 'amount_by_currency_id'. Expected 'str'. Found '{}'.".format(
                            type(key_of_amount_by_currency_id)
                        ),
                    )
                    enforce(
                        type(value_of_amount_by_currency_id) is int,
                        "Invalid type for dictionary values in content 'amount_by_currency_id'. Expected 'int'. Found '{}'.".format(
                            type(value_of_amount_by_currency_id)
                        ),
                    )
                enforce(
                    isinstance(self.quantities_by_good_id, dict),
                    "Invalid type for content 'quantities_by_good_id'. Expected 'dict'. Found '{}'.".format(
                        type(self.quantities_by_good_id)
                    ),
                )
                for (
                    key_of_quantities_by_good_id,
                    value_of_quantities_by_good_id,
                ) in self.quantities_by_good_id.items():
                    enforce(
                        isinstance(key_of_quantities_by_good_id, str),
                        "Invalid type for dictionary keys in content 'quantities_by_good_id'. Expected 'str'. Found '{}'.".format(
                            type(key_of_quantities_by_good_id)
                        ),
                    )
                    enforce(
                        type(value_of_quantities_by_good_id) is int,
                        "Invalid type for dictionary values in content 'quantities_by_good_id'. Expected 'int'. Found '{}'.".format(
                            type(value_of_quantities_by_good_id)
                        ),
                    )
            elif self.performative == TacMessage.Performative.TAC_ERROR:
                expected_nb_of_contents = 1
                enforce(
                    isinstance(self.error_code, CustomErrorCode),
                    "Invalid type for content 'error_code'. Expected 'ErrorCode'. Found '{}'.".format(
                        type(self.error_code)
                    ),
                )
                if self.is_set("info"):
                    expected_nb_of_contents += 1
                    info = cast(Dict[str, str], self.info)
                    enforce(
                        isinstance(info, dict),
                        "Invalid type for content 'info'. Expected 'dict'. Found '{}'.".format(
                            type(info)
                        ),
                    )
                    for key_of_info, value_of_info in info.items():
                        enforce(
                            isinstance(key_of_info, str),
                            "Invalid type for dictionary keys in content 'info'. Expected 'str'. Found '{}'.".format(
                                type(key_of_info)
                            ),
                        )
                        enforce(
                            isinstance(value_of_info, str),
                            "Invalid type for dictionary values in content 'info'. Expected 'str'. Found '{}'.".format(
                                type(value_of_info)
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
