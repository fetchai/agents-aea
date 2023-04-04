# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2023 Valory AG
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
"""This module contains the Faucet implementation for the solana ledger."""
import json
import time
from typing import Optional, Union

from aea_ledger_solana.constants import (
    DEFAULT_ADDRESS,
    LAMPORTS_PER_SOL,
    TESTNET_NAME,
    _SOLANA,
)
from aea_ledger_solana.utils import default_logger
from solana.rpc.api import Client  # type: ignore
from solders.pubkey import Pubkey as PublicKey

from aea.common import Address
from aea.crypto.base import FaucetApi
from aea.helpers.base import try_decorator


class SolanaFaucetApi(FaucetApi):
    """Solana testnet faucet API."""

    identifier = _SOLANA
    testnet_name = TESTNET_NAME
    DEFAULT_AMOUNT = 500000000

    def get_wealth(self, address: Address, url: Optional[str] = None) -> None:
        """
        Get wealth from the faucet for the provided address.

        :param address: the address.
        :param url: the url

        """
        amount = self.DEFAULT_AMOUNT
        self.try_get_wealth(address, amount, url)

    @staticmethod
    @try_decorator(
        "An error occurred while attempting to generate wealth:\n{}",
        logger_method="error",
    )
    def try_get_wealth(
        address: Address, amount: Optional[int] = None, url: Optional[str] = None
    ) -> Optional[str]:
        """
        Get wealth from the faucet for the provided address.

        :param address: the address.
        :param amount: optional int
        :param url: the url

        :return: optional string
        """
        if url is None:
            url = DEFAULT_ADDRESS

        if amount is None:
            amount = int(LAMPORTS_PER_SOL * 0.5)
        else:
            amount = LAMPORTS_PER_SOL * amount

        solana_client = Client(url, commitment="confirmed")
        resp = solana_client.request_airdrop(PublicKey.from_string(address), amount)

        response = json.loads(resp.to_json())
        if "message" in response:
            default_logger.error("Response: {}".format(response["message"]))
            raise Exception(response.get("message"))  # pylint
        if response["result"] is None:
            default_logger.error("Response: {}".format("airdrop failed"))
        elif "error" in response:  # pragma: no cover
            default_logger.error("Response: {}".format("airdrop failed"))
        elif "result" in response:  # pragma: nocover
            default_logger.warning(
                "Response: {}\nMessage: {}".format("success", response["result"])
            )
            return response["result"]
        raise Exception("airdrop failed")

    @staticmethod
    def generate_wealth_if_needed(
        api,
        address,
        min_amount=None,
    ) -> Union[str, None]:
        """Check the balance prior to generating wealth."""
        balance = api.get_balance(address)

        min_balance = min_amount if min_amount is not None else 1000000000
        if balance >= min_balance:
            return "not required"
        faucet = SolanaFaucetApi()
        cnt = 0
        transaction_digest = None
        while transaction_digest is None and cnt < 10:
            transaction_digest = faucet.try_get_wealth(address)
            cnt += 1
            time.sleep(5)

        if transaction_digest is None:
            return "failed"
        _, is_settled = api.wait_get_receipt(transaction_digest)
        if is_settled is True:
            return "success"
        return "failed"
