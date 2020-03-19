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

"""This module contains the default message definition."""

from collections import defaultdict
from enum import Enum
from typing import Any, Dict, cast

from aea.configurations.base import PublicId
from aea.mail.base import Address
from aea.protocols.base import Message


class TACMessage(Message):
    """The TAC message class."""

    protocol_id = PublicId("fetchai", "tac", "0.1.0")

    class Type(Enum):
        """TAC Message types."""

        REGISTER = "register"
        UNREGISTER = "unregister"
        TRANSACTION = "transaction"
        GET_STATE_UPDATE = "get_state_update"
        CANCELLED = "cancelled"
        GAME_DATA = "game_data"
        TRANSACTION_CONFIRMATION = "transaction_confirmation"
        # STATE_UPDATE = "state_update"
        TAC_ERROR = "tac_error"

        def __str__(self):
            """Get string representation."""
            return self.value

    class ErrorCode(Enum):
        """This class defines the error codes."""

        GENERIC_ERROR = 0
        REQUEST_NOT_VALID = 1
        AGENT_ADDR_ALREADY_REGISTERED = 2
        AGENT_NAME_ALREADY_REGISTERED = 3
        AGENT_NOT_REGISTERED = 4
        TRANSACTION_NOT_VALID = 5
        TRANSACTION_NOT_MATCHING = 6
        AGENT_NAME_NOT_IN_WHITELIST = 7
        COMPETITION_NOT_RUNNING = 8
        DIALOGUE_INCONSISTENT = 9

    _from_ec_to_msg = {
        ErrorCode.GENERIC_ERROR: "Unexpected error.",
        ErrorCode.REQUEST_NOT_VALID: "Request not recognized",
        ErrorCode.AGENT_ADDR_ALREADY_REGISTERED: "Agent addr already registered.",
        ErrorCode.AGENT_NAME_ALREADY_REGISTERED: "Agent name already registered.",
        ErrorCode.AGENT_NOT_REGISTERED: "Agent not registered.",
        ErrorCode.TRANSACTION_NOT_VALID: "Error in checking transaction",
        ErrorCode.TRANSACTION_NOT_MATCHING: "The transaction request does not match with a previous transaction request with the same id.",
        ErrorCode.AGENT_NAME_NOT_IN_WHITELIST: "Agent name not in whitelist.",
        ErrorCode.COMPETITION_NOT_RUNNING: "The competition is not running yet.",
        ErrorCode.DIALOGUE_INCONSISTENT: "The message is inconsistent with the dialogue.",
    }  # type: Dict[ErrorCode, str]

    def __init__(self, type: Type, **kwargs):
        """
        Initialize.

        :param tac_type: the type of TAC message.
        """
        super().__init__(type=type, **kwargs)
        assert self._is_consistent(), "TACMessage initialization inconsistent."

    @property
    def type(self) -> Type:  # noqa: F821
        """Get the type for the message."""
        assert self.is_set("type"), "type is not set"
        return TACMessage.Type(self.get("type"))

    @property
    def agent_name(self) -> str:
        """Get the agent name from the message."""
        assert self.is_set("agent_name"), "Agent name is not set."
        return cast(str, self.get("agent_name"))

    @property
    def tx_id(self) -> str:
        """Get the transaction id from the message."""
        assert self.is_set("tx_id"), "Transaction id is not set."
        return cast(str, self.get("tx_id"))

    @property
    def tx_sender_addr(self) -> str:
        """Get the sender of the transaction."""
        assert self.is_set("tx_sender_addr"), "Tx_sender_addr is not set."
        return cast(str, self.get("tx_sender_addr"))

    @property
    def tx_counterparty_addr(self) -> str:
        """Get the counterparty of the transaction."""
        assert self.is_set("tx_counterparty_addr"), "Tx_counterparty_addr is not set."
        return cast(str, self.get("tx_counterparty_addr"))

    @property
    def amount_by_currency_id(self) -> Dict[str, int]:
        """Get the amount for each currency."""
        assert self.is_set("amount_by_currency_id"), "Amount by currency is not set."
        return cast(Dict[str, int], self.get("amount_by_currency_id"))

    @property
    def tx_sender_fee(self) -> int:
        """Get the transaction fee for the sender."""
        assert self.is_set("tx_sender_fee"), "Tx_sender_fee is not set."
        return cast(int, self.get("tx_sender_fee"))

    @property
    def tx_counterparty_fee(self) -> int:
        """Get the transaction fee for the counterparty."""
        assert self.is_set("tx_counterparty_fee"), "Tx_counterparty_fee is not set."
        return cast(int, self.get("tx_counterparty_fee"))

    @property
    def quantities_by_good_id(self) -> Dict[str, int]:
        """Get the quantities of the good ids from the message."""
        assert self.is_set("quantities_by_good_id")
        return cast(Dict[str, int], self.get("quantities_by_good_id"))

    @property
    def exchange_params_by_currency_id(self) -> Dict[str, float]:
        """Get the exchange parameters for each currency."""
        assert self.is_set(
            "exchange_params_by_currency_id"
        ), "exchange_params_by_currency_id is not set."
        return cast(Dict[str, float], self.get("exchange_params_by_currency_id"))

    @property
    def utility_params_by_good_id(self) -> Dict[str, float]:
        """Get the utility parameters for each good."""
        assert self.is_set(
            "utility_params_by_good_id"
        ), "utility_params_by_good_id is not set."
        return cast(Dict[str, float], self.get("utility_params_by_good_id"))

    @property
    def tx_fee(self) -> int:
        """Get the transaction fee."""
        assert self.is_set("tx_fee"), "tx_fee is not set."
        return cast(int, self.get("tx_fee"))

    @property
    def agent_addr_to_name(self) -> Dict[Address, str]:
        """Get the mapping from agent address to name."""
        assert self.is_set("agent_addr_to_name"), "agent_id_to_name is not set."
        return cast(Dict[Address, str], self.get("agent_addr_to_name"))

    @property
    def good_id_to_name(self) -> Dict[str, str]:
        """Get mapping from good id to name."""
        assert self.is_set("good_id_to_name"), "good_id_to_name is not set."
        return cast(Dict[str, str], self.get("good_id_to_name"))

    @property
    def version_id(self) -> str:
        """Get the version id."""
        assert self.is_set("version_id"), "version_id is not set."
        return cast(str, self.get("version_id"))

    @property
    def error_code(self) -> ErrorCode:  # noqa: F821
        """Get the error code."""
        assert self.is_set("error_code"), "error_code is not set."
        return TACMessage.ErrorCode(self.get("error_code"))

    @property
    def info(self) -> Dict[str, Any]:
        """Get the info dictionary."""
        assert self.is_set("info"), "info is not set."
        return cast(Dict[str, Any], self.get("info"))

    @property
    def tx_nonce(self) -> int:
        """Get the nonce of the transaction."""
        assert self.is_set("tx_nonce"), "Tx_nonce is not set."
        return cast(int, self.get("tx_nonce"))

    @property
    def tx_sender_signature(self) -> bytes:
        """Get the transaction signature for the sender."""
        assert self.is_set("tx_sender_signature"), "Tx_sender_signature is not set."
        return cast(bytes, self.get("tx_sender_signature"))

    @property
    def tx_counterparty_signature(self) -> bytes:
        """Get the transaction signature for the counterparty."""
        assert self.is_set(
            "tx_counterparty_signature"
        ), "Tx_counterparty_fee is not set."
        return cast(bytes, self.get("tx_counterparty_signature"))

    def _is_consistent(self) -> bool:
        """Check that the data is consistent."""
        try:
            assert isinstance(self.type, TACMessage.Type), "Type is not valid type."
            if self.type == TACMessage.Type.REGISTER:
                assert isinstance(self.agent_name, str)
                assert len(self.body) == 2
            elif self.type == TACMessage.Type.UNREGISTER:
                assert len(self.body) == 1
            elif self.type == TACMessage.Type.TRANSACTION:
                assert isinstance(self.tx_id, str)
                assert isinstance(self.tx_sender_addr, str)
                assert isinstance(self.tx_counterparty_addr, str)
                assert isinstance(self.amount_by_currency_id, dict)
                for key, int_value in self.amount_by_currency_id.items():
                    assert type(key) == str and type(int_value) == int
                assert len(self.amount_by_currency_id.keys()) == len(
                    set(self.amount_by_currency_id.keys())
                )
                assert isinstance(self.tx_sender_fee, int)
                assert self.tx_sender_fee >= 0
                assert isinstance(self.tx_counterparty_fee, int)
                assert self.tx_counterparty_fee >= 0
                assert isinstance(self.quantities_by_good_id, dict)
                for key, int_value in self.quantities_by_good_id.items():
                    assert type(key) == str and type(int_value) == int
                assert len(self.quantities_by_good_id.keys()) == len(
                    set(self.quantities_by_good_id.keys())
                )
                assert isinstance(self.tx_nonce, int)
                assert isinstance(self.tx_sender_signature, bytes)
                assert isinstance(self.tx_counterparty_signature, bytes)
                assert len(self.body) == 11
            elif self.type == TACMessage.Type.GET_STATE_UPDATE:
                assert len(self.body) == 1
            elif self.type == TACMessage.Type.CANCELLED:
                assert len(self.body) == 1
            elif self.type == TACMessage.Type.GAME_DATA:
                assert isinstance(self.amount_by_currency_id, dict)
                for key, int_value in self.amount_by_currency_id.items():
                    assert type(key) == str and type(int_value) == int
                assert isinstance(self.exchange_params_by_currency_id, dict)
                for key, float_value in self.exchange_params_by_currency_id.items():
                    assert type(key) == str and type(float_value) == float
                assert (
                    self.amount_by_currency_id.keys()
                    == self.exchange_params_by_currency_id.keys()
                )
                assert isinstance(self.quantities_by_good_id, dict)
                for key, int_value in self.quantities_by_good_id.items():
                    assert type(key) == str and type(int_value) == int
                assert isinstance(self.utility_params_by_good_id, dict)
                for key, float_value in self.utility_params_by_good_id.items():
                    assert type(key) == str and type(float_value) == float
                assert (
                    self.quantities_by_good_id.keys()
                    == self.utility_params_by_good_id.keys()
                )
                assert isinstance(self.tx_fee, int)
                assert type(self.agent_addr_to_name) in [dict, defaultdict]
                assert type(self.good_id_to_name) in [dict, defaultdict]
                for good_id, name in self.good_id_to_name.items():
                    assert isinstance(good_id, str) and isinstance(name, str)
                assert isinstance(self.version_id, str)
                assert len(self.body) == 9
            elif self.type == TACMessage.Type.TRANSACTION_CONFIRMATION:
                assert isinstance(self.tx_id, str)
                assert isinstance(self.amount_by_currency_id, dict)
                for key, int_value in self.amount_by_currency_id.items():
                    assert type(key) == str and type(int_value) == int
                assert len(self.amount_by_currency_id.keys()) == len(
                    set(self.amount_by_currency_id.keys())
                )
                assert isinstance(self.quantities_by_good_id, dict)
                for key, int_value in self.quantities_by_good_id.items():
                    assert type(key) == int and type(int_value) == int
                assert len(self.quantities_by_good_id.keys()) == len(
                    set(self.quantities_by_good_id.keys())
                )
                assert len(self.body) == 4
            # elif tac_type == TACMessage.Type.STATE_UPDATE:
            #     assert self.is_set("game_data")
            #     assert self.is_set("transactions")
            #     assert len(self.body) == 3
            elif self.type == TACMessage.Type.TAC_ERROR:
                assert self.error_code in TACMessage.ErrorCode
                if self.is_set("info"):
                    isinstance(self.info, dict)
                    assert len(self.body) == 3
                else:
                    assert len(self.body) == 2
            else:
                raise ValueError("Type not recognized.")

        except (AssertionError, ValueError):  # pragma: no cover
            return False

        return True
