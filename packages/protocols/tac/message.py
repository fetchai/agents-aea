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
from typing import Dict, Optional, cast
from collections import defaultdict

from aea.protocols.base import Message


class TACMessage(Message):
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

    def check_consistency(self) -> bool:
        """Check that the data is consistent."""
        try:
            assert self.is_set("type")
            tac_type = TACMessage.Type(self.get("type"))
            if tac_type == TACMessage.Type.REGISTER:
                assert self.is_set("agent_name")
                assert len(self.body) == 2
            elif tac_type == TACMessage.Type.UNREGISTER:
                assert len(self.body) == 1
            elif tac_type == TACMessage.Type.TRANSACTION:
                assert self.is_set("transaction_id")
                assert type(self.get("transaction_id")) == str
                assert self.is_set("counterparty")
                assert type(self.get("counterparty")) == str
                assert self.is_set("amount_by_currency")
                amount_by_currency = cast(Dict, self.get("amount_by_currency"))
                for key, value in amount_by_currency.items():
                    assert type(key) == str and type(value) == int
                assert len(amount_by_currency.keys()) == len(set(amount_by_currency.keys()))
                assert self.is_set("sender_tx_fee")
                sender_tx_fee = self.get("sender_tx_fee")
                assert type(sender_tx_fee) == int
                assert cast(int, sender_tx_fee) >= 0
                assert self.is_set("counterparty_tx_fee")
                counterparty_tx_fee = self.get("counterparty_tx_fee")
                assert type(counterparty_tx_fee) == int
                assert cast(int, counterparty_tx_fee) >= 0
                assert self.is_set("quantities_by_good_pbk")
                quantities_by_good_pbk = cast(Dict, self.get("quantities_by_good_pbk"))
                for key, value in quantities_by_good_pbk.items():
                    assert type(key) == str and type(value) == int
                assert len(quantities_by_good_pbk.keys()) == len(set(quantities_by_good_pbk.keys()))
                assert len(self.body) == 7
            elif tac_type == TACMessage.Type.GET_STATE_UPDATE:
                assert len(self.body) == 1
            elif tac_type == TACMessage.Type.CANCELLED:
                assert len(self.body) == 1
            elif tac_type == TACMessage.Type.GAME_DATA:
                assert self.is_set("amount_by_currency")
                amount_by_currency = cast(Dict, self.get("amount_by_currency"))
                for key, value in amount_by_currency.items():
                    assert type(key) == str and type(value) == int
                assert self.is_set("exchange_params_by_currency")
                exchange_params_by_currency = cast(Dict, self.get("exchange_params_by_currency"))
                for key, value in exchange_params_by_currency.items():
                    assert type(key) == str and type(value) == float
                assert amount_by_currency.keys() == exchange_params_by_currency.keys()
                assert self.is_set("quantities_by_good_pbk")
                quantities_by_good_pbk = cast(Dict, self.get("quantities_by_good_pbk"))
                for key, value in quantities_by_good_pbk.items():
                    assert type(key) == str and type(value) == int
                assert self.is_set("utility_params_by_good_pbk")
                utility_params_by_good_pbk = cast(Dict, self.get("utility_params_by_good_pbk"))
                for key, value in utility_params_by_good_pbk.items():
                    assert type(key) == str and type(value) == float
                assert quantities_by_good_pbk.keys() == utility_params_by_good_pbk.keys()
                assert self.is_set("tx_fee")
                assert type(self.get("tx_fee")) == int
                assert self.is_set("agent_pbk_to_name")
                assert type(self.get("agent_pbk_to_name")) in [dict, defaultdict]
                assert self.is_set("good_pbk_to_name")
                assert type(self.get("good_pbk_to_name")) in [dict, defaultdict]
                assert self.is_set("version_id")
                assert type(self.get("version_id")) == str
                assert len(self.body) == 9
            elif tac_type == TACMessage.Type.TRANSACTION_CONFIRMATION:
                assert self.is_set("transaction_id")
                assert type(self.get("transaction_id")) == str
                assert self.is_set("amount_by_currency")
                amount_by_currency = cast(Dict, self.get("amount_by_currency"))
                for key, value in amount_by_currency.items():
                    assert type(key) == str and type(value) == int
                assert len(amount_by_currency.keys()) == len(set(amount_by_currency.keys()))
                assert self.is_set("quantities_by_good_pbk")
                quantities_by_good_pbk = cast(Dict, self.get("quantities_by_good_pbk"))
                for key, value in quantities_by_good_pbk.items():
                    assert type(key) == str and type(value) == int
                assert len(quantities_by_good_pbk.keys()) == len(set(quantities_by_good_pbk.keys()))
                assert len(self.body) == 4
            # elif tac_type == TACMessage.Type.STATE_UPDATE:
            #     assert self.is_set("game_data")
            #     assert self.is_set("transactions")
            #     assert len(self.body) == 3
            elif tac_type == TACMessage.Type.TAC_ERROR:
                assert self.is_set("error_code")
                error_code = self.get("error_code")
                assert error_code in set(self.ErrorCode)
                assert len(self.body) == 2
            else:
                raise ValueError("Type not recognized.")
        except (AssertionError, ValueError):  # pragma: no cover
            return False

        return True
