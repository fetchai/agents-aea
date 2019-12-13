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
from enum import Enum
from typing import Dict, Optional, cast, Any
from collections import defaultdict

from aea.configurations.base import Address
from aea.decision_maker.internal_base import InternalMessage


class TACMessage(InternalMessage):
    """The TAC message class."""

    protocol_id = "tac"

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
        AGENT_PBK_ALREADY_REGISTERED = 2
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
        ErrorCode.AGENT_PBK_ALREADY_REGISTERED: "Agent pbk already registered.",
        ErrorCode.AGENT_NAME_ALREADY_REGISTERED: "Agent name already registered.",
        ErrorCode.AGENT_NOT_REGISTERED: "Agent not registered.",
        ErrorCode.TRANSACTION_NOT_VALID: "Error in checking transaction",
        ErrorCode.TRANSACTION_NOT_MATCHING: "The transaction request does not match with a previous transaction request with the same id.",
        ErrorCode.AGENT_NAME_NOT_IN_WHITELIST: "Agent name not in whitelist.",
        ErrorCode.COMPETITION_NOT_RUNNING: "The competition is not running yet.",
        ErrorCode.DIALOGUE_INCONSISTENT: "The message is inconsistent with the dialogue."
    }  # type: Dict[ErrorCode, str]

    def __init__(self, tac_type: Optional[Type] = None,
                 **kwargs):
        """
        Initialize.

        :param tac_type: the type of TAC message.
        """
        super().__init__(type=tac_type, **kwargs)
        assert self.check_consistency(), "TACMessage initialization inconsistent."

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
    def transaction_id(self) -> str:
        """Get the transaction id from the message."""
        assert self.is_set("transaction_id"), "Transaction id is not set."
        return cast(str, self.get("transaction_id"))

    @property
    def counterparty(self) -> str:
        """Get the counterparty of the transaction."""
        assert self.is_set("counterparty"), "Counterparty is not set."
        return cast(str, self.get("counterparty"))

    @property
    def amount_by_currency(self) -> Dict[str, int]:
        """Get the amount for each currency."""
        assert self.is_set("amount_by_currency"), "Amount by currency is not set."
        return cast(Dict[str, int], self.get('amount_by_currency'))

    @property
    def sender_tx_fee(self) -> int:
        """Get the transaction fee for the sender."""
        assert self.is_set("sender_tx_fee"), "Sender tx fee is not set."
        return cast(int, self.get("sender_tx_fee"))

    @property
    def counterparty_tx_fee(self) -> int:
        """Get the transaction fee for the counterparty."""
        assert self.is_set("counterparty_tx_fee"), "Counterparty transcation fee is not set."
        return cast(int, self.get("counterparty_tx_fee"))

    @property
    def quantities_by_good_pbk(self) -> Dict[str, int]:
        """Get the quantities of the good public keys from the message."""
        assert self.is_set('quantities_by_good_pbk')
        return cast(Dict[str, int], self.get("quantities_by_good_pbk"))

    @property
    def exchange_params_by_currency(self) -> Dict[str, int]:
        """Get the amount for each currency."""
        assert self.is_set("exchange_params_by_currency"), "exchange_params_by_currency is not set."
        return cast(Dict[str, int], self.get("exchange_params_by_currency"))

    @property
    def utility_params_by_good_pbk(self) -> Dict[str, int]:
        """Get the amount for each currency."""
        assert self.is_set("utility_params_by_good_pbk"), "utility_params_by_good_pbk is not set."
        return cast(Dict[str, int], self.get("utility_params_by_good_pbk"))

    @property
    def tx_fee(self) -> int:
        """Get the amount for each currency."""
        assert self.is_set("tx_fee"), "tx_fee is not set."
        return cast(int, self.get("tx_fee"))

    @property
    def agent_pbk_to_name(self) -> Dict[str, Address]:
        """Get the amount for each currency."""
        assert self.is_set("agent_pbk_to_name"), "agent_pbk_to_name is not set."
        return cast(Dict[str, Address], self.get("agent_pbk_to_name"))

    @property
    def good_pbk_to_name(self) -> Dict[str, Address]:
        """Get the amount for each currency."""
        assert self.is_set("good_pbk_to_name"), "good_pbk_to_name is not set."
        return cast(Dict[str, Address], self.get("good_pbk_to_name"))

    @property
    def version_id(self) -> str:
        """Get the amount for each currency."""
        assert self.is_set("version_id"), "version_id is not set."
        return cast(str, self.get("version_id"))

    @property
    def error_code(self) -> ErrorCode:  # noqa: F821
        """Get the amount for each currency."""
        assert self.is_set("error_code"), "error_code is not set."
        return TACMessage.ErrorCode(self.get("error_code"))

    @property
    def info(self) -> Dict[str, Any]:
        """Get the amount for each currency."""
        assert self.is_set("info"), "info is not set."
        return cast(Dict[str, Any], self.get("info"))

    def check_consistency(self) -> bool:
        """Check that the data is consistent."""
        try:
            assert self.type in TACMessage.Type, "Type is not valid."
            if self.type == TACMessage.Type.REGISTER:
                isinstance(self.agent_name, str)
                assert len(self.body) == 2
            elif self.type == TACMessage.Type.UNREGISTER:
                assert len(self.body) == 1
            elif self.type == TACMessage.Type.TRANSACTION:
                isinstance(self.transaction_id, str)
                isinstance(self.counterparty, str)
                isinstance(self.amount_by_currency, dict)
                for key, value in self.amount_by_currency.items():
                    assert type(key) == str and type(value) == int
                assert len(self.amount_by_currency.keys()) == len(set(self.amount_by_currency.keys()))
                isinstance(self.sender_tx_fee, int)
                assert self.sender_tx_fee >= 0
                isinstance(self.counterparty_tx_fee, int)
                assert self.counterparty_tx_fee >= 0
                isinstance(self.quantities_by_good_pbk, dict)
                for key, value in self.quantities_by_good_pbk.items():
                    assert type(key) == str and type(value) == int
                assert len(self.quantities_by_good_pbk.keys()) == len(set(self.quantities_by_good_pbk.keys()))
                assert len(self.body) == 7
            elif self.type == TACMessage.Type.GET_STATE_UPDATE:
                assert len(self.body) == 1
            elif self.type == TACMessage.Type.CANCELLED:
                assert len(self.body) == 1
            elif self.type == TACMessage.Type.GAME_DATA:
                isinstance(self.amount_by_currency, dict)
                for key, value in self.amount_by_currency.items():
                    assert type(key) == str and type(value) == int
                isinstance(self.exchange_params_by_currency, dict)
                for key, value in self.exchange_params_by_currency.items():
                    assert type(key) == str and type(value) == float
                assert self.amount_by_currency.keys() == self.exchange_params_by_currency.keys()
                isinstance(self.quantities_by_good_pbk, dict)
                for key, value in self.quantities_by_good_pbk.items():
                    assert type(key) == str and type(value) == int
                isinstance(self.utility_params_by_good_pbk, dict)
                for key, value in self.utility_params_by_good_pbk.items():
                    assert type(key) == str and type(value) == float
                assert self.quantities_by_good_pbk.keys() == self.utility_params_by_good_pbk.keys()
                isinstance(self.tx_fee, int)
                assert self.is_set("agent_pbk_to_name")
                assert type(self.get("agent_pbk_to_name")) in [dict, defaultdict]
                assert self.is_set("good_pbk_to_name")
                assert type(self.get("good_pbk_to_name")) in [dict, defaultdict]
                isinstance(self.version_id, str)
                assert len(self.body) == 9
            elif self.type == TACMessage.Type.TRANSACTION_CONFIRMATION:
                isinstance(self.transaction_id, str)
                isinstance(self.amount_by_currency, dict)
                for key, value in self.amount_by_currency.items():
                    assert type(key) == str and type(value) == int
                assert len(self.amount_by_currency.keys()) == len(set(self.amount_by_currency.keys()))
                isinstance(self.quantities_by_good_pbk, dict)
                for key, value in self.quantities_by_good_pbk.items():
                    assert type(key) == str and type(value) == int
                assert len(self.quantities_by_good_pbk.keys()) == len(set(self.quantities_by_good_pbk.keys()))
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
