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

"""This package contains a scaffold of a model."""

from typing import Dict, Optional, Tuple

from aea.crypto.ledger_apis import LedgerApis
from aea.helpers.transaction.base import Terms
from aea.skills.base import Model


REQUIRED_KEYS = [
    "ethereum_address",
    "fetchai_address",
    "signature_of_ethereum_address",
    "signature_of_fetchai_address",
    "developer_handle",
]
DEFAULT_TOKEN_DISPENSE_AMOUNT = 100000
DEFAULT_TOKEN_DENOMINATION = "atestfet"


class Strategy(Model):
    """This class is the strategy model."""

    def __init__(self, **kwargs) -> None:
        """
        Initialize the strategy of the agent.

        :return: None
        """
        self._token_denomination = kwargs.pop(
            "token_denomination", DEFAULT_TOKEN_DENOMINATION
        )
        self._token_dispense_amount = kwargs.pop(
            "token_dispense_amount", DEFAULT_TOKEN_DISPENSE_AMOUNT
        )
        super().__init__(**kwargs)
        self._is_ready_to_register = False
        self._is_registered = False
        self.is_registration_pending = False
        self.signature_of_ethereum_address: Optional[str] = None
        self._ledger_id = "ethereum"

    def valid_registration(
        self, registration_info: Dict[str, str], sender: str
    ) -> Tuple[bool, int, str]:
        """
        Check if the registration info is valid.

        :param registration_info: the registration info
        :param sender: the sender
        :return: tuple of success, error code and error message
        """
        if not all([key in registration_info for key in REQUIRED_KEYS]):
            return (
                False,
                1,
                f"missing keys in registration info, required: {REQUIRED_KEYS}!",
            )
        if not sender == registration_info["fetchai_address"]:
            return (
                False,
                1,
                "fetchai address of agent and registration info do not match!",
            )
        if not self._valid_signature(
            registration_info["ethereum_address"],
            registration_info["signature_of_fetchai_address"],
            sender,
            "ethereum",
        ):
            return (False, 1, "fetchai address and signature do not match!")
        if not self._valid_signature(
            sender,
            registration_info["signature_of_ethereum_address"],
            registration_info["ethereum_address"],
            "fetchai",
        ):
            return (False, 1, "ethereum address and signature do not match!")
        return (True, 0, "all good!")

    @staticmethod
    def _valid_signature(
        expected_signer: str, signature: str, message_str: str, ledger_id: str
    ) -> bool:
        """
        Check if the signature and message match the expected signer.

        :param expected_signer: the signer
        :param signature: the signature
        :param message_str: the message
        :param ledger_id: the ledger id
        :return: bool indiciating validity
        """
        result = expected_signer in LedgerApis.recover_message(
            ledger_id, message_str.encode("utf-8"), signature
        )
        return result

    def get_terms(self, counterparty: str) -> Terms:
        """
        Get terms of transaction.

        :param counterparty: the counterparty to receive funds
        :return: the terms
        """
        terms = Terms(
            ledger_id="fetchai",
            sender_address=self.context.agent_address,
            counterparty_address=counterparty,
            amount_by_currency_id={
                self._token_denomination: self._token_dispense_amount
            },
            quantities_by_good_id={},
            nonce="",
        )
        return terms
